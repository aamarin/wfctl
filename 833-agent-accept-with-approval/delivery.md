# Delivery Plan: Agent accepts with approval (833)

**Feature**: `833-agent-accept-with-approval` | **Date**: 2026-11-20
**Source**: `specs/833-agent-accept-with-approval/tasks.md` (29 tasks)
**Parent issue**: none

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (this branch's PR) | T001 - T029 | `wfctl/evidence/_prompted.py` (created), `wfctl/evidence/__init__.py`, `wfctl/_review_gate.py`, `wfctl/guard/_hook.py`, `wfctl/cli.py`, `wfctl/_review_notes.py`, `wfctl/_evidence.py`, `wfctl/arch/_records.py`, `wfctl/agents/codex/rules/wfctl.rules` (modified); about 9 skill files under `wfctl/agents/` and `AGENTS.md` (prose); `tests/test_prompted.py`, `tests/test_prompted_rules.py` (created), 7 test files (modified); `changes/833.change.md` (created) | L | #407 merged and this branch rebased; definition of done green; every review group run; the quickstart walk done |

**Rationale**: Single PR. Signal 3 decides it. The guard change, the commands' terminal checks, and the installed rules only make sense together. Merged alone, the guard change lets the plain spelling through to a command that still refuses. The commands change alone loosens the terminal check with no prompt in front of it. Signal 2 points the same way, since the security reviewers judge all three against one threat model.

The file count reaches L, which the delivery plan says to flag rather than split. Nine of the files are prose edits to skills and `AGENTS.md`, so the code change sits at M. This is flagged to the user, and the default stands unless they ask for a split.

**PR closes**: `Closes #833`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #833 | T001 - T029 | `[833] The agent runs arch accept after the user approves the prompt` | L | this branch's PR |

**Grouping pattern**: Single issue
**Rationale**: one PR closes one issue, and #833 already exists, so nothing is created.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001, T002 | #407 merged and rebased; suite green |
| 1 | Sequential | T003 → T004 | the table and its exports |
| 2 | Parallel | T005 ‖ T006 | `uv run pytest tests/test_prompted.py -q` |
| 3 | Sequential | T007 → T008 → T009 → T010 | all in `_review_gate.py` |
| 4 | Parallel | T011 ‖ T012 | `uv run pytest tests/test_review_gate.py tests/test_accept_check_threat_model.py -q` |
| 5 | Parallel | (T013 → T014 → T015 → T016) ‖ (T017 → T018) ‖ (T019 → T020) ‖ (T021 → T022 → T023) | T013, T014, T017, T019's `cli.py` part, and T021 all edit `cli.py`, so one agent takes those, or they're sequenced |
| 6 | Parallel | T024 ‖ T025 ‖ T026 ‖ T027 | T025 after T014 |
| 7 | Sequential | T028 → T029 | definition of done, then the walk with the user |

**Single-agent order** (recommended, since wave 5's parallel branches share `cli.py`):
T001 → T002 → T003 → … → T029

---

## Agent Fanning Instructions

Single agent recommended. Wave 5's branches all edit `wfctl/cli.py`, and wave 3 is one file, so fanning saves little and risks conflicting edits. Wave 6's prose edits (T026, T027) can go to a parallel agent once T014 lands, with the `writing-style` skill loaded.

**Fan-in gate after wave 6:** `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy`
