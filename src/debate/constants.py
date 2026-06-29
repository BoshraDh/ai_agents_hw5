"""Shared enums and constants for the AI Debate system."""

from enum import Enum


class AgentRole(str, Enum):
    """Identifies which agent sent or is receiving a message."""

    FATHER = "father_agent"
    PRO = "pro_agent"
    CON = "con_agent"


class MessageType(str, Enum):
    """Classifies the purpose of a DebateMessage."""

    ARGUMENT = "argument"
    COUNTER_ARGUMENT = "counter_argument"
    ROUTING = "routing"
    VERDICT = "verdict"
    HEARTBEAT = "heartbeat"
    REJECTION = "rejection"


class DebateStatus(str, Enum):
    """Current lifecycle state of the debate session."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
