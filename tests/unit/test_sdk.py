"""Tests for DebateSDK — the single public interface."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from debate.sdk.sdk import DebateSDK


def _mock_llm(content: str, winner: str = "pro_agent"):
    verdict = json.dumps({
        "winner": winner,
        "pro_score": 72.0,
        "con_score": 60.0,
        "justification": "Better evidence chain.",
        "criterion": "persuasion_power",
        "rounds_evaluated": 2,
    })
    responses = [
        json.dumps({"content": content}),
        json.dumps({"content": f"Counter: {content}"}),
    ] * 3 + [verdict]
    counter = {"n": 0}

    def _call(system, messages, use_search=False):
        idx = counter["n"] % len(responses)
        counter["n"] += 1
        return responses[idx], []

    return _call


class TestDebateSDKInterface:
    def test_start_debate_returns_string_session_id(self, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        from debate.orchestrator.debate_orchestrator import DebateOrchestrator
        orch = DebateOrchestrator(str(tmp_path / "config"), use_processes=False)
        mock = _mock_llm("AI helps doctors.")
        with (
            patch.object(orch._pro, "_call_llm", side_effect=mock),
            patch.object(orch._con, "_call_llm", side_effect=mock),
            patch.object(orch._father, "_call_llm", side_effect=mock),
        ):
            orch.run()
        sid = orch.session_id
        sdk._sessions[sid] = orch
        assert isinstance(sid, str) and len(sid) > 0

    def test_get_transcript_returns_list(self, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        from debate.orchestrator.debate_orchestrator import DebateOrchestrator
        orch = DebateOrchestrator(str(tmp_path / "config"), use_processes=False)
        mock = _mock_llm("AI cures cancer.")
        with (
            patch.object(orch._pro, "_call_llm", side_effect=mock),
            patch.object(orch._con, "_call_llm", side_effect=mock),
            patch.object(orch._father, "_call_llm", side_effect=mock),
        ):
            orch.run()
        sid = orch.session_id
        sdk._sessions[sid] = orch
        transcript = sdk.get_transcript(sid)
        assert isinstance(transcript, list)
        assert len(transcript) > 0

    def test_get_verdict_returns_dict_with_winner(self, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        from debate.orchestrator.debate_orchestrator import DebateOrchestrator
        orch = DebateOrchestrator(str(tmp_path / "config"), use_processes=False)
        mock = _mock_llm("AI assists surgeons.", winner="pro_agent")
        with (
            patch.object(orch._pro, "_call_llm", side_effect=mock),
            patch.object(orch._con, "_call_llm", side_effect=mock),
            patch.object(orch._father, "_call_llm", side_effect=mock),
        ):
            orch.run()
        sid = orch.session_id
        sdk._sessions[sid] = orch
        verdict = sdk.get_verdict(sid)
        assert verdict is not None
        assert "winner" in verdict

    def test_get_transcript_unknown_session_returns_empty(self, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        assert sdk.get_transcript("no-such-id") == []

    def test_get_verdict_unknown_session_returns_none(self, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        assert sdk.get_verdict("no-such-id") is None

    def test_get_status_returns_string(self, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        status = sdk.get_status()
        assert isinstance(status, str)
