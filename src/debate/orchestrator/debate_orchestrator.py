"""DebateOrchestrator — manages the debate lifecycle and agent coordination."""

from __future__ import annotations

import uuid
from pathlib import Path

from debate.agents.con_agent import ConAgent
from debate.agents.father_agent import FatherAgent
from debate.agents.pro_agent import ProAgent
from debate.constants import DebateStatus
from debate.models.messages import DebateMessage, Verdict
from debate.shared.config import ConfigManager
from debate.shared.gatekeeper import ApiGatekeeper
from debate.shared.logger import DebateLogger
from debate.shared.message_bus import MessageBus


class DebateOrchestrator:
    """Coordinates three agents through N debate rounds and collects the verdict."""

    def __init__(self, config: ConfigManager) -> None:
        self._config = config
        self._session_id = str(uuid.uuid4())[:8]
        self._logger = DebateLogger(config, self._session_id)
        self._gatekeeper = ApiGatekeeper(config)
        self._bus = MessageBus()
        self._transcript: list[DebateMessage] = []
        self._verdict: Verdict | None = None
        self._status = DebateStatus.IDLE

        self._father = FatherAgent(config, self._gatekeeper, self._bus)
        self._pro = ProAgent(config, self._gatekeeper, self._bus)
        self._con = ConAgent(config, self._gatekeeper, self._bus)

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def status(self) -> DebateStatus:
        return self._status

    def run(self, topic: str | None = None) -> tuple[list[DebateMessage], Verdict]:
        """Run the full debate synchronously. Returns (transcript, verdict)."""
        if topic:
            self._config._setup["debate"]["topic"] = topic

        self._status = DebateStatus.RUNNING
        self._logger.info("DEBATE_START", topic=self._config.topic)

        try:
            prev_con_msg: DebateMessage | None = None
            for round_num in range(1, self._config.max_rounds + 1):
                self._logger.info("ROUND_START", round=round_num)
                pro_msg = self._pro.generate_argument(round_num, prev_con_msg)
                self._transcript.append(pro_msg)
                self._father.route(pro_msg)
                con_msg = self._con.generate_counter(round_num, pro_msg)
                self._transcript.append(con_msg)
                self._father.route(con_msg)
                prev_con_msg = con_msg
                self._logger.info("ROUND_END", round=round_num)

            self._verdict = self._father.evaluate_debate(self._transcript)
            self._status = DebateStatus.COMPLETED
            self._logger.info("DEBATE_END", winner=self._verdict.winner.value)
            self._save_transcript()
            return self._transcript, self._verdict

        except Exception as exc:
            self._status = DebateStatus.FAILED
            self._logger.error("DEBATE_FAILED", error=str(exc))
            self._save_transcript()
            raise

    def _save_transcript(self) -> Path:
        return self._logger.save_transcript(
            [m.model_dump() for m in self._transcript]
        )

    def get_transcript(self) -> list[DebateMessage]:
        return list(self._transcript)

    def get_verdict(self) -> Verdict | None:
        return self._verdict
