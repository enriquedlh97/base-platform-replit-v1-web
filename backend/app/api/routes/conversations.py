"""Conversation management routes."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import col, func, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.workspaces import get_workspace_or_404
from app.models import (
    Conversation,
    ConversationCreate,
    ConversationMessage,
    ConversationMessageCreate,
    ConversationMessagePublic,
    ConversationPublic,
    ConversationsListPublic,
    ConversationSummary,
    ConversationUpdate,
    ConversationWithTasks,
    CuaTask,
    CuaTaskSummary,
    Workspace,
)
from app.models import (
    Message as ResponseMessage,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_conversation_or_404(
    conversation_id: UUID, workspace_id: UUID, session: SessionDep
) -> Conversation:
    """Verify conversation exists and belongs to workspace."""
    statement: SelectOfScalar[Conversation] = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.workspace_id == workspace_id,
    )
    conversation = session.exec(statement).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/workspaces/{workspace_id}", response_model=list[ConversationPublic])
def get_workspace_conversations(
    workspace_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get all conversations for a workspace."""
    get_workspace_or_404(workspace_id, session, current_user)
    statement: SelectOfScalar[Conversation] = (
        select(Conversation)
        .where(Conversation.workspace_id == workspace_id)
        .order_by(col(Conversation.created_at).desc())
    )
    return list(session.exec(statement).all())


@router.get(
    "/workspaces/{workspace_id}/summaries", response_model=ConversationsListPublic
)
def get_workspace_conversations_with_summaries(
    workspace_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    status: str | None = Query(default=None, description="Filter by status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> Any:
    """Get conversations for a workspace with message and task counts.

    Returns a list of conversations with summary information including:
    - Message count
    - Task count
    - Last message preview
    """
    get_workspace_or_404(workspace_id, session, current_user)

    # Build base query
    query = select(Conversation).where(Conversation.workspace_id == workspace_id)

    # Apply status filter if provided
    if status:
        query = query.where(Conversation.status == status)

    # Get total count
    count_query = (
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.workspace_id == workspace_id)
    )
    if status:
        count_query = count_query.where(Conversation.status == status)
    total_count = session.exec(count_query).one()

    # Apply pagination and ordering
    query = (
        query.order_by(col(Conversation.updated_at).desc()).offset(skip).limit(limit)
    )
    conversations = list(session.exec(query).all())

    # Build summaries with counts
    summaries: list[ConversationSummary] = []
    for conv in conversations:
        # Get message count
        message_count_query = (
            select(func.count())
            .select_from(ConversationMessage)
            .where(ConversationMessage.conversation_id == conv.id)
        )
        message_count = session.exec(message_count_query).one()

        # Get task count
        task_count_query = (
            select(func.count())
            .select_from(CuaTask)
            .where(CuaTask.conversation_id == conv.id)
        )
        task_count = session.exec(task_count_query).one()

        # Get last message
        last_message_query = (
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conv.id)
            .order_by(col(ConversationMessage.created_at).desc())
            .limit(1)
        )
        last_message = session.exec(last_message_query).first()

        summaries.append(
            ConversationSummary(
                id=conv.id,
                workspace_id=conv.workspace_id,
                visitor_name=conv.visitor_name,
                visitor_email=conv.visitor_email,
                channel=conv.channel,
                status=conv.status,
                human_time_saved_minutes=conv.human_time_saved_minutes,
                tags=conv.tags,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=message_count,
                task_count=task_count,
                last_message_content=last_message.content[:100]
                if last_message
                else None,
                last_message_role=last_message.role if last_message else None,
                last_message_at=last_message.created_at if last_message else None,
            )
        )

    return ConversationsListPublic(data=summaries, count=total_count)


@router.post("/workspaces/{workspace_id}", response_model=ConversationPublic)
def create_conversation(
    workspace_id: UUID,
    session: SessionDep,
    conversation_in: ConversationCreate,
    current_user: CurrentUser,
) -> Any:
    """Create a new conversation for a workspace."""
    get_workspace_or_404(workspace_id, session, current_user)

    db_conversation = Conversation.model_validate(
        conversation_in, update={"workspace_id": workspace_id}
    )
    session.add(db_conversation)
    session.commit()
    session.refresh(db_conversation)
    return db_conversation


@router.get("/{conversation_id}", response_model=ConversationPublic)
def get_conversation(
    conversation_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get a conversation by ID."""
    statement: SelectOfScalar[Conversation] = select(Conversation).where(
        Conversation.id == conversation_id
    )
    conversation = session.exec(statement).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify workspace ownership
    workspace_statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.id == conversation.workspace_id
    )
    workspace = session.exec(workspace_statement).first()
    if workspace and workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")
    return conversation


@router.get("/{conversation_id}/with-tasks", response_model=ConversationWithTasks)
def get_conversation_with_tasks(
    conversation_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get a conversation with its associated CUA tasks."""
    statement: SelectOfScalar[Conversation] = select(Conversation).where(
        Conversation.id == conversation_id
    )
    conversation = session.exec(statement).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify workspace ownership
    workspace_statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.id == conversation.workspace_id
    )
    workspace = session.exec(workspace_statement).first()
    if workspace and workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")

    # Get associated tasks
    tasks_statement: SelectOfScalar[CuaTask] = (
        select(CuaTask)
        .where(CuaTask.conversation_id == conversation_id)
        .order_by(col(CuaTask.created_at).desc())
    )
    tasks = list(session.exec(tasks_statement).all())

    # Convert tasks to summaries
    task_summaries = [
        CuaTaskSummary(
            id=task.id,
            workspace_id=task.workspace_id,
            conversation_id=task.conversation_id,
            trace_id=task.trace_id,
            instruction=task.instruction,
            status=task.status,
            model_id=task.model_id,
            final_state=task.final_state,
            error_message=task.error_message,
            step_count=len(task.steps) if task.steps else 0,
            task_metadata=task.task_metadata if task.task_metadata else {},
            started_at=task.started_at,
            completed_at=task.completed_at,
            created_at=task.created_at,
        )
        for task in tasks
    ]

    return ConversationWithTasks(
        id=conversation.id,
        workspace_id=conversation.workspace_id,
        visitor_name=conversation.visitor_name,
        visitor_email=conversation.visitor_email,
        channel=conversation.channel,
        status=conversation.status,
        human_time_saved_minutes=conversation.human_time_saved_minutes,
        tags=conversation.tags,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        tasks=task_summaries,
    )


@router.patch("/{conversation_id}", response_model=ConversationPublic)
def update_conversation(
    conversation_id: UUID,
    session: SessionDep,
    conversation_in: ConversationUpdate,
    current_user: CurrentUser,
) -> Any:
    """Update a conversation."""
    statement: SelectOfScalar[Conversation] = select(Conversation).where(
        Conversation.id == conversation_id
    )
    conversation = session.exec(statement).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify workspace ownership
    workspace_statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.id == conversation.workspace_id
    )
    workspace = session.exec(workspace_statement).first()
    if workspace and workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")

    update_data = conversation_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    conversation.sqlmodel_update(update_data)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


# Message routes
@router.get(
    "/{conversation_id}/messages", response_model=list[ConversationMessagePublic]
)
def get_conversation_messages(
    conversation_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get all messages for a conversation."""
    # Verify conversation exists and user has access
    conversation_statement: SelectOfScalar[Conversation] = select(Conversation).where(
        Conversation.id == conversation_id
    )
    conversation = session.exec(conversation_statement).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify workspace ownership
    workspace_statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.id == conversation.workspace_id
    )
    workspace = session.exec(workspace_statement).first()
    if workspace and workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")

    statement: SelectOfScalar[ConversationMessage] = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by("created_at")
    )
    return list(session.exec(statement).all())


@router.post("/{conversation_id}/messages", response_model=ConversationMessagePublic)
def create_conversation_message(
    conversation_id: UUID,
    session: SessionDep,
    message_in: ConversationMessageCreate,
    current_user: CurrentUser,
) -> Any:
    """Create a new message in a conversation."""
    # Verify conversation exists and user has access
    conversation_statement: SelectOfScalar[Conversation] = select(Conversation).where(
        Conversation.id == conversation_id
    )
    conversation = session.exec(conversation_statement).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify workspace ownership
    workspace_statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.id == conversation.workspace_id
    )
    workspace = session.exec(workspace_statement).first()
    if workspace and workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")

    timestamp = message_in.timestamp or datetime.now(timezone.utc)
    db_message = ConversationMessage.model_validate(
        message_in,
        update={
            "conversation_id": conversation_id,
            "timestamp": timestamp,
        },
    )
    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    return db_message


@router.delete("/{conversation_id}", response_model=ResponseMessage)
def delete_conversation(
    conversation_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Delete a conversation."""
    statement: SelectOfScalar[Conversation] = select(Conversation).where(
        Conversation.id == conversation_id
    )
    conversation = session.exec(statement).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify workspace ownership
    workspace_statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.id == conversation.workspace_id
    )
    workspace = session.exec(workspace_statement).first()
    if workspace and workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")

    session.delete(conversation)
    session.commit()
    return ResponseMessage(message="Conversation deleted successfully")
