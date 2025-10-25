import logging
from collections.abc import Sequence
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import func, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.supabase import supabase_admin_client
from app.models import (
    Message,
    User,
    UserCreate,
    UserPublic,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.services.file_upload import FileUploadService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    count_statement: SelectOfScalar[int] = select(func.count()).select_from(User)
    count: int = session.exec(count_statement).one()

    statement: SelectOfScalar[User] = select(User).offset(skip).limit(limit)
    users: Sequence[User] = session.exec(statement).all()

    return UsersPublic(data=users, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)

    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    # This deletes the user from Supabase Auth, and the database cascade
    # will handle deleting the local user and their items.
    supabase_admin_client.auth.admin.delete_user(str(current_user.id))
    return Message(message="User deleted successfully")


@router.post("/me/avatar", response_model=UserPublic)
async def upload_avatar_me(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    avatar: Annotated[UploadFile, File()],
) -> UserPublic:
    """
    Upload avatar for the current user.

    The avatar will be uploaded to Supabase Storage in the 'avatars' bucket
    and the user's avatar_url will be updated in the database.

    Expected: multipart/form-data with 'avatar' field containing the image file.
    Max size: 5MB. Allowed types: image/jpeg, image/png, image/webp.
    """
    # Log upload attempt
    logger.info(
        "Avatar upload attempt: user=%s filename=%s content_type=%s size=%s",
        current_user.id,
        avatar.filename,
        avatar.content_type,
        avatar.size if hasattr(avatar, "size") else "unknown",
    )

    try:
        avatar_url: str = await FileUploadService.upload_image_for_user(
            file=avatar,
            user_id=current_user.id,
            bucket_name="avatars",
        )

        # Update the user's avatar_url in the database
        current_user.avatar_url = avatar_url
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

        # Explicit conversion from User to UserPublic for type safety
        return UserPublic.model_validate(current_user)

    except HTTPException:
        # Re-raise HTTPExceptions (validation errors, upload failures)
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process avatar upload: {str(e)}",
        )


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = session.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """

    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: UUID
) -> Message:
    """
    Delete a user.
    """
    user: User | None = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    # This deletes the user from Supabase Auth, and the database cascade
    # will handle deleting the local user and their items.
    supabase_admin_client.auth.admin.delete_user(str(user.id))
    return Message(message="User deleted successfully")
