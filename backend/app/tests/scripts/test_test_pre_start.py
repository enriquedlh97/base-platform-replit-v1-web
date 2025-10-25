"""Test the `init` helper in `app.tests_pre_start`.

`init()` validates database availability by creating a SQLModel `Session` and
running a trivial `SELECT 1` query.  In this test we stub the `Session` object
so that no real database connection is needed and then check that:

1. `init()` completes without raising an exception.
2. The mocked `Session.exec` method is called exactly once, ensuring the
   connectivity check was attempted.

By patching `app.tests_pre_start.Session` with a `MagicMock` that acts as a
context manager the test remains fast and isolated from external services.
"""

from unittest.mock import MagicMock, patch

from app.tests_pre_start import init, logger


def test_init_successful_connection() -> None:
    """Patch `Session`, call `init()`, verify a single `exec` occurs."""
    engine_mock: MagicMock = MagicMock()

    session_mock: MagicMock = MagicMock()
    session_mock.exec = MagicMock(return_value=True)
    # Configure the mock to be used as a context manager.
    session_mock.__enter__.return_value = session_mock
    session_mock.__exit__.return_value = None

    with (
        patch("app.tests_pre_start.Session", return_value=session_mock),
        patch.object(logger, "info"),
        patch.object(logger, "error"),
        patch.object(logger, "warn"),
    ):
        connection_successful: bool
        try:
            init(engine_mock)
            connection_successful = True
        except Exception:
            connection_successful = False

        assert connection_successful, (
            "The database connection should be successful and not raise an exception."
        )

        assert session_mock.exec.call_count == 1, (
            "The session should execute exactly one statement."
        )
