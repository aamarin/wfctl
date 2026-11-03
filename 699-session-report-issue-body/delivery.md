# Delivery Plan: Session report issue body (699)

**Feature**: `699-session-report-issue-body` | **Date**: 2026-11-03
**Source**: `tasks.md` in this spec folder (20 tasks)
**Parent issue**: none

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (to be opened) | T001 - T020 | `wfctl/_session_report.py` (modified), `tests/test_session_report.py` (modified), `tests/test_start_session_asks_conditionally.py` (modified), `wfctl/agents/skills/start-session/SKILL.md` (modified), `wfctl/agents/skills/start-session/references/rationale.md` (modified), `changes/699.change.md` (created) | S | T020 passes: the full suite, ruff, mypy, `wfctl doctor`, and `wfctl verify` |

**Rationale**: Single PR. The two stories share one function and one test file, and hiding the body is only correct when the no-handoff case still prints it, so neither half can merge alone.

**PR closes**: `Closes #699`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #699 | T001 - T020 | `[699] Session report prints the issue body only on a branch's first session` | S | the PR above |

**Grouping pattern**: Single issue
**Rationale**: The branch's own issue covers the whole change, so no issue needs creating.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 → T003 | The two existing tests pass with `handoff=lambda: None` before the renderer changes |
| 1 | Parallel | (T004 - T009 → T010 → T011) ‖ (T012 → T013) | The renderer and its tests, beside the skill row and its test. Different files. |
| 2 | Sequential | T014 → T015 → T016 | Both stories' merge gates |
| 3 | Sequential | T017 → T018 → T019 → T020 | Definition of done, install, quickstart |

**Single-agent order** (recommended for this S feature):
T001 → T002 → T003 → T004 - T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020

---

## Agent Fanning Instructions

A single agent is recommended for this S feature. The wave table is here for reference.
