"""Workspace management routes."""

import logging
import re
from datetime import datetime, timezone
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile
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
from app.services.file_upload import FileUploadService

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
    """
    Get current user's workspace. Auto-creates one if it doesn't exist.
    This ensures users can immediately access features like the knowledge base
    without requiring a setup wizard.
    """
    statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.owner_id == current_user.id
    )
    workspace = session.exec(statement).first()

    if not workspace:
        # Auto-create workspace with default values
        # Generate handle from email or use UUID-based fallback
        base_handle = current_user.email.split("@")[0].lower()
        # Sanitize handle: only lowercase letters, numbers, and hyphens
        handle = re.sub(r"[^a-z0-9-]", "", base_handle)[:50]  # Limit length
        if not handle:  # Fallback if email produces invalid handle
            handle = f"user-{str(current_user.id)[:8]}"

        # Ensure handle is unique
        original_handle = handle
        counter = 1
        while True:
            handle_statement: SelectOfScalar[Workspace] = select(Workspace).where(
                Workspace.handle == handle
            )
            existing_handle = session.exec(handle_statement).first()
            if not existing_handle:
                break
            handle = f"{original_handle}-{counter}"
            counter += 1
            if counter > 1000:  # Safety limit
                # Fallback to UUID-based handle
                handle = f"user-{str(current_user.id).replace('-', '')[:20]}"
                break

        workspace = Workspace(
            owner_id=current_user.id,
            handle=handle,
            name="My Workspace",
            type="individual",
            tone="professional",
            timezone="UTC",
            is_active=True,
            knowledge_base=None,
            public_name=current_user.full_name or current_user.name,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        logger.info(
            f"Auto-created workspace for user {current_user.id} with handle '{handle}'"
        )

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


@router.post("/{workspace_id}/profile-image", response_model=WorkspacePublic)
async def upload_workspace_profile_image(
    workspace_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    profile_image: Annotated[UploadFile, File()],
) -> Any:
    """
    Upload profile image for a workspace.

    The image will be uploaded to Supabase Storage in the 'workspace-profiles' bucket
    and the workspace's profile_image_url will be updated in the database.

    Expected: multipart/form-data with 'profile_image' field containing the image file.
    Max size: 5MB. Allowed types: image/jpeg, image/png, image/webp.
    """
    workspace = get_workspace_or_404(workspace_id, session, current_user)

    # Log upload attempt
    logger.info(
        "Workspace profile image upload attempt: workspace=%s filename=%s content_type=%s size=%s",
        workspace_id,
        profile_image.filename,
        profile_image.content_type,
        profile_image.size if hasattr(profile_image, "size") else "unknown",
    )

    try:
        profile_image_url: str = await FileUploadService.upload_image_for_workspace(
            file=profile_image,
            workspace_id=workspace_id,
            bucket_name="avatars",
        )

        # Update the workspace's profile_image_url in the database
        workspace.profile_image_url = profile_image_url
        workspace.updated_at = datetime.now(timezone.utc)
        session.add(workspace)
        session.commit()
        session.refresh(workspace)

        return workspace

    except HTTPException:
        # Re-raise HTTPExceptions (validation errors, upload failures)
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.exception("Failed to process workspace profile image upload")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process profile image upload: {str(e)}",
        )
