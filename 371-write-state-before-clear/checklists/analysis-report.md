## Specification Analysis Report

Post-remediation. Run unattended; every finding below was applied to the artifacts in this run.

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| A1 | Duplication | LOW | spec.md FR-004, FR-010 | FR-010 ("never resend … whether the earlier send succeeded or failed") restated FR-004's once-per-session rule for the success path. | **Fixed**: FR-004 owns the success path (including after a hold); FR-010 now covers only retries of a failed or not-taken send. |
| C1 | Underspecification | MEDIUM | tasks.md T013 | The hook CLI test would spawn the worker from pytest's own process; the worker waits for its parent pid to exit, so the in-process test waits out the 10 s cap and asserts nothing about ordering. | **Fixed**: T013 runs the hook as a child process and asserts the child exits before the stub's send timestamp. |
| C2 | Underspecification | LOW | tasks.md T001, T034 | "implementation notes" named a destination no artifact defines. | **Fixed**: T001 only confirms the baseline; T034 records the median in the PR description's testing section. |
| F1 | Inconsistency | LOW | spec.md US2 scenario 3; contracts/hook-session-restart.md | Skip message placeholder was `<worktree path>` in the spec and `<repo root>` in the contract. | **Fixed**: spec now reads `<repo root>`, matching the contract. |

**Coverage Summary Table:**

| Requirement Key | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | Yes | T019, T020 | Yes | T013, T005 |
| FR-002 | Yes | T015, T026 | Yes | T011, T024 |
| FR-003 | Yes | T015 | Yes | T011 |
| FR-004 | Yes | T015, T026 | Yes | T011, T024 |
| FR-005 | Yes | T017, T018 | Yes | T012, T013 |
| FR-006 | Yes | T017 | Yes | T012 |
| FR-007 | Yes | T018 | Yes | T013 |
| FR-008 | Yes | T026, T027 | Yes | T024, T025 |
| FR-009 | Yes | T026, T027 | Yes | T024, T025 |
| FR-010 | Yes | T026 | Yes | T024 |
| FR-010a | Yes | T026 | Yes | T024 |
| FR-011 | Yes | T018, T019 | Yes | T013 |
| FR-012 | Yes | T017 | Yes | T012 |
| FR-013 | Yes | T008, T031 | Yes | T029 |
| FR-014 | Yes | T008, T031 | Yes | T029 |
| FR-015 | Yes | T031 | Yes | T030 |
| FR-016 | Yes | T021 | Yes | T014, T022 |
| FR-017 | Yes | T021 | Yes | T014 |
| FR-018 | Yes | T021 | Yes | T014 |
| FR-019 | Yes | T004 | Yes | T003 |
| FR-020 | Yes | T004, T006 | Yes | T003, T005 |
| FR-021 | Yes | T006 | Yes | T005 |
| FR-022 | Yes | T006, T020 | Yes | T005 |
| SC-001 | Yes | T035 | Yes | live |
| SC-002 | Yes | T015, T026 | Yes | T011, T024 |
| SC-003 | Yes | T026, T027 | Yes | T024, T025 |
| SC-004 | Yes | T034 | Yes | timing |
| SC-005 | Yes | T006 | Yes | T005 |
| SC-006 | Yes | T031 | Yes | T029, T035 |

**Constitution Alignment Issues:** None. No `.specify/memory/constitution.md`; plan substitutes gates from `AGENTS.md` and accepted records and records the substitution in Complexity Tracking. All substituted gates hold against tasks.

**Design-record contradiction (pass G):** 5 records read (all `proposed`), none reversed. Closest reading considered: `371-the-session-restart-sends-from-a-detached-worker` Decision names "`hook session-restart` in `cli.py` as the thin caller"; T019 adds an `_entry.py` fast path beside the `hook_app` registration. The decision function stays pure in `_restart.py` and `cli.py` still registers and dispatches the command, so this adds a second thin caller rather than moving the decision — not a reversal.

**Unmapped Tasks:** T001, T002, T010, T023, T028, T032, T036 (setup and merge gates); T033 (README).

**Verification Gaps:** None — every implementation task names a test file or command.

**Metrics:**

- Total Requirements: 29 (23 FR, 6 SC)
- Total Tasks: 36
- Coverage %: 100%
- Ambiguity Count: 0
- Duplication Count: 1 (fixed)
- Critical Issues Count: 0

**Next Actions:** No finding stands. Proceed to `/speckit.decompose`.
