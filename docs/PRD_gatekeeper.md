# PRD — API Gatekeeper

**Component**: `src/debate/shared/gatekeeper.py`  
**Version**: 1.00  
**Date**: 2026-06-29

---

## 1. Purpose

The API Gatekeeper is a centralized controller for all calls to the Anthropic API.
No agent, tool, or service may call the Anthropic API directly — all calls must pass
through the Gatekeeper. This provides rate limiting, budget enforcement, retry logic,
and usage telemetry in one place.

---

## 2. Responsibilities

| Responsibility | Description |
|---|---|
| Rate Limiting | Enforce `requests_per_minute` and `requests_per_hour` ceilings |
| FIFO Queuing | When rate-limited, queue requests in arrival order (no drops) |
| Retry on Failure | Retry transient errors (429, 503) up to `max_retries` with backoff |
| Budget Enforcement | Track cumulative spend; halt if `budget_usd` exceeded |
| Token Logging | Log input tokens, output tokens, estimated cost per call |
| Concurrency Control | Limit simultaneous in-flight API calls to `concurrent_max` |

---

## 3. Functional Requirements

- **FR-G01**: All API calls shall pass through `ApiGatekeeper.execute()`
- **FR-G02**: If RPM limit is reached, the request shall be queued (not rejected)
- **FR-G03**: Queued requests shall be dispatched in FIFO order as capacity permits
- **FR-G04**: Transient API errors (rate limit errors, server errors) shall trigger retry
- **FR-G05**: Each retry shall wait `retry_backoff_seconds × attempt_number` before retry
- **FR-G06**: After `max_retries` exhausted, raise `ApiCallFailedException`
- **FR-G07**: If cumulative cost exceeds `budget_usd`, raise `BudgetExceededException`
- **FR-G08**: The Gatekeeper shall be thread-safe (shared across processes is NOT required — each process instantiates its own Gatekeeper)

---

## 4. Interface

```python
class ApiGatekeeper:
    def __init__(self, config: ConfigManager) -> None: ...

    def execute(self, fn: Callable, *args, **kwargs) -> Any:
        """Execute an API call function under rate limit + retry protection."""
```

Usage:

```python
response = gatekeeper.execute(
    anthropic_client.messages.create,
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    messages=[...]
)
```

---

## 5. Configuration (from `config/rate_limits.json`)

```json
{
  "version": "1.00",
  "rate_limits": {
    "requests_per_minute": 30,
    "requests_per_hour": 500,
    "concurrent_max": 3
  },
  "retry": {
    "max_retries": 3,
    "retry_backoff_seconds": 2.0,
    "retry_on_status_codes": [429, 503, 500]
  },
  "budget": {
    "budget_usd": 5.0,
    "alert_at_usd": 3.0
  }
}
```

---

## 6. Custom Exceptions

```python
class BudgetExceededException(Exception):
    """Raised when cumulative API spend exceeds budget_usd."""

class ApiCallFailedException(Exception):
    """Raised after max_retries exhausted without a successful response."""

class RateLimitQueueFullException(Exception):
    """Raised if internal FIFO queue reaches a hard cap (safety valve)."""
```

---

## 7. Dependencies

- `shared/config.py` — Rate limit and retry config
- `shared/logger.py` — Token usage logging
- `anthropic` SDK — Actual API calls (passed in as callable)
