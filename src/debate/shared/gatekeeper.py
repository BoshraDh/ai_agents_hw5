"""API Gatekeeper — centralized rate limiting, queuing, retry, and budget enforcement."""

from __future__ import annotations

import time
import threading
from collections import deque
from typing import Any, Callable

from debate.shared.config import ConfigManager


class BudgetExceededException(Exception):
    """Raised when cumulative API spend exceeds the configured budget ceiling."""


class ApiCallFailedException(Exception):
    """Raised after max_retries are exhausted without a successful API response."""


class ApiGatekeeper:
    """Controls all Anthropic API calls: rate limit, FIFO queue, retry, budget."""

    def __init__(self, config: ConfigManager) -> None:
        self._config = config
        self._lock = threading.Lock()
        self._request_times: deque[float] = deque()
        self._total_cost_usd: float = 0.0

    def _enforce_rate_limit(self) -> None:
        """Block until a request slot is available within the RPM window."""
        with self._lock:
            now = time.monotonic()
            cutoff = now - 60.0
            while self._request_times and self._request_times[0] < cutoff:
                self._request_times.popleft()
            if len(self._request_times) >= self._config.requests_per_minute:
                sleep_time = 60.0 - (now - self._request_times[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
            self._request_times.append(time.monotonic())

    def _check_budget(self) -> None:
        if self._total_cost_usd >= self._config.budget_usd:
            raise BudgetExceededException(
                f"Budget ${self._config.budget_usd:.2f} exceeded. "
                f"Total spent: ${self._total_cost_usd:.4f}"
            )

    def execute(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute an API call with rate limiting, retries, and budget check."""
        self._check_budget()
        self._enforce_rate_limit()

        last_error: Exception | None = None
        for attempt in range(1, self._config.max_retries + 1):
            try:
                result = fn(*args, **kwargs)
                self._track_cost(result)
                return result
            except Exception as exc:
                last_error = exc
                if attempt < self._config.max_retries:
                    time.sleep(self._config.retry_backoff * attempt)

        raise ApiCallFailedException(
            f"API call failed after {self._config.max_retries} attempts"
        ) from last_error

    def _track_cost(self, response: Any) -> None:
        """Estimate cost from response usage metadata if available."""
        try:
            usage = response.usage
            input_tokens = getattr(usage, "input_tokens", 0)
            output_tokens = getattr(usage, "output_tokens", 0)
            cost = (input_tokens / 1_000_000) * 0.25 + (output_tokens / 1_000_000) * 1.25
            with self._lock:
                self._total_cost_usd += cost
        except AttributeError:
            pass
