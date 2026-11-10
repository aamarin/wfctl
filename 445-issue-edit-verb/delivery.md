# Delivery Plan: issue edit verb (445)

**Feature**: `445-issue-edit-verb` | **Date**: 2026-11-10
**Source**: `445-issue-edit-verb/tasks.md` (28 tasks)
**Parent issue**: none

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (opened at implement) | T001 - T028 | `changes/445.addition.md` (created), `wfctl/_tracker.py` (modified), `wfctl/cli.py` (modified), `wfctl/agents/trackers/github.json` (modified), `wfctl/agents/skills/scaffold-tracker/SKILL.md` (modified), `tests/test_tracker.py` (modified), `tests/test_tracker_records_issue_verbs.py` (modified), `docs/reference.md` (modified), `AGENTS.md` (modified) | M | `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `uv run wfctl verify` pass, every review group has reviewed HEAD, and the real GitHub edit in T027 has been run with the user's go-ahead |

**Rationale**: Single PR. The count is 9 files, which the sizing table puts at L, but four of them are small:

1. The release note is one line.
2. `github.json` gains one entry.
3. `docs/reference.md` and `AGENTS.md` each gain `edit` in a list.

The code change sits in `wfctl/_tracker.py` and `wfctl/cli.py`, with tests in two files, so the review load is that of an M change.

All four boundary signals point to one PR:

1. Every story edits `wfctl/_tracker.py` and `tests/test_tracker.py`, so separate PRs would conflict on the same functions.
2. A reviewer needs the failure lines (US2) and the template check (US3) beside the edit function (US1) to judge whether a two-field edit can report or record the wrong thing.
3. US1 can merge alone, but it would ship an `edit` verb that `tracker-check` lets a backend declare without `{field}`, which is the overwrite plan-review PR-001 found.
4. The stories share the edit function and its two `dispatch` helpers, so they aren't independent.

**PR closes**: `Closes #445`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #445 | T001 - T028 | An issue's title is the one field wfctl issue cannot write, so a retitle reaches GitHub by name and leaves no record | M | the one PR above |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, and #445 already exists, so there is no issue to create.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | No dependencies. |
| 1 | Sequential | T002 → T003 → T004 → T005 | All four edit `wfctl/_tracker.py`. T005 is the Phase 2 gate, and `dispatch` behaves as before. |
| 2 | Parallel | (T006, T007, T008) ‖ T009 ‖ T012 ‖ T023 | T006 - T008 share `tests/test_tracker.py`, so one agent writes them together. T012 and T023 touch package data only. |
| 3 | Sequential | T010 → T011 → T013 | T010 needs the Wave 1 helpers. T013 is the Phase 3 gate. |
| 4 | Sequential | (T014 - T017) → T018 → T019 | The tests go in `tests/test_tracker.py` and fail before T018. T019 is the Phase 4 gate. |
| 5 | Sequential | (T020, T022) → T021 → T024 | T022 needs T010. T021 edits `wfctl/_tracker.py` after T018. T024 is the Phase 5 gate. |
| 6 | Parallel, then sequential | T025 ‖ T026, then T027 → T028 | T027 writes to a real GitHub issue, so the user is asked first. T028 is the final gate. |

**Single-agent order** (recommended):
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T012 → T023 → T010 → T011 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T022 → T021 → T024 → T025 → T026 → T027 → T028

---

## Agent Fanning Instructions

A single agent is recommended. Most tasks edit `wfctl/_tracker.py` or `tests/test_tracker.py`, so parallel agents would wait on each other or conflict. The only work that can run apart is T012 and T023, and each takes a few minutes.
