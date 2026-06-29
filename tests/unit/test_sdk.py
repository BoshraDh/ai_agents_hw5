"""Tests for DebateSDK — the single public interface."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from debate.constants import DebateStatus
from debate.orchestrator.debate_orchestrator import DebateOrchestrator
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
    ] * 2 + [verdict]
    counter = {"n": 0}

    def _call(system, messages, use_search=False):
        idx = counter["n"] % len(responses)
        counter["n"] += 1
        return responses[idx], []

    return _call


def _run_mocked_orch(config_dir: str, content: str, winner: str = "pro_agent") -> DebateOrchestrator:
    orch = DebateOrchestrator(config_dir, use_processes=False)
    mock = _mock_llm(content, winner)
    with (
        patch.object(orch._pro, "_call_llm", side_effect=mock),
        patch.object(orch._con, "_call_llm", side_effect=mock),
        patch.object(orch._father, "_call_llm", side_effect=mock),
    ):
        orch.run()
    return orch


class TestDebateSDKInterface:
    def test_start_debate_returns_string_session_id(self, config, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        orch = _run_mocked_orch(str(tmp_path / "config"), "AI helps doctors.")
        sid = orch.session_id
        sdk._sessions[sid] = orch
        assert isinstance(sid, str) and len(sid) > 0

    def test_get_transcript_returns_list(self, config, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        orch = _run_mocked_orch(str(tmp_path / "config"), "AI cures cancer.")
        sid = orch.session_id
        sdk._sessions[sid] = orch
        transcript = sdk.get_transcript(sid)
        assert isinstance(transcript, list)
        assert len(transcript) > 0

    def test_get_verdict_returns_dict_with_winner(self, config, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        orch = _run_mocked_orch(str(tmp_path / "config"), "AI assists surgeons.", winner="pro_agent")
        sid = orch.session_id
        sdk._sessions[sid] = orch
        verdict = sdk.get_verdict(sid)
        assert verdict is not None
        assert "winner" in verdict

    def test_get_transcript_unknown_session_returns_empty(self, config, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        assert sdk.get_transcript("no-such-id") == []

    def test_get_verdict_unknown_session_returns_none(self, config, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        assert sdk.get_verdict("no-such-id") is None

    def test_get_status_returns_string(self, config, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        status = sdk.get_status()
        assert isinstance(status, str)

    def test_get_status_with_sessions(self, config, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        mock_orch = MagicMock()
        mock_orch.status = DebateStatus.COMPLETED
        sdk._sessions["sess-1"] = mock_orch
        assert sdk.get_status() == DebateStatus.COMPLETED.value

    def test_get_config_summary_has_required_keys(self, config, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        summary = sdk.get_config_summary()
        assert "topic" in summary
        assert "budget_usd" in summary
        assert "max_rounds" in summary

    def test_set_topic_updates_topic(self, config, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        sdk.set_topic("New topic for testing")
        assert sdk.get_config_summary()["topic"] == "New topic for testing"

    def test_stop_clears_sessions(self, config, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        mock_orch = MagicMock()
        sdk._sessions["sess-1"] = mock_orch
        sdk.stop()
        assert len(sdk._sessions) == 0
