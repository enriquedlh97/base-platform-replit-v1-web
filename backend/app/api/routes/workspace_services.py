"""Workspace services management routes."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlmodel import select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.workspaces import get_workspace_or_404
from app.models import (
    Message,
    Workspace,
    WorkspaceService,
    WorkspaceServiceCreate,
    WorkspaceServicePublic,
    WorkspaceServiceUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspace-services", tags=["workspace-services"])


def get_service_or_404(
    service_id: UUID, workspace_id: UUID, session: SessionDep
) -> WorkspaceService:
    """Verify service exists and belongs to workspace."""
    statement: SelectOfScalar[WorkspaceService] = select(WorkspaceService).where(
        WorkspaceService.id == service_id, WorkspaceService.workspace_id == workspace_id
    )
    service = session.exec(statement).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.get("/workspaces/{workspace_id}", response_model=list[WorkspaceServicePublic])
def get_workspace_services(
    workspace_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get all services for a workspace."""
    get_workspace_or_404(workspace_id, session, current_user)
    statement: SelectOfScalar[WorkspaceService] = (
        select(WorkspaceService)
        .where(WorkspaceService.workspace_id == workspace_id)
        .order_by("sort_order")
    )
    return list(session.exec(statement).all())


@router.post("/workspaces/{workspace_id}", response_model=WorkspaceServicePublic)
def create_workspace_service(
    workspace_id: UUID,
    session: SessionDep,
    service_in: WorkspaceServiceCreate,
    current_user: CurrentUser,
) -> Any:
    """Create a new service for a workspace."""
    get_workspace_or_404(workspace_id, session, current_user)

    db_service = WorkspaceService.model_validate(
        service_in, update={"workspace_id": workspace_id}
    )
    session.add(db_service)
    session.commit()
    session.refresh(db_service)
    return db_service


@router.get("/{service_id}", response_model=WorkspaceServicePublic)
def get_service(
    service_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get a service by ID."""
    service = session.get(WorkspaceService, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Verify workspace ownership
    workspace = session.get(Workspace, service.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")
    return service


@router.patch("/{service_id}", response_model=WorkspaceServicePublic)
def update_service(
    service_id: UUID,
    session: SessionDep,
    service_in: WorkspaceServiceUpdate,
    current_user: CurrentUser,
) -> Any:
    """Update a service."""
    service = session.get(WorkspaceService, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Verify workspace ownership
    workspace = session.get(Workspace, service.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")

    update_data = service_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    service.sqlmodel_update(update_data)
    session.add(service)
    session.commit()
    session.refresh(service)
    return service


@router.delete("/{service_id}", response_model=Message)
def delete_service(
    service_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Delete a service."""
    service = session.get(WorkspaceService, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Verify workspace ownership
    workspace = session.get(Workspace, service.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")

    session.delete(service)
    session.commit()
    return Message(message="Service deleted successfully")
