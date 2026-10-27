# Analyze scan for #649

## Session 2026-10-26

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 8 · Critical: 0 · Acted on: 4 · Accepted: 4
- Detail: /Users/andremarin/Development/wfctl-specs/649-design-checks-by-context/checklists/analysis-report.md

This run was unattended, so remediation followed the wrapper's policy. Every fix went into `tasks.md`. `plan.md` wasn't edited, because an edit makes the third plan review stale and sends the pipeline back to `plan` (`plan-edit-requires-new-review`). Where a fix belonged in the plan, `tasks.md` now says the task wins and names the passage.

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Clear |
| C · Underspecification | Resolved (1 MEDIUM, task fixed) |
| D · Constitution alignment | Clear |
| E · Coverage gaps | Resolved (1 MEDIUM, task fixed) |
| F · Inconsistency | Outstanding (1 MEDIUM, 1 LOW; 1 MEDIUM, 1 LOW resolved) |
| G · Design-record contradiction | Outstanding (2 HIGH) |
| Requirement-to-task coverage | 100% |

### Findings

- **C · Underspecification, MEDIUM**: T003's lead branch, context names on the row and the reasons in the JSON `annotation` and under `--all`, can't be built. The row and the JSON `annotation` are one field, the payload's `sub_steps` carry no `reason`, a reason on a done pass makes its step read as held, and `--all` prints no line beyond the row.
  → Fixed: T003 now keeps the reasons on the row, prints it with `soft_wrap=True`, and gives those three reasons. Decided against a new payload field for the names-only row: research R6 rejected it, and FR-010a needs the reasons under `--all`.
- **F · Inconsistency, MEDIUM**: T003, T012, and T048 edit `plan.md` during implementation, and any edit routes the pipeline back to `plan`. T003's edit only records a display choice.
  → Fixed: T003 writes the choice to `contracts/cli.md` only. T012 and T048 now say the edit makes the review stale, and name `/plan-review` and `wfctl step sign-off plan.plan-review` as the ways forward. Decided against dropping the plan edits from T012 and T048: a plan that no longer matches the merged code of #635 or #648 needs a new review.
- **F · Inconsistency, LOW**: the tasks differ from the plan in three places the "Review findings these tasks settle" section didn't name. The `--context` skill text moves from Phase A to Phases 5 and 9, the `speckit-brainstorm` `allowed-tools` line and `design-passes` don't change, and the Constitution Check says the `Level` constants are the one addition beyond the level-3 record.
  → Fixed: a paragraph in that section says the task wins and lists the three. Decided against editing `plan.md`, for the staleness reason above. Moving the skill text decides nothing new, since the plan's Phase A text teaches a refusal that only exists once Phase B lands.
- **E · Coverage gaps, MEDIUM**: `step none brainstorm.software-design` had no test for its `--context` success line, its two name refusals, or the bare-form refusal (FR-010, FR-011). T025 runs before #648 adds the pass.
  → Fixed: T049 adds those four tests in `tests/test_step_none.py`, and Phase 9's Verification block names the file. Decided against adding them to T025, which runs before the pass exists.
- **F · Inconsistency, MEDIUM**: T032 and T033 read per-context exception files whether or not the repo has a name list. FR-021 and `plan.md` Phase B item 7 put the guard check under "with a name list", and FR-002 rules out a new refusal or finding in a repo with no list. The two disagree only when per-context files exist without a list.
  → Accepted: out of scope. Reading the domain page at the commit the guard acts on, or amending FR-002, is a choice the artifacts never made. Filed as #653.
- **F · Inconsistency, LOW**: T033 extends #635 R12's skip to an inherited per-context "no" whenever the branch changes any level-2 record. A narrower rule, skipping only when a changed record governs that context, matches research R8 as well. PR-015 asked the plan to choose.
  → Accepted: out of scope, since it picks between approaches the plan left open. Filed as #653.
- **G · Design-record contradiction, HIGH**: T008 reverses a proposed decision.
  Record: `docs/architecture/design/649-contexts-module.md`
  Decision: "`_arch.py` gets only the `governs` field and the `validate` finding."
  Task: "Add `split_names(value) -> tuple[str, ...]` and `Record.governs: tuple[str, ...] = ()` to `wfctl/_arch.py`"
  → Accepted: the record is `proposed`, and conforming the task or amending the record would ratify it. Filed as #652.
- **G · Design-record contradiction, HIGH**: T017 reverses a proposed decision.
  Record: `docs/architecture/design/649-contexts-module.md`
  Decision: "Each check gathers its own records and calls `unanswered`. The architecture pass gives it this branch's level-2 records, and #648's pass gives it this branch's level-3 records."
  Task: "It gathers level-2 records from `records_on_this_branch(...)`, and level-3 records from `records_on_this_branch(repo_root, arch / DESIGN_DIR)` ... A mapping in `_evidence`, keyed by `Level`, picks the folder for each level"
  → Accepted: the record is `proposed`. The user chose to share one function with the Boundary line in the plan walkthrough (research R7), so this is likely the design moving, and the record needs a person to amend it. Filed as #652.

The six plan-review mappings in `tasks.md` were each checked against the review's suggested response, and all six hold. PR-013's held only after the C fix above.

### Filing

- **The level-3 record predates the plan's additions**: both G findings. Filed as #652.
- **Two open choices in the per-context exception readers**: both T032 and T033 findings. Filed as #653.

### Deferred

- None. Every pass ran, and pass G read the one record `design.md` lists.
