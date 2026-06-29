"""Tests for ConAgent counter-argument generation."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from debate.agents.con_agent import ConAgent
from debate.constants import AgentRole, MessageType
from debate.shared.gatekeeper import ApiGatekeeper
from debate.shared.message_bus import MessageBus


@pytest.fixture
def con(config):
    gk = ApiGatekeeper(config)
    bus = MessageBus()
    return ConAgent(config, gk, bus)


class TestConAgent:
    def test_role_is_con(self, con):
        assert con.role == AgentRole.CON

    def test_generate_counter_references_pro_msg(self, con, sample_pro_message):
        mock_response = json.dumps({
            "content": "AI causes more harm than good as shown by job losses.",
            "citations": [],
        })
        with patch.object(con, "_call_llm", return_value=(mock_response, [])):
            msg = con.generate_counter(1, sample_pro_message)

        assert msg.from_agent == AgentRole.CON
        assert msg.to_agent == AgentRole.FATHER
        assert msg.message_type == MessageType.COUNTER_ARGUMENT
        assert msg.references_message_id == sample_pro_message.message_id

    def test_generate_counter_round_number(self, con, sample_pro_message):
        mock_response = json.dumps({"content": "Counter.", "citations": []})
        with patch.object(con, "_call_llm", return_value=(mock_response, [])):
            msg = con.generate_counter(3, sample_pro_message)
        assert msg.round_number == 3
