import random
import string

from fastapi.testclient import TestClient


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def get_superuser_token_headers(client: TestClient) -> dict[str, str]:
    """
    TODO: Replace with JWT-based superuser authentication
    This function previously used password authentication which has been removed.
    Need to implement JWT token generation for superuser testing.
    """
    # TODO: Implement JWT-based superuser authentication headers
    # This requires creating Supabase utilities for the test suite to:
    # 1. Generate valid Supabase JWT tokens for superuser testing
    # 2. Mock Supabase superuser responses
    # 3. Return proper Authorization headers with JWT tokens
    # 4. Handle superuser creation if needed
    raise NotImplementedError(
        "Password authentication removed. Implement JWT authentication."
    )
