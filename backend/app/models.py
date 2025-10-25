# TODO: For future scalability, refactor this file into a `models/` package.
# When this is done, group models by domain (e.g., `user.py`, `item.py`, etc.).
# Remember to use string-based forward references in `Relationship` calls
# (e.g., `owner: "User" | None = Relationship(...)`) to avoid circular import errors.
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr
from pydantic import Field as PydanticField
from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    name: str | None = None
    about: str | None = None
    avatar_url: str | None = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    pass


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)
    name: str | None = None
    about: str | None = None
    avatar_url: str | None = None


# Database model, database table inferred from class name
class User(UserBase, table=True):
    # NOTE: `id` is both this table's primary key **and** a foreign key to
    # `auth.users(id)`. The cross-schema FK is created in Alembic migration
    # b2dddd882db1 and therefore isn't declared here to avoid reflection
    # issues with SQLModel.
    id: UUID = Field(primary_key=True)
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: UUID
    owner_id: UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class ClientBase(SQLModel):
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    phone: str = Field(min_length=1, max_length=255)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    pass


class Client(ClientBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    appointments: list["Appointment"] = Relationship(back_populates="client")


class ServiceBase(SQLModel):
    category: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    duration: int = Field(ge=0)
    price: float = Field(ge=0)


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(ServiceBase):
    category: str = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    duration: int = Field(default=None, ge=0)
    price: float = Field(default=None, ge=0)


class Service(ServiceBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    appointments: list["Appointment"] = Relationship(back_populates="service")


class ServicePublic(ServiceBase):
    id: UUID


class ServicesPublic(SQLModel):
    data: list[ServicePublic]
    count: int


class ProviderBase(SQLModel):
    public_name: str = Field(min_length=1, max_length=255)
    email: str = Field(max_length=255, nullable=False, unique=True)
    accepts_online_bookings: bool = Field(default=False)
    services: dict[str, list[str]] = Field(default=None, sa_column=Column(JSON))
    photo_url: str | None = Field(default=None)

    # Working hours will be stored as JSON data
    working_hours: dict[str, str] = Field(default=None, sa_column=Column(JSON))


class ProviderCreate(ProviderBase):
    pass


class ProviderUpdate(ProviderBase):
    public_name: str = Field(default=None, min_length=1, max_length=255)
    email: str = Field(default=None, max_length=255)


class Provider(ProviderBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    appointments: list["Appointment"] = Relationship(back_populates="provider")


class ProviderPublic(ProviderBase):
    id: UUID


class ProvidersPublic(SQLModel):
    data: list[ProviderPublic]
    count: int


class AppointmentBase(SQLModel):
    appointment_date: datetime = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    price: float
    status: str = Field(max_length=50, nullable=False)
    client_notes: str | None = Field(default=None, max_length=255)
    internal_notes: str | None = Field(default=None, max_length=255)
    duration: int = Field(nullable=False)

    client_id: UUID
    provider_id: UUID
    service_id: UUID


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(AppointmentBase):
    appointment_date: datetime
    price: float
    status: str
    client_notes: str | None = None
    internal_notes: str | None = None


class Appointment(AppointmentBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    client_id: UUID = Field(foreign_key="client.id")
    provider_id: UUID = Field(foreign_key="provider.id")
    service_id: UUID = Field(foreign_key="service.id")

    client: Client = Relationship(back_populates="appointments")
    provider: Provider = Relationship(back_populates="appointments")
    service: Service = Relationship(back_populates="appointments")


class AppointmentPublic(AppointmentBase):
    id: UUID


class AppointmentsPublic(SQLModel):
    data: list[AppointmentPublic]
    count: int


# Webhook Models
class SupabaseUser(BaseModel):
    id: UUID
    email: EmailStr


# TODO: Probably no longer necessary
class SupabaseWebhookPayload(BaseModel):
    type: str
    record: SupabaseUser
    table: str
    schema_name: str = PydanticField(alias="schema")


# TODO: Probably no longer necessary
class UserCreateFromWebhook(BaseModel):
    id: UUID
    email: EmailStr


# Install table: stores Expo push tokens for each user
class Install(SQLModel, table=True):
    __tablename__ = "installs"
    user_id: UUID = Field(primary_key=True, foreign_key="user.id", ondelete="CASCADE")
    expo_tokens: list[str] = Field(
        sa_column=Column(ARRAY(String), nullable=False, default=list)
    )


# Achievement table: tracks user achievements
class Achievement(SQLModel, table=True):
    __tablename__ = "achievements"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    name: str
    progress: int
    goal: int
    type: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Event table: stores events, linked to users
class Event(SQLModel, table=True):
    __tablename__ = "events"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")


# Properties to receive via API for event creation
class EventCreate(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None)
    start_time: datetime | None = Field(default=None)
    end_time: datetime | None = Field(default=None)
    status: str = Field(min_length=1, max_length=50)


# Properties to receive via API for event updates
class EventUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None)
    start_time: datetime | None = Field(default=None)
    end_time: datetime | None = Field(default=None)
    status: str | None = Field(default=None, min_length=1, max_length=50)


# Properties returned via API for events
class EventPublic(SQLModel):
    id: UUID
    name: str
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    user_id: UUID


# Category table: event/post categories
class Category(SQLModel, table=True):
    __tablename__ = "categories"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Properties to return via API, id is always required
class CategoryPublic(SQLModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


# Post table: user posts, linked to users and categories
class Post(SQLModel, table=True):
    __tablename__ = "posts"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    category_id: UUID | None = Field(
        default=None, foreign_key="categories.id", ondelete="SET NULL"
    )
    title: str
    content: str | None = None
    image_url: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Properties to receive via API on post creation
class PostCreate(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    content: str | None = Field(default=None)
    category_id: str | UUID | None = Field(
        default=None, description="Category ID as string or UUID"
    )
    image_url: str | None = Field(default=None)


class PostPublic(SQLModel):
    id: UUID
    user_id: UUID
    category_id: UUID | None = None
    title: str
    content: str | None = None
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime
    # Additional fields for frontend compatibility
    category_name: str | None = None  # Populated from category_id
    author: UserPublic | None = None  # Populated from user_id


# UserStat table: user statistics
class UserStat(SQLModel, table=True):
    __tablename__ = "user_stats"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    mrr: Decimal | None = None
    arr: Decimal | None = None
    weekly_post_views: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Referral table: tracks user referrals
class Referral(SQLModel, table=True):
    __tablename__ = "referrals"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    referrer_user_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    referred_user_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Project table: user projects, linked to users
class Project(SQLModel, table=True):
    __tablename__ = "projects"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    name: str = Field(max_length=255)
    description: str | None = None
    number_of_days: int | None = None
    paid_project: bool = Field(default=False)
    street: str | None = None
    us_zip_code: str | None = Field(max_length=10)
    project_type: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Properties to receive via API on project creation
class ProjectCreate(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    number_of_days: int | None = Field(ge=1, le=200)
    paid_project: bool = Field(default=False)
    street: str | None = None
    us_zip_code: str | None = Field(max_length=10)
    project_type: str | None = None


class ProjectPublic(SQLModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None = None
    number_of_days: int | None = None
    paid_project: bool
    street: str | None = None
    us_zip_code: str | None = None
    project_type: str | None = None
    created_at: datetime
    updated_at: datetime
