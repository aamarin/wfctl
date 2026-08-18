# Delivery Plan: step-command drift check (31)

**Feature**: `31-step-command-drift-check` | **Date**: 2026-08-17
**Source**: `specs/31-step-command-drift-check/tasks.md` (19 tasks)
**Parent issue**: #31

---

## File-Touch Matrix

| Task | File | Action |
| --- | --- | --- |
| T001, T002 | — | READ ONLY (baseline capture) |
| T003, T004 | `tests/test_pipeline_commands.py` | CREATE |
| T005, T006 | `wfctl/_pipeline.py` | MODIFY |
| T007 | — | READ ONLY (gate) |
| T008–T012 | `tests/test_pipeline_commands.py` | MODIFY |
| T013, T014 | — | READ ONLY (baseline diff, gate) |
| T015, T016 | `tests/test_pipeline_commands.py` | MODIFY |
| T017 | — | READ ONLY (gate) |
| T018, T019 | — | READ ONLY (CI config re-read, gate) |

**Two files.** One created, one modified. Seven of the nineteen tasks write
nothing at all.

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
| --- | --- | --- | --- | --- |
| 1 | T001–T019 | `wfctl/_pipeline.py` (modified), `tests/test_pipeline_commands.py` (created) | **XS** | `uv run pytest -q && uv run mypy && uv run ruff check .` green on 3.11 and 3.13 |

**Rationale**: Single PR. All four boundary signals point the same way.

1. **File conflict risk** — no. Two files, and every task that touches
   `tests/test_pipeline_commands.py` is sequenced within one story.
2. **Reviewability** — bundle. The restructure and the check only make sense
   read together: the check exists because the merged table cannot guarantee that
   a named command is a real file, and the merged table exists because the check
   could not see the two worse drift shapes. Split across two PRs, each reviewer
   sees half an argument.
3. **Mergeable increment** — the MVP boundary (Phases 1, 3, 4) *is* mergeable
   alone, and would be a legitimate PR. But it lands in the same two files as
   Phase 5, so splitting buys a second review cycle over a three-line message
   change and nothing else.
4. **Story independence** — no. US1 reads the table US3 produces, and US2 only
   rewrites US1's failure message. None has a separate runtime path.

**PR closes**: `Closes #31`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
| --- | --- | --- | --- | --- |
| #31 | T001–T019 | Nothing checks that `_STEP_COMMAND` names commands wf-skills actually installs | ~45 min | PR #1 |

**Grouping pattern**: Single issue.
**Rationale**: XS feature, one PR, and the issue already exists — the branch is
named `31-step-command-drift-check` for it. No issue is created here; creating a
second would put two issues behind one PR, which the rule forbids.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
| --- | --- | --- | --- |
| 0 | Parallel | T001 ‖ T002 | Baseline capture, no edits. T002's output is consumed by T013 — capture before anything moves. |
| 1 | Sequential | T003 → T004 | Same new file. **T003 must pass against the current three-table code**, before T005 exists. A behaviour test written after the refactor tests the new structure, not the old behaviour. |
| 2 | Sequential | T005 → T006 → T007 | Both edit `wfctl/_pipeline.py`. T007 is the fan-in gate: `pytest && mypy && ruff`. |
| 3 | Sequential | T008 → T009 | T009 (`_unresolved`) is the helper the next three tasks all call. |
| 4 | Parallel | T010 ‖ T011 ‖ T012 | Independent of one another once T009 exists — different assertions, no shared state. Same file, so not marked `[P]` in `tasks.md`; write in any order. |
| 5 | Sequential | T013 → T014 | T013 diffs `wfctl status` against the Wave 0 baseline. T014 is the MVP merge gate — **the feature is shippable here.** |
| 6 | Sequential | T015 → T016 → T017 | Failure-message work. Same file, and T016 asserts what T015 renders. |
| 7 | Parallel | T018 ‖ T019 | T018 re-reads CI config and writes nothing. T019 is the final gate. |

**Single-agent order** (recommended for this XS feature):
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 →
T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019

---

## Agent Fanning Instructions

Single agent. Nineteen tasks across two files, of which seven write nothing —
fanning would cost more coordination than the work contains.

The wave table above is for ordering, not for parallelism. Only two waves hold
genuinely concurrent work (0 and 4), and both are small enough that a single
agent does them in sequence faster than two agents can hand off.

**The one ordering constraint that is not a preference**: T003 before T005. It is
recorded in the Wave 1 gate and repeated here because getting it wrong produces a
green suite that proves nothing.
