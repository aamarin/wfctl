## Specification Analysis Report

This is the report after remediation. All three findings were fixed in `tasks.md` during this run.

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| C1 | Underspecification | MEDIUM | tasks.md § Dependencies; phases 4–6 | The tasks didn't say whether the CLI change (phase 4) and the skill changes (phase 6) land together. The level-3 record requires the same commit, and the per-phase "merge gate" wording could be read as separate merges. | **Fixed**: the Dependencies section now says phases 4–6 land in one commit, quoting the record. |
| E1 | Coverage gap | MEDIUM | tasks.md T029, T035 | T035 removes `Bash(wfctl notify*)` from `speckit.decompose.md`, and `test_decompose_allows_the_commands_its_notify_gate_needs` asserts that entry is there. No task updated the test. | **Fixed**: T029 now rewrites that test to require `wfctl report-block`. |
| E2 | Coverage gap | LOW | spec.md Edge Cases; tasks.md T020 | The edge case "a leftover local grant file changes nothing" had no verification. | **Fixed**: T020 adds a case with a leftover `notify.json`. |

**Coverage Summary Table:**

| Requirement Key | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | yes | T002, T003 | T004 | trunk included |
| FR-002 | yes | T021, T024 | T020 | no tracker call |
| FR-003 | yes | T024, T025 | Phase 5 grep, T020 | |
| FR-004 | yes | T011 | T006 | |
| FR-005 | yes | T025 | Phase 5 grep | `labels` verb untouched |
| FR-006 | yes | T011 | T006 | lifted-hold line |
| FR-007 | yes | T011 | T006, T007 | |
| FR-008 | yes | T012 | T008, T009 | old `block-cleared` |
| FR-009 | yes | T013 | T009 | close in, start/stop out |
| FR-010 | yes | T014 | T010 | |
| FR-011 | yes | T022, T023 | T017, T019 | |
| FR-012 | yes | T021 | T020 | |
| FR-013 | yes | T021 | T020 | wording in research R1 |
| FR-014 | yes | T030, T031, T033–T035 | T029, T038 | |
| FR-015 | yes | T030, T031, T033 | T038 manual read | |
| FR-016 | yes | T032 | T029 | |
| FR-017 | yes | T036, T037 | T039 | |
| FR-018 | yes | T040 | `wfctl arch check` | |
| SC-001 | yes | T002 | T004 | |
| SC-002 | yes | T013 | T009 | |
| SC-003 | yes | T039 | grep | |
| SC-004 | yes | T021 | T020 | |
| SC-005 | yes | T022, T023 | T019 | |

**Constitution Alignment Issues:** none. There is no `.specify/memory/constitution.md`. The plan's gates come from `AGENTS.md` and the accepted records, and that substitution is noted in Complexity Tracking. Checked against `pipeline-state-is-one-payload`, `a-rule-is-expressed-as-a-check`, `vendor-upstream-skills`, `session-state-is-re-derived` and `wfctl-runs-the-verification`, with no conflict.

**Unmapped Tasks:** T001 (baseline) and T041, T042 (final validation) are validation-only by design.

**Verification Gaps:** none after remediation. Every story has an Independent Test and a Verification block, and every implementation task names a verification path.

**Design records:** 2 listed in design.md, both read. No task reverses the Decision or Consequences of either.

**Metrics:**

- Total Requirements: 18 FR + 5 SC = 23
- Total Tasks: 42
- Coverage %: 100% (23/23)
- Ambiguity Count: 0
- Duplication Count: 0
- Critical Issues Count: 0

**Next Actions:** no CRITICAL or HIGH finding stands. Every finding was fixed in this run, and nothing was filed. Proceed to `/speckit.decompose`.
