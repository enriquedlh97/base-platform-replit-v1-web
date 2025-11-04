"""Scheduling connector management routes."""

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
    SchedulingConnector,
    SchedulingConnectorCreate,
    SchedulingConnectorPublic,
    SchedulingConnectorUpdate,
    Workspace,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connectors", tags=["scheduling-connectors"])


def get_connector_or_404(
    connector_id: UUID, workspace_id: UUID, session: SessionDep
) -> SchedulingConnector:
    """Verify connector exists and belongs to workspace."""
    statement: SelectOfScalar[SchedulingConnector] = select(SchedulingConnector).where(
        SchedulingConnector.id == connector_id,
        SchedulingConnector.workspace_id == workspace_id,
    )
    connector = session.exec(statement).first()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    return connector


@router.get(
    "/workspaces/{workspace_id}", response_model=list[SchedulingConnectorPublic]
)
def get_workspace_connectors(
    workspace_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get all connectors for a workspace."""
    get_workspace_or_404(workspace_id, session, current_user)
    statement: SelectOfScalar[SchedulingConnector] = select(SchedulingConnector).where(
        SchedulingConnector.workspace_id == workspace_id
    )
    return list(session.exec(statement).all())


@router.post("/workspaces/{workspace_id}", response_model=SchedulingConnectorPublic)
def create_connector(
    workspace_id: UUID,
    session: SessionDep,
    connector_in: SchedulingConnectorCreate,
    current_user: CurrentUser,
) -> Any:
    """Create a new connector for a workspace."""
    get_workspace_or_404(workspace_id, session, current_user)

    db_connector = SchedulingConnector.model_validate(
        connector_in, update={"workspace_id": workspace_id}
    )
    session.add(db_connector)
    session.commit()
    session.refresh(db_connector)
    return db_connector


@router.get("/{connector_id}", response_model=SchedulingConnectorPublic)
def get_connector(
    connector_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get a connector by ID."""
    statement: SelectOfScalar[SchedulingConnector] = select(SchedulingConnector).where(
        SchedulingConnector.id == connector_id
    )
    connector = session.exec(statement).first()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    # Verify workspace ownership
    workspace_statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.id == connector.workspace_id
    )
    workspace = session.exec(workspace_statement).first()
    if workspace and workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")
    return connector


@router.patch("/{connector_id}", response_model=SchedulingConnectorPublic)
def update_connector(
    connector_id: UUID,
    session: SessionDep,
    connector_in: SchedulingConnectorUpdate,
    current_user: CurrentUser,
) -> Any:
    """Update a connector."""
    statement: SelectOfScalar[SchedulingConnector] = select(SchedulingConnector).where(
        SchedulingConnector.id == connector_id
    )
    connector = session.exec(statement).first()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    # Verify workspace ownership
    workspace_statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.id == connector.workspace_id
    )
    workspace = session.exec(workspace_statement).first()
    if workspace and workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")

    update_data = connector_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    connector.sqlmodel_update(update_data)
    session.add(connector)
    session.commit()
    session.refresh(connector)
    return connector


@router.post("/{connector_id}/activate", response_model=SchedulingConnectorPublic)
def activate_connector(
    connector_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Activate a connector (deactivates other connectors for the workspace)."""
    statement: SelectOfScalar[SchedulingConnector] = select(SchedulingConnector).where(
        SchedulingConnector.id == connector_id
    )
    connector = session.exec(statement).first()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    # Verify workspace ownership
    workspace_statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.id == connector.workspace_id
    )
    workspace = session.exec(workspace_statement).first()
    if workspace and workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")

    # Deactivate all other connectors for this workspace
    if workspace:
        deactivate_statement: SelectOfScalar[SchedulingConnector] = select(
            SchedulingConnector
        ).where(
            SchedulingConnector.workspace_id == workspace.id,
            SchedulingConnector.id != connector_id,
        )
        other_connectors = list(session.exec(deactivate_statement).all())
        for other_connector in other_connectors:
            other_connector.is_active = False
            other_connector.updated_at = datetime.now(timezone.utc)
            session.add(other_connector)

    # Activate this connector
    connector.is_active = True
    connector.updated_at = datetime.now(timezone.utc)
    session.add(connector)
    session.commit()
    session.refresh(connector)
    return connector


@router.post("/{connector_id}/deactivate", response_model=SchedulingConnectorPublic)
def deactivate_connector(
    connector_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Deactivate a connector."""
    statement: SelectOfScalar[SchedulingConnector] = select(SchedulingConnector).where(
        SchedulingConnector.id == connector_id
    )
    connector = session.exec(statement).first()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    # Verify workspace ownership
    workspace_statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.id == connector.workspace_id
    )
    workspace = session.exec(workspace_statement).first()
    if workspace and workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")

    connector.is_active = False
    connector.updated_at = datetime.now(timezone.utc)
    session.add(connector)
    session.commit()
    session.refresh(connector)
    return connector


@router.delete("/{connector_id}", response_model=Message)
def delete_connector(
    connector_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Delete a connector."""
    statement: SelectOfScalar[SchedulingConnector] = select(SchedulingConnector).where(
        SchedulingConnector.id == connector_id
    )
    connector = session.exec(statement).first()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    # Verify workspace ownership
    workspace_statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.id == connector.workspace_id
    )
    workspace = session.exec(workspace_statement).first()
    if workspace and workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your workspace")

    session.delete(connector)
    session.commit()
    return Message(message="Connector deleted successfully")
