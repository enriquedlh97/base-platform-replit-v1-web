"""Test the `init` helper in `app.backend_pre_start`.

The production `init()` function performs a very small health-check: it opens a
SQLModel `Session` and executes a simple `SELECT 1`.  The goal of this test is
therefore to verify that:

1. `init()` does not raise an exception when the connection succeeds (we stub
   the connection so it always "succeeds").
2. Exactly one call to `Session.exec` is made – confirming that the health-check
   query is executed.

A real database is not required for this test.  Instead we patch
`app.backend_pre_start.Session` so that it returns a `MagicMock` acting as a
context manager.  This keeps the test fast, deterministic and independent of
external resources.
"""

from unittest.mock import MagicMock, patch

from app.backend_pre_start import init, logger


def test_init_successful_connection() -> None:
    """Patch `Session`, run `init()`, and assert exactly one `exec` call."""
    engine_mock: MagicMock = MagicMock()

    session_mock: MagicMock = MagicMock()
    session_mock.exec = MagicMock(return_value=True)
    # Configure the mock to be used as a context manager.
    session_mock.__enter__.return_value = session_mock
    session_mock.__exit__.return_value = None

    with (
        patch("app.backend_pre_start.Session", return_value=session_mock),
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
