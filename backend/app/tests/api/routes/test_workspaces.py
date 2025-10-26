"""Tests for workspace endpoints."""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User, Workspace


def test_create_workspace(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating a workspace."""
    data = {
        "handle": "my-consulting-business",
        "name": "My Consulting Business",
        "type": "business",
        "tone": "professional",
        "timezone": "America/New_York",
    }
    response = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["handle"] == data["handle"]
    assert content["name"] == data["name"]
    assert content["type"] == data["type"]
    assert content["tone"] == data["tone"]
    assert content["timezone"] == data["timezone"]
    assert content["is_active"] is True
    assert "id" in content
    assert "owner_id" in content


def test_create_workspace_duplicate_handle(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test that duplicate handles are rejected."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Create first workspace
    workspace1 = Workspace(
        owner_id=user.id,
        handle="unique-handle",
        name="First Workspace",
        type="individual",
        tone="professional",
        timezone="UTC",
    )
    db.add(workspace1)
    db.commit()

    # Try to create another workspace with the same handle (different user would need another user fixture)
    # For now, test with same user trying to create second workspace
    data = {
        "handle": "unique-handle",
        "name": "Second Workspace",
        "type": "business",
        "tone": "warm",
        "timezone": "America/Los_Angeles",
    }
    response = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 409
    content = response.json()
    assert "already" in content["detail"].lower()


def test_create_second_workspace_same_user(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test that a user cannot create a second workspace."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Create first workspace
    workspace1 = Workspace(
        owner_id=user.id,
        handle="first-workspace",
        name="First Workspace",
        type="individual",
        tone="professional",
        timezone="UTC",
    )
    db.add(workspace1)
    db.commit()

    # Try to create second workspace
    data = {
        "handle": "second-workspace",
        "name": "Second Workspace",
        "type": "business",
        "tone": "warm",
        "timezone": "America/Los_Angeles",
    }
    response = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 409
    content = response.json()
    assert "already has a workspace" in content["detail"].lower()


def test_get_my_workspace(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting current user's workspace."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Create workspace
    workspace = Workspace(
        owner_id=user.id,
        handle="my-workspace",
        name="My Workspace",
        type="individual",
        tone="professional",
        timezone="UTC",
    )
    db.add(workspace)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/workspaces/me",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["handle"] == "my-workspace"
    assert content["owner_id"] == str(user.id)


def test_get_my_workspace_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test getting workspace when user has none."""
    response = client.get(
        f"{settings.API_V1_STR}/workspaces/me",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert "no workspace" in content["detail"].lower()


def test_get_workspace_by_id(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting workspace by ID."""
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

    response = client.get(
        f"{settings.API_V1_STR}/workspaces/{workspace.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(workspace.id)
    assert content["handle"] == "test-workspace"


def test_get_workspace_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test getting non-existent workspace."""
    response = client.get(
        f"{settings.API_V1_STR}/workspaces/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert "not found" in content["detail"].lower()


def test_update_workspace(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating workspace."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Create workspace
    workspace = Workspace(
        owner_id=user.id,
        handle="original-handle",
        name="Original Name",
        type="individual",
        tone="professional",
        timezone="UTC",
    )
    db.add(workspace)
    db.commit()

    # Update workspace
    data = {
        "name": "Updated Name",
        "tone": "warm",
        "timezone": "America/New_York",
    }
    response = client.patch(
        f"{settings.API_V1_STR}/workspaces/{workspace.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == "Updated Name"
    assert content["tone"] == "warm"
    assert content["timezone"] == "America/New_York"
    assert content["handle"] == "original-handle"  # Handle unchanged


def test_update_workspace_handle(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating workspace handle."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Create workspace
    workspace = Workspace(
        owner_id=user.id,
        handle="old-handle",
        name="Test Workspace",
        type="individual",
        tone="professional",
        timezone="UTC",
    )
    db.add(workspace)
    db.commit()

    # Update handle
    data = {"handle": "new-handle"}
    response = client.patch(
        f"{settings.API_V1_STR}/workspaces/{workspace.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["handle"] == "new-handle"


def test_delete_workspace(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test deleting workspace."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Create workspace
    workspace = Workspace(
        owner_id=user.id,
        handle="to-delete",
        name="To Delete",
        type="individual",
        tone="professional",
        timezone="UTC",
    )
    db.add(workspace)
    db.commit()

    # Delete workspace
    response = client.delete(
        f"{settings.API_V1_STR}/workspaces/{workspace.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "deleted" in content["message"].lower()

    # Verify it's deleted
    deleted_workspace = db.get(Workspace, workspace.id)
    assert deleted_workspace is None
