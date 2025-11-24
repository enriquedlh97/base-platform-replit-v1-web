from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.services.cua_scheduling_tool import CUASchedulingTool


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


def get_scheduling_tool() -> SchedulingToolPort:
    """Get the appropriate scheduling tool implementation.

    Returns CUASchedulingTool if CUA is available, otherwise NoopSchedulingTool.
    """
    # For now, always use CUA tool. In the future, this could check config/env
    return CUASchedulingTool()
