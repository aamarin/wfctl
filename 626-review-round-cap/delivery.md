# Delivery Plan: wfctl stops a review group after three rounds (626)

**Feature**: `626-review-round-cap` | **Date**: 2026-10-26
**Source**: `626-review-round-cap/tasks.md` (39 tasks)
**Parent issue**: #626

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| One PR, not yet opened | T001 - T039 | `wfctl/_review_config.py` (modified), `wfctl/_review.py` (modified), `wfctl/cli.py` (modified), `wfctl/agents/skills/opening-a-change/SKILL.md` (modified), `wfctl/agents/skills/fanning-out-code-review/SKILL.md` (modified), `AGENTS.md` (modified), `docs/architecture/design/642-commit-range-takes-judged-branch.md` (modified), `docs/architecture/design/642-origin-head-trusted-on-full-fetch.md` (modified), `changes/626.addition.md` (created), `changes/626.change.md` (created), and six test files | L by file count, M by code | T038 passes, every review group has signed off, and the spec dir is stored (T039) |

**Rationale**: Single PR. Only three of the ten files carry code, and the rest
are skill text, docs, and release notes. US1 and US3 both rewrite `start` in
`_review.py` and `review_start_cmd` in `cli.py`, and T030 replaces the cap that
T014 passes. A PR with US1 alone would ship a `review.rounds` key that
`wfctl check config` accepts and nothing reads. US2's skill text describes the
cap that US1 enforces, so it can't merge first either.

**PR closes**: `Closes #626`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #626 | T001 - T039 | `[626] wfctl stops a review group after three rounds` | M | The one PR above |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the feature, and #626 is already open, so there
is no issue to create.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Baseline is green, no edits |
| 1 | Parallel | T002 ‖ T004 ‖ T016 ‖ T017 | Different test files, and US2 needs nothing from Phase 2 |
| 2 | Parallel | T003 → T005 → T006 ‖ T018 ‖ T019 | T005 and T006 both edit `_review.py`, so they run in order |
| 3 | Sequential | T007 → T020 → T021 | Phase 2 gate, then read the installed skills |
| 4 | Parallel | T008 ‖ T009 ‖ T010 | T008 and T009 both edit `tests/test_review.py`, so write them in one pass |
| 5 | Sequential | T011 → T012 → T013 → T014 → T015 | `_review.py`, then `cli.py`, then the US1 gate |
| 6 | Parallel | T022 ‖ T023 ‖ T024 ‖ T025 ‖ T026 | T022 to T024 share `tests/test_review.py`, so write them in one pass |
| 7 | Sequential | T027 → T028 → T029 → T030 → T031 → T032 → T033 | `_review.py`, then `cli.py`, then the US3 gate |
| 8 | Parallel | T034 ‖ T035 ‖ T036 | Different files, all prose |
| 9 | Sequential | T037 → T038 → T039 | End-to-end run, final gate, then store the specs |

**Single-agent order** (recommended):
T001 → T002 → ... → T039, in tasks.md order.

---

## Agent Fanning Instructions

We recommend a single agent. After wave 1, every code wave edits `_review.py`
or `cli.py` in order, so only the test-writing and prose waves can run in
parallel. For those, starting a second agent costs more than it saves. If a
second agent is used, give it US2 (T016 to T021), since it changes only the two
skills and their tests.
