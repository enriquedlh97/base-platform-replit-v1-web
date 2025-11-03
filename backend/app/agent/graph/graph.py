import os
from collections.abc import AsyncIterator
from typing import Any

from langchain_groq import ChatGroq

from app.agent.core.prompts import build_chat_messages, build_system_prompt
from app.core.config import settings


async def stream_agent_reply(
    *,
    workspace_knowledge_base_text: str,
    conversation_history: list[dict[str, str]],
    request_id: str | None,
) -> AsyncIterator[dict[str, Any]]:
    """Minimal streaming agent.

    Emits dict events: {"type": "delta", "text_chunk": str} and optional tool_* later.
    """
    # Configure model from central settings (.env via app/core/config.py)
    if not settings.GROQ_API_KEY:
        # Let the route emit an error event with a clear message
        raise RuntimeError("Missing GROQ_API_KEY in backend environment")
    # Ensure downstream SDK sees the key via env (ChatGroq reads env var)
    os.environ.setdefault("GROQ_API_KEY", settings.GROQ_API_KEY)

    model = ChatGroq(
        model=settings.TEXT_MODEL_NAME,
        temperature=settings.MODEL_TEMPERATURE,
        stop_sequences=None,
    )

    system_prompt = build_system_prompt(workspace_knowledge_base_text)
    messages = build_chat_messages(conversation_history, system_prompt)

    # Avoid unused variable warning while keeping signature stable for idempotency in future
    _ = request_id

    # LangChain message format expected: list of dict(role, content)
    accumulated: list[str] = []
    try:
        async for chunk in model.astream(messages):
            # Some providers populate .delta, others only .content
            text_chunk = getattr(chunk, "delta", None) or getattr(
                chunk, "content", None
            )
            if text_chunk:
                accumulated.append(text_chunk)
                yield {"type": "delta", "text_chunk": text_chunk}
    # As a safety net, fall back to a single-shot completion if streaming yields nothing
    except Exception:
        pass
    if not accumulated:
        try:
            response = await model.ainvoke(messages)
            text = getattr(response, "content", None)
            if text:
                yield {"type": "delta", "text_chunk": text}
        except Exception:
            # Swallow here; the route will emit an error event
            return
