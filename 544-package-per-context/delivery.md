# Delivery Plan: Check imports against the Context Map (544)

**Feature**: `544-package-per-context` | **Date**: 2026-11-02
**Source**: `tasks.md` (61 tasks)
**Parent issue**: #86

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (one PR) | T001 - T061 | `.github/scripts/check_imports.py` (created), `.github/scripts/check_imports.baseline` (created), `tests/test_import_check.py` (created), `docs/architecture/domain/wfctl.md` (modified), `wfctl/_review_notes.py` (modified), `wfctl/cli.py` (modified), `wfctl/_review_gate.py` (modified), `tests/test_review_notes.py` (modified), `tests/test_review_gate.py` (modified), `tests/test_review_workflow.py` (modified), `wfctl.json` (modified), `.github/workflows/ci.yml` (modified), `.github/workflows/review.yml` (modified), `AGENTS.md` (modified), `changes/544.addition.md` (created) | L | Every review group has reviewed HEAD, CI is green, and the user merges by hand after checking the 39 placement lines against research R7 and reading the diffs of both `TRUSTED` files (T061, FR-015) |

**Rationale**: Single PR. The work splits cleanly between the import check
(Phases 1 - 7, T054, T055) and the approval check (Phase 8, T056). We considered
shipping them as two PRs, and the user chose one so that approval is enforced
from the first merge. Otherwise there would be a window where a branch could add
baseline lines or map arrows that nobody approved.

Most of the 15 files are small edits. The bulk of the code goes into two new
files, the script and its test file.

**PR closes**: `Closes #544`

#544 is one part of epic #86, so this PR doesn't close #86.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #544 | T001 - T061 | `[544] Check imports against the Context Map` | L | this branch's PR |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, so it closes exactly one
issue. The module moves are tracked separately under #671 and aren't part of this
plan.

---

## Parallelization Waves

Most implementation tasks edit `.github/scripts/check_imports.py`, so they run
one after another. The parallel waves are mostly test writing and the edits
outside the script.

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 | No dependencies |
| 1 | Parallel | T003 + T004 ‖ T005 - T009 | T003 and T004 edit the domain page, so one agent does both. T005 - T009 all write to `tests/test_import_check.py`, so they go in sequence or in separate test classes |
| 2 | Sequential | T010 → T011 → T012 → T013 → T014 → T015 | All edit the script. T015 is the Phase 2 merge gate |
| 3 | Sequential | T016, T017 → T018 → T019 → T020 | US1. T020 is its gate |
| 4 | Sequential | T021 - T023 → T024 → T025 → T026 | US2. It extends US1's rule list, so it runs after US1 |
| 5 | Parallel | US3 (T027 - T033) ‖ US4 (T034 - T039) ‖ US5 (T040 - T042) | They change different functions in the same script, so merge them one at a time. US3's real-tree test needs US2 done |
| 6 | Parallel | T043 - T047 | Phase 8 tests. They go in three different test files |
| 7 | Sequential | T048 → T049 → T050 → T051 → T052 → T053 | T048 and T049 edit the script, and T050 - T052 edit wfctl. T053 is the gate |
| 8 | Parallel | T054 ‖ T055 ‖ T056 → T057 | T055 and T056 both add tests to `tests/test_review_workflow.py`. T056 has to settle plan-review finding PR-042, saying how the step runs in `pr` without breaking `test_nothing_from_the_prs_checkout_is_executed` |
| 9 | Parallel | T058 ‖ T059 → T060 → T061 | T060 is the definition of done. T061 is the PR body |

**Single-agent order** (recommended):
T001 → T015, then US1 → US2 → US3 → US4 → US5, then T043 → T053, T054 → T057,
and T058 → T061.

---

## Agent Fanning Instructions

We recommend one agent for this feature. Nearly every implementation task edits
the same script, so parallel agents would spend their time merging one file. The
waves above mark where test writing could fan out if needed.
