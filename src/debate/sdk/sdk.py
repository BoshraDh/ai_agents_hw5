"""DebateSDK — the only public interface for the debate system."""

from __future__ import annotations

import contextlib

from debate.constants import DebateStatus
from debate.orchestrator.debate_orchestrator import DebateOrchestrator
from debate.shared.config import ConfigManager


class DebateSDK:
    """Public API for the AI Debate System. CLI and tests use only this class."""

    def __init__(self, config_dir: str = "config", use_processes: bool = True) -> None:
        self._config = ConfigManager(config_dir)
        self._config_dir = config_dir
        self._use_processes = use_processes
        # GAP-10: per-session store so get_transcript/get_verdict honour session_id
        self._sessions: dict[str, DebateOrchestrator] = {}

    def start_debate(self, topic: str | None = None) -> str:
        """Start a new debate session. Returns the session_id."""
        orch = DebateOrchestrator(self._config_dir, use_processes=self._use_processes)
        orch.run(topic)
        sid = orch.session_id
        self._sessions[sid] = orch
        return sid

    def get_transcript(self, session_id: str) -> list[dict]:
        """Return the full transcript for the given session_id."""
        orch = self._sessions.get(session_id)
        if orch is None:
            return []
        return [m.model_dump() for m in orch.get_transcript()]

    def get_verdict(self, session_id: str) -> dict | None:
        """Return the verdict for the given session_id, or None if not complete."""
        orch = self._sessions.get(session_id)
        if orch is None:
            return None
        verdict = orch.get_verdict()
        return verdict.model_dump() if verdict else None

    def get_status(self) -> str:
        """Return the status of the most recent session."""
        if not self._sessions:
            return DebateStatus.IDLE.value
        last = next(reversed(self._sessions))
        return self._sessions[last].status.value

    def get_config_summary(self) -> dict:
        """Return a human-readable summary of current configuration."""
        return {
            "topic": self._config.topic,
            "max_rounds": self._config.max_rounds,
            "father_model": self._config.father_model,
            "pro_model": self._config.pro_model,
            "con_model": self._config.con_model,
            "budget_usd": self._config.budget_usd,
        }

    def set_topic(self, topic: str) -> None:
        """Update the debate topic in the active config."""
        self._config.set_topic(topic)

    def stop(self) -> None:
        """Stop and clean up all session resources."""
        for orch in self._sessions.values():
            with contextlib.suppress(Exception):
                orch.stop()
        self._sessions.clear()
