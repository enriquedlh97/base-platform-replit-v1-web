from fastapi.encoders import jsonable_encoder
from sqlmodel import Session

from app import crud
from app.models import User, UserCreate, UserUpdate
from app.tests.utils.utils import random_email


def test_create_user(db: Session) -> None:
    email = random_email()
    user_in = UserCreate(email=email)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.email == email


def test_authenticate_with_valid_jwt_token(db: Session) -> None:  # noqa: ARG001
    """Test that a valid JWT token can authenticate a user."""
    # TODO: Implement proper JWT authentication testing
    # This requires creating Supabase utilities for the test suite to:
    # 1. Generate valid Supabase JWT tokens for testing
    # 2. Mock Supabase user responses
    # 3. Test the full authentication flow through deps.py
    pass


def test_authenticate_with_invalid_jwt_token(db: Session) -> None:  # noqa: ARG001
    """Test that an invalid JWT token is properly rejected."""
    # TODO: Implement proper JWT authentication testing
    # This requires creating Supabase utilities for the test suite to:
    # 1. Generate invalid JWT tokens for testing
    # 2. Test token rejection scenarios
    # 3. Verify proper error handling in authentication flow
    pass


def test_authenticate_with_expired_jwt_token(db: Session) -> None:  # noqa: ARG001
    """Test that an expired JWT token is properly rejected."""
    # TODO: Implement proper JWT authentication testing
    # This requires creating Supabase utilities for the test suite to:
    # 1. Generate expired JWT tokens for testing
    # 2. Test expiration handling
    # 3. Verify proper error responses
    pass


def test_authenticate_with_malformed_jwt_token(db: Session) -> None:  # noqa: ARG001
    """Test that a malformed JWT token is properly rejected."""
    # TODO: Implement proper JWT authentication testing
    # This requires creating Supabase utilities for the test suite to:
    # 1. Test malformed token scenarios
    # 2. Verify proper error handling
    # 3. Test edge cases in token parsing
    pass


def test_get_user_by_email(db: Session) -> None:
    """Test that we can retrieve a user by email for JWT authentication."""
    email = random_email()
    user_in = UserCreate(email=email)
    user = crud.create_user(session=db, user_create=user_in)

    # Test successful lookup
    found_user = crud.get_user_by_email(session=db, email=email)
    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.email == email


def test_get_user_by_email_not_found(db: Session) -> None:
    """Test that get_user_by_email returns None for non-existent users."""
    non_existent_email = random_email()
    found_user = crud.get_user_by_email(session=db, email=non_existent_email)
    assert found_user is None


def test_get_user_by_email_case_sensitive(db: Session) -> None:
    """Test that email lookup is case sensitive."""
    email = random_email()
    user_in = UserCreate(email=email)
    _: User = crud.create_user(session=db, user_create=user_in)

    # Test with different case
    different_case_email = email.upper() if email.islower() else email.lower()
    found_user = crud.get_user_by_email(session=db, email=different_case_email)
    assert found_user is None


def test_check_if_user_is_active(db: Session) -> None:
    email = random_email()
    user_in = UserCreate(email=email)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.is_active is True  # Supabase trigger sets active


def test_check_if_user_is_active_inactive(db: Session) -> None:
    email = random_email()
    user_in = UserCreate(email=email, is_active=False)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.is_active is True  # Supabase trigger overrides and sets to True


def test_check_if_user_is_superuser(db: Session) -> None:
    email = random_email()
    user_in = UserCreate(email=email, is_superuser=True)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.is_superuser is False  # Supabase trigger defaults to False


def test_check_if_user_is_superuser_normal_user(db: Session) -> None:
    username = random_email()
    user_in = UserCreate(email=username)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.is_superuser is False


def test_get_user(db: Session) -> None:
    username = random_email()
    user_in = UserCreate(email=username, is_superuser=True)
    user = crud.create_user(session=db, user_create=user_in)
    user_2 = db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_update_user(db: Session) -> None:
    email = random_email()
    user_in = UserCreate(email=email, is_superuser=True)
    user = crud.create_user(session=db, user_create=user_in)
    user_in_update = UserUpdate(is_superuser=False)
    if user.id is not None:
        crud.update_user(session=db, db_user=user, user_in=user_in_update)
    user_2 = db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert user_2.is_superuser is False
