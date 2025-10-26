"""Tests for workspace service endpoints."""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User, Workspace, WorkspaceService


def test_create_workspace_service(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a workspace service."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Create workspace
    workspace = Workspace(
        owner_id=user.id,
        handle="test-workspace",
        name="Test Workspace",
        type="individual",
        tone="professional",
        timezone="UTC",
    )
    db.add(workspace)
    db.commit()

    # Create service
    data = {
        "name": "Strategy Consultation",
        "description": "60-minute strategy session",
        "format": "Video Call",
        "duration_minutes": 60,
        "starting_price": 150.00,
        "is_active": True,
        "sort_order": 1,
    }
    response = client.post(
        f"{settings.API_V1_STR}/workspace-services/workspaces/{workspace.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert content["format"] == data["format"]
    assert content["duration_minutes"] == data["duration_minutes"]
    assert float(content["starting_price"]) == data["starting_price"]
    assert content["workspace_id"] == str(workspace.id)
    assert "id" in content


def test_list_workspace_services(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test listing workspace services."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Create workspace
    workspace = Workspace(
        owner_id=user.id,
        handle="test-workspace",
        name="Test Workspace",
        type="individual",
        tone="professional",
        timezone="UTC",
    )
    db.add(workspace)
    db.commit()

    # Create services
    service1 = WorkspaceService(
        workspace_id=workspace.id,
        name="Service 1",
        description="First service",
        format="Video",
        duration_minutes=30,
        is_active=True,
        sort_order=1,
    )
    service2 = WorkspaceService(
        workspace_id=workspace.id,
        name="Service 2",
        description="Second service",
        format="In-person",
        duration_minutes=60,
        is_active=True,
        sort_order=2,
    )
    db.add(service1)
    db.add(service2)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/workspace-services/workspaces/{workspace.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 2
    assert content[0]["name"] == "Service 1"
    assert content[1]["name"] == "Service 2"


def test_get_service_by_id(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting a service by ID."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Create workspace and service
    workspace = Workspace(
        owner_id=user.id,
        handle="test-workspace",
        name="Test Workspace",
        type="individual",
        tone="professional",
        timezone="UTC",
    )
    db.add(workspace)
    db.commit()

    service = WorkspaceService(
        workspace_id=workspace.id,
        name="Test Service",
        description="Test description",
        format="Video",
        duration_minutes=45,
        is_active=True,
        sort_order=1,
    )
    db.add(service)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/workspace-services/{service.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(service.id)
    assert content["name"] == "Test Service"


def test_update_service(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a service."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Create workspace and service
    workspace = Workspace(
        owner_id=user.id,
        handle="test-workspace",
        name="Test Workspace",
        type="individual",
        tone="professional",
        timezone="UTC",
    )
    db.add(workspace)
    db.commit()

    service = WorkspaceService(
        workspace_id=workspace.id,
        name="Original Name",
        description="Original description",
        format="Video",
        duration_minutes=30,
        is_active=True,
        sort_order=1,
    )
    db.add(service)
    db.commit()

    # Update service
    data = {
        "name": "Updated Name",
        "description": "Updated description",
        "duration_minutes": 60,
    }
    response = client.patch(
        f"{settings.API_V1_STR}/workspace-services/{service.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == "Updated Name"
    assert content["description"] == "Updated description"
    assert content["duration_minutes"] == 60


def test_delete_service(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test deleting a service."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Create workspace and service
    workspace = Workspace(
        owner_id=user.id,
        handle="test-workspace",
        name="Test Workspace",
        type="individual",
        tone="professional",
        timezone="UTC",
    )
    db.add(workspace)
    db.commit()

    service = WorkspaceService(
        workspace_id=workspace.id,
        name="To Delete",
        description="Will be deleted",
        format="Video",
        duration_minutes=30,
        is_active=True,
        sort_order=1,
    )
    db.add(service)
    db.commit()

    # Delete service
    response = client.delete(
        f"{settings.API_V1_STR}/workspace-services/{service.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "deleted" in content["message"].lower()

    # Verify it's deleted
    deleted_service = db.get(WorkspaceService, service.id)
    assert deleted_service is None


def test_service_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test accessing non-existent service."""
    response = client.get(
        f"{settings.API_V1_STR}/workspace-services/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert "not found" in content["detail"].lower()
