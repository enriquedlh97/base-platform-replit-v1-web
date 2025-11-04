"""Conversation message management routes."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlmodel import select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Conversation,
    ConversationMessage,
    ConversationMessageCreate,
    ConversationMessagePublic,
    Workspace,
)
from app.models import (
    Message as ResponseMessage,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])


def get_message_or_404(
    message_id: UUID, conversation_id: UUID, session: SessionDep
) -> ConversationMessage:
    """Verify message exists and belongs to conversation."""
    statement: SelectOfScalar[ConversationMessage] = select(ConversationMessage).where(
        ConversationMessage.id == message_id,
        ConversationMessage.conversation_id == conversation_id,
    )
    message = session.exec(statement).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.get(
    "/conversations/{conversation_id}", response_model=list[ConversationMessagePublic]
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


@router.post(
    "/conversations/{conversation_id}", response_model=ConversationMessagePublic
)
def create_message(
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


@router.get("/{message_id}", response_model=ConversationMessagePublic)
def get_message(
    message_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get a message by ID."""
    statement: SelectOfScalar[ConversationMessage] = select(ConversationMessage).where(
        ConversationMessage.id == message_id
    )
    message = session.exec(statement).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Verify conversation and workspace ownership
    conversation_statement: SelectOfScalar[Conversation] = select(Conversation).where(
        Conversation.id == message.conversation_id
    )
    conversation = session.exec(conversation_statement).first()
    if conversation:
        workspace_statement: SelectOfScalar[Workspace] = select(Workspace).where(
            Workspace.id == conversation.workspace_id
        )
        workspace = session.exec(workspace_statement).first()
        if workspace and workspace.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not your workspace")
    return message


@router.delete("/{message_id}", response_model=ResponseMessage)
def delete_message(
    message_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Delete a message."""
    statement: SelectOfScalar[ConversationMessage] = select(ConversationMessage).where(
        ConversationMessage.id == message_id
    )
    message = session.exec(statement).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Verify conversation and workspace ownership
    conversation_statement: SelectOfScalar[Conversation] = select(Conversation).where(
        Conversation.id == message.conversation_id
    )
    conversation = session.exec(conversation_statement).first()
    if conversation:
        workspace_statement: SelectOfScalar[Workspace] = select(Workspace).where(
            Workspace.id == conversation.workspace_id
        )
        workspace = session.exec(workspace_statement).first()
        if workspace and workspace.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not your workspace")

    session.delete(message)
    session.commit()
    return ResponseMessage(message="Message deleted successfully")
