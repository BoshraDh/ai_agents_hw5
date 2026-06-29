"""Configuration manager — reads config/*.json files at startup."""

from __future__ import annotations

import json
from pathlib import Path


class ConfigManager:
    """Loads and provides access to all config/*.json values."""

    def __init__(self, config_dir: str | Path = "config") -> None:
        self._config_dir = Path(config_dir)
        self._setup = self._load("setup.json")
        self._rate_limits = self._load("rate_limits.json")
        self._logging = self._load("logging_config.json")

    def _load(self, filename: str) -> dict:
        path = self._config_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # --- Debate settings ---

    @property
    def topic(self) -> str:
        return self._setup["debate"]["topic"]

    def set_topic(self, value: str) -> None:
        """Update debate topic at runtime (does not write back to disk)."""
        self._setup["debate"]["topic"] = value

    @property
    def pro_position(self) -> str:
        return self._setup["debate"]["pro_position"]

    @property
    def con_position(self) -> str:
        return self._setup["debate"]["con_position"]

    @property
    def max_rounds(self) -> int:
        return int(self._setup["debate"]["max_rounds"])

    @property
    def word_limit(self) -> int:
        return int(self._setup["debate"]["word_limit_per_response"])

    @property
    def father_model(self) -> str:
        return self._setup["agents"]["father_model"]

    @property
    def pro_model(self) -> str:
        return self._setup["agents"]["pro_model"]

    @property
    def con_model(self) -> str:
        return self._setup["agents"]["con_model"]

    @property
    def max_tokens(self) -> int:
        return int(self._setup["agents"]["max_tokens_per_response"])

    @property
    def llm_timeout(self) -> float:
        return float(self._setup["timeouts"]["llm_call_seconds"])

    @property
    def round_timeout(self) -> float:
        """Timeout for a full round-trip through the Father process."""
        return float(self._setup["timeouts"]["round_timeout_seconds"])

    @property
    def heartbeat_interval(self) -> float:
        return float(self._setup["timeouts"]["heartbeat_interval_seconds"])

    @property
    def max_restarts(self) -> int:
        return int(self._setup["watchdog"]["max_restarts_per_process"])

    # --- Rate limit settings ---

    @property
    def requests_per_minute(self) -> int:
        return int(self._rate_limits["rate_limits"]["requests_per_minute"])

    @property
    def requests_per_hour(self) -> int:
        """GAP-6: RPH ceiling, previously unread from config."""
        return int(self._rate_limits["rate_limits"]["requests_per_hour"])

    @property
    def concurrent_max(self) -> int:
        """GAP-5: max simultaneous in-flight API calls."""
        return int(self._rate_limits["rate_limits"]["concurrent_max"])

    @property
    def max_queue_size(self) -> int:
        """Hard cap on Gatekeeper admission queue depth."""
        return int(self._rate_limits["rate_limits"]["max_queue_size"])

    @property
    def max_retries(self) -> int:
        return int(self._rate_limits["retry"]["max_retries"])

    @property
    def retry_backoff(self) -> float:
        return float(self._rate_limits["retry"]["retry_backoff_seconds"])

    @property
    def budget_usd(self) -> float:
        return float(self._rate_limits["budget"]["budget_usd"])

    @property
    def alert_at_usd(self) -> float:
        """GAP-8: budget alert threshold before hitting the ceiling."""
        return float(self._rate_limits["budget"]["alert_at_usd"])

    @property
    def input_cost_per_million(self) -> float:
        """GAP-9: per-million input token cost, read from config (not hardcoded)."""
        return float(self._rate_limits["cost_per_million_tokens"]["input"])

    @property
    def output_cost_per_million(self) -> float:
        """GAP-9: per-million output token cost, read from config (not hardcoded)."""
        return float(self._rate_limits["cost_per_million_tokens"]["output"])

    # --- Logging settings ---

    @property
    def log_dir(self) -> str:
        return self._logging["logging"]["log_dir"]

    @property
    def max_log_files(self) -> int:
        return int(self._logging["logging"]["max_files"])

    @property
    def max_log_lines(self) -> int:
        return int(self._logging["logging"]["max_lines_per_file"])
