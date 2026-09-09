# Delivery Plan: one predicate signature (314)

**Feature**: `314-one-predicate-signature` | **Date**: 2026-09-09
**Source**: `<spec_root>/314-one-predicate-signature/tasks.md` (33 tasks)
**Parent issue**: #314

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR A | T001–T033 | `wfctl/_predicates.py` (created), `wfctl/_pipeline.py` (modified), `wfctl/cli.py` (modified), `tests/test_predicates.py` (created), `tests/test_pipeline_state_names.py` (modified), `tests/test_pipeline_commands.py` (modified) | M (6 files) | `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor` all green, and T022's render diff empty |

**Rationale**: Single PR. Applying the four boundary signals, three say bundle
and none says split.

- **File conflict risk** — every task edits `wfctl/_pipeline.py` or the module
  carved out of it. Two PRs would edit the same file concurrently, which is the
  case the framework says to split *only* when the edits cannot be sequenced.
  They can be, so this is a bundle signal rather than a split one.
- **Reviewability** — the change's whole claim is that no step reaches a
  different verdict, and T022's render diff is what evidences it. A reviewer
  handed half the restructure cannot check that claim; the diff is only
  meaningful against the finished state.
- **Mergeable increment** — Phases 1–3 would merge green, so this signal is
  neutral rather than blocking. It is outweighed by the one above.
- **Size** — 6 files is M, which the sizing table sends to a single PR and a
  single issue without discussion.

The 33 tasks make this look larger than it is: most are one extraction each, and
Phase 1 and Phase 6 are capture-and-verify rather than edits.

**PR closes**: `Closes #314`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #314 | T001–T033 | `[314] The eight predicates share no signature, and the third shape the epic was waiting for has arrived` | ~1 day | PR A |

**Grouping pattern**: Single issue
**Rationale**: #314 already scopes exactly this work and rules out the four
neighbouring changes by name; splitting it would create sub-issues whose only
boundary is which phase of one refactor they cover.

**No issues are created by this plan.** The one row names an issue that already
exists, so nothing here reaches anyone outside the repo — which is why this step
completes on a branch where `wfctl status` reports "will not notify anyone".

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 → T003 | Baseline capture. No edits. Nothing below is verifiable without it |
| 1 | Sequential | T004 → T005 → T006 → T007 → T008 → T009 → T010 | Foundational. Each moves code the next one needs; ordering is real, not conservatism |
| 2 | Parallel | T011 ‖ T012 ‖ T013 ‖ T014 ‖ T015 | Five independent extractions into one new file. Different functions, no shared state |
| 3 | Sequential | T016 → T017 → T018 → T019 → T020 | T016 must land byte-identical before T017 re-types the table, so T021's change stays attributable |
| 4 | Parallel | T021 ‖ T024, then T022 → T023 → T025 | T021 and T024 touch different files; T022's diff needs T021 finished |
| 5 | Sequential | T026 → T027 → T028 | The `State` widening and the deliberate-failure check |
| 6 | Parallel | T029 ‖ T030, then T031 → T032 → T033 | Polish, review panel, definition of done |

**Single-agent order** (recommended): T001 → T033 in numeric order. The parallel
waves above are marked for correctness, not because this feature needs fanning.

---

## Agent Fanning Instructions

**Single agent recommended.** Six files, one of which is a straight extraction
from another, and the verification is a whole-change diff rather than a per-task
one. Wave 2's five extractions are genuinely independent, but they are five short
functions moving into one new file — coordinating five agents over one file costs
more than it saves, and the fan-in gate would be the same `uv run pytest -q` a
single agent runs anyway.

The wave table is kept for the ordering constraints it records, which bind a
single agent just as much: T016 before T017, and T021 before T022.

**Fan-in gate after every wave:** `uv run pytest -q && uv run mypy wfctl/`
