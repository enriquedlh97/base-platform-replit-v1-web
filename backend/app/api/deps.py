import logging
from collections.abc import Generator
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security.http import HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.core.security import ALGORITHM, SupabaseBearer
from app.models import TokenPayload, User

# set module-level logger
logger = logging.getLogger(__file__)

# Create instance of our custom security dependency
supabase_bearer = SupabaseBearer()


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def get_token_from_credentials(
    credentials: HTTPAuthorizationCredentials | None = Depends(supabase_bearer),
) -> str:
    """Extract the token string from HTTPAuthorizationCredentials."""
    if credentials is None:
        logger.warning("Missing authorization credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    return token


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(get_token_from_credentials)]


# TODO: This is not used anywhere, remove it
def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


# TODO: Refactor and rename to get_current_user
def get_current_user_from_supabase(session: SessionDep, token: TokenDep) -> User:
    try:
        if not settings.SUPABASE_AUTH_JWT_SECRET:
            raise ValueError("SUPABASE_AUTH_JWT_SECRET is not set")
        payload = jwt.decode(
            token,
            settings.SUPABASE_AUTH_JWT_SECRET,
            algorithms=[ALGORITHM],
            options={"verify_aud": False},
        )
        token_data = TokenPayload(**payload)
        user_id = UUID(token_data.sub)
    except (InvalidTokenError, ValidationError, ValueError) as e:
        logger.warning("JWT validation error: %s (type: %s)", e, type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user: User | None = session.get(User, user_id)
    if not user:
        logger.warning("User not found in database for user_id: %s", user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found in database",
        )

    if not user.is_active:
        logger.info("User %s is inactive", user.id)
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


# Replace CurrentUser dependency to validate Supabase JWTs instead of local tokens
# This assumes all authenticated routes will rely on Supabase-issued tokens.
# If you still need the original local auth flow, create a separate alias.

# TODO: Update after refactoring get_current_user_from_supabase -> get_current_user
CurrentUser = Annotated[User, Depends(get_current_user_from_supabase)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
