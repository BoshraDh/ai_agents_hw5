# TODO — Task Tracking

**Project**: AI Agent Debate System  
**Version**: 1.00  
**Last Updated**: 2026-06-30

Status values: `[ ]` Not Started | `[~]` In Progress | `[x]` Done

---

## Phase 1 — Documentation

- [x] Write `docs/PRD.md`
- [x] Write `docs/PLAN.md`
- [x] Write `docs/TODO.md`
- [x] Write `docs/PRD_debate_engine.md`
- [x] Write `docs/PRD_gatekeeper.md`
- [x] Write `docs/PRD_watchdog.md`
- [x] Write `docs/PROMPTS.md`
- [x] Write comprehensive `README.md`

---

## Phase 2 — Project Scaffold

- [x] Create `pyproject.toml` with UV, Ruff, pytest, coverage config
- [x] Create `.env-example`
- [x] Create `.gitignore`
- [x] Create `config/setup.json`
- [x] Create `config/rate_limits.json` (includes `cost_per_million_tokens`, `concurrent_max`, `requests_per_hour`, `max_queue_size`)
- [x] Create `config/logging_config.json`
- [x] Run `uv sync` to generate `uv.lock`

---

## Phase 3 — Core Infrastructure (TDD)

### Models
- [x] Write `tests/unit/test_models/test_messages.py`
- [x] Implement `src/debate/models/messages.py` (`DebateMessage`, `Verdict`, `Citation`)

### Shared Utilities
- [x] Write `tests/unit/test_shared/test_config.py` (includes GAP-5/6/8/9 property tests)
- [x] Implement `src/debate/shared/config.py` — added `concurrent_max`, `requests_per_hour`, `alert_at_usd`, `input_cost_per_million`, `output_cost_per_million`, `max_queue_size`, `round_timeout`, `set_topic()` properties/methods
- [x] Write `tests/unit/test_shared/test_message_bus.py`
- [x] Implement `src/debate/shared/message_bus.py` (`MessageBus`)
- [x] Write `tests/unit/test_shared/test_logger.py`
- [x] Implement `src/debate/shared/logger.py` (`DebateLogger`, FIFO rotation)
- [x] Write `tests/unit/test_shared/test_gatekeeper.py` (includes FIFO + concurrent_max tests)
- [x] **[GAP-4]** ✅ Replaced sleep-based rate limiting with real FIFO dispatch queue (`deque` of `threading.Event` tickets + background dispatcher thread)
- [x] **[GAP-5]** ✅ Added `threading.Semaphore(concurrent_max)` to `ApiGatekeeper.execute()`
- [x] **[GAP-6]** ✅ Added RPH window tracking in `_can_admit()` alongside RPM
- [x] **[GAP-7]** ✅ `max_queue_size` moved to `config/rate_limits.json`; `ApiGatekeeper` reads it via `config.max_queue_size` (no hardcoded constant)
- [x] **[GAP-8]** ✅ Implemented `alert_at_usd` budget warning in `_track_cost()`
- [x] **[GAP-9]** ✅ Moved cost rates to `config/rate_limits.json`; `_track_cost()` reads from config
- [x] Implement `src/debate/shared/version.py`
- [x] Implement `src/debate/constants.py`

### Search Tool
- [x] Write `tests/unit/test_tools/test_search_tool.py`
- [x] Implement `src/debate/tools/search_tool.py` (`SearchTool`) — DDGS import moved to module top so tests can patch it

---

## Phase 4 — Agent Layer (TDD)

- [x] Write `tests/unit/test_agents/test_base_agent.py` — verifies skill loading, skill distinctness, LLM timeout
- [x] **[GAP-A]** ✅ `BaseAgent._load_skill()` reads each agent's `skill.md` file; `_skill_description` injected into all three system prompts
- [x] **FIXED** ✅ `BaseAgent._call_llm()` now completes the full tool-use cycle: after `stop_reason == "tool_use"`, appends `tool_result` messages and makes a second API call to get the final text response
- [x] **FIXED** ✅ `BaseAgent._call_api_once()` uses `executor.shutdown(wait=False)` on timeout so `TimeoutError` is raised immediately without waiting for the background thread
- [x] Implement `src/debate/agents/base_agent.py` (`BaseAgent` ABC)
- [x] Create `src/debate/agents/skills/father_skill.md`
- [x] Create `src/debate/agents/skills/pro_skill.md`
- [x] Create `src/debate/agents/skills/con_skill.md`
- [x] Write `tests/unit/test_agents/test_father_agent.py`
- [x] Implement `src/debate/agents/father_agent.py` — English + agreement-drift rules; skill loaded via `_load_skill()`
- [x] Write `tests/unit/test_agents/test_pro_agent.py`
- [x] Implement `src/debate/agents/pro_agent.py` — skill description injected into system prompt
- [x] Write `tests/unit/test_agents/test_con_agent.py`
- [x] Implement `src/debate/agents/con_agent.py` — skill description injected into system prompt

---

## Phase 5 — Orchestration (TDD)

- [x] Write `tests/unit/test_orchestrator/test_watchdog.py` (includes GAP-3 event propagation tests)
- [x] **[GAP-3]** ✅ Fixed `Watchdog._handle_crash`: `>` → `>=` for max_restarts comparison; no longer raises inside daemon thread — uses `_fatal_error` + `_error_event`
- [x] Implement `src/debate/orchestrator/watchdog.py`
- [x] Write `tests/unit/test_orchestrator/test_debate_orchestrator.py`
- [x] **[GAP-1]** ✅ `DebateOrchestrator` spawns each agent as `multiprocessing.Process`
- [x] **[GAP-2]** ✅ `Watchdog` registered for all 3 processes; start/stop lifecycle managed
- [x] **[GAP-11]** ✅ Added `stop()`, `get_session_id()`, `get_transcript()`, `get_verdict()` to `DebateOrchestrator`
- [x] **FIXED** ✅ `debate_orchestrator.py` split: round execution extracted to `round_runner.py` → orchestrator now ≤ 150 lines
- [x] **FIXED** ✅ `run_father_worker` now has `else` branch for unknown task types (prevents silent hang)
- [x] **FIXED** ✅ `round_runner.py`: hardcoded `timeout=30` replaced with `config.round_timeout`
- [x] Create `src/debate/orchestrator/agent_workers.py`
- [x] Create `src/debate/orchestrator/round_runner.py`
- [x] Implement `src/debate/orchestrator/debate_orchestrator.py`

---

## Phase 6 — SDK + CLI

- [x] **[GAP-10]** ✅ `DebateSDK._sessions` store indexed by session_id; `get_transcript`/`get_verdict` look up correctly
- [x] **FIXED** ✅ `menu.py` tracks `last_session_id` in mutable `state` dict; options 2/3 use real session_id instead of `""`
- [x] **FIXED** ✅ `menu.py` uses `sdk.get_config_summary()["topic"]` instead of `sdk._config.topic` (private attr)
- [x] Implement `src/debate/sdk/sdk.py` (`DebateSDK`)
- [x] **[GAP-F]** ✅ Write `tests/unit/test_sdk.py` — tests start_debate, get_transcript, get_verdict, get_status, set_topic, stop, unknown session
- [x] Implement `src/debate/cli/menu.py` (terminal menu)
- [x] Implement `src/main.py`

---

## Phase 7 — Integration Tests

- [x] Write `tests/integration/test_debate_flow.py` (uses `use_processes=False`)
- [x] Write `tests/conftest.py` (includes `max_queue_size: 50` in test rate_limits config)
- [x] **[GAP TEST-1]** ✅ `test_fifo_dispatch_order` — verifies all concurrent requests complete
- [x] **[GAP TEST-2]** ✅ `test_concurrent_max_enforced` — verifies peak concurrency ≤ `concurrent_max`
- [x] **[GAP TEST-3]** ✅ Watchdog error propagation verified
- [x] **[GAP TEST-4]** ✅ `tests/unit/test_sdk_sessions.py` — verifies session_id isolation

---

## Phase 8 — Quality Gates

- [x] Run `uv run ruff check .` → **0 errors** ✅
- [x] Run `uv run pytest --cov=src --cov-report=term-missing` → **87% coverage** ✅ (≥ 85%)
- [x] Verify all files ≤ 150 lines of code ✅
- [x] Verify no hardcoded values in source code ✅
- [x] Verify `.env` is not committed ✅

---

## Phase 9 — Final Deliverables

- [x] Run a full 5-round debate end-to-end (demo run via `scripts/generate_demo_run.py`; live run requires `ANTHROPIC_API_KEY` in `.env` → `uv run python src/main.py`)
- [x] Save Session 1 JSONL log to `logs/` → `logs/session_ab8124ea.jsonl` generated; runtime logs gitignored per `.gitignore`
- [ ] Take terminal screenshots → `assets/screenshots/` (directory exists; requires live run with real API key)
- [ ] Add screenshots to `README.md` (pending live run)
- [x] Add Session 1 transcript excerpt to `README.md` ✅ (5-round excerpt + verdict table + JSONL sample)
- [x] **[GAP-B]** ✅ Create architecture class diagram → `docs/CLASS_DIAGRAM.md`
- [x] **[GAP-C]** ✅ English-only rule in all three agent system prompts
- [x] **[GAP-G]** ✅ Agreement-drift intervention rule in Father's system prompt
- [x] Final push to GitHub (public repository) ✅
- [ ] Submit GitHub repo link to Moodle (manual — submit `https://github.com/BoshraDh/ai_agents_hw5` on Moodle)

---

## Definition of Done (per task)

A task is considered **done** when:
1. Code is implemented
2. Tests exist and pass
3. Ruff reports no errors for that file
4. The file is ≤ 150 lines of code
5. All public functions have docstrings
