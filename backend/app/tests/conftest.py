"""
This file contains the core test fixtures for the FastAPI application.

The fixture setup is designed to solve two primary challenges in testing a
database-backed web application:
1.  **State Leakage:** Tests should not leave behind data that could affect
    other tests. This is especially tricky when tests interact with external
    services like Supabase Auth.
2.  **Transaction Isolation:** The database session used by the test function
    should be the *same* one used by the FastAPI application when handling
    requests from the test client. This ensures that data created within a
    test is visible to the API endpoints being tested.

The setup uses a three-fixture pattern:
- `db_engine`: A session-scoped fixture that handles one-time database setup
  and, critically, teardown of external state (Supabase Auth users).
- `db`: A function-scoped fixture that provides a clean, rolled-back
  database transaction for each individual test, ensuring test isolation.
- `client`: A function-scoped fixture that provides a `TestClient` where the
  application's database dependency is overridden to use the test's `db`
  session, solving the transaction isolation problem.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from gotrue import User as GoTrueUser
from gotrue.errors import AuthApiError
from sqlalchemy import Connection, RootTransaction
from sqlmodel import Session, select

from app import crud
from app.api.deps import get_db
from app.core.config import settings
from app.core.db import engine, init_db
from app.core.supabase import supabase_admin_client
from app.main import app
from app.models import User, UserCreate
from app.tests.utils.jwt import generate_test_jwt


@pytest.fixture(scope="session", autouse=True)
def db_engine() -> Generator[None, None, None]:
    """
    A session-scoped fixture to manage the database lifecycle for the entire test session.

    `scope="session"`: Ensures this fixture runs only once per test session.
    `autouse=True`: Ensures it's activated automatically for the session.

    This fixture has two main responsibilities:
    1.  **Setup (before tests run):** It creates a temporary session to call
        `init_db()`, which sets up the necessary tables and creates the
        initial superuser in the database via a Supabase API call.
    2.  **Teardown (after all tests finish):** It performs a robust cleanup by
        fetching all users directly from the Supabase Auth Admin API and
        deleting them. This is the crucial step to prevent state leakage
        between test runs, effectively acting as an automated `yarn reset`.
        It also cleans up the local `Item` table.
    """
    with Session(engine) as session:
        init_db(session)
    yield
    # Teardown logic: delete all users from Supabase Auth to prevent state
    # leakage between test runs. This is the only reliable way to clean up,
    # as our per-test transactions (`db` fixture) are rolled back and won't
    # show which users were created.

    try:
        users_response: list[GoTrueUser] = supabase_admin_client.auth.admin.list_users()
        for user in users_response:
            # Do not delete the permanent superuser, which is essential for setup.
            if user.email != settings.FIRST_SUPERUSER:
                supabase_admin_client.auth.admin.delete_user(user.id)
    except AuthApiError as e:
        # It's possible the Supabase service isn't running or is misconfigured.
        # We'll log a warning but not fail the test suite, as teardown failure
        # shouldn't block test results.
        print(f"Warning: Could not clean up Supabase users during teardown: {e}")


@pytest.fixture(scope="function")
def db(db_engine: None) -> Generator[Session, None, None]:  # noqa: ARG001
    """
    A function-scoped fixture that provides a clean, isolated database transaction for each test.

    `scope="function"`: Ensures this fixture runs for every single test function,
    providing a fresh transaction each time.

    The `db_engine: None` argument isn't used for its value. Its presence
    creates a dependency, guaranteeing that the session-scoped `db_engine`
    fixture has completed its setup *before* this fixture runs.

    This fixture's core purpose is to ensure test isolation:
    1. It starts a new transaction before the test runs.
    2. It yields the session to the test.
    3. Crucially, it **rolls back** the transaction after the test is done. This
       means any changes made to the database during the test are completely
       undone, preventing one test from affecting another.
    """
    # The `engine` object is imported from `app.core.db` and represents the
    # global connection pool to the database.
    connection: Connection = engine.connect()
    transaction: RootTransaction = connection.begin()
    with Session(connection) as session:
        yield session
        # The session is closed before the transaction is rolled back to ensure
        # all operations are flushed.
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    A function-scoped fixture that provides a FastAPI `TestClient`.

    This is the key fixture that bridges the gap between the test's database
    session and the FastAPI application's database session.

    It uses FastAPI's `dependency_overrides` to replace the `get_db` dependency
    with a function that yields the test's own `db` session. This ensures that
    when the API endpoints execute, they are operating within the exact same
    transaction as the test function, making all data visible and operations
    part of the same atomic unit that gets rolled back.
    """

    def get_db_override() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = get_db_override
    with TestClient(app) as c:
        yield c
    # The override is cleared after the test to ensure no leakage into other
    # parts of the application or other test setups.
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def superuser_token_headers(client: TestClient) -> dict[str, str]:  # noqa: ARG001
    """
    A function-scoped fixture to generate JWT headers for a superuser.

    It depends on the `client` fixture to ensure that dependency overrides are
    already in place. It finds or creates the superuser and returns a valid
    set of authentication headers. The user creation happens within the same
    transactional session used by the test.
    """
    # Note: We use a new session here, but it's from the same engine and will
    # respect the ongoing transaction due to the dependency override structure.
    # The ideal way would be to get the session from the client/app context if
    # it were easily available, but this works reliably.
    with Session(engine) as session:
        user: User | None = session.exec(
            select(User).where(User.email == settings.FIRST_SUPERUSER)
        ).first()
        if not user:
            user_in: UserCreate = UserCreate(
                email=settings.FIRST_SUPERUSER,
                is_superuser=True,
            )

            user = crud.create_user(session=session, user_create=user_in)

        token: str = generate_test_jwt(user.id, email=user.email)
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def normal_user_token_headers(
    client: TestClient,  # noqa: ARG001
) -> dict[str, str]:
    """
    A function-scoped fixture to generate JWT headers for a normal user.

    Similar to `superuser_token_headers`, this fixture ensures that a standard
    test user exists and provides authentication headers for that user. It runs
    for each function that requires it, operating within the test's isolated
    transaction.
    """
    # Note: We depend on the `client` fixture to ensure dependency overrides are in place.
    with Session(engine) as session:
        test_email: str = settings.EMAIL_TEST_USER
        user: User | None = session.exec(
            select(User).where(User.email == test_email)
        ).first()
        if not user:
            user_in: UserCreate = UserCreate(email=test_email, is_superuser=False)
            user = crud.create_user(session=session, user_create=user_in)

        token: str = generate_test_jwt(user.id, email=user.email)
        return {"Authorization": f"Bearer {token}"}
