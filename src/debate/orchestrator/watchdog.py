"""Watchdog — monitors agent processes and signals main thread on unrecoverable crash."""

from __future__ import annotations

import multiprocessing
import threading
import time
from collections.abc import Callable

from debate.constants import AgentRole
from debate.shared.config import ConfigManager
from debate.shared.logger import DebateLogger


class ProcessUnrecoverableException(Exception):  # noqa: N818
    """Raised when a process exceeds max_restarts_per_process."""


class _ProcessEntry:
    def __init__(self, role: AgentRole, process: multiprocessing.Process, factory: Callable):
        self.role = role
        self.process = process
        self.factory = factory
        self.restart_count = 0


class Watchdog(threading.Thread):
    """Monitors registered agent processes; auto-restarts on crash.

    GAP-3: ProcessUnrecoverableException is no longer raised inside run()
    (which would be silently swallowed in a daemon thread). Instead, it is
    stored and signalled via _error_event. The main thread calls
    check_for_fatal_error() between rounds to propagate it.
    """

    def __init__(self, config: ConfigManager, logger: DebateLogger) -> None:
        super().__init__(daemon=True, name="Watchdog")
        self._config = config
        self._logger = logger
        self._entries: list[_ProcessEntry] = []
        self._running = False
        # GAP-3: error signalling instead of raising in daemon thread
        self._error_event = threading.Event()
        self._fatal_error: ProcessUnrecoverableException | None = None

    def register(
        self,
        role: AgentRole,
        process: multiprocessing.Process,
        factory: Callable,
    ) -> None:
        """Register an agent process for monitoring."""
        self._entries.append(_ProcessEntry(role, process, factory))

    def start(self) -> None:
        """Start the monitoring loop."""
        self._running = True
        super().start()

    def stop(self) -> None:
        """Signal the monitoring loop to exit cleanly."""
        self._running = False

    def get_status(self) -> dict[str, str]:
        """Return health status for all monitored processes."""
        return {
            e.role.value: ("alive" if e.process.is_alive() else "dead")
            for e in self._entries
        }

    def check_for_fatal_error(self) -> None:
        """GAP-3: call from main thread between rounds to propagate Watchdog errors."""
        if self._error_event.is_set() and self._fatal_error is not None:
            raise self._fatal_error

    def run(self) -> None:
        """Main monitoring loop — polls every heartbeat_interval seconds."""
        while self._running:
            for entry in self._entries:
                if not entry.process.is_alive():
                    self._handle_crash(entry)
            time.sleep(self._config.heartbeat_interval)

    def _handle_crash(self, entry: _ProcessEntry) -> None:
        entry.restart_count += 1
        self._logger.warning(
            "WATCHDOG_RESTART",
            role=entry.role.value,
            attempt=entry.restart_count,
        )
        if entry.restart_count >= self._config.max_restarts:
            self._running = False
            # GAP-3: signal via event instead of raising inside daemon thread
            self._fatal_error = ProcessUnrecoverableException(
                f"{entry.role.value} crashed {entry.restart_count} times — aborting"
            )
            self._error_event.set()
            return
        new_process = entry.factory()
        entry.process = new_process
        new_process.start()
