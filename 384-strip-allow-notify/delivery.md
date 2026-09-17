# Delivery Plan: Strip allow-notify (384)

**Feature**: `384-strip-allow-notify` | **Date**: 2026-09-15
**Source**: `specs/384-strip-allow-notify/tasks.md` (42 tasks)
**Parent issue**: #384

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (to open) | T001–T042 | 8 modules under `wfctl/` (modified); 7 skill and command files under `wfctl/agents/` (modified); `README.md`, `docs/reference.md`, `AGENTS.md` (modified); up to 7 records under `docs/architecture/` (log lines); about 26 test files (5 deleted, 4 renamed, 2 created, the rest modified) | XL by file count | `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/` green; `uv run wfctl doctor` exit 0; SC-003 grep clean |

**Rationale**: Single PR. On file count this is XL, which the sizing table says to flag. It is flagged here and not split, because every split signal points towards bundling:

- **Mergeable increment: no.** Removing the CLI verbs without the skills installs a tree whose skills call commands that don't exist. Removing the payload keys without the skills sends `end-session` to read a key that isn't there. Both failures are loud, but they are still failures.
- **Required by record.** `384-the-agent-reports-through-two-flat-verbs` says "Every skill call site and both docs change in the same commit as the CLI", and `pipeline-state-is-one-payload` rules out the payload and its views changing in different changes.
- **Reviewability: yes, bundled.** A reviewer checks one property, that no reader of the grant survives, and needs every reader in front of them to check it.
- **Most of the file count is deletion.** Five test files and about a dozen functions are removed. What the reviewer actually reads is closer to M.

**PR closes**: `Closes #384`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #384 | T001–T042 | `Remove --allow-notify: the outward-action grant adds a stop nobody asked for` | about half a day | the PR above |

**Grouping pattern**: Single issue
**Rationale**: The issue already exists and the branch is named for it, so no issue is created.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Baseline green |
| 1 | Sequential | T002 → T003 → T004 → T005 | US1. `_tracker.py` refusal removed. Gate: `uv run pytest -q` |
| 2 | Parallel | T006 ‖ T007 ‖ T008 ‖ T009 ‖ T010 | US2 tests. Separate files |
| 3 | Sequential | T011 → T012 → T013 → T014 → T015 → T016 | US2 implementation. `cli.py` and `_session.py` shared with Wave 5. Gate: pytest and mypy |
| 4 | Parallel | T017 ‖ T018 ‖ T019 ‖ T020 | US3 tests |
| 5 | Sequential | T021 → T022 → T023 → T024 → T025 → T026 → T027 → T028 | US3 implementation. Deletes the grant. Gate: pytest, ruff, mypy |
| 6 | Parallel | T029 ‖ T030 ‖ T031 ‖ T032 ‖ T033 ‖ T034 ‖ T035 ‖ T036 ‖ T037 | US4. One file each |
| 7 | Sequential | T038 | install-skills and doctor |
| 8 | Parallel then sequential | T039 ‖ T040 → T041 → T042 | Polish and final validation |

**Single-agent order** (recommended): T001 → T042 in order. Waves 1–7 land as one commit (tasks.md § Dependencies).

---

## Agent Fanning Instructions

Single agent recommended. Waves 2, 4 and 6 could be fanned, but each file in
them is small, and the ordering constraint that phases 4–6 share one commit
makes fan-in coordination cost more than it saves.
