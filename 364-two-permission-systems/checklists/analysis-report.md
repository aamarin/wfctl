# Specification Analysis Report

**Feature**: `364-two-permission-systems` | **Date**: 2026-09-13
**Artifacts**: `spec.md`, `plan.md`, `tasks.md` — all three present and read
**State**: post-remediation. Five findings were applied to the artifacts during
this run; the rows below carry their resolution rather than the pre-fix text.

## Findings

| ID | Category | Severity | Location(s) | Summary | Resolution |
| --- | --- | --- | --- | --- | --- |
| E1 | Coverage gap | HIGH | spec.md SC/FR block; tasks.md Phase 3 | FR-009 — *there must be no way to report a success through this command* — carried zero tasks and zero tests. It is the narrow exception to `wfctl-runs-the-verification`, enforced by the shape of the surface and by nothing that fails when the shape changes. | Fixed: added `T010a` asserting against the command's own parameter set that its only recordable outcomes are a block and a clearing. |
| F1 | Inconsistency | HIGH | spec.md SC-005; spec.md US2 *Why this priority* | Both asserted the blocked agent cannot reach the release. FR-013, clarification Q4 and `contracts/cli.md` all make `--clear` ungated and explicitly agent-reachable — so SC-005 was a measurable outcome the design deliberately does not deliver, and a test written against it would have failed by design. | Fixed: both restated to the property that holds — the asymmetry is on *what may be reported*, not on who may clear. |
| F2 | Inconsistency | MEDIUM | spec.md Edge Cases | *An action spelling that matches nothing* said the action determines which step is held, and that an action belonging to no step holds nothing. FR-010 and `data-model.md` say the step is inferred at call time and the report names no step of its own. | Fixed: reworded to FR-010's rule, and says what an odd spelling actually costs — the release, not the hold. |
| C1 | Underspecification | MEDIUM | tasks.md T013 | *Refuse … when `--reason` is absent* read as covering every mode, which would refuse the `--clear` mode T023 builds. `contracts/cli.md` gives `--clear` exit 0 always. | Fixed: scoped to the reporting mode, with the conflict it would otherwise create named in the task. |
| F3 | Inconsistency | MEDIUM | spec.md SC-003 | *all seven grant states* — `_NOTIFY_LINES` (`wfctl/cli.py:179`) carries seven keys and `_notify_line` builds an eighth for `label`. `plan.md` and `T029` both say eight; `research.md` reconciles the two but SC-003 is what a reader verifies. | Fixed: SC-003 now reads eight renderings, naming the seven keyed states plus the built one. |
| A1 | Duplication | LOW | spec.md FR-012, FR-020 | FR-020 restates FR-012's most-recent-event rule for the success case. | Accepted: FR-020 carries the matching-by-action-name fact FR-012 does not, and that fact is where the design says it breaks first. Merging them would lose it. |

## Coverage Summary

Post-remediation. 27 requirement keys — FR-001 to FR-021 and SC-001 to SC-006.
Every success criterion here states a property of the build rather than a
post-launch metric, so all six are counted.

| Requirement Key | Has Task? | Task IDs | Verification? |
| --- | --- | --- | --- |
| FR-001 | yes | T032 | `test_the_second_permission_layer_is_named_in_every_grant_state` |
| FR-002 | yes | T032 | same loop — keyed on nothing |
| FR-003 | yes | T030 | `test_the_new_line_names_no_command` |
| FR-004 | yes | T031 | `test_the_irreversible_line_names_every_action_in_its_class` |
| FR-005 | yes | T011 | `test_a_run_holding_no_grant_can_still_report_a_block` |
| FR-006 | yes | T008, T011 | same |
| FR-007 | yes | T013 | `test_a_block_with_no_reason_is_refused_and_stores_nothing` |
| FR-008 | yes | T014 | `test_a_branch_with_no_feature_still_stores_the_report` |
| FR-009 | yes | **T010a** | `test_no_spelling_of_blocked_records_a_success` |
| FR-010 | yes | T002, T012 | `test_the_step_comes_from_inference_not_from_the_caller` |
| FR-011 | yes | T015, T016 | `test_holding_a_done_step_does_not_cascade_the_steps_after_it` |
| FR-012 | yes | T004, T022 | `test_the_most_recent_event_for_an_action_is_the_one_that_stands` |
| FR-013 | yes | T023 | `test_clearing_works_for_a_run_holding_no_grant` |
| FR-014 | yes | T024 | `test_clearing_an_action_with_no_block_standing_says_so` |
| FR-015 | yes | T025 | `test_the_remedy_names_the_host_and_the_clearing_command` |
| FR-016 | yes | T026 | `test_the_next_action_for_a_held_step_is_the_steps_own_command` |
| FR-017 | yes | T019 | manual — `install-skills`, then read it as an agent would |
| FR-018 | yes | T017, T033 | `test_a_held_step_adds_no_new_state_name_and_no_new_payload_key` |
| FR-019 | yes | T009 | `test_notify_still_refuses_a_run_holding_no_grant` |
| FR-020 | yes | T022 | `test_a_later_success_for_the_same_action_releases_the_hold` |
| FR-021 | yes | T005 | `test_a_block_on_one_branch_does_not_hold_a_step_on_another` |
| SC-001 | yes | T025, T027 | `tests/test_console_plaintext.py`, extended |
| SC-002 | yes | T010, T016, T017 | `test_a_block_holds_a_step_whose_own_artifacts_read_done` |
| SC-003 | yes | T029, T031 | the eight-rendering loop |
| SC-004 | yes | T008, T011 | one command, no preparatory step |
| SC-005 | yes | T021, T023, **T010a** | release path, plus the no-success assertion |
| SC-006 | yes | T018, T033 | `tests/test_pipeline_payload_snapshot.py` |

**Requirement-to-task coverage: 100%** (27 of 27). Pre-remediation: 96% (26 of
27) — FR-009 was the gap.

## Constitution Alignment

This repository has no `.specify/memory/constitution.md`. `plan.md` substitutes
`AGENTS.md` § Definition of done, § Testing conventions and § Code style plus the
records `wfctl arch context` prints, and records the substitution in Complexity
Tracking as the template requires. No conflict found against those gates: the
validation plan is the repository's own three commands plus `doctor`, the skill
change carries the `install-skills`-and-read-it step `AGENTS.md` requires for
anything under `wfctl/agents/`, and `NO_COLOR` is pinned on the output
assertions.

## Design-record contradiction (pass G)

One record listed in `design.md`:

```
docs/architecture/design/364-the-block-report-is-its-own-verb.md   (proposed)
```

Read against its `Decision` and `Consequences` sections only. No task reverses
either. Each of the Decision's five commitments has a task carrying it: T011 (a
separate verb that never calls `action_grant`), T012 (the step comes from
inference), T002 (the event kind), T015 (a `block_reason` shaped after
`verification_block`), T023 (`--clear`, ungated), T009 (`notify` unchanged). The
Consequences section's one obligation — *`status` must print that remedy, the way
`verification_block` prints* — is T025.

`design.md` also names the level-2 record
`docs/architecture/the-agent-reports-the-block-wfctl-never-saw.md` in prose
outside the list, and says why: it binds as a level-2 record through `wfctl arch
context`, not as a structural choice for this feature. Not read as a level-3
record here.

## Unmapped Tasks

None. Every task maps to a requirement, a user story's verification block, or the
repository's own definition of done (T001, T038, T039).

## Verification Gaps

None outstanding. T019 (the skill instruction) and T036 (the `--help` review
question) are verified by reading rather than by assertion — both are stated that
way deliberately, T019 on `AGENTS.md`'s rule that the suite checks skills ship
and cross-reference rather than that they read well, T036 because the level-3
record files it as a review question rather than a test.

## Metrics

- Total requirements: 27 (21 FR, 6 SC)
- Total tasks: 40 (T001–T039 plus T010a)
- Coverage: 100% (requirements with ≥ 1 task), post-remediation
- Ambiguity count: 0 unresolved placeholders; 1 underspecification found and fixed
- Duplication count: 1, accepted
- Critical issues: 0

## Next Actions

Computed after remediation, not from the pre-fix report.

- No CRITICAL finding was found, and none stands.
- The two HIGH findings were both fixed in the artifacts: FR-009 now has a task,
  and SC-005 states a property the design delivers.
- Nothing was filed. Every finding this run produced was in scope and applied.
- Proceed to `/speckit.decompose`. The three PR slices `tasks.md` names — the
  event layer and the honest stop, the release and the remedy, the two authority
  lines — are the signal that step reads.
- Outstanding and not this step's: both design records are `proposed`. T037 moves
  them to `accepted`, and it is a person's task — `wfctl arch accept` records
  where a human agreed and never decides that an agreement happened.
