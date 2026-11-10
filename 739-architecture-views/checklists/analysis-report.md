# Specification Analysis Report

Feature: `739-architecture-views` (#739, with #738). Inputs: `spec.md`, `plan.md`, and `tasks.md`, all present and read. The repository has no `.specify/memory/constitution.md`, so constitution alignment used the gates `plan.md §Constitution Check` takes from `AGENTS.md` and the accepted records.

Design records: none, since `design.md` records no level-3 decision.

This report reflects the artifacts after remediation. Three findings were fixed in `tasks.md` during this run, and one stands.

## Findings

| ID | Category | Severity | Location(s) | Summary | Status |
| --- | --- | --- | --- | --- | --- |
| F1 | Inconsistency | MEDIUM | tasks.md T010, T032 | T010 (User Story 1) read `covers` "with the same bracket parsing `Record.kinds` uses", but `Record.kinds` is added by T032 in User Story 3, which runs independently. | Fixed: both tasks now name one bracket-list helper beside `split_names`, added by whichever lands first. |
| B1 | Ambiguity | MEDIUM | tasks.md T020, T022 | The tasks didn't say which `unchecked` reason wins for an out-of-tree view with no `covers` line, while `plan.md §Validation Strategy` says every present view under that root prints `not in this repository's history`. | Fixed: T020 tests that case, and T022 checks the history reason first for an out-of-tree root. |
| E1 | Coverage gap | LOW | spec.md FR-007; tasks.md T025 | FR-007 says no command, step, or PR is refused for a view, and only the exit code of `arch context` was tested. | Fixed: T025 now checks that only `wfctl/arch/` and `arch_context_cmd` use `_views`. |
| B2 | Ambiguity | LOW | spec.md FR-006a | For an in-tree view with no `covers` line in a directory that isn't a git repository, nothing says which `unchecked` reason prints. Plan review PR-015 reports the same gap in `data-model.md`. | Accepted: choosing the order for this case is a decision the three artifacts haven't made, and its fix belongs in `data-model.md`, which this step doesn't edit. |

## Coverage summary

| Requirement | Has task? | Task IDs | Verification? |
| --- | --- | --- | --- |
| FR-001 | yes | T007, T010 | T007 |
| FR-002 | yes | T007, T010 | T007 |
| FR-003 | yes | T011, T012, T013 | T008, T015 |
| FR-003a | yes | T012, T013 | T008 |
| FR-003b | yes | T012, T013, T045 | T008 |
| FR-003c | yes | T011, T012, T013 | T008 |
| FR-004 | yes | T008 | T008 |
| FR-005 | yes | T021, T023 | T016, T017 |
| FR-006 | yes | T021, T023 | T017 |
| FR-006a | yes | T022 | T018, T019, T020 |
| FR-007 | yes | T023 | T017, T025 |
| FR-008 | yes | T004 | T003 |
| FR-009 | yes | T032 | T027 |
| FR-010 | yes | T033 | T028 |
| FR-011 | yes | T033, T034 | T028 |
| FR-012 | yes | T034 | T029 |
| FR-013 | yes | T035 | T029 |
| FR-014 | yes | T034 | T029 |
| FR-015 | yes | T036 | T030 |
| FR-016 | yes | T042 | T041 |
| FR-017 | yes | T037, T038 | T040 |
| FR-017a | yes | T037 | T031 |
| FR-018 | yes | T044, T045 | T044, T045 |
| FR-019 | yes | T039 | T039 |
| FR-020 | yes | T001, T002 | T049 |
| SC-001 | yes | T015, T044, T045 | quickstart §1 |
| SC-002 | yes | T017, T023 | T017, quickstart §2 |
| SC-003 | yes | T029, T035 | quickstart §3 |
| SC-004 | yes | T026 | T026 |
| SC-005 | yes | T042 | T041 |
| SC-006 | yes | T022 | T018 |

**Constitution alignment issues:** none. Every gate in `plan.md §Constitution Check` has a task: release notes (T001, T002), the import check (T005, T015, T025), install-skills and an exercise for each skill change (T015, T024, T038), and `wfctl verify` (T049).

**Unmapped tasks:** none. Setup, checkpoint, and polish tasks each serve a requirement or a gate.

**Verification gaps:** none. Every implementation task names a test, a command, or a manual check.

## Metrics

- Total requirements: 25 functional requirements and 6 success criteria
- Total tasks: 49
- Coverage: 100% (31 of 31 have at least one task)
- Ambiguity count: 2 (1 fixed)
- Duplication count: 0
- Critical issues: 0

## Next actions

No CRITICAL or HIGH finding stands. One LOW stands, B2, and it wasn't filed. It's the same gap as plan review PR-015, and the user decides whether to fix it in `data-model.md` before implementing or file it. `/speckit.decompose` can run.
