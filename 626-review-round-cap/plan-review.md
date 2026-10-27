# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | ce505bac67e4a2b08143bd8e6d84e243134d8f63 | technical strategy |
| spec.md | 81217e14d8637b1611a0333ec7c6e097b1091b4c | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | aaabe0549f5adeaac928dff090cde4be9bddc65d | design-record index |
| research.md | 0c5e71c50ddbb64eadf125f19685e2774c5e8c53 | planning evidence |
| data-model.md | 142a067dd4e8d84ec07dca945d76fd2b597e8d9d | planning evidence |
| quickstart.md | 189f41bfae57580bc1643a543ea4701da2ae35d9 | planning evidence |
| contracts/cli.md | 6d9c8bd7ac52a070b5f69d42893d5416d1a34f93 | planning evidence |
| docs/architecture/review-round-count.md | 3c8019a211b55887fdd3a64310564638c0c7173c | accepted architecture record |
| docs/architecture/review-round-cap.md | 666b350e7b510f98f6fb6f5bc6f7218c13817631 | accepted architecture record |
| docs/architecture/design/642-commit-range-takes-judged-branch.md | b5dff1df8d6f4b6472f244ad198cf71a142cd580 | design record the trunk read sits beside |
| docs/architecture/design/642-origin-head-trusted-on-full-fetch.md | 241b285ccc6db8375365d9df6eda744a71857604 | design record the trunk read sits beside |
| plan-review.plan.md | 7b2b330905348dc22992528b7c1f3c7e0c67eb84 | base of this re-review |

## Review scope

- Re-review: the earlier report exists, the plan copy exists, and the copy's
  identity equals the earlier report's `plan.md` row.
- Changed since the earlier report, from the plan diff: `§Technical Context`
  Performance Goals, `§Constitution Check` release note item, `§Code changes,
  wfctl/_review.py` items 4 and 5, and `§Project Structure` (the second release
  note, the two #642 records, and the trunk tests that keep passing). These
  were reviewed together with the parts that refer to them: `§Summary`,
  `§wfctl/cli.py` item 1, `§AGENTS.md "Declaring reviewers"`, and every
  requirement trace row below.
- Inputs named as changed by the invoking command, each re-read in full with
  the whole of `plan.md` reviewed against it: `spec.md`, `research.md`,
  `data-model.md`, `quickstart.md`, and `contracts/cli.md`. The other input
  rows of the earlier report match their files now.
- Design records: none listed in `design.md`, which records no level-3
  decision. The two #642 records are read because the plan changes the
  function both of them decide (`trunk_refs`) and now adds a Log line to each.
- Lenses: requirements and traceability, architecture and boundaries
  (dependency and scope reported here), and adversarial implementation and
  verification (verification and risk reported here).
- Conditional lenses: security and reliability applied. The cap is a control
  the user places on the agent, and the trunk read decides which commits the
  PR check and `review sign-off` can see.
- Existing code inspected, to check claims the revision makes:
  `wfctl/_review.py` (`TRUNK_MESSAGE`, `NoTrunk`, `_git`, `trunk_refs` and its
  docstring, `_refuse_a_single_branch_clone`, `commit_range`),
  `wfctl/_paths.py` (`declared_trunk`, `_resolve_declared`, `trunk_branch`),
  `wfctl/_review_gate.py` (`_judge`), `wfctl/cli.py` (`review_start_cmd`,
  `review_sign_off_cmd`), `.github/scripts/check_release_note.py` (two notes
  for one issue), the `review_repo` fixture, and the trunk tests named in the
  plan:
  `tests/test_review.py::test_range_with_no_trunk_branch_names_the_trunk_key`,
  `tests/test_review_cli.py::test_start_with_no_trunk_branch_names_the_trunk_key`,
  `tests/test_review_cli.py::test_start_refuses_a_trunk_that_is_the_branch_under_review`,
  `tests/test_review_gate.py::test_no_trunk_branch_gives_the_error_refusal`,
  and `tests/test_review_gate.py::test_a_trunk_that_is_the_judged_branch_is_refused`.
  `git symbolic-ref --quiet --short` exit codes were checked in a scratch
  repository.
- Reviewers: the lenses above, run in sequence by one agent in a fresh context.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 2

No BLOCKER findings identified in this review. All seven findings the earlier
review left open are fixed. A working-tree `trunk` the clone lacks now refuses
as today, so `review start`, `review sign-off`, and the guard agree on it, and
the two existing tests stand. A default-branch `trunk` the clone lacks has its
own row, and its messages name `wfctl.json on origin/<default>`.

The two open findings are small:

1. PR-023: a branch that sets `trunk` to its own name gets a warning from
   `review start`, but the guard refuses its PR. That is the disagreement R11
   step 5 says it avoids.
2. PR-024: quickstart step 10 expects `review start` to list the branch's
   commits, and at that point in the sequence it prints outcome 3 instead.

## Findings

### PR-001: Outcome 3 checks the head, but the guard checks each commit

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Code changes, wfctl/_review.py` item 8: at the cap, `start`
    checks whether the sign-off covers every commit in the group's range.
  - `spec.md §FR-002`, `§FR-004`, `research.md §R4`, and `data-model.md
    §Sign-off` say the same.
- Finding: The earlier plan checked whether the sign-off covered the head.
  After a clean trunk merge, that refused a change the guard allowed.
- Why it matters: The rule matches the guard's.
- Suggested response: Fixed in an earlier revision, and still holds.
- Corroborated by: adversarial implementation and verification; architecture
  and boundaries

### PR-002: The branch's `trunk` key chooses where the cap is read

- Priority: MAJOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `research.md §R11`, `spec.md §FR-017`, `plan.md §wfctl/_review.py` items 4
    and 5: reviews read the trunk from `wfctl.json` on the default branch.
- Finding: The earlier plan left open whether the gap was accepted or closed.
- Why it matters: An implementer doesn't choose the record's scope.
- Suggested response: Fixed in an earlier revision, and still holds.
- Corroborated by: security and reliability; architecture and boundaries

### PR-003: Outcome 3's line has no source for its count

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §wfctl/_review.py` item 9 and `data-model.md §Types in code`:
    `Started.rounds` and `Started.sign_off`.
  - `contracts/cli.md §Outcome 3`: lines for at the cap, past the cap, and a
    cap of 0.
- Finding: The count, the check order, and the above-cap and cap-0 wordings
  were missing.
- Why it matters: The test that pins the line has a source for every value.
- Suggested response: Fixed in an earlier revision, and still holds.
- Corroborated by: adversarial implementation and verification

### PR-004: The plan doesn't name the test that pins the old Step 1 text

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Project Structure, tests/`: names
    `test_the_panel_step_stops_after_three_rounds_to_ask_for_a_sign_off` for
    FR-013.
- Finding: The rewrite would have failed a test the plan didn't list.
- Why it matters: Both skill rewrites have a named test.
- Suggested response: Fixed in an earlier revision, and still holds.
- Corroborated by: requirements and traceability

### PR-005: The plan names the guard's git timeout, not the one `review start` uses

- Priority: MINOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence:
  - `plan.md §wfctl/cli.py` item 1: both calls get `timeout=None`, matching
    `review_start_cmd`, which passes none today.
- Finding: The value `review start` passes was left open.
- Why it matters: The value is stated and matches the code.
- Suggested response: Fixed in an earlier revision, and still holds.
- Corroborated by: single lens

### PR-006: No artifact says who parses the trunk's JSON

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §wfctl/_review.py` items 2 and 3 and `research.md §R2`:
    `_read_config_at` parses the file for both readers.
- Finding: The JSON step and the non-object `review` case had no owner.
- Why it matters: The two readers share one parser.
- Suggested response: Fixed in an earlier revision, and still holds.
- Corroborated by: single lens

### PR-007: The quickstart doesn't say how a scratch clone runs this checkout's wfctl

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `quickstart.md` opening: defines `wf()` as `uv run --project "$WT" wfctl`.
- Finding: The end-to-end check would have run another wfctl.
- Why it matters: SC-001 is checked against this worktree's code.
- Suggested response: Fixed in an earlier revision, and still holds.
- Corroborated by: single lens

### PR-008: Artifacts written before clarify disagree with the plan

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Summary`: names the three out-of-date lines in `design.md` and
    says to follow the plan.
- Finding: `design.md` carried pre-clarify wording, and the plan didn't say
  so.
- Why it matters: An implementer reading `design.md` is told which source
  wins.
- Suggested response: Fixed in an earlier revision, and still holds.
- Corroborated by: requirements and traceability

### PR-009: The trunk-change refusal sends the user to a sign-off the same check refuses

- Priority: BLOCKER
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R11`: a branch that names a different trunk the clone has
    gets a `⚠` warning, and the review goes on against the default branch's
    trunk. Its alternatives explain why the refusal and a sign-off exemption
    were both dropped.
  - `plan.md §Project Structure`: "review sign-off succeeds on a branch that
    names another trunk".
- Finding: The earlier plan refused a trunk change inside `trunk_refs`, which
  also refused the sign-off the refusal asked for.
- Why it matters: The user has a route past every trunk outcome. The new
  refusals each name a fix.
- Suggested response: Fixed in an earlier revision, and still holds. PR-023
  is a narrower case of the same shape.
- Corroborated by: security and reliability; adversarial implementation and
  verification

### PR-010: With no `origin/HEAD`, a branch edit still chooses where the cap is read

- Priority: MAJOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `review-round-cap.md §Consequences`, last bullet, `research.md §R11`, and
    `plan.md §Constitution Check` ownership item 2 all state the same known
    limit and name the three layouts.
- Finding: The earlier plan described the gap as closed everywhere.
- Why it matters: The implementer doesn't decide the record's scope.
- Suggested response: Fixed in an earlier revision, and still holds.
- Corroborated by: security and reliability; architecture and boundaries

### PR-011: How the check reads the default branch, and what it does when that fails, is unspecified

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R11`: five named steps and a case table, and
    `data-model.md §Review trunk` repeats the table.
- Finding: The read, the failure cases, the order, and who prints what were
  left to the implementer.
- Why it matters: The wording a pinned test asserts comes from the artifacts.
- Suggested response: Fixed in an earlier revision. The edges it left open,
  PR-016 to PR-018, are fixed in this one.
- Corroborated by: adversarial implementation and verification

### PR-012: Repositories the refusal catches without an agent edit aren't named to users

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §AGENTS.md "Declaring reviewers"`: the second paragraph tells a
    repository whose trunk isn't its default branch to declare it there.
  - `plan.md §Project Structure`: `changes/626.change.md` carries the same
    upgrade step.
- Finding: Nothing told a user about the upgrade step.
- Why it matters: The docs and the release note name the fix.
- Suggested response: Fixed in an earlier revision, and still holds.
- Corroborated by: architecture and boundaries

### PR-013: Some wording still says the sign-off covers the head

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Summary`, `contracts/cli.md §Outcome 3`, `spec.md §User Story 1`
    outcome 3, and `quickstart.md` steps 6 and 7 name the signed-off commit.
- Finding: The outcome 3 line named the head, which is false after a clean
  merge.
- Why it matters: The pinned line is true in that case.
- Suggested response: Fixed in an earlier revision, and still holds.
- Corroborated by: requirements and traceability

### PR-014: FR-012 and FR-017 disagree, and FR-017's merge refusal isn't observable from the `main` checkout

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `spec.md §FR-012` and `§FR-017` no longer contradict each other, and
    `plan.md §Project Structure, tests/test_review_gate.py` covers the `main`
    checkout.
- Finding: FR-012 and FR-017 contradicted each other, and the `main` checkout
  path had no test.
- Why it matters: A test written from the spec expects what the design does.
- Suggested response: Fixed in an earlier revision, and still holds.
- Corroborated by: requirements and traceability

### PR-015: The performance line counts the git calls from before the trunk check

- Priority: MINOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence:
  - `plan.md §Technical Context` Performance Goals and `research.md §R9`: up
    to seven git calls per `trunk_refs` call when the branch declares a
    different trunk, about 23 in `review start`, and up to 21 in the guard
    with three groups.
- Finding: The line predated the trunk read.
- Why it matters: The count is stated for both callers, and it now includes
  the two `show-ref` calls `_resolve_declared` makes for a branch's own trunk.
- Suggested response: Fixed, and the count was updated for PR-016's fix.
- Corroborated by: single lens

### PR-016: A branch that names a trunk the clone doesn't have falls between two rows of R11

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R11` step 5 and case table: "The working tree names a trunk
    the clone doesn't have | refused with `NoTrunk`, as today", and the same
    for a working-tree value that isn't a branch name. The paragraph after
    the steps gives the reason: `_judge` raises `NoTrunk` for the same state.
  - `data-model.md §Review trunk`: the same row.
  - `plan.md §wfctl/_review.py` item 4: "still raises `NoTrunk`, as today, so
    `review start` and the guard's `_judge` agree".
  - `plan.md §Project Structure`:
    `test_range_with_no_trunk_branch_names_the_trunk_key`,
    `test_start_with_no_trunk_branch_names_the_trunk_key`, and
    `test_no_trunk_branch_gives_the_error_refusal` keep passing unchanged.
    `contracts/cli.md §No trunk` keeps today's wording for this case.
  - `spec.md §FR-017`: names only the readers that decide which commits a
    review covers, and says the guard's checks on where a command may run
    keep reading the working tree.
  - Code: `_paths.trunk_branch` answers None for a declared name that
    `_resolve_declared` can't find, and `_judge` raises `NoTrunk` for it
    before it calls `unreviewed`. The `review_repo` fixture writes `"trunk":
    "nope"` untracked, with `origin/HEAD` set and a full fetch, so the tests
    run on the default-branch path, where step 5 now refuses.
- Finding: The earlier plan left this case between two rows, and either
  reading broke a test or left the guard and `review start` disagreeing.
- Why it matters: The case has one answer, and it matches the guard.
- Suggested response: Fixed by `research.md §R11` step 5, `plan.md
  §wfctl/_review.py` item 4, `spec.md §FR-017`, and the test list.
- Corroborated by: adversarial implementation and verification; requirements
  and traceability

### PR-017: A default-branch `trunk` that names a branch the clone lacks has no row, and its message points at the wrong file

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `research.md §R11` case table: "`trunk` is a branch name the clone
    doesn't have … | refused with `NoTrunk`, naming `wfctl.json on
    origin/main`". The paragraph after the table says why it refuses rather
    than warns.
  - `plan.md §wfctl/_review.py` item 5: on the default-branch path, the
    same-name and `NoTrunk` messages name `wfctl.json on origin/<default>`.
  - `contracts/cli.md §No trunk`: both lines, and that the fallback path
    keeps today's wording.
  - `data-model.md §Types in code`: `ReviewTrunk.source` carries the ref the
    messages name.
- Finding: The case had no row, and its message sent the user to the working
  tree's file.
- Why it matters: The message names the file wfctl read.
- Suggested response: Fixed by the sections above.
- Corroborated by: adversarial implementation and verification

### PR-018: R11's first git command can't tell "no `origin/HEAD`" from a git failure

- Priority: MINOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence:
  - `research.md §R11` step 1 and `plan.md §wfctl/_review.py` item 4: `git
    symbolic-ref --quiet --short refs/remotes/origin/HEAD` through `_git` with
    `answers=(0, 1)`.
  - Checked in a scratch repository: with `--quiet`, a missing `origin/HEAD`
    exits 1, a dangling one exits 0 and prints `origin/main`, and a git
    failure exits 128. Without `--quiet`, the missing case exits 128.
- Finding: The earlier command exited 128 for both cases.
- Why it matters: A missing `origin/HEAD` takes the fallback, and a failure
  still raises.
- Suggested response: Fixed by the sections above.
- Corroborated by: single lens

### PR-019: The #642 records and the `trunk_refs` docstring still say the branch's declaration decides the trunk

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §wfctl/_review.py` item 5: rewrite the `trunk_refs` docstring to
    say the trunk comes from `review_trunk`, and that a declared trunk decides
    only on the fallback path. `research.md §R11` says the same.
  - `plan.md §Project Structure`: a Log line in each #642 record saying #626
    moved trunk resolution for reviews into `review_trunk`. Both records end
    in a `## Log` section, so the line has a place to go.
- Finding: The docstring and both records would have kept stating the old
  rule.
- Why it matters: The next reader of `trunk_refs` or either record is told
  where the rule moved.
- Suggested response: Fixed by the sections above.
- Corroborated by: architecture and boundaries

### PR-020: research.md R4, R5, and R10 trail the plan

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R4`: `_covered_by_sign_off` returns the signed-off commit,
    or None, and a function, matching `plan.md §wfctl/_review.py` item 6.
  - `research.md §R5`: four steps, with `review_trunk` as step 2, matching
    `plan.md §wfctl/cli.py` item 1.
  - `research.md §R10` items 4 and 5: the trunk paragraph and the two release
    notes, matching `plan.md §AGENTS.md` and `§Project Structure`.
- Finding: Three research entries described the plan before the previous
  revision.
- Why it matters: An implementer reading research alone builds what the plan
  says.
- Suggested response: Fixed by the sections above.
- Corroborated by: requirements and traceability

### PR-021: The release note is filed as an addition, but the change alters behaviour users rely on

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `spec.md §FR-016`, `plan.md §Constitution Check`, `§Project Structure`,
    and `research.md §R10` item 5: `changes/626.addition.md` for the new key
    and the refusal, and `changes/626.change.md` for the round order and the
    trunk read, with the upgrade step.
  - `.github/scripts/check_release_note.py`: the note pattern takes any
    number of notes per issue, and `changes/` already holds two notes for
    #604.
- Finding: The behaviour changes and the upgrade step would have landed under
  "Additions".
- Why it matters: The upgrade step is filed where an existing user looks.
- Suggested response: Fixed by the sections above.
- Corroborated by: single lens

### PR-022: The quickstart's scratch clone may have no `origin/HEAD`, so step 10 can show the fallback

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `quickstart.md` step 2: clone with `git clone` from a remote that already
    has commits on `main`, check `git symbolic-ref refs/remotes/origin/HEAD`,
    and run `git remote set-head origin --auto` when it has none.
- Finding: Step 2 didn't say how to make the clone.
- Why it matters: Step 10 checks the default-branch read rather than the
  fallback.
- Suggested response: Fixed by step 2. The check line prints a `fatal:` error
  rather than nothing when `origin/HEAD` is missing, which a person running
  it will still read correctly. PR-024 is a separate gap in step 10.
- Corroborated by: single lens

### PR-023: A branch that sets `trunk` to its own name gets a warning from `review start` and a refusal from the guard

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `spec.md §FR-017`: "When the working tree names a different trunk that
    the clone has, `review start` MUST print a `⚠` warning and go on, and
    MUST NOT refuse." The branch under review is a branch the clone has.
  - `plan.md §Project Structure, tests/test_review_cli.py`:
    `test_start_refuses_a_trunk_that_is_the_branch_under_review` drops
    `origin/HEAD`, and a new test pins the warning and the review against
    `main` when `origin/HEAD` is set.
  - `contracts/cli.md §Warnings`: the warning ends "until the change merges".
  - `wfctl/_review_gate.py`, `_judge`: reads `_paths.trunk_branch`, which
    returns the working tree's declaration, and refuses when it equals the
    judged branch, before it calls `unreviewed`.
    `tests/test_review_gate.py::test_a_trunk_that_is_the_judged_branch_is_refused`
    pins that refusal, and the plan doesn't change it.
  - `research.md §R11`, the paragraph after step 5: a missing branch refuses
    rather than warns, "because the guard refuses the same branch. … A
    warning in `review start` would tell the user the change can merge, and
    the guard would then refuse the PR." `plan.md §wfctl/_review.py` item 4
    gives the same reason.
- Finding: With `origin/HEAD` set, a branch whose `wfctl.json` says
  `"trunk": "637-x"` on branch `637-x` gets the mismatch warning. Then
  `review start` runs against `main`, and `review sign-off` succeeds. The
  guard then refuses `gh pr create` with "the trunk branch is 637-x, the
  branch this command acts on; check trunk in wfctl.json". A sign-off doesn't
  get past that refusal, since it comes before `unreviewed`. This is the
  disagreement R11's step 5 rationale says the plan avoids, in the one
  "different trunk the clone has" case where `_judge` refuses.
- Why it matters: No commit is hidden, since the guard refuses and `review
  start` measures against `main`. But an unattended agent can spend rounds
  against the cap on a branch that can't open a PR, and the warning tells it
  the change can merge. The fix is to revert the edit, which is a new commit
  and costs every group another round.
- Suggested response: Pick one and write it into R11's table and FR-017:
  1. Refuse in `trunk_refs` when the working tree's declaration names the
     branch under review, with today's same-name message. `trunk_refs` already
     has `branch`, and this keeps today's test unchanged.
  2. Keep the warning, and add a row to R11's table saying the guard refuses
     this branch's PR, so the step 5 rationale no longer claims full agreement.
- Corroborated by: adversarial implementation and verification; security and
  reliability

### PR-024: Quickstart step 10 expects a commit list that `review start` doesn't print at that point

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `quickstart.md` step 10: `wf review start security` "prints the trunk
    warning, still reads the cap of 3 from `origin/main`, and still lists this
    branch's commits since `main`".
  - `quickstart.md` steps 3 to 9: security has 3 runs, step 4's refusal wrote
    none, the step 5 sign-off covers every commit in the range (step 7 says so
    after the clean merge), and steps 9 and 10 make only uncommitted edits to
    `wfctl.json`.
  - `data-model.md §review start outcomes` and `contracts/cli.md §Outcome 3`:
    at the cap with a sign-off covering the range, `review start` prints the
    outcome 3 line, with no commit count or list.
- Finding: At step 10, the command prints the trunk warning and "security has
  run 3 of 3 rounds; the sign-off at <sha> covers every commit left to
  review". The cap of 3 shows in that line. The commit range doesn't show
  anywhere, so the third expectation can't be checked from this output.
- Why it matters: A person following the quickstart either can't confirm the
  expectation, or reads outcome 3 as a failure. The range is covered by the
  `tests/test_review.py` case for a branch that names another trunk, so only
  the manual check is affected.
- Suggested response: Replace the third clause with what the command prints
  (the outcome 3 line, reading `3 of 3`, where a read of `loose` would start
  run 004 as `round 4 of 9`). Alternatively, check the range with the guard
  command from step 8.
- Corroborated by: single lens

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §_review.py items 1, 8; research.md §R3 | covered |
| FR-002 | plan.md §_review.py item 8; research.md §R4; data-model.md §outcomes | covered |
| FR-003 | plan.md §_review.py item 7, §cli.py item 3; research.md §R6 | covered |
| FR-004 | plan.md §_review.py items 6, 8; contracts/cli.md §Outcome 3 | covered |
| FR-005 | plan.md §cli.py item 5; research.md §R8 | covered |
| FR-006 | plan.md §_review_config.py items 1 - 3; research.md §R1 | covered |
| FR-007 | plan.md §_review.py items 2, 3; research.md §R2 | covered |
| FR-008 | research.md §R2; data-model.md §Round cap | covered |
| FR-009 | plan.md §_review.py item 3; data-model.md §Round cap; contracts/cli.md §Warnings | covered |
| FR-010 | plan.md §cli.py item 1; research.md §R5 | covered |
| FR-011 | research.md §R1, §R5 | covered |
| FR-012 | plan.md §Summary, §_review.py item 5; research.md §R9 | covered |
| FR-013 | plan.md §opening-a-change; tests/test_opening_a_change_panel.py | covered |
| FR-014 | plan.md §fanning-out-code-review; tests/test_review_fanout_skill.py | covered |
| FR-015 | plan.md §AGENTS.md | covered |
| FR-016 | plan.md §Project Structure; research.md §R10 item 5 | covered |
| FR-017 | plan.md §_review.py items 4, 5; research.md §R11; contracts/cli.md | covered; PR-023 on a branch that names itself |
| SC-001 | tests/test_review.py; quickstart.md steps 3, 4 | covered |
| SC-002 | research.md §R3 | covered |
| SC-003 | research.md §R2, §R11; quickstart.md steps 9, 10 | covered where `origin/HEAD` is trusted, a limit the cap record states; PR-024 on step 10 |
| SC-004 | plan.md §opening-a-change Step 1 | covered by reading the rewritten text |
| SC-005 | research.md §R2; data-model.md §Round cap | covered |

## Assumptions challenged

- `review start` and the guard agree on every working-tree `trunk`. Holds for
  a name the clone lacks and for a value that isn't a branch name. Doesn't
  hold for a name equal to the branch under review (PR-023).
- The guard's code doesn't change while the `NoTrunk` message gains a branch
  name and a source. Holds only if `NoTrunk` keeps a form that takes no
  arguments, since `_judge` calls `_review.NoTrunk()`. The plan doesn't say
  so, but mypy and `test_no_trunk_branch_gives_the_error_refusal`, which the
  plan lists as unchanged, both fail on a required argument, so the suite
  finds it.
- A default-branch `trunk` the clone lacks is usually an unfetched branch.
  Plausible, but R11's own example is a deleted `develop`, which `git fetch`
  doesn't fix. In that case every review command and the guard refuse on
  every branch, including the branch that fixes `trunk` on the default
  branch. The guard reports `NoTrunk` as a failed check, which `AGENTS.md`
  already routes to the user, who can open and merge the fix from their own
  terminal. The route exists, and the plan accepts the cost for the reason
  R11 gives.
- `review_repo`'s untracked `"trunk": "nope"` runs on the default-branch path.
  Checked: `git remote add` writes a refspec that fetches every branch, and
  the fixture sets `origin/HEAD` by hand, so R11 steps 1 to 3 pass, and step 5
  raises `NoTrunk` with today's wording, as the two tests expect.
- Two release notes for one issue pass the check. Checked: the pattern in
  `check_release_note.py` matches each, and #604 already has two.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- R11 step 5 says why a missing working-tree trunk refuses, and names the two
  tests that pin it, so the next editor doesn't turn it into a warning.
- R11 step 1 says why `--quiet` is there, with the exit codes, so it isn't
  dropped as noise.
- The plan lists the existing tests that must keep passing unchanged, not
  only the ones it adds or edits, which is how a behaviour change shows up as
  a red test rather than a silent one.
- `ReviewTrunk.source` lets each refusal name the file wfctl read, rather than
  the one the user would otherwise edit.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
