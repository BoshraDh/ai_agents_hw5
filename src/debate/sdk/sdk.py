"""DebateSDK — the only public interface for the debate system."""

from __future__ import annotations

from debate.constants import DebateStatus
from debate.orchestrator.debate_orchestrator import DebateOrchestrator
from debate.shared.config import ConfigManager


class DebateSDK:
    """Public API for the AI Debate System. CLI and tests use only this class."""

    def __init__(self, config_dir: str = "config") -> None:
        self._config = ConfigManager(config_dir)
        self._orchestrator: DebateOrchestrator | None = None

    def start_debate(self, topic: str | None = None) -> str:
        """Start a new debate session. Returns the session_id."""
        self._orchestrator = DebateOrchestrator(self._config)
        self._orchestrator.run(topic)
        return self._orchestrator.session_id

    def get_transcript(self, session_id: str) -> list[dict]:
        """Return the full debate transcript as a list of dicts."""
        if self._orchestrator is None:
            return []
        return [m.model_dump() for m in self._orchestrator.get_transcript()]

    def get_verdict(self, session_id: str) -> dict | None:
        """Return the verdict as a dict, or None if debate is not complete."""
        if self._orchestrator is None:
            return None
        verdict = self._orchestrator.get_verdict()
        return verdict.model_dump() if verdict else None

    def get_status(self) -> str:
        """Return the current debate status as a string."""
        if self._orchestrator is None:
            return DebateStatus.IDLE.value
        return self._orchestrator.status.value

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
        self._config._setup["debate"]["topic"] = topic

    def stop(self) -> None:
        """Stop the debate and clean up resources."""
        self._orchestrator = None
