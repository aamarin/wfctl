# Research: CI review check

Each entry gives the decision, why, and what else was weighed. Facts marked
"checked" were run or read on 2026-10-25 after merging `main` with #642.

## R1. A note on commit C covers every branch commit up to C

**Decision**: the notes reader treats a group's line on commit C as that group
having reviewed every commit on the branch that C can reach.

**Rationale**: checked in `wfctl/_review.py`. `start` calls `commit_range`
with the group's last reviewed commit (line 542). `commit_range` starts the
range at that commit when it is an ancestor of the head, and at the merge base
with the trunk otherwise (lines 286 - 292). `check` moves the last reviewed
commit to the run's head on completion (line 707). So each completed run
covers from the previous run's head, or from the merge base after a rebase, up
to its own head. A chain of runs therefore covers every branch commit the last
noted commit can reach. This was the third assumption in `design.md`, and it
holds.

**Alternatives considered**: storing the run's base in the note as well. We
didn't choose it because the chain already implies the base, and a base line
would break the one-line-per-event format that lets `cat_sort_uniq` merge
notes (`627-review-note-line-per-event.md`).

## R2. The CI command is `wfctl check reviews`

**Decision**: the CI command is `wfctl check reviews`, and the resend command
is `wfctl store reviews`.

**Rationale**: the `check` group already holds `check specs` and `check
config`, each a read-only verdict that exits 1 on a finding. `store` holds
`store specs`, which pushes. The pair `check reviews` and `store reviews`
mirrors `check specs` and `store specs`, so a reader who knows one pair can
guess the other. `review ci` was the working name. It ties the command to
where it runs rather than what it does, and a person can run the same check
locally before pushing.

**Alternatives considered**: `wfctl review ci`, rejected for the reason above.
`wfctl review verify`, rejected because `verify` already names the
definition-of-done run.

## R3. The notes reader walks only the branch's own commits

**Decision**: the reader lists the commits on the head that the trunk can't
reach, in topological order, with their notes, in one git call:

```
git log --topo-order --format=%x01%H%n%N --notes=refs/notes/wfctl-review \
    <head> --not <trunk refs> --
```

A group's last reviewed commit is the first commit in that order whose note
has `reviewed by <group>`. The signed-off commits are every listed commit
whose note has `signed off by a person`.

**Rationale**: commits on `main` carry notes from their own PRs' reviews.
Walking all of history could pick one of those as a group's last reviewed
commit. That pick is harmless, since `commit_range` would still list the
branch's own commits, but it makes the two readers disagree for no reason.
Walking only the branch matches what the state directory holds. Any noted
commit the reader picks is safe, because a note implies coverage of
everything it can reach (R1). Picking a less recent one can only list extra
commits as unreviewed, never hide one. The trunk refs come from
`_review.trunk_refs`, so both readers use the same trunk.

**Alternatives considered**: `git notes list` followed by `git cat-file
--batch`. It gives the same answer in two calls and needs its own order. A
walk over all of history was rejected for the reason above.

## R4. GitHub runs `main`'s copy of the job, on `pull_request_target`

**Decision**: the job lives in a new `.github/workflows/review.yml`, triggered
by `pull_request_target`. GitHub then runs the workflow file from the base
branch. The job checks out the base branch into `trusted/` and the PR's head
commit into `pr/`, and runs `uv run --project trusted wfctl check reviews`
with `pr/` as its working directory. Nothing in `pr/` is executed.

**Rationale**: the maintainer chose this in the plan session (spec
Clarifications, 2026-10-25). Under `pull_request`, GitHub runs the PR's own
workflow file and the job would run the PR's own wfctl, so a PR that broke the
check code would pass its own check. `pull_request_target` is risky when a job
runs the PR's code with the base repository's token. This job only reads the
PR's commits, notes, and `wfctl.json` as data, and asks for `contents: read`.

`uv run --project trusted` installs the base branch's wfctl into
`trusted/.venv`. The entry point's `sys.path` starts at the venv's `bin`, not
the working directory, so a Python file in `pr/` isn't imported.

**Assumed, checked after merge**: a `pull_request_target` job reports its check
on the PR's head commit, so the ruleset's `review` requirement is met. GitHub
reads this workflow from the base branch, so a throwaway PR can test it only
once `review.yml` is on `main` (quickstart.md, step 2). If it doesn't hold, the
fallback keeps `pull_request` and runs `main`'s wfctl from the `trusted/`
checkout. That fallback runs the PR's own workflow file, which FR-017a
forbids, so it needs FR-017a amended first, and that is the maintainer's
decision. The ruleset isn't applied until one of the two is settled. R8's
rerun lookup assumes the `pull_request_target` check too, so the fallback
would mean checking R8 again.

**Bootstrap**: this feature's own PR gets no `review` job, since `main` has no
`review.yml` yet. It relies on the local guard, and the ruleset entry is
applied by hand only after the post-merge check passes.

**Alternatives considered**: `pull_request` with the PR's own wfctl, as the
design first had it. The maintainer rejected it for the reason above.
`pull_request` with a `trusted/` checkout of `main`, kept as the fallback.

## R5. CI finds the trunk with `git remote set-head origin --auto`

**Replaced by R14.** The job now names the trunk with `--base` from the
event, so it runs no `set-head` step. The probe findings below still hold and
explain why `trunk_refs`' single-branch refusal doesn't fire in CI.

**Decision**: a job step runs `git -C pr remote set-head origin --auto` before
the check. `wfctl.json` gains no `trunk` key.

**Rationale**: checked in the probe run on draft PR #647. `actions/checkout`
with `fetch-depth: 0` leaves `origin/main` and full history but no
`origin/HEAD` and no local `main`, and the step set `origin/HEAD` to
`origin/main`. `_paths.trunk_branch` then finds `origin/main`. `trunk_refs`
refuses a single-branch clone unless `remote.origin.fetch` covers every
branch (`642-origin-head-trusted-on-full-fetch.md`). `actions/checkout`
adds `origin` with `git remote add`, which writes the default
`+refs/heads/*:refs/remotes/origin/*` refspec, so the refusal shouldn't fire.
The job's first run on a throwaway PR confirms it.

The step works in any repository that copies the job, whatever its default
branch is called. A `trunk` key would be one more thing each repository has to
set.

**Alternatives considered**: a `trunk` key in `wfctl.json`. Rejected for the
reason above, though `trunk_branch` already honours one if a repository sets
it.

## R6. Recording a line reads the note first

**Decision**: `record(repo_root, sha, line)` reads the commit's note and
appends the line only when it isn't there yet.

**Rationale**: FR-003 forbids a duplicate line, and `git notes append` adds
one every time. `wfctl review check` on an already-complete run returns
`complete` again, so the CLI would otherwise append a second `reviewed by
security`. Reading first makes `record` idempotent. A note added on a
completion whose push failed is still there, and a later `check` or `store
reviews` sends it. The design record says recording doesn't read first; this
read only skips a duplicate and doesn't merge anything, so the record's point
stands: wfctl needs no merge logic of its own.

**Alternatives considered**: appending only when this call completed the run.
A crash between completion and the append would then leave a run with no note,
and nothing would add it later.

## R7. Sending the notes, and the rejected push

**Decision**: `send(repo_root)` pushes `refs/notes/wfctl-review` to `origin`
with the spec store's 60-second network timeout. When `origin` rejects it as
not a fast-forward, `send` fetches the remote ref into
`refs/notes/wfctl-review-remote`, runs `git notes --ref=wfctl-review merge -s
cat_sort_uniq refs/notes/wfctl-review-remote`, deletes the temporary ref, and
pushes once more. A second rejection is an error naming the cause.

**Rationale**: the scratch repository test in the design session showed
`cat_sort_uniq` joins both clones' lines and the next push succeeds (git
2.44.0). One retry is enough for one user. A loop would only matter with many
machines racing.

`store reviews` compares the local ref with `git ls-remote origin
refs/notes/wfctl-review` first, and reports "nothing to send" when they match.
A missing local ref is also "nothing to send".

**Alternatives considered**: always fetch and merge before pushing. It costs a
network round trip on every completion to handle a race one user rarely
meets.

## R8. Rerunning the failed job

**Decision**: after a successful push, `rerun(repo_root, branch)` runs `gh pr
view --json number,headRefOid` for the branch. If the branch has an open PR, it
runs `gh pr checks <number> --json name,state,link` and finds the check named
`review`. If that check's state is `FAILURE`, it reads the run id and job id
from the link (`…/actions/runs/<run>/job/<job>`) and runs `gh run rerun <run>
--job <job>`. A missing PR, a missing check, or a check that didn't fail
reruns nothing. When `gh` isn't installed, or `origin` isn't a GitHub
repository, the rerun does nothing and prints nothing, since there's no check
to rerun there. Any other `gh` failure prints a warning telling the user to
rerun the check on the PR, and leaves the exit code alone. wfctl doesn't
retry.

**Rationale**: `gh pr checks` reports checks on the PR's head commit
whichever event made them, which suits a `pull_request_target` job whose run
may not list the PR's branch as its own. Rerunning one job by id leaves any
other failed job alone. The job name `review` is part of the job's contract
(`contracts/review-job.md`), the same as the ruleset relies on it.

**Assumed, checked after merge**: the link `gh pr checks` returns for an
Actions job has that shape. Quickstart step 3 checks it on the throwaway PR.

The warning names a manual rerun, not `store reviews`. When the push worked
and only the rerun failed, local and remote notes match, so `store reviews`
would report "nothing to send" and rerun nothing. The maintainer decided in
the plan walkthrough that wfctl doesn't make up for a GitHub error, and the
user reruns the check.

**Alternatives considered**: `gh run list --workflow review.yml --branch
<branch>`. For `pull_request_target` the run's branch may be the base branch,
so the lookup could miss the PR's run. `gh run rerun --failed`, which would
also rerun a failing test job nobody asked about.

## R9. The guard's notes rules

**Decision**: `_review_gate.read` adds two text rules, in the same first pass
as the sign-off refusal:

1. A `git` command whose words include `notes` followed by `add`, `append`,
   `edit`, `copy`, `merge`, `remove`, or `prune`, allowing options such as
   `--ref x` or `-c core.notesRef=x` before or between them.
2. A `git` command whose words include `push` and either an argument holding
   `refs/notes/` or the `--mirror` option.

Each rule reads one command between the separators `_SEPARATOR` already
splits on. `_hook.py`'s substring test adds `"notes" in command` and
`"--mirror" in command`.

**Rationale**: `627-guard-blocks-note-writes.md` decided on every notes ref
rather than ours, so the rules never ask which ref a write targets. Reading
stays allowed: `git notes show`, `git notes list`, `git log --notes`, and a
plain `git push`.

**Alternatives considered**: refusing only `refs/notes/wfctl-review`, rejected
in the design record.

## R10. `unreviewed` takes coverage as arguments

**Decision**: the new signature is

```python
def unreviewed(
    repo_root: Path,
    groups: Sequence[Group],
    head: str,
    last_reviewed: Mapping[str, str | None],
    signed_off: Sequence[str],
    timeout: float | None = None,
    *,
    branch: str | None = None,
    trunk: str | None = None,
) -> dict[str, tuple[str, ...]]
```

`trunk` is the branch `--base` names (R14). `unreviewed` passes it to
`commit_range`, which passes it to `trunk_refs`. `None` keeps today's lookup.

`coverage_from_state(agent_dir, groups)` in `_review.py` returns the two
values from the state directory, with the one sign-off as a tuple of zero or
one commit. `coverage_from_notes(repo_root, head, groups, timeout, *, branch,
trunk)`
in `_review_notes.py` returns them from the notes (R3). A signed-off commit
this repository doesn't have is dropped, as `unreviewed` does today. A commit
is covered when it is any signed-off commit or an ancestor of one.

**Rationale**: `627-unreviewed-takes-coverage.md`. The two callers,
`_review_gate.py:780` and `cli.py:6262`, each gain one call to the state
reader and keep their results (FR-010).

**Alternatives considered**: in the design record.

## R11. Where the note is recorded

**Decision**: the CLI records the note, not `_review.check` or
`_review.sign_off`. `review check` records `reviewed by <group>` on the run's
head whenever the run is complete. `review sign-off` records `signed off by a
person` on the head after writing the sign-off. Each then sends and reruns.

**Rationale**: `_review.py` stays a state directory module with no remote
calls, and its tests need no notes setup. The CLI already holds the repo root
and the branch.

**Alternatives considered**: recording inside `_review.check`. It would put a
git write and a push inside a function the guard also imports.

## R12. The release sign-off

**Decision**: `release.py` prints, after opening the PR, the two commands the
maintainer runs: `git switch release/v<version>`, then `wfctl review
sign-off`. They go in the script's closing output beside the existing
`--cleanup=verbatim` hint. `review.yml` has no exception for release
branches.

The script ends with `git switch main` (`release.py` line 398), and the
sign-off refuses to run on the trunk. Printing the switch keeps the sign-off
CLI unchanged. A commit argument on the sign-off would also work, but it adds
a CLI surface for one caller, and the switch is one line.

**Rationale**: spec Clarifications, 2026-10-24. A scripted sign-off would let
an agent that runs `release.py` cut and merge a release with nobody involved.

**Alternatives considered**: in the spec's clarification.

## R13. CI requires `main`'s groups plus the PR's additions

**Decision**: `wfctl check reviews` builds its group list from two files it
reads from git: `git show <trunk ref>:wfctl.json` and `git show
<head>:wfctl.json`. It requires every group the trunk lists, then appends
every group the head lists that the trunk doesn't, matched by name. A missing
file, or one with no `review` key, gives the default groups for that side.
The trunk ref is `trunk_refs`' first entry, the same one the range uses. In
CI that is `origin/<base>` from `--base` (R14). A problem in either file's
`review` key is a cause-naming failure under FR-016.

**Rationale**: the maintainer decided this in the plan walkthrough. A PR that
removes a group from its own `wfctl.json` shouldn't skip that group's review
on the same PR, so the trunk's list governs. A PR that adds a group means the
group should run, so it is required on that PR too. Reading both files from
git, rather than from the working tree or the `trusted/` checkout, means the
command needs no flag and gives the same answer locally and in CI. Only group
names matter here, since CI reads notes by group name and never counts
reviewers.

The local commands use the same list, as the maintainer decided after the
second plan review (PR-012). The guard and `wfctl review sign-off` call the
function `check reviews` calls, so a PR that removes a group is blocked
locally instead of passing locally and failing in CI. `wfctl review start`
and `wfctl review check` accept that list plus any group in the working
tree's `wfctl.json` (FR-010a). They take a group's skill and reviewers from
the working tree when it lists the group, and from the trunk's file
otherwise, which is how a removed group still runs. A group that's only in
the working tree can run, but nothing requires it until it's committed, so a
user can try a new group before it's enforced.

The list function takes the two parsed configs as arguments and reads no
files, the same split `unreviewed` uses (FR-009). Each caller reads the files
with `git show`, so the guard path still imports neither `typer` nor `rich`.
Both live in `_review_config.py`: `load` gains a sibling that parses a
file's text, and the list function sits beside it. Each file is validated on
its own, and the join is by group name only. So a trunk group `money-rules`
and a head group `mutation` aren't reported as a first-letter clash, since
neither file has one. The clash only matters to `relay`, which refuses an
ambiguous letter (FR-010a).

The local commands read the trunk's file at the last fetched
`origin/<trunk>`. When `main` adds a group after the last fetch, the guard
reads the older list and lets the PR open, and CI then requires the new
group. Both sides agree for the same trunk ref, and a fetch brings the local
side level.

A problem in the trunk's `review` key fails every PR, including the PR that
fixes it, and the guard refuses `gh pr create` on every branch too. We keep
it a failure rather than falling back to the default groups, since a silent
fallback would drop a custom group's requirement without anyone noticing.
`AGENTS.md` gives the recovery beside the ruleset steps: the maintainer opens
the fixing PR from their own terminal, removes `review` from the ruleset's
required checks, merges, and applies the ruleset again.

**Alternatives considered**: the head's list alone, as the spec first had it.
We didn't choose it because a PR could drop a group and skip its review. The
trunk's list alone, rejected because a group a PR adds would go unchecked on
that PR. A `--groups-from <path>` flag pointing at `trusted/wfctl.json`,
rejected because the trunk's file is already in git and a flag would make the
local and CI runs differ. For the local commands, keeping the working tree's
list, with a sign-off as the way past a removed group. We didn't choose it
because the guard would let a PR open that CI then fails, and the sign-off
would see nothing unreviewed and write no note.

## R14. CI measures against the PR's base branch

**Decision**: `wfctl check reviews` gains `--base <branch>` (FR-015a). The job
passes the PR's base branch from the event, through an environment variable
rather than an inline `${{ }}` expression, so a branch name can't inject shell
text. With `--base`, `trunk_refs` takes `origin/<branch>` as the trunk, skips
`_paths.trunk_branch`, and still refuses a trunk that is the branch under
review. It skips the single-branch clone refusal, as a declared trunk does,
since that refusal guards against `origin/HEAD` naming the wrong branch and
`--base` doesn't use `origin/HEAD`. The trunk's `wfctl.json` for R13 is read
from the same ref. R10's `trunk` keyword carries the branch down. Without
`--base`, nothing changes, so the guard and a local run still use the `trunk`
key or `origin/HEAD`.

The job also runs on the `edited` event type, beside the default `opened`,
`synchronize`, and `reopened`. GitHub sends `edited` when a PR's base branch
changes, which is how a stacked PR gets checked against `main` after its
parent merges. `edited` also fires on a title or description edit, which
reruns the check harmlessly.

**Assumed, checked after merge**: GitHub sends `edited` when it retargets a
PR itself after the parent branch is deleted. Quickstart step 5 checks it.

The job has a `concurrency` group keyed by PR number, with
`cancel-in-progress: true`. Without it, a run against the old base and a run
started by the retarget can both be in flight for the same head commit, and
whichever finishes last sets the result. Cancelling the older run leaves the
newer one's result.

**Rationale**: the maintainer chose this after the second plan review
(PR-013). `_paths.trunk_branch` takes the `trunk` key from the working tree's
`wfctl.json` before `origin/HEAD`, and in the job that file is the PR's. A PR
that set `trunk` to a branch already holding its head got an empty range and
passed with no review, and R13 would have read the groups from that branch
too. The event's base branch comes from GitHub, so the PR's files can't
change it. A PR can still target an unusual branch, but the `main` ruleset
only requires the check on PRs into `main`, so that gets nothing past it.

R13 rejected a flag because a config path passed in CI would make local and
CI runs read different files. `--base` names a branch instead. A local run
without it reads the same trunk the guard reads, which is the branch the user
will open the PR against in the usual case.

**Alternatives considered**: ignoring the `trunk` key in CI and using GitHub's
default branch. We didn't choose it because a repository that merges into
`develop` would be measured against the wrong branch, and a stacked PR would
need reviews for its parent's commits. Reading `trunk` from the `trusted/`
checkout's `wfctl.json`. We didn't choose it because it's still wrong for a
stacked PR, and the base branch is already known.
