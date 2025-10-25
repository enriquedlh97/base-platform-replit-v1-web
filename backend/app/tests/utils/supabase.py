from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from app.core.supabase import supabase_admin_client


class SupabaseMock:
    """Utility for mocking Supabase admin client responses."""

    @staticmethod
    def mock_user_response(email: str) -> SimpleNamespace:
        """
        Create a mock response for a user lookup.

        Args:
            email: The email to include in the mock user response

        Returns:
            A SimpleNamespace object mimicking Supabase's user response
        """

        class _DummyUser:
            def __init__(self, email_: str):
                self.email = email_

        return SimpleNamespace(user=_DummyUser(email))

    @staticmethod
    def patch_get_user_by_id(email: str) -> Any:
        """
        Context manager to patch get_user_by_id with a mock response.

        Args:
            email: The email to return in the mock response

        Returns:
            A patch context manager that mocks the Supabase admin client
        """
        dummy_response: SimpleNamespace = SupabaseMock.mock_user_response(email)

        def _fake_get_user(*_: Any, **__: Any) -> SimpleNamespace:
            return dummy_response

        return patch.object(
            supabase_admin_client.auth.admin, "get_user_by_id", _fake_get_user
        )
