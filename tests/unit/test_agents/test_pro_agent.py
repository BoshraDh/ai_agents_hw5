"""Tests for ProAgent argument generation."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from debate.agents.pro_agent import ProAgent
from debate.constants import AgentRole, MessageType
from debate.models.messages import Citation, DebateMessage
from debate.shared.gatekeeper import ApiGatekeeper
from debate.shared.message_bus import MessageBus


@pytest.fixture
def pro(config):
    gk = ApiGatekeeper(config)
    bus = MessageBus()
    return ProAgent(config, gk, bus)


class TestProAgent:
    def test_role_is_pro(self, pro):
        assert pro.role == AgentRole.PRO

    def test_generate_argument_opening(self, pro):
        expected_content = "AI has created 3.5M new jobs in the last decade."
        mock_response = json.dumps({
            "content": expected_content,
            "citations": [],
        })
        mock_citation = Citation(url="https://example.com", snippet="x", source="X")
        with patch.object(pro, "_call_llm", return_value=(mock_response, [mock_citation])):
            msg = pro.generate_argument(1, None)

        assert msg.from_agent == AgentRole.PRO
        assert msg.to_agent == AgentRole.FATHER
        assert msg.message_type == MessageType.ARGUMENT
        assert msg.round_number == 1
        assert msg.references_message_id is None
        assert expected_content in msg.content

    def test_generate_argument_with_opponent_msg(self, pro, sample_con_message):
        mock_response = json.dumps({"content": "My rebuttal.", "citations": []})
        with patch.object(pro, "_call_llm", return_value=(mock_response, [])):
            msg = pro.generate_argument(2, sample_con_message)

        assert msg.references_message_id == sample_con_message.message_id
        assert msg.round_number == 2
