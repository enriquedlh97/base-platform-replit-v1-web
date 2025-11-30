"""Context variables for passing workspace/conversation context through agent tools.

This module provides context variables that can be set by the agent graph
and accessed by tools during execution, without modifying tool signatures.
"""

from contextvars import ContextVar
from uuid import UUID

# Context variables for workspace and conversation IDs
# These are set by the agent graph before tool execution
workspace_id_context: ContextVar[UUID | None] = ContextVar(
    "workspace_id_context", default=None
)
conversation_id_context: ContextVar[UUID | None] = ContextVar(
    "conversation_id_context", default=None
)


def set_agent_context(
    workspace_id: UUID | None = None,
    conversation_id: UUID | None = None,
) -> None:
    """Set the current workspace and conversation context.

    Call this before invoking the agent to make context available to tools.

    Args:
        workspace_id: The workspace UUID
        conversation_id: The conversation UUID (optional)
    """
    workspace_id_context.set(workspace_id)
    conversation_id_context.set(conversation_id)


def get_workspace_id() -> UUID | None:
    """Get the current workspace ID from context.

    Returns:
        The workspace UUID if set, None otherwise.
    """
    return workspace_id_context.get()


def get_conversation_id() -> UUID | None:
    """Get the current conversation ID from context.

    Returns:
        The conversation UUID if set, None otherwise.
    """
    return conversation_id_context.get()


def clear_agent_context() -> None:
    """Clear the agent context after execution.

    Call this after agent execution completes to clean up context.
    """
    workspace_id_context.set(None)
    conversation_id_context.set(None)
