# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 917273ccd1741eff61dfe1348db5ca30abd3a6b7 | technical strategy |
| spec.md | 2c9c89ffdad0c1ac38363061140b52d7bebb3519 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 5b70b93efa85d2ea8df1ffebc08e3907829c2dac | design-record index |
| docs/architecture/design/software-design-none-is-a-claim.md | c217a83b3a517bd3cb516abd105a4371599a43c7 | design record |
| docs/architecture/declarations/648-design-gate.md | 8358208e0cc21da4a35f3dc336d376f18fa8b8fa | level-2 declaration design.md names |
| docs/architecture/promised-evidence-blocks-on-silence.md | 970abb8f55ac25118a36d9e71ef3d2220f662666 | proposed record the plan amends (research R10) |
| research.md | 1efe6afae5de4efc4261b3f0db3c152c0bee3ea6 | planning evidence |
| data-model.md | 643113cb11c28e27dc808f047b5f9b08781e5625 | planning evidence |
| contracts/cli.md | 1a11576d8914c89c7978c85b38977ffd1dbcabc2 | interface contract |
| quickstart.md | 8cc6853b66ebb2a5c2b0c8c5600c4bca27fa9bbe | end-to-end verification |
| checklists/requirements.md | 5d24c2763686d2b8e4a90fa6867b32d57f7b5efa | requirements-quality checklist |
| AGENTS.md | 506b62be5f7860aad3ead6ba5bae864db68b15ba | gates the plan substitutes for the constitution |
| docs/architecture/vendor-upstream-skills.md | 4d6b0177ffe76f882118423926af27d76b74e934 | accepted record the plan cites for editing skills in place |
| plan-review.plan.md | 85a62d65e623aa2a9231e744809e60414aa982b5 | base of this re-review |

## Review scope

- Re-review: the plan copy's identity equals the earlier report's `plan.md`
  row, so the copy was diffed against `plan.md`
- Changed since the earlier report, in `plan.md`: `§_evidence.py` items 5.2,
  5.4 and 5.5 (the checks-off reading moves to `display`, and `blocks` is
  asked before the reason is chosen), items 6.2 and 6.3 (the same two changes
  for the architecture check), `§cli.py, check_config_cmd` (the new finding
  runs before the early return for a missing `wfctl.json`), tests 8a and 8b
  (new assertions), and the new test 8d. Reviewed together with the sections
  that refer to them: items 5.1, 5.3, 6.1, 6.4 and 6.5, `§_paths.py` items 2
  and 3, `§cli.py, status_cmd`, the test list, and the requirement trace
- Inputs whose identity changed since the earlier report: none. Every input
  row other than `plan.md` and the plan copy matches its file. No input was
  named as changed by the invoking command
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification
- Conditional lenses: security and reliability applied, carried from the
  earlier review (the unattended claim grant and the new hold's ways out).
  The revision touched neither
- Design records: 1 listed in design.md,
  `docs/architecture/design/software-design-none-is-a-claim.md`
- Existing code inspected, to check the claims the revision makes:
  `wfctl/_evidence.py` (`Assessment` and its `renders`, `blocks`,
  `_PROMISED`, `DRAWINGS_UNCHECKED`, `_architecture_answered`,
  `brainstorm_architecture`, `_judge_drawings`, `brainstorm`),
  `wfctl/_pipeline.py` (`_pass_states`, `_read_pass`, `collect_warnings`),
  `wfctl/cli.py` (`status_cmd`'s pass-row loop at lines 812-848,
  `check_config_cmd` at lines 6620-6688), and `tests/test_evidence.py`
  (`test_every_inconclusive_verdict_goes_through_blocks`)
- Reviewers: the lenses above, run in sequence by one agent in a fresh context

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 13

No BLOCKER findings identified in this review. The three MAJOR findings the
earlier review left open are fixed. PR-020 is fixed by asking `blocks` before
choosing a reason in both checks, and by test 8d, which patches `blocks` and
would fail a reader that settles git's silence on its own. PR-021 is fixed by
putting the checks-off text in `display`, which the code renders on the row
without making it a warning. PR-022 is fixed by running the new `check config`
finding before the early return for a missing `wfctl.json`.

The twelve MINOR findings from the earlier review are still open, since the
revision didn't touch them. One new MINOR finding, PR-028, is that
`research.md §R10` still names the source-scanning test as the guard, which
the plan's own test 8d now says it can't be.

## Findings

### PR-001: The unattended claim FR-009a requires has no grant in either brainstorm surface

- Priority: MAJOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence: `plan.md §speckit-brainstorm and commands/speckit.brainstorm.md,
  allowed-tools` and test 14, unchanged since the earlier review
- Finding: Fixed, as the earlier review found.
- Why it matters: FR-009a works unattended.
- Suggested response: None.
- Corroborated by: security and reliability, adversarial implementation and
  verification

### PR-002: Test 8 expects a remedy the pass can never produce

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence: `plan.md` test 8 now reads "Held when the arch root is outside the
  tree, with the same reason (FR-006)", which matches the rewritten FR-006 and
  `contracts/cli.md §held because git can't answer`
- Finding: Fixed. The test changed again with FR-006, and still agrees with
  the spec and the contract.
- Why it matters: The test asserts what the spec now requires.
- Suggested response: None.
- Corroborated by: adversarial implementation and verification

### PR-003: The contract's held output contradicts the pass cascade

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `contracts/cli.md §held on the pass` is unchanged, and the new
  `§held because git can't answer` block shows `software-design ○` after a
  held `architecture`, which matches `_pass_states`' cascade
- Finding: Fixed.
- Why it matters: None remaining.
- Suggested response: None.
- Corroborated by: adversarial implementation and verification

### PR-004: R7's width rationale is false, and the departure from FR-007 is unlabelled

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence: `research.md §R7` unchanged since the fix
- Finding: Fixed.
- Why it matters: None remaining.
- Suggested response: None.
- Corroborated by: requirements and traceability

### PR-005: Two acceptance scenarios have no planned test

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence: `plan.md` tests 11 and 12
- Finding: Fixed.
- Why it matters: None remaining.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-006: SC-004 is a rule visible in an artifact and has no check

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence: `plan.md` test 13
- Finding: Fixed.
- Why it matters: None remaining.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-007: The quickstart runs the installed wfctl, not the working tree's

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence: `quickstart.md` defines and uses `$WFCTL`; the file is unchanged
- Finding: Fixed.
- Why it matters: None remaining.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-008: Two places in design-levels still give level 3 no claim

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `plan.md §design-levels, where each answer is written (line 88)`
  and `§design-levels, Where the levels land`
- Finding: Fixed.
- Why it matters: None remaining.
- Suggested response: None.
- Corroborated by: requirements and traceability

### PR-009: The test changes R9 and Project Structure list don't match the suite

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence: `research.md §R9` items 2 and the `storyctl_dir` paragraph, and
  `plan.md` test 15
- Finding: Fixed. PR-014 and PR-026 cover tests R9 and R10 still miss.
- Why it matters: The snapshot test keeps its meaning.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-010: The plan's validation list omits two commands spec.md names

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `plan.md §Technical Context › Testing`
- Finding: Fixed.
- Why it matters: None remaining.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-011: design.md and spec.md name different release-note files

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `design.md §MVP Scope` item 5, `research.md §R8`, `spec.md` FR-011
- Finding: Fixed.
- Why it matters: None remaining.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-012: Docstrings that count brainstorm's passes as two are left stale

- Priority: MINOR
- Category: Enhancement Suggestion
- Status: fixed
- Evidence: `plan.md §_evidence.py` item 7 (renumbered from 4)
- Finding: Fixed for the places it named. PR-013 lists the rest.
- Why it matters: None remaining.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-013: Three more comments still count brainstorm's passes as two

- Priority: MINOR
- Category: Enhancement Suggestion
- Status: open
- Evidence:
  - `tests/test_cli_status.py:44`, `tests/test_pipeline_state_names.py:249`,
    and the `brainstorm_architecture` docstring ("`design.md` is the other
    pass's business", "then both passes run") still say two
  - `plan.md §_evidence.py` item 7 doesn't list them
- Finding: Unchanged from the earlier review.
- Why it matters: Each becomes false once the third pass lands, and the
  `test_cli_status.py` docstring sits beside an assertion the plan changes.
- Suggested response: Add the three to item 7. A `grep` for "two passes" and
  "two built-in" over `wfctl/` and `tests/` finds them.
- Corroborated by: single reviewer

### PR-014: R9's rule for affected tests misses a test that stages no design.md

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `research.md §R9` still selects tests that "stage `design.md` and an
    architecture answer"
  - `tests/test_pipeline_state_names.py`
    `test_a_written_record_with_no_design_doc_leaves_exactly_one_pass_outstanding`
    stages a record and no `design.md`, and asserts the outstanding passes are
    exactly `["design-doc"]`. The new pass makes that `["software-design"]`
- Finding: Unchanged from the earlier review.
- Why it matters: The quickest repair swaps the expected name and removes the
  only test that `design-doc` is reported when it's the last thing missing.
- Suggested response: List the test in R9, and keep its meaning by adding a
  claim or a `design/` record to its setup.
- Corroborated by: single reviewer

### PR-015: Test 14 checks one spelling of the broad grant

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence: `plan.md` test 14 still asserts that `Bash(wfctl step none*)` is
  absent. That passes against `Bash(wfctl step none *)` and `Bash(wfctl*)`
- Finding: Unchanged from the earlier review.
- Why it matters: A space before the `*` widens the grant and keeps the test
  green.
- Suggested response: Match two command lines against the grants with
  `fnmatchcase`, as `tests/test_provenance.py` does: the
  `brainstorm.software-design` claim must match a grant, and
  `wfctl step none plan.plan-review --reason x` must match none.
- Corroborated by: security and reliability

### PR-016: The narrow grant doesn't stop the agent from claiming another pass

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence: `plan.md §allowed-tools` still presents the narrow grant as what
  keeps the agent from claiming `plan.plan-review`. Both brainstorm surfaces
  grant `Write` with no path limit, and `_step_claims` reads any `*.md` under
  the branch's claim folder
- Finding: Unchanged from the earlier review.
- Why it matters: A later change could rely on the grant as enforcement.
- Suggested response: Say the grant limits the command line, and that the PR
  review of the committed claim is the control.
- Corroborated by: security and reliability

### PR-017: No test fails if the width is hard-coded, and "20 in every repository" overstates it

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence: `plan.md §cli.py, status_cmd` and `contracts/cli.md` still say the
  width is 20 in every repository, and test 9 uses built-in names only
- Finding: Unchanged from the earlier review.
- Why it matters: `.ljust(20)` passes every planned test, and a declared pass
  longer than 16 characters is where it differs.
- Suggested response: Add a declared long name to test 9, and say "at least
  20".
- Corroborated by: single reviewer

### PR-018: Two quickstart steps leave the reader to guess

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence: `quickstart.md` step 6 says "remove the claim" with no path, and
  step 7 reads `.claude/skills/` from the scratch repository, where nothing is
  installed
- Finding: Unchanged from the earlier review.
- Why it matters: A reader who finds no skills could report SC-004 failed.
- Suggested response: Give step 6 the `rm` with the path, and step 7 the
  worktree's absolute path.
- Corroborated by: single reviewer

### PR-019: The design record says the remedy prints under `how:`, and the spec says `next:`

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence: `docs/architecture/design/software-design-none-is-a-claim.md
  §Verification` is unchanged and still says `how:`
- Finding: Unchanged from the earlier review. The plan follows the spec.
- Why it matters: Someone checking the record's own verification would look in
  the wrong place.
- Suggested response: Correct the record's line, if its owner agrees.
- Corroborated by: single reviewer

### PR-020: The software design check settles a git silence before asking `blocks`

- Priority: MAJOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §_evidence.py` item 5.4 now returns `Assessment("done")` when
    `blocks(verdict, "repo-declared")` is false, and item 5.5 chooses
    `GIT_UNANSWERED_REASON` or `SOFTWARE_DESIGN_REASON` only after `blocks`
    has decided to hold. The plan says why: handling `inconclusive` first
    would be the reader deciding what git's silence means
  - Item 6.2 gives `_architecture_answered` the same order: `None` when
    `blocks` is false, and the reason only once it holds
  - Test 8d patches `_evidence.blocks` to return false and expects both
    checks to read done when git can't answer. Checked against the code: both
    readers live in `_evidence.py` and call `blocks` by its module name, so
    the patch reaches them. With `blocks` false, `_architecture_answered`
    returns `None` and `brainstorm_architecture` falls through to
    `_judge_drawings`, which reads `done` (with `DRAWINGS_UNCHECKED` as
    display when there is no trunk), which is today's ambient behaviour. A
    reader that returned early on `inconclusive` would read `in_progress`
    under the patch and fail
- Finding: Fixed. The order now matches
  `promised-evidence-blocks-on-silence.md §Decision`, and a test that can
  observe the order replaces the claim that the source-scanning test did.
  PR-028 covers the claim, which `research.md` still makes.
- Why it matters: A later change to `blocks` now reaches both readers, and
  test 8d fails if one stops following it.
- Suggested response: None.
- Corroborated by: architecture and boundaries, adversarial implementation and
  verification

### PR-021: A checks-off reading is a warning, so it prints on every `wfctl status`

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §_evidence.py` items 5.2 and 6.3 now return
    `Assessment("skipped", display=CHECKS_OFF_REASON)`, and say why
  - Checked against the code: `_pass_states` passes `reading.renders()` as
    the row's annotation and `reading.reason` as its reason
    (`_pipeline.py:551-553`). `renders()` returns `display` when it is set.
    `collect_warnings` lists a finished pass only when it has a `reason`
    (`_pipeline.py:1010-1012`), so this reading adds no warning
  - `cli.py:821` hides a skipped pass without `--all` when it carries no
    warning, and `cli.py:832-837` prints its annotation with no warning mark
    under `--all`, which is what `contracts/cli.md §checks turned off` shows
  - Test 8a now asserts an empty `warnings` list and no warning line
- Finding: Fixed.
- Why it matters: A repo that turns the checks off sees the two rows only
  under `--all`, as the contract shows.
- Suggested response: None.
- Corroborated by: adversarial implementation and verification

### PR-022: `check config` never reads the setting when `wfctl.json` is missing

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §cli.py, check_config_cmd` items 1 to 3 now call
    `design_record_checks_problems` before the early return at
    `cli.py:6637-6639`, print its problems under the `✗ wfctl.json:` heading
    and exit 1 when there is no `wfctl.json`, and add them beside
    `declared_trunk_problems` when there is one
  - `plan.md §_paths.py` item 2 reads a missing `wfctl.json` as on, so the
    outside-the-tree problem is raised in a repo with no `wfctl.json`
  - Test 8b now covers a repo with no `wfctl.json`, and asserts exit 1 and
    the absence of `no configuration to check`
- Finding: Fixed. The finding now runs in the repo FR-006b is written for.
- Why it matters: That repo is warned before its branches are held at
  brainstorm.
- Suggested response: None.
- Corroborated by: requirements and traceability, adversarial implementation
  and verification

### PR-023: The spec says turned-off checks read done, and the plan reads them as skipped

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md` FR-006a: both checks "MUST both read done"; US5 acceptance 3:
    "both checks read done and say the setting turned them off"
  - `plan.md` items 5.2 and 6.3, `data-model.md` state 2, and
    `contracts/cli.md §checks turned off`: `skipped`, drawn `–`
- Finding: Both advance the pipeline, and `skipped` is the better state for a
  check that didn't run. But the plan doesn't label the departure the way R7
  labels its departure from FR-007, and a test written from the spec would
  assert `done`.
- Why it matters: It is a small guess. The revision for PR-021 changed how
  these rows carry their text and kept `skipped`, so the departure still
  stands unlabelled.
- Suggested response: Label it in R10 as a departure from FR-006a's wording,
  or change the spec to say "pass".
- Corroborated by: requirements and traceability

### PR-024: R10 says a held architecture check has no way out without the new key, and a claim is one

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `research.md §R10`: "with the folder outside the project, a held
    architecture check would have no way out"; Complexity Tracking repeats it
  - `_declared.load` includes every built-in pass, so
    `wfctl step none brainstorm.architecture --reason "…"` is accepted
  - `_pass_states` reads claims first, and `_step_claims` reads them from disk
    under the arch root, not through git
- Finding: A claim releases the architecture check in a repo git can't see, as
  it does the software design check. The key is still the better answer, for
  the reason R10 gives for the other check: one claim per branch, forever. A
  claim written outside the project is also never committed, so the PR
  reviewer the spec relies on never sees it.
- Why it matters: The rationale for the new key should rest on a true
  premise, and the uncommitted-claim point is a better reason than the one
  given.
- Suggested response: Reword R10 and the Complexity Tracking row to say a
  claim is possible on both checks but costs one per branch, and isn't
  committed where the reviewer would read it.
- Corroborated by: single reviewer

### PR-025: Item 6.5 misdescribes `brainstorm`'s own reading in both new states

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `plan.md §_evidence.py` item 6.5: "A held branch where git can't answer
    reads `in_progress`, the same as any other held branch"
  - `_evidence.py` `brainstorm`: with no `design.md` and no `spec.md`, a
    non-`None` answer from `_architecture_answered` falls through to
    `pending`. So with git unable to answer and no `design.md`, the step reads
    `pending` and cascades. Only with `design.md` does the roll-up make it
    `in_progress`
  - With the checks off, item 6.1 makes `_architecture_answered` return `None`,
    so `brainstorm` reads its own `done` for a branch with nothing in it. The
    step then reads `in_progress` on `design-doc` and never reads `pending`
  - Item 6.3 doesn't say whether `brainstorm_architecture` checks the setting
    before or after the `spec.md` escape, which decides whether a branch past
    specify with the checks off still gets the drawing warning
- Finding: The behaviour in the first case is right, since it matches an
  in-tree branch with no answer. The sentence describing it is wrong. The
  second case is a change for an in-tree repo that turns the checks off, and
  today's out-of-tree behaviour for one that doesn't. Neither is stated.
- Why it matters: An implementer who reads 6.5 and tests it with no
  `design.md` sees `pending`, and may "fix" `brainstorm` to match the
  sentence.
- Suggested response: Rewrite 6.5 for both cases, say whether a checks-off
  branch with nothing in it reading `in_progress` is intended, and fix the
  order in 6.3.
- Corroborated by: adversarial implementation and verification

### PR-026: R10's list of inverted tests misses two whose premise is the old behaviour

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - Measured in a scratch copy with only the source changed to
    `"repo-declared"`, five tests fail that pass unchanged:
    `test_design_gate_drawing.py`
    `test_a_failing_record_under_an_arch_root_outside_the_repository_is_not_judged`
    (line 584, before the line-601 section R10 names),
    `test_with_no_trunk_a_committed_failing_record_finishes_the_step_and_says_so`,
    `test_with_no_trunk_an_arch_root_outside_the_repository_carries_no_unchecked_line`,
    `test_pipeline_state_names.py`
    `test_a_step_with_its_artifact_present_is_done` and
    `test_the_architecture_pass_and_the_design_doc_pass_read_independently`,
    and `test_pipeline_commands.py`
    `test_an_unreadable_arch_root_advances_the_design_step`
  - The last is documented as "The ambient rule end to end"
  - `_evidence.py:161-167`, the `DRAWINGS_UNCHECKED` comment, argues the pass
    finishes because "holding the branch on a check that cannot run asks the
    user for a trunk they may have no reason to create", which item 6.4
    doesn't list for rewording
- Finding: The suite will find all of these, as R10 says. Two of them need a
  decision rather than a flipped assertion. The line-584 test and the
  `test_pipeline_commands.py` test are each the only end-to-end proof of a
  rule this change narrows. Deleting them loses the proof, and flipping them
  silently leaves a docstring that says the opposite.
- Why it matters: An implementer under a red suite will take the quickest
  edit.
- Suggested response: Name both in R10. Rewrite the
  `test_pipeline_commands.py` test to assert the hold and the remedy, and
  point "the ambient rule end to end" at `decompose`, the remaining ambient
  caller. Add the `DRAWINGS_UNCHECKED` comment to item 6.4.
- Corroborated by: single reviewer

### PR-027: The quickstart has no step for User Story 5

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `spec.md` US5's Independent Test is an end-to-end check: a repo with an
    outside architecture folder is held, then set to `"off"` and released
  - `quickstart.md` is unchanged, and every step uses a repo with a trunk and
    an in-tree root
- Finding: Tests 7, 8, 8a and 8b cover US5 in the suite. The only end-to-end
  check doesn't, so the remedy text and `check config` finding are never seen
  as a user would see them.
- Why it matters: The remedy text is the user's only guide out of the new
  hold. PR-022 showed how easily the `check config` half could go green in
  the case that matters, and only a run in a repo with no `wfctl.json` would
  show it as the user meets it.
- Suggested response: Add a step that sets `WFCTL_ARCH_DIR` outside the scratch
  repo, runs `$WFCTL check config` and `$WFCTL status`, then writes
  `{ "design_record_checks": "off" }` and runs `$WFCTL status --all`.
- Corroborated by: single reviewer

### PR-028: R10 still names the source-scanning test as the guard that test 8d says it can't be

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `research.md §R10` item 3: `test_every_inconclusive_verdict_goes_through_blocks`
    "should pass unchanged, and it's the check that the new reader doesn't
    skip the rule"
  - `plan.md` test 8d: that test "can't show that, since it only checks that
    `blocks` is called somewhere in the function, and a reader that returned
    early for `inconclusive` would still pass it"
  - `tests/test_evidence.py:128-164` confirms the plan: the test collects the
    names of functions whose body contains the literal `"inconclusive"` and
    those that call `blocks`, and asserts the first set is inside the second.
    It doesn't look at order
- Finding: The plan revision corrected the claim in the plan and left it
  standing in research, so the two planning artifacts now disagree about which
  test guards the rule.
- Why it matters: An implementer who reads R10 first may treat test 8d as
  redundant and drop it, which brings back the gap PR-020 closed. It forces no
  behavioural guess, since the plan is explicit.
- Suggested response: Reword R10 item 3 to say the source-scanning test still
  passes and still catches a reader that never calls `blocks`, and that test
  8d is what checks the order.
- Corroborated by: architecture and boundaries, adversarial implementation and
  verification

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §_pipeline.py item 2; research R1 | covered |
| FR-002 | plan.md §_evidence.py item 5.3; tests 2, 3, 11 | covered |
| FR-003 | plan.md §_evidence.py items 1, 2, 5.5; contracts/cli.md; test 1 | covered |
| FR-004 | research R5; test 5 | covered |
| FR-005 | plan.md §_evidence.py item 5.1; test 6 | covered |
| FR-006 | plan.md §_evidence.py items 3, 5.4, 5.5, 6; tests 7, 8, 8c, 8d | covered; PR-025, PR-028 |
| FR-006a | plan.md §_paths.py item 2; §_evidence.py items 4, 5.2, 6.1, 6.3; test 8a | covered; PR-023 |
| FR-006b | plan.md §_paths.py item 3; §cli.py check_config_cmd; test 8b | covered |
| FR-007 | plan.md §cli.py status_cmd; research R7; test 9 | covered; PR-017 |
| FR-008 | plan.md §design-levels; test 13 | covered |
| FR-009 | plan.md §speckit-brainstorm items 1 and 2; test 13 | covered |
| FR-009a | plan.md §speckit-brainstorm item 3; §allowed-tools; test 14 | covered; PR-015, PR-016 |
| FR-010 | plan.md §software-design-decisions; test 13 | covered |
| FR-011 | plan.md §changes/648.change.md; research R8; `wfctl verify` | covered |
| SC-001 | tests 1 to 5 and 12 | covered |
| SC-002 | tests 2, 3, and 5 | covered |
| SC-003 | test 6 | covered |
| SC-004 | test 13; quickstart.md step 7 | covered; PR-018 |
| SC-005 | tests 7, 8, 8a, 8b, 8c, 8d | covered; PR-027 |
| US5 | tests 7, 8, 8a, 8b; docs/reference.md | covered in the suite; PR-027 |
| Edge: git can't answer, three cases | plan.md §_evidence.py items 5.4, 5.5 and 6; tests 7, 8, 8d | covered; the failing-git-command case has no test, which is reasonable |
| Edge: declared `software-design` | research R6; test 10 | covered |
| Edge: claim and record together | `_pass_states` reads the claim first | covered by existing code; no test named |
| Assumption: other git checks still proceed | research R10 (`decompose` stays `ambient`) | covered |
| Validation Strategy | plan.md §Technical Context | covered |

## Assumptions challenged

- `blocks` is reached by test 8d's patch. Verified: both readers sit in
  `_evidence.py` and call the module-level `blocks` by name, and nothing
  imports it under another name into that module.
- With `blocks` patched to false, both checks read done where git can't
  answer. Verified for the architecture check through `_judge_drawings`,
  which reads `done` both with no trunk (with `DRAWINGS_UNCHECKED` as display)
  and with the arch root outside the tree. The software design reader returns
  `done` at item 5.4 by construction.
- A `display`-only skipped reading neither warns nor shows without `--all`.
  Verified against `collect_warnings` and `cli.py:821`.
- Printing the outside-the-tree problem under `✗ wfctl.json:` when no
  `wfctl.json` exists names a file that isn't there. The plan says why: the
  fix is a key in that file. That is a judgement about wording, not a gap.
- Every way into the new hold has a way out, as the earlier review found. The
  revision didn't change the hold's entry conditions.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The revision states the reason for each change beside it (why `display`, why
  `blocks` first, why before the early return), so an implementer doesn't
  have to rediscover the code behaviour each one depends on.
- Test 8d checks the rule by behaviour rather than by source shape, and the
  plan says plainly what the existing source-scanning test can't catch.
- The hold comes with its way out written into the remedy, and a typo in the
  new setting reads as on, so a mistake never turns a check off.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
