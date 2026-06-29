# Product Requirements Document (PRD)

**Project**: AI Agent Debate System  
**Assignment**: Exercise 02 — Lesson 05  
**Course**: Orchestration for AI Agents | Dr. Yoram Segal  
**Version**: 1.00  
**Date**: 2026-06-29

---

## 1. Project Overview

### 1.1 Context

This project is part of the "Orchestration for AI Agents" course. The goal is to demonstrate
mastery of multi-agent orchestration by building a real, functioning debate system where
three AI agents interact via structured JSON messages.

### 1.2 Problem Statement

A simple chatbot cannot hold a structured, adversarial debate — it lacks distinct personas,
enforced turn-taking, neutral moderation, and a verdict mechanism. This project solves that
by orchestrating three specialized agents with well-defined roles and communication protocols.

### 1.3 Target Users

- Course instructor (grader): evaluates code quality, architecture, and debate quality
- Student developer: runs debates to observe multi-agent behavior
- Potential future user: anyone interested in AI-driven debate simulation

---

## 2. Goals and Success Criteria

### 2.1 Primary Goals

1. Build a working 3-agent debate that produces a readable, coherent transcript
2. Demonstrate all required engineering patterns (SDK, OOP, Gatekeeper, Watchdog, TDD)
3. Meet all submission requirements from both the assignment and the guidelines document

### 2.2 KPIs and Acceptance Criteria

| KPI | Target |
|---|---|
| Minimum debate rounds | 5 (configurable) |
| Minimum citations per argument | 1 (internet search mandatory) |
| Test coverage | ≥ 85% |
| Ruff linting errors | 0 |
| Max lines per source file | 150 |
| All agents respond via Father | 100% (no direct child-to-child) |
| Father delivers a verdict | Always — no ties |
| Config values hardcoded in source | 0 |

---

## 3. Functional Requirements

### 3.1 Debate Engine

- **FR-01**: The system shall spawn three independent processes: Father, Pro, and Con agents
- **FR-02**: All inter-agent messages shall pass through the Father agent (no direct child-to-child)
- **FR-03**: Each argument shall reference the opponent's most recent message by `message_id`
- **FR-04**: Each argument shall include at least one internet citation obtained via a search tool
- **FR-05**: The debate shall run for a configurable number of rounds (default: 5)
- **FR-06**: After all rounds, the Father shall deliver a verdict with winner, scores, and justification
- **FR-07**: The Father shall never declare a tie — one winner must be chosen
- **FR-08**: All messages shall conform to the `DebateMessage` JSON schema

### 3.2 API Gatekeeper

- **FR-09**: Every call to the Anthropic API shall pass through the `ApiGatekeeper`
- **FR-10**: The Gatekeeper shall enforce rate limits from `config/rate_limits.json`
- **FR-11**: When rate-limited, requests shall be queued (FIFO), not dropped
- **FR-12**: The Gatekeeper shall retry on transient failures (up to `max_retries` attempts)
- **FR-13**: The Gatekeeper shall halt and raise an exception if the budget ceiling is exceeded

### 3.3 Watchdog

- **FR-14**: A Watchdog thread shall monitor all three agent processes via heartbeat
- **FR-15**: If a process fails to send a heartbeat within `heartbeat_timeout_seconds`, it shall be restarted
- **FR-16**: Maximum restart attempts per process shall be configurable

### 3.4 Internet Search

- **FR-17**: Both Pro and Con agents shall use the DuckDuckGo search tool to find citations
- **FR-18**: The search tool shall be registered as an Anthropic tool_use tool
- **FR-19**: Citations shall be included in the `DebateMessage.citations` field

### 3.5 Logging

- **FR-20**: All debate messages, API calls, and errors shall be logged in JSONL format
- **FR-21**: Log files shall rotate using FIFO (max 20 files × 500 lines, configurable)
- **FR-22**: The full debate transcript shall be saved as a JSONL session file

### 3.6 Terminal Interface

- **FR-23**: The system shall provide a keyboard-driven terminal menu
- **FR-24**: Menu options: start debate, view transcript, view verdict, change topic, show config, exit
- **FR-25**: The CLI shall call only `DebateSDK` methods — never internal modules directly

---

## 4. Non-Functional Requirements

### 4.1 Performance

- **NFR-01**: Each agent response shall complete within `timeout_seconds` (default: 60s)
- **NFR-02**: The Watchdog shall check process health every `heartbeat_interval_seconds` (default: 10s)

### 4.2 Security

- **NFR-03**: No API keys or secrets shall appear in source code or committed files
- **NFR-04**: API keys shall only be read from environment variables

### 4.3 Maintainability

- **NFR-05**: All source files shall be ≤ 150 lines of code
- **NFR-06**: All public functions and classes shall have docstrings
- **NFR-07**: Code shall pass `ruff check` with zero errors
- **NFR-08**: Test coverage shall be ≥ 85%

### 4.4 Portability

- **NFR-09**: The project shall use `uv` as the sole package manager
- **NFR-10**: `pyproject.toml` shall be the single source of truth for dependencies
- **NFR-11**: The full environment shall be reproducible with `uv sync`

---

## 5. Assumptions and Constraints

- The Anthropic API is available and the user has a valid API key
- Internet access is available for DuckDuckGo searches during the debate
- Budget is limited — default rounds set to 5 (per assignment permission, no grade penalty)
- All three agents use the Anthropic API (Father uses `claude-sonnet-4-6`, children use `claude-haiku-4-5`)

---

## 6. Out of Scope

- A graphical user interface (GUI is optional; terminal menu is sufficient)
- Multi-turn debate memory across sessions
- Support for more than 3 agents
- Real-time streaming of agent responses to the terminal

---

## 7. Timeline and Milestones

| Milestone | Description |
|---|---|
| M1 — Docs | All `docs/` files written and reviewed |
| M2 — Scaffold | `pyproject.toml`, config files, package structure created |
| M3 — Models + Shared | `messages.py`, `config.py`, `gatekeeper.py`, `logger.py`, `message_bus.py` |
| M4 — Agents | `base_agent.py`, `father_agent.py`, `pro_agent.py`, `con_agent.py` |
| M5 — Orchestration | `debate_orchestrator.py`, `watchdog.py` |
| M6 — SDK + CLI | `sdk.py`, `menu.py` |
| M7 — Full Run | First complete debate, JSONL log, screenshots |
| M8 — Final | README updated, tests passing ≥85%, Ruff clean, GitHub push |
