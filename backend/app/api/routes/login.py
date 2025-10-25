from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.api.deps import (
    CurrentUser,
    get_current_user_from_supabase,
)
from app.models import UserPublic

router = APIRouter(tags=["login"])


@router.post("/login/test-token", response_model=UserPublic)
def test_token(
    current_user: Annotated[CurrentUser, Depends(get_current_user_from_supabase)],
) -> Any:
    """
    Test access token
    """
    return current_user
