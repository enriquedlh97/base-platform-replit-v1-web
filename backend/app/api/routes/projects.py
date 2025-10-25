import logging
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, status

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import Project, ProjectCreate, ProjectPublic

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectPublic)
async def create_project(
    session: SessionDep,
    current_user: CurrentUser,
    name: Annotated[str, Form(min_length=1, max_length=255)],
    description: Annotated[str | None, Form()] = None,
    number_of_days: Annotated[int | None, Form(ge=1, le=200)] = None,
    paid_project: Annotated[bool, Form()] = False,
    street: Annotated[str | None, Form()] = None,
    us_zip_code: Annotated[str | None, Form(max_length=10)] = None,
    project_type: Annotated[str | None, Form()] = None,
) -> ProjectPublic:
    """
    Create a new project.

    The project will be created with the user_id automatically set from the authenticated user.
    """
    # Create project data
    project_data: ProjectCreate = ProjectCreate(
        name=name,
        description=description,
        number_of_days=number_of_days,
        paid_project=paid_project,
        street=street,
        us_zip_code=us_zip_code,
        project_type=project_type,
    )

    # Create project in database
    try:
        # Create project using CRUD function
        project: Project = crud.create_project(
            session=session, project_in=project_data, user_id=current_user.id
        )

        return ProjectPublic.model_validate(project)

    except ValueError as e:
        # Handle validation errors from CRUD function
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Handle other errors
        logging.error(f"Error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}",
        )
