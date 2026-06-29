"""Tests for DebateLogger FIFO rotation."""

from __future__ import annotations

import json
from pathlib import Path

from debate.shared.logger import DebateLogger


class TestDebateLogger:
    def test_creates_log_file(self, config):
        logger = DebateLogger(config, "test-session")
        logger.info("TEST_EVENT", detail="hello")
        log_dir = Path(config.log_dir)
        files = list(log_dir.glob("debate_*.jsonl"))
        assert len(files) >= 1

    def test_log_content_is_valid_jsonl(self, config):
        logger = DebateLogger(config, "test-session")
        logger.info("TEST_EVENT", key="value")
        log_dir = Path(config.log_dir)
        files = sorted(log_dir.glob("debate_*.jsonl"))
        with open(files[-1]) as f:
            lines = f.readlines()
        record = json.loads(lines[-1])
        assert record["level"] == "INFO"
        assert record["event"] == "TEST_EVENT"

    def test_rotation_deletes_oldest(self, config):
        config._logging["logging"]["max_files"] = 3
        config._logging["logging"]["max_lines_per_file"] = 1
        logger = DebateLogger(config, "rotation-test")
        for i in range(6):
            logger.info(f"EVENT_{i}")
        log_dir = Path(config.log_dir)
        files = list(log_dir.glob("debate_*.jsonl"))
        assert len(files) <= 3

    def test_save_transcript(self, config, sample_pro_message):
        logger = DebateLogger(config, "transcript-test")
        path = logger.save_transcript([sample_pro_message.model_dump()])
        assert path.exists()
        with open(path) as f:
            line = json.loads(f.readline())
        assert line["from_agent"] == "pro_agent"
