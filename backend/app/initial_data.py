import logging

from gotrue.errors import AuthApiError
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine, init_db
from app.core.supabase import supabase_admin_client
from app.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_superuser_exists() -> None:
    """
    Check if the superuser exists in our local `public.user` table.
    If not, create them in Supabase Auth, which will trigger their creation
    in our local database.
    """
    email = settings.FIRST_SUPERUSER
    password = settings.FIRST_SUPERUSER_PASSWORD

    with Session(engine) as session:
        # First, check if the user already exists in our database.
        user = session.exec(select(User).where(User.email == email)).first()

        if user:
            logger.info(f"Superuser {email} already exists. Skipping creation.")
            return

        # If user does not exist locally, they don't exist in Supabase Auth either.
        # Create them in Supabase Auth now.
        logger.info(f"Superuser {email} not found. Creating in Supabase Auth...")
        try:
            supabase_admin_client.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": True,  # Auto-confirm the email
                }
            )
            logger.info(f"Successfully created superuser {email} in Supabase Auth.")
        except AuthApiError as e:
            if "Email address already registered" in str(e):
                logger.warning(
                    f"Supabase creation failed because user {email} already exists there. "
                    "The trigger should have created them locally. There might be an inconsistency."
                )
            else:
                logger.error(f"Error creating superuser in Supabase: {e}")
                raise
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while creating superuser in Supabase: {e}"
            )
            raise


def init() -> None:
    with Session(engine) as session:
        init_db(session)


def main() -> None:
    logger.info("Ensuring superuser exists and is configured...")
    ensure_superuser_exists()
    init()
    logger.info("Superuser check complete.")


if __name__ == "__main__":
    main()
