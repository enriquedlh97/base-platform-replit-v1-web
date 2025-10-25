from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlmodel import select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import Category, Post, PostCreate, PostPublic, User, UserPublic
from app.services.file_upload import FileUploadService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/", response_model=list[PostPublic])
def read_posts(
    session: SessionDep,
    current_user: CurrentUser,  # noqa: ARG001
) -> list[PostPublic]:
    posts: Sequence[Post] = session.exec(select(Post)).all()

    # Convert to PostPublic with additional fields populated
    post_publics = []
    for post in posts:
        # Get category name if category_id exists
        category_name: str | None = None
        if post.category_id:
            category = session.exec(
                select(Category).where(Category.id == post.category_id)
            ).first()
            if category:
                category_name = category.name

        # Get user details for author
        author: UserPublic | None = None
        if post.user_id:
            user = session.exec(select(User).where(User.id == post.user_id)).first()
            if user:
                author = UserPublic.model_validate(user)

        # Create PostPublic with additional fields
        post_data = post.model_dump()
        post_data["category_name"] = category_name
        post_data["author"] = author
        post_publics.append(PostPublic.model_validate(post_data))

    return post_publics


@router.post("/", response_model=PostPublic)
async def create_post(
    session: SessionDep,
    current_user: CurrentUser,
    title: Annotated[str, Form(min_length=1, max_length=255)],
    content: Annotated[str | None, Form()] = None,
    category_id: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> PostPublic:
    """
    Create a new post with optional image upload.

    The image will be uploaded to Supabase Storage and the post will be created
    with the image URL. The user_id is automatically set from the authenticated user.

    File uploads are handled by the centralized FileUploadService for consistent
    validation, error handling, and storage management.
    """
    # Handle image upload if provided
    image_url: str | None = None
    if image:
        try:
            # Use FileUploadService for the complete upload flow
            image_url = await FileUploadService.upload_image_for_user(
                file=image,
                user_id=current_user.id,
                bucket_name="post-images",
                max_size_mb=5,
            )
        except HTTPException:
            # Re-raise HTTPExceptions (validation errors, upload failures)
            raise
        except Exception as e:
            # Handle unexpected errors
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process image: {str(e)}",
            )

    # Create post data
    post_data: PostCreate = PostCreate(
        title=title, content=content, category_id=category_id, image_url=image_url
    )

    # Create post in database
    try:
        # Create post using CRUD function (handles UUID conversion internally)
        post: Post = crud.create_post(
            session=session, post_in=post_data, user_id=current_user.id
        )

        # Create enhanced PostPublic with additional fields
        category_name: str | None = None
        if post.category_id:
            category = session.exec(
                select(Category).where(Category.id == post.category_id)
            ).first()
            if category:
                category_name = category.name

        author: UserPublic | None = None
        if post.user_id:
            user = session.exec(select(User).where(User.id == post.user_id)).first()
            if user:
                author = UserPublic.model_validate(user)

        post_dict = post.model_dump()
        post_dict["category_name"] = category_name
        post_dict["author"] = author
        return PostPublic.model_validate(post_dict)

    except ValueError as e:
        # Handle validation errors from CRUD function
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle other errors
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create post: {str(e)}",
        )
