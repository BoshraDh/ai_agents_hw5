"""Tests for ConfigManager — including new GAP-5/6/8/9 properties."""

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

    # GAP-5
    def test_concurrent_max(self, config):
        assert config.concurrent_max == 5

    # GAP-6
    def test_requests_per_hour(self, config):
        assert config.requests_per_hour == 1000

    # GAP-8
    def test_alert_at_usd(self, config):
        assert config.alert_at_usd == 5.0

    # GAP-9
    def test_input_cost_per_million(self, config):
        assert config.input_cost_per_million == 0.25

    def test_output_cost_per_million(self, config):
        assert config.output_cost_per_million == 1.25

    def test_missing_config_raises(self, tmp_path):
        from debate.shared.config import ConfigManager
        with pytest.raises(FileNotFoundError):
            ConfigManager(str(tmp_path / "nonexistent"))
