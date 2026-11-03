# Specification Analysis Report: #432

Scanned `spec.md`, `plan.md`, and `tasks.md`, with `contracts/cli.md`, `data-model.md`, and `research.md` for cross-reference. The repository has no `.specify/memory/constitution.md`, so pass D checks the gates the plan takes from AGENTS.md and the accepted records.

Design records: 2 listed in design.md
  docs/architecture/design/432-session-report-is-a-status-flag.md
  docs/architecture/design/432-doctor-session-scopes-claim-notices.md

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| F1 | Inconsistency | HIGH | tasks.md T005 item 3, T006; spec.md Edge Cases (last item); contracts/cli.md trunk paragraph | T005 and T006 fall back to the local branch `_paths.trunk_branch` returns when there's no `origin/HEAD`. The spec and the CLI contract both say a repo with no `origin/HEAD` reads `Commits: trunk not found` and lists the last 20 commits. | Make T005 and T006 match the spec: with no `origin/HEAD`, report trunk not found without calling `review_trunk`. |
| E1 | Coverage gap | MEDIUM | spec.md FR-003; contracts/cli.md `Session:` line; tasks.md T017 | No test checks that the report prints the session holder and the last stop's kind, which step 8 reads. T007 tests `last_stop()` alone. | Add to T017: the `Session: <holder> · last stop: <kind>` line, and `last_stop` in `--json`. |
| E2 | Coverage gap | MEDIUM | contracts/cli.md ("It writes nothing"); 432-session-report-is-a-status-flag.md Verification; tasks.md T020 | T020 tests that plain `status` writes nothing. Nothing tests that `status --session` writes nothing, which the contract and the design record's Verification both ask for. | Add to T017: `status --session` leaves `events.jsonl` and the state dir unchanged. |
| E3 | Coverage gap | MEDIUM | spec.md FR-005; data-model.md `uncommitted`; tasks.md T017 | No test covers the uncommitted-changes list. | Add to T017: a dirty tree lists its `git status --short` lines under `Uncommitted`, and a clean tree lists none. |
| E4 | Coverage gap | MEDIUM | spec.md US3 acceptance 5 and 6, SC-004; tasks.md T037 | T037's manual run compares step 8 rows only. Nothing checks that a green `doctor` leaves the reference file unopened, or that a drifted one opens it and repairs as before. | Add both checks to T037. |
| B1 | Ambiguity | LOW | spec.md SC-001 | "Materially less than 19.2k tokens" has no threshold. The PR records both figures, so a reviewer can judge it, but nothing says what counts as passing. | Pick a number, or accept the before/after figures as the criterion. That choice is the user's. |

## Coverage summary

| Requirement | Has task? | Task IDs | Verification? |
| --- | --- | --- | --- |
| FR-001 | yes | T019, T020 | T017, T020 |
| FR-002 | yes | T020 | T017 |
| FR-003 | yes | T008, T019 | T007, T017 |
| FR-004 | yes | T003, T019 | T017, T018 |
| FR-005 | yes | T001, T006 | T005, T017 |
| FR-006 | yes | T019 | T017 |
| FR-007 | yes | T013–T015, T019 | T017 |
| FR-008 | yes | T023 | T022 |
| FR-009 | yes | T019 | T017 |
| FR-010 | yes | T010, T013 | T009 |
| FR-011 | yes | T010, T014 | T009 |
| FR-012 | yes | T012, T015 | T011, T017 |
| FR-013 | yes | T029 | T028 |
| FR-014 | yes | T029 | T028 |
| FR-015 | yes | T036 | T031 |
| FR-016 | yes | T036 | T031 |
| FR-017 | yes | T036 | T032 |
| FR-018 | yes | T035 | T034, T037 |
| FR-019 | yes | T026, T036 | T025 |
| FR-020 | yes | T039 | T039 |
| FR-021 | yes | T040 | T040 |
| FR-022 | yes | T036 | T031, T032 |
| SC-001, SC-002 | yes | T038 | T038 (B1) |
| SC-003 | yes | T037 | T037 |
| SC-004 | yes | T037 | T037 |
| SC-005 | yes | T030 | T028, T030 |

**Pass D (gates from AGENTS.md and the accepted records)**: no conflict. The release note is T039, the definition of done is T042, and `uv run` is used throughout.

**Pass G**: both records read, both `proposed`. No task reverses either Decision or Consequences. The report stays a `status` flag, plain `status` makes no tracker call (T020), `start` is untouched, the skill runs the four commands (T031, T036), and `doctor --session` filters claim notices only (T028, T029).

**Unmapped tasks**: none. T041 and T043 are process tasks from the handoff.

## Metrics

- Total requirements: 22 FR and 5 SC
- Total tasks: 43
- Coverage: 100% of requirements have at least one task
- Ambiguity count: 1
- Duplication count: 0
- Critical issues: 0

## Remediation

The user approved the fixes on 2026-11-02.

- F1: fixed. T005 item 3 and T006 now report trunk not found with no `origin/HEAD`, and T001 carries the same rule into `research.md`.
- E1, E2, E3: fixed. T017 gains items 7, 8, and 9.
- E4: fixed. T037 checks that the reference file opens only when `doctor` isn't green.
- B1: accepted. The user didn't set a threshold, so the PR's before and after figures stand as the evidence for SC-001.

## Next actions

No CRITICAL or HIGH finding stands. One LOW stands, B1, accepted rather than fixed. Proceed to `/speckit.decompose`.
