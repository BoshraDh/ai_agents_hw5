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
    "con_model": "claude-haiku-4-5-20251001"
  },
  "timeouts": {
    "llm_call_seconds": 60,
    "heartbeat_interval_seconds": 10,
    "heartbeat_timeout_seconds": 30
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
│       │   ├── base_agent.py          # Abstract base class
│       │   ├── father_agent.py        # Judge: routes + delivers verdict
│       │   ├── pro_agent.py           # Pro debater (Research Advocate skill)
│       │   └── con_agent.py           # Con debater (Devil's Advocate skill)
│       ├── orchestrator/
│       │   ├── debate_orchestrator.py # Manages 3 processes + rounds
│       │   └── watchdog.py            # Heartbeat monitor + restart
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
| **OOP + Inheritance** | `BaseAgent → FatherAgent / ProAgent / ConAgent` |
| **API Gatekeeper** | `shared/gatekeeper.py` — rate limit + FIFO queue + retry |
| **Watchdog** | `orchestrator/watchdog.py` — heartbeat monitor + auto-restart |
| **Timeouts** | Every LLM call wrapped in `ThreadPoolExecutor` with timeout |
| **JSON IPC** | All inter-agent messages are `DebateMessage` Pydantic objects |
| **Structured Logs** | FIFO rotating JSONL — 20 files × 500 lines (configurable) |
| **Internet Search** | Anthropic tool_use + DuckDuckGo (mandatory per assignment) |
| **TDD** | Tests written before code; 85%+ coverage enforced |
| **Ruff** | Zero linting errors required |
| **UV** | Sole package manager — no pip/venv |

---

## License

All rights reserved. Academic submission for course use only.
