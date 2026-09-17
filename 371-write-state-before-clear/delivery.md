# Delivery Plan: Session restart that writes its handoff first (371)

**Feature**: `371-write-state-before-clear` | **Date**: 2026-09-15
**Source**: `specs/371-write-state-before-clear/tasks.md` (36 tasks)
**Parent issue**: #371

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (to open) | T001–T036 | `wfctl/_restart.py` (created), `wfctl/_restart_send.py` (created), `wfctl/_entry.py` (modified), `wfctl/_paths.py` (modified), `wfctl/_settings.py` (modified), `wfctl/cli.py` (modified), `wfctl/agents/commands/end-session.md` (modified), `wfctl/agents/skills/end-session/SKILL.md` (modified), `README.md` (modified); tests: `tests/test_restart_decide.py`, `tests/test_restart_occupancy.py`, `tests/test_restart_send.py`, `tests/test_restart_hook_cli.py`, `tests/test_restart_end_session.py` (created), `tests/test_settings_merge.py`, `tests/test_install_hook_merge.py`, `tests/test_paths.py` (modified) | L | `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor` green; T022 exercised; T035 live check reported |

**Rationale**: Single PR. Nine source/doc files puts this at L, which the skill says to flag rather than split. It is flagged here for the reviewer, because this run is unattended and the branch already names its one issue:

- **Mutual dependency.** The installer identity change (T003–T006) is a mergeable increment on its own, but its only reason to exist is the second Stop row; merged alone it ships prune and per-subcommand doctor logic for a case no shipped hook exercises. US1 without US2 would ship a restart that is silent on hold/skip/not-taken to every repo with the claude layer, on by default.
- **Reviewability.** The two level-2 records are one decision in two halves — a reviewer accepting `wfctl-performs-the-session-restart` needs `a-managed-hook-is-owned-by-its-subcommand` in the same diff to see it can install.
- **File conflict.** `cli.py` is touched by T006, T019 and T020; `_restart.py` by T008, T015, T016, T018, T026, T027, T031. Sequenced in one branch, not split.

If a reviewer wants a split, the clean seam is **PR A = T001–T010** (installer identity + readers, no behavior change for consumers) and **PR B = T011–T036**, each with its own issue.

**PR closes**: `Closes #371`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #371 (Session restart) | T001–T036 | `[371] Nothing writes a session's state before /clear, so a session that is not formally ended leaves nothing behind` | 1.5–2 days, plus one live pane session for T035 | the PR above |

**Grouping pattern**: Single issue
**Rationale**: The branch was cut for #371 and one PR delivers it; no issue is created, so nothing here notifies anyone.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 | baseline green |
| 1 | Parallel | T003 ‖ T005 ‖ T007 | failing tests, three different files |
| 2 | Sequential | T004 → T006 | T006 calls T004's `_settings` API |
| 2 | Parallel | T008 ‖ T009 | with T004–T006; different files |
| 3 | Sequential | T010 | Foundational merge gate |
| 4 | Parallel | T011 ‖ T012 ‖ T013 ‖ T014 | failing tests, four new files |
| 5 | Sequential | T015 → T016 → T018 → T019 → T020 | all in `_restart.py` / `cli.py` / `_entry.py`; each builds on the last |
| 5 | Parallel | T017 ‖ T021 | beside the chain above; `_restart_send.py` and the skill are separate files |
| 6 | Sequential | T022 → T023 | install, exercise, US1 gate |
| 7 | Parallel | T024 ‖ T025 ‖ T029 ‖ T030 | failing tests; two files each touched by one US |
| 8 | Sequential | T026 → T027 → T028 → T031 → T032 | all in `_restart.py` |
| 9 | Parallel | T033 ‖ T034 | README, timing |
| 10 | Sequential | T035 → T036 | live check needs a person to edit `~/.claude/settings.json`; final gate |

**Single-agent order** (recommended — see below):
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024 → T025 → T026 → T027 → T028 → T029 → T030 → T031 → T032 → T033 → T034 → T035 → T036

---

## Agent Fanning Instructions

Single agent recommended. The parallel waves are test-writing, where a fanned agent
would need the whole of `data-model.md` in context to write T011 or T024 correctly,
and every implementation wave funnels through `_restart.py` or `cli.py`. The
classifier risk in `plan.md` also argues for one agent that can stop and report
rather than several that might each route around a refusal differently.
