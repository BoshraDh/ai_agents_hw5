"""FIFO rotating JSONL logger for all debate events."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from debate.shared.config import ConfigManager


class DebateLogger:
    """Thread-safe FIFO rotating JSONL logger."""

    def __init__(self, config: ConfigManager, session_id: str) -> None:
        self._config = config
        self._session_id = session_id
        self._lock = threading.Lock()
        self._log_dir = Path(config.log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._current_file: Path | None = None
        self._line_count = 0
        self._rotate()

    def _rotate(self) -> None:
        """Open a new log file, deleting oldest if at max_files limit."""
        existing = sorted(self._log_dir.glob("debate_*.jsonl"))
        if len(existing) >= self._config.max_log_files:
            existing[0].unlink()
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        self._current_file = self._log_dir / f"debate_{ts}.jsonl"
        self._line_count = 0

    def _write(self, record: dict) -> None:
        if self._line_count >= self._config.max_log_lines:
            self._rotate()
        assert self._current_file is not None
        with open(self._current_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        self._line_count += 1

    def info(self, event: str, **kwargs) -> None:
        """Log an INFO-level event."""
        with self._lock:
            self._write({"level": "INFO", "event": event, "session": self._session_id,
                         "ts": datetime.now(timezone.utc).isoformat(), **kwargs})

    def warning(self, event: str, **kwargs) -> None:
        """Log a WARNING-level event."""
        with self._lock:
            self._write({"level": "WARNING", "event": event, "session": self._session_id,
                         "ts": datetime.now(timezone.utc).isoformat(), **kwargs})

    def error(self, event: str, **kwargs) -> None:
        """Log an ERROR-level event."""
        with self._lock:
            self._write({"level": "ERROR", "event": event, "session": self._session_id,
                         "ts": datetime.now(timezone.utc).isoformat(), **kwargs})

    def save_transcript(self, messages: list[dict]) -> Path:
        """Write the full debate transcript to a dedicated session JSONL file."""
        path = self._log_dir / f"session_{self._session_id}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")
        return path
