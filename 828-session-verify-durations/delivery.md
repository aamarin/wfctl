# Delivery Plan: wfctl measures feature time and verify cost (828)

**Feature**: `828-session-verify-durations` | **Date**: 2026-11-20
**Source**: `828-session-verify-durations/tasks.md` (42 tasks)
**Parent issue**: none

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (to open) | T001–T042 | `changes/828.addition.md` (created), `wfctl/_verify.py` (modified), `wfctl/evidence/_events.py` (modified), `wfctl/evidence/_timings.py` (created), `wfctl/evidence/__init__.py` (modified), `wfctl/cli.py` (modified), `tests/test_verify.py` (modified), `tests/test_worktree_remove.py` (modified), `tests/test_timings.py` (created), `docs/reference.md` (modified), `README.md` (modified, if it lists commands) | L | The user has accepted or rejected `worktree-span-read-from-git` and `828-verify-measures-each-child`, `uv run wfctl verify` and `uv run wfctl doctor` are green, and every review group has reviewed HEAD |

**Rationale**: Single PR. The change is L by file count, but three of the eleven files are tests and two are docs, so the source change is five files. The only clean split follows the two records: verify timing in one PR, and worktree lifetime with `wfctl timings` in the other. The user chose one PR over that split on 2026-11-20. A split needs a new issue and a second review panel, and it only helps if one record is held while the other is accepted.

**PR closes**: `Closes #828`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #828 | T001–T042 | wfctl records session and verify durations | L | PR (to open) |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, so the branch's own issue is the only one and no issue is created.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | The release note has no dependencies. Implementation waits on both proposed records. |
| 1 | Parallel | T002 → T003 ‖ T004–T009 (US1 tests) | Foundational changes `_events.py` and `test_timings.py`, and US1 changes `_verify.py` and `test_verify.py`, so they share no file. |
| 2 | Parallel | T010 → T011 → T012 → T013 → T014 → T015 ‖ T016–T020 (US2 tests) ‖ T024–T033 (US3 tests) | The US2 and US3 tests need T003. US1 ends at its gate, T015. |
| 3 | Sequential | T021 → T022 → T023 | US2 implementation. T021 edits `evidence/__init__.py` and T022 edits `cli.py`. |
| 4 | Sequential | T034 → T035 → T036 → T037 → T038 → T039 | US3 implementation. T038 edits `cli.py` and `evidence/__init__.py` after US2's edits to them. |
| 5 | Sequential | T040 → T041 → T042 | Docs, then the quickstart (the user runs step 3), then verify and doctor as the merge gate. |

**Single-agent order** (recommended):
T001 → T002 → T003 → T004–T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016–T020 → T021 → T022 → T023 → T024–T033 → T034 → T035 → T036 → T037 → T038 → T039 → T040 → T041 → T042

---

## Agent Fanning Instructions

A single agent is recommended. US2 and US3 both edit `wfctl/cli.py` and `wfctl/evidence/__init__.py`, and each story's test tasks share one test file, so the edits can't run in parallel. US1 could go to a second agent beside Foundational, since it shares no file, but the time saved is small next to the cost of merging two sessions' commits on one branch.
