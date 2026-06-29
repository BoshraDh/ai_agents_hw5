"""Tests for Watchdog: event-based error propagation and process monitoring."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from debate.constants import AgentRole
from debate.orchestrator.watchdog import ProcessUnrecoverableException, Watchdog
from debate.shared.logger import DebateLogger


@pytest.fixture
def watchdog(config):
    logger = DebateLogger(config, "watchdog-test")
    return Watchdog(config, logger)


class TestWatchdogStatus:
    def test_get_status_alive(self, watchdog):
        mock_process = MagicMock()
        mock_process.is_alive.return_value = True
        watchdog.register(AgentRole.PRO, mock_process, lambda: mock_process)
        assert watchdog.get_status()[AgentRole.PRO.value] == "alive"

    def test_get_status_dead(self, watchdog):
        mock_process = MagicMock()
        mock_process.is_alive.return_value = False
        watchdog.register(AgentRole.CON, mock_process, lambda: mock_process)
        assert watchdog.get_status()[AgentRole.CON.value] == "dead"

    def test_is_daemon_thread(self, watchdog):
        assert watchdog.daemon is True

    def test_stop_sets_running_false(self, watchdog):
        watchdog._running = True
        watchdog.stop()
        assert watchdog._running is False


class TestWatchdogErrorPropagation:
    """GAP-3: ProcessUnrecoverableException must reach the main thread via event."""

    def test_check_for_fatal_error_silent_when_no_crash(self, watchdog):
        """No crash — check_for_fatal_error must not raise."""
        watchdog.check_for_fatal_error()  # should not raise

    def test_check_for_fatal_error_raises_after_max_restarts(self, config, watchdog):
        """Simulate max restarts exceeded — error_event must be set."""
        dead_process = MagicMock()
        dead_process.is_alive.return_value = False
        # Use a factory that returns a process that is immediately dead
        dead_factory = MagicMock(return_value=dead_process)
        watchdog.register(AgentRole.PRO, dead_process, dead_factory)

        # Manually trigger crashes past max_restarts
        entry = watchdog._entries[0]
        for _ in range(config.max_restarts + 1):
            watchdog._handle_crash(entry)

        # Event must be set and check_for_fatal_error must raise
        assert watchdog._error_event.is_set()
        with pytest.raises(ProcessUnrecoverableException):
            watchdog.check_for_fatal_error()

    def test_exception_not_raised_inside_thread(self, config, watchdog):
        """_handle_crash must NOT raise inside the daemon thread — only set the event."""
        dead_process = MagicMock()
        dead_process.is_alive.return_value = False
        dead_factory = MagicMock(return_value=dead_process)
        watchdog.register(AgentRole.CON, dead_process, dead_factory)

        entry = watchdog._entries[0]
        for _ in range(config.max_restarts + 1):
            # This must NOT raise — it should only set the event
            try:
                watchdog._handle_crash(entry)
            except ProcessUnrecoverableException:
                pytest.fail("_handle_crash raised inside daemon thread — GAP-3 still broken")

        assert watchdog._fatal_error is not None
