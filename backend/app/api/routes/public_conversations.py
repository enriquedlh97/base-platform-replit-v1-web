"""Public, anonymous chat endpoints for workspace-scoped conversations.

Phase 1: minimal create/post/list with polling support.
"""

import logging
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlmodel import select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.agent.core.context import clear_agent_context, set_agent_context
from app.agent.graph.graph import stream_agent_reply
from app.agent.interfaces.http.sse import encode_sse_event
from app.api.deps import SessionDep
from app.models import (
    Conversation,
    ConversationCreate,
    ConversationMessage,
    ConversationMessagePublic,
    SchedulingConnector,
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


class WorkspaceProfilePublic(BaseModel):
    """Public workspace profile information for display on public chat page."""

    handle: str
    public_name: str | None
    subtitle: str | None
    description: str | None
    profile_image_url: str | None


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


@router.get("/workspaces/{workspace_handle}", response_model=WorkspaceProfilePublic)
def get_workspace_profile(
    workspace_handle: str,
    session: SessionDep,
) -> Any:
    """Get public workspace profile by handle.

    Returns public profile information (name, subtitle, description, profile image)
    for display on the public chat page. No authentication required.
    """
    workspace = _resolve_workspace_by_handle(session, workspace_handle)
    return WorkspaceProfilePublic(
        handle=workspace.handle,
        public_name=workspace.public_name,
        subtitle=workspace.subtitle,
        description=workspace.description,
        profile_image_url=workspace.profile_image_url,
    )


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
    _since: datetime | None = None,
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
    if _since:
        query = query.where(ConversationMessage.created_at > _since)
    if limit:
        query = query.limit(min(max(limit, 1), 200))

    rows: list[ConversationMessage] = list(session.exec(query).all())
    next_since = rows[-1].created_at if rows else _since
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


@router.get(
    "/conversations/{conversation_id}/stream",
)
async def stream_public_conversation(
    conversation_id: UUID,
    session: SessionDep,
    _since: datetime | None = None,
    request_id: str | None = None,
) -> StreamingResponse:
    """Server-Sent Events (SSE) stream for assistant reply.

    For MVP, we start a single agent run that streams tokens (delta events)
    and emits a final message_end with the full text, which we persist.
    """
    # Validate conversation and load workspace and history
    statement_conv: SelectOfScalar[Conversation] = select(Conversation).where(
        Conversation.id == conversation_id
    )
    conversation = session.exec(statement_conv).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    statement_ws: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.id == conversation.workspace_id
    )
    workspace = session.exec(statement_ws).first()
    if not workspace or not workspace.is_active:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get Calendly connector URL if available
    calendly_url: str | None = None
    connector_statement: SelectOfScalar[SchedulingConnector] = select(
        SchedulingConnector
    ).where(
        SchedulingConnector.workspace_id == workspace.id,
        SchedulingConnector.type == "calendly",
        SchedulingConnector.is_active == True,  # noqa: E712
    )
    calendly_connector = session.exec(connector_statement).first()
    if calendly_connector and calendly_connector.config:
        calendly_url = calendly_connector.config.get("link")

    # Load conversation history ordered by created_at
    history_query = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by("created_at")
    )
    history_rows: list[ConversationMessage] = list(session.exec(history_query).all())

    start_ts = datetime.now(timezone.utc)
    logger.info(
        "public_stream_start",
        extra={
            "conversation_id": str(conversation_id),
            "workspace_id": str(workspace.id),
            "request_id": request_id,
        },
    )

    async def event_generator() -> AsyncIterator[bytes]:
        full_text_chunks: list[str] = []
        # message_start
        yield encode_sse_event("message_start", {"message_id": str(conversation_id)})

        # Set agent context for tool access to workspace/conversation IDs
        set_agent_context(
            workspace_id=workspace.id,
            conversation_id=conversation_id,
        )

        try:
            async for evt in stream_agent_reply(
                workspace_knowledge_base_text=workspace.knowledge_base or "",
                conversation_history=[
                    {"role": m.role, "content": m.content} for m in history_rows
                ],
                calendly_url=calendly_url,
                request_id=request_id,
            ):
                if evt["type"] == "delta":
                    full_text_chunks.append(evt["text_chunk"])
                    yield encode_sse_event("delta", {"text_chunk": evt["text_chunk"]})
                elif evt["type"] == "message_end":
                    # Handle intermediate message_end (e.g., after pre-message, before tool)
                    # Save the current accumulated text as a separate message
                    if full_text_chunks:
                        pre_message_text = "".join(full_text_chunks)
                        timestamp = datetime.now(timezone.utc)
                        db_message = ConversationMessage(
                            conversation_id=conversation_id,
                            role="assistant",
                            content=pre_message_text,
                            timestamp=timestamp,
                        )
                        session.add(db_message)
                        session.commit()
                        # Clear chunks for the next message
                        full_text_chunks = []
                        # Start a new message
                        yield encode_sse_event(
                            "message_start", {"message_id": str(conversation_id)}
                        )
                elif evt["type"] == "tool_call":
                    yield encode_sse_event(
                        "tool_call",
                        {
                            "id": evt.get("id"),
                            "tool": evt.get("tool"),
                            "args": evt.get("args", {}),
                        },
                    )
                elif evt["type"] == "tool_result":
                    yield encode_sse_event(
                        "tool_result",
                        {
                            "id": evt.get("id"),
                            "status": evt.get("status"),
                            "data": evt.get("data"),
                            "error": evt.get("error"),
                        },
                    )
        except Exception as exc:  # pragma: no cover
            logger.exception(
                "public_stream_error",
                extra={
                    "conversation_id": str(conversation_id),
                    "workspace_id": str(workspace.id),
                    "request_id": request_id,
                },
            )
            yield encode_sse_event(
                "error", {"code": "stream_failed", "message": str(exc)}
            )
        # message_end and persistence
        full_text = "".join(full_text_chunks)
        yield encode_sse_event(
            "message_end",
            {"message_id": str(conversation_id), "full_text": full_text},
        )
        if full_text:
            timestamp = datetime.now(timezone.utc)
            db_message = ConversationMessage(
                conversation_id=conversation_id,
                role="assistant",
                content=full_text,
                timestamp=timestamp,
            )
            session.add(db_message)
            session.commit()

        end_ts = datetime.now(timezone.utc)
        latency_ms = int((end_ts - start_ts).total_seconds() * 1000)
        logger.info(
            "public_stream_end",
            extra={
                "conversation_id": str(conversation_id),
                "workspace_id": str(workspace.id),
                "request_id": request_id,
                "latency_ms": latency_ms,
            },
        )

        # Clear agent context after execution
        clear_agent_context()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
