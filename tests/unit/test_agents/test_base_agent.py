"""Tests for BaseAgent — skill loading, timeout, and LLM plumbing."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from debate.constants import AgentRole
from debate.agents.base_agent import _SKILLS_DIR


class TestSkillLoading:
    """GAP-A: Agents must load their skill.md file at construction time."""

    def test_pro_skill_description_non_empty(self, config):
        """ProAgent must load a non-empty skill description from pro_skill.md."""
        from debate.agents.pro_agent import ProAgent
        from debate.shared.gatekeeper import ApiGatekeeper
        agent = ProAgent(config, ApiGatekeeper(config))
        assert agent._skill_description
        assert "Research Advocate" in agent._skill_description

    def test_con_skill_description_non_empty(self, config):
        """ConAgent must load a non-empty skill description from con_skill.md."""
        from debate.agents.con_agent import ConAgent
        from debate.shared.gatekeeper import ApiGatekeeper
        agent = ConAgent(config, ApiGatekeeper(config))
        assert agent._skill_description
        assert "Devil's Advocate" in agent._skill_description

    def test_father_skill_description_non_empty(self, config):
        """FatherAgent must load a non-empty skill description from father_skill.md."""
        from debate.agents.father_agent import FatherAgent
        from debate.shared.gatekeeper import ApiGatekeeper
        agent = FatherAgent(config, ApiGatekeeper(config))
        assert agent._skill_description
        assert "Impartial Judge" in agent._skill_description

    def test_pro_and_con_skills_are_different(self, config):
        """Pro and Con skills must differ — same skill would defeat the debate purpose."""
        from debate.agents.pro_agent import ProAgent
        from debate.agents.con_agent import ConAgent
        from debate.shared.gatekeeper import ApiGatekeeper
        gk = ApiGatekeeper(config)
        pro = ProAgent(config, gk)
        con = ConAgent(config, gk)
        assert pro._skill_description != con._skill_description

    def test_skill_files_exist_on_disk(self):
        """All three skill.md files must be present in the skills/ directory."""
        for filename in ("pro_skill.md", "con_skill.md", "father_skill.md"):
            assert (_SKILLS_DIR / filename).exists(), f"Missing skill file: {filename}"

    def test_missing_skill_file_returns_empty_string(self, config):
        """If a skill file is absent, _load_skill must return '' without crashing."""
        from debate.agents.pro_agent import ProAgent
        from debate.shared.gatekeeper import ApiGatekeeper
        agent = ProAgent(config, ApiGatekeeper(config))
        with patch("debate.agents.base_agent._SKILLS_DIR", Path("/nonexistent")):
            result = agent._load_skill()
        assert result == ""


class TestBaseAgentTimeout:
    def test_llm_timeout_raises_timeout_error(self, config):
        """A slow LLM call that exceeds llm_timeout must raise TimeoutError."""
        from debate.agents.pro_agent import ProAgent
        from debate.shared.gatekeeper import ApiGatekeeper
        import time

        agent = ProAgent(config, ApiGatekeeper(config))

        def slow_call(**kwargs):
            time.sleep(10)

        with patch.object(agent._gatekeeper, "execute", side_effect=slow_call):
            with pytest.raises(TimeoutError):
                agent._call_llm("system", [{"role": "user", "content": "hi"}])
