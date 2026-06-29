"""Tests for ConfigManager."""

from __future__ import annotations

import pytest


class TestConfigManager:
    def test_topic(self, config):
        assert config.topic == "Test topic"

    def test_max_rounds(self, config):
        assert config.max_rounds == 2

    def test_father_model(self, config):
        assert "claude" in config.father_model

    def test_log_dir(self, config):
        assert "logs" in config.log_dir

    def test_budget_usd(self, config):
        assert config.budget_usd == 10.0

    def test_max_retries(self, config):
        assert config.max_retries == 2

    def test_missing_config_raises(self, tmp_path):
        from debate.shared.config import ConfigManager
        with pytest.raises(FileNotFoundError):
            ConfigManager(str(tmp_path / "nonexistent"))
