"""Tests for FatherAgent routing and verdict evaluation."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from debate.agents.father_agent import FatherAgent
from debate.constants import AgentRole, MessageType
from debate.models.messages import DebateMessage
from debate.shared.gatekeeper import ApiGatekeeper
from debate.shared.message_bus import MessageBus


@pytest.fixture
def father(config):
    gk = ApiGatekeeper(config)
    bus = MessageBus()
    return FatherAgent(config, gk, bus)


class TestFatherAgent:
    def test_route_to_pro(self, father):
        msg = DebateMessage(
            from_agent=AgentRole.CON,
            to_agent=AgentRole.PRO,
            message_type=MessageType.ROUTING,
            round_number=1,
            content="For Pro",
        )
        father.route(msg)
        received = father._bus.receive_for_pro(timeout=1.0)
        assert received.message_id == msg.message_id

    def test_route_to_con(self, father):
        msg = DebateMessage(
            from_agent=AgentRole.PRO,
            to_agent=AgentRole.CON,
            message_type=MessageType.ROUTING,
            round_number=1,
            content="For Con",
        )
        father.route(msg)
        received = father._bus.receive_for_con(timeout=1.0)
        assert received.message_id == msg.message_id

    def test_evaluate_debate_returns_verdict(self, father, sample_pro_message, sample_con_message):
        verdict_json = json.dumps({
            "winner": "pro_agent",
            "pro_score": 75.0,
            "con_score": 60.0,
            "justification": "Pro was more persuasive.",
            "criterion": "persuasion_power",
            "rounds_evaluated": 1,
        })
        with patch.object(father, "_call_llm", return_value=(verdict_json, [])):
            verdict = father.evaluate_debate([sample_pro_message, sample_con_message])
        assert verdict.winner == AgentRole.PRO

    def test_evaluate_invalid_json_raises(self, father, sample_pro_message):
        with (
            patch.object(father, "_call_llm", return_value=("not json", [])),
            pytest.raises(ValueError, match="invalid Verdict JSON"),
        ):
            father.evaluate_debate([sample_pro_message])
