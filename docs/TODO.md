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
- [ ] Write `tests/unit/test_shared/test_message_bus.py`
- [ ] Implement `src/debate/shared/message_bus.py` (`MessageBus`)
- [ ] Write `tests/unit/test_shared/test_logger.py`
- [ ] Implement `src/debate/shared/logger.py` (`DebateLogger`, FIFO rotation)
- [ ] Write `tests/unit/test_shared/test_gatekeeper.py`
- [ ] Implement `src/debate/shared/gatekeeper.py` (`ApiGatekeeper`)
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
- [ ] Write `tests/unit/test_orchestrator/test_debate_orchestrator.py`
- [ ] Implement `src/debate/orchestrator/debate_orchestrator.py` (`DebateOrchestrator`)

---

## Phase 6 — SDK + CLI

- [ ] Implement `src/debate/sdk/sdk.py` (`DebateSDK`)
- [ ] Write `tests/unit/test_sdk.py`
- [ ] Implement `src/debate/cli/menu.py` (terminal menu)
- [ ] Implement `src/main.py` (entry point)

---

## Phase 7 — Integration Tests

- [ ] Write `tests/integration/test_debate_flow.py`
- [ ] Write `tests/conftest.py` (shared fixtures + mocks)
- [ ] Run full integration test with mocked Anthropic API

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
