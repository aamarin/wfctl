# Delivery Plan: record leads with drawing (109)

**Feature**: `109-record-leads-with-drawing` | **Date**: 2026-09-16
**Source**: `specs/109-record-leads-with-drawing/tasks.md` (40 tasks)
**Parent issue**: #109

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR #1 | T001–T040 | `wfctl/_arch.py` (modified), `wfctl/cli.py` (modified), `tests/test_arch_diagram.py` (created), `tests/test_arch_sections.py` (created), `tests/test_arch_accept_drawing.py` (created), `tests/test_arch_labels.py` (created), `wfctl/agents/skills/architecture-decisions/record-template.md` (modified), `wfctl/agents/skills/architecture-decisions/SKILL.md` (modified), `docs/architecture/design/109-traceability-is-label-agreement.md` (modified) | L | T040 — `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && uv run wfctl doctor` — plus the two judgments no command returns: T017 (the refusal reads well cold) and T031 (SC-004) |

**Rationale**: Single PR, chosen by the user against this plan's own input. Nine
files and three merge gates in one review is L by the sizing table, and
`tasks.md`'s Logical PR Boundaries argued for three slices. Both costs of
declining that are real and are recorded here rather than discovered at review:

- **T024's manual skills pass covers one half of one PR.** Phase 4 is the only
  phase that changes `wfctl/agents/`, and a green suite is not evidence about a
  skills change (AGENTS.md). In a three-PR split the reviewer knows T024 covered
  that PR entirely. Here the PR body has to say which files it exercised, because
  the diff cannot.
- **Phase 5 is droppable, and dropping it is now a partial revert.** T031 is a
  human judgment with a stated failure branch — more than two findings a reader
  calls wrong and the check does not ship. As a separate PR that is a decline.
  Inside this PR it is `git revert` of the T026–T032 commits before merge, which
  is why those tasks are kept on their own commits rather than squashed into the
  module work.

**PR closes**: `Closes #109`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #109 | T001–T040 | `[109] Human views are visual-first — the record leads with a drawing` | 1.5–2 days | PR #1 |

**Grouping pattern**: Single issue
**Rationale**: One PR closes exactly one issue, and #109 is already open and
already scoped to the whole feature — nothing to create.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Parallel | T001 ‖ T002 ‖ T003 | All read-only. T003 must be green before any edit, or every later verification is unreadable |
| 1 | Sequential | T004 → T005 → T006 | All three modify `wfctl/_arch.py` |
| 2 | Parallel | T007 ‖ T008 | Different test files, both against Wave 1 code |
| 3 | Sequential | T009 | Foundational merge gate — `pytest` on the two new files + `mypy` |
| 4 | Sequential | T010 → T011 | Same file, `tests/test_arch_accept_drawing.py`. Confirm failing before Wave 5 |
| 5 | Sequential | T012 → T013 → T014 → T015 | All `wfctl/_arch.py`. Module before console, every time |
| 6 | Sequential | T016 | `wfctl/cli.py` — the console, after the module owns the invariant |
| 7 | Sequential | T017 → T018 | T017 is a cold read with no assertion behind it; T018 is the US1 merge gate |
| 8 | Parallel | T019 ‖ T020 | Different test files |
| 9 | Parallel | T021 ‖ T022 ‖ T023 | Three different files — `_arch.py`, the template, the skill |
| 10 | Sequential | T024 → T025 | T024 installs with `uv run` and writes a record end to end; nothing automated reaches it |
| 11 | Sequential | T026 → T027 | Same file, `tests/test_arch_labels.py` |
| 12 | Sequential | T028 → T029 | Both `wfctl/_arch.py` |
| 13 | Sequential | T030 | Corpus test, same file as Wave 11 |
| 14 | Sequential | T031 → T032 | **The revert point.** T031 fails SC-004 → revert T026–T032 and merge without Phase 5 |
| 15 | Parallel | T033 ‖ T039 | The record amendment and the FR-013 test touch different files |
| 16 | Parallel | T034 ‖ T035 ‖ T036 | Three independent checks over a finished tree |
| 17 | Sequential | T037 → T038 → T040 | quickstart, then the review panel, then the whole-feature gate |

**Single-agent order** (recommended): T001 → T002 → … → T040, in `tasks.md` order.

---

## Agent Fanning Instructions

Single agent recommended, despite the L size. The parallelism above is real but
thin: every `‖` pair is either two test files or two documents, and the critical
path is `wfctl/_arch.py`, which ten tasks modify in sequence. Fanning agents at
Waves 2, 8, 9, 15 and 16 saves minutes and costs a merge conflict on the one file
that carries the feature.

The wave table earns its place as the **revert map** instead. Waves 11–14 are
Phase 5, and they are the tasks T031 can send back. Keep them on their own
commits so that revert is a clean one.

**Fan-in gate after every wave ending in a gate task** (3, 7, 10, 14, 17):
`uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/`
