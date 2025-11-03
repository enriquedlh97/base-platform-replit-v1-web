"""Public, anonymous chat endpoints for workspace-scoped conversations.

Phase 1: minimal create/post/list with polling support.
"""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.deps import SessionDep
from app.models import (
    Conversation,
    ConversationCreate,
    ConversationMessage,
    ConversationMessagePublic,
    Workspace,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["public"])


class CreatePublicConversationRequest(BaseModel):
    workspace_handle: str = Field(min_length=1, max_length=100)
    idempotency_key: str | None = Field(default=None, max_length=128)


class CreatePublicConversationResponse(BaseModel):
    conversation_id: UUID
    created_at: datetime


class PostPublicMessageRequest(BaseModel):
    role: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1)
    idempotency_key: str | None = Field(default=None, max_length=128)


class ListMessagesResponse(BaseModel):
    messages: list[ConversationMessagePublic]
    next_since: datetime | None


def _resolve_workspace_by_handle(
    session: SessionDep, workspace_handle: str
) -> Workspace:
    statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.handle == workspace_handle
    )
    workspace = session.exec(statement).first()
    if not workspace or not workspace.is_active:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.post("/conversations", response_model=CreatePublicConversationResponse)
def create_public_conversation(
    session: SessionDep,
    payload: CreatePublicConversationRequest,
) -> Any:
    """Create a new anonymous conversation for a workspace handle.

    For MVP, we do not enforce idempotency at DB level; callers may reuse
    the same conversation or de-duplicate client-side if needed.
    """
    workspace = _resolve_workspace_by_handle(session, payload.workspace_handle)

    db_conversation = Conversation.model_validate(
        ConversationCreate(channel="web_public", status="active"),
        update={
            "workspace_id": workspace.id,
        },
    )
    session.add(db_conversation)
    session.commit()
    session.refresh(db_conversation)
    return CreatePublicConversationResponse(
        conversation_id=db_conversation.id, created_at=db_conversation.created_at
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationMessagePublic,
)
def post_public_message(
    conversation_id: UUID,
    session: SessionDep,
    payload: PostPublicMessageRequest,
) -> Any:
    """Post a user message to a conversation.

    If idempotency_key is provided and the combination already exists, return the
    existing message. For Phase 1, we only check an optional column match.
    """
    # Validate conversation exists
    statement_conv: SelectOfScalar[Conversation] = select(Conversation).where(
        Conversation.id == conversation_id
    )
    conversation = session.exec(statement_conv).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if payload.idempotency_key:
        # Best-effort lookup by idempotency_key if column exists
        try:
            statement_existing: SelectOfScalar[ConversationMessage] = select(
                ConversationMessage
            ).where(
                ConversationMessage.conversation_id == conversation_id,
                ConversationMessage.role == payload.role,
                ConversationMessage.content == payload.content,
                ConversationMessage.idempotency_key == payload.idempotency_key,
            )
            existing = session.exec(statement_existing).first()
            if existing:
                return existing
        except Exception:
            # Column might not exist yet; proceed to insert
            logger.debug("Idempotency check skipped (column missing)")

    timestamp = datetime.now(timezone.utc)
    db_message = ConversationMessage(
        conversation_id=conversation_id,
        role=payload.role,
        content=payload.content,
        timestamp=timestamp,
    )
    # Set idempotency_key if column exists
    if hasattr(db_message, "idempotency_key"):
        db_message.idempotency_key = payload.idempotency_key

    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    return db_message


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ListMessagesResponse,
)
def list_public_messages(
    conversation_id: UUID,
    session: SessionDep,
    since: datetime | None = None,
    limit: int = 50,
) -> Any:
    # Validate conversation exists
    statement_conv: SelectOfScalar[Conversation] = select(Conversation).where(
        Conversation.id == conversation_id
    )
    conversation = session.exec(statement_conv).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    query = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by("created_at")
    )
    if since:
        query = query.where(ConversationMessage.created_at > since)
    if limit:
        query = query.limit(min(max(limit, 1), 200))

    rows: list[ConversationMessage] = list(session.exec(query).all())
    next_since = rows[-1].created_at if rows else since
    public_rows: list[ConversationMessagePublic] = [
        ConversationMessagePublic(
            id=m.id,
            conversation_id=m.conversation_id,
            content=m.content,
            role=m.role,
            timestamp=m.timestamp,
            created_at=m.created_at,
        )
        for m in rows
    ]
    return ListMessagesResponse(messages=public_rows, next_since=next_since)
