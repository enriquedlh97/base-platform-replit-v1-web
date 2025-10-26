"""Utility functions for creating test workspaces."""

from uuid import UUID

from sqlmodel import Session

from app.models import Workspace


def create_random_workspace(
    session: Session, owner_id: UUID, handle: str = "test-workspace"
) -> Workspace:
    """Create a workspace for testing."""
    workspace = Workspace(
        owner_id=owner_id,
        handle=handle,
        name="Test Workspace",
        type="individual",
        tone="professional",
        timezone="UTC",
    )
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace
