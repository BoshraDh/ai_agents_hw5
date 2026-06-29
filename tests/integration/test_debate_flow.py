"""Integration test — full debate flow with all Anthropic calls mocked.

Uses use_processes=False so patches on agent instances take effect
(multiprocessing would create separate memory spaces where patches don't propagate).
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from debate.constants import AgentRole
from debate.orchestrator.debate_orchestrator import DebateOrchestrator


def _make_pro_resp():
    return json.dumps({"content": "AI saved 1M lives via early cancer detection."})


def _make_con_resp():
    return json.dumps({"content": "AI surveillance has imprisoned innocent people."})


def _make_verdict():
    return json.dumps({
        "winner": "pro_agent",
        "pro_score": 78.0,
        "con_score": 65.0,
        "justification": "Pro demonstrated stronger evidence chain.",
        "criterion": "persuasion_power",
        "rounds_evaluated": 2,
    })


@pytest.fixture
def orchestrator(config, tmp_path):
    """DebateOrchestrator in synchronous mode so mocks work correctly.

    The `config` fixture writes test configs to tmp_path/config, so
    we must point DebateOrchestrator at that same directory.
    """
    return DebateOrchestrator(str(tmp_path / "config"), use_processes=False)


class TestDebateFlow:
    def test_full_debate_returns_transcript_and_verdict(self, orchestrator):
        responses = [_make_pro_resp(), _make_con_resp()] * 2 + [_make_verdict()]
        call_count = {"n": 0}

        def mock_llm(system, messages, use_search=False):
            idx = call_count["n"] % len(responses)
            call_count["n"] += 1
            return responses[idx], []

        with (
            patch.object(orchestrator._pro, "_call_llm", side_effect=mock_llm),
            patch.object(orchestrator._con, "_call_llm", side_effect=mock_llm),
            patch.object(orchestrator._father, "_call_llm", side_effect=mock_llm),
        ):
            transcript, verdict = orchestrator.run()

        assert len(transcript) == orchestrator._config.max_rounds * 2
        assert verdict.winner in (AgentRole.PRO, AgentRole.CON)
        assert verdict.criterion == "persuasion_power"

    def test_transcript_has_alternating_agents(self, orchestrator):
        call_count = {"n": 0}
        responses = [_make_pro_resp(), _make_con_resp()] * 2 + [_make_verdict()]

        def mock_llm(system, messages, use_search=False):
            idx = call_count["n"] % len(responses)
            call_count["n"] += 1
            return responses[idx], []

        with (
            patch.object(orchestrator._pro, "_call_llm", side_effect=mock_llm),
            patch.object(orchestrator._con, "_call_llm", side_effect=mock_llm),
            patch.object(orchestrator._father, "_call_llm", side_effect=mock_llm),
        ):
            transcript, _ = orchestrator.run()

        roles = [m.from_agent for m in transcript]
        assert roles[0] == AgentRole.PRO
        assert roles[1] == AgentRole.CON

    def test_session_id_is_returned(self, orchestrator):
        call_count = {"n": 0}
        responses = [_make_pro_resp(), _make_con_resp()] * 2 + [_make_verdict()]

        def mock_llm(system, messages, use_search=False):
            idx = call_count["n"] % len(responses)
            call_count["n"] += 1
            return responses[idx], []

        with (
            patch.object(orchestrator._pro, "_call_llm", side_effect=mock_llm),
            patch.object(orchestrator._con, "_call_llm", side_effect=mock_llm),
            patch.object(orchestrator._father, "_call_llm", side_effect=mock_llm),
        ):
            orchestrator.run()

        assert len(orchestrator.session_id) == 8
        assert orchestrator.get_session_id() == orchestrator.session_id
