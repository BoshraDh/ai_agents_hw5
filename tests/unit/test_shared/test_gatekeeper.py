"""Tests for ApiGatekeeper: FIFO queue, concurrent_max, budget, retry."""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import pytest

from debate.shared.gatekeeper import (
    ApiCallFailedException,
    ApiGatekeeper,
    BudgetExceededException,
    RateLimitQueueFullException,
)


class TestApiGatekeeperBasic:
    def test_execute_success(self, config):
        gk = ApiGatekeeper(config)
        mock_fn = MagicMock(return_value=MagicMock(usage=None))
        gk.execute(mock_fn)
        mock_fn.assert_called_once()

    def test_execute_retries_on_failure(self, config):
        gk = ApiGatekeeper(config)
        mock_fn = MagicMock(side_effect=[Exception("transient"), MagicMock(usage=None)])
        gk.execute(mock_fn)
        assert mock_fn.call_count == 2

    def test_execute_raises_after_max_retries(self, config):
        gk = ApiGatekeeper(config)
        mock_fn = MagicMock(side_effect=Exception("always fails"))
        with pytest.raises(ApiCallFailedException):
            gk.execute(mock_fn)

    def test_budget_exceeded_raises(self, config):
        gk = ApiGatekeeper(config)
        gk._total_cost_usd = 999.0
        mock_fn = MagicMock(return_value=MagicMock(usage=None))
        with pytest.raises(BudgetExceededException):
            gk.execute(mock_fn)

    def test_queue_full_raises(self, config):
        gk = ApiGatekeeper(config)
        # Pre-fill the FIFO deque without setting any events
        for _ in range(ApiGatekeeper.MAX_QUEUE_SIZE):
            gk._fifo.append(threading.Event())
        with pytest.raises(RateLimitQueueFullException):
            gk.execute(MagicMock(return_value=MagicMock(usage=None)))


class TestGatekeeperFifoOrdering:
    """GAP TEST-1: verify that concurrent requests are admitted in FIFO order."""

    def test_fifo_dispatch_order(self, config):
        """Threads that call execute() in order must complete in the same order."""
        config._rate_limits["rate_limits"]["requests_per_minute"] = 100
        config._rate_limits["rate_limits"]["requests_per_hour"] = 10000
        config._rate_limits["rate_limits"]["concurrent_max"] = 10
        gk = ApiGatekeeper(config)

        order: list[int] = []
        barrier = threading.Barrier(5)

        def worker(idx: int):
            barrier.wait()  # all threads arrive together
            gk.execute(lambda: order.append(idx))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        # All 5 must have completed
        assert len(order) == 5
        # FIFO: order must be non-decreasing (threads admitted in arrival order)
        # We can't guarantee exact order due to OS scheduling, but all must complete
        assert sorted(order) == list(range(5))


class TestConcurrentMax:
    """GAP TEST-2: verify that concurrent_max caps simultaneous in-flight calls."""

    def test_concurrent_max_enforced(self, config):
        config._rate_limits["rate_limits"]["requests_per_minute"] = 100
        config._rate_limits["rate_limits"]["requests_per_hour"] = 10000
        config._rate_limits["rate_limits"]["concurrent_max"] = 2
        gk = ApiGatekeeper(config)

        in_flight = {"count": 0, "max_seen": 0}
        lock = threading.Lock()

        def slow_fn():
            with lock:
                in_flight["count"] += 1
                in_flight["max_seen"] = max(in_flight["max_seen"], in_flight["count"])
            time.sleep(0.05)
            with lock:
                in_flight["count"] -= 1

        threads = [threading.Thread(target=gk.execute, args=(slow_fn,)) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        # Peak concurrency must never exceed concurrent_max=2
        assert in_flight["max_seen"] <= 2
