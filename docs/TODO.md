# TODO — Task Tracking

**Project**: AI Agent Debate System  
**Version**: 1.00  
**Last Updated**: 2026-06-29

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

- [ ] Create `pyproject.toml` with UV, Ruff, pytest, coverage config
- [ ] Create `.env-example`
- [ ] Create `.gitignore`
- [ ] Create `config/setup.json`
- [ ] Create `config/rate_limits.json`
- [ ] Create `config/logging_config.json`
- [ ] Run `uv sync` to generate `uv.lock`

---

## Phase 3 — Core Infrastructure (TDD)

### Models
- [ ] Write `tests/unit/test_models/test_messages.py` (tests first)
- [ ] Implement `src/debate/models/messages.py` (`DebateMessage`, `Verdict`, `Citation`)
- [ ] Verify tests pass

### Shared Utilities
- [ ] Write `tests/unit/test_shared/test_config.py`
- [ ] Implement `src/debate/shared/config.py` (`ConfigManager`)
- [ ] **[GAP-5/6]** Add `requests_per_hour` and `concurrent_max` properties to `ConfigManager` — both values exist in `rate_limits.json` but have no properties and are silently ignored
- [ ] Write `tests/unit/test_shared/test_message_bus.py`
- [ ] Implement `src/debate/shared/message_bus.py` (`MessageBus`)
- [ ] Write `tests/unit/test_shared/test_logger.py`
- [ ] Implement `src/debate/shared/logger.py` (`DebateLogger`, FIFO rotation)
- [ ] Write `tests/unit/test_shared/test_gatekeeper.py`
- [ ] Implement `src/debate/shared/gatekeeper.py` (`ApiGatekeeper`)
- [ ] **[GAP-4] CRITICAL** Replace sleep-based rate limiting in `ApiGatekeeper._enforce_rate_limit()` with a real FIFO queue (e.g., `queue.Queue` + `threading.Semaphore`) so concurrent waiters are dispatched in arrival order (FR-G02/G03)
- [ ] **[GAP-5] CRITICAL** Add `concurrent_max` semaphore to `ApiGatekeeper` to cap simultaneous in-flight API calls (PRD-G: "Limit simultaneous in-flight calls to `concurrent_max`")
- [ ] **[GAP-6]** Add `requests_per_hour` window tracking to `ApiGatekeeper` (config value `requests_per_hour` is currently dead)
- [ ] **[GAP-7]** Implement `RateLimitQueueFullException` and raise it if FIFO queue exceeds a hard cap (defined in PRD_gatekeeper.md but missing from code)
- [ ] **[GAP-8]** Implement `alert_at_usd` budget warning in `ApiGatekeeper._track_cost()` — log a WARNING when spend crosses `alert_at_usd` (config value exists, code ignores it)
- [ ] **[GAP-9]** Move hardcoded cost rates in `gatekeeper.py:76` (`0.25`, `1.25`) to `config/rate_limits.json` — violates the no-hardcoded-values rule (NFR)
- [ ] Implement `src/debate/shared/version.py`
- [ ] Implement `src/debate/constants.py`

### Search Tool
- [ ] Write `tests/unit/test_tools/test_search_tool.py`
- [ ] Implement `src/debate/tools/search_tool.py` (`SearchTool`)

---

## Phase 4 — Agent Layer (TDD)

- [ ] Write `tests/unit/test_agents/test_base_agent.py`
- [ ] Implement `src/debate/agents/base_agent.py` (`BaseAgent` ABC)
- [ ] Create `src/debate/agents/skills/father_skill.md`
- [ ] Create `src/debate/agents/skills/pro_skill.md`
- [ ] Create `src/debate/agents/skills/con_skill.md`
- [ ] Write `tests/unit/test_agents/test_father_agent.py`
- [ ] Implement `src/debate/agents/father_agent.py` (`FatherAgent`)
- [ ] Write `tests/unit/test_agents/test_pro_agent.py`
- [ ] Implement `src/debate/agents/pro_agent.py` (`ProAgent`)
- [ ] Write `tests/unit/test_agents/test_con_agent.py`
- [ ] Implement `src/debate/agents/con_agent.py` (`ConAgent`)

---

## Phase 5 — Orchestration (TDD)

- [ ] Write `tests/unit/test_orchestrator/test_watchdog.py`
- [ ] Implement `src/debate/orchestrator/watchdog.py` (`Watchdog`)
- [ ] **[GAP-3]** Fix `ProcessUnrecoverableException` propagation: daemon thread must signal main thread via `threading.Event` or a shared `queue.Queue` — raising inside `run()` is silently swallowed
- [ ] Write `tests/unit/test_orchestrator/test_debate_orchestrator.py`
- [ ] Implement `src/debate/orchestrator/debate_orchestrator.py` (`DebateOrchestrator`)
- [ ] **[GAP-1] CRITICAL** Refactor `DebateOrchestrator` to spawn each agent as `multiprocessing.Process` (FR-E01). Currently agents are plain in-process objects — this violates the assignment's core architecture requirement.
- [ ] **[GAP-2] CRITICAL** Wire `Watchdog` into `DebateOrchestrator`: import Watchdog, create instance, register all 3 processes with their factory callables, call `watchdog.start()` before rounds begin, call `watchdog.stop()` on exit
- [ ] **[GAP-11]** Add `stop()` method and `get_session_id()` method to `DebateOrchestrator` to match PRD-E interface definition

---

## Phase 6 — SDK + CLI

- [ ] Implement `src/debate/sdk/sdk.py` (`DebateSDK`)
- [ ] **[GAP-10]** Fix `get_transcript(session_id)` and `get_verdict(session_id)` in `DebateSDK` to actually honor `session_id` — currently the parameter is accepted but ignored; querying an old session returns the latest session's data instead
- [ ] Write `tests/unit/test_sdk.py`
- [ ] Implement `src/debate/cli/menu.py` (terminal menu)
- [ ] Implement `src/main.py` (entry point)

---

## Phase 7 — Integration Tests

- [ ] Write `tests/integration/test_debate_flow.py`
- [ ] Write `tests/conftest.py` (shared fixtures + mocks)
- [ ] Run full integration test with mocked Anthropic API
- [ ] **[GAP TEST-1]** Add `test_gatekeeper_fifo_ordering`: launch N concurrent threads all hitting `execute()` at once; verify they are dispatched in arrival order when rate-limited
- [ ] **[GAP TEST-2]** Add `test_gatekeeper_concurrent_max`: verify no more than `concurrent_max` calls run simultaneously (requires semaphore to be implemented first)
- [ ] **[GAP TEST-3]** Add `test_orchestrator_watchdog_integration`: spawn a real process that intentionally crashes; verify Watchdog detects it, restarts it, and the main thread is notified if max restarts exceeded
- [ ] **[GAP TEST-4]** Add `test_sdk_session_isolation`: run two debates, store both session_ids, verify that querying session A after running session B returns session A's data (not B's)

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
