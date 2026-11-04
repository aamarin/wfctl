# Delivery Plan: Read review.commands from the trunk (711)

**Feature**: `711-review-commands-from-trunk` | **Date**: 2026-11-04
**Source**: `tasks.md` in this spec folder (18 tasks)
**Parent issue**: none

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (to be opened) | T001 - T018 | `wfctl/_review.py`, `wfctl/_review_config.py`, `wfctl/cli.py` (`review_start_cmd` only), `tests/test_review.py`, `tests/test_review_config.py`, `tests/test_review_cli.py`, `wfctl/agents/skills/fanning-out-code-review/SKILL.md`, `AGENTS.md` (all modified), `changes/711.change.md` (created) | S | T018 passes: the full suite, ruff, mypy, and `wfctl doctor` |

**Rationale**: Single PR. Reading the commands from the trunk and warning about the branch's difference are one behavior change, and the existing tests that declare commands only on the branch have to move to the trunk in the same commit that changes the reader.

**PR closes**: `Closes #711`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #711 | T001 - T018 | `Read review.commands from the trunk, not the branch` | S | the PR above |

**Grouping pattern**: Single issue
**Rationale**: The branch's own issue covers the whole change, so no issue needs creating.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Parallel | T001 ‖ T002 | Different files |
| 1 | Sequential | T003 → T004 → T005 → T006 → T007 → T008 | The CLI wiring and its tests |
| 2 | Sequential | T009 → T010 → T011 | Stories 2 and 3 |
| 3 | Sequential | T012 → T013 → T014 → T015 → T016 → T017 → T018 | Docs, refactor, definition of done |
