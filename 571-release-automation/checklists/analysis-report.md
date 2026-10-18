# Specification Analysis Report: release automation

Run on 2026-10-16 over `spec.md`, `plan.md`, and `tasks.md`. This report is
written after remediation, so every finding below carries what was done about
it. The repository has no `.specify/memory/constitution.md`. Pass D checks
against the accepted records `wfctl arch context` prints and AGENTS.md, as
`plan.md` §Constitution Check does.

Design records: 2 listed in design.md

- docs/architecture/change-carries-release-note.md
- docs/architecture/design/571-towncrier-builds-release-notes.md

## Findings

| ID | Category | Severity | Location(s) | Summary | Outcome |
| --- | --- | --- | --- | --- | --- |
| E1 | Coverage | MEDIUM | spec.md User Story 3 scenarios 3, 4; tasks.md T034 | No task verified a tag present with its release missing, or a release commit carrying the wrong version. | Fixed: T034 now checks four cases, these two included. |
| E2 | Coverage | MEDIUM | spec.md FR-013; tasks.md T024 | No test asserted that the release script never pushes `main`. | Fixed: T024 asserts `origin`'s `main` is unchanged after a run. |
| E3 | Coverage | LOW | spec.md FR-007; tasks.md T008 | The failure message's example command was not asserted by any test. | Fixed: T008 asserts the `uv run towncrier create` example. |
| F1 | Inconsistency | LOW | plan.md §Structure Decision; tasks.md T016 | The plan commits `571.none.md` and settles the category at review, while T016 asked Andre before committing. | Fixed: T016 follows the plan. |
| C1 | Underspecification | LOW | tasks.md T041; plan.md §Source Code | `tests/test_ruleset.py` was in the tasks and missing from the plan's file list. | Fixed: the Notes in `tasks.md` say why it is added, and `plan.md` is left alone so the plan review stays current. |
| F2 | Inconsistency | LOW | tasks.md T036 | The verification step for the drift test was worded so it could be read backwards. | Fixed: reworded to say which test fails, and when. |

## Coverage summary

| Requirement | Has task? | Task IDs | Verification? |
| --- | --- | --- | --- |
| FR-001 | yes | T008, T014 | T008 |
| FR-002 | yes | T008, T014 | T008 |
| FR-003 | yes | T009, T013 | T009 |
| FR-003a | yes | T009, T013 | T009 |
| FR-004 | yes | T010, T014 | T010 |
| FR-005 | yes | T003, T005, T012 | T005, T011 |
| FR-006 | yes | T015, T017 | `wfctl check config`, the pull request's job |
| FR-007 | yes | T008, T014 | T008 |
| FR-008 | yes | T020, T025 | T020 |
| FR-009 | yes | T021, T025 | T021 |
| FR-010 | yes | T020, T026 | T020 |
| FR-011 | yes | T023, T027 | T023 |
| FR-012 | yes | T024, T028 | T024 |
| FR-013 | yes | T024, T028 | T024 |
| FR-014 | yes | T022, T026 | T022 |
| FR-015 | yes | T023, T027, T030 | T023, T030 |
| FR-016 | yes | T032, T034 | T034, first release |
| FR-017 | yes | T002 | `uv lock --check` |
| FR-018 | yes | T033, T036, T037, T038, T039 | T036, reading |
| FR-019 | yes | T016 | `wfctl verify` |
| FR-020 | yes | T039, T041, T042, T044 | T041, read-back after merge |
| SC-003 | yes | T002, T028 | the required `lint` check on the release pull request |
| SC-005 | yes | T037 | `git diff origin/main -- wfctl/` |

SC-001, SC-002, and SC-004 are outcomes measured on releases after merge, and
are left out of the count.

## Pass G: design-record contradiction

Both records were read in their Decision and Consequences sections, and both
are `accepted`. No task does the opposite of either. The tasks build the check
as this repository's own script rather than `towncrier check`, build the draft
from a copy without the `none` notes, delete every note in the release commit,
write no `CHANGELOG.md`, send the release through its own pull request, and
leave applying the ruleset to Andre after merge.

## Metrics

- Requirements: 21 functional, 2 buildable success criteria
- Tasks: 48
- Coverage: 100%
- Ambiguity: 0
- Duplication: 0
- Critical: 0

## Next actions

No finding stands, so the next step is `/speckit.decompose`.
