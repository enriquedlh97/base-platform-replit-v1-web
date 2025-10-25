import logging
from typing import Final

from fastapi import Request
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials

# Set up logger for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALGORITHM: Final[str] = "HS256"


class SupabaseBearer(HTTPBearer):
    """
    Custom security dependency for Supabase JWT token validation.

    This inherits from HTTPBearer to get automatic OpenAPI support and
    standard Bearer token parsing, while allowing custom validation logic.
    """

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(
            request
        )

        # If credentials is None and auto_error=False, super() already handled it
        if credentials is None:
            return None

        # The token is already validated as Bearer by super().__call__
        # You can add additional JWT validation logic here if needed
        # token: str = credentials.credentials

        # Example: Add custom validation logic here
        # if not self._is_valid_jwt(token):
        #     if self.auto_error:
        #         raise HTTPException(
        #             status_code=status.HTTP_401_UNAUTHORIZED,
        #             detail="Invalid JWT token",
        #             headers={"WWW-Authenticate": "Bearer"},
        #         )
        #     return None

        return credentials
