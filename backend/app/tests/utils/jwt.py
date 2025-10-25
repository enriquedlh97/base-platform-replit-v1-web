import datetime
from datetime import timedelta
from uuid import UUID

import jwt

from app.core import security
from app.core.config import settings
from app.tests.utils.utils import random_email


def generate_test_jwt(
    user_id: UUID, *, email: str | None = None, expiration_minutes: int = 60
) -> str:
    """
    Generate a valid Supabase JWT token for testing.

    Args:
        user_id: The user ID to include in the token
        email: Optional email to include in the token (defaults to random email)
        expiration_minutes: Token expiration time in minutes (default: 60)

    Returns:
        A signed JWT token that will pass Supabase validation
    """
    now: datetime.datetime = datetime.datetime.now(datetime.UTC)

    # Use provided email or generate a random one
    user_email: str = email or random_email()

    # Build payload with standard Supabase claims
    payload: dict[str, str | int] = {
        "sub": str(user_id),
        "email": user_email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expiration_minutes)).timestamp()),
        "role": "authenticated",
    }

    # Sign with the same secret Supabase uses
    return jwt.encode(
        payload, settings.SUPABASE_AUTH_JWT_SECRET, algorithm=security.ALGORITHM
    )
