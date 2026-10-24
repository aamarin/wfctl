# Specification Analysis Report: #622

Written after remediation. All six findings were fixed in `spec.md` or
`tasks.md`, and `plan.md` was not edited, so the plan review stays valid.

Design records: 4 listed in design.md
  docs/architecture/design/622-review-records-in-state-dir.md
  docs/architecture/design/622-review-groups-list.md
  docs/architecture/design/622-blocked-reviewer-relays-report.md
  docs/architecture/design/622-review-check-in-worktree-guard.md

All four are `proposed`. Pass G compared every task against each record's
Decision and Consequences sections and found no reversal.

## Findings

| ID | Category | Severity | Location(s) | Summary | Status |
| --- | --- | --- | --- | --- | --- |
| F1 | Inconsistency | MEDIUM | spec.md FR-012; `622-review-check-in-worktree-guard.md` Decision item 3; research.md R4; T025.4 | The record, research, the plan's test list, and T025 refuse `gh pr merge --auto` every time. The spec's FRs didn't require it, so T025.4 traced to no requirement. | Fixed: FR-012 now requires the refusal, with the record's reason. |
| F2 | Inconsistency | MEDIUM | tasks.md T027.4; research.md R4 and R6 pattern 8 | T027.4 asserted the unlisted-word message for `grep "gh pr create\|gh pr merge"`. Under R4's rules the word after `gh` is `pr`, which is listed. The plain-verb rule fires, because the verb `create\|gh` holds a backslash, and the separator rule also fires on the second match. A correct implementation would fail the test as written. | Fixed: T027.4 asserts the plain-verb message, notes the separator rule, and keeps the unlisted-word message for the `rg` form, where it is right. |
| E1 | Coverage gap | MEDIUM | spec.md US6 scenario 2; design.md Key Assumptions item 3 | No task checked that a security reviewer on a branch with an earlier review keeps its findings inside the new commits. That is the one test of whether reviewers follow wfctl's note over the vendored `/security-review` file. | Fixed: T074 checks it at quickstart step 7, where the security group runs again over the fix commit. |
| E2 | Coverage gap | LOW | tasks.md T063; spec.md US6 Independent Test | T063 says the fresh-repository `install-skills` run needs Andre, but no task asked him for it. | Fixed: T074 asks Andre for it, alongside the sign-off step. |
| E3 | Coverage gap | LOW | spec.md Validation Strategy; tasks.md T040 | The Validation Strategy compares the timing run with the figures in the `_hook.py` docstring. T040 didn't. | Fixed: T040 makes the comparison. |
| E4 | Coverage gap | LOW | spec.md FR-012; tasks.md T022.1 | FR-012 names `--repo` as well as `-R`, and no test used the `--repo` spelling. | Fixed: T022.1 adds `--repo` before `pr` and before the verb, spaced and with `=`. |

## The nine gaps the tasks agent filled

| # | Gap | Weighed |
| --- | --- | --- |
| 1 | US1 is P1 but is built last | No finding. tasks.md's Story order section gives the dependency, which is the note pass F asks for. |
| 2 | plan.md is silent on the bash-fence tests in `tests/test_review_fanout_skill.py` | No finding. The plan's skill rewrite says `wfctl review check` replaces the coordinator's own counting, so retiring those fences (T066) follows from it. Naming the file in `plan.md` would reopen the plan review for a list entry tasks.md already carries. |
| 3 | The `agent_dir` and `storyctl_dir` fixtures set `WFCTL_STATE_DIR` as well as `WFCTL_BRANCH` | Confirmed in `tests/conftest.py`, lines 253 - 254 and 445 - 446. T020 is right to clear both. No finding. |
| 4 | `review start` doesn't print the group's skill | Confirmed in contracts/cli.md. `review groups` prints it, and the plan's `opening-a-change` rewrite already runs from that list. T069 is consistent. No finding. |
| 5 | The 5-second timeout as a module constant | An implementation detail that keeps the hang test fast, and nothing decided it otherwise. No finding. |
| 6 | `_paths` helpers let `TimeoutExpired` propagate | `resolve_branch` catches only `CalledProcessError` today, so a timeout already propagates. T004 pins existing behavior. No finding. |
| 7 | Which rule refuses the `grep` form | Finding F2, fixed. |
| 8 | SC-003 timed in process, results in `guard-timing.md` | In-process timing measures the added Python cost directly. The guard's 27 ms interpreter startup would bury a 1 ms difference in a process-level timing. The Validation Strategy's docstring comparison was missing, which is E3, fixed. |
| 9 | US6's fresh-repository run left to Andre | Finding E2, fixed. |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Verification? |
| --- | --- | --- | --- |
| FR-001 | Yes | T067, T070, T071 | Yes |
| FR-002 | Yes | T062, T071 | Yes |
| FR-003 | Yes | T067, T070, T071 | Yes |
| FR-004 | Yes | T067, T070, T071 | Yes |
| FR-005 | Yes | T011, T015 | Yes |
| FR-006 | Yes | T009, T014 | Yes |
| FR-007 | Yes | T009, T014 | Yes |
| FR-008 | Yes | T010, T015 | Yes |
| FR-009 | Yes | T011, T015 | Yes |
| FR-010 | Yes | T012, T015, T016 | Yes |
| FR-011 | Yes | T015, T016, T066 | Yes |
| FR-012 | Yes | T021, T022, T025, T031, T034, T036 | Yes |
| FR-012a | Yes | T026, T035 | Yes |
| FR-012b | Yes | T023, T024, T032, T033 | Yes |
| FR-012c | Yes | T026, T035 | Yes |
| FR-013 | Yes | T022, T029, T039 | Yes |
| FR-014 | Yes | T028, T029, T038, T039 | Yes |
| FR-015 | Yes | T021, T036 | Yes |
| FR-016 | Yes | T022, T030, T037 | Yes |
| FR-017 | Yes | T043, T044, T046, T047 | Yes |
| FR-018 | Yes | T006, T007 | Yes |
| FR-019 | Yes | T006, T007 | Yes |
| FR-020 | Yes | T006, T007 | Yes |
| FR-021 | Yes | T006, T050, T053 | Yes |
| FR-022 | Yes | T006, T065 | Yes |
| FR-023 | Yes | T051, T052, T054 | Yes |
| FR-024 | Yes | T057 - T061 | Yes |
| FR-025 | Yes | T059, T062 | Yes |
| FR-026 | Yes | T066, T069 | Yes |
| SC-002 | Yes | T011 | Yes |
| SC-003 | Yes | T002, T040 | Yes |
| SC-004 | Yes | T013, T017, T074 | Yes |
| SC-005 | Yes | T006, T065 | Yes |

SC-001 is an outcome count over PRs opened after the change, so it is left out
of the inventory. The gate tasks above are what deliver it.

**Constitution Alignment Issues:** none. The repository has no
`.specify/memory/constitution.md`. The plan's substitute gates, drawn from
`AGENTS.md` and the accepted records, were checked against the tasks: the
release note (T001), no new `MANAGED_HOOKS` row (T037 and the Notes), skill
source under `wfctl/agents/` only, `install-skills` and `doctor` after a skill
change (T063, T071), and the `AGENTS.md` sections (T055, T073). The round cap
deviation from `a-rule-is-expressed-as-a-check` is recorded in the plan and
carried by #626.

**Unmapped Tasks:** none. T025.4 mapped to no FR before F1 was fixed.

**Verification Gaps:** none left. E1 - E4 were fixed.

## Metrics

- Total requirements: 33 (29 FRs, 4 buildable SCs)
- Total tasks: 76
- Coverage: 100% (33 of 33 with at least one task)
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0
- Findings: 6 (2 MEDIUM inconsistency, 1 MEDIUM coverage gap, 3 LOW coverage gaps), all fixed

## Next Actions

Only MEDIUM and LOW findings were found, and all six were fixed, so nothing
stands. The next step is `/speckit.decompose`.
