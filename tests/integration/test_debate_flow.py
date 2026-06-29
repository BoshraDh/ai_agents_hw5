"""Integration test — full debate flow with all Anthropic calls mocked."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from debate.constants import AgentRole
from debate.orchestrator.debate_orchestrator import DebateOrchestrator


def _make_mock_llm_response(content: str):
    """Return a mock Anthropic response with the given text content."""
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(type="text", text=content)]
    mock_resp.usage = MagicMock(input_tokens=100, output_tokens=50)
    return mock_resp


@pytest.fixture
def orchestrator(config):
    return DebateOrchestrator(config)


class TestDebateFlow:
    def test_full_debate_returns_transcript_and_verdict(self, orchestrator):
        pro_response = json.dumps({"content": "AI saved 1M lives via early cancer detection."})
        con_response = json.dumps({"content": "AI surveillance has imprisoned innocent people."})
        verdict_response = json.dumps({
            "winner": "pro_agent",
            "pro_score": 78.0,
            "con_score": 65.0,
            "justification": "Pro demonstrated stronger evidence chain.",
            "criterion": "persuasion_power",
            "rounds_evaluated": 2,
        })

        call_count = {"n": 0}
        responses = [pro_response, con_response] * 2 + [verdict_response]

        def mock_call_llm(system, messages, use_search=False):
            idx = call_count["n"] % len(responses)
            call_count["n"] += 1
            return responses[idx], []

        with (
            patch.object(orchestrator._pro, "_call_llm", side_effect=mock_call_llm),
            patch.object(orchestrator._con, "_call_llm", side_effect=mock_call_llm),
            patch.object(orchestrator._father, "_call_llm", side_effect=mock_call_llm),
        ):
            transcript, verdict = orchestrator.run()

        assert len(transcript) == orchestrator._config.max_rounds * 2
        assert verdict.winner in (AgentRole.PRO, AgentRole.CON)
        assert verdict.criterion == "persuasion_power"

    def test_transcript_has_alternating_agents(self, orchestrator):
        pro_response = json.dumps({"content": "Pro argument."})
        con_response = json.dumps({"content": "Con counter."})
        verdict_response = json.dumps({
            "winner": "con_agent",
            "pro_score": 55.0,
            "con_score": 70.0,
            "justification": "Con was sharper.",
            "criterion": "persuasion_power",
            "rounds_evaluated": 2,
        })

        responses = [pro_response, con_response, pro_response, con_response, verdict_response]
        call_count = {"n": 0}

        def mock_call_llm(system, messages, use_search=False):
            idx = call_count["n"] % len(responses)
            call_count["n"] += 1
            return responses[idx], []

        with (
            patch.object(orchestrator._pro, "_call_llm", side_effect=mock_call_llm),
            patch.object(orchestrator._con, "_call_llm", side_effect=mock_call_llm),
            patch.object(orchestrator._father, "_call_llm", side_effect=mock_call_llm),
        ):
            transcript, _ = orchestrator.run()

        roles = [m.from_agent for m in transcript]
        assert roles[0] == AgentRole.PRO
        assert roles[1] == AgentRole.CON
