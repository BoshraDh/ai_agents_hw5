# PRD — Watchdog (Process Health Monitor)

**Component**: `src/debate/orchestrator/watchdog.py`  
**Version**: 1.00  
**Date**: 2026-06-29

---

## 1. Purpose

The Watchdog is a background daemon thread that continuously monitors the health of
all three agent processes. If any process dies unexpectedly (due to an exception,
memory error, or timeout), the Watchdog automatically restarts it, allowing the
debate to continue without manual intervention.

---

## 2. Responsibilities

| Responsibility | Description |
|---|---|
| Heartbeat Monitoring | Checks `process.is_alive()` for each registered process |
| Crash Detection | Detects when a process terminates without clean shutdown |
| Auto-Restart | Calls `process.start()` on a new instance when crash detected |
| Max Restart Tracking | Counts restarts per process; stops retrying after max exceeded |
| Status Reporting | Provides current health status for all monitored processes |
| Graceful Shutdown | Stops monitoring on `stop()` call; does not kill processes |

---

## 3. Functional Requirements

- **FR-W01**: The Watchdog shall run as a `threading.Thread` daemon in the orchestrator process
- **FR-W02**: The Watchdog shall poll all agent processes every `heartbeat_interval_seconds`
- **FR-W03**: If a process is not alive, the Watchdog shall log the crash and attempt restart
- **FR-W04**: A new `multiprocessing.Process` instance shall be created on restart (not the same object)
- **FR-W05**: If a process crashes more than `max_restarts_per_process` times, the Watchdog shall raise `ProcessUnrecoverableException` and halt the debate
- **FR-W06**: The Watchdog shall emit a `WATCHDOG_RESTART` log event for each restart
- **FR-W07**: The Watchdog shall stop cleanly when `watchdog.stop()` is called

---

## 4. Heartbeat Protocol

The Watchdog uses Python's `multiprocessing.Process.is_alive()` to detect crashes.
This is sufficient for detecting hard crashes (process exit, uncaught exceptions).

For detecting "zombie" processes that are alive but stuck (e.g., waiting forever on
a blocked Queue), the orchestrator enforces a per-round timeout using
`ThreadPoolExecutor` + `Future.result(timeout=...)`.

---

## 5. Interface

```python
class Watchdog(threading.Thread):
    def __init__(self, config: ConfigManager, logger: DebateLogger) -> None: ...

    def register(self, role: AgentRole, process: Process, factory: Callable) -> None:
        """Register an agent process and its factory function for restart."""

    def start(self) -> None:
        """Start the monitoring loop as a daemon thread."""

    def stop(self) -> None:
        """Signal the monitoring loop to exit cleanly."""

    def get_status(self) -> dict[str, str]:
        """Return health status of all monitored processes."""
```

---

## 6. Configuration (from `config/setup.json`)

```json
{
  "watchdog": {
    "heartbeat_interval_seconds": 10,
    "max_restarts_per_process": 3
  }
}
```

---

## 7. Custom Exceptions

```python
class ProcessUnrecoverableException(Exception):
    """Raised when a process exceeds max_restarts_per_process."""
```

---

## 8. Dependencies

- `shared/config.py` — Heartbeat interval and restart limit
- `shared/logger.py` — Crash and restart event logging
- `constants.py` — `AgentRole` enum
