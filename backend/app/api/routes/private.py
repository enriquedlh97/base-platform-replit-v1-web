from fastapi import APIRouter
from pydantic import BaseModel

from app import crud
from app.api.deps import SessionDep
from app.models import (
    User,
    UserCreate,
    UserPublic,
)

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    email: str
    full_name: str
    is_verified: bool = False


@router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> User:
    """
    Create a new user.
    """
    # Use the shared helper which creates the auth.users entry via Supabase
    # Admin API and waits for the trigger to insert the public.user row.

    user: User = crud.create_user(
        session=session, user_create=UserCreate(email=user_in.email)
    )

    # Update additional fields that are not part of the Supabase payload.
    if user_in.full_name:
        user.full_name = user_in.full_name
        session.add(user)
        session.commit()
        session.refresh(user)

    return user
