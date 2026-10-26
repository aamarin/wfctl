# Delivery Plan: Brainstorm holds until the software design question is answered (648)

**Feature**: `648-design-gate` | **Date**: 2026-10-26
**Source**: `648-design-gate/tasks.md` (57 tasks)
**Parent issue**: #648

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (opened at implement) | T001 - T057 | `wfctl/_paths.py`, `wfctl/_pipeline.py`, `wfctl/_evidence.py`, `wfctl/cli.py`, `wfctl/agents/commands/speckit.brainstorm.md`, `wfctl/agents/skills/{design-levels,speckit-brainstorm,software-design-decisions}/SKILL.md`, `README.md`, `docs/reference.md`, `docs/architecture/design/software-design-none-is-a-claim.md` (all modified); `changes/648.change.md`, `tests/test_software_design_pass.py` (created); about 8 existing test files (modified) | L | T057 green: suite, ruff, mypy, `wfctl verify`, `wfctl doctor`, `wfctl check config`, and `quickstart.md` |

**Rationale**: Single PR. The file count puts it at L, but most of that is three
skill files and two docs that change a few lines each, and the code sits in four
modules. The stories can't merge separately. US1 alone holds branches with no
claim answer, US1 and US5 both change `_evidence.py` and the same new test file,
and US4's skill text names the claim US3 grants. A split would put
half-finished behaviour on `main`. This run was unattended, so the size wasn't
discussed with a person, and the reviewer can ask for a split at the PR.

**PR closes**: `Closes #648`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #648 | T001 - T057 | `[648] Brainstorm holds until the software design question is answered` | L | the single PR above |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, and #648 is already open, so no
issue is created.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Parallel | T001 ‖ T002 ‖ T004 ‖ T005 | Planning artifact fixes, separate files. T003 is done. |
| 1 | Sequential | T006 → T007 → T008 → T009 → T010 → T011 | Foundational. T006 to T008 share `_paths.py`. Gate: T011 |
| 2 | Sequential | T012 - T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 | US1. Tests first, then the reader and the pass. T020 needs the suite's failures, so it follows T017. Gate: T022 |
| 3 | Parallel | (T023 - T027) ‖ (T028, T029, T030 → T031 → T032 → T033) | US2 and US3. US2 adds tests only; US3 touches the grant files. Both write `tests/test_software_design_pass.py`, so commit them one after the other. Gates: T027, T033 |
| 4 | Parallel | T034 → (T035 ‖ T036 ‖ T037) → T038 | US4, three separate skill files. Load `writing-style` first. Gate: T038 |
| 5 | Sequential | T039 - T045 → T046 → T047 → T048 → T049 → T050 → T051 → T052 → T053 | US5. T046 to T048 share `_evidence.py`. Gate: T053 |
| 6 | Parallel | T054 ‖ T055 ‖ T056 → T057 | Polish, then the definition of done |

**Single-agent order** (recommended):
T001 → T002 → T004 → T005 → T006 … T022 → T023 … T033 → T034 … T038 → T039 … T053 → T054 → T055 → T056 → T057

---

## Agent Fanning Instructions

Single agent recommended. Every story after US1 writes to
`tests/test_software_design_pass.py` or `_evidence.py`, so parallel agents would
spend more on merging than they save. Waves 0 and 4 are the only safe fan-outs,
and each is a few minutes of work.

**Fan-in gate after each wave:** `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy`
