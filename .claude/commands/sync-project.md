Perform a full project sync for the ai_agents_hw5 repository. Execute every step below in order without asking for confirmation.

## Step 1 — Discover all changes since last sync

- Run `git log --oneline -20` to see recent commits.
- Run `git diff HEAD~1 HEAD --name-only` (or `git diff --name-only` for uncommitted changes) to get the list of changed files.
- Read every changed source file in `src/`, `tests/`, `config/`, and `docs/` to understand what was modified.

## Step 2 — Cross-check implementation against requirements

Verify the current codebase satisfies every requirement from:
1. Assignment 5 PDF (Exercise 02 — AI Agent Debate), specifically:
   - §8.1: Three-agent architecture (Father/Pro/Con)
   - §8.3: All 8 mandatory requirements (dialogue, skill differentiation, ≥10 pings or 5 with note, mutual referencing, internet search tool, Father verdict/no tie, Father routing, JSON format)
   - §8.4: No Claude CLI; no tie; uses real LLM; no politically correct language guard
   - §8.6: Timeouts, Watchdog + keep-alive, OOP/inheritance, class diagram, TDD, Ruff, no hardcoded params, Cyber check, Gatekeeper, SDK layer, FIFO structured logs, terminal operation
   - §8.7: README with screenshots+session log, English/Hebrew only, UV + pyproject.toml, .env-example, GitHub public repo

2. Software submission guidelines (V3.00):
   - docs/ folder with PRD.md, PLAN.md, TODO.md, README.md, PROMPTS.md
   - 85%+ test coverage, Ruff 0 errors, max 150 lines/file, no hardcoded values
   - SDK layer as only public interface, BaseAgent inheritance hierarchy
   - API keys only via environment variables, .env in .gitignore

## Step 3 — Update docs/TODO.md

- Mark any newly completed tasks as `[x]`.
- Add any newly discovered tasks or gaps as new `[ ]` items.
- Label newly discovered gaps as GAP-* with a short description.
- Do NOT remove any existing tasks — only update status.

## Step 4 — Update docs/PLAN.md

- Add or update any section that reflects a new architectural decision, design change, or implementation pattern introduced since the last sync.
- Update the IPC Design table, SDK API contract, or ADR sections if relevant.
- Do not rewrite sections that have not changed.

## Step 5 — Update docs/PRD.md

- If any requirement was clarified, added, or scoped differently, update the relevant FR-* or NFR-* entry.
- If a new component was added (e.g. a new module, new config key, new agent behaviour), add a corresponding requirement entry.
- Do not change requirement IDs for existing items.

## Step 6 — Update README.md (only if needed)

- Update the project structure tree if new files were added.
- Update the engineering features table if a new feature was added.
- Update the configuration section if new config keys were added.
- Do NOT add placeholder sections like "Screenshots coming soon" — only add real content.

## Step 7 — Verify quality gates

Report the status of each gate (do not run if it would cost money or require the live API):
- [ ] `uv run ruff check .` — must be 0 errors
- [ ] `uv run pytest tests/ --cov=src` — must be ≥ 85%
- [ ] All source files ≤ 150 lines of code
- [ ] No hardcoded strings/numbers in src/ (check config.py references)
- [ ] `.env` not tracked in git (`git ls-files .env` must return empty)
- [ ] `uv.lock` exists and is committed

## Step 8 — Commit and push

Stage all modified documentation and source files. Use a commit message in this format:

```
docs: sync-project — update PRD/PLAN/TODO/README after <brief description of what changed>
```

Then push to `origin main`.

## Step 9 — Print a sync summary

Output a concise table with four sections:
1. **Changed files** — list every file that was modified or created
2. **Docs updated** — which of PRD/PLAN/TODO/README changed and why
3. **Tasks completed** — list of tasks newly marked `[x]`
4. **Remaining gaps** — any open `[ ]` items that are blocking or high-priority
