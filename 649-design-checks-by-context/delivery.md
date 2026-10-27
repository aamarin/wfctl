# Delivery Plan: The design checks match records to the contexts a branch changes (649)

**Feature**: `649-design-checks-by-context` | **Date**: 2026-10-26
**Source**: `tasks.md` in this feature folder (62 tasks)
**Parent issue**: #649

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR 1 | T005 to T011, T043 to T047, T054 to T057 | `wfctl/_contexts.py` (created), `wfctl/_arch.py`, `wfctl/cli.py`, `docs/architecture/domain/wfctl.md`, five skill folders, `tests/test_contexts.py` (created), `tests/test_arch_records.py`, `tests/test_remaining_commands.py` (modified) | M | #652 decided before T008, and the checks green |
| PR 2 | T001 to T004, T012 to T042, T058 | `wfctl/_design_exceptions.py`, `_contexts.py`, `_evidence.py`, `_pipeline.py`, `_record_gate.py`, `cli.py`, `.github/pull_request_template.md`, `opening-a-change`, four skill folders, eight test files (modified) | L | #635 and PR 1 merged, #653 decided before T032 and T033, and the checks green |
| PR 3 | T048 to T053, T059 to T062 | `wfctl/_evidence.py`, three skill folders, `docs/architecture/design/design-exceptions-module.md`, `tests/test_software_design_pass.py`, `tests/test_step_none.py` (modified) | M | #648 and PR 2 merged, and the definition of done green |

**Rationale**: Multiple PRs. The feature touches about 30 files and splits along its two dependencies. PR 1 needs neither #635 nor #648 and changes no check's behavior. PR 2 extends #635's code, and PR 3 extends #648's. The user chose this split on 2026-10-26.

**PR closes**: PR 1 `Closes #655`, PR 2 `Closes #656`, PR 3 `Closes #657`.

PR 3 is the final PR, so its description also carries `Closes #649` once all three have merged.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #655 (Issue A) | T005-T011, T043-T047, T054-T057 | `[649] Name the contexts on the domain page and check governs in doctor` | M | PR 1 |
| #656 (Issue B) | T001-T004, T012-T042, T058 | `[649] The architecture check matches records to the branch's contexts` | L | PR 2 |
| #657 (Issue C) | T048-T053, T059-T062 | `[649] The software design check matches records to the branch's contexts` | M | PR 3 |

**Grouping pattern**: Hierarchical
**Rationale**: Each PR merges on its own and waits on a different dependency, so each gets one child issue under #649, which stays open until PR 3 merges.

### Getting this spec into a sub-issue worktree

Run `wfctl feature-paths` in the sub-issue worktree and read `FEATURE_DIR`. This repo records a spec root outside the working tree, so the #649 spec dir is already at a stable absolute path every worktree can read, and there is nothing to move.

`resolve_spec_dir` finds it by scanning the spec root for a `delivery.md` whose Issue Grouping Map names the branch's issue key, and `speckit-orchestrate` takes that row's `Tasks` column as the sub-issue's range. Name each worktree for its child issue, such as `workmux add 655-context-names --base main`.

### Release notes

`tasks.md` has one release-note task, T004, written for #649. The release-note check reads the branch's own issue, so each PR commits its own note instead:

1. PR 1: `changes/655.addition.md`, since the doctor finding and the name list are new and change no existing behavior.
2. PR 2: `changes/656.change.md`, with T004's content, since a branch that passes the architecture check today can pause after it ships.
3. PR 3: `changes/657.change.md`, since the same is true of the software design check.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | #652 decided | Decides where `split_names` lives (T008) and whether `context_gap` gathers both levels (T017) |
| 1 | Parallel | T005 ‖ T006 → T007 | T006 and T007 share `tests/test_contexts.py` |
| 2 | Sequential | T008 → T009 → T010 → T011 | Phase 2 merge gate |
| 3 | Parallel | T043 ‖ T044 ‖ T054 ‖ T055 ‖ T056 ‖ T057 | Different files |
| 4 | Sequential | T045 → T046 → T047 | PR 1 ready |
| 5 | Sequential | #635 merged, PR 1 merged, #653 decided → T012 | Rebase. A `plan.md` edit needs a new plan review |
| 6 | Parallel | T001 ‖ T002 ‖ T003 ‖ T004 ‖ T013 ‖ T015 | Different files |
| 7 | Sequential | T014 → T016 → T017 → T018 → T019 | Phase 3 merge gate |
| 8 | Sequential | T020 → T021 → T022 | US1 |
| 9 | Parallel | T023 ‖ T024 ‖ T025 ‖ T026 ‖ T027 ‖ T028 ‖ T037 ‖ T040 | Each in its own test file, except T023, T037, and T040, which share `test_design_gate_drawing.py` and run one after the other |
| 10 | Sequential | T029 → T030 → T031 → T032 → T033 → T034 → T035 → T036 | Four of these edit `cli.py` |
| 11 | Sequential | T038 → T039 → T041 → T042 → T058 | PR 2 ready |
| 12 | Sequential | #648 merged, PR 2 merged → T048 | Rebase |
| 13 | Sequential | T049 → T050 → T051 → T052 → T053 | US6 |
| 14 | Sequential | T059 → T060 → T061 → T062 | PR 3 ready |

**Single-agent order**: one agent per PR, in its own worktree. Inside each PR, follow the wave order above.

---

## Agent Fanning Instructions

Single agent per PR. The parallel waves are short test-writing passes, and most implementation tasks in PR 2 edit `cli.py` or `_evidence.py`, so fanning out would mostly produce merge conflicts. Each PR's fan-in gate is `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy`.
