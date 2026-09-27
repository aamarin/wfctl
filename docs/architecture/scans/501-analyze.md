# Analyze scan for #501

## Session 2026-09-27

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md; all three present and read
- Findings: 8 · Critical: 0 · Acted on: 7 · Accepted: 1
- Detail: /Users/andremarin/Development/wfctl-specs/501-plan-review/checklists/analysis-report.md

The run was unattended and settled step 8 by the wrapper's policy. The one
finding it could not apply is held for Andre rather than filed, since his
standing instructions ask that an outward-facing action be confirmed in the
moment. The repository has no constitution, so pass D read the gates `plan.md`
substitutes for one: `AGENTS.md`, the twelve accepted records, and his standing
instructions.

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Resolved (1 LOW, fixed) |
| C · Underspecification | Resolved (1 MEDIUM, fixed) |
| D · Constitution alignment | Resolved (1 MEDIUM, fixed) |
| E · Coverage gaps | Resolved (2 MEDIUM, fixed) |
| F · Inconsistency | Resolved (1 HIGH and 1 MEDIUM, fixed) |
| G · Design-record contradiction | Outstanding (1 HIGH, 2 records read) |
| Requirement-to-task coverage | 100% |

### Findings

- **G · Design-record contradiction, HIGH.** T026 puts the report and plan-copy
  paths in `SKILL.md`, and `501-plan-review-wrapper-split` gives the report path
  to the wrapper.
  Record: `docs/architecture/design/501-plan-review-wrapper-split.md`
  Decision: "It holds the marker to surface, wfctl's step names (`plan`,
  `tasks`, and `analyze`), the report path, and the instruction to follow
  `writing-a-scan-file`."
  Task: "Write the report to `FEATURE_DIR/plan-review.md` and the copy to
  `FEATURE_DIR/plan-review.plan.md`."
  → Accepted: the record is proposed, and rewriting T026 to conform would
  ratify it, which is a person's call. The contract for the command already
  sides with the record, so the likely fix is one line in T026 and one in the
  plan's structure listing.
    Not filed: held for Andre, who confirms outward-facing actions in the moment.
- **F · Inconsistency, HIGH.** Research R4 makes a step row's `auto` depend on
  the approval grant, and the #325 test
  `test_the_reported_flag_is_the_table_and_nothing_else` states that it must
  not. The test calls with the default grant, so it would keep passing and the
  reversal would go unseen.
  → Fixed: T013 now rewrites that test's docstring to cite R4 and adds a loop
  under `auto_approve=True`. Decided against leaving the test as it is: a
  docstring that states a rule the code no longer follows is the kind of claim
  nothing checks.
- **F · Inconsistency, MEDIUM.** The merge gate for User Story 1 allowed a
  known-red test, which the definition of done does not allow.
  → Fixed: the command-file assertion moved to T025 item 7 as a widening of the
  existing drift check to pass commands, and T017 requires every test green.
  Decided against widening the check in slice 1: it would turn that slice red
  until slice 2 lands.
- **E · Coverage gaps, MEDIUM.** FR-012, which forbids an approved or rejected
  verdict in the report, had no task and no verification.
  → Fixed: T026 keeps the rule, and T033 greps every report for the forbidden
  words.
- **E · Coverage gaps, MEDIUM.** Nothing exercised FR-025's fallback to a full
  review when the plan copy is missing.
  → Fixed: T033 runs a re-review with the copy deleted.
- **C · Underspecification, MEDIUM.** FR-010 required reading a constitution this
  repository does not have, and the constitution's path belongs to the runner.
  → Fixed: FR-010 reads it when the repository has one and reports its absence,
  which follows from FR-016 making only a missing `spec.md` or `plan.md`
  inconclusive. T030 names the path in the wrapper. Decided against treating a
  missing constitution as `inconclusive`: FR-016 already rules that out.
- **D · Constitution alignment, MEDIUM.** The rule that prose written to a file
  goes through `andres-voice` was named on two tasks, while seven more write
  prose.
  → Fixed: a line in the Notes section names every such task.
- **B · Ambiguity, LOW.** User Story 1's acceptance scenarios read 1, 2, 5, 6,
  3, 4.
  → Fixed: reordered, with every number kept, since none is cited elsewhere.

### Filing

- **The report path sits in the skill, against the wrapper-split record.** It
  covers G1. Not filed: held for Andre's confirmation.
  Title: T026 puts the plan-review report path in the skill, which the
  wrapper-split record gives to the wrapper
  Body: `docs/architecture/design/501-plan-review-wrapper-split.md` (proposed)
  says the `/plan-review` wrapper holds the report path. T026 in
  `tasks.md`, and the Source Code listing in `plan.md`, put
  `FEATURE_DIR/plan-review.md` and `FEATURE_DIR/plan-review.plan.md` in
  `SKILL.md` instead. The command contract already puts them in the wrapper
  (section 5). There are two ways to settle it: have the skill refer to "the
  report path the invoking command names" and move both paths into T030, or
  amend the record to allow a method to name its own output file.

### Deferred

- **Next Actions.** F1's fix makes the reversal visible, but whether a grant
  should answer a step row at all is the question the handoff already carries as
  its open question 2, and it stays Andre's.
