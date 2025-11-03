"""Tests for conversation endpoints."""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Conversation, ConversationMessage, User, Workspace


def test_create_conversation(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a conversation."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Ensure workspace exists via endpoint (auto-creates if missing)
    me = client.get(
        f"{settings.API_V1_STR}/workspaces/me", headers=normal_user_token_headers
    )
    assert me.status_code == 200
    workspace_id = me.json()["id"]

    # Create conversation
    data = {
        "visitor_name": "John Doe",
        "visitor_email": "john@example.com",
        "channel": "web",
        "status": "active",
    }
    response = client.post(
        f"{settings.API_V1_STR}/conversations/workspaces/{workspace_id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["visitor_name"] == data["visitor_name"]
    assert content["visitor_email"] == data["visitor_email"]
    assert content["channel"] == data["channel"]
    assert content["status"] == data["status"]
    assert content["workspace_id"] == str(workspace_id)
    assert "id" in content


def test_list_conversations(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test listing conversations for a workspace."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    me = client.get(
        f"{settings.API_V1_STR}/workspaces/me", headers=normal_user_token_headers
    )
    assert me.status_code == 200
    workspace_id = me.json()["id"]

    # Create conversations
    conv1 = Conversation(
        workspace_id=workspace_id,
        visitor_name="Alice",
        visitor_email="alice@example.com",
        channel="web",
        status="active",
    )
    conv2 = Conversation(
        workspace_id=workspace_id,
        visitor_name="Bob",
        visitor_email="bob@example.com",
        channel="instagram",
        status="completed",
    )
    db.add(conv1)
    db.add(conv2)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/conversations/workspaces/{workspace_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 2


def test_get_conversation_by_id(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting a conversation by ID."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    me = client.get(
        f"{settings.API_V1_STR}/workspaces/me", headers=normal_user_token_headers
    )
    assert me.status_code == 200
    workspace_id = me.json()["id"]

    conversation = Conversation(
        workspace_id=workspace_id,
        visitor_name="Test User",
        visitor_email="test@example.com",
        channel="web",
        status="active",
    )
    db.add(conversation)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/conversations/{conversation.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(conversation.id)
    assert content["visitor_name"] == "Test User"


def test_update_conversation_status(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating conversation status."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    me = client.get(
        f"{settings.API_V1_STR}/workspaces/me", headers=normal_user_token_headers
    )
    assert me.status_code == 200
    workspace_id = me.json()["id"]

    conversation = Conversation(
        workspace_id=workspace_id,
        visitor_name="Test User",
        visitor_email="test@example.com",
        channel="web",
        status="active",
    )
    db.add(conversation)
    db.commit()

    # Update status
    data = {"status": "completed"}
    response = client.patch(
        f"{settings.API_V1_STR}/conversations/{conversation.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["status"] == "completed"


def test_add_message_to_conversation(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test adding a message to a conversation."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    me = client.get(
        f"{settings.API_V1_STR}/workspaces/me", headers=normal_user_token_headers
    )
    assert me.status_code == 200
    workspace_id = me.json()["id"]

    conversation = Conversation(
        workspace_id=workspace_id,
        visitor_name="Test User",
        visitor_email="test@example.com",
        channel="web",
        status="active",
    )
    db.add(conversation)
    db.commit()

    # Add message
    data = {"content": "Hello, I need help with scheduling.", "role": "user"}
    response = client.post(
        f"{settings.API_V1_STR}/conversations/{conversation.id}/messages",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["content"] == data["content"]
    assert content["role"] == data["role"]
    assert content["conversation_id"] == str(conversation.id)
    assert "id" in content


def test_list_messages_in_conversation(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test listing messages in a conversation."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # Create workspace and conversation
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

    conversation = Conversation(
        workspace_id=workspace.id,
        visitor_name="Test User",
        visitor_email="test@example.com",
        channel="web",
        status="active",
    )
    db.add(conversation)
    db.commit()

    # Add messages
    msg1 = ConversationMessage(
        conversation_id=conversation.id, content="Hello", role="user"
    )
    msg2 = ConversationMessage(
        conversation_id=conversation.id,
        content="Hi! How can I help?",
        role="assistant",
    )
    db.add(msg1)
    db.add(msg2)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/conversations/{conversation.id}/messages",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 2
    assert content[0]["role"] == "user"
    assert content[1]["role"] == "assistant"


def test_delete_conversation(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test deleting a conversation."""
    # Get the user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    me = client.get(
        f"{settings.API_V1_STR}/workspaces/me", headers=normal_user_token_headers
    )
    assert me.status_code == 200
    workspace_id = me.json()["id"]

    conversation = Conversation(
        workspace_id=workspace_id,
        visitor_name="Test User",
        visitor_email="test@example.com",
        channel="web",
        status="active",
    )
    db.add(conversation)
    db.commit()

    # Delete conversation
    response = client.delete(
        f"{settings.API_V1_STR}/conversations/{conversation.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "deleted" in content["message"].lower()

    # Verify it's deleted
    deleted_conversation = db.get(Conversation, conversation.id)
    assert deleted_conversation is None


def test_conversation_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test accessing non-existent conversation."""
    response = client.get(
        f"{settings.API_V1_STR}/conversations/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert "not found" in content["detail"].lower()
