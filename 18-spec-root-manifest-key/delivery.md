# Delivery Plan: spec-root-manifest-key (18)

**Feature**: `18-spec-root-manifest-key` | **Date**: 2026-08-05
**Source**: `specs/18-spec-root-manifest-key/tasks.md` (34 tasks)
**Parent issue**: #18

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| 1 | T001–T034 | `wfctl/_paths.py` (modified), `wfctl/cli.py` (modified), `tests/test_paths.py` (modified), `tests/test_install_skills.py` (modified), `tests/test_spec_root.py` (created), `README.md` (modified) | M (6 files) | All four phase gates green — T006, T016, T024, T030 — plus T032 (`ruff`, `mypy`), T033 (manual quickstart walkthrough including worktree removal) and T034 (full suite vs. the T001 baseline) |

**Rationale**: Single PR. Six files at ~60 lines of implementation is M-size, which
the sizing table maps to one PR. Three of the four boundary signals say bundle:
both halves of the work edit `wfctl/_paths.py`, `wfctl/cli.py` and
`tests/test_paths.py` but can be sequenced (signal 1 → keep together); a reviewer
assessing the main-checkout guard needs the resolver it extends in the same diff
(signal 2); and US2 is not story-independent — it extends the very function US1
introduces (signal 4). Only signal 3 permits a split, since Phases 1–3 would merge
cleanly on their own, and taking it would buy no parallelism because the second PR
could not start until the first merged.

**PR closes**: `Closes #18`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #18 | T001–T034 | `feature-paths hardcodes specs/ when the dir doesn't exist yet, so specs can't live outside the repo` | ~3–4 hours | PR 1 |

**Grouping pattern**: Single issue.
**Rationale**: One PR delivers the whole feature, and #18 already exists and
describes exactly this scope — no new issue is created, and no parent epic is
needed.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Baseline: `pytest`, `ruff`, `mypy` recorded. No edits — this is the evidence SC-004 is compared against. |
| 1 | Parallel | T002 ‖ T003 ‖ T004 | Phase 2 failing tests. One file (`tests/test_install_skills.py`), independent functions. Gate: all three must FAIL. |
| 2 | Sequential | T005 → T006 | `_NON_LAYER_KEYS` change, then the Phase 2 merge gate. Blocks every story. |
| 3 | Parallel | T007 ‖ T008 ‖ T009 ‖ T010 | US1 failing tests, all in `tests/test_paths.py`, no shared fixture state. Gate: all four must FAIL. |
| 4 | Sequential | T011 → T012 → T013 → T014 → T015 → T016 | Resolver before its call sites; T011 and T012 touch the same file, T013 a second one. Ends at the Phase 3 merge gate. |
| 5 | Parallel | T017 ‖ T018 ‖ T019 ‖ T020 | US2 failing tests; each builds its own worktree in `tmp_path`. Gate: all four must FAIL. |
| 6 | Sequential | T021 → T022 → T023 → T024 | T021 edits the function T011 created — strictly after Wave 4. Ends at the Phase 4 merge gate. |
| 7 | Parallel | T025 ‖ T026 ‖ T027 | US3 failing tests across two files. Gate: all three must FAIL. |
| 8 | Sequential | T028 → T029 → T030 | Command, then the doctor check, then the Phase 5 merge gate. T028 reuses the `.git` guard from Wave 6. |
| 9 | Parallel | T031 ‖ T032 | README and lint — different surfaces. |
| 10 | Sequential | T033 → T034 | Manual quickstart walkthrough (including `git worktree remove` survival), then the full-suite final gate. |

Every task from T001 to T034 appears in exactly one wave.

**Single-agent order** (recommended): T001 → T002 → T003 → T004 → T005 → T006 →
T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 →
T018 → T019 → T020 → T021 → T022 → T023 → T024 → T025 → T026 → T027 → T028 →
T029 → T030 → T031 → T032 → T033 → T034.

---

## Agent Fanning Instructions

Single agent recommended despite the M size. The wave table shows parallelism
only among test-writing tasks, and every one of those groups lands in a single
file — fanning them to separate agents would produce concurrent edits to
`tests/test_paths.py` for no wall-clock gain. The implementation waves (4, 6, 8)
are strictly sequential: Wave 6 edits the function Wave 4 creates, and Wave 8
reuses the guard Wave 6 adds.

The wave table stands as the ordering contract and as a template for larger
features, not as a fanning plan for this one.

**Fan-in gates**: `pytest tests/test_install_skills.py` (after Wave 2),
`pytest tests/test_paths.py tests/test_install_skills.py` (after Wave 4),
`pytest tests/test_paths.py` (after Wave 6),
`pytest tests/test_spec_root.py tests/test_install_skills.py` (after Wave 8),
full `pytest` (after Wave 10).
