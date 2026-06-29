"""Shared pytest fixtures and mocks."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from debate.constants import AgentRole, MessageType
from debate.models.messages import Citation, DebateMessage, Verdict
from debate.shared.config import ConfigManager


@pytest.fixture
def config(tmp_path: Path) -> ConfigManager:
    """ConfigManager pointing at minimal test config files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    setup = {
        "version": "1.00",
        "debate": {
            "topic": "Test topic",
            "pro_position": "Pro position",
            "con_position": "Con position",
            "max_rounds": 2,
            "word_limit_per_response": 100,
        },
        "agents": {
            "father_model": "claude-haiku-4-5-20251001",
            "pro_model": "claude-haiku-4-5-20251001",
            "con_model": "claude-haiku-4-5-20251001",
            "max_tokens_per_response": 256,
        },
        "timeouts": {
            "llm_call_seconds": 5,
            "round_timeout_seconds": 30,
            "heartbeat_interval_seconds": 1,
            "heartbeat_timeout_seconds": 5,
        },
        "watchdog": {"max_restarts_per_process": 2},
    }
    rate_limits = {
        "version": "1.00",
        "rate_limits": {"requests_per_minute": 60, "requests_per_hour": 1000, "concurrent_max": 5},
        "retry": {"max_retries": 2, "retry_backoff_seconds": 0.1, "retry_on_status_codes": [429]},
        "budget": {"budget_usd": 10.0, "alert_at_usd": 5.0},
        "cost_per_million_tokens": {"input": 0.25, "output": 1.25},
    }
    logging_cfg = {
        "version": "1.00",
        "logging": {
            "log_dir": str(tmp_path / "logs"),
            "max_files": 5,
            "max_lines_per_file": 50,
            "log_format": "jsonl",
            "levels": {"debate_messages": "INFO", "api_calls": "DEBUG", "errors": "ERROR", "watchdog": "WARNING"},
        },
    }
    (config_dir / "setup.json").write_text(json.dumps(setup))
    (config_dir / "rate_limits.json").write_text(json.dumps(rate_limits))
    (config_dir / "logging_config.json").write_text(json.dumps(logging_cfg))

    os.environ["ANTHROPIC_API_KEY"] = "test_key"
    return ConfigManager(str(config_dir))


@pytest.fixture
def sample_pro_message() -> DebateMessage:
    return DebateMessage(
        from_agent=AgentRole.PRO,
        to_agent=AgentRole.FATHER,
        message_type=MessageType.ARGUMENT,
        round_number=1,
        content="AI has dramatically improved medical diagnoses.",
        citations=[Citation(url="https://example.com", snippet="AI saves lives", source="MedNews")],
    )


@pytest.fixture
def sample_con_message() -> DebateMessage:
    return DebateMessage(
        from_agent=AgentRole.CON,
        to_agent=AgentRole.FATHER,
        message_type=MessageType.COUNTER_ARGUMENT,
        round_number=1,
        content="AI has displaced millions of workers.",
        citations=[Citation(url="https://example2.com", snippet="Job losses", source="EconReview")],
    )


@pytest.fixture
def sample_verdict() -> Verdict:
    return Verdict(
        winner=AgentRole.PRO,
        pro_score=72.5,
        con_score=65.0,
        justification="Pro demonstrated stronger logical chain.",
        criterion="persuasion_power",
        rounds_evaluated=2,
    )
