# Specification Analysis Report

Analyzed `spec.md`, `plan.md`, and `tasks.md` for #407. The repository has no
`.specify/memory/constitution.md`, so the constitution pass checked the gates
`plan.md` borrows from `AGENTS.md`. This report reflects the artifacts after
remediation.

| ID | Category | Severity | Location(s) | Summary | Recommendation | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | Coverage gap | MEDIUM | tasks.md T008; record `approval-mode-is-stored-intent` "Must let through" case 5 | No task tested that `start` with no flag leaves a mode that is on unchanged. SC-002 asks for all six "Must let through" cases. | Extend T008 | Fixed |
| E2 | Coverage gap | MEDIUM | spec.md Edge Cases, first bullet; tasks.md T002 | The edge case where the event is appended and the `mode.json` write fails had no test. Only a failed append was covered. | Extend T002 | Fixed |
| C1 | Underspecification | MEDIUM | spec.md Validation Strategy; plan.md Technical Context; tasks.md T034 | The plan's manual Claude Code prompt check was missing from the spec's Validation Strategy, and T034 deferred adding it to implement. | Add the check to spec.md now | Fixed |

## Coverage summary

| Requirement | Has task? | Task IDs | Verification? |
| --- | --- | --- | --- |
| FR-001 | Yes | T002, T004, T010, T012 | T002, T010 |
| FR-002 | Yes | T011, T012 | T011 |
| FR-003 | Yes | T003, T005, T020, T021 | T003, T020 |
| FR-004 | Yes | T010, T012 | T010 |
| FR-005 | Yes | T010, T012 | T010 |
| FR-006 | Yes | T010 | T010 |
| FR-007 | Yes | T002, T004 | T002 |
| FR-008 | Yes | T007 | T007 |
| FR-009 | Yes | T008 | T008 |
| FR-010 | Yes | T022, T023, T024, T025 | T022, T025 (manual) |
| FR-011 | Yes | T026, T027, T028 | T026, T028 |
| FR-012 | Yes | T029, T030, T031, T032 | T029, T032 |
| FR-013 | Yes | T029, T030 | T029 |
| FR-014 | Yes | T002, T004 | T002 |
| FR-015 | Yes | T014 - T019, T034 | T014, T015, T034 (manual) |
| SC-001 | Yes | T010 | T010 |
| SC-002 | Yes | T008, T010, T011, T022 | each of the 11 cases traced to a test |
| SC-003 | Yes | T020 | T020 |
| SC-004 | Yes | T026 | T026 |
| SC-005 | Yes | T029 | T029 |

SC-002 trace. "Must keep catching": 1 is T010 scenario 4, 2 is T010 scenario 5,
3 and 4 are T022, and 5 is T008. "Must let through": 1 is T011, 2 is T010
scenario 1, 3 is T010 scenario 6, 4 is T010 scenario 3, 5 is T008, and 6 is
T022 and T025.

## Constitution alignment

No constitution exists. Each gate in the plan's Constitution Check has tasks:
the three `uv run` commands (T035), `install-skills` for changes under
`wfctl/agents/` (T032), the release note (T001), and the import check (T006,
T027).

## Unmapped tasks

None. T001 and T033 - T037 are cross-cutting work the definition of done and
the plan require.

## Verification gaps

None after remediation. Every implementation task names a test, a command, or
a manual check.

## Design records

Design records: none — design.md records no level-3 decision.

## Metrics

- Total requirements: 15 functional, 5 success criteria
- Total tasks: 37
- Coverage: 100% of requirements have at least one task
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0

## Next actions

No CRITICAL or HIGH finding stands. All three MEDIUM findings were fixed in
`spec.md` and `tasks.md`, so `/speckit.decompose` can run.

Remediation: settled
