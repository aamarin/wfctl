# Specification Analysis Report

Feature: #628, every change runs the design passes and records whether it needs a spec.
Run: 2026-10-23, after remediation. Artifacts read: spec.md, plan.md, tasks.md, plus contracts/, data-model.md, research.md, and quickstart.md. The repo has no constitution, so the gates come from `AGENTS.md` and the in-force records.

Design records: 3 listed in design.md
  docs/architecture/design/628-design-passes-own-skill.md (proposed)
  docs/architecture/design/628-early-answer-in-commit-trailer.md (rejected, not compared)
  docs/architecture/design/628-spec-answer-in-pr-body.md (proposed)

## Findings

| ID | Category | Severity | Location(s) | Summary | Outcome |
| --- | --- | --- | --- | --- | --- |
| C1 | Underspecification | MEDIUM | tasks.md T034 | T034 said to copy the wording of `design-passes` step 2 into `design-levels`. That step also tells the agent not to run `wfctl arch none`, which contradicts `design-levels` level 2 and the last sentence of FR-012. | Fixed: T034 copies only the opening read step and says why the `arch none` line stays out. |
| C2 | Underspecification | LOW | tasks.md T002 | T002 builds the five baseline bodies from the PR template, which has no "Needs a spec?" section until T027. | Fixed: T002 adds the heading and body to each file by hand. |
| C3 | Underspecification | MEDIUM | tasks.md T020 | The no-key row asked a unit test to compare against output "before this change", which a test can't run. | Fixed: the row asserts each bad body prints only the `✓` line and exits 0 with no key, and T030 does the real byte comparison. |
| E1 | Coverage gap | MEDIUM | spec.md US1 scenarios 2-4; tasks.md T005 | T005's only verification was that every referenced skill ships. Nothing checked that a yes skips the passes, that an in-boundary change writes nothing, or that a term change goes to `model-the-domain` first. | Fixed: T005 adds a read-back against scenarios 2 to 4. |
| D1 | Repo gates | LOW | tasks.md header | `AGENTS.md` and the user instructions require `writing-style` for any prose, and only T037 named it, while most tasks write prose. | Fixed: the header says to load it for every prose task. |
| F1 | Inconsistency | LOW | plan.md Technical Context, Scale/Scope | Says "edits to four skills"; the plan's own source tree and tasks edit six. | Accepted: any plan.md edit changes its hash, so the plan review reads as stale and the pipeline drops back to plan. tasks.md lists it under open items. |
| F2 | Inconsistency | LOW | plan.md Technical Context, Testing | Doesn't name `tests/test_review_fanout_skill.py`, which T029 verifies with. | Accepted: same reason as F1. |
| F3 | Inconsistency | LOW | tests/test_pipeline_commands.py:407, tasks.md T008 | A test docstring says `design-levels` excludes bug fixes and copy edits, which T008 makes untrue. | Fixed: T008 rewords the docstring. |
| F4 | Inconsistency | LOW | docs/architecture/design/628-design-passes-own-skill.md, Consequences | The record says the cross-reference test can't catch a place that stops pointing to the skill. T003 adds a test that does. | Accepted: the fix is in the record, outside the three artifacts. Already open as PR-015. |
| F5 | Inconsistency | MEDIUM | tasks.md T007; worktree-handoff item 3 | T007 leaves two sentences in the route item that still say `design-levels` owns the line and that boundary-moving work goes through the pipeline. | Accepted: whether to cut them is a wording decision for Andre. Already open as PR-016. |
| C4 | Underspecification | MEDIUM | data-model.md §Section finding; tasks.md T023 | An emphasized bare answer such as "**No.**" passes the no-reason check, since emphasis isn't stripped. | Accepted: stripping emphasis changes the check's behavior, which the artifacts haven't decided. Already open as PR-024. |
| C5 | Underspecification | LOW | research.md R5; spec.md FR-007 | The no-reason rule applies to every listed section, so a repo can't list one where a bare yes or no is a full answer. | Accepted: a product decision for Andre. Already open as PR-023. |

## Coverage summary

| Requirement | Has task? | Task IDs | Verification? |
| --- | --- | --- | --- |
| FR-001 | Yes | T005 | T005 read-back, T015 |
| FR-002 | Yes | T005 | T005 |
| FR-003 | Yes | T005 | T005 read-back |
| FR-004 | Yes | T007-T013 | T003, T004, T014 |
| FR-005 | Yes | T005 | T005 per contract step 1 |
| FR-006 | Yes | T017, T022, T028 | T017 |
| FR-007 | Yes | T018, T020, T023, T025 | T018, T020, T030 |
| FR-008 | Yes | T002, T020, T030 | T020, T030 |
| FR-009 | Yes | T019, T021, T024, T026 | T019, T021 |
| FR-010 | Yes | T027, T028 | T028 |
| FR-011 | Yes | T034 | T034, T035 |
| FR-012 | Yes | T005, T034 | T005 read-back, T015 |
| FR-013 | Yes | constraint in tasks header | review of the diff |
| FR-014 | Yes | T029 | T029, T032 |
| SC-001 | Yes | T015 | manual run |
| SC-002 | Yes | T018, T020 | T020, T030 |
| SC-003 | Yes | T002, T020, T030 | T030 |
| SC-004 | Yes | T004 | T004 |
| SC-005 | Yes | T031 | subagent run |

Every user story has an Independent Test and a Verification block. Every implementation task names a verification path. No task is unmapped.

## Metrics

- Total requirements: 19 (14 FR, 5 SC)
- Total tasks: 39
- Coverage: 100%
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0

## Next actions

No CRITICAL or HIGH finding stands, and no story or task lacks a verification path. Two MEDIUM findings stand (F5, C4) with two LOW ones (F4, C5), and each is a decision for Andre that's already open in `plan-review.md`. The two plan.md fixes (F1, F2) wait for the next plan revision. The pipeline can proceed to `/speckit.decompose`.
