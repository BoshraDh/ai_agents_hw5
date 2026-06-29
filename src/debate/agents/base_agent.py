"""Abstract base class for all debate agents."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path

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

    def _call_llm(
        self,
        system: str,
        messages: list[dict],
        use_search: bool = False,
    ) -> tuple[str, list[Citation]]:
        """Call Anthropic API through Gatekeeper, handle tool_use if needed."""
        tools = [SEARCH_TOOL_DEFINITION] if use_search else []
        citations: list[Citation] = []

        def _api_call():
            kwargs = {
                "model": self._model,
                "max_tokens": self._config.max_tokens,
                "system": system,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools
            return self._gatekeeper.execute(
                self._client.messages.create, **kwargs
            )

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_api_call)
                response = future.result(timeout=self._config.llm_timeout)
        except FuturesTimeoutError as exc:
            raise TimeoutError(f"{self.role.value} LLM call timed out") from exc

        text_parts: list[str] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use" and block.name == "search_web":
                citations = self._search_tool.handle_tool_call(block.input)

        return "\n".join(text_parts), citations

    @abstractmethod
    def run(self) -> None:
        """Entry point for the agent process."""

    def _validate_message(self, msg: DebateMessage) -> None:
        """Raise ValueError if the message violates schema rules."""
        if not msg.content.strip():
            raise ValueError(f"{self.role.value}: empty content in message")
