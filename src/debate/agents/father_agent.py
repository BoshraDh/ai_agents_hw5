"""Father agent — routes messages and delivers the final verdict."""

from __future__ import annotations

import json

from debate.constants import AgentRole, MessageType
from debate.models.messages import DebateMessage, Verdict
from debate.shared.config import ConfigManager
from debate.shared.gatekeeper import ApiGatekeeper
from debate.shared.message_bus import MessageBus
from debate.agents.base_agent import BaseAgent


_SYSTEM_PROMPT = """You are the Judge and Moderator of an AI debate on the topic: "{topic}"

Your responsibilities:
1. ROUTING: Forward arguments without modification. Add a brief routing note (max 20 words).
2. ENFORCEMENT: Reject arguments that do not reference the opponent's last message_id.
3. VERDICT: After all rounds, evaluate based solely on PERSUASION POWER.
   Score logical structure, rhetorical effectiveness, evidence quality, and directness of rebuttal.
   You MUST choose exactly one winner — ties are FORBIDDEN.
   Output a JSON object matching the Verdict schema. Do not include text outside the JSON."""


class FatherAgent(BaseAgent):
    """Routes messages between Pro and Con; evaluates debate and renders verdict."""

    def __init__(
        self,
        config: ConfigManager,
        gatekeeper: ApiGatekeeper,
        bus: MessageBus,
    ) -> None:
        super().__init__(AgentRole.FATHER, config, gatekeeper)
        self._bus = bus

    def route(self, message: DebateMessage) -> None:
        """Forward a message to the appropriate agent queue."""
        if message.to_agent == AgentRole.PRO:
            self._bus.send_to_pro(message)
        elif message.to_agent == AgentRole.CON:
            self._bus.send_to_con(message)

    def evaluate_debate(self, transcript: list[DebateMessage]) -> Verdict:
        """Analyze the full transcript and return a Verdict. No ties permitted."""
        summary = "\n\n".join(
            f"[Round {m.round_number} | {m.from_agent.value}]: {m.content}"
            for m in transcript
            if m.message_type in (MessageType.ARGUMENT, MessageType.COUNTER_ARGUMENT)
        )
        system = _SYSTEM_PROMPT.format(topic=self._config.topic)
        prompt = (
            f"The debate has concluded after {self._config.max_rounds} rounds.\n\n"
            f"Full transcript:\n{summary}\n\n"
            "Evaluate based on persuasion power only. Output a valid Verdict JSON object."
        )
        text, _ = self._call_llm(system, [{"role": "user", "content": prompt}])
        try:
            raw = json.loads(text.strip())
            return Verdict(**raw)
        except Exception as exc:
            raise ValueError(f"Father returned invalid Verdict JSON: {text!r}") from exc

    def run(self) -> None:
        """Not used directly — Father is driven by DebateOrchestrator."""
