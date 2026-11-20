## Specification Analysis Report

Read after remediation. Artifacts: `spec.md`, `plan.md`, `tasks.md`, with `data-model.md`, `contracts/`, and `quickstart.md` as supporting context. No `.specify/memory/constitution.md` exists, so pass D checks the plan's substituted gates (the accepted architecture records and `AGENTS.md`).

| ID | Category | Severity | Location(s) | Summary | Recommendation | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | Coverage | MEDIUM | spec.md US1 acceptance 4; tasks.md T004 | No task tested a grandchild's peak counting toward its command | Add a grandchild test | Fixed in T004 |
| E2 | Coverage | MEDIUM | spec.md FR-003; tasks.md T009 | No task checked that output keeps streaming | Add a `capfd` check | Fixed in T009 |
| F1 | Inconsistency | MEDIUM | contracts/wfctl-timings.md rule 4, data-model.md validation 3, spec.md FR-014, tasks.md T028 | The contract and data model put a malformed span's branch on the no-span line, even beside a valid span; FR-014 and T028 don't | Say in tasks which rule wins | Fixed in tasks.md Notes |
| B1 | Ambiguity | LOW | tasks.md T004 | "close to 50 MB" had no tolerance | Use SC-002's 20% over a no-allocation baseline | Fixed in T004 |
| E3 | Coverage | LOW | spec.md FR-018; tasks.md T031 | No test that `wfctl timings` writes nothing | Assert the state folder is unchanged | Fixed in T031 |
| E4 | Coverage | LOW | spec.md FR-011; tasks.md T024 | No test that a linked worktree and the main checkout read the same logs | Add to the loader test | Fixed in T024 |
| E5 | Coverage | LOW | spec.md FR-013; tasks.md T027 | The open-now test didn't name the oldest-age figure | Name count and oldest age | Fixed in T027 |
| F2 | Inconsistency | LOW | plan.md Part 3 step 5; tasks.md T030 | The plan's "left out of that command's figures" reads as either per entry or per figure | Record T030's per-figure rule | Fixed in tasks.md Notes |

**Coverage Summary Table:**

| Requirement Key | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | Yes | T004, T009, T011, T013 | Yes | |
| FR-002 | Yes | T004, T011 | Yes | grandchild case added (E1) |
| FR-003 | Yes | T009, T011 | Yes | added (E2) |
| FR-004 | Yes | T005, T011 | Yes | |
| FR-005 | Yes | T009, T013 | Yes | |
| FR-006 | Yes | T006, T012 | Yes | |
| FR-007 | Yes | T016, T017, T022 | Yes | |
| FR-008 | Yes | T002, T003, T016 | Yes | |
| FR-009 | Yes | T018, T022 | Yes | |
| FR-010 | Yes | T019, T022 | Yes | |
| FR-011 | Yes | T024, T034 | Yes | added (E4) |
| FR-012 | Yes | T025, T036 | Yes | |
| FR-013 | Yes | T027, T035 | Yes | named (E5) |
| FR-014 | Yes | T028, T036 | Yes | |
| FR-015 | Yes | T029, T036, T037 | Yes | |
| FR-016 | Yes | T029 | Yes | |
| FR-017 | Yes | T029 | Yes | |
| FR-018 | Yes | T031 | Yes | added (E3) |
| FR-019 | Yes | T031 | Yes | |
| FR-020 | Yes | T037 | Yes | |
| FR-021 | Yes | T025, T028, T031 | Yes | |
| FR-022 | Yes | T038 | Yes | no flag is added |
| SC-001 | Yes | T041 | Manual | quickstart step 1 |
| SC-002 | Yes | T007, T008 | Yes | |
| SC-003 | Yes | T041 | Manual | quickstart step 3, run by the user |
| SC-004 | Yes | T033 | Yes | |

SC-005 is an outcome, not buildable work, so it has no row.

**Constitution Alignment Issues:** none. The substituted gates hold: no new dependency, new code in `wfctl/evidence/` behind the package, a release note (T001), and nothing stored by `wfctl timings`.

**Design record (pass G):** `docs/architecture/design/828-verify-measures-each-child.md` (proposed). Its Decision and Consequences ask for `Popen` plus `os.wait4`, one result per command, `returncode` set from the `wait4` status, an interrupt that kills and reaps, and a "largest process" label. T010 to T013 and T037 do each. No task reverses it.

**Unmapped Tasks:** none. T001, T040, T041, and T042 are setup and polish.

**Verification Gaps:** none. Every implementation task names its verifying test or command.

**Metrics:**

- Total requirements: 26 (22 FR, 4 buildable SC)
- Total tasks: 42
- Coverage: 100% before and after remediation (E1 to E5 sharpened existing coverage rather than covering a requirement with no task)
- Ambiguity count: 1
- Duplication count: 0
- Critical issues: 0

**Next Actions:** no finding stands, so the feature can go to `/speckit.decompose`. Implementation still waits for the user to accept or reject `worktree-span-read-from-git` and `828-verify-measures-each-child`.

Remediation: settled
