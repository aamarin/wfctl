# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 06cc9fce3aa12eca6167ac5b3f034b8157d64e89 | technical strategy |
| spec.md | 36130e83efd7cf26e04864e3fdf4ae84c899c41d | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | a300e080b4678211c03622c9cc526026ac136c85 | design-record index |
| docs/architecture/design/627-unreviewed-takes-coverage.md | 6952a2a5ce10f93a970695db193bacb0a5ffa297 | design record |
| docs/architecture/design/627-review-note-line-per-event.md | 2899b52b14cad409fc8524a1c28eb34f789988a0 | design record |
| docs/architecture/design/627-guard-blocks-note-writes.md | 666b18a2720685bbb6174ea35aa39ea7d69b17ac | design record |
| docs/architecture/review-record-in-git-notes.md | 00389d02a47676c5a0efaa0f649ee16a4fd4ff05 | accepted level-2 record the plan implements |
| docs/architecture/review-covers-unreviewed-commits.md | 24c4b0e1c20ef1fa397c6e861eaf907785b28769 | accepted level-2 record for the range rules |
| research.md | 59cf1651e2f87ee14be4b63a276d06f15b2326f9 | planning evidence |
| data-model.md | 469957bb0c12a9250c332ad93f7d854cb9bca7e9 | planning evidence |
| quickstart.md | a563a80554c1892fdc4c411fb301657f43e31835 | planning evidence |
| contracts/cli.md | 03c3df17467cd06fed7c1c661930a09a0db79ff0 | contract |
| contracts/review-job.md | c18409e6a0dda3726e7c4a86832605ad160d3369 | contract |
| contracts/review-note.md | dfdbb4b3891a514c88396ff9d958191cc203a765 | contract |
| checklists/requirements.md | f0f311123f87812b1660c822ee055effe594c3f7 | requirements-quality checklist |
| plan-review.plan.md | ac694568f3e22398d13e703fe85b79db0ce4e3cd | base of this re-review |

## Review scope

- Re-review: the earlier report and the plan copy exist, and the copy's
  identity equals the earlier report's `plan.md` row
- Changed since the earlier report: `plan.md §Summary` (the local-passes
  sentence narrowed to a current `origin/main`), `§Constitution Check` (the
  re-check line names R14), and `§Project Structure` (`_review_config.py`, the
  `_review.py`, `_review_gate.py`, and `cli.py` lines, the new and widened test
  lines, and the `AGENTS.md` recovery line), reviewed together with the
  requirement trace rows that point into them
- Inputs that changed besides `plan.md`, each re-read in full with the whole
  plan reviewed against it: `spec.md`, `research.md`, `quickstart.md`,
  `contracts/cli.md`, `contracts/review-job.md`,
  `docs/architecture/review-record-in-git-notes.md`, and
  `docs/architecture/design/627-review-note-line-per-event.md`
- Unchanged since the earlier report: `design.md`,
  `627-unreviewed-takes-coverage.md`, `627-guard-blocks-note-writes.md`,
  `review-covers-unreviewed-commits.md`, `data-model.md`,
  `contracts/review-note.md`, and `checklists/requirements.md`
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification
- Conditional lenses: security and reliability applied, since the feature adds
  a `pull_request_target` job that reads PR content with the base repository's
  token, decides which PR-supplied data the check trusts, and changes which
  groups the local guard requires
- Design records: 3 listed in design.md
  - docs/architecture/design/627-unreviewed-takes-coverage.md
  - docs/architecture/design/627-review-note-line-per-event.md
  - docs/architecture/design/627-guard-blocks-note-writes.md
- Existing code inspected: `wfctl/_review.py` (`trunk_refs`,
  `_refuse_a_single_branch_clone`, `relay`), `wfctl/_paths.py`
  (`resolve_branch`), `wfctl/_review_config.py` (`_resolve`), and
  `wfctl/cli.py` (`_review_groups_or_exit`, `review_start_cmd`,
  `review_check_cmd`, `review_groups_cmd`, the sign-off command, `relay_cmd`)
- Reviewers: the four lenses above, run in sequence by one agent in a fresh
  context

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 7

No BLOCKER findings identified in this review. Twelve of the sixteen findings
the earlier report left open are fixed by the edits to the spec, research,
contracts, quickstart, plan, and the two records.

Four earlier findings still stand. PR-004, PR-005, and PR-011 were left open on
purpose and their evidence is unchanged. PR-009 is narrowed: the contract now
covers a failed note write in `review check`, but not in the sign-off, where
running the command again records nothing.

Three new findings are all MINOR:

1. The contract says `review check` "still" refuses a name outside the group
   list, and today it checks only the name's shape, so the change adds trunk
   lookups and their failures to the step that records the note (PR-024).
2. The `relay` refusal's example can't happen, and its "rename one" remedy
   doesn't fit the one case that can, a group renamed on the branch (PR-025).
3. The contract says quickstart step 4 checks the ruleset's `integration_id`,
   and neither that step nor the planned ruleset test does (PR-026).

## Findings

### PR-001: The trigger decision reverses the accepted record's consequence with no record of its own

- Priority: MAJOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `docs/architecture/review-record-in-git-notes.md §Consequences` says GitHub
    runs `main`'s copy of the job and `main`'s wfctl, and `§Log` carries the
    2026-10-25 `revised` entries.
- Finding: The earlier plan reversed a stated consequence of the accepted
  record while the record still said the opposite.
- Why it matters: The record is what the next reader trusts about which code
  CI runs.
- Suggested response: Fixed by the revised record and the Constitution Check
  row.
- Corroborated by: architecture and boundaries, security and reliability

### PR-002: The fallback for the trigger decision breaks FR-017a, and the plan doesn't say what happens to the requirement

- Priority: MAJOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence:
  - `research.md §R4` "Assumed, checked after merge", `spec.md §Assumptions`
    last bullet, and `quickstart.md §2`.
- Finding: The earlier plan presented the fallback as a post-merge step with no
  word on the requirement it breaks.
- Why it matters: The fallback would have shipped a job that breaks a MUST.
- Suggested response: Fixed by R4, the spec assumption, and quickstart step 2.
- Corroborated by: adversarial implementation and verification, requirements
  and traceability

### PR-003: The sign-off command that `release.py` prints can't run where the script leaves the maintainer

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `spec.md §FR-024` and `research.md §R12`.
- Finding: The earlier plan left the printed text, and so the CLI change, to
  the implementer.
- Why it matters: `test_release_script.py` pins whichever line is chosen.
- Suggested response: Fixed by FR-024 and R12.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-004: The guard's push rule misses a short ref name and a glob refspec

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `spec.md §FR-020` and `research.md §R9` rule 2 are unchanged: the guard
    refuses a `git push` whose text names `refs/notes/` or carries `--mirror`.
  - The earlier scratch check on git 2.44.0: `git push origin
    notes/wfctl-review` pushed `refs/notes/wfctl-review`.
- Finding: `notes/wfctl-review` and a `'refs/*:refs/*'` refspec both push the
  notes ref with no `refs/notes/` in the command text.
- Why it matters: These are ordinary forms of the push the rule exists for.
  Left open by the author on purpose.
- Suggested response: Have rule 2 also refuse a push argument holding `notes/`
  or a `refs/*` glob, and add both forms to the guard tests.
- Corroborated by: security and reliability

### PR-005: The notes rule doesn't say which word has to be `notes`

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `research.md §R9` rule 1 is unchanged: "A `git` command whose words include
    `notes` followed by `add`, …"
  - `wfctl/_review_gate.py` `_SEPARATOR` splits on newlines, so each line of a
    heredoc commit message is read as its own command.
- Finding: Under a loose reading, `git commit -m "refuse git notes add"` is
  refused, and R9 doesn't say how `GIT_NOTES_REF=x git notes add` is read as a
  `git` command.
- Why it matters: Two implementers would write different rules, and no planned
  test catches a false refusal. Left open by the author on purpose.
- Suggested response: State that `notes` is git's subcommand, that an
  environment assignment may come before `git`, and test that a commit message
  naming `git notes add` is allowed.
- Corroborated by: adversarial implementation and verification

### PR-006: Recording a line reads the note first, and the design record still says it doesn't

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `docs/architecture/design/627-review-note-line-per-event.md §Consequences`
    now says recording reads the note only to skip a duplicate line, and the
    paragraph under `§Diagram` says the same.
- Finding: The record described a write path the code won't have.
- Why it matters: The record is what the next reader trusts about the write
  path.
- Suggested response: Fixed by the revised Consequences bullet and diagram
  paragraph. The diagram itself still draws only an `appends` arrow from
  `review check` to the note, and the record has no Log line for the change.
  The record is `proposed`, so neither is raised here.
- Corroborated by: architecture and boundaries

### PR-007: The spec asks for a job run on this feature's own PR, which the plan says can't happen

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §Validation Strategy` names a run on a throwaway PR after this
    feature merges.
- Finding: The spec's validation line could not be met as the plan stood.
- Why it matters: An analyze pass or the PR reviewer would read an unmet item.
- Suggested response: Fixed by the revised validation line.
- Corroborated by: requirements and traceability

### PR-008: The spec left "where else `contents: read` applies" to the plan, and the plan answers only for the new job

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `contracts/review-job.md §Trigger and trust` and `plan.md §Project
    Structure` (`ci.yml`).
- Finding: The plan didn't answer the question the spec handed it.
- Why it matters: A PR's own jobs ran with a token that could push notes.
- Suggested response: Fixed by the contract and the plan's structure line.
- Corroborated by: security and reliability

### PR-009: The plan defines a failed push but not a failed local write of the note

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `contracts/cli.md §wfctl review check` now gives the failed-write warning
    and says the next `review check` records the note again.
  - `contracts/cli.md §wfctl review sign-off`: "with the same added lines and
    the same warning on a failed send". It says nothing about a failed write.
  - `wfctl/cli.py` sign-off command: when `unreviewed` returns nothing, it
    prints "nothing unreviewed; no sign-off needed" and returns before any
    later step.
- Finding: Half fixed. When the sign-off's note write fails, the sign-off is
  already in the state directory, so running the sign-off again finds nothing
  unreviewed and returns before it records anything. `store reviews` sends
  only notes that exist. Nothing then writes the line, and CI fails until a
  new commit is signed off.
- Why it matters: The sign-off is the path a release PR depends on (FR-023),
  and the warning, whatever it says, has no command to name.
- Suggested response: Have the sign-off record the note even when nothing is
  unreviewed and the state directory's sign-off is the head, or say in the
  contract what the warning tells the person to do.
- Corroborated by: adversarial implementation and verification

### PR-010: Any commit status named `review` meets the ruleset entry

- Priority: MINOR
- Category: Enhancement Suggestion
- Status: fixed
- Evidence:
  - `contracts/review-job.md §Trigger and trust`: the ruleset lists
    `{ "context": "review", "integration_id": 15368 }`, the GitHub Actions app.
- Finding: A required check with no `integration_id` was met by a commit
  status anyone with write access could post.
- Why it matters: That was cheaper than forging a note.
- Suggested response: Fixed by the contract. PR-026 covers the verification
  that the contract says exists and doesn't.
- Corroborated by: security and reliability

### PR-011: The two readers can disagree when the state directory's last reviewed commit has left the branch

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `research.md §R3` is unchanged: "Walking only the branch matches what the
    state directory holds."
  - `wfctl/_review.py` `commit_range` falls back to the merge base for a last
    reviewed commit that isn't an ancestor of the head.
  - `spec.md §SC-004`: the two report the same commits "in every scenario of
    the shared test".
- Finding: After a reset that drops the state directory's last reviewed
  commit, the guard counts from the merge base while the notes reader counts
  from an older noted commit.
- Why it matters: An implementer whose shared test includes a reset sees the
  readers disagree and may change one to match. Left open by the author on
  purpose.
- Suggested response: Narrow R3's claim to histories where that commit is on
  the branch, and say the guard is the stricter of the two elsewhere.
- Corroborated by: adversarial implementation and verification

### PR-012: CI requires a group the PR removed, and nothing local can review it or sign it off

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-010`, `§FR-010a`, `research.md §R13`, and `contracts/cli.md
    §Which groups the local commands use`.
- Finding: The earlier plan left a PR that removes a group with CI red and no
  local command that could turn it green.
- Why it matters: That path now works end to end, including the panel listing
  and the relay.
- Suggested response: Fixed by FR-010, FR-010a, and R13.
- Corroborated by: requirements and traceability, adversarial implementation
  and verification

### PR-013: The trunk R13 trusts is chosen by the PR's own `wfctl.json`

- Priority: MAJOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `spec.md §FR-015a`, `research.md §R14`, and `contracts/review-job.md
    §Steps` 4.
- Finding: The earlier plan let one `trunk` line in the PR's file empty the
  range and pick the groups.
- Why it matters: The base branch comes from the event, which the PR's files
  can't change.
- Suggested response: Fixed by FR-015a, R14, and the job contract.
- Corroborated by: security and reliability, architecture and boundaries

### PR-014: The plan's source list leaves out the loader R13 needs

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Project Structure` lists `_review_config.py` ("parse a
    wfctl.json's text; the FR-015 group list"), and its `_review_gate.py` and
    `cli.py` lines name the group list change.
  - `research.md §R13`, fourth paragraph: each file is validated alone and the
    join is by name only.
- Finding: The earlier plan didn't say where the text loader lives or whether
  the joined list is validated as one declaration.
- Why it matters: Three callers depend on the answer.
- Suggested response: Fixed by the plan's structure lines and R13.
- Corroborated by: deterministic checks

### PR-015: A problem in the trunk's `review` key fails every PR, including the one that fixes it

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `research.md §R13`, sixth paragraph: the failure stays, for a stated
    reason, and `AGENTS.md` gives the recovery beside the ruleset steps.
  - `plan.md §Project Structure`: the `AGENTS.md` line adds "recovering from a
    broken review key on main (R13)".
- Finding: The earlier plan left the recovery unwritten.
- Why it matters: Recovery needs a person and a ruleset edit, and now says so.
- Suggested response: Fixed by R13 and the plan's `AGENTS.md` line.
- Corroborated by: adversarial implementation and verification

### PR-016: The rerun assumes `gh` and a GitHub `origin` in every repository wfctl installs into

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §R8`: when `gh` isn't installed, or `origin` isn't a GitHub
    repository, the rerun does nothing and prints nothing.
- Finding: Every completed run in a repository without GitHub would have
  printed a warning.
- Why it matters: A warning printed every time teaches the user to ignore it.
- Suggested response: Fixed by R8.
- Corroborated by: architecture and boundaries

### PR-017: `review groups` and `relay` still read only the working tree, so the panel doesn't list a removed group

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-010a` now names `review groups` and `relay`, and says
    `review groups` lists a removed group so the panel runs it.
  - `contracts/cli.md §Which groups the local commands use` and `plan.md
    §Project Structure` (`cli.py`) match.
- Finding: The panel never started a removed group, and `relay` couldn't find
  it.
- Why it matters: The removed-group path now works without the guard's refusal
  as a prompt.
- Suggested response: Fixed by FR-010a, the contract, and the plan's `cli.py`
  line. PR-025 covers the letter clash the wider list opens.
- Corroborated by: adversarial implementation and verification

### PR-018: FR-010 says the guard's results are unchanged except for a removed group, and the edge cases change an uncommitted group too

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-010` now lists three cases: a group the branch dropped, a
    group only in the working tree, and a `review` key problem read from git.
- Finding: FR-010 named only one of the three changes.
- Why it matters: A regression test written from the old wording would have
  pinned the wrong behaviour.
- Suggested response: Fixed by FR-010.
- Corroborated by: requirements and traceability

### PR-019: R10's `unreviewed` signature has no way to carry `--base` down to `trunk_refs`

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R10`: `unreviewed` and `coverage_from_notes` take a `trunk`
    keyword, passed through `commit_range` to `trunk_refs`.
  - `research.md §R14`: a trunk named by `--base` skips the single-branch
    refusal and still refuses the branch under review.
  - `wfctl/_review.py` `trunk_refs` runs `_refuse_a_single_branch_clone` only
    for an `origin/` trunk with no declared trunk, so the skip matches the
    existing rule for a declared trunk.
- Finding: The earlier plan didn't name the parameter or say whether the
  refusal applied.
- Why it matters: R10 is the interface the shared test describes.
- Suggested response: Fixed by R10 and R14.
- Corroborated by: deterministic checks

### PR-020: The accepted record says CI requires `main`'s groups, and R14 reads the base branch's

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `docs/architecture/review-record-in-git-notes.md §Consequences`: "The check
    requires every review group that the PR's base branch lists", read from
    GitHub's event. A second 2026-10-25 `revised` Log entry records it.
  - `plan.md §Constitution Check` re-check line names R14.
- Finding: The record said `main`'s groups.
- Why it matters: The record is what the next reader trusts about whose groups
  CI requires.
- Suggested response: Fixed by the record and the plan's re-check line.
- Corroborated by: architecture and boundaries

### PR-021: The plan says a PR that passes locally passes in CI, and the local trunk can be stale

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Summary`: "as long as the local `origin/main` is current (R13)".
  - `research.md §R13`, fifth paragraph: the stale-fetch case, and "Both sides
    agree for the same trunk ref".
- Finding: The earlier sentence claimed agreement unconditionally.
- Why it matters: A test written from it would fail the first time `main`
  moved.
- Suggested response: Fixed by the Summary and R13. A residual for stacked PRs
  is noted under Assumptions challenged.
- Corroborated by: adversarial implementation and verification

### PR-022: No test covers the local group list FR-010 and FR-010a add

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `spec.md §Validation Strategy`: tests for the guard refusing a dropped
    group, `review start` and `review groups` with it, a working-tree-only
    group, and the removed-group history in the readers-agree test.
  - `plan.md §Project Structure`: `test_review_config.py`, and the widened
    `test_review_notes.py`, `test_review_gate.py`, and `test_review_cli.py`
    lines.
- Finding: Nothing checked the behaviours that fixed PR-012.
- Why it matters: A later change to the group lookup would have undone them
  silently.
- Suggested response: Fixed by the Validation Strategy and the test lines.
- Corroborated by: adversarial implementation and verification

### PR-023: The `edited` trigger is assumed to fire on an automatic retarget, and overlapping runs are unordered

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §R14` marks the retarget `edited` event as checked after
    merge, and `quickstart.md §5` checks it.
  - `contracts/review-job.md §Trigger and trust`: a `concurrency` group keyed
    by PR number with `cancel-in-progress: true`.
- Finding: The assumption was unmarked, and two runs on one head were
  unordered.
- Why it matters: A result measured against a parent branch could have stood
  on a PR into `main`.
- Suggested response: Fixed by R14, quickstart step 5, and the contract.
- Corroborated by: security and reliability

### PR-024: `review check` gains a group lookup it doesn't have today, and the contract calls it unchanged

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `contracts/cli.md §Which groups the local commands use`: for `review
    start`, `review check`, `review groups`, and `relay`, "A name in neither
    still prints `✗ no review group named '<group>'` and exits 1."
  - `plan.md §Project Structure` (`cli.py`): `review check` uses the FR-010a
    list.
  - `wfctl/cli.py` `review_check_cmd` checks only `PLAIN_NAME` and then calls
    `_review.check(agent_dir, group)`. It never loads `wfctl.json` and never
    looks up a trunk.
- Finding: For `review check`, the lookup is new. Loading the FR-010a list
  means `git show` of the trunk's and the head's `wfctl.json`, so `review
  check` can now fail on a missing trunk, a shallow clone, or a problem in the
  trunk's `review` key, and it refuses a group whose run exists but which no
  list names any more. `review check` is the step that completes a run and
  records the note (FR-001).
- Why it matters: An implementer reading "still" adds the lookup without
  noticing it puts the trunk's failures in front of the note write, and no
  planned test covers `review check` with a broken trunk or a dropped group
  that has a run.
- Suggested response: Either keep `review check` as it is, accepting any group
  with a run, and drop it from the FR-010a list, or say in the contract that
  the lookup is new and which failures it adds.
- Corroborated by: requirements and traceability

### PR-025: The `relay` refusal's example can't arise, and its remedy doesn't fit the case that can

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `contracts/cli.md §Which groups the local commands use`: "✗ reviewer s2
    matches two groups, security and style; rename one in wfctl.json".
  - `wfctl/_review_config.py` `_resolve` puts the built-in `security` and
    `code` in every file's order and reports any other group sharing their
    letter, so `style` fails validation in whichever file lists it.
  - `research.md §R13`: each file is validated alone, so a clash exists only
    between a group the trunk lists and the branch dropped, and a group the
    branch or working tree adds.
  - `wfctl/_review.py` `relay` takes the first group whose letter matches.
- Finding: The only clash the joined list can hold is a custom trunk group
  against a custom group the branch adds, and the ordinary way to get one is
  renaming a group on the branch, such as `money-rules` to `money`. The trunk's
  side can't be renamed on that branch, since a rename there is a removal and
  the trunk still requires the old name. `review start` also prints the same
  ids, `m1` and up, for both groups.
- Why it matters: A rename leaves the relay refusing both groups' reviewers
  with advice that doesn't help, and an implementer copying the contract's
  example writes a test for a state the loader never produces.
- Suggested response: Use a reachable example, have the remedy name the group
  the branch added, and consider letting `relay` pick the one group whose
  latest run lists the id as expected, refusing only when both do.
- Corroborated by: adversarial implementation and verification

### PR-026: The contract says quickstart checks the ruleset's `integration_id`, and nothing does

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `contracts/review-job.md §Trigger and trust`: "The id is checked in
    quickstart step 4: the read-back must show it on the `review` entry."
  - `quickstart.md §4`: "The read-back lists six required checks, `review`
    among them." It doesn't mention the id.
  - `plan.md §Project Structure`: `test_ruleset.py` "reads job names from
    review.yml as well as ci.yml", and `rulesets/main.json` "review added to
    required checks". Neither names `integration_id`. `spec.md §FR-018` is
    unchanged.
- Finding: The id that fixed PR-010 lives only in one contract. The step the
  contract names to check it doesn't, and no planned test pins it.
- Why it matters: An implementer working from the plan's structure lines adds
  `{ "context": "review" }` and every check passes, which reopens PR-010
  silently.
- Suggested response: Add the id to quickstart step 4's read-back and to the
  `test_ruleset.py` line, or to FR-018.
- Corroborated by: deterministic checks

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | research.md §R11, contracts/cli.md §review check | covered; PR-024 |
| FR-002 | research.md §R11, contracts/cli.md §review sign-off | covered; PR-009 |
| FR-003 | research.md §R6, contracts/review-note.md | covered |
| FR-004 | research.md §R7, contracts/cli.md | covered; PR-009 |
| FR-005 | plan.md §Technical Context (Storage), research.md §R11 | covered |
| FR-005a | plan.md §Summary, research.md §R8, contracts/cli.md §store reviews | covered |
| FR-006 | research.md §R7 | covered |
| FR-007 | research.md §R7 | covered |
| FR-008 | contracts/cli.md §store reviews | covered |
| FR-009 | research.md §R10, data-model.md §Coverage | covered |
| FR-010 | plan.md §Summary, §Project Structure, research.md §R13, contracts/cli.md §Which groups | covered |
| FR-010a | plan.md §Project Structure, research.md §R13, contracts/cli.md §Which groups | covered; PR-024, PR-025 |
| FR-011 | research.md §R3, data-model.md §Coverage | covered; PR-011 |
| FR-012 | research.md §R10, data-model.md §Unreviewed commit | covered |
| FR-013 | research.md §R2, contracts/cli.md §check reviews | covered |
| FR-014 | contracts/cli.md §check reviews | covered |
| FR-015 | plan.md §Summary, research.md §R13, contracts/cli.md §check reviews | covered |
| FR-015a | plan.md §Summary, research.md §R10, §R14, contracts/cli.md §check reviews | covered |
| FR-016 | contracts/cli.md §check reviews | covered |
| FR-017 | contracts/review-job.md §Steps, research.md §R14 | covered |
| FR-017a | research.md §R4, contracts/review-job.md | covered |
| FR-018 | plan.md §Project Structure, contracts/review-job.md, quickstart.md §4 | covered; PR-026 |
| FR-019 | research.md §R9 | covered; PR-005 |
| FR-020 | research.md §R9 | PR-004 |
| FR-021 | research.md §R9 | covered |
| FR-022 | research.md §R9, plan.md §Project Structure | covered |
| FR-023 | research.md §R12 | covered; PR-009 |
| FR-024 | research.md §R12 | covered |
| FR-025 | plan.md §Project Structure (AGENTS.md) | covered |
| SC-001 | quickstart.md §2 - §5 | covered; PR-026 |
| SC-002 | research.md §R11, quickstart.md §3 | covered |
| SC-003 | research.md §R1, `commit_range` merge rule | covered |
| SC-004 | plan.md §Project Structure (test_review_notes.py) | covered; PR-011 |
| SC-005 | plan.md §Project Structure (test_review_gate.py) | PR-004, PR-005 |

## Assumptions challenged

- A `pull_request_target` job reports its check on the PR's head commit.
  Stated in `research.md §R4`, checked only after merge, and the ruleset waits
  on it.
- `gh pr checks` returns a link of the form `…/actions/runs/<run>/job/<job>`.
  Stated in `research.md §R8`, and checked in quickstart step 3.
- GitHub sends `edited` when it retargets a stacked PR itself. Stated in
  `research.md §R14`, and checked in quickstart step 5.
- `15368` is the GitHub Actions app's id for a check's `integration_id`. Stated
  in `contracts/review-job.md`, and checked only if PR-026's read-back is
  added.
- The local guard measures against the `trunk` key or `origin/HEAD`, while CI
  measures against the PR's base. For a stacked PR the two differ even with a
  current fetch: a child that drops a group its parent added is required to
  review it in CI and not locally. The plan's Summary names only a stale
  `origin/main`. R13's "agree for the same trunk ref" is accurate, the case is
  narrow, and CI is the stricter side, so this is noted here and not raised.
- Group names alone decide coverage in CI, while FR-010a takes a group's skill
  and reviewers from the working tree. A PR can therefore point an existing
  group at a different skill or fewer reviewers and run that on itself. The
  change shows in the PR's diff, and the record's claim is about a PR
  weakening its check by accident, so this is noted here and not raised.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- `research.md §R14` passes the base branch through `env:` rather than an
  inline expression, so a branch name can't inject shell text into the step.
- `research.md §R13` keeps the list function free of file reads, so the guard
  path still imports neither `typer` nor `rich`, and validates each file alone
  so a join never reports a clash neither file has.
- `research.md §R13` keeps a broken trunk `review` key a failure and writes
  the recovery down, rather than falling back to defaults that would drop a
  custom group's requirement silently.
- `spec.md §FR-010` now lists each case where the guard's result changes,
  which gives the regression tests an exact target.
- `quickstart.md §4` applies the ruleset only after the post-merge checks
  pass, so a broken trigger never blocks every merge.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
