from typing import Any


def encode_sse_event(event: str, data: dict[str, Any]) -> bytes:
    """Encode an SSE event line with a JSON payload.

    We keep it minimal to avoid extra deps.
    """
    # Lazy import to avoid heavy deps at import time
    import json

    payload = json.dumps(data, ensure_ascii=False)
    # event: <name>\n data: <json>\n\n
    return f"event: {event}\n".encode() + f"data: {payload}\n\n".encode()
