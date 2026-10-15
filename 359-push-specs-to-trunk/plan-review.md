# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | f06707088ad4824e9dbcf339f14614f88f9eb7b0 | technical strategy |
| spec.md | 68507ea870e0226a517cc6af694c083dd4630d8e | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | c08921165ed069a8150511b76ededfe5f029282e | design-record index |
| docs/architecture/design/store-specs-implement-pass.md | 67ebbd9713bc4f7aaf8c69f62c7934979a6b6eee | design record |
| docs/architecture/design/store-specs-at-removal.md | 9a8ab88a08fa68b6f36465310ca2252e355b1718 | design record |
| docs/architecture/design/store-specs-merges-before-push.md | d8dacdaa617398f9aae737ad02a355de3b8e1091 | design record |
| docs/architecture/spec-storage-read-from-git.md | e95749c063e9aac84c9aa1f23b205c3e4c7e8638 | level-2 record the plan implements |
| research.md | 5449b17874e96a7aaeb0c0bc7782277ae5b8bbf9 | planning evidence |
| data-model.md | 6ea70cff0e8568cd36ef2e88a3664910f3b8ad0f | planning evidence |
| contracts/cli.md | 1f7430d6d0254e2187ac61f8d151e15748ea8054 | planning evidence |
| quickstart.md | d1ff4edccde503ea9a4f869aa532a18d76e431f5 | planning evidence |
| plan-review.plan.md | 51905313e32de76891bfd0e7addbd656ac0acedd | base of this re-review |

## Review scope

- Re-review: the plan copy's identity equals the earlier report's `plan.md`
  row, so the review diffed the copy against `plan.md`.
- Changed in `plan.md`: the host-block routing test in
  `test_store_specs_pass.py`, which now reads the `next-step.md` that
  `wfctl next` writes and says why `resume`'s copy would not do; and the #40
  bullet under `§Risks`, which now cites #40's record at `2e9f124` and
  `b3fc797` in place of `448301e`. These were reviewed together with the
  `next_cmd` and `next_step_content` entries under `§Project Structure` and
  the `stops_removal` test in `test_spec_store.py`.
- Changed inputs, each re-read in full with the whole of `plan.md` reviewed
  against it: `research.md`, whose §R6 and §R15 were edited. The command named
  it as changed, and its identity no longer matches the earlier report's row.
- Unchanged since the earlier report, by identity: `spec.md`, `design.md`, the
  three design records, the level-2 record, `data-model.md`,
  `contracts/cli.md`, `quickstart.md`, and the constitution, which is still
  absent.
- Also read: #40's record `docs/architecture/design/40-archive-is-a-command-group.md`
  on the local branch `40-save-uncommitted-on-remove`, at `2e9f124` and at
  `b3fc797`, which is still the last commit to touch it. The record is not on
  disk in this worktree, so it has no row above.
- Existing code inspected: `wfctl/cli.py` `next_cmd` and `resume_cmd`, to check
  that both write `next-step.md` and that only `next_cmd` calls
  `next_step_content` directly; and `tests/conftest.py`, to recheck PR-004.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification
- Conditional lenses: security and reliability applied, because the store
  pushes to a remote, writes into a checkout every branch shares, runs inside
  worktree removal, and serialises concurrent runs with a lock
- Reviewers: the four lenses above, run in sequence by one agent

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 15

No BLOCKER findings identified in this review. The revision fixes the three
findings it set out to: PR-026, PR-027, and PR-028. It also corrects the stale
`448301e` citation in `plan.md §Risks` that the earlier report listed under
`## Assumptions challenged`.

The other twelve earlier MINOR findings are still open, since the revision did
not touch them. PR-024 is among them, and it is still waiting on a design call.
The revised R6 adds one new MINOR finding, PR-029. R6 now decides that
`committed_not_backed_up` exits 0 and says #40 has to match, but no test in the
plan pins that exit code, so the branch that merges second can change it
without a test failing.

## Findings

### PR-001: A path staged by anyone stops every store's merge

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `research.md §R8` point 2 and rationale: a staged path anywhere in the spec
    store blocks a merge that isn't a fast-forward, and the store reads
    `git diff --cached --name-only` to name the folders and the remedy
  - `data-model.md §Store result`: outcome `merge_blocked_staged`
  - `contracts/cli.md §wfctl store specs`: the staged-files output and its
    remedy line
  - `plan.md §Project Structure`: a test that stages another folder's file and
    moves the remote, and a test that clears it by storing the owning branch
- Finding: Fixed in an earlier review and unchanged since.
- Why it matters: The output points a person at the staged files rather than
  at edits that aren't there.
- Suggested response: Fixed by `research.md §R8` and its tests.
- Corroborated by: security and reliability, adversarial implementation

### PR-002: After the host refuses the push, `implement` routes to `wfctl verify` and the store never lifts the hold

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R15`: `wfctl store specs` records a `store-specs` action on
    `stored`, and a `store-specs` block on a finished `implement` routes to
    the pass with `auto: false`
  - `contracts/cli.md §wfctl status --json`: `next_command` stays
    `/store-specs` while the block holds `implement`
- Finding: Fixed in an earlier review and unchanged in substance.
- Why it matters: A person who runs `wfctl store specs` in their own shell
  lifts the hold in the common case.
- Suggested response: Fixed by `research.md §R15`. PR-018 covers the path the
  rule leaves unstated.
- Corroborated by: architecture and boundaries

### PR-003: `GIT_TERMINAL_PROMPT=0` does not stop an SSH prompt, and pfms's spec store pushes over SSH

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `research.md §R7` (unchanged): every git call runs with
    `GIT_TERMINAL_PROMPT=0`, so the store "never waits on a person"
  - `plan.md §Technical Context` Constraints: "never prompts for credentials
    (research R7)"
  - pfms's spec store remote is `git@github.com:MarinVentures/pfms.git`, as
    the first review found
- Finding: The variable governs git's own credential prompt for HTTPS. SSH asks
  for a key passphrase or a host-key confirmation on its own, so a removal in
  pfms can still stop at a prompt. The 60-second timeout bounds the wait, but
  the plan's test only checks that the variable is set.
- Why it matters: The claim holds for one of the two repositories the plan
  names.
- Suggested response: Set `GIT_SSH_COMMAND` with `-o BatchMode=yes` as well, or
  narrow the constraint to HTTPS and say that SSH is bounded by the timeout.
- Corroborated by: security and reliability

### PR-004: Nothing keeps a test from storing the developer's real spec dir

- Priority: MINOR
- Category: Enhancement Suggestion
- Status: open
- Evidence:
  - `plan.md §Project Structure`: `archive-specs` runs the store, and the new
    tests build their own bare remotes. The archive tests may also run through
    `hook worktree-remove`.
  - `tests/conftest.py`: its autouse fixtures stub the version check, the
    install origin, and the bundle. Only the `storyctl_dir` fixture sets
    `WFCTL_SPEC_DIR`, and it is not autouse.
- Finding: A later test that invokes `store specs`, `archive-specs`, or the
  removal hook without a fixture that sets the spec dir resolves the real spec
  store from the working directory, and on a developer's machine it would
  commit and push.
- Why it matters: The suite is offline by design, and this change adds the
  first code path in it that can push.
- Suggested response: Add an autouse guard in the style of the version-check
  stub, for example one that makes the store refuse any remote that is not a
  local path under the test's temporary folder.
- Corroborated by: security and reliability

### PR-005: The payload snapshot records no passes, so it will not move

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `research.md §R13` (unchanged): the snapshot is regenerated because every
    case "now carries a `store-specs` entry", and "the diff should show only
    the new entries"
  - `plan.md §Implementation order` step 6 and the `pipeline_payload_snapshot.json`
    entry under `§Project Structure`: only `store-specs` entries may appear
  - `tests/test_pipeline_payload_snapshot.py` `_dump`: records each step's
    `name`, `state`, `annotation`, `reason`, and `remedy`, and no sub-steps
- Finding: The snapshot holds step rows only. A `skipped` pass leaves
  `implement`'s row as it was, so the regenerated file should not change at
  all, and the check in step 6 has nothing to look at.
- Why it matters: An implementer following step 6 finds no entries and has to
  guess whether to widen `_dump`, which is a change to a shared test the plan
  does not scope.
- Suggested response: Restate R13. The snapshot should not change, and an
  unchanged snapshot is the check that the pass moved no step row.
- Corroborated by: adversarial implementation and verification

### PR-006: In a layout with nowhere to push, the default `wfctl status` shows nothing

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md` US5: wfctl "says plainly where the files are and that nothing
    backs them up"
  - `data-model.md §The store-specs pass`: a `skipped` reading carries its text
    in `display`, with `reason` empty
  - `wfctl/cli.py` `status_cmd`: a `skipped` pass with no warning is hidden
    unless `--all` is passed, as the first review found
- Finding: The text reaches `wfctl status --json` and `wfctl status --all`, but
  the default view hides the pass and `implement` reads finished. The default
  layout keeps `specs/` inside the worktree, so most repositories see this.
- Why it matters: The plan's choice is defensible, but it is a visible product
  decision that neither the spec nor the record makes, and the plan doesn't
  state it.
- Suggested response: State where the layout text is visible, or decide that
  the default view shows this pass.
- Corroborated by: requirements and traceability

### PR-007: "The next store from any branch pushes it" holds only for a store with files of its own

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `contracts/cli.md §wfctl store specs` and `§wfctl archive-specs`: the
    not-pushed message still says "the next `wfctl store specs` from any branch
    pushes it"
  - `spec.md §FR-009`: a fully stored spec dir pushes nothing
- Finding: A commit left unpushed goes up only when some other branch stores
  files of its own. A branch whose spec dir is already stored pushes nothing,
  and no command lets a person push the leftover without typing git in the
  spec store.
- Why it matters: The message is a promise to a person deciding whether to
  act, and it isn't true for a branch with nothing new.
- Suggested response: Reword the message to say the next store that has files
  to push sends it, or let the store push whenever the spec store's branch is
  ahead of its upstream and say how that fits US2 scenario 2.
- Corroborated by: adversarial implementation and verification

### PR-008: The SC-006 timing measures two git calls, and the reader makes more

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `spec.md §Validation Strategy` real run step 4: "`time wfctl status` with
    and without the pass"
  - `quickstart.md §6` (unchanged): "The pass costs exactly the two git
    commands from research R3"
  - `plan.md §Technical Context` Performance Goals: "It runs two git commands
    scoped to one folder"
  - `research.md §R2`: the reader asks for the layout first, which takes
    several more git calls through `owns_branch`
- Finding: The quickstart times part of the reader's work and never times
  status without the pass, which is what the spec's validation asks for.
- Why it matters: The budget is very likely met, but the evidence recorded for
  SC-006 would not show it.
- Suggested response: Time `wfctl status` with the pass and with
  `wfctl step none implement.store-specs`, and drop "exactly the two git
  commands".
- Corroborated by: requirements and traceability

### PR-009: Two output strings disagree, and one says "committed" when nothing was

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `data-model.md §Store result`: `⚠ committed N files, not backed up —
    <branch> has no upstream`
  - `contracts/cli.md §wfctl store specs`: `⚠ committed 3 files, not backed up
    — specs-trunk has no upstream branch`, in a file whose examples are exact
  - `data-model.md §The store-specs pass`: `store_no_upstream` displays `no
    upstream branch; committed, not backed up` whatever the spec dir's git
    state is
- Finding: The two artifacts give different text for one outcome. The pass's
  text also claims a commit in a layout where the pipeline never runs the
  store. Neither file has changed since the earlier report.
- Why it matters: Exact-text tests will be written against one of the two.
- Suggested response: Pick one string for `committed_not_backed_up`, and drop
  "committed" from the pass's display.
- Corroborated by: deterministic checks

### PR-010: The plan doesn't say which fetch and push failures read "unreachable"

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `spec.md §FR-006`: "When the fetch or the push fails because the remote is
    unreachable"
  - `data-model.md §Store result`: `not_pushed`, `push_refused`, and
    `git_failed` are three outcomes for a failed fetch or push
  - `research.md §R7` (unchanged): only a timeout is mapped
- Finding: An authentication failure, a deleted remote branch, or a permission
  error on push each needs to land on one of three outcomes, and the plan
  doesn't give the rule.
- Why it matters: Telling a person "unreachable" over a credential failure
  sends them to check the network.
- Suggested response: State the rule. For example, a timeout or a connection
  error reads `not_pushed`, a non-fast-forward push reads `push_refused`, and
  anything else reads `git_failed` with git's message.
- Corroborated by: adversarial implementation and verification

### PR-011: A conflict or an interrupted merge stops every branch's store, and no recovery is named

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `research.md §R8` point 1 (unchanged): on a conflict the store reads the
    unmerged paths, aborts, keeps its commit, and names the folders. The
    `MERGE_HEAD` check runs only after a merge the store itself started.
  - `contracts/cli.md §wfctl store specs`: the conflict output still ends "the
    merge was aborted and your commit is kept", with no next step, while the
    staged-files output does name one
  - `research.md §R5`: the lock is released when the process exits, which
    includes a store killed partway through a merge
- Finding: After a conflict, the next store from any branch merges the same
  upstream and hits the same conflict. A store killed mid-merge leaves
  `MERGE_HEAD` behind, and the next store's `git commit -- <dir>` fails before
  the check is reached. In both cases every branch's store fails until a
  person resolves it by hand, and the plan gives that person no command. At
  removal these failures warn rather than stop, but the warning repeats on
  every removal until someone acts.
- Why it matters: The staged-files case has a remedy line, and the conflict
  case, which blocks every branch the same way, still has none.
- Suggested response: Say that a conflict blocks every branch until it is
  resolved, add a remedy line naming the git commands to run in the spec
  store, and decide whether the store aborts a merge it finds in progress
  before it starts.
- Corroborated by: adversarial implementation and verification

### PR-012: No test covers the import cost of the moved `owns_branch`

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `plan.md §Risks`: the existing guard tests are the check for the
    `committable` refactor
  - `wfctl/_hook.py` module docstring: the guard keeps its imports to the
    standard library and `wfctl._guard`, because it runs before every Bash call
  - `tests/test_guard_entry.py`
    `test_the_refusal_path_never_imports_typer_or_rich`: its command has no
    `git` in it, so `committable` never runs in that test
- Finding: After the move, `_hook.committable` imports `_spec_store`. If that
  module imports `rich`, `typer`, or `wfctl.cli` at module scope, the guard's
  commit path pays for it, and no existing test fails.
- Why it matters: The refactor runs before every Bash call an agent makes.
- Suggested response: Import `_spec_store` inside `committable`, keep its
  module-scope imports to the standard library, and add an import test whose
  command contains `git commit`.
- Corroborated by: architecture and boundaries

### PR-013: When #40 merges first, nothing says how removal turns a failed push into a warning

- Priority: MAJOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `research.md §R6`: removal "calls the store as a function and reads
    `StoreResult.stops_removal`"
  - `data-model.md §Store result`: "Removal reads that property, never the exit
    code"
  - #40's record at `b3fc797`, `§Decision`: the hook "decides from its result,
    not from the exit code of `store specs`"
- Finding: Fixed in an earlier review and unchanged in substance.
- Why it matters: A failed push, a held lock, or a staged file in the spec
  store no longer stops every removal.
- Suggested response: Fixed by `research.md §R6` and `data-model.md §Store
  result`.
- Corroborated by: architecture and boundaries, security and reliability

### PR-014: R8 doesn't say how a refused merge is told apart from a conflict

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R8`: after a failed merge the store first runs
    `git rev-parse -q --verify MERGE_HEAD`. Present means a conflict, and
    absent means a refusal, which `git diff --cached --name-only` then
    classifies.
  - `plan.md §Project Structure` `_spec_store.store` and the conflict test in
    `test_spec_store.py`
- Finding: Fixed in an earlier review and unchanged in substance.
- Why it matters: A conflict can no longer be read as staged files and left
  mid-merge.
- Suggested response: Fixed by `research.md §R8` and the conflict test.
- Corroborated by: adversarial implementation and verification

### PR-015: An untracked file in the merge's way is a fourth refusal, and R8 calls it a local edit

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `research.md §R8` point 3 (unchanged): with no `MERGE_HEAD` and nothing
    staged, the refusal is "a file the upstream changed has unstaged local
    edits", and the store names the files "from git's message"
  - `contracts/cli.md`: "merge blocked by local edits to <file>", with the
    remedy "store or discard that edit"
  - Scratch reproduction in an earlier review, git 2.44.0: an untracked local
    file that the upstream adds makes the merge exit 2 with no `MERGE_HEAD`
    and nothing staged, under the header "The following untracked working tree
    files would be overwritten by merge"
  - `spec.md §Assumptions`: this repository's spec store holds 58 untracked
    spec dirs from other branches
- Finding: The order still sends this refusal to kind 3, and its text is wrong
  for it. The file is untracked rather than edited, and a parser keyed on
  git's local-changes header finds no file names.
- Why it matters: Like the staged case, it blocks every branch's store until a
  person moves the files, and the output sends them looking for an edit.
- Suggested response: Name the untracked case in R8, with its own text and
  remedy, or word kind 3 so it is true for both, and parse the file list from
  either header.
- Corroborated by: security and reliability

### PR-016: One new test expects a store that the earlier push already made unnecessary

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Project Structure` `test_spec_store.py`: "storing the branch that
    owns the staged folder clears the index and pushes the first branch's kept
    commit with its own; the first branch's next store reads already_stored"
  - `spec.md §FR-009`: a stored spec dir creates no commit and pushes nothing
- Finding: Fixed in an earlier review and unchanged since.
- Why it matters: The test can be written as stated and pass against a store
  that follows FR-009.
- Suggested response: Fixed by the revised test entry.
- Corroborated by: adversarial implementation and verification

### PR-017: R15's routing rule keys on an outstanding pass, not on the block it was written for

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §R15`: "The rule keys on the block's action matching the
    outstanding pass's name, not on any outstanding pass."
  - `plan.md §Project Structure` `next_step_content` and the routing tests in
    `test_store_specs_pass.py`
- Finding: Fixed in an earlier review and unchanged in substance.
- Why it matters: Two implementers route a `push` block on a finished
  `implement` the same way.
- Suggested response: Fixed by `research.md §R15`.
- Corroborated by: architecture and boundaries

### PR-018: The hold outlives a spec dir that reached the remote by another route

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `research.md §R15`: only `stored` records the action, and "a person who
    runs `wfctl store specs` in their own shell lifts the hold without a second
    command". The routing rule keys on a pass that reads `in_progress`.
  - `contracts/cli.md §wfctl store specs`: a `not_pushed` commit is pushed by
    the next store from any branch
- Finding: Suppose a person runs `wfctl store specs` after the block, it ends
  `not_pushed`, and another branch's store later pushes the commit. The pass
  reads `done`, no action was recorded, and a second `wfctl store specs`
  reports `already_stored`, which records nothing. The hold stays, and with the
  pass no longer outstanding, routing goes to `wfctl verify`, which is the
  outcome R15 says it prevents. The edits to R15 in this revision did not touch
  this path.
- Why it matters: The block's remedy line still names
  `wfctl report-action store-specs`, so a person can recover, but the plan's
  claim about a second command is not true on this path.
- Suggested response: State that this path needs `report-action`, or record
  the action on `already_stored` when a `store-specs` block is standing, since
  the spec dir is then on the remote.
- Corroborated by: adversarial implementation and verification

### PR-019: Three statements say wfctl writes nothing but git history, and R15 writes an event

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `plan.md §Technical Context` Storage: "Nothing else is written"
  - `plan.md §Constitution Check` `session-state-is-re-derived`: "nothing
    about the store is recorded by wfctl. Git history is the only record."
  - `data-model.md` opening: "Nothing here is written to disk by wfctl", and
    "The only thing the store writes is git history"
  - `research.md §R15`: a successful store records a `store-specs` action with
    `_session.record_outward_action`
- Finding: The artifacts still disagree. The event doesn't break FR-014, since
  the pass never reads it, but the three statements are false.
- Why it matters: A reviewer checking the plan against
  `session-state-is-re-derived` reads a claim the design no longer makes.
- Suggested response: Say that the store writes git history and one action
  event, and that the pass reads only git.
- Corroborated by: deterministic checks

### PR-020: R6 and the data model define `stops_removal` in two ways, and they disagree for a spec dir inside the worktree

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R6` and `data-model.md §Store result`: `stops_removal` is
    true "for any result where the spec dir is inside the worktree and was not
    copied out", and false for every outcome for a spec dir outside it
  - `plan.md §Project Structure` `test_spec_store.py`: the `stops_removal`
    test for both sides
  - #40's record at `2e9f124`, `§Decision` and `§Verification`: the same rule,
    and a test for `not_applicable` inside the worktree
- Finding: Fixed in an earlier review and unchanged in substance.
- Why it matters: A merged `store` that returned `not_applicable` before the
  copy-out stops the removal instead of deleting the only copy.
- Suggested response: Fixed by `research.md §R6`, `data-model.md §Store
  result`, and the test. PR-024, still open, covers one consequence of the
  rule.
- Corroborated by: architecture and boundaries, security and reliability

### PR-021: The `archive-specs` contract promises exit 0 where #40's hook exits non-zero

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `contracts/cli.md §wfctl archive-specs`: the exit rule is narrowed to the
    store's outcomes, and `archive unsaved` keeps its own refusals once #40 is
    merged
  - `plan.md §Implementation order` step 7: the moved removal tests start from
    a clean worktree
- Finding: Fixed in an earlier review and unchanged since.
- Why it matters: A test built from the contract no longer fails for a reason
  unrelated to the store.
- Suggested response: Fixed by `contracts/cli.md §wfctl archive-specs` and
  step 7. See also `## Assumptions challenged` on what "clean" has to cover.
- Corroborated by: requirements and traceability

### PR-022: R8 lists the conflicted folders after the abort, and the command it names then prints nothing

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R8` point 1: the store reads the conflicted paths with
    `git diff --name-only --diff-filter=U` before it runs `git merge --abort`,
    and says why
  - `plan.md §Project Structure` `test_spec_store.py`: the conflict test
    expects the output to name the folder, which pins the order
- Finding: Fixed in an earlier review and unchanged since.
- Why it matters: An implementer following the sentence in order prints the
  conflicted folders.
- Suggested response: Fixed by `research.md §R8` point 1.
- Corroborated by: adversarial implementation and verification

### PR-023: #40's new sentence makes `not_applicable` inside the worktree exit 1 by hand, and this plan exits 0

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - #40's record at `b3fc797`, `§Decision`: "`store specs` run by hand still
    exits 1 for a copy-out refusal and for a spec-store failure, so a script
    can tell the spec files aren't backed up yet. It exits 0 when it reports a
    spec dir as not applicable, because in that layout no command could make
    it pass."
  - `research.md §R6`: "`not_applicable` exits 0 when `store specs` is run by
    hand, inside the worktree or not", and "#40's record at `b3fc797` agrees on
    `not_applicable`"
  - `plan.md §Project Structure` `test_spec_store.py`: "not_applicable for a
    spec dir inside the worktree sets stops_removal and still exits 0 by hand"
- Finding: Fixed in an earlier review. The rewording of R6 in this revision
  keeps the same agreement and the same test.
- Why it matters: Whichever branch merges second writes one exit code for the
  default layout, and a test holds it.
- Suggested response: Fixed by #40's record at `b3fc797`, `research.md §R6`,
  `data-model.md §Store result`, and the test.
- Corroborated by: architecture and boundaries

### PR-024: The new rule stops every removal when the spec store is its own checkout inside the worktree

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `research.md §R6` and `data-model.md §Store result`: `stops_removal` is
    true "for any result where the spec dir is inside the worktree and was not
    copied out". The edits to R6 in this revision left that sentence as it
    was.
  - `research.md §R2`: the `store` layout needs the root to be the top of its
    own checkout, on a branch of its own. Nothing requires that checkout to sit
    outside the code's worktree.
  - `spec.md §FR-021`: when the push fails at removal, removal warns and goes
    ahead. The spec's edge case on two stores says this is safe because "the
    files stay in the spec store outside the worktree".
  - #40's record at `b3fc797`: the copy-out runs "in the default layout", with
    `specs/` inside the worktree
- Finding: A spec store cloned inside the worktree, and ignored by the code
  repository, is the `store` layout with the spec dir inside the worktree. Read
  literally, R6 stops removal there even after `stored`, since nothing was
  copied out and #40's copy-out is for the default layout only, so every
  removal in that layout stops. Read as an outcome rule, a `not_pushed` there
  warns and goes ahead, as FR-021 says, and deleting the worktree deletes the
  unpushed commit. The plan's test covers `not_applicable` inside and every
  outcome outside, and neither reading of this case. This was left open on
  purpose, pending a design call.
- Why it matters: No repository uses this layout today, so the cost is
  bounded, but the two readings differ between a removal that never finishes
  and a commit that is lost.
- Suggested response: Say whether a spec store inside the worktree is
  supported. If it is, make `stops_removal` true there unless the result is
  `stored` or `already_stored`. If it is not, have `layout` read it as
  `unmanaged`.
- Corroborated by: security and reliability, adversarial implementation and
  verification

### PR-025: `block_action` has two callers, and the plan names one

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `research.md §R15`: "There are two callers, and both pass it:
    `build_report` in `_pipeline.py`, which answers `status` and `resume`, and
    `next_cmd` in `cli.py`, which writes `next-step.md`"
  - `plan.md §Project Structure` `cli.py`: the `next_cmd` entry, which "passes
    `block_action` from `by_step`, as `build_report` does (R15)"
- Finding: Fixed in an earlier review and unchanged in substance.
- Why it matters: `status` and `next-step.md` route a `store-specs` block the
  same way.
- Suggested response: Fixed by `research.md §R15` and the `next_cmd` entry.
  PR-026, now also fixed, covered which command the test runs to write
  `next-step.md`.
- Corroborated by: architecture and boundaries, adversarial implementation and
  verification

### PR-026: `wfctl resume` also writes `next-step.md`, so the new test can pass while `next_cmd` drops the argument

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Project Structure` `test_store_specs_pass.py`: the host-block
    routing test now checks "`status --json` and ... the `next-step.md` that
    `wfctl next` writes", and says `resume`'s copy goes through `build_report`
    and "would not exercise `next_cmd`"
  - `research.md §R15`: "`resume` writes `next-step.md` too, but from
    `build_report`'s answer, so only the copy `wfctl next` writes shows whether
    `next_cmd` passed it"
  - `wfctl/cli.py`: `next_cmd`, registered as `next`, calls
    `next_step_content` itself, and `resume_cmd` writes `next-step.md` from
    `build_report`'s result. Both claims are accurate.
- Finding: The test entry now names the command whose copy it reads, and that
  copy is the only one that fails when `next_cmd` drops `block_action`.
- Why it matters: The test catches the miss it was added for.
- Suggested response: Fixed by the revised test entry and `research.md §R15`.
- Corroborated by: adversarial implementation and verification

### PR-027: R6 says #40 exits 1 "only" for two cases, and #40's reason for exit 1 fits `committed_not_backed_up`, which this plan exits 0

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §R6`: "#40's record at `b3fc797` agrees on `not_applicable`",
    with no "only", and a new paragraph: "#40's record names no exit code for
    `committed_not_backed_up`, so this plan's data model decides it, and it
    exits 0", because "choosing a remote is the person's decision rather than
    the store's"
  - #40's record at `b3fc797`: no mention of an upstream branch or of
    `committed_not_backed_up` anywhere in the record, which confirms R6's
    reading
  - `data-model.md §Store result`: `committed_not_backed_up` exits 0
- Finding: R6 no longer claims #40 agrees on an outcome #40 never names. It
  says which side decides the exit code, gives the reason, and says #40 has to
  match if it later names one.
- Why it matters: An implementer reading R6 no longer takes #40's silence for
  agreement.
- Suggested response: Fixed by `research.md §R6`. PR-029 covers the test the
  decision still lacks.
- Corroborated by: architecture and boundaries

### PR-028: The sentence inserted into R15 leaves "Its docstring" pointing at the wrong function

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R15`: the paragraph now opens "`next_step_content`'s
    docstring says an outstanding pass is 'Checked after `blocked`'"
  - `wfctl/_pipeline.py` `next_step_content`: the docstring that holds that
    text
- Finding: R15 names the function whose docstring it quotes.
- Why it matters: The reason for the docstring change now points at the right
  function.
- Suggested response: Fixed by `research.md §R15`.
- Corroborated by: deterministic checks

### PR-029: No test pins the exit code R6 now decides for `committed_not_backed_up`

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `research.md §R6`: "#40's record names no exit code for
    `committed_not_backed_up`, so this plan's data model decides it, and it
    exits 0", and "If #40 later names an exit code for this outcome, it has to
    match this one"
  - `data-model.md §Store result`: `committed_not_backed_up` exits 0
  - `plan.md §Project Structure` `test_spec_store.py`: "each layout kind is
    detected" checks the layout and no exit code. The exit-code tests cover
    `not_pushed`, `merge_blocked_staged`, and `not_applicable`, and no test
    runs `store specs` by hand in the `store_no_upstream` layout.
  - #40's record at `b3fc797`, `§Decision`: `store specs` exits 1 "so a script
    can tell the spec files aren't backed up yet", which an implementer could
    read as covering this outcome
- Finding: R6 now treats this exit code as a decision another branch must
  respect, but nothing in the plan would fail if the branch that merges second
  gave it exit 1. PR-023 was the same kind of split, and a test closed it for
  `not_applicable`.
- Why it matters: Whichever branch merges second rewrites `store specs`, and
  #40's stated reason for exit 1 fits this outcome. No repository uses the
  `store_no_upstream` layout today, so the cost is bounded.
- Suggested response: Add a test that runs `store specs` by hand in a spec
  store with no upstream, expects `committed_not_backed_up`, and exits 0.
- Corroborated by: architecture and boundaries, adversarial implementation and
  verification

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Project Structure `store`; research R8 | covered |
| FR-002 | research R9 | covered |
| FR-003 | research R8 | PR-015 |
| FR-004 | plan.md §Technical Context Constraints | covered |
| FR-005 | contracts/cli.md §Never | covered |
| FR-006 | research R6, R7 | PR-010 |
| FR-007 | research R8 | PR-011 |
| FR-008 | data-model §Store result | covered |
| FR-009 | data-model §Store result `already_stored` | PR-007 |
| FR-010 | research R2 | PR-024 |
| FR-011 | research R6, R11; data-model §Store result | covered |
| FR-012 | data-model §Store result; research R6 | PR-009, PR-029 |
| FR-013 | data-model §Layout `unmanaged` | covered |
| FR-014 | data-model opening; plan.md §Constitution Check | PR-019 |
| FR-015 | research R3 | covered |
| FR-016 | research R3 | covered |
| FR-017 | plan.md §Project Structure `_pipeline.py` | covered |
| FR-018 | research R4; data-model §The store-specs pass | PR-006, PR-009 |
| FR-019 | contracts/cli.md §/store-specs; research R15; plan.md `next_cmd` | PR-018 |
| FR-020 | research R11; contracts/cli.md §archive-specs | covered |
| FR-021 | research R6, R11; plan.md §Implementation order step 7 | PR-024 |
| FR-022 | contracts/cli.md §archive-specs | covered |
| FR-023 | research R10; data-model §check specs | covered |
| FR-024 | data-model §check specs | covered |
| FR-025 | contracts/cli.md §check --help | covered |
| FR-026 | research R12 | covered |
| FR-027 | research R5 | covered |
| SC-001 | plan.md §Summary; research R15; quickstart §2 - 3 | covered |
| SC-002 | quickstart §7; plan.md tests in `test_archive_specs.py` | covered |
| SC-003 | contracts/cli.md §archive-specs | covered |
| SC-004 | research R3; quickstart §4 | covered |
| SC-005 | plan.md tests in `test_spec_store.py` | covered |
| SC-006 | research R14; quickstart §6 | PR-008 |

## Assumptions challenged

- `contracts/cli.md §wfctl archive-specs` and `plan.md §Implementation order`
  step 7 ask the moved removal tests for a "clean worktree", and the reason
  they give is uncommitted edits. #40's `archive unsaved` also refuses commits
  that aren't pushed or merged, so a fixture whose branch carries one fresh
  commit with no upstream is clean in the usual sense and still fails. The
  contract's sentence before it names both, so the intent is clear, but step 7
  names only a dirty worktree.
- `research.md §R15` reads one block per step. `_apply_block_hold` keeps the
  most recently filed block when two actions hold one step, so a `push` block
  filed after a `store-specs` block routes to `wfctl verify` while the
  `store-specs` hold still stands. That follows the existing rule for which
  block applies, and the plan doesn't mention it.
- `research.md §R8` point 1 writes `.git/MERGE_HEAD`. In pfms the spec store is
  a worktree, whose `MERGE_HEAD` lives in its own git directory. The command R8
  gives, `git rev-parse -q --verify MERGE_HEAD`, finds it either way, so only
  the path in the prose is off.
- `research.md §R6` says exit 1 lets the orchestrate stall count stop an
  unattended run. The stall count in `wfctl/_stall.py` never reads an exit
  code. A store that keeps failing still stalls, because none of the files it
  digests change. The behaviour holds, and only the stated reason is wrong.
- `research.md §R2` assumes the store's git calls reach the spec store. A
  `GIT_DIR` or `GIT_WORK_TREE` exported in the calling environment would send
  them to another repository, and the store's subprocess environment could
  clear both.
- `research.md §R15` assumes the `/store-specs` wrapper files its block under
  exactly `store-specs`. The routing rule also matches on that spelling, so the
  wrapper's text is the whole link for both the release and the route. No test
  in the plan reads the installed wrapper for it.
- Only this branch names the property `stops_removal`. #40's record says "the
  store's result says whether the outcome stops the removal" without naming
  it. Whichever branch merges second reconciles the name and the result type
  along with `store specs` itself, which is more than the "one function" that
  `plan.md §Risks` describes.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- `research.md §R6` now says which side owns each exit-code decision. #40 and
  this plan agree on `not_applicable`, and for `committed_not_backed_up` R6
  says #40 is silent, that this plan decides, and why.
- The routing test in `test_store_specs_pass.py` says which command's copy of
  `next-step.md` it reads and why the other copy would not do, so the reason
  survives into the test.
- `research.md §R6` keeps two questions apart: whether removal stops, which
  `stops_removal` answers, and what `store specs` exits by hand. One test pins
  both answers on the outcome where they differ.
- `research.md §R8` point 1 says why the read comes before the abort and cites
  the reproduction, so the order is not left for an implementer to rediscover
  through a red test.
- The implementation order writes the `merge --abort` test before any store
  code, so the level-3 record's open assumption is tested before anything is
  built on it.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
