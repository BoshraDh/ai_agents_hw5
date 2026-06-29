"""Tests for ApiGatekeeper."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from debate.shared.gatekeeper import (
    ApiCallFailedException,
    ApiGatekeeper,
    BudgetExceededException,
)


class TestApiGatekeeper:
    def test_execute_success(self, config):
        gk = ApiGatekeeper(config)
        mock_fn = MagicMock(return_value=MagicMock(usage=None))
        result = gk.execute(mock_fn)
        mock_fn.assert_called_once()

    def test_execute_retries_on_failure(self, config):
        gk = ApiGatekeeper(config)
        mock_fn = MagicMock(side_effect=[Exception("transient"), MagicMock(usage=None)])
        result = gk.execute(mock_fn)
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
