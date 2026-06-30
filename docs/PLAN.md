# Architecture & Technical Planning (PLAN)

**Project**: AI Agent Debate System  
**Version**: 1.00  
**Date**: 2026-06-30

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
├── Properties: role, config, gatekeeper, search_tool, _skill_description
├── Methods:
│   ├── _load_skill() → str                   [reads agents/skills/<role>_skill.md]
│   ├── _call_api_once(system, messages, tools) → Any   [single API call + timeout]
│   ├── _call_llm(system, messages, use_search) → tuple[str, list[Citation]]
│   │       loops: tool_use → execute → tool_result → second API call → text
│   ├── _validate_message(msg)                [raises ValueError on empty content]
│   └── run() → None  [abstract — subprocess entry point]
│
├── FatherAgent(BaseAgent)
│   ├── route(message, queue) → None          [no-op when bus=None]
│   └── evaluate_debate(transcript) → Verdict [parses JSON verdict from LLM]
│
├── ProAgent(BaseAgent)
│   └── generate_argument(round_number, prev_con_msg) → DebateMessage
│
└── ConAgent(BaseAgent)
    └── generate_counter(round_number, pro_msg) → DebateMessage
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
| Process model | 3 × `multiprocessing.Process` via `agent_workers.py` | Isolation — one stuck agent cannot block others |
| Worker functions | Module-level in `agent_workers.py` | Required for Windows spawn picklability |
| Process mode | `use_processes=True` (prod) / `False` (tests) | Tests mock `_call_llm` on in-process agents |
| Watchdog | `threading.Thread` | Lightweight; only checks `process.is_alive()` |
| Watchdog error propagation | `threading.Event` + `check_for_fatal_error()` | Daemon thread exceptions are silently swallowed; event allows main thread to raise |
| Gatekeeper FIFO queue | `deque[threading.Event]` + dispatcher thread | True FIFO ordering; tickets admitted in arrival order |
| Gatekeeper concurrency cap | `threading.Semaphore(concurrent_max)` | Hard cap on simultaneous in-flight API calls |

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

### ADR-06: Skill files as external Markdown (§6.2)
**Decision**: Each agent reads its persona/strategy from a `.md` file at construction  
**Rationale**: Assignment §6.2 requires the Skill architecture pattern; externalising prompts makes them editable without code changes  
**Trade-off**: Risk of missing file at startup; mitigated by `_load_skill()` returning `""` gracefully and tests verifying all three files exist

### ADR-07: Round execution extracted to `round_runner.py`
**Decision**: `_round_via_processes` and `_get_verdict_from_father` extracted to `orchestrator/round_runner.py`  
**Rationale**: `debate_orchestrator.py` exceeded the 150-line limit; splitting by concern keeps both files focused  
**Trade-off**: An extra module; import graph grows slightly

---

## 8. SDK API Contract

```python
class DebateSDK:
    def start_debate(self, topic: str | None = None) -> str:
        """Start a new debate. Returns session_id."""

    def get_transcript(self, session_id: str) -> list[dict]:
        """Return all DebateMessages for the session as dicts."""

    def get_verdict(self, session_id: str) -> dict | None:
        """Return the Verdict for the session as a dict, or None."""

    def get_status(self) -> str:
        """Return current DebateStatus as string."""

    def get_config_summary(self) -> dict:
        """Return human-readable config: topic, rounds, models, budget."""

    def set_topic(self, topic: str) -> None:
        """Update the debate topic for the next start_debate() call."""

    def stop(self) -> None:
        """Gracefully stop all session orchestrators."""
```

Session store: `_sessions: dict[str, DebateOrchestrator]` ensures `get_transcript` /
`get_verdict` return correct data when multiple debates have been run.

The CLI imports **only** `DebateSDK`. All other modules are internal.

---

## 9. Skill Architecture (§6.2)

Each agent loads its Skill definition at construction time from `src/debate/agents/skills/`:

| Agent | Skill file | Key persona |
|---|---|---|
| FatherAgent | `father_skill.md` | Impartial Judge — routes, validates, delivers verdict |
| ProAgent | `pro_skill.md` | Research Advocate — evidence-first + logical chain |
| ConAgent | `con_skill.md` | Devil's Advocate — reductio ad absurdum + source rebuttal |

`BaseAgent._load_skill()` reads the file and stores it in `self._skill_description`.
Each subclass injects `{skill_description}` into its system prompt template.

---

## 10. File Size Compliance

Every source file must stay ≤ 150 lines. Current status:

| File | Lines | Status |
|---|---|---|
| `debate_orchestrator.py` | 146 | ✅ (process + watchdog init extracted to `round_runner.py`) |
| `config.py` | 144 | ✅ |
| `gatekeeper.py` | 141 | ✅ |
| `base_agent.py` | 126 | ✅ |
| `round_runner.py` | 119 | ✅ (round logic + process helpers) |
| `watchdog.py` | 101 | ✅ |
| `menu.py` | 92 | ✅ |
| `pro_agent.py` | 86 | ✅ |
| `messages.py` | 83 | ✅ |
| `agent_workers.py` | 79 | ✅ |
| `con_agent.py` | 79 | ✅ |
| `father_agent.py` | 77 | ✅ |
| `sdk.py` | 72 | ✅ |
| All others | ≤67 | ✅ |

All files verified ≤ 150 lines. No further splits needed.
