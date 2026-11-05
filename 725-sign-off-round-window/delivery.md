# Delivery Plan: A sign-off opens a new window of review rounds (725)

**Feature**: `725-sign-off-round-window` | **Date**: 2026-11-05
**Source**: `specs/725-sign-off-round-window/tasks.md` (25 tasks)
**Parent issue**: #621

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (opened at the end of implement) | T001 - T025 | `wfctl/_review.py` (modified), `wfctl/cli.py` (modified), `tests/test_review.py` (modified), `tests/test_review_cli.py` (modified), `wfctl/agents/skills/opening-a-change/SKILL.md` (modified), `wfctl/agents/skills/fanning-out-code-review/SKILL.md` (modified), `AGENTS.md` (modified), `changes/725.change.md` (created) | M | CI green, every review group has reviewed HEAD, and the user has accepted `review-round-window` |

**Rationale**: Single PR. The code change is two modules, and the three docs describe the behavior that code changes, so a PR without them would leave agents reading the old rule.

**PR closes**: `Closes #725`

#725 isn't the last child of #621, so the PR doesn't close the parent.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #725 | T001 - T025 | `A sign-off allows three more review rounds` | M | the one PR above |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, and the branch's own issue already exists, so no issue is created.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | no dependencies |
| 1 | Sequential | T002 → T003 → T004 → T005 → T006 → T007 → T008 | all in `wfctl/_review.py` and `tests/test_review.py`; T008 is the gate |
| 2 | Sequential | T009 - T013 → T014 → T015 - T016 → T017 → T018 | tests first, then `start`, then `cli.py`; T018 is the gate |
| 3 | Parallel | T019 ‖ T020 → T021 | T019 only runs tests; T020 and T021 edit `_review.py` after Wave 2 |
| 4 | Parallel | T022 ‖ T023 | different skill files |
| 5 | Sequential | T024 → T025 | quickstart walk, then the definition of done |

**Single-agent order** (recommended for this M feature):
T001 → T002 → … → T025

---

## Agent Fanning Instructions

Single agent recommended. Waves 1 - 3 all edit `wfctl/_review.py` and `tests/test_review.py`, so parallel agents would conflict, and Wave 4 is two short doc edits.
