# Research: wfctl stops a review group after three rounds

Each entry below is a decision the plan rests on, the reason for it, and the
alternatives we didn't choose. The spec left nothing marked NEEDS
CLARIFICATION, so these come from reading the code `review start` already runs.

## R1. One parser for `review.rounds`

**Decision**: `_review_config` parses and validates `review.rounds` in one
function, `parse_rounds`. `load` calls it on the working tree's `wfctl.json`, so
`wfctl check config`, `review start`, and the worktree guard all report an
invalid value. The trunk read in R2 calls the same function on the trunk's copy.
`rounds` joins `_REVIEW_KEYS`.

A valid value is an `int` of 0 or more, and not a `bool`. `True` is a subclass
of `int` in Python, so `"rounds": true` would otherwise pass as 1. That's the
same check `_is_count` makes for a reviewer count.

**Rationale**: The module's docstring says it is the one reader for every
caller, "so `wfctl check config`, `wfctl review start` and the worktree guard
can't disagree". If the trunk read had its own validator, a value `check config`
accepts on a branch could fall back to the default once it merged.

**Alternatives considered**:

- Validate in `_review.py` beside the trunk read. We didn't choose this because
  it makes a second reader of the `review` key, and the two would drift.
- Return the cap from `load` beside the groups. We didn't choose this because
  `load` has three callers that use only the groups, and the working tree's cap
  is read only for the mismatch warning. A small `load_rounds` helper serves
  that one caller.

## R2. Reading `wfctl.json` from the trunk

**Decision**: `_review.trunk_rounds(repo_root, timeout, branch=...)` reads the
first ref `trunk_refs` returns, which is `refs/remotes/origin/<trunk>` when it
exists and the local branch otherwise. It runs two git commands through
`_review._git`:

1. `git ls-tree --name-only <ref> -- wfctl.json`. Empty output means the trunk
   has no `wfctl.json`, and the cap is the default with no warning.
2. `git show <ref>:wfctl.json`. `trunk_rounds` parses the text with
   `json.loads` and takes the `review` value. When the top level or `review`
   isn't an object, the cap is the default with a warning. Otherwise `review`
   goes to `_review_config.parse_rounds`. A trunk with no `review` key gets the
   default with no warning.

It returns the cap, the short ref name for messages (such as `origin/main`), and
a warning line or None.

The two git commands and the JSON parse live in one helper,
`_read_config_at(repo_root, ref, timeout)`, which returns the parsed object or
a reason it couldn't be read. `review_trunk` in R11 reads the default branch's
file through the same helper.

**Rationale**: `trunk_refs` is the ref `commit_range` measures from, so the cap
and the commit range come from the same trunk. `_git` passes
`--no-replace-objects` and turns off grafts, which keeps this read on the real
objects like every other read in the module. Asking `ls-tree` first gives a
clear answer for a missing file. Otherwise wfctl would have to tell "no such
path" apart from other `git show` failures by matching stderr text, and that
wording changes between git versions.

**Alternatives considered**:

- Read the local `main`. We didn't choose this because a person's local `main`
  usually trails `origin/main`, which is why `trunk_refs` puts the remote first.
  The local ref is still the fallback when there's no remote. The cap record
  accepts that an agent can move a local ref.
- Read the trunk with `git show` alone and treat any failure as "no file". We
  didn't choose this because a real git failure, such as a timeout, would then
  fall back to the default without saying anything.
- Run `git fetch` before reading. We didn't choose this because `review start`
  makes no network call today, and a stale `origin/main` is already the trunk
  the commit range uses.

## R3. Counting the runs a group has started

**Decision**: `_review.runs_started(agent_dir, group)` counts the run folders
holding a `run.json`. It shares one helper, `_run_numbers`, with `latest_run`,
so both functions skip the same folders.

**Rationale**: `latest_run` already skips a folder with no `run.json` because it
belongs to an interrupted start. If the count used a different rule, the count
and the next run number could disagree. The count is derived on every call, as
`session-state-is-re-derived.md` requires.

**Alternatives considered**:

- Use the latest run's number as the count. We didn't choose this because the
  number can skip, since `start` steps past a folder another start created
  first. The count is the folders that hold a record.
- Count `review-start` events in `events.jsonl`. We didn't choose this because
  the run folders are what `check`, `relay`, and the guard read, so a count from
  a second source could disagree with them.

## R4. The order `start` decides in, and the sign-off check

**Decision**: `_review.start` gains a `cap: int` parameter and decides in this
order:

1. Compute the commit range. With no commits, return as today (outcome 1).
2. Count the runs started. Under the cap, write the run (outcome 2).
3. At or past the cap, check whether the sign-off covers every commit in the
   group's range. If it does, return a `Started` with no run and
   `sign_off` set to the signed-off commit (outcome 3).
4. Otherwise raise `RoundCapReached` (outcome 4).

The sign-off check moves into one helper, `_covered_by_sign_off(repo_root,
agent_dir, timeout)`. It returns the signed-off commit, or None, and a function
that answers, for any commit, whether the sign-off covers it. Outcome 3 prints
the signed-off commit. `unreviewed` and `start` both use the helper, and both
apply it to every commit in the range. A commit is covered when it is the
signed-off commit or one of its ancestors, and only when the repository has the
signed-off commit.

**Rationale**: The spec fixes the order in FR-002. Checking the range first
keeps "up to date" true at the cap. Sharing the helper keeps `review start` and
the guard in agreement about what a sign-off covers. If `start` refused where
the guard allows the PR, it would ask the user for a sign-off they already gave.

That's why `start` checks the range and not the head. `commit_range` leaves out
a merge of the trunk that git would have made on its own. So when the agent
merges `main` cleanly after a sign-off, the new head isn't covered, but every
commit in the range still is. The guard allows that PR, and checking the head
would make `review start` refuse it.

**Alternatives considered**:

- Check whether the sign-off covers the head. We didn't choose this because it
  disagrees with the guard after a clean merge of the trunk, as above.
- Call `unreviewed` from `start`. We didn't choose this because `unreviewed`
  computes the range for every group, and `start` already has its own group's
  range.

## R5. Where the cap is read

**Decision**: The `review start` command reads the cap before it calls
`_review.start`, prints any warning, and passes the cap in. The command does
this in four steps:

1. Load the groups from the working tree. An invalid `review.rounds` there
   refuses here, as any other invalid `review` setting does (clarify Q1).
2. Call `review_trunk` (R11) and print its warning.
3. Call `trunk_rounds` and print its warning.
4. Compare the cap with `load_rounds(repo_root)`. When the working tree sets a
   different valid value, print the mismatch warning.

A `ReviewError` from step 2 or 3, such as no trunk, prints `✗` and the message
on one line, and exits 1, the same as an error from `start`.

**Rationale**: Each warning is about the configuration, not the run, so it is
printed whichever outcome follows, outcome 1 included. A user who raised the cap
on the branch sees why it hasn't taken effect, even when there's nothing to
review. `_review.start` stays free of output, as it is today.

**Alternatives considered**:

- Read the cap inside `_review.start` and return the warnings in `Started`. We
  didn't choose this because outcome 4 raises rather than returns, so the
  warnings would also need to ride on the exception.

## R6. The refusal

**Decision**: `RoundCapReached(ReviewError)` carries the group, the count, and
the cap, and its message is the first line of outcome 4:

| State | First line |
| --- | --- |
| count equals the cap | `security has run 3 of 3 rounds on this branch, the most review.rounds allows` |
| count above the cap | `security has run 4 rounds on this branch, more than the 3 review.rounds allows` |
| cap is 0 | `review.rounds is 0, so security doesn't run on this branch` |

The command prints `✗ ` and the message, then the second line:
`  Ask the user to run `wfctl review sign-off` in their own terminal.`. It exits
1. Nothing is written, since the refusal happens before the run folder is made.

**Rationale**: Making it a subclass of `ReviewError` keeps the command's one
`except` clause. A separate class lets the command add the second line only for
this refusal. The message wording follows the clarify answers.

## R7. Two starts at once

**Decision**: Accepted, not handled. Two `review start` calls for the same group
that run at the same moment can both read a count of 2 under a cap of 3, and
both write a run.

**Rationale**: The panel skill runs one group at a time, and `start` already
guarantees that two racing starts get different run numbers. The count is
tamper-evident rather than unforgeable, the same limit `review-round-count.md`
accepts. Recounting after the folder is made would need a lock to be exact.

## R8. The header and the panel skill

**Decision**: The header gains ` · round N of M` after the run number. N is the
count before this run plus 1, and M is the cap.

**Rationale**: The spec's assumption flagged the `_say` docstring in
`wfctl/cli.py`, which says the panel skill parses these lines. Reading
`fanning-out-code-review` Steps 1 and 2 shows what it parses: the `reports:`
path and one reviewer per roster line. The header is shown as an example and
read as prose. So adding the round breaks nothing in the skill. The test that
asserts the exact header, `test_start_prints_the_run_the_reports_path_and_one_line_per_reviewer`,
changes with it.

## R9. The worktree guard

**Decision**: No code change in `_review_gate`. The guard calls `unreviewed`,
which reaches `trunk_refs`, so it measures each group's commits against the
trunk `review_trunk` finds (R11). It prints none of `review_trunk`'s warnings.
`_review_gate` calls `_review_config.load`, so once `rounds` is a known key it
passes. An invalid branch value makes the guard fail with `can't read the
review config`, the same as any other invalid `review` setting.

`_judge` still reads `_paths.trunk_branch` directly, for its same-name check and
for the rule that only the checkout on the trunk merges another branch's PR.
Those checks decide where a command may run, not which commits count as
reviewed, so the branch's own `trunk` setting there can't hide a commit.

**Rationale**: That matches clarify Q1, where an invalid value on the branch is
refused like any other. The guard reads only whether commits are unreviewed or
signed off. It never needed the cap.

The trunk read adds up to five git calls per `trunk_refs` call:
`symbolic-ref`, `config --get-all`, a ref check, `ls-tree`, and `show`. A
branch that declares a different trunk adds up to two more, to resolve that
name. The guard makes one `trunk_refs` call per group, so a repository with
three groups adds up to 21 local git calls to each PR the guard checks. Each one takes a few
milliseconds. Each runs under the guard's 5-second timeout, and a call that
times out ends the check with an error, so the timeouts don't add up.

## R10. The skill and doc text

**Decision**:

1. `opening-a-change` Step 1, lines 73 - 89: each group runs once per round, in
   order. Security doesn't run again over its own fixes. wfctl counts the rounds
   and refuses the fourth, and the agent then stops and asks the user to sign
   off or say how to proceed. The sentence saying wfctl doesn't count rounds yet
   goes.
2. `opening-a-change`, the guard-refusal bullet at line 375: when `review start`
   refuses a round, ask the user for a sign-off.
3. `fanning-out-code-review`, line 82: the example header gains `round 3 of 3`.
   The paragraph after it gains one sentence for each of outcomes 3 and 4.
4. `AGENTS.md` "Declaring reviewers": one paragraph on `review.rounds`, covering
   what it caps, the default of 3, that 0 means every change needs a sign-off,
   and that wfctl reads it from the trunk. A second paragraph says reviews read
   `trunk` from the default branch, so a repository whose trunk isn't its
   default branch declares it there.
5. Two release notes. `changes/626.addition.md` covers the new `review.rounds`
   key and the refusal. `changes/626.change.md` covers what an existing user
   relies on that now behaves differently: each group runs once per round, and
   reviews read `trunk` from the default branch, with the upgrade step for a
   repository whose trunk isn't its default branch.

**Rationale**: These are the places that describe the round limit today. The
agent reads `fanning-out-code-review` each time it runs `review start`, so that
skill is where it learns what the two new outcomes mean.

## R11. Reviews read the trunk from the default branch

**Decision**: Reviews stop trusting the branch's own `trunk` setting. wfctl
reads the trunk from `wfctl.json` on the repository's default branch, the one
`origin/HEAD` names, the same way it reads `review.rounds` from the trunk. A
branch that names a different trunk gets a `⚠` warning, and the review goes on
against the default branch's trunk. The difference alone is never refused.

A new function, `_review.review_trunk(repo_root, timeout)`, finds the trunk in
five steps:

1. Read `origin/HEAD` with `git symbolic-ref --quiet --short
   refs/remotes/origin/HEAD`, through `_git` with `answers=(0, 1)`. Exit 1
   means there's no `origin/HEAD`, so go to the fallback below. Without
   `--quiet`, a missing `origin/HEAD` exits 128, the same as any fatal git
   error, and the two rows of the table below couldn't be told apart.
2. Check that `origin` fetches every branch, the same test
   `_refuse_a_single_branch_clone` makes today. A clone that fetches only some
   branches can have an `origin/HEAD` that names the branch under review, so
   wfctl doesn't trust it and goes to the fallback.
3. Check that the ref `origin/HEAD` names exists. If it doesn't, as after the
   default branch is renamed, raise a `ReviewError` that says to run
   `git remote set-head origin --auto`.
4. Read `wfctl.json` on that ref with `ls-tree` and `show`, through the helper
   R2 uses for the cap. The trunk is the file's `trunk` value. With no file or
   no key, the trunk is the default branch itself.
5. Compare the trunk with the working tree's declaration from
   `_paths.declared_trunk`. When the working tree names a different branch,
   resolve that name with `_paths._resolve_declared`. If the clone has the
   branch, return the mismatch warning. If it doesn't, raise `NoTrunk`, as
   today. When the working tree's value isn't a branch name at all, raise
   `NoTrunk` too, as today.

Step 5 refuses a branch name the clone doesn't have, rather than warning,
because the guard refuses the same branch. `_judge` reads
`_paths.trunk_branch` directly and raises `NoTrunk` for it before it calls
`unreviewed`. A warning in `review start` would tell the user the change can
merge, and the guard would then refuse the PR. Refusing in both places keeps
today's behavior and its two tests,
`test_range_with_no_trunk_branch_names_the_trunk_key` and
`test_start_with_no_trunk_branch_names_the_trunk_key`. A branch can only refuse
its own reviews this way, so it gains nothing against the cap.

The fallback is today's resolution, `_paths.trunk_branch`, with its
single-branch clone refusal. It reads the working tree's `trunk` first, so in
these layouts the branch still chooses its own trunk:

- a remote added with `git remote add`, which records no `origin/HEAD`;
- a bare clone;
- a clone made with `--single-branch`.

That's a known limit, recorded in `review-round-cap.md`'s Consequences.

`trunk_refs` calls `review_trunk` in place of `_paths.trunk_branch`, and its
signature doesn't change. After that, it runs today's checks in today's order:
the same-name check, then the ref lookup that raises `NoTrunk`. `commit_range`,
`start`, `unreviewed`, `review sign-off`, and the guard's `unreviewed` call all
go through `trunk_refs`, so they all measure against the same trunk.
`trunk_rounds` reads the cap from the trunk `review_trunk` returns. The `review
start` command calls `review_trunk` once more to print its warning, since
`trunk_refs` returns only refs. The `trunk_refs` docstring is rewritten to say
the trunk comes from `review_trunk`. Its line "A declared trunk is used either
way" holds only on the fallback path now.

`ReviewTrunk` also records where the trunk came from: the default branch's
`wfctl.json`, or the fallback. On the default-branch path, the same-name
message and the `NoTrunk` message name that file, such as `check trunk in
wfctl.json on origin/main`. On the fallback path they keep today's wording,
which points at the working tree's `wfctl.json`, since that's the file wfctl
read. Otherwise the user is sent to edit a file wfctl no longer reads, and the
edit only adds a mismatch warning.

Each case has one answer:

| Case | Trunk used | Warning |
| --- | --- | --- |
| No `origin/HEAD` | today's resolution | none |
| `origin` doesn't fetch every branch | today's resolution, including its refusal | none |
| `origin/HEAD` names a ref this clone doesn't have | refused, with `git remote set-head origin --auto` | — |
| No `wfctl.json` on the default branch, or no `trunk` key | the default branch | none |
| `trunk` is a branch name the clone has | that branch | none |
| `trunk` is a branch name the clone doesn't have, such as a deleted `develop` | refused with `NoTrunk`, naming `wfctl.json on origin/main` | — |
| `trunk` isn't a non-blank string, or is `HEAD` | the default branch | `trunk on origin/main isn't a branch name; wfctl reviews against main` |
| `wfctl.json` isn't valid JSON, or isn't an object | the default branch | `can't read wfctl.json on origin/main (<reason>); wfctl reviews against main` |
| The working tree names a different trunk the clone has | the default branch's trunk | `this branch sets trunk to loose, but wfctl reads main from origin/main until the change merges` |
| The working tree names a trunk the clone doesn't have | refused with `NoTrunk`, as today | — |
| The working tree's `trunk` isn't a branch name | refused with `NoTrunk`, as today | — |
| A git call fails or times out | refused, as any other git failure in `_review` | — |

A default-branch `trunk` the clone doesn't have is refused rather than warned
about, unlike a value that isn't a branch name. The repository named a real
trunk, and measuring against the default branch instead would review the wrong
commits with no sign anything was off. The usual cause is a clone that hasn't
fetched the branch, which `git fetch` fixes, and `check config` reports a name
that doesn't resolve before it merges.

The command prints these warnings. The guard prints none of them, since it
reports only a refusal.

**Rationale**: The plan's first version refused a branch that changed the
trunk, and that refusal had no way past it. `review sign-off` calls
`unreviewed`, which reaches `trunk_refs`, so the user's own sign-off was
refused by the same check. A PR that changed the trunk on purpose was refused
too. Reading the trunk from the default branch removes the reason to refuse.
The branch's setting no longer moves the cap or the commit range, so there's
nothing to block. The warning tells the user why their edit hasn't taken
effect, the same as the cap's mismatch warning.

A changed trunk did two kinds of damage, and this closes both. It could raise
the cap, and it could hide the branch's commits from the PR check, since
`commit_range` leaves out every commit the trunk has. Both read the trunk
through `trunk_refs`.

The default branch is the source because the agent can't push to it. A
repository whose trunk isn't its default branch, such as `develop`, now has to
declare that in the default branch's `wfctl.json`. Today a repository can
declare it only on the branch its work starts from. After this change, reviews
in such a repository measure against the default branch until the declaration
lands there, and every branch shows the mismatch warning. `AGENTS.md` and the
release note say so.

A ref that `origin/HEAD` names but the clone doesn't have is refused rather
than skipped. Skipping it would let a deleted ref turn the check off with no
message, and `git remote set-head origin --auto` fixes it in one command. A
bad `trunk` value on the default branch warns and uses the default branch
rather than refusing. A refusal there would stop every review in the
repository until someone fixed the trunk, which is the reason R2 warns on a bad
cap instead of refusing.

The way around this is still a local ref move: pointing `origin/HEAD` at
another branch with `git remote set-head`, or deleting it so the fallback
runs. `review-round-cap.md` already accepts a local ref move.

**Alternatives considered**:

- Refuse a branch that names a different trunk. We didn't choose this because
  the refusal blocked the sign-off that was supposed to get past it, and a
  deliberate trunk change had no route through.
- Exempt `review sign-off` from the refusal. We didn't choose this because the
  sign-off would then list commits counted against the branch's chosen trunk,
  and the user signing off would never see the commits that trunk hides.
- Compare with the remote's default branch name directly. We didn't choose
  this because it gets every repository whose trunk isn't its default branch
  wrong.
- Fall back to a bare layout's own HEAD before the working tree. We didn't
  choose this because it covers one of the three layouts, and the fallback
  already reads the bare HEAD when the working tree declares nothing.
- Check only in `trunk_rounds`. We didn't choose this because the PR check
  reads the same trunk, and a changed trunk would still hide commits from it.
