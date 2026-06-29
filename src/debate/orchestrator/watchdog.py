"""Watchdog — background thread that monitors agent processes and restarts crashed ones."""

from __future__ import annotations

import multiprocessing
import threading
import time
from typing import Callable

from debate.constants import AgentRole
from debate.shared.config import ConfigManager
from debate.shared.logger import DebateLogger


class ProcessUnrecoverableException(Exception):
    """Raised when a process exceeds max_restarts_per_process."""


class _ProcessEntry:
    def __init__(self, role: AgentRole, process: multiprocessing.Process, factory: Callable):
        self.role = role
        self.process = process
        self.factory = factory
        self.restart_count = 0


class Watchdog(threading.Thread):
    """Monitors registered agent processes; auto-restarts on crash."""

    def __init__(self, config: ConfigManager, logger: DebateLogger) -> None:
        super().__init__(daemon=True, name="Watchdog")
        self._config = config
        self._logger = logger
        self._entries: list[_ProcessEntry] = []
        self._running = False

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
        """Signal the monitoring loop to exit."""
        self._running = False

    def get_status(self) -> dict[str, str]:
        """Return health status for all monitored processes."""
        return {
            e.role.value: ("alive" if e.process.is_alive() else "dead")
            for e in self._entries
        }

    def run(self) -> None:
        """Main monitoring loop — runs every heartbeat_interval seconds."""
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
        if entry.restart_count > self._config.max_restarts:
            self._running = False
            raise ProcessUnrecoverableException(
                f"{entry.role.value} crashed {entry.restart_count} times — aborting"
            )
        new_process = entry.factory()
        entry.process = new_process
        new_process.start()
