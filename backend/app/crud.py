import time
from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from gotrue import User as GoTrueUser
from gotrue import UserResponse
from gotrue.errors import AuthApiError
from sqlmodel import Session, col, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.core.supabase import supabase_admin_client
from app.models import (
    Appointment,
    AppointmentCreate,
    AppointmentUpdate,
    Client,
    ClientCreate,
    ClientUpdate,
    Event,
    EventCreate,
    EventUpdate,
    Item,
    ItemCreate,
    Post,
    PostCreate,
    Project,
    ProjectCreate,
    Provider,
    ProviderCreate,
    Service,
    ServiceCreate,
    User,
    UserCreate,
    UserUpdate,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    user_data: dict[str, Any] = user_create.model_dump()
    try:
        response: UserResponse = supabase_admin_client.auth.admin.create_user(
            {"email": user_data["email"], "email_confirm": True}
        )
        user_id: UUID = UUID(response.user.id)
    except AuthApiError as e:
        if "A user with this email address has already been registered" in str(e):
            # TODO: See if there is a specific error to catch, not just a string.
            # If user already exists in Supabase, fetch them to get the ID.
            # The GoTrue client doesn't support direct filtering by email, so we
            # must paginate through users page by page until we find the match.
            page: int = 1
            found_user: GoTrueUser | None = None
            while True:
                # Fetch a page of users.
                users_response: list[GoTrueUser] = (
                    supabase_admin_client.auth.admin.list_users(
                        page=page,
                        per_page=50,  # 50 is a common page size default
                    )
                )
                # Search for the user on the current page.
                for user in users_response:
                    if user.email == user_data["email"]:
                        found_user = user
                        break  # Exit the inner loop once user is found
                if found_user:
                    break  # Exit the outer loop as we have our user

                # If we received fewer users than the page size, we've reached the end.
                if len(users_response) < 50:
                    break
                page += 1

            if not found_user:
                # This should be an impossible state: the error says the user
                # exists, but we couldn't find them. Raise to avoid hiding this.
                raise RuntimeError(
                    f"Could not find user {user_data['email']} in Supabase "
                    "after duplicate user error."
                )
            user_id = UUID(found_user.id)
        else:
            raise  # Re-raise any other unexpected API errors

    # The Postgres trigger (created in migrations) will synchronously insert a
    # row into public.user.  Nonetheless we poll briefly to ensure it’s
    # committed before returning, so callers don’t race.

    statement: SelectOfScalar[User] = select(User).where(User.id == user_id)
    for _ in range(50):  # ~5 s max (50 × 0.1 s)bash ./scripts/test.sh
        db_user: User | None = session.exec(statement).first()
        if db_user is not None:
            return db_user
        time.sleep(0.1)  # TODO: Is this sleep ideal?

    raise RuntimeError("Shadow user row was not created by trigger in time")


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    db_user.sqlmodel_update(user_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement: SelectOfScalar[User] = select(User).where(User.email == email)
    session_user: User | None = session.exec(statement).first()
    return session_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: UUID) -> Item:
    db_item: Item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def get_client_by_email(session: Session, email: str) -> Client | None:
    statement: SelectOfScalar[Client] = select(Client).where(Client.email == email)
    return session.exec(statement).first()


def get_client_by_id(session: Session, client_id: UUID) -> Client | None:
    statement: SelectOfScalar[Client] = select(Client).where(Client.id == client_id)
    return session.exec(statement).first()


def create_client(*, session: Session, client_in: ClientCreate) -> Client:
    db_client: Client = Client.model_validate(client_in)
    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    return db_client


def update_client(
    session: Session, client_id: UUID, client_in: ClientUpdate
) -> Client | None:
    statement = select(Client).where(Client.id == client_id)
    db_client: Client | None = session.exec(statement).first()
    if db_client:
        for key, value in client_in.dict(exclude_unset=True).items():
            setattr(db_client, key, value)
        session.commit()
        session.refresh(db_client)
    return db_client


def create_service(*, session: Session, service_in: ServiceCreate) -> Service:
    db_service: Service = Service.model_validate(service_in)
    session.add(db_service)
    session.commit()
    session.refresh(db_service)
    return db_service


def create_post(*, session: Session, post_in: PostCreate, user_id: UUID) -> Post:
    """
    Create a new post in the database.

    Args:
        session: Database session
        post_in: Post creation data (category_id can be string or UUID)
        user_id: ID of the user creating the post

    Returns:
        Created Post object

    Raises:
        ValueError: If category_id is provided but invalid
    """
    # Handle UUID conversion for category_id
    category_uuid: UUID | None = None
    if post_in.category_id:
        try:
            # Handle both string and UUID inputs
            if isinstance(post_in.category_id, str):
                category_uuid = UUID(post_in.category_id)
            else:
                category_uuid = post_in.category_id
        except (ValueError, TypeError):
            raise ValueError("Invalid category_id format")

    # Create post with validated data
    db_post: Post = Post.model_validate(
        post_in, update={"user_id": user_id, "category_id": category_uuid}
    )
    session.add(db_post)
    session.commit()
    session.refresh(db_post)
    return db_post


def get_all_services(session: Session) -> list[Service]:
    statement: SelectOfScalar[Service] = select(Service)
    return list(session.exec(statement).all())


def get_service_by_id(session: Session, service_id: UUID) -> Service | None:
    statement: SelectOfScalar[Service] = select(Service).where(Service.id == service_id)
    return session.exec(statement).first()


def delete_service(session: Session, service_id: UUID) -> Service | None:
    service: Service | None = get_service_by_id(session=session, service_id=service_id)
    if service:
        session.delete(service)
        session.commit()
    return service


def get_all_clients(session: Session) -> list[Client]:
    statement: SelectOfScalar[Client] = select(Client)
    return list(session.exec(statement).all())


def delete_client(session: Session, client_id: UUID) -> Client | None:
    """
    Delete a client by client_id.
    """
    statement: SelectOfScalar[Client] = select(Client).where(Client.id == client_id)
    db_client: Client | None = session.exec(statement).first()

    if db_client:
        session.delete(db_client)
        session.commit()

    return db_client


def create_provider(session: Session, provider_in: ProviderCreate) -> Provider:
    db_provider: Provider = Provider(**provider_in.dict())
    session.add(db_provider)
    session.commit()
    session.refresh(db_provider)
    return db_provider


def get_all_providers(session: Session) -> list[Provider]:
    statement: SelectOfScalar[Provider] = select(Provider)
    return list(session.exec(statement).all())


def get_provider_by_id(session: Session, provider_id: UUID) -> Provider | None:
    statement: SelectOfScalar[Provider] = select(Provider).where(
        Provider.id == provider_id
    )
    return session.exec(statement).first()


def delete_provider(session: Session, provider_id: UUID) -> Provider | None:
    provider: Provider | None = get_provider_by_id(session, provider_id)
    if provider:
        session.delete(provider)
        session.commit()
    return provider


def create_appointment(
    session: Session, appointment_in: AppointmentCreate
) -> Appointment:
    db_appointment: Appointment = Appointment(**appointment_in.dict())
    session.add(db_appointment)
    session.commit()
    session.refresh(db_appointment)
    return db_appointment


def get_all_appointments(
    session: Session, skip: int = 0, limit: int = 100
) -> list[Appointment]:
    # TODO: Fix deprecated method .query
    return session.query(Appointment).offset(skip).limit(limit).all()


def get_appointment_by_id(session: Session, appointment_id: UUID) -> Appointment | None:
    # TODO: Fix deprecated method .query
    return session.query(Appointment).filter_by(id=appointment_id).first()


def get_appointments_by_client(
    session: Session, client_id: UUID, skip: int = 0, limit: int = 100
) -> list[Appointment]:
    # TODO: Fix deprecated method .query
    return (
        session.query(Appointment)
        .filter_by(client_id=client_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_appointments_by_provider(
    session: Session, provider_id: UUID, skip: int = 0, limit: int = 100
) -> list[Appointment]:
    # TODO: Fix deprecated method .query
    return (
        session.query(Appointment)
        .filter_by(provider_id=provider_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_appointment_by_date_and_provider(
    session: Session, appointment_date: datetime, provider_id: UUID
) -> Appointment | None:
    # TODO: Fix deprecated method .query
    return (
        session.query(Appointment)
        .filter_by(appointment_date=appointment_date, provider_id=provider_id)
        .first()
    )


def update_appointment(
    session: Session, appointment_id: UUID, appointment_in: AppointmentUpdate
) -> Appointment | None:
    # TODO: Fix deprecated method .query
    db_appointment: Appointment | None = (
        session.query(Appointment).filter_by(id=appointment_id).first()
    )
    if db_appointment:
        for key, value in appointment_in.dict(exclude_unset=True).items():
            setattr(db_appointment, key, value)
        session.commit()
        session.refresh(db_appointment)
        return db_appointment
    return None


def delete_appointment(session: Session, appointment_id: UUID) -> bool:
    # TODO: Fix deprecated method .query
    db_appointment = session.query(Appointment).filter_by(id=appointment_id).first()
    if db_appointment:
        session.delete(db_appointment)
        session.commit()
        return True
    return False


def create_project(
    *, session: Session, project_in: ProjectCreate, user_id: UUID
) -> Project:
    """
    Create a new project in the database.

    Args:
        session: Database session
        project_in: Project creation data
        user_id: ID of the user creating the project

    Returns:
        Created Project object
    """
    # Create project with validated data
    db_project: Project = Project.model_validate(
        project_in, update={"user_id": user_id}
    )
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project


def create_event(*, session: Session, event_in: EventCreate, user_id: UUID) -> Event:
    """
    Create a new event in the database.

    Args:
        session: Database session
        event_in: Event creation data
        user_id: ID of the user creating the event

    Returns:
        Created Event object
    """
    # Create event with validated data
    db_event: Event = Event.model_validate(event_in, update={"user_id": user_id})
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event


def get_events_by_user(
    session: Session, user_id: UUID, skip: int = 0, limit: int = 100
) -> Sequence[Event]:
    """
    Get events for a specific user.

    Args:
        session: Database session
        user_id: ID of the user
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of events for the user
    """
    statement: SelectOfScalar[Event] = (
        select(Event)
        .where(Event.user_id == user_id)
        .order_by(col(Event.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


def get_event_by_id(session: Session, event_id: UUID) -> Event | None:
    """
    Get an event by its ID.

    Args:
        session: Database session
        event_id: ID of the event

    Returns:
        Event object if found, None otherwise
    """
    statement: SelectOfScalar[Event] = select(Event).where(Event.id == event_id)
    return session.exec(statement).first()


def update_event(
    session: Session, event_id: UUID, event_in: EventUpdate
) -> Event | None:
    """
    Update an existing event.

    Args:
        session: Database session
        event_id: ID of the event to update
        event_in: Event update data

    Returns:
        Updated Event object if found, None otherwise
    """
    statement: SelectOfScalar[Event] = select(Event).where(Event.id == event_id)
    db_event: Event | None = session.exec(statement).first()
    if db_event:
        for key, value in event_in.model_dump(exclude_unset=True).items():
            setattr(db_event, key, value)
        session.commit()
        session.refresh(db_event)
        return db_event
    return None


def delete_event(session: Session, event_id: UUID) -> bool:
    """
    Delete an event by its ID.

    Args:
        session: Database session
        event_id: ID of the event to delete

    Returns:
        True if event was deleted, False otherwise
    """
    statement: SelectOfScalar[Event] = select(Event).where(Event.id == event_id)
    db_event: Event | None = session.exec(statement).first()
    if db_event:
        session.delete(db_event)
        session.commit()
        return True
    return False
