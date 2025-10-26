"""Workspace management routes."""

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
    Message,
    SchedulingConnector,
    Workspace,
    WorkspaceCreate,
    WorkspacePublic,
    WorkspaceService,
    WorkspaceUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def get_workspace_or_404(
    workspace_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Workspace:
    """Verify workspace exists and user has access."""
    statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.id == workspace_id
    )
    workspace = session.exec(statement).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")
    return workspace


@router.post("/", response_model=WorkspacePublic)
def create_workspace(
    *, session: SessionDep, workspace_in: WorkspaceCreate, current_user: CurrentUser
) -> Any:
    """
    Create a new workspace. Each user can have exactly one workspace.
    """
    # Check if user already has a workspace
    existing_statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.owner_id == current_user.id
    )
    existing = session.exec(existing_statement).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already has a workspace")

    # Check if handle is already taken
    handle_statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.handle == workspace_in.handle
    )
    existing_handle = session.exec(handle_statement).first()
    if existing_handle:
        raise HTTPException(
            status_code=409,
            detail=f"Handle '{workspace_in.handle}' is already taken",
        )

    db_workspace = Workspace.model_validate(
        workspace_in, update={"owner_id": current_user.id}
    )
    session.add(db_workspace)
    session.commit()
    session.refresh(db_workspace)
    return db_workspace


@router.get("/me", response_model=WorkspacePublic)
def get_my_workspace(*, session: SessionDep, current_user: CurrentUser) -> Any:
    """Get current user's workspace."""
    statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.owner_id == current_user.id
    )
    workspace = session.exec(statement).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="No workspace found")
    return workspace


@router.get("/{workspace_id}", response_model=WorkspacePublic)
def get_workspace(
    workspace_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get workspace by ID."""
    workspace = get_workspace_or_404(workspace_id, session, current_user)
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspacePublic)
def update_workspace(
    workspace_id: UUID,
    session: SessionDep,
    workspace_in: WorkspaceUpdate,
    current_user: CurrentUser,
) -> Any:
    """Update workspace."""
    workspace = get_workspace_or_404(workspace_id, session, current_user)

    # Check if handle is being changed and if new handle is available
    if workspace_in.handle and workspace_in.handle != workspace.handle:
        handle_statement: SelectOfScalar[Workspace] = select(Workspace).where(
            Workspace.handle == workspace_in.handle
        )
        existing_handle = session.exec(handle_statement).first()
        if existing_handle:
            raise HTTPException(
                status_code=409,
                detail=f"Handle '{workspace_in.handle}' is already taken",
            )

    update_data = workspace_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    workspace.sqlmodel_update(update_data)
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


@router.delete("/{workspace_id}", response_model=Message)
def delete_workspace(
    workspace_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Delete workspace."""
    workspace = get_workspace_or_404(workspace_id, session, current_user)

    # Check for dependent records
    service_statement: SelectOfScalar[WorkspaceService] = select(
        WorkspaceService
    ).where(WorkspaceService.workspace_id == workspace_id)
    services = list(session.exec(service_statement).all())

    connector_statement: SelectOfScalar[SchedulingConnector] = select(
        SchedulingConnector
    ).where(SchedulingConnector.workspace_id == workspace_id)
    connectors = list(session.exec(connector_statement).all())

    conversation_statement: SelectOfScalar[Conversation] = select(Conversation).where(
        Conversation.workspace_id == workspace_id
    )
    conversations = list(session.exec(conversation_statement).all())

    if services or connectors or conversations:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete workspace with dependent records. Delete them first.",
        )

    session.delete(workspace)
    session.commit()
    return Message(message="Workspace deleted successfully")
