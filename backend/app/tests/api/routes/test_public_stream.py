from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import settings


async def _fake_stream_agent_reply(**_: Any) -> AsyncIterator[dict[str, Any]]:
    # Minimal async generator yielding two chunks
    yield {"type": "delta", "text_chunk": "Hello "}
    await asyncio.sleep(0)
    yield {"type": "delta", "text_chunk": "world"}


def test_public_stream_happy_path(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # Create a workspace via API
    create_ws = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        json={
            "handle": "my-workspace",
            "name": "My Workspace",
            "type": "demo",
            "tone": "friendly",
            "timezone": "UTC",
        },
        headers=superuser_token_headers,
    )
    assert create_ws.status_code == 200, create_ws.text

    # Create a public conversation
    conv = client.post(
        f"{settings.API_V1_STR}/public/conversations",
        json={"workspace_handle": "my-workspace"},
    )
    assert conv.status_code == 200, conv.text
    conversation_id = conv.json()["conversation_id"]

    # Post a user message
    msg = client.post(
        f"{settings.API_V1_STR}/public/conversations/{conversation_id}/messages",
        json={"role": "user", "content": "Hi"},
    )
    assert msg.status_code == 200, msg.text

    # Monkeypatch the agent streamer at the route import site
    import app.api.routes.public_conversations as pc_mod

    pc_mod.stream_agent_reply = _fake_stream_agent_reply  # type: ignore[attr-defined]

    # Stream
    with client.stream(
        "GET", f"{settings.API_V1_STR}/public/conversations/{conversation_id}/stream"
    ) as resp:
        assert resp.status_code == 200
        # Read a few lines to ensure SSE frames
        lines: list[str] = []
        for raw in resp.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            lines.append(line)
            if "event: message_end" in line:
                break

        # Ensure we saw delta and message_end events
        assert any("event: delta" in ln for ln in lines)
        assert any("event: message_end" in ln for ln in lines)


async def _failing_stream_agent_reply(**_: Any) -> AsyncIterator[dict[str, Any]]:
    # Simulate an exception during streaming
    yield {"type": "delta", "text_chunk": "Oops"}
    raise RuntimeError("boom")


def test_public_stream_error_path(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    create_ws = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        json={
            "handle": "ws-err",
            "name": "WS ERR",
            "type": "demo",
            "tone": "neutral",
            "timezone": "UTC",
        },
        headers=superuser_token_headers,
    )
    assert create_ws.status_code == 200

    conv = client.post(
        f"{settings.API_V1_STR}/public/conversations",
        json={"workspace_handle": "ws-err"},
        headers=superuser_token_headers,
    )
    conversation_id = conv.json()["conversation_id"]

    client.post(
        f"{settings.API_V1_STR}/public/conversations/{conversation_id}/messages",
        json={"role": "user", "content": "Hi"},
    )

    import app.api.routes.public_conversations as pc_mod

    pc_mod.stream_agent_reply = _failing_stream_agent_reply  # type: ignore[attr-defined]

    with client.stream(
        "GET", f"{settings.API_V1_STR}/public/conversations/{conversation_id}/stream"
    ) as resp:
        assert resp.status_code == 200
        seen = ""
        for raw in resp.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            seen += line + "\n"
            if "event: error" in line or "event: message_end" in line:
                break
        assert ("event: error" in seen) or ("event: message_end" in seen)


def test_public_stream_404(client: TestClient) -> None:
    bad_id = str(uuid4())
    resp = client.get(f"{settings.API_V1_STR}/public/conversations/{bad_id}/stream")
    assert resp.status_code == 404
