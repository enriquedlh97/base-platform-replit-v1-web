from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.models import User, UserCreate
from app.tests.utils.utils import random_email


def user_authentication_headers(
    *,
    client: TestClient,  # noqa: ARG001
    email: str,  # noqa: ARG001
    password: str,  # noqa: ARG001
) -> dict[str, str]:
    """
    TODO: Replace with JWT-based authentication
    This function previously used password authentication which has been removed.
    Need to implement JWT token generation for testing.
    """
    # TODO: Implement JWT-based authentication headers
    # This requires creating Supabase utilities for the test suite to:
    # 1. Generate valid Supabase JWT tokens for testing
    # 2. Mock Supabase user responses
    # 3. Return proper Authorization headers with JWT tokens
    raise NotImplementedError(
        "Password authentication removed. Implement JWT authentication."
    )


def create_random_user(db: Session) -> User:
    """Create a random user without password (for JWT authentication)."""
    email = random_email()
    user_in = UserCreate(email=email)
    user = crud.create_user(session=db, user_create=user_in)
    return user


def authentication_token_from_email(*, email: str, db: Session) -> dict[str, str]:
    """
    TODO: Replace with JWT-based authentication
    Return a valid JWT token for the user with given email.

    If the user doesn't exist it is created first.
    """
    # TODO: Implement JWT-based authentication token generation
    # This requires creating Supabase utilities for the test suite to:
    # 1. Generate valid Supabase JWT tokens for testing
    # 2. Mock Supabase user responses
    # 3. Handle user creation if needed
    # 4. Return proper Authorization headers with JWT tokens

    # For now, ensure user exists in database
    user = crud.get_user_by_email(session=db, email=email)
    if not user:
        user_in_create = UserCreate(email=email)
        user = crud.create_user(session=db, user_create=user_in_create)

    raise NotImplementedError(
        "Password authentication removed. Implement JWT authentication."
    )
