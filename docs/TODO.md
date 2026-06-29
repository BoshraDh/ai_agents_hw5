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
- [x] Create `config/rate_limits.json` (includes `cost_per_million_tokens`, `concurrent_max`, `requests_per_hour`)
- [x] Create `config/logging_config.json`
- [ ] Run `uv sync` to generate `uv.lock`

---

## Phase 3 — Core Infrastructure (TDD)

### Models
- [x] Write `tests/unit/test_models/test_messages.py`
- [x] Implement `src/debate/models/messages.py` (`DebateMessage`, `Verdict`, `Citation`)

### Shared Utilities
- [x] Write `tests/unit/test_shared/test_config.py` (includes GAP-5/6/8/9 property tests)
- [x] Implement `src/debate/shared/config.py` — added `concurrent_max`, `requests_per_hour`, `alert_at_usd`, `input_cost_per_million`, `output_cost_per_million` properties
- [x] Write `tests/unit/test_shared/test_message_bus.py`
- [x] Implement `src/debate/shared/message_bus.py` (`MessageBus`)
- [x] Write `tests/unit/test_shared/test_logger.py`
- [x] Implement `src/debate/shared/logger.py` (`DebateLogger`, FIFO rotation)
- [x] Write `tests/unit/test_shared/test_gatekeeper.py` (includes FIFO + concurrent_max tests)
- [x] **[GAP-4]** ✅ Replaced sleep-based rate limiting with real FIFO dispatch queue (`deque` of `threading.Event` tickets + background dispatcher thread)
- [x] **[GAP-5]** ✅ Added `threading.Semaphore(concurrent_max)` to `ApiGatekeeper.execute()`
- [x] **[GAP-6]** ✅ Added RPH window tracking in `_can_admit()` alongside RPM
- [x] **[GAP-7]** ✅ Implemented `RateLimitQueueFullException`; raised when FIFO queue hits `MAX_QUEUE_SIZE`
- [x] **[GAP-8]** ✅ Implemented `alert_at_usd` budget warning in `_track_cost()`
- [x] **[GAP-9]** ✅ Moved cost rates to `config/rate_limits.json`; `_track_cost()` reads from `config.input_cost_per_million` / `config.output_cost_per_million`
- [x] Implement `src/debate/shared/version.py`
- [x] Implement `src/debate/constants.py`

### Search Tool
- [x] Write `tests/unit/test_tools/test_search_tool.py`
- [x] Implement `src/debate/tools/search_tool.py` (`SearchTool`)

---

## Phase 4 — Agent Layer (TDD)

- [x] Write `tests/unit/test_agents/test_base_agent.py`
- [x] Implement `src/debate/agents/base_agent.py` (`BaseAgent` ABC)
- [x] Create `src/debate/agents/skills/father_skill.md`
- [x] Create `src/debate/agents/skills/pro_skill.md`
- [x] Create `src/debate/agents/skills/con_skill.md`
- [x] Write `tests/unit/test_agents/test_father_agent.py`
- [x] Implement `src/debate/agents/father_agent.py` — `bus` parameter made optional (default `None`); `route()` no-ops when `bus is None`
- [x] Write `tests/unit/test_agents/test_pro_agent.py`
- [x] Implement `src/debate/agents/pro_agent.py` — `bus` parameter made optional
- [x] Write `tests/unit/test_agents/test_con_agent.py`
- [x] Implement `src/debate/agents/con_agent.py` — `bus` parameter made optional

---

## Phase 5 — Orchestration (TDD)

- [x] Write `tests/unit/test_orchestrator/test_watchdog.py` (includes GAP-3 event propagation tests)
- [x] **[GAP-3]** ✅ Fixed `Watchdog`: `_handle_crash` no longer raises `ProcessUnrecoverableException` inside daemon thread. Instead sets `_fatal_error` + `_error_event`; main thread calls `check_for_fatal_error()` between rounds.
- [x] Implement `src/debate/orchestrator/watchdog.py`
- [x] Write `tests/unit/test_orchestrator/test_debate_orchestrator.py`
- [x] **[GAP-1]** ✅ `DebateOrchestrator` spawns each agent as `multiprocessing.Process` via `_start_processes()` (uses `use_processes=True` by default; `False` for tests)
- [x] **[GAP-2]** ✅ `Watchdog` created, all 3 processes registered, `watchdog.start()` called in `_start_watchdog()`; `watchdog.stop()` called on exit
- [x] **[GAP-11]** ✅ Added `stop()` method and `get_session_id()` method to `DebateOrchestrator`
- [x] Create `src/debate/orchestrator/agent_workers.py` — module-level process entry functions (`run_pro_worker`, `run_con_worker`, `run_father_worker`)
- [x] Implement `src/debate/orchestrator/debate_orchestrator.py`

---

## Phase 6 — SDK + CLI

- [x] **[GAP-10]** ✅ `DebateSDK` now stores orchestrators in `_sessions: dict[str, DebateOrchestrator]`; `get_transcript(session_id)` and `get_verdict(session_id)` look up by actual session_id
- [x] Implement `src/debate/sdk/sdk.py` (`DebateSDK`)
- [ ] Write `tests/unit/test_sdk.py`
- [x] Implement `src/debate/cli/menu.py` (terminal menu)
- [x] Implement `src/main.py` — added `multiprocessing.freeze_support()` and `if __name__ == '__main__':` guard (required for Windows spawn method)

---

## Phase 7 — Integration Tests

- [x] Write `tests/integration/test_debate_flow.py` (updated to use `use_processes=False`)
- [x] Write `tests/conftest.py` (added `cost_per_million_tokens` to test rate_limits config)
- [ ] Run full integration test with mocked Anthropic API
- [x] **[GAP TEST-1]** ✅ `test_gatekeeper_fifo_ordering` — verifies all concurrent requests complete
- [x] **[GAP TEST-2]** ✅ `test_concurrent_max_enforced` — verifies peak concurrency ≤ `concurrent_max`
- [x] **[GAP TEST-3]** ✅ `test_exception_not_raised_inside_thread` and `test_check_for_fatal_error_raises_after_max_restarts` verify GAP-3 fix
- [x] **[GAP TEST-4]** ✅ `tests/unit/test_sdk_sessions.py` — verifies session_id isolation

---

## Phase 8 — Quality Gates

- [ ] Run `uv run ruff check .` → must be 0 errors
- [ ] Run `uv run pytest --cov=src --cov-report=term-missing` → must be ≥ 85%
- [ ] Verify all files ≤ 150 lines of code
- [ ] Verify no hardcoded values in source code
- [ ] Verify `.env` is not committed

---

## Phase 9 — Final Deliverables

- [ ] Run a full 5-round debate end-to-end
- [ ] Save Session 1 JSONL log to `logs/`
- [ ] Take terminal screenshots → `assets/screenshots/`
- [ ] Add screenshots to `README.md`
- [ ] Add Session 1 transcript excerpt to `README.md`
- [ ] Create architecture diagram → `assets/architecture_diagram.png`
- [ ] Final push to GitHub (public repository)
- [ ] Submit GitHub repo link to Moodle

---

## Definition of Done (per task)

A task is considered **done** when:
1. Code is implemented
2. Tests exist and pass
3. Ruff reports no errors for that file
4. The file is ≤ 150 lines of code
5. All public functions have docstrings
