"""Abstract base class for all debate agents."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import Any

import anthropic

from debate.constants import AgentRole
from debate.models.messages import Citation, DebateMessage
from debate.shared.config import ConfigManager
from debate.shared.gatekeeper import ApiGatekeeper
from debate.tools.search_tool import SEARCH_TOOL_DEFINITION, SearchTool

_SKILL_FILES: dict[AgentRole, str] = {
    AgentRole.FATHER: "father_skill.md",
    AgentRole.PRO: "pro_skill.md",
    AgentRole.CON: "con_skill.md",
}
_SKILLS_DIR = Path(__file__).parent / "skills"


class BaseAgent(ABC):
    """Shared foundation for all three debate agents."""

    def __init__(
        self,
        role: AgentRole,
        config: ConfigManager,
        gatekeeper: ApiGatekeeper,
    ) -> None:
        self.role = role
        self._config = config
        self._gatekeeper = gatekeeper
        self._search_tool = SearchTool()
        self._client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", "")
        )
        self._model = self._resolve_model()
        self._skill_description: str = self._load_skill()

    def _load_skill(self) -> str:
        """Load the agent's Skill definition from its skill.md file."""
        skill_file = _SKILLS_DIR / _SKILL_FILES.get(self.role, "")
        if skill_file.exists():
            return skill_file.read_text(encoding="utf-8").strip()
        return ""

    def _resolve_model(self) -> str:
        if self.role == AgentRole.FATHER:
            return self._config.father_model
        if self.role == AgentRole.PRO:
            return self._config.pro_model
        return self._config.con_model

    def _call_api_once(
        self, system: str, messages: list[dict], tools: list[dict]
    ) -> Any:
        """Single API call with timeout. Raises TimeoutError on deadline."""
        def _request():
            kwargs: dict = {
                "model": self._model,
                "max_tokens": self._config.max_tokens,
                "system": system,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools
            return self._gatekeeper.execute(self._client.messages.create, **kwargs)

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(_request)
        try:
            result = future.result(timeout=self._config.llm_timeout)
            executor.shutdown(wait=False)
            return result
        except FuturesTimeoutError as exc:
            executor.shutdown(wait=False)
            raise TimeoutError(f"{self.role.value} LLM call timed out") from exc

    def _call_llm(
        self,
        system: str,
        messages: list[dict],
        use_search: bool = False,
    ) -> tuple[str, list[Citation]]:
        """Call the LLM, handling the full tool-use cycle if the model calls search_web."""
        tools = [SEARCH_TOOL_DEFINITION] if use_search else []
        citations: list[Citation] = []
        conversation = list(messages)

        while True:
            response = self._call_api_once(system, conversation, tools)
            if response.stop_reason == "tool_use":
                # Execute all tool calls and build tool_result messages
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use" and block.name == "search_web":
                        new_cites = self._search_tool.handle_tool_call(block.input)
                        citations.extend(new_cites)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps([c.model_dump() for c in new_cites]),
                        })
                # Feed results back — LLM will then produce the final text response
                conversation.append({"role": "assistant", "content": response.content})
                conversation.append({"role": "user", "content": tool_results})
            else:
                text_parts = [b.text for b in response.content if b.type == "text"]
                return "\n".join(text_parts), citations

    @abstractmethod
    def run(self) -> None:
        """Entry point for the agent process."""

    def _validate_message(self, msg: DebateMessage) -> None:
        """Raise ValueError if the message violates schema rules."""
        if not msg.content.strip():
            raise ValueError(f"{self.role.value}: empty content in message")
