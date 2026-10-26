# Delivery Plan: Mirror below recorded dir (293)

**Feature**: `293-mirror-below-recorded-dir` | **Date**: 2026-10-09
**Source**: `293-mirror-below-recorded-dir/tasks.md` (21 tasks)
**Parent issue**: #293

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (to be opened) | T001 - T021 | `wfctl/cli.py` (modified), `tests/test_install_skills.py` (modified), `tests/test_bundle.py` (modified) | XS | `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` pass, `uv run wfctl doctor` is green after this worktree's redo, and the review panel has run |

**Rationale**: Single PR. The code change is one table entry, and every test
either drives it or pins a consequence of it, so no subset can be merged and
reviewed on its own.

**PR closes**: `Closes #293`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #293 | T001 - T021 | `[293] A file dropped from below a recorded directory can never leave a consuming repo` | XS | the single PR |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, and #293 already exists, so
there is nothing to create.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 | The fixture helpers every later test uses |
| 1 | Parallel | T003 - T006 ‖ T007 | T007 is in `tests/test_bundle.py`, the rest in `tests/test_install_skills.py`; each must fail before T008 |
| 2 | Sequential | T008 → T009 | The one code change, then the Phase 3 merge gate |
| 3 | Sequential | T010 - T013 → T014 - T018 | Both phases edit `tests/test_install_skills.py`, so they run one after the other |
| 4 | Sequential | T019 → T020 → T021 | T019 reinstalls this worktree's skills, so it follows a green suite |

**Single-agent order** (recommended for this XS feature):
T001 → T002 → T003 - T007 → T008 → T009 → T010 - T013 → T014 - T018 → T019 →
T020 → T021

---

## Agent Fanning Instructions

A single agent is recommended for this XS feature. Nearly every task edits
`tests/test_install_skills.py`, so parallel agents would conflict on that file.
The wave table is kept for reference.
