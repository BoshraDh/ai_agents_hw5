"""Pydantic models for all inter-agent JSON messages."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

from debate.constants import AgentRole, MessageType


class Citation(BaseModel):
    """A single internet citation accompanying an argument."""

    url: str
    snippet: str
    source: str


class DebateMessage(BaseModel):
    """JSON message passed between agents via the MessageBus."""

    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: AgentRole
    to_agent: AgentRole
    message_type: MessageType
    round_number: int
    content: str
    citations: list[Citation] = Field(default_factory=list)
    word_count: int = 0
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    references_message_id: str | None = None

    @field_validator("word_count", mode="before")
    @classmethod
    def compute_word_count(cls, v: int, info) -> int:
        """Auto-compute word_count from content if not provided."""
        if v == 0 and "content" in (info.data or {}):
            return len(info.data["content"].split())
        return v

    def to_json(self) -> str:
        """Serialize to JSON string for IPC transport."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> "DebateMessage":
        """Deserialize from JSON string."""
        return cls.model_validate_json(data)


class Verdict(BaseModel):
    """Final judgment rendered by the Father agent after all rounds."""

    winner: AgentRole
    pro_score: float
    con_score: float
    justification: str
    criterion: str = "persuasion_power"
    rounds_evaluated: int
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @field_validator("winner")
    @classmethod
    def winner_must_not_be_father(cls, v: AgentRole) -> AgentRole:
        """Father cannot win the debate."""
        if v == AgentRole.FATHER:
            raise ValueError("Verdict winner must be pro_agent or con_agent, not father_agent")
        return v

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> "Verdict":
        """Deserialize from JSON string."""
        return cls.model_validate_json(data)
