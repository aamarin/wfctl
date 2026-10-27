# Specification Analysis Report: #627

Scanned `spec.md`, `plan.md`, and `tasks.md` after `/speckit.tasks`. The report reflects the state after remediation. Five findings were fixed in `tasks.md`, and one stands by the maintainer's choice.

The repository has no `.specify/memory/constitution.md`. The plan takes its gates from `AGENTS.md` and the accepted records, and the tasks carry each of them: the three `uv run` commands close every phase, T001 adds the release note, and T055 runs `wfctl verify` and `wfctl doctor`.

Design records: 3 listed in design.md
  docs/architecture/design/627-unreviewed-takes-coverage.md
  docs/architecture/design/627-review-note-line-per-event.md
  docs/architecture/design/627-guard-blocks-note-writes.md

All three are `proposed`, and no task reverses their Decision or Consequences sections.

## Findings

| ID | Category | Severity | Location(s) | Summary | Disposition |
| --- | --- | --- | --- | --- | --- |
| F1 | Inconsistency | HIGH | tasks.md T018, T019; spec.md FR-010a | T019 had `relay` pick the group whose latest run expects the id, and refuse only when both runs do. FR-010a says `relay` exits 1 naming both groups whenever two share the letter. The tasks chose an approach the spec had already decided against. | Fixed: T019 refuses whenever two groups match, as FR-010a says, with the renamed-group example and a remedy naming the group the branch added. T018 tests that. |
| F2 | Inconsistency | MEDIUM | plan.md §Project Structure (`cli.py`); tasks.md T030 | The plan says `review check` uses the FR-010a group list. T030 keeps today's name check and loads no group list, so a broken trunk config can't stop a completed run from recording its note (PR-024). | Accepted: the maintainer chose to carry PR-024 in the tasks rather than edit the plan, since a plan edit needs another plan review. FR-010a still holds, because `review check` accepts every group on the list. T030 updates `contracts/cli.md`. |
| E1 | Coverage gap | MEDIUM | spec.md SC-003; tasks.md T032 | No task tested that a clean merge of `main` into a reviewed branch passes the check with no new review. | Fixed: T032 adds that case. |
| E2 | Coverage gap | LOW | spec.md FR-005; tasks.md T024 | No task checked that the state directory record is still written beside the note. | Fixed: T024 checks `last-reviewed.json` is still written. |
| E3 | Coverage gap | LOW | spec.md FR-017; tasks.md T035 | The workflow test didn't check the step that fetches the notes ref. | Fixed: T035 checks it. |
| F3 | Inconsistency | LOW | contracts/review-note.md reader rule 3; data-model.md rule 3 | The contract says a group line counts when "the current `wfctl.json`" lists the group. The data model and FR-015 say the trunk's or the head's. | Fixed: T015 updates the contract's rule 3 to match. |

## Coverage Summary

| Requirement | Has task? | Task IDs | Verification? |
| --- | --- | --- | --- |
| FR-001 | yes | T024, T030 | T024 |
| FR-002 | yes | T026, T029 | T026 |
| FR-003 | yes | T021, T027 | T021 |
| FR-004 | yes | T022, T024, T026, T028 - T030 | T022, T024, T026 |
| FR-005 | yes | T024, T030 | T024 |
| FR-005a | yes | T023, T028, T045, T046 | T023, T045 |
| FR-006 | yes | T022, T028, T046 | T022, T045 |
| FR-007 | yes | T044, T046 | T044 |
| FR-008 | yes | T044, T045, T046 | T044, T045 |
| FR-009 | yes | T002, T006 | T002 |
| FR-010 | yes | T012, T014, T016 | T012, T014 |
| FR-010a | yes | T013, T017 - T019, T030 | T013, T018 |
| FR-011 | yes | T010, T015 | T010 |
| FR-012 | yes | T002, T006 | T002 |
| FR-013 | yes | T032, T038 | T032 |
| FR-014 | yes | T032, T038 | T032 |
| FR-015 | yes | T004, T008, T034, T038 | T004, T034 |
| FR-015a | yes | T003, T005, T033, T038 | T003, T033 |
| FR-016 | yes | T032, T038 | T032 |
| FR-017 | yes | T035, T039 | T035 |
| FR-017a | yes | T035, T039 | T035 |
| FR-018 | yes | T036, T041 | T036 |
| FR-019 | yes | T048, T049 | T048 |
| FR-020 | yes | T048, T049 | T048 |
| FR-021 | yes | T048, T049 | T048 |
| FR-022 | yes | T048, T049 | T048 |
| FR-023 | yes | T039, T042 | T035 (no branch exception), T037 |
| FR-024 | yes | T037, T042 | T037 |
| FR-025 | yes | T052 | T052 |
| SC-001 | yes | T036, T041, after-merge quickstart steps 2 - 5 | manual, after merge |
| SC-002 | yes | T054 | T054 |
| SC-003 | yes | T032 | T032 |
| SC-004 | yes | T011 | T011 |
| SC-005 | yes | T048 | T048 |

## Unmapped tasks

None. T001 serves the release note gate, and T009, T020, T031, T043, T047, T050, and T055 are phase gates.

## Verification gaps

None. Every story has an Independent Test and a Verification block, and every implementation task names its test or command.

## Metrics

- Total requirements: 34 (29 FR, 5 SC)
- Total tasks: 55
- Coverage: 100%
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0

## Next Actions

No CRITICAL finding was found. One MEDIUM finding stands, F2, and it was accepted rather than fixed. It records the maintainer's choice to carry PR-024 in the tasks instead of editing the plan, and it needs no action before `/speckit.decompose`.
