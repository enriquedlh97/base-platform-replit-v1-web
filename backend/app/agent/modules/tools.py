from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class SchedulingToolPort(Protocol):
    async def create_booking(self, *, args: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class NoopSchedulingTool(SchedulingToolPort):
    async def create_booking(self, *, args: dict[str, Any]) -> dict[str, Any]:
        # Stub implementation for MVP; returns a deterministic failure result
        return {
            "status": "failed",
            "error": {"code": "not_implemented", "message": "scheduling not available"},
        }
