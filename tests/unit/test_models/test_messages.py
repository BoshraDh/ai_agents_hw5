"""Tests for DebateMessage, Verdict, and Citation Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from debate.constants import AgentRole, MessageType
from debate.models.messages import Citation, DebateMessage, Verdict


class TestCitation:
    def test_valid_citation(self):
        c = Citation(url="https://example.com", snippet="Some text", source="Example")
        assert c.url == "https://example.com"

    def test_fields_required(self):
        with pytest.raises(ValidationError):
            Citation(url="https://example.com")


class TestDebateMessage:
    def test_auto_message_id(self):
        msg = DebateMessage(
            from_agent=AgentRole.PRO,
            to_agent=AgentRole.FATHER,
            message_type=MessageType.ARGUMENT,
            round_number=1,
            content="Test argument",
        )
        assert msg.message_id is not None
        assert len(msg.message_id) == 36  # UUID4 format

    def test_auto_timestamp(self):
        msg = DebateMessage(
            from_agent=AgentRole.PRO,
            to_agent=AgentRole.FATHER,
            message_type=MessageType.ARGUMENT,
            round_number=1,
            content="Test argument",
        )
        assert "T" in msg.timestamp

    def test_json_roundtrip(self):
        msg = DebateMessage(
            from_agent=AgentRole.PRO,
            to_agent=AgentRole.FATHER,
            message_type=MessageType.ARGUMENT,
            round_number=1,
            content="Hello debate world",
            citations=[Citation(url="https://x.com", snippet="x", source="X")],
        )
        restored = DebateMessage.from_json(msg.to_json())
        assert restored.message_id == msg.message_id
        assert restored.content == msg.content
        assert len(restored.citations) == 1

    def test_references_message_id_optional(self):
        msg = DebateMessage(
            from_agent=AgentRole.CON,
            to_agent=AgentRole.FATHER,
            message_type=MessageType.COUNTER_ARGUMENT,
            round_number=1,
            content="Counter argument",
        )
        assert msg.references_message_id is None

    def test_references_message_id_set(self):
        msg = DebateMessage(
            from_agent=AgentRole.CON,
            to_agent=AgentRole.FATHER,
            message_type=MessageType.COUNTER_ARGUMENT,
            round_number=1,
            content="Counter argument",
            references_message_id="some-uuid",
        )
        assert msg.references_message_id == "some-uuid"


class TestVerdict:
    def test_valid_verdict(self):
        v = Verdict(
            winner=AgentRole.PRO,
            pro_score=75.0,
            con_score=60.0,
            justification="Pro was more persuasive.",
            rounds_evaluated=5,
        )
        assert v.winner == AgentRole.PRO
        assert v.criterion == "persuasion_power"

    def test_father_cannot_win(self):
        with pytest.raises(ValidationError):
            Verdict(
                winner=AgentRole.FATHER,
                pro_score=50.0,
                con_score=50.0,
                justification="Tie.",
                rounds_evaluated=5,
            )

    def test_json_roundtrip(self):
        v = Verdict(
            winner=AgentRole.CON,
            pro_score=60.0,
            con_score=80.0,
            justification="Con was better.",
            rounds_evaluated=3,
        )
        restored = Verdict.from_json(v.to_json())
        assert restored.winner == AgentRole.CON
        assert restored.pro_score == 60.0
