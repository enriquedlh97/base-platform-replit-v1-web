"""Tests for scheduling connector endpoints."""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import SchedulingConnector, User


def test_create_connector(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a scheduling connector."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Ensure workspace exists via endpoint (auto-creates if missing)
    me = client.get(
        f"{settings.API_V1_STR}/workspaces/me", headers=normal_user_token_headers
    )
    assert me.status_code == 200
    workspace_id = me.json()["id"]

    # Create connector
    data = {
        "type": "calendly",
        "config": {
            "calendly_url": "https://calendly.com/testuser",
            "meeting_types": ["15min", "30min"],
            "timezone": "America/New_York",
        },
        "is_active": False,
    }
    response = client.post(
        f"{settings.API_V1_STR}/connectors/workspaces/{workspace_id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["type"] == data["type"]
    assert content["config"] == data["config"]
    assert content["is_active"] is False
    assert content["workspace_id"] == str(workspace_id)
    assert "id" in content


def test_list_connectors(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test listing connectors for a workspace."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    me = client.get(
        f"{settings.API_V1_STR}/workspaces/me", headers=normal_user_token_headers
    )
    assert me.status_code == 200
    workspace_id = me.json()["id"]

    # Get initial count to account for any existing connectors
    initial_response = client.get(
        f"{settings.API_V1_STR}/connectors/workspaces/{workspace_id}",
        headers=normal_user_token_headers,
    )
    assert initial_response.status_code == 200
    initial_count = len(initial_response.json())

    # Create connectors
    connector1 = SchedulingConnector(
        workspace_id=workspace_id,
        type="calendly",
        config={"url": "https://calendly.com/user1"},
        is_active=True,
    )
    connector2 = SchedulingConnector(
        workspace_id=workspace_id,
        type="square",
        config={"api_key": "test_key"},
        is_active=False,
    )
    db.add(connector1)
    db.add(connector2)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/connectors/workspaces/{workspace_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    # Should have initial count plus the 2 we just created
    assert len(content) == initial_count + 2
    # Verify our new connectors are in the list
    connector_types = {c["type"] for c in content}
    assert "calendly" in connector_types
    assert "square" in connector_types


def test_activate_connector(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test activating a connector."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    me = client.get(
        f"{settings.API_V1_STR}/workspaces/me", headers=normal_user_token_headers
    )
    assert me.status_code == 200
    workspace_id = me.json()["id"]

    # Create connector
    connector = SchedulingConnector(
        workspace_id=workspace_id,
        type="calendly",
        config={"url": "https://calendly.com/testuser"},
        is_active=False,
    )
    db.add(connector)
    db.commit()

    # Activate connector
    response = client.post(
        f"{settings.API_V1_STR}/connectors/{connector.id}/activate",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["is_active"] is True
    assert content["id"] == str(connector.id)


def test_activate_connector_deactivates_others(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test that activating a connector deactivates other connectors."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    me = client.get(
        f"{settings.API_V1_STR}/workspaces/me", headers=normal_user_token_headers
    )
    assert me.status_code == 200
    workspace_id = me.json()["id"]

    # Create two connectors
    connector1 = SchedulingConnector(
        workspace_id=workspace_id,
        type="calendly",
        config={"url": "https://calendly.com/user1"},
        is_active=True,
    )
    connector2 = SchedulingConnector(
        workspace_id=workspace_id,
        type="square",
        config={"api_key": "test_key"},
        is_active=False,
    )
    db.add(connector1)
    db.add(connector2)
    db.commit()

    # Activate connector2
    response = client.post(
        f"{settings.API_V1_STR}/connectors/{connector2.id}/activate",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["is_active"] is True

    # Verify connector1 is deactivated
    db.refresh(connector1)
    assert connector1.is_active is False


def test_deactivate_connector(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test deactivating a connector."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    me = client.get(
        f"{settings.API_V1_STR}/workspaces/me", headers=normal_user_token_headers
    )
    assert me.status_code == 200
    workspace_id = me.json()["id"]

    # Create active connector
    connector = SchedulingConnector(
        workspace_id=workspace_id,
        type="calendly",
        config={"url": "https://calendly.com/testuser"},
        is_active=True,
    )
    db.add(connector)
    db.commit()

    # Deactivate connector
    response = client.post(
        f"{settings.API_V1_STR}/connectors/{connector.id}/deactivate",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["is_active"] is False


def test_delete_connector(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test deleting a connector."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Use existing workspace (auto-created by /workspaces/me endpoint)
    # This avoids unique constraint violations since each user can only have one workspace
    me = client.get(
        f"{settings.API_V1_STR}/workspaces/me", headers=normal_user_token_headers
    )
    assert me.status_code == 200
    workspace_id = me.json()["id"]

    # Create connector
    connector = SchedulingConnector(
        workspace_id=workspace_id,
        type="calendly",
        config={"url": "https://calendly.com/testuser"},
        is_active=False,
    )
    db.add(connector)
    db.commit()

    # Delete connector
    response = client.delete(
        f"{settings.API_V1_STR}/connectors/{connector.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "deleted" in content["message"].lower()

    # Verify it's deleted
    deleted_connector = db.get(SchedulingConnector, connector.id)
    assert deleted_connector is None


def test_connector_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test accessing non-existent connector."""
    response = client.get(
        f"{settings.API_V1_STR}/connectors/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert "not found" in content["detail"].lower()
