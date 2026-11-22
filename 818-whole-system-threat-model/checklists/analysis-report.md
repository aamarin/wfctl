# Specification Analysis Report

Scope: `spec.md`, `plan.md`, `tasks.md`, read after remediation. Constitution: absent at `.specify/memory/constitution.md`. Design records: 1 listed in `design.md`, `docs/architecture/design/818-threat-baseline-layers-over-upstream.md` (status `proposed`).

| ID | Category | Severity | Location(s) | Summary | Disposition |
| --- | --- | --- | --- | --- | --- |
| E1 | Coverage gaps | MEDIUM | spec.md FR-013, edge case "committed but empty"; tasks.md T018 | No test that an empty committed `THREAT_MODEL.md` reads done | Fixed: T018 adds the case |
| E2 | Coverage gaps | MEDIUM | spec.md FR-014; tasks.md T018, T024 | T024 pins `needs_person` false, but no state test runs with auto-approve on | Fixed: T018 adds the missing-file case with auto-approve on |
| F1 | Inconsistency | MEDIUM | tasks.md T019, T021; plan.md cites research R6; data-model.md | Tasks hold the pass with no trunk, while research R6 row 4 and data-model.md say skipped with `DRAWINGS_UNCHECKED` | Fixed: T021 states it replaces that row and why, citing the spec's git-failure edge case |
| F2 | Inconsistency | LOW | tasks.md T030; plan.md cites research R2 | T030 gives Claude upstream's own helper path, while research R2 says the relative path | Fixed: T030 states it replaces R2 on Claude and still meets FR-005a |
| E3 | Coverage gaps (unmapped task) | LOW | tasks.md T031 | T031 added a skill line about public repositories that no requirement asks for, and it sat uneasily with FR-007a's unattended commit | Fixed: T031 removed; the question it carried is filed as #852 |

## Coverage summary

| Requirement | Has task? | Task IDs | Verification? |
| --- | --- | --- | --- |
| FR-001 | yes | T001, T004, T005 | T005, T009, T010 |
| FR-002 | yes | T012, T015 | T012, T034 |
| FR-003 | yes | T013, T016 | T013 |
| FR-004 | yes | T006 | T009 |
| FR-005 | yes | T028, T030 | T028 |
| FR-005a | yes | T028, T030 | T028, T034 |
| FR-006 | yes | T028, T030 | T028 |
| FR-007 | yes | T028, T030 | T028 |
| FR-007a | yes | T029, T030 | T029 |
| FR-007b | yes | T029, T032, T033 | T029, T033 |
| FR-008 | yes | T023, T024 | T018, T024 |
| FR-009 | yes | T018, T021 | T018 |
| FR-010 | yes | T018, T021 | T018 |
| FR-011 | yes | T018, T021 | T018 |
| FR-012 | yes | T020, T025 | T020, T025 |
| FR-012a | yes | T020, T021 | T020 |
| FR-013 | yes | T018, T021 | T018 |
| FR-014 | yes | T018, T024 | T018, T024 |
| FR-015 | yes | T036, T037 | T036, T038 |
| FR-015a | yes | T029, T030 | T029 |
| FR-016 | yes | T014 | T014 |
| FR-017 | yes | T008 | T008 |
| FR-018 | yes | T007 | T007 |
| FR-019 | yes | T040 | T040, T042 |
| SC-001 | yes | T018–T021 | T018–T020 |
| SC-002 | yes | T018, T024 | T018 |
| SC-003 | yes | T030, T034 | T034 |
| SC-004 | yes | T037, T038 | T038 |
| SC-005 | yes | T040 | T040 |

**Constitution alignment issues**: none checked; no constitution exists in this repository.

**Unmapped tasks**: none after E3. T043 to T046 are cross-cutting validation.

**Verification gaps**: none. Every story has an Independent Test and a Verification block, and every implementation task names a test or check.

**Design-record contradiction (pass G)**: 1 record read. Its Decision has `threat-baseline` hold wfctl's three additions, the pass and `design-levels` name `/threat-baseline`, and the skill mirrors beside `threat-model` and `_lib`. T015, T023, T030, and T037 carry exactly that. No task reverses it.

## Metrics

- Total requirements: 24 functional, 5 success criteria
- Total tasks: 45 (T001 to T046, T031 removed)
- Coverage: 100% of requirements have at least one task
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0

## Next actions

No CRITICAL or HIGH finding stands. All five findings were fixed in `tasks.md`, so the feature can go on to `/speckit.decompose`. Research R2 and R6 row 4, and the no-trunk row in `data-model.md`, still describe the earlier choices. `tasks.md` names where it replaces them, so an implementer reading T021 and T030 gets the current answer.

- **Public-repository disclosure of `THREAT_MODEL.md`** (E3, from plan review PR-011) — Filed as #852.

Remediation: settled
