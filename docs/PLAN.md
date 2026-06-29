# Architecture & Technical Planning (PLAN)

**Project**: AI Agent Debate System  
**Version**: 1.00  
**Date**: 2026-06-29

---

## 1. System Architecture (C4 Model)

### 1.1 Context Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  User (Student / Grader)                                    │
│  Interacts via terminal keyboard menu                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                   ┌───────▼────────┐
                   │  AI Debate     │
                   │  System        │◄──── Anthropic Claude API
                   │  (Python)      │◄──── DuckDuckGo Search API
                   └───────┬────────┘
                           │
                   writes  ▼
                   ┌───────────────┐
                   │  logs/ JSONL  │
                   │  transcripts  │
                   └───────────────┘
```

### 1.2 Container Diagram

```
┌──────────────────────────────────────────────────────────┐
│  AI Debate System                                        │
│                                                          │
│  ┌──────────┐    ┌──────────────────────────────────┐   │
│  │  CLI     │───►│  DebateSDK (sdk/sdk.py)           │   │
│  │  menu.py │    │  Single public entry point        │   │
│  └──────────┘    └──────────────┬───────────────────┘   │
│                                 │                        │
│                  ┌──────────────▼───────────────────┐   │
│                  │  DebateOrchestrator               │   │
│                  │  + Watchdog (thread)              │   │
│                  └──┬──────────┬──────────┬──────────┘   │
│                     │          │          │              │
│           ┌─────────▼──┐  ┌───▼──────┐  ┌▼──────────┐  │
│           │ ProAgent   │  │FatherAgent│  │ConAgent   │  │
│           │ (process)  │  │(process) │  │(process)  │  │
│           └─────────┬──┘  └───┬──────┘  └┬──────────┘  │
│                     │         │           │             │
│                     └────┬────┘           │             │
│                          │MessageBus      │             │
│                          │(multiprocess   │             │
│                          │ Queue + JSON)  │             │
│                     ┌────▼────────────────▼──────────┐  │
│                     │  ApiGatekeeper                  │  │
│                     │  rate limit + queue + retry     │  │
│                     └────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 1.3 Component Diagram — Agent Layer

```
BaseAgent (ABC)
├── Properties: role, config, gatekeeper, message_bus, search_tool
├── Methods:
│   ├── _call_llm(prompt, tools) → str        [routes through Gatekeeper]
│   ├── _search_web(query) → list[Citation]   [mandatory per argument]
│   ├── _validate_response(msg)               [checks JSON schema]
│   └── _build_system_prompt() → str          [loads from PROMPTS.md section]
│
├── FatherAgent(BaseAgent)
│   ├── route(message, target_queue) → None
│   ├── evaluate_debate(transcript) → Verdict
│   └── is_round_complete(round_n) → bool
│
├── ProAgent(BaseAgent)
│   └── generate_argument(topic, prev_con_msg) → DebateMessage
│
└── ConAgent(BaseAgent)
    └── generate_counter(father_forwarded_msg) → DebateMessage
```

---

## 2. Data Models

### 2.1 DebateMessage (JSON schema)

```json
{
  "message_id": "uuid4",
  "from_agent": "pro_agent | con_agent | father_agent",
  "to_agent": "father_agent | pro_agent | con_agent",
  "message_type": "argument | counter_argument | routing | verdict | heartbeat",
  "round_number": 1,
  "content": "The argument text...",
  "citations": [
    {
      "url": "https://example.com/article",
      "snippet": "Key quote from source",
      "source": "Example News"
    }
  ],
  "word_count": 180,
  "timestamp": "2026-06-29T12:00:00Z",
  "references_message_id": "uuid-of-opponent-last-message | null"
}
```

### 2.2 Verdict (JSON schema)

```json
{
  "winner": "pro_agent | con_agent",
  "pro_score": 72.5,
  "con_score": 65.0,
  "justification": "Pro agent demonstrated stronger rhetorical technique...",
  "criterion": "persuasion_power",
  "rounds_evaluated": 5,
  "timestamp": "2026-06-29T12:05:00Z"
}
```

---

## 3. Message Flow (Sequence)

```
Orchestrator        Pro             Father          Con
     |               |                |               |
     |--start_round->|                |               |
     |               |--generate()--> |               |
     |               |  (search web)  |               |
     |               |  returns JSON  |               |
     |               |--DebateMsg---> |               |
     |               |                |--validate()   |
     |               |                |--route()----->|
     |               |                |               |--generate()
     |               |                |               |  (search web)
     |               |                |               |  returns JSON
     |               |                |<--DebateMsg---|
     |               |                |--validate()   |
     |               |<--forwarded----|               |
     |               |  (next round)  |               |
     |<-transcript---|                |               |
     |               |                |               |
     |--get_verdict->|                |               |
     |               |                |--evaluate()   |
     |               |                |--Verdict----->|
     |<-Verdict------|                |               |
```

---

## 4. IPC Design

| Decision | Choice | Rationale |
|---|---|---|
| IPC mechanism | `multiprocessing.Queue` | Thread-safe, no file I/O, built-in Python |
| Message format | JSON (`DebateMessage`) | Structured, monitorable, token-efficient |
| Process model | 3 × `multiprocessing.Process` | Isolation — one stuck agent cannot block others |
| Watchdog | `threading.Thread` | Lightweight; only checks `process.is_alive()` |

---

## 5. Configuration Architecture

```
config/
├── setup.json          ← debate topic, rounds, agent models, timeouts
├── rate_limits.json    ← RPM, RPH, concurrent_max, retry, budget_usd
└── logging_config.json ← max_files, max_lines_per_file, log_dir
```

All values read by `ConfigManager` at startup. No fallback to hardcoded values.
Config version validated on startup.

---

## 6. Logging Architecture

- Format: JSONL (one JSON object per line)
- Rotation: FIFO — oldest file deleted when `max_files` reached
- Each file capped at `max_lines_per_file` (default: 500)
- Log levels: INFO (messages), WARNING (retries), ERROR (failures), DEBUG (API calls)
- Session transcript: separate file `logs/session_{timestamp}.jsonl`

---

## 7. Architectural Decision Records (ADRs)

### ADR-01: DuckDuckGo over other search providers
**Decision**: Use `duckduckgo-search` Python library  
**Rationale**: Free, no API key required, sufficient citation quality  
**Trade-off**: Less reliable than paid providers; results may vary

### ADR-02: All agents use Anthropic Claude
**Decision**: Father uses `claude-sonnet-4-6`; Pro/Con use `claude-haiku-4-5`  
**Rationale**: Sonnet for better judgment quality; Haiku for cost efficiency  
**Trade-off**: Could use different providers for more genuine diversity; rejected for simplicity

### ADR-03: multiprocessing over asyncio
**Decision**: `multiprocessing.Process` for agents  
**Rationale**: True isolation; LLM calls are blocking I/O; easier Watchdog implementation  
**Trade-off**: Higher memory than asyncio; IPC serialization overhead

### ADR-04: Pydantic for message validation
**Decision**: `pydantic.BaseModel` for `DebateMessage` and `Verdict`  
**Rationale**: Automatic JSON serialization/deserialization; schema enforcement at runtime  
**Trade-off**: Additional dependency; minor performance overhead

### ADR-05: 5 rounds default (budget mode)
**Decision**: Default `max_rounds = 5`  
**Rationale**: Assignment explicitly allows reducing to 5 with README note; no grade penalty  
**Trade-off**: Shorter debate; configurable to 10 if budget permits

---

## 8. SDK API Contract

```python
class DebateSDK:
    def start_debate(self, topic: str | None = None) -> str:
        """Start a new debate. Returns session_id."""

    def get_transcript(self, session_id: str) -> list[dict]:
        """Return all DebateMessages for the session as dicts."""

    def get_verdict(self, session_id: str) -> dict:
        """Return the Verdict for the session as a dict."""

    def get_status(self) -> str:
        """Return current DebateStatus as string."""

    def stop(self) -> None:
        """Gracefully stop the debate and all processes."""
```

The CLI imports **only** `DebateSDK`. All other modules are internal.

---

## 9. File Size Compliance Plan

Every source file must stay ≤ 150 lines. Split strategy:

| If file grows over 150 lines | Split by |
|---|---|
| `base_agent.py` | Extract `_timeout_wrapper.py` mixin |
| `debate_orchestrator.py` | Extract `round_manager.py` |
| `gatekeeper.py` | Extract `queue_manager.py` |
| `messages.py` | Extract `verdict_model.py` |
