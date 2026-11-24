# Delivery Plan: Install asks before changing a settings file (859)

**Feature**: `859-ask-rule-literal-star` | **Date**: 2026-11-23
**Source**: `tasks.md` (52 tasks)
**Parent issue**: none

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (to open) | T001–T052 | `wfctl/cli.py` (modified), `tests/test_settings_ask.py` (created), `tests/test_install_hook_merge.py` (modified), the existing install and doctor tests that expect an unattended save or a doctor exit 1 (modified by T029 and T045), `changes/859.fix.md` (modified), `wfctl/agents/skills/start-session/references/doctor-repair.md` (modified), `docs/reference.md` (modified) | M | pytest, ruff, mypy, and `wfctl verify` are green, and the security and code review groups cover HEAD |

**Rationale**: Single PR. Every implementation task edits `wfctl/cli.py`. If the Phase 2 refactor or US1 landed alone, the release would still change settings files unattended, which is the defect this branch fixes.

**PR closes**: `Closes #859`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #859 | T001–T052 | `[859] An auto-approve ask rule reads its * literally` | M | the PR above |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, so the branch's own issue is the only one, and it already exists.

T050 files a follow-up issue to amend `docs/architecture/install-modes.md`. This PR doesn't close that issue, so it has no row here.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | The test file collects with no errors |
| 1 | Sequential | T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 | All in `wfctl/cli.py`. T011 gate: the full suite, ruff, and mypy are green |
| 2 | Parallel | T012 ‖ T013 ‖ T014 ‖ T015 ‖ T016 ‖ T017 ‖ T018 ‖ T019 ‖ T020 | US1 tests in separate functions. Each fails before wave 3 |
| 3 | Sequential | T021 → T022 → T023 → T024 → T025 → T026 | `_save_settings` and install. T026 gate |
| 4 | Parallel | T027 ‖ T028 | US2 tests |
| 5 | Sequential | T029 → T030 → T031 | T029 also patches the existing tests to answer yes. T031 gate |
| 6 | Parallel | T032 ‖ T033 ‖ T034 | US3 tests |
| 7 | Sequential | T035 → T036 → T037 | T035 and T036 land together so the suite stays green |
| 8 | Parallel | T038 ‖ T039 ‖ T040 ‖ T041 | US4 tests |
| 9 | Sequential | T042 → T043 → T044 → T045 → T046 | Doctor. T043 and T045 land together |
| 10 | Parallel | T047 ‖ T048 ‖ T049 ‖ T050 | Separate files. T050 is a tracker write |
| 11 | Sequential | T051 → T052 | The user runs T052's attended install at a terminal |

**Single-agent order** (recommended): T001 to T011, then US1 (T012 to T026), US2 (T027 to T031), US3 (T032 to T037), US4 (T038 to T046), and Polish (T047 to T052).

---

## Agent Fanning Instructions

We recommend a single agent. Every implementation task edits `wfctl/cli.py`, so the only safe parallel work is drafting tests within a wave, and that saves little over writing them in order. US4 (waves 8 and 9) could run beside waves 2 to 7 once wave 1 is done, but it would edit the same file as US1 to US3 at the same time, so it stays sequential.
