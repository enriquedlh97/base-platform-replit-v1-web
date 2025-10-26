"""Conversation management routes."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlmodel import col, select
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
    ConversationUpdate,
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
