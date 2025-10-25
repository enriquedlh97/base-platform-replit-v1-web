from collections.abc import Sequence

from fastapi import APIRouter
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import Category, CategoryPublic

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryPublic])
def read_categories(
    session: SessionDep,
    current_user: CurrentUser,  # noqa: ARG001
) -> list[CategoryPublic]:
    """
    Retrieve all categories.
    """
    categories: Sequence[Category] = session.exec(select(Category)).all()
    return [CategoryPublic.model_validate(category) for category in categories]
