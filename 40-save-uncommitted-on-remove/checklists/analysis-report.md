# Specification Analysis Report

**Feature**: Save unsaved work when a worktree is removed (#40)
**Date**: 2026-10-15
**Artifacts**: spec.md, plan.md, tasks.md, all present and read. There is no constitution at `.specify/memory/constitution.md`, so pass D checked against the gates plan.md takes from `AGENTS.md` and the in-force records.
**Design records**: 1 listed in design.md. `docs/architecture/design/40-archive-is-a-command-group.md`, status `proposed`.

This report describes the artifacts after remediation. Three findings were fixed in `tasks.md`, and six were filed as #600.

## Findings

| ID | Category | Severity | Location(s) | Summary | Disposition |
| --- | --- | --- | --- | --- | --- |
| G1 | Design-record contradiction | HIGH | tasks.md T019, T023, T028; record Decision | The `to_unsaved` outcome doesn't stop removal, while the record says any result for a spec dir inside the worktree that isn't a finished copy-out does | Filed, #600 item 1 |
| F1 | Inconsistency | HIGH | spec.md SC-004; plan.md via research R3; tasks.md T007, T009 | SC-004 promises a squash-merged branch is never stopped, and the merge check stops one once trunk has changed the same lines | Filed, #600 item 2 |
| F2 | Inconsistency | MEDIUM | plan.md Constitution Check; tasks.md T028 | The plan says only `StoreResult` decides whether a spec dir stops removal, and T028's first phase decides it from the copy-out plan | Filed, #600 item 3 |
| F3 | Inconsistency | MEDIUM | plan.md Source Code, Risks; tasks.md T023, T044 | `store(worktree, branch, overwrite)` differs from #359's `store(spec_dir, branch, repo_root)` | Filed, #600 item 4 |
| C1 | Underspecification | MEDIUM | spec.md FR-013, FR-015; tasks.md T013 | Nothing says what happens when `git ls-files --others` fails, and the two readings have opposite results | Filed, #600 item 5 |
| C2 | Underspecification | LOW | spec.md FR-016, FR-018; tasks.md T014, T039 | No rule covers overlap between `save_on_remove` folders, untracked files, and the spec dir | Filed, #600 item 6 |
| E1 | Coverage gap | MEDIUM | spec.md FR-033; tasks.md T026 | FR-033's second half, leaving earlier numbered archives in place, had no test | Fixed: T026 now tests it |
| E2 | Coverage gap | LOW | spec.md FR-013; tasks.md T006 | A failing `git status` warning had no test, though research R4 makes it an FR-013 case | Fixed: T006 now tests it |
| E3 | Coverage gap | MEDIUM | plan.md Source Code; tasks.md T032, T042 | The template comment, this repository's `.workmux.yaml` comment, and the `_archive._plan` inventory row describe the old hook and had no task | Fixed: T032 and T042 now cover them |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | yes | T028 | T026 | |
| FR-002 | yes | T028 | T026 | |
| FR-003 | yes | T028 | T026 | |
| FR-004 | yes | T029 | T026 | |
| FR-005 | yes | T029 | T026 | |
| FR-006 | yes | T032 | T027 | |
| FR-007 | yes | T032 | T027 | |
| FR-008 | yes | T031 | T026 | |
| FR-009 | yes | T008, T010 | T006 | |
| FR-010 | yes | T009, T010 | T007 | |
| FR-011 | yes | T009 | T007 | |
| FR-012 | yes | T009 | T007 | |
| FR-013 | yes | T008, T009 | T006, T007 | E2 fixed |
| FR-014 | yes | T004, T010 | T006 | The "no flag skips a stop" half is a negative requirement with no task to write |
| FR-015 | yes | T013, T014 | T012 | C1 filed |
| FR-016 | yes | T039 | T035 | |
| FR-017 | yes | T013, T039 | T035 | |
| FR-018 | yes | T013 | T012 | C2 filed |
| FR-019 | yes | T014 | T012 | |
| FR-019a | yes | T014 | T001, T012 | |
| FR-020 | yes | T014 | T012 | |
| FR-021 | yes | T014 | T012 | |
| FR-022 | yes | T014, T015 | T012 | |
| FR-023 | yes | T015, T016 | T012 | |
| FR-024 | yes | T021, T023 | T018 | |
| FR-025 | yes | T021 | T018 | |
| FR-026 | yes | T021, T023 | T018, T019 | |
| FR-027 | yes | T021, T024 | T018, T019 | |
| FR-028 | yes | T021, T023 | T018 | |
| FR-029 | yes | T023 | T019 | G1 filed |
| FR-030 | yes | T023, T024 | T019 | |
| FR-031 | yes | T023 | T019 | |
| FR-032 | yes | T023, T028 | T019, T026 | |
| FR-033 | yes | T030 | T026 | E1 fixed |
| FR-034 | yes | T037, T038 | T036 | |
| FR-035 | yes | T030 | T026 | |
| SC-001 | yes | T006 - T010, T047 | T006, T007, T047 | |
| SC-002 | yes | T014 | T012 | |
| SC-003 | yes | T039 | T035 | |
| SC-004 | yes | T009 | T007 | F1 filed |
| SC-005 | yes | T029, T032 | T026, T047 | |
| SC-006 | yes | T023 | T019 | |

## Constitution Alignment Issues

None. The repository has no constitution, and plan.md's gates from `AGENTS.md` and the in-force records are each carried by a task.

## Unmapped Tasks

None. T001 - T005 are setup and shared types, and T041 - T047 are documentation, the #359 merge check, and validation.

## Verification Gaps

None. Every story has an Independent Test and a Verification block, and every implementation task names a test or command.

## Metrics

- Total requirements: 36 functional requirements and 6 success criteria
- Total tasks: 47
- Coverage: 100% (36 of 36 functional requirements have at least one task)
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0

## Next Actions

No CRITICAL finding stands. Two HIGH findings stand, G1 and F1, along with three MEDIUM and one LOW, and all six were filed as #600 rather than fixed, because each needs a design choice. G1 also needs the proposed record accepted or revised, which only Andre can do. Settle #600 before `/speckit.implement` reaches T007, T009, T013, T023, or T028, since those tasks build what it decides.
