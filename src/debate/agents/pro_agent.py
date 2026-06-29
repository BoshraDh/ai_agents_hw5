"""Pro agent — Research Advocate: evidence-first argumentation."""

from __future__ import annotations

import json

from debate.agents.base_agent import BaseAgent
from debate.constants import AgentRole, MessageType
from debate.models.messages import DebateMessage
from debate.shared.config import ConfigManager
from debate.shared.gatekeeper import ApiGatekeeper
from debate.shared.message_bus import MessageBus

_SYSTEM_PROMPT = """You are the Pro Advocate in a structured debate.
Topic: "{topic}"
Your position: "{pro_position}"

--- Skill Definition ---
{skill_description}
--- End Skill ---

Rules:
1. SEARCH FIRST: Use the search_web tool to find at least one recent, credible source.
2. BUILD THE CHAIN: evidence → inference → conclusion.
3. CITE EXPLICITLY: All sources must appear in the citations field.
4. REBUT DIRECTLY: Identify the weakest claim in the opponent's last argument and address it.
5. REFERENCE: Set references_message_id to the opponent's last message_id.
6. WORD LIMIT: Under {word_limit} words.
7. LANGUAGE: Respond in English only.

Output ONLY a JSON object matching the DebateMessage schema. No text outside the JSON."""


class ProAgent(BaseAgent):
    """Argues in favor of AI being a benefit to humanity."""

    def __init__(
        self,
        config: ConfigManager,
        gatekeeper: ApiGatekeeper,
        bus: MessageBus | None = None,
        round_number: int = 1,
        prev_con_msg: DebateMessage | None = None,
    ) -> None:
        super().__init__(AgentRole.PRO, config, gatekeeper)
        self._bus = bus
        self._round_number = round_number
        self._prev_con_msg = prev_con_msg

    def generate_argument(
        self, round_number: int, prev_con_msg: DebateMessage | None
    ) -> DebateMessage:
        """Generate a Pro argument for the given round."""
        system = _SYSTEM_PROMPT.format(
            topic=self._config.topic,
            pro_position=self._config.pro_position,
            word_limit=self._config.word_limit,
            skill_description=self._skill_description,
        )
        opponent_context = (
            f"Opponent's last argument (message_id={prev_con_msg.message_id}):\n"
            f"{prev_con_msg.content}"
            if prev_con_msg
            else "This is the opening argument — no opponent message yet."
        )
        user_msg = f"Round {round_number} of {self._config.max_rounds}.\n{opponent_context}"
        text, citations = self._call_llm(
            system, [{"role": "user", "content": user_msg}], use_search=True
        )
        try:
            raw = json.loads(text.strip())
        except json.JSONDecodeError:
            raw = {"content": text}

        return DebateMessage(
            from_agent=AgentRole.PRO,
            to_agent=AgentRole.FATHER,
            message_type=MessageType.ARGUMENT,
            round_number=round_number,
            content=raw.get("content", text),
            citations=citations or raw.get("citations", []),
            references_message_id=prev_con_msg.message_id if prev_con_msg else None,
        )

    def run(self) -> None:
        """Not used directly — Pro is driven by DebateOrchestrator."""
