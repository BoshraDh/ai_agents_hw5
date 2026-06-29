"""Tests for MessageBus IPC wrapper."""

from __future__ import annotations

import pytest

from debate.constants import AgentRole, MessageType
from debate.models.messages import DebateMessage
from debate.shared.message_bus import MessageBus


class TestMessageBus:
    def test_send_and_receive_pro(self):
        bus = MessageBus()
        msg = DebateMessage(
            from_agent=AgentRole.FATHER,
            to_agent=AgentRole.PRO,
            message_type=MessageType.ROUTING,
            round_number=1,
            content="Here is your task",
        )
        bus.send_to_pro(msg)
        received = bus.receive_for_pro(timeout=2.0)
        assert received.message_id == msg.message_id

    def test_send_and_receive_con(self):
        bus = MessageBus()
        msg = DebateMessage(
            from_agent=AgentRole.FATHER,
            to_agent=AgentRole.CON,
            message_type=MessageType.ROUTING,
            round_number=1,
            content="Your turn",
        )
        bus.send_to_con(msg)
        received = bus.receive_for_con(timeout=2.0)
        assert received.content == "Your turn"

    def test_receive_timeout_raises(self):
        bus = MessageBus()
        with pytest.raises(TimeoutError):
            bus.receive_for_pro(timeout=0.1)
