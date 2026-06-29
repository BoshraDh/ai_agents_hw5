"""Tests for Watchdog process monitor."""

from __future__ import annotations

import multiprocessing
import time
from unittest.mock import MagicMock, patch

import pytest

from debate.constants import AgentRole
from debate.orchestrator.watchdog import ProcessUnrecoverableException, Watchdog
from debate.shared.logger import DebateLogger


@pytest.fixture
def watchdog(config):
    logger = DebateLogger(config, "watchdog-test")
    return Watchdog(config, logger)


class TestWatchdog:
    def test_get_status_alive(self, watchdog):
        mock_process = MagicMock()
        mock_process.is_alive.return_value = True
        watchdog.register(AgentRole.PRO, mock_process, lambda: mock_process)
        status = watchdog.get_status()
        assert status[AgentRole.PRO.value] == "alive"

    def test_get_status_dead(self, watchdog):
        mock_process = MagicMock()
        mock_process.is_alive.return_value = False
        watchdog.register(AgentRole.CON, mock_process, lambda: mock_process)
        status = watchdog.get_status()
        assert status[AgentRole.CON.value] == "dead"

    def test_stop_sets_running_false(self, watchdog):
        watchdog._running = True
        watchdog.stop()
        assert watchdog._running is False

    def test_is_daemon_thread(self, watchdog):
        assert watchdog.daemon is True
