import logging
import warnings

from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.models import User

logger = logging.getLogger(__name__)

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        # This should not happen in a properly configured environment.
        # The superuser must be created in Supabase Auth first, which will trigger
        # the creation of the user profile in our public.user table.
        # This script's job is only to grant superuser privileges.
        warnings.warn(
            f"Superuser with email {settings.FIRST_SUPERUSER} not found in the database. "
            "Please create the user in Supabase Auth first, then rerun this script.",
            UserWarning,
            stacklevel=1,
        )
    elif not user.is_superuser:
        user.is_superuser = True
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info(f"Promoted user {settings.FIRST_SUPERUSER} to superuser.")
