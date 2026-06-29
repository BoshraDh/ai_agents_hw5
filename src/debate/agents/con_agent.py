"""Con agent — Devil's Advocate: reductio ad absurdum and source contradiction."""

from __future__ import annotations

import json

from debate.constants import AgentRole, MessageType
from debate.models.messages import DebateMessage
from debate.shared.config import ConfigManager
from debate.shared.gatekeeper import ApiGatekeeper
from debate.shared.message_bus import MessageBus
from debate.agents.base_agent import BaseAgent


_SYSTEM_PROMPT = """You are the Con Advocate in a structured debate.
Topic: "{topic}"
Your position: "{con_position}"

Your skill is "Devil's Advocate":
1. FIND THE EXCEPTION: Use search_web to find a counter-example or contradicting study.
2. REDUCTIO AD ABSURDUM: Show how the Pro's argument leads to an absurd conclusion if taken to extremes.
3. CONTRADICT THE SOURCE: Find a source that supersedes or contradicts what Pro cited.
4. CITE EXPLICITLY: All sources must appear in the citations field.
5. REFERENCE: Set references_message_id to the Pro's last message_id.
6. WORD LIMIT: Under {word_limit} words.

Output ONLY a JSON object matching the DebateMessage schema. No text outside the JSON."""


class ConAgent(BaseAgent):
    """Argues that AI poses serious threats to humanity."""

    def __init__(
        self,
        config: ConfigManager,
        gatekeeper: ApiGatekeeper,
        bus: MessageBus | None = None,
    ) -> None:
        super().__init__(AgentRole.CON, config, gatekeeper)
        self._bus = bus

    def generate_counter(
        self, round_number: int, pro_msg: DebateMessage
    ) -> DebateMessage:
        """Generate a Con counter-argument responding to the given Pro message."""
        system = _SYSTEM_PROMPT.format(
            topic=self._config.topic,
            con_position=self._config.con_position,
            word_limit=self._config.word_limit,
        )
        user_msg = (
            f"Round {round_number} of {self._config.max_rounds}.\n"
            f"Pro's argument (message_id={pro_msg.message_id}):\n{pro_msg.content}"
        )
        text, citations = self._call_llm(
            system, [{"role": "user", "content": user_msg}], use_search=True
        )
        try:
            raw = json.loads(text.strip())
        except json.JSONDecodeError:
            raw = {"content": text}

        return DebateMessage(
            from_agent=AgentRole.CON,
            to_agent=AgentRole.FATHER,
            message_type=MessageType.COUNTER_ARGUMENT,
            round_number=round_number,
            content=raw.get("content", text),
            citations=citations or raw.get("citations", []),
            references_message_id=pro_msg.message_id,
        )

    def run(self) -> None:
        """Not used directly — Con is driven by DebateOrchestrator."""
