# Delivery Plan: Drop unloaded skills (698)

**Feature**: `698-drop-unloaded-skills` | **Date**: 2026-11-03
**Source**: `specs/698-drop-unloaded-skills/tasks.md` (17 tasks)
**Parent issue**: none

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (not yet opened) | T001 - T017 | `wfctl/cli.py` (modified), `wfctl/agents/skills/` (3 deleted, 3 modified), `wfctl/agents/commands/` (3 deleted, 1 modified), `docs/architecture/` (3 modified), `tests/` (3 modified), `changes/698.change.md` (created) | S | CI green, review groups clear |

**Rationale**: Single PR. The deletions, the mirror edit, and the tests that pin
them fail each other's checks when split, since the pinned wrapper set and the
mirror set have to change in the same commit.

**PR closes**: `Closes #698`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #698 | T001 - T017 | Stop shipping skills that sessions never load | S | the #698 PR |

**Grouping pattern**: Single issue

**Rationale**: An S feature that one PR delivers whole, so no new issue is created.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | baseline green |
| 1 | Sequential | T002 → T003 → T004 | tests written first, failing |
| 2 | Sequential | T005 → T006 | the mirror set can't name a deleted skill |
| 3 | Parallel | T007 ‖ T008 ‖ T009 ‖ T010 ‖ T011 | different files |
| 4 | Sequential | T012 → T013 → T014 | against the trimmed bundle |
| 5 | Sequential | T015 → T016 → T017 | verification last |

**Single-agent order** (recommended for S features):
T001 → T002 → ... → T017

---

## Agent Fanning Instructions

A single agent is recommended for this S feature. The wave table is for
reference.
