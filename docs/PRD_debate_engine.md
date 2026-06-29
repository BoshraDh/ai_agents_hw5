# PRD — Debate Engine (Orchestration Mechanism)

**Component**: `src/debate/orchestrator/debate_orchestrator.py`  
**Version**: 1.00  
**Date**: 2026-06-29

---

## 1. Purpose

The Debate Engine is the central coordinator of the AI debate. It manages the lifecycle
of three agent processes, enforces the turn-based protocol, and produces a complete
debate transcript that the Father agent then uses to render a verdict.

---

## 2. Responsibilities

| Responsibility | Description |
|---|---|
| Process Management | Spawns and terminates ProAgent, FatherAgent, ConAgent processes |
| Round Orchestration | Iterates through N rounds, advancing state correctly |
| Message Routing Enforcement | Ensures all messages go through Father (no child bypass) |
| Timeout Enforcement | Aborts any round that exceeds `timeout_seconds` |
| Transcript Accumulation | Collects all DebateMessages in chronological order |
| Session Logging | Writes full transcript to JSONL file on completion |
| Verdict Retrieval | After final round, asks Father to evaluate and return Verdict |

---

## 3. Functional Requirements

- **FR-E01**: The engine shall spawn exactly three processes: Pro, Father, Con
- **FR-E02**: Each round consists of: Pro generates argument → Father routes to Con → Con generates counter → Father routes to Pro
- **FR-E03**: The engine shall block until each step completes (with timeout)
- **FR-E04**: The engine shall accumulate all messages in a session store (in-memory list)
- **FR-E05**: On completion of all rounds, the engine shall call `FatherAgent.evaluate_debate()`
- **FR-E06**: The engine shall save the transcript JSONL file on exit (whether normal or error)
- **FR-E07**: The engine shall not expose internal queues or processes outside its boundary

---

## 4. Interface

```python
class DebateOrchestrator:
    def __init__(self, config: ConfigManager, gatekeeper: ApiGatekeeper) -> None: ...
    def run(self, topic: str) -> tuple[list[DebateMessage], Verdict]: ...
    def stop(self) -> None: ...
    def get_session_id(self) -> str: ...
```

`run()` blocks until the debate is complete. Returns `(transcript, verdict)`.

---

## 5. Error Handling

| Error Condition | Action |
|---|---|
| Agent process dies | Watchdog thread restarts it; Orchestrator retries the round |
| LLM call times out | Abort the round; log error; skip to next round |
| Budget exceeded | Raise `BudgetExceededException`; save partial transcript |
| All rounds timeout | Return partial transcript; Father evaluates available data |

---

## 6. Dependencies

- `shared/message_bus.py` — IPC Queues
- `shared/gatekeeper.py` — All API calls
- `shared/logger.py` — Event logging
- `shared/config.py` — Round count, timeout values
- `orchestrator/watchdog.py` — Process health monitoring
- `agents/father_agent.py`, `agents/pro_agent.py`, `agents/con_agent.py`
- `models/messages.py` — DebateMessage, Verdict schemas
