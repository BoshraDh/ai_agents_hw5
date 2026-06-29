"""API Gatekeeper — FIFO queue, concurrent_max, RPM+RPH limits, budget enforcement."""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Callable

from debate.shared.config import ConfigManager


class BudgetExceededException(Exception):
    """Raised when cumulative spend exceeds budget_usd."""


class ApiCallFailedException(Exception):
    """Raised after max_retries exhausted without a successful response."""


class RateLimitQueueFullException(Exception):
    """GAP-7: raised when FIFO admission queue hits its hard cap."""


class ApiGatekeeper:
    """Controls all Anthropic API calls: FIFO queue, concurrent_max, RPM+RPH, budget."""

    MAX_QUEUE_SIZE = 50

    def __init__(self, config: ConfigManager) -> None:
        self._config = config
        # GAP-5: semaphore enforces concurrent_max in-flight calls
        self._concurrent_sem = threading.Semaphore(config.concurrent_max)
        # GAP-4: deque of Event tickets — FIFO admission queue
        self._fifo: deque[threading.Event] = deque()
        self._fifo_lock = threading.Lock()
        # GAP-6: track both RPM and RPH windows
        self._rpm_times: deque[float] = deque()
        self._rph_times: deque[float] = deque()
        self._rate_lock = threading.Lock()
        # Budget tracking
        self._total_cost_usd: float = 0.0
        self._cost_lock = threading.Lock()
        self._alert_logged = False
        # Background dispatcher drives FIFO queue
        threading.Thread(
            target=self._dispatch_loop, daemon=True, name="GKDispatcher"
        ).start()

    # ------------------------------------------------------------------ public

    def execute(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute an API call under FIFO rate limiting, concurrency cap, and budget check."""
        self._check_budget()
        # Obtain a FIFO ticket
        ticket = threading.Event()
        with self._fifo_lock:
            if len(self._fifo) >= self.MAX_QUEUE_SIZE:
                raise RateLimitQueueFullException("Gatekeeper admission queue is full")
            self._fifo.append(ticket)
        ticket.wait()  # Block until dispatcher admits this request (FIFO order)
        # Enforce concurrent_max — block if too many calls are in flight
        with self._concurrent_sem:
            return self._run_with_retry(fn, *args, **kwargs)

    # ----------------------------------------------------------------- private

    def _dispatch_loop(self) -> None:
        """Background thread: admit queued tickets in FIFO order when rate allows."""
        while True:
            admitted = False
            with self._fifo_lock:
                if self._fifo:
                    with self._rate_lock:
                        if self._can_admit():
                            ticket = self._fifo.popleft()
                            now = time.monotonic()
                            self._rpm_times.append(now)
                            self._rph_times.append(now)
                            ticket.set()
                            admitted = True
            if not admitted:
                time.sleep(0.05)

    def _can_admit(self) -> bool:
        """True when both RPM and RPH windows have capacity. Caller holds _rate_lock."""
        now = time.monotonic()
        while self._rpm_times and self._rpm_times[0] < now - 60.0:
            self._rpm_times.popleft()
        while self._rph_times and self._rph_times[0] < now - 3600.0:
            self._rph_times.popleft()
        return (
            len(self._rpm_times) < self._config.requests_per_minute
            and len(self._rph_times) < self._config.requests_per_hour
        )

    def _run_with_retry(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        last_err: Exception | None = None
        for attempt in range(1, self._config.max_retries + 1):
            try:
                result = fn(*args, **kwargs)
                self._track_cost(result)
                return result
            except Exception as exc:
                last_err = exc
                if attempt < self._config.max_retries:
                    time.sleep(self._config.retry_backoff * attempt)
        raise ApiCallFailedException(
            f"API call failed after {self._config.max_retries} attempts"
        ) from last_err

    def _check_budget(self) -> None:
        with self._cost_lock:
            if self._total_cost_usd >= self._config.budget_usd:
                raise BudgetExceededException(
                    f"Budget ${self._config.budget_usd:.2f} exceeded "
                    f"(spent ${self._total_cost_usd:.4f})"
                )

    def _track_cost(self, response: Any) -> None:
        """GAP-9: cost rates from config, not hardcoded. GAP-8: alert_at_usd warning."""
        try:
            usage = response.usage
            tokens_in = getattr(usage, "input_tokens", 0)
            tokens_out = getattr(usage, "output_tokens", 0)
            cost = (
                (tokens_in / 1_000_000) * self._config.input_cost_per_million
                + (tokens_out / 1_000_000) * self._config.output_cost_per_million
            )
            with self._cost_lock:
                self._total_cost_usd += cost
                if not self._alert_logged and self._total_cost_usd >= self._config.alert_at_usd:
                    self._alert_logged = True
                    import warnings
                    warnings.warn(
                        f"[Gatekeeper] Budget alert: ${self._total_cost_usd:.4f} spent "
                        f"(alert threshold ${self._config.alert_at_usd:.2f})",
                        stacklevel=3,
                    )
        except AttributeError:
            pass
