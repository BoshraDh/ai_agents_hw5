"""GAP TEST-4: verify DebateSDK honours session_id (no data bleed between sessions)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from debate.sdk.sdk import DebateSDK


def _mock_llm_factory(content: str, winner: str = "pro_agent"):
    """Returns a _call_llm mock that returns the given content."""
    verdict = json.dumps({
        "winner": winner,
        "pro_score": 70.0,
        "con_score": 60.0,
        "justification": f"Winner is {winner}.",
        "criterion": "persuasion_power",
        "rounds_evaluated": 2,
    })
    responses = [
        json.dumps({"content": content}),
        json.dumps({"content": f"Counter to: {content}"}),
    ] * 2 + [verdict]
    call_count = {"n": 0}

    def mock_llm(system, messages, use_search=False):
        idx = call_count["n"] % len(responses)
        call_count["n"] += 1
        return responses[idx], []

    return mock_llm


class TestSDKSessionIsolation:
    """GAP-10: get_transcript and get_verdict must use session_id to look up the right data."""

    def test_two_sessions_return_independent_data(self, tmp_path):
        """Running two debates must not bleed data between session IDs."""
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)

        from debate.orchestrator.debate_orchestrator import DebateOrchestrator

        def run_with_mock(content, winner):
            orch = DebateOrchestrator(str(tmp_path / "config"), use_processes=False)
            mock_llm = _mock_llm_factory(content, winner)
            with (
                patch.object(orch._pro, "_call_llm", side_effect=mock_llm),
                patch.object(orch._con, "_call_llm", side_effect=mock_llm),
                patch.object(orch._father, "_call_llm", side_effect=mock_llm),
            ):
                orch.run()
            sid = orch.session_id
            sdk._sessions[sid] = orch
            return sid

        sid_a = run_with_mock("Session A argument", "pro_agent")
        sid_b = run_with_mock("Session B argument", "con_agent")

        assert sid_a != sid_b

        verdict_a = sdk.get_verdict(sid_a)
        verdict_b = sdk.get_verdict(sid_b)

        assert verdict_a is not None
        assert verdict_b is not None
        assert verdict_a["winner"] == "pro_agent"
        assert verdict_b["winner"] == "con_agent"

        transcript_a = sdk.get_transcript(sid_a)
        transcript_b = sdk.get_transcript(sid_b)

        assert any("Session A" in m["content"] for m in transcript_a)
        assert any("Session B" in m["content"] for m in transcript_b)

    def test_unknown_session_returns_empty(self, tmp_path):
        sdk = DebateSDK(str(tmp_path / "config"), use_processes=False)
        assert sdk.get_transcript("nonexistent-id") == []
        assert sdk.get_verdict("nonexistent-id") is None
