from unittest.mock import patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from httpx import Response
from sqlmodel import Session, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app import crud
from app.core.config import settings
from app.models import User, UserCreate
from app.tests.utils.supabase import SupabaseMock
from app.tests.utils.utils import random_email


def test_get_users_superuser_me(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # Mock Supabase admin client for the API call
    with SupabaseMock.patch_get_user_by_id(settings.FIRST_SUPERUSER):
        response = client.get(
            f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers
        )
        current_user = response.json()
        assert current_user
        assert current_user["is_active"] is True
        assert current_user["is_superuser"]
        assert current_user["email"] == settings.FIRST_SUPERUSER


def test_get_users_normal_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    # Mock Supabase admin client for the API call
    with SupabaseMock.patch_get_user_by_id(settings.EMAIL_TEST_USER):
        response = client.get(
            f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers
        )
        current_user = response.json()
        assert current_user
        assert current_user["is_active"] is True
        assert current_user["is_superuser"] is False
        assert current_user["email"] == settings.EMAIL_TEST_USER


def test_create_user_new_email(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    with (
        patch("app.utils.send_email", return_value=None),
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.SMTP_USER", "admin@example.com"),
    ):
        username: str = random_email()
        data: dict[str, str] = {"email": username}
        response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json=data,
        )
        assert 200 <= response.status_code < 300
        created_user = response.json()
        user: User | None = crud.get_user_by_email(session=db, email=username)
        assert user
        assert user.email == created_user["email"]


def test_get_existing_user(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    username: str = random_email()
    user_in: UserCreate = UserCreate(email=username)
    user: User = crud.create_user(session=db, user_create=user_in)
    user_id: UUID = user.id
    response = client.get(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
    )
    assert 200 <= response.status_code < 300
    api_user = response.json()
    existing_user: User | None = crud.get_user_by_email(session=db, email=username)
    assert existing_user
    assert existing_user.email == api_user["email"]


def test_get_existing_user_permissions_error(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/users/{uuid4()}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "The user doesn't have enough privileges"}


def test_create_user_existing_username(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    username: str = random_email()
    user_in: UserCreate = UserCreate(email=username)
    crud.create_user(session=db, user_create=user_in)
    data: dict[str, str] = {"email": username}
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=data,
    )
    created_user = response.json()
    assert response.status_code == 400
    assert "_id" not in created_user


def test_create_user_by_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    username: str = random_email()
    data: dict[str, str] = {"email": username}
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403


def test_retrieve_users(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    username: str = random_email()
    user_in: UserCreate = UserCreate(email=username)
    crud.create_user(session=db, user_create=user_in)

    username2: str = random_email()
    user_in2: UserCreate = UserCreate(email=username2)
    crud.create_user(session=db, user_create=user_in2)

    response = client.get(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers
    )
    all_users = response.json()

    assert len(all_users["data"]) > 1
    assert "count" in all_users
    for item in all_users["data"]:
        assert "email" in item


def test_update_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    full_name: str = "Updated Name"
    email: str = random_email()
    data: dict[str, str] = {"full_name": full_name, "email": email}
    response = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["email"] == email
    assert updated_user["full_name"] == full_name

    user_query: SelectOfScalar[User] = select(User).where(User.email == email)
    user_db: User | None = db.exec(user_query).first()
    assert user_db
    assert user_db.email == email
    assert user_db.full_name == full_name


def test_update_user_me_email_exists(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    username: str = random_email()
    user_in: UserCreate = UserCreate(email=username)
    user: User = crud.create_user(session=db, user_create=user_in)

    data: dict[str, str] = {"email": user.email}
    response = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "User with this email already exists"


def test_update_user(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    username: str = random_email()
    user_in: UserCreate = UserCreate(email=username)
    user: User = crud.create_user(session=db, user_create=user_in)

    data: dict[str, str] = {"full_name": "Updated_full_name"}
    response = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    updated_user = response.json()

    assert updated_user["full_name"] == "Updated_full_name"

    user_query: SelectOfScalar[User] = select(User).where(User.email == username)
    user_db: User | None = db.exec(user_query).first()
    db.refresh(user_db)
    assert user_db
    assert user_db.full_name == "Updated_full_name"


def test_update_user_not_exists(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data: dict[str, str] = {"full_name": "Updated_full_name"}
    response = client.patch(
        f"{settings.API_V1_STR}/users/{uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "The user with this id does not exist in the system"
    )


def test_update_user_email_exists(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    username: str = random_email()
    user_in: UserCreate = UserCreate(email=username)
    user: User = crud.create_user(session=db, user_create=user_in)

    username2: str = random_email()
    user_in2: UserCreate = UserCreate(email=username2)
    user2: User = crud.create_user(session=db, user_create=user_in2)

    data: dict[str, str] = {"email": user2.email}
    response = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "User with this email already exists"


def test_delete_user_me(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,  # noqa: ARG001
) -> None:
    """
    Test that regular users can delete their own accounts.

    TODO: This test needs to be updated when we implement Supabase user deletion.
    Currently only tests local database deletion, but we'll need to mock Supabase
    admin client calls when we implement dual-deletion approach.

    After fixing this, remember to remove the `# noqa: ARG001` from the function signature.
    """
    response = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    deleted_user = response.json()
    assert deleted_user["message"] == "User deleted successfully"


def test_delete_user_me_as_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=superuser_token_headers,
    )
    assert response.status_code == 403
    response = response.json()
    assert response["detail"] == "Super users are not allowed to delete themselves"


def test_delete_user_super_user(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    username: str = random_email()
    user_in: UserCreate = UserCreate(email=username)
    user: User = crud.create_user(session=db, user_create=user_in)
    user_id: UUID = user.id
    response = client.delete(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    deleted_user = response.json()
    assert deleted_user["message"] == "User deleted successfully"
    result: User | None = db.exec(select(User).where(User.id == user_id)).first()
    assert result is None


def test_delete_user_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/users/{uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_delete_user_current_super_user_error(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    super_user: User | None = crud.get_user_by_email(
        session=db, email=settings.FIRST_SUPERUSER
    )
    assert super_user
    user_id: UUID = super_user.id

    response = client.delete(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 403
    assert (
        response.json()["detail"] == "Super users are not allowed to delete themselves"
    )


def test_delete_user_without_privileges(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    username: str = random_email()
    user_in: UserCreate = UserCreate(email=username)
    user: User = crud.create_user(session=db, user_create=user_in)

    # Use the real Supabase flow; the normal_user fixture ensures the user exists.
    # The API should correctly reject the deletion based on privileges.
    response: Response = client.delete(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "The user doesn't have enough privileges"
