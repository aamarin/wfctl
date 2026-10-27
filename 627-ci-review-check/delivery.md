# Delivery Plan: A required CI check fails a PR while a review group has unreviewed commits (627)

**Feature**: `627-ci-review-check` | **Date**: 2026-10-25
**Source**: `tasks.md` in this feature directory (55 tasks)
**Parent issue**: #627

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (opened at implement) | T001 - T055 | `wfctl/_review.py` (modified), `wfctl/_review_gate.py` (modified), `wfctl/_review_config.py` (modified), `wfctl/_review_notes.py` (created), `wfctl/_hook.py` (modified), `wfctl/cli.py` (modified), `.github/workflows/review.yml` (created), `.github/workflows/ci.yml` (modified), `.github/rulesets/main.json` (modified), `.github/scripts/release.py` (modified), `AGENTS.md` (modified), `docs/reference.md` (modified), `changes/627.addition.md` (created), plus 8 test files | L | `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `uv run wfctl verify` pass, both review groups have reviewed the head, and CI is green |

**Rationale**: Single PR. The user approved one PR on 2026-10-25 after the L size was flagged. We chose one PR for three reasons.

The three P1 stories can't be merged separately in a useful way. The check can't pass any PR until US3 builds the group list and the counting function, US2 writes the notes, and US1 reads them in CI.

The two P2 stories depend on the P1 code. US4 extends the `send` function US2 adds, and US5's guard rule matters only once wfctl writes notes.

The file count overstates the size. `ci.yml`, `main.json`, `release.py`, and `_hook.py` each get an edit of a few lines.

We didn't choose a first PR holding Phase 2 and US3. It would merge cleanly, but it changes which groups the guard requires and gives the user nothing new to use until the later PRs land.

**PR closes**: `Closes #627`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #627 (Issue A) | T001 - T055 | `[627] A required CI check fails a PR while a review group has unreviewed commits` | L | the implementation PR |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, so the branch's own issue is the only issue, and decompose creates none.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | no dependencies |
| 1 | Parallel | T002 ‖ T003 ‖ T004 | tests for Phase 2, written first |
| 2 | Sequential | T005 → T006 → T007 → T008 → T009 | T006 needs T005's `trunk` keyword, and T007 updates T006's callers. Gate: T009 |
| 3 | Parallel | T010 ‖ T011 ‖ T012 ‖ T013 ‖ T014 ‖ T048 | US3 tests, and US5's tests, which need only Phase 2 |
| 4 | Sequential | T015 → T016 → T017 → T018 → T019 → T020 | T016 and T017 both edit `cli.py`, and T019 needs T017. Gate: T020 |
| 5 | Parallel | T049 ‖ T021 ‖ T022 ‖ T023 ‖ T024 ‖ T025 ‖ T026 | T049 edits `_review_gate.py` and `_hook.py`, and touches no file the US2 tests do |
| 6 | Sequential | T050 → T027 → T028 → T029 → T030 → T031 | T050 is US5's gate. T029 and T030 both edit `cli.py` and `contracts/cli.md`. Gate: T031 |
| 7 | Parallel | T032 ‖ T033 ‖ T034 ‖ T035 ‖ T036 ‖ T037 | US1 tests |
| 8 | Sequential | T038 | `check reviews` in `cli.py` |
| 9 | Parallel | T039 ‖ T040 ‖ T041 ‖ T042 | different files. Fan-in gate: T043 |
| 10 | Sequential | T043 | merge gate |
| 11 | Parallel | T044 ‖ T045 | US4 tests |
| 12 | Sequential | T046 → T047 | gate: T047 |
| 13 | Parallel | T051 ‖ T052 ‖ T053 | docs |
| 14 | Sequential | T054 → T055 | T054 runs both review groups on the branch. Final gate: T055 |

**Single-agent order** (recommended):
T001 → T002 - T009 → T010 - T020 → T048 - T050 → T021 - T031 → T032 - T043 → T044 - T047 → T051 - T055

---

## Agent Fanning Instructions

A single agent is recommended. Most phases funnel through `wfctl/cli.py` and `contracts/cli.md`, so the parallel waves above hold only test-writing and small file edits. Fanning those out saves little time and leaves the implementing agent to reconcile tests it didn't write. The wave table shows where parallelism is safe if a later session wants it.
