from collections.abc import Sequence

from fastapi import APIRouter

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import Event, EventCreate, EventPublic

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=list[EventPublic])
def read_events(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[EventPublic]:
    """
    Retrieve events for the authenticated user.
    """
    events: Sequence[Event] = crud.get_events_by_user(
        session=session, user_id=current_user.id, limit=100
    )

    # Convert Event models to EventPublic models (like posts.py does)
    return [EventPublic.model_validate(event) for event in events]


@router.post("/", response_model=EventPublic)
def create_event(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    event_in: EventCreate,
) -> EventPublic:
    """
    Create a new event for the authenticated user.
    """
    # Create event using CRUD function
    event: Event = crud.create_event(
        session=session,
        event_in=event_in,
        user_id=current_user.id,
    )

    # Convert Event model to EventPublic model (like posts.py does)
    return EventPublic.model_validate(event)
