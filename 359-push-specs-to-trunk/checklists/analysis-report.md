# Specification Analysis Report

Feature: 359-push-specs-to-trunk. Run on 2026-10-15, unattended, after
`/speckit.tasks`. This report states the artifacts as they stand after
remediation. Each finding below was fixed by an edit to `tasks.md`, and the
Status column says so.

Design records: 3 listed in design.md
  docs/architecture/design/store-specs-implement-pass.md
  docs/architecture/design/store-specs-at-removal.md
  docs/architecture/design/store-specs-merges-before-push.md

## Findings

| ID | Category | Severity | Location(s) | Summary | Status |
| --- | --- | --- | --- | --- | --- |
| E1 | Coverage | MEDIUM | spec.md FR-008; tasks.md T011 | No task asserted the two-line success output or that the count's noun is "files". | Fixed: T011 asserts both. |
| B1 | Ambiguity | LOW | spec.md FR-008, US1 example | "Never 'specs'" read literally fails on the success line, which names `origin/specs-trunk`. | Fixed: T011 asserts the noun rather than the word's absence. |
| E2 | Coverage | MEDIUM | spec.md §Edge Cases; data-model.md `no_spec_dir`; tasks.md T017 | No spec dir, and a store on `main`, had no test. | Fixed: T017 tests `no_spec_dir` for both. |
| E3 | Coverage | MEDIUM | spec.md FR-016; tasks.md T029 | Only the pass was tested for making no network call. `check specs` was not. | Fixed: T029 asserts no fetch. |
| E4 | Coverage | LOW | spec.md US2 scenario 2; tasks.md T025 | A fully stored spec dir at removal had no test. | Fixed: T025 covers it. |
| F1 | Inconsistency | MEDIUM | spec.md FR-018; store-specs-implement-pass.md; tasks.md T018 | The spec and the record say a `skipped` reading carries "a reason". T018 says `reason` is always `None`. The same word means two things. | Fixed: T018 says the FR-018 reason is the `display` text, and that the payload's `reason` field is a different thing. |
| F2 | Inconsistency | LOW | plan.md §Project Structure, Implementation order step 6; tasks.md T023 | The plan says to regenerate the payload snapshot, and T023 says it must not change (PR-005). | Fixed: T023 says it supersedes the plan, and why the plan is left unedited. |
| F3 | Inconsistency | LOW | tasks.md §Parallel opportunities, §Within each story | US3 was listed as running beside US1, but both edit `wfctl/cli.py`, which the same section says forces them into sequence. | Fixed: only T029 runs beside US1, and T030 and T031 wait for T017. |
| F4 | Inconsistency | LOW | tasks.md T025, T026 | T025 edited `tests/test_archive_specs.py` before T026 checked whether #40 had moved those tests onto `hook worktree-remove`. | Fixed: T025 starts after T026's check. |

No task reverses a design record. All three records are `proposed`, and each
was compared against its Decision and Consequences sections.

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | yes | T011, T014 | yes | |
| FR-002 | yes | T011, T014 | yes | |
| FR-003 | yes | T011, T014 | yes | |
| FR-004 | yes | T014, T033 | yes | |
| FR-005 | yes | T014 | yes | |
| FR-006 | yes | T012, T014 | yes | |
| FR-007 | yes | T034, T039 | yes | |
| FR-008 | yes | T011, T017 | yes | E1 |
| FR-009 | yes | T011 | yes | |
| FR-010 | yes | T007, T008 | yes | |
| FR-011 | yes | T043, T046 | yes | |
| FR-012 | yes | T043, T045 | yes | |
| FR-013 | yes | T043, T046 | yes | |
| FR-014 | yes | T009, T018 | yes | |
| FR-015 | yes | T009 | yes | |
| FR-016 | yes | T013, T029 | yes | E3 |
| FR-017 | yes | T019 | yes | |
| FR-018 | yes | T013, T018, T044 | yes | F1 |
| FR-019 | yes | T022 | manual | read after T051, run in T053 |
| FR-020 | yes | T026, T027 | yes | |
| FR-021 | yes | T025, T027 | yes | |
| FR-022 | yes | T025, T027 | yes | |
| FR-023 | yes | T029, T030 | yes | |
| FR-024 | yes | T029, T030 | yes | |
| FR-025 | yes | T031 | yes | |
| FR-026 | yes | T048 | manual | read after T051 |
| FR-027 | yes | T038, T041 | yes | |
| SC-001 | yes | T013, T053 | yes | |
| SC-002 | yes | T025, T053 | yes | |
| SC-003 | yes | T025 | yes | |
| SC-004 | yes | T029, T053 | yes | |
| SC-005 | yes | T033 | yes | |
| SC-006 | yes | T050 | manual | |

## Constitution Alignment Issues

None. The repository has no `.specify/memory/constitution.md`. The plan
substitutes gates drawn from `AGENTS.md` and the accepted records, and records
that under Complexity Tracking. No task conflicts with those gates.

## Unmapped Tasks

None. The setup, validation and polish tasks (T001 to T003, T010, T024, T028,
T032, T042, T047, T049 to T053) support every story rather than one requirement.

## Verification Gaps

None after remediation.

## Metrics

- Total requirements: 33 (27 functional, 6 success criteria)
- Total tasks: 53
- Coverage: 100% (33 of 33 have at least one task)
- Ambiguity count: 1
- Duplication count: 0
- Critical issues count: 0

## Next Actions

No CRITICAL or HIGH finding stands, and every finding was fixed in `tasks.md`.
Proceed to `/speckit.decompose`.

Two plan-review findings remain open and wait on Andre: PR-006 (whether the
default `wfctl status` shows a `skipped` store-specs pass) and PR-024 (what
removal does when the spec store's checkout sits inside the code worktree).
`tasks.md` already records both as his call, so this report doesn't raise them
again.
