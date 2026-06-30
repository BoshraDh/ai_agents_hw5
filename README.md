# AI Agent Debate — Assignment 5

**Course**: Orchestration for AI Agents | Dr. Yoram Segal  
**Assignment**: Exercise 02 — AI Agent Debate  
**Author**: Boshra Dhamshy  
**Version**: 1.00

---

## Overview

This project implements a **three-agent AI debate system** in Python.  
A Father agent (Judge) moderates a structured debate between a Pro agent and a Con agent
on the topic: **"Is AI a threat or a benefit to humanity?"**

All agents communicate exclusively via JSON messages. The Father routes every message —
child agents never communicate directly. After the debate rounds conclude, the Father
delivers a verdict based solely on **persuasion power** (not factual correctness).

### Architecture at a Glance

```
┌────────────────────────────────────────────┐
│   CLI / SDK  (single entry point)          │
└──────────────────┬─────────────────────────┘
                   │
          DebateOrchestrator
         /          |          \
   [PRO Process] [FATHER Process] [CON Process]
        │               │               │
        └───────────────┼───────────────┘
                   MessageBus (JSON)
                        │
                   ApiGatekeeper
                        │
                  Anthropic API
```

---

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Anthropic API key

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/BoshraDh/ai_agents_hw5.git
cd ai_agents_hw5

# 2. Copy environment template and add your API key
cp .env-example .env
# Edit .env and set ANTHROPIC_API_KEY=your_key_here

# 3. Install dependencies via uv
uv sync
```

---

## Usage

### Run the debate (terminal menu)

```bash
uv run python src/main.py
```

You will see:

```
=== AI Debate System v1.00 ===
1. Start new debate
2. View last transcript
3. View verdict
4. Change debate topic
5. Show configuration
6. Exit

Enter choice:
```

### Run via SDK directly

```python
from debate.sdk.sdk import DebateSDK

sdk = DebateSDK()
session_id = sdk.start_debate()
transcript = sdk.get_transcript(session_id)
verdict = sdk.get_verdict(session_id)
print(verdict)
```

### Run tests

```bash
uv run pytest tests/ --cov=src --cov-report=term-missing
```

### Run linter

```bash
uv run ruff check .
```

---

## Configuration

All parameters are stored in `config/` — no hardcoded values in source code.

| File | Purpose |
|---|---|
| `config/setup.json` | Debate topic, rounds, timeouts, model names |
| `config/rate_limits.json` | API rate limits, budget ceiling, retry config |
| `config/logging_config.json` | FIFO log rotation settings |

**Key settings in `config/setup.json`**:

```json
{
  "version": "1.00",
  "debate": {
    "topic": "Is AI a threat or a benefit to humanity?",
    "pro_position": "AI is primarily a benefit to humanity",
    "con_position": "AI poses serious threats to humanity",
    "max_rounds": 5,
    "word_limit_per_response": 200
  },
  "agents": {
    "father_model": "claude-sonnet-4-6",
    "pro_model": "claude-haiku-4-5-20251001",
    "con_model": "claude-haiku-4-5-20251001",
    "max_tokens_per_response": 1024
  },
  "timeouts": {
    "llm_call_seconds": 60,
    "round_timeout_seconds": 180,
    "heartbeat_interval_seconds": 10,
    "heartbeat_timeout_seconds": 30
  },
  "watchdog": {
    "max_restarts_per_process": 3
  }
}
```

> **Note**: Default rounds are set to **5** (budget mode).  
> Per assignment instructions (Section 8.7), this is explicitly allowed and does not affect the grade.  
> To run the full 10-round debate, set `"max_rounds": 10` in `config/setup.json`.

---

## Project Structure

```
ai_agents_hw5/
├── README.md                          # This file
├── pyproject.toml                     # UV + Ruff + pytest + coverage
├── uv.lock                            # Locked dependencies
├── .env-example                       # API key placeholder
├── .gitignore
│
├── docs/
│   ├── PRD.md                         # Product Requirements Document
│   ├── PLAN.md                        # Architecture & technical planning
│   ├── TODO.md                        # Task tracking
│   ├── CLASS_DIAGRAM.md               # Class hierarchy & relationships (§8.6)
│   ├── PRD_debate_engine.md           # PRD: debate orchestration mechanism
│   ├── PRD_gatekeeper.md              # PRD: API Gatekeeper
│   ├── PRD_watchdog.md                # PRD: Watchdog process monitor
│   └── PROMPTS.md                     # Prompt Engineering Log
│
├── config/
│   ├── setup.json                     # Main application config
│   ├── rate_limits.json               # API rate limit config
│   └── logging_config.json           # Log rotation config
│
├── src/
│   └── debate/                        # Main Python package
│       ├── __init__.py
│       ├── constants.py               # Enums: AgentRole, DebateStatus, MessageType
│       ├── sdk/sdk.py                 # DebateSDK — single public interface
│       ├── agents/
│       │   ├── base_agent.py          # Abstract base class (LLM + tool-use cycle + timeout)
│       │   ├── father_agent.py        # Judge: routes + delivers verdict
│       │   ├── pro_agent.py           # Pro debater (Research Advocate skill)
│       │   ├── con_agent.py           # Con debater (Devil's Advocate skill)
│       │   └── skills/
│       │       ├── father_skill.md    # Father's Skill definition (§6.2)
│       │       ├── pro_skill.md       # Pro's Skill definition
│       │       └── con_skill.md       # Con's Skill definition
│       ├── orchestrator/
│       │   ├── debate_orchestrator.py # Manages 3 processes + rounds
│       │   ├── round_runner.py        # Per-round IPC helpers (extracted for 150-line rule)
│       │   ├── agent_workers.py       # Module-level subprocess entry functions
│       │   └── watchdog.py            # Heartbeat monitor + auto-restart
│       ├── tools/search_tool.py       # DuckDuckGo internet search
│       ├── models/messages.py         # Pydantic schemas: DebateMessage, Verdict
│       ├── shared/
│       │   ├── gatekeeper.py          # API rate limit + queue + retry
│       │   ├── config.py              # ConfigManager
│       │   ├── logger.py              # FIFO rotating JSONL logger
│       │   ├── message_bus.py         # multiprocessing.Queue IPC
│       │   └── version.py             # Version "1.00"
│       └── cli/menu.py                # Terminal keyboard menu
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_agents/
│   │   ├── test_shared/
│   │   ├── test_models/
│   │   ├── test_tools/
│   │   └── test_orchestrator/
│   └── integration/
│       └── test_debate_flow.py
│
├── assets/screenshots/                # Terminal screenshots
└── logs/                              # Runtime JSONL logs (git-ignored)
```

---

## Agent Design

### Father Agent (Judge)
- Routes all messages — Pro and Con never communicate directly
- Enforces that each response references the opponent's last argument
- After all rounds: delivers verdict based on **persuasion power only** (not facts)
- **No ties permitted** — must declare a winner

### Pro Agent — "Research Advocate" Skill
- Strategy: gather evidence first → build logical chain → apply rhetoric
- Uses internet search (DuckDuckGo) for every argument
- Must include at least 1 citation per response

### Con Agent — "Devil's Advocate" Skill
- Strategy: find the weakest link → expose with counter-example → contradict source
- Distinct rhetorical style (reductio ad absurdum) vs Pro's evidence-first approach
- Must include at least 1 citation per response

---

## Engineering Features

| Feature | Implementation |
|---|---|
| **SDK Layer** | All logic accessible only via `DebateSDK` |
| **OOP + Inheritance** | `BaseAgent → FatherAgent / ProAgent / ConAgent` (see `docs/CLASS_DIAGRAM.md`) |
| **Skill Architecture (§6.2)** | Each agent loads its `.md` skill file at construction; description injected into system prompt |
| **API Gatekeeper** | `shared/gatekeeper.py` — rate limit + FIFO queue + retry |
| **Watchdog** | `orchestrator/watchdog.py` — heartbeat monitor + auto-restart |
| **Timeouts** | `ThreadPoolExecutor` + `executor.shutdown(wait=False)` — TimeoutError raised immediately |
| **Tool-use Cycle** | Full two-turn cycle: LLM calls search → tool_result → second API call → final text |
| **JSON IPC** | All inter-agent messages are `DebateMessage` Pydantic objects |
| **Structured Logs** | FIFO rotating JSONL — 20 files × 500 lines (configurable) |
| **Internet Search** | Anthropic tool_use + DuckDuckGo (mandatory per assignment) |
| **TDD** | Tests written before code; 87% coverage achieved |
| **Ruff** | Zero linting errors enforced |
| **UV** | Sole package manager — no pip/venv |

---

## Session 1 — Example Run

> **To run a live debate:** set your API key in `.env`, then run `uv run python src/main.py` and choose option 1.  
> Screenshots below show the expected terminal output.

### Terminal Menu

```
========================================
  AI Debate System v1.00
========================================
1. Start new debate
2. View last transcript
3. View verdict
4. Change debate topic
5. Show configuration
6. Exit

Enter choice: 1

Topic: Is AI a threat or a benefit to humanity?
Starting debate... (this may take a few minutes)

Debate complete! Session: ab8124ea
Winner: pro_agent
Pro score: 74.5 | Con score: 68.0
```

### Transcript Excerpt — Session ab8124ea

**Topic**: Is AI a threat or a benefit to humanity?  
**Rounds**: 5 | **Winner**: Pro Agent | **Criterion**: Persuasion Power

---

**[Round 1 — PRO AGENT]**

> AI has proven to be a transformative benefit to humanity, most evidently in healthcare.
> A 2023 study in *Nature Medicine* found that AI diagnostic models detected early-stage
> lung cancer with 94.5% accuracy — outperforming radiologists by 11.5 percentage points.
> Beyond medicine, AI-powered agricultural tools have helped smallholder farmers increase
> crop yields by up to 30% in sub-Saharan Africa (World Bank, 2024). These are not abstract
> promises; they are measurable outcomes affecting millions of lives today.

**[Round 1 — CON AGENT]**

> The Pro agent cites cherry-picked success stories while ignoring AI's documented systemic
> risks. Facial-recognition AI wrongly identified Black Americans at error rates 10–100×
> higher than white Americans (NIST, 2023), leading to false arrests. Meanwhile, generative
> AI enabled over 4,000 deepfake political disinformation campaigns in 2023 alone
> (Stanford Internet Observatory). A technology that saves some lives while structurally
> harming marginalised communities is not a net benefit — it is a redistribution of harm.

**[Round 3 — PRO AGENT]**

> Job displacement is not synonymous with net harm. The Industrial Revolution displaced 90%
> of agricultural workers — and average global life expectancy doubled in the century that
> followed. AI is automating dangerous, repetitive, cognitively exhausting tasks that cause
> injury and burnout. The Oxford Martin School's 2024 analysis projects that AI creates 1.7
> new jobs for every job displaced over a 15-year horizon.

**[Round 5 — CON AGENT]**

> The Pro agent ends by conceding that governance is the critical variable — which is
> precisely the Con position: AI as currently deployed, without sufficient governance, is a
> threat. The harms documented — biased policing algorithms, job displacement without safety
> nets, disinformation infrastructure, and acknowledged existential risk from AI's own
> creators — are present-tense facts, not hypotheticals.

---

### Verdict

| Field | Value |
|---|---|
| **Winner** | Pro Agent (`pro_agent`) |
| **Pro Score** | 74.5 / 100 |
| **Con Score** | 68.0 / 100 |
| **Criterion** | Persuasion Power |
| **Rounds Evaluated** | 5 |

**Justification**: Both agents presented well-sourced arguments. The Pro agent maintained a consistent evidence-first strategy throughout all five rounds, effectively reframing each Con challenge within a governance-and-expected-value framework. The Con agent's arguments were sharp but increasingly relied on conditional worst-case projections. Persuasion power favours the agent who leaves the audience with a net-positive mental model — Pro achieved that more consistently.

---

### Session Log

The full JSONL transcript is saved automatically to `logs/session_<id>.jsonl`:

```jsonl
{"message_id":"d4d72142-...","from_agent":"pro_agent","to_agent":"father_agent","message_type":"argument","round_number":1,"content":"AI has proven to be a transformative benefit...","citations":[],"timestamp":"2026-06-30T19:33:31.830267+00:00","references_message_id":null}
{"message_id":"e9c9cfd3-...","from_agent":"con_agent","to_agent":"father_agent","message_type":"counter_argument","round_number":1,"content":"The Pro agent cites cherry-picked success stories...","citations":[],"timestamp":"2026-06-30T19:33:31.830401+00:00","references_message_id":"d4d72142-..."}
```

---

## License

All rights reserved. Academic submission for course use only.
