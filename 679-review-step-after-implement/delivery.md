# Delivery Plan: Review step after implement (679)

**Feature**: `679-review-step-after-implement` | **Date**: 2026-11-01
**Source**: `tasks.md` in this feature folder (54 tasks)
**Parent issue**: #679

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (opened at the end of implement) | T001 - T054 | `wfctl/_review.py`, `wfctl/_review_gate.py`, `wfctl/_evidence.py`, `wfctl/_pipeline.py`, `wfctl/_declared.py`, `wfctl/_stall.py`, `wfctl/_contract.py`, `wfctl/_design_exceptions.py`, `wfctl/cli.py`, `wfctl/contracts/status-payload.json` (all modified); 4 skills under `wfctl/agents/skills/`, `README.md`, `AGENTS.md` (modified); `changes/679.addition.md` (created); about 14 test files | XL by file count | `uv run pytest -q`, ruff, and mypy green; `uv run wfctl doctor` green; every review group has reviewed HEAD |

**Rationale**: Single PR. The file count reads XL, but most of it is one change seen from every reader of the step table, and splitting it doesn't make either half easier to review:

1. The two halves edit the same four modules, `_evidence.py`, `_pipeline.py`, `cli.py`, and `_contract.py`, so two PRs would conflict in each one.
2. The no-spec route ends at the review step, so its main acceptance scenario (User Story 2, scenario 3) can't be tested without the review row.
3. The user already decided to keep the no-spec route on this branch (2026-10-31), and the two level-3 records and the accepted level-2 records were written for one change.

The one cut that could merge alone is the shared review function (Phase 2), which changes nothing visible. We didn't make it its own PR, because a PR with no visible change can't be checked against the feature it exists for, and it's the smallest phase.

**PR closes**: `Closes #679`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #679 | T001 - T054 | `Make review a pipeline step after implement` | XL, one PR | the branch's PR |

**Grouping pattern**: Single issue
**Rationale**: One PR closes exactly one issue, and #679 already exists, so no issue is created.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Baseline green before any edit |
| 1 | Sequential | T002 → T005 → T006 → T007 → T008 → T009 | All edit `tests/test_review.py` or `wfctl/_review.py`; T009 is the merge gate |
| 2 | Parallel | T010 + T011 ‖ T012 + T015 ‖ T013 ‖ T014 | US1 tests, grouped by shared file |
| 3 | Sequential | T016 → T017 → T018, with T019 ‖ T020 beside them | Evidence field before reader, reader before the step table |
| 4 | Sequential | T021 → T022 → T024 → T025 → T026 → T027 → T028 | T028 is the US1 merge gate; T023 waits for wave 6 |
| 5 | Parallel | T029 ‖ T030 + T031 ‖ T032 | US2 tests |
| 6 | Sequential | T033 → T034 → T035 → T036 → T037 → T023 → T038 → T039 | T023 runs here, after T034, as analyze's finding F2 records |
| 7 | Sequential | T040 → T041 → T042 | US3 |
| 8 | Parallel | T043 ‖ T044 ‖ T046 ‖ T047 ‖ T048 | Skill text and docs, different files |
| 9 | Sequential | T049 → T050 → T045 → T051 → T052 → T053 → T054 | T045 and T051 need the user; T052 and T053 need implement done on this branch |

**Single-agent order** (recommended): the waves above in order, one agent. The parallel waves are small, and most tasks share `_evidence.py`, `_pipeline.py`, or `cli.py`, so fanning out would mostly trade time for merge conflicts.

---

## Agent Fanning Instructions

Single agent recommended. The wave table shows where parallel work is safe if a later run wants it.
