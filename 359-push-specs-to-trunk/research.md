# Research: storing a branch's spec dir on its spec store's remote

Each entry is one decision the plan rests on. The spec and the three level-3
records settled what the feature does. These settle how, against the code as it
stands on `main` at `f433146`.

## R1. One new module holds the spec store's git work

**Decision**: A new module, `wfctl/_spec_store.py`, holds everything that asks
git about the spec store or writes to it: which layout the spec root is in,
which spec dirs are not stored, and the store itself. `cli.py` gets two thin
commands and a changed `archive-specs`, and `_evidence.py` gets one reader that
calls into the module.

**Rationale**: Three callers ask the same question (the pass, `check specs`,
and removal), and the store writes what the question reads. Keeping both halves
in one file means the definition of "stored" that the store aims for and the one
the readers check cannot drift apart. `_archive.py` is the nearest neighbour,
but it copies files out of a worktree and never touches git, and #40 is
reshaping it on a parallel branch.

**Alternatives considered**: Putting the reads in `_paths.py`, which already
asks git about worktrees. We didn't choose this because `_paths.py` resolves
where things are, and this is a question about their state. Putting everything
in `_archive.py`. We didn't choose this because it would put this branch's work
and #40's in one file at the same time, which is the conflict both branches
agreed to avoid.

## R2. The layout check shares the guard's rule for "a branch of the store's own"

**Decision**: The store commits only when the spec root passes the same test the
worktree guard already applies before it lets an agent commit there:
`_hook.committable`. That function asks git whether the root belongs to another
repository than the code, or has a branch checked out that no other worktree of
this project has. The per-root half of it moves into `_spec_store.owns_branch(root,
here)`, and `_hook.committable` calls it. The store adds one condition the guard
checks only for folders: `git rev-parse --show-toplevel` run in the root must
name the root itself (FR-010).

The layouts come out as four kinds:

1. `store`: passes both checks, and its checked-out branch has an upstream.
2. `store_no_upstream`: passes both checks, and `git rev-parse @{u}` fails.
3. `in_repo`: git, run in the spec root, finds the code repository's own
   checkout. The default `specs/` is this kind.
4. `unmanaged`: anything else. That covers a plain folder, where git finds no
   repository, and a folder nested inside some other repository, where a commit
   would land on that repository's branch.

**Rationale**: The guard's docstring already lists the ways a spec root can look
like a store and not be one, such as a store whose `.git` was replaced to point
at the main checkout. If the store used a second, simpler test, the guard would
refuse a hand commit in a folder where the store happily commits, or the other
way round. One rule means one answer.

**Alternatives considered**: Testing only `--show-toplevel == root`. We didn't
choose this because a worktree of the code repository with the code's own branch
checked out passes it, and a commit there lands on a feature branch.

## R3. "Stored" is read with two git calls, scoped by pathspec

**Decision**: A spec dir is stored when both of these print nothing:

```
git status --porcelain -z --untracked-files=all -- <spec dir>
git log --format= --name-only @{u}..HEAD -- <spec dir>
```

The first counts uncommitted files, untracked ones included. The second names
files in commits the upstream doesn't have yet. Neither touches the network,
because `@{u}` is git's local copy of the remote branch, which a push updates
(FR-016).

`check specs` runs the same two commands once over the whole store root and
groups the output by each path's first component, so 100 spec dirs cost two git
calls rather than 200.

**Rationale**: Both commands were checked in the brainstorm (`design.md`, Key
Assumptions). `--untracked-files=all` is what makes a brand-new spec dir count
as many files rather than one directory line.

**Alternatives considered**: `git rev-list --count @{u}..HEAD -- <dir>`. It
answers yes or no, but `check specs` and the store's own output both want file
names, so `log --name-only` answers both questions at once.

## R4. The pass reports through `display`, never `reason`

**Decision**: The `store-specs` reader returns `Assessment("in_progress", None,
"<text>")` when the spec dir is not stored, and `Assessment("skipped", None,
"<text>")` for a layout with nowhere to push. The text goes in `display`, and
`reason` stays empty in every case.

**Rationale**: The roll-up in `_pipeline.py` copies an outstanding pass's
`reason` onto its step, and a step with a reason is routed as blocked. For
`implement` with no open tasks, a blocked step routes to `wfctl verify`
(`next_step_content`). So a reason on this pass would send the run to verify
instead of `/store-specs`. `plan_review` avoids the same trap the same way, and
its docstring says why. A `skipped` reading with a reason would also be listed as
a warning on every `status` (`check-rework-loop`), which is wrong for a layout
the repository chose on purpose.

## R5. Two stores at once are serialised with an OS file lock

**Decision**: The store takes `fcntl.flock` on a file named `wfctl-store.lock`
inside the spec store's git directory, as `git rev-parse --git-dir` run in the
spec root names it. It tries without blocking every 0.2 seconds for up to 10
seconds (FR-027), then exits 1 with `another store is running in <root>`. The
lock covers the whole run, from the first `git add` to the end of the push.

**Rationale**: The lock has to cover the whole sequence, not only the index
writes, so a second store cannot commit in between the first one's merge and
its push. An OS lock is released when the process exits, even after a crash or a
killed hook, so a dead store never leaves a lock behind that a person has to
delete. A lock file created with `O_EXCL` would need exactly that cleanup.

The git directory, and not the spec root, keeps the lock file out of the working
tree, so it never shows up as an untracked file in the store. In pfms the spec
store is a worktree, and `--git-dir` names that worktree's own directory, which
is where its own index lives. That makes the lock exactly as wide as the thing
two stores would fight over.

**Alternatives considered**: Retrying when git reports `index.lock` exists. We
didn't choose this because it only covers the moments git holds its own lock,
and two stores can still interleave between them. `fcntl` is POSIX only, which
matches where wfctl runs today: CI runs on Ubuntu, and both repositories using
wfctl are on macOS.

## R6. Exit codes: 0 only when the spec dir is safe or there was nothing to do

This answers the question clarify deferred to the plan.

**Decision**: `wfctl store specs` exits 0 when the spec dir is stored, was
already stored, or the layout has nowhere to push and the output says where the
files are. It exits 1 in every other case: committed but not pushed, a merge
conflict, a merge refused because of local edits, a push refused, the lock
timing out, or any git failure.

`archive-specs` runs the store inside its own handling and turns every store
failure into a warning when the spec dir lives outside the worktree (FR-021).
The commit, or the uncommitted files, are still in the spec store on disk, and
removing the worktree can't delete them.

The exit code is therefore not what removal reads. Removal calls the store as a
function and reads `StoreResult.stops_removal`. The property is true for any
result where the spec dir is inside the worktree and was not copied out, since
there deleting the worktree deletes the only copy. #40's copy-out refusals in
the default layout, such as a destination that already holds different files,
are one case. `not_applicable` for a spec dir inside the worktree is the other.
Every outcome this branch adds for a spec dir outside the worktree has
`stops_removal` false, so removal prints the store's output as a warning and
goes ahead. The data model's store result table says the same.

On this branch, `not_applicable` for a spec dir inside the worktree never reaches
removal, because `archive-specs` runs the store only where the spec dir is
outside the worktree (R11). Once both branches are merged, `store specs` runs
#40's copy-out in the default layout before it would return `not_applicable`, so
removal reads the copy-out's outcome there. Whichever branch merges second
checks that order.

The condition on `not_applicable` is there in case that check is missed. If a
merged `store` returned `not_applicable` before the copy-out ran, an outcome-only
rule would let removal delete the only copy with no error. With the condition,
the removal stops instead. #40's record at `2e9f124` makes the same rule and
tests it.

The two records agree on `stops_removal`, and the exit code by hand is a
separate question. `not_applicable` exits 0 when `store specs` is run by hand,
inside the worktree or not. In that layout the store has nothing it can do, so
it says where the files are and stops, and the pass reads `skipped` for the same
reason (FR-011, User Story 5). That is the reasoning `committed_not_backed_up`
already uses. An exit of 1 there would make `store specs` fail on every run in
every repository on the default layout, with no command that could ever make it
pass. #40's record at `b3fc797` agrees on `not_applicable`: `store specs` run
by hand exits 1 for a copy-out refusal and for a spec store failure, and exits 0
for `not_applicable`.

#40's record names no exit code for `committed_not_backed_up`, so this plan's
data model decides it, and it exits 0. The store committed the files and has no
remote to push them to. Setting an upstream would let the next run push, but
choosing a remote is the person's decision rather than the store's, so the store
reports "not backed up" and stops. If #40 later names an exit code for this
outcome, it has to match this one.

The rule lives on `StoreResult` rather than in the removal command, because two
branches write removal commands. Today that is `archive-specs`, and after #40 it
is `wfctl hook worktree-remove`, with `archive-specs` as its alias. Both read the
same property, so they can't disagree about when removal stops. #40's record
says the hook "exits non-zero when either one refuses". For the store, a refusal
means `stops_removal` is true, not that `store specs` exited 1. A failed push
exits 1 from `store specs` run by hand, and only warns at removal.

**Rationale**: The pass reads `in_progress` in all of the exit-1 cases, so an
exit code of 0 there would tell a script the store worked when the pipeline
says it didn't. Exit 1 also lets `speckit-orchestrate`'s stall count stop an
unattended run that keeps failing to push, rather than reporting success each
time.

**Alternatives considered**: Exit 0 for "committed, not pushed", since nothing
is lost. We didn't choose this because "nothing is lost" is removal's question,
and removal already handles it by warning. The store's own question is whether
the spec dir is backed up, and it isn't.

## R7. The store never waits on a person or a dead network

**Decision**: Every git call the store makes runs with `GIT_TERMINAL_PROMPT=0`,
and `fetch` and `push` run with a 60-second timeout. A timeout is reported the
same way as an unreachable remote, "committed, not pushed".

**Rationale**: The store runs from a `pre_remove` hook and from an unattended
pass, and in both nobody is at the terminal. Without the variable, a missing
credential makes git prompt for a password and the hook hangs with no output.

## R8. A merge that can't finish is backed out and reported by kind

**Decision**: The store fetches only the upstream branch (`git fetch <remote>
<branch>`, read from `branch.<name>.remote` and `branch.<name>.merge`) and runs
`git merge --no-edit @{u}`. Three failures are told apart, in this order:

1. A conflict. After a failed merge, the store first checks whether
   `.git/MERGE_HEAD` exists (`git rev-parse -q --verify MERGE_HEAD`). If it
   does, the merge started and stopped on a conflict. The store first reads the
   conflicted paths with `git diff --name-only --diff-filter=U`, then runs
   `git merge --abort`, keeps its own commit, names the folders those paths sit
   in, and exits 1 (FR-007). The read has to come before the abort, because
   after it that command prints nothing (reproduced with git 2.44.0).
2. A merge git refused to start because the spec store's index holds staged
   files. With no `MERGE_HEAD`, the store reads `git diff --cached --name-only`,
   and when it prints anything, this is the kind. It names the folders those
   files sit in, says to store the branch that owns each folder or unstage the
   files, and exits 1. Nothing was started, so there is nothing to abort.
3. A merge git refused to start, with nothing staged, because a file the
   upstream changed has unstaged local edits. The store names the files from
   git's message and exits 1.

The `MERGE_HEAD` check comes first because `git diff --cached` isn't empty after
a conflict either. A started merge stages what it merged and lists the unmerged
paths, so checking the index first would read a conflict as staged files, skip
`git merge --abort`, and leave the spec store mid-merge. That stops every
branch's store until a person aborts it. This was reproduced with git 2.44.0: a
conflict exits 1 and leaves `MERGE_HEAD`, and a merge refused for a staged path
exits 2 and leaves none.

**Rationale**: Git refuses a merge that isn't a fast-forward whenever the index
differs from `HEAD`, whether or not the upstream touches the staged files. This
was reproduced with git 2.44.0: with `200/o` staged and the remote one commit
ahead in another folder, `git merge --no-edit @{u}` exits 2 and names `200/o`,
and the same edit left unstaged merges cleanly. The store's own commit always
makes the merge a non-fast-forward once the remote has moved, so one staged file
anywhere in the spec store blocks every branch's store until it is committed or
unstaged.

That is not rare. FR-001 leaves other staged files in place on purpose, and a
store killed between its `git add` and its `git commit` leaves its own folder
staged. So the output has to name the cause and the remedy. "Local edits" would
send a person looking for unstaged changes that aren't there, and "conflict"
would not be true either.

Storing the owning branch is the remedy the output names first, because its
`git commit -- <dir>` takes that folder's staged files into a commit and leaves
the index clean. Unstaging is the remedy for a file no branch owns.

The third kind needs the same folder edited on two machines, and that folder
also edited locally, which the spec's assumption that each branch writes only
its own folder makes rare. It still has to say something true.

The level-3 record assumes `git merge --abort` leaves other branches' local
edits alone, and says a test must confirm it before the store relies on it. That
test is the first one written (see the plan's implementation order).

## R9. The commit names its files, and the output counts them

**Decision**: Before committing, the store takes the list of files that differ
between `@{u}` and the working tree under the spec dir. The commit subject is
`specs(<issue>): store <first file> and N others`, or `store <file>` for one.
The issue key comes from `extract_issue_key` on the branch, so it matches the
existing `specs(<issue>):` commits on `specs-trunk` (FR-002). The success line
counts every file in that list, which includes files from an earlier commit of
this branch's that was never pushed, since the push carries them too.

**Rationale**: "Stored 4 files" should mean the four files that just reached
the remote. Counting only the new commit would undercount when an earlier store
committed and couldn't push.

## R10. "In progress" means a worktree of this repository resolves to the spec dir

**Decision**: `check specs` builds its "In progress" set by running
`resolve_spec_dir` on every branch `worktree_branches` returns. A spec dir in
that set goes under the "In progress" heading. Everything else unstored goes
under "not stored".

**Rationale**: `resolve_spec_dir` is the one place that decides which spec dir a
branch owns, including the key glob and an epic's grouping map. Matching folder
names against branch names directly would disagree with it whenever a branch's
slug differs from its spec dir's. `worktree_branches` already drops `prunable`
entries, so a worktree deleted by hand doesn't keep a spec dir marked as in
progress forever.

Only this machine's worktrees are seen. The spec records that as an accepted
edge case.

## R11. Removal's in-worktree path stays as it is on this branch

**Decision**: On this branch, `archive-specs` changes only where the spec dir is
outside the worktree. There it runs the store and prints what the store printed,
instead of the "durable" line. Where the spec dir is inside the worktree, it
keeps today's copy into the state directory, and #40 replaces that with its
copy-out to the main checkout.

**Rationale**: FR-011 gives the in-worktree copy-out to #40, and whichever branch
merges second merges `main` in. Leaving that path untouched here keeps the
second merge to one function.

#40 is also moving the removal hook to `wfctl hook worktree-remove`, which runs
`wfctl store specs` and then `wfctl archive unsaved`, with `archive-specs` as
its hidden alias. New repositories are seeded with the one
`wfctl hook worktree-remove` line, and existing hooks keep calling
`archive-specs` without an edit. So the store's removal behaviour lives in
`store specs`, whichever branch merges first:

1. If #40 merges first, `wfctl hook worktree-remove` already calls
   `store specs`, and this branch drops its `archive_specs_cmd` change when it
   merges `main` in. It still checks that the hook reads `stops_removal` rather
   than the exit code (R6), and it moves the removal tests onto the hook
   instead of dropping them, so a failed push at removal is still tested to
   warn and go ahead.
2. If this branch merges first, `archive-specs` runs the store as described
   above, and #40 folds that call into `wfctl hook worktree-remove` when it
   merges `main` in.

`store specs` itself, run in the `in_repo` layout, commits nothing and says the
spec dir is inside the code repository and not backed up. It exits 0.

## R12. The end-of-session instruction names the store instead of forbidding it

**Decision**: `wfctl/agents/skills/end-session/SKILL.md` step 7 keeps its count
of uncommitted files. Its "Report only" paragraph changes so that in a spec
store with an upstream branch, the report line names `wfctl store specs` as the
way to store them, and still says not to `git add` or `git commit` there by hand
(FR-026). The other layouts keep "report only".

**Rationale**: The session summary is not a pipeline step, so the session
doesn't run the store itself. But a person reading the line needs to know there
is now one command for it, and a hand commit would bypass the one-folder rule
in FR-001.

## R13. The payload snapshot moves, and the contract does not

**Decision**: `tests/pipeline_payload_snapshot.json` is regenerated, because
every case in it now carries a `store-specs` entry under `implement`. The status
payload contract (`wfctl/contracts/status-payload.json`) records key shapes, not
which passes exist, so its version stays 1.3.

**Rationale**: The snapshot test's docstring says a deliberate verdict change
regenerates the file and says why in the commit message. Every snapshot case
builds its spec dir in a temporary folder with no store, so the new entry reads
`pending` or `skipped` there, and no other verdict moves. The diff should show
only the new entries, which is the check that nothing else changed.

## R14. The pass reads git only once `implement` is done

**Decision**: No extra work is needed for SC-006. `_pass_states` evaluates a
step's passes only when the step's own reading is `done`, so on every branch
short of a finished `implement`, `wfctl status` never calls this reader.

**Rationale**: The level-3 record assumed reading git on every status was cheap
enough. It turns out most status calls never read it at all, and the ones that do
run two git commands scoped to one folder. The quickstart still times it against
this repository's store, because that is what SC-006 asks for.

## R15. A store that pushes records its action, and a host block routes to the pass

**Decision**: When `wfctl store specs` ends with `stored`, it records a
`store-specs` action with `_session.record_outward_action`, the same event
`wfctl report-action store-specs` writes. While a host block filed for the
`store-specs` action holds `implement` and the `store-specs` pass reads
`in_progress`, `next_command` is `/store-specs` with `auto: false`, not
`wfctl verify`.

The rule keys on the block's action matching the outstanding pass's name, not
on any outstanding pass. A block filed for another action, such as `push` or
`issue-close` on a finished `implement`, routes exactly as it does today, to
`wfctl verify` or `/speckit.implement`, whatever pass is outstanding under it.
So does a pass a repository declares under `implement`, unless a block was
filed for that pass's own name. Where one was and the pass is manual, routing
returns the qualified pass name with `auto: false`, the same answer a manual
pass gets today.

`next_step_content` gains a `block_action` argument, which each caller reads off
the `StandingBlock` that `_apply_block_hold` already returns in `by_step`. There
are two callers, and both pass it: `build_report` in `_pipeline.py`, which
answers `status` and `resume`, and `next_cmd` in `cli.py`, which writes
`next-step.md`. `next_cmd` already receives `by_step` and discards it as
`_by_step`. If only one caller passed it, `status` would name `/store-specs`
while `next-step.md`, the file an agent acts on, would still say
`wfctl verify`. `resume` writes `next-step.md` too, but from `build_report`'s
answer, so only the copy `wfctl next` writes shows whether `next_cmd` passed it.

`next_step_content`'s docstring says an outstanding pass is "Checked after
`blocked`", because a host
block "means the same thing regardless of what a pass underneath happens to
read". That stays true for every block except one filed for the outstanding
pass's own action, and the docstring changes to name that one exception and
the reason for it below.

**Rationale**: When the host refuses the push, the wrapper files
`wfctl report-block store-specs`, which holds `implement`. That hold lifts only
when a `store-specs` action is recorded. Previously, only `report-action`
recorded one, because no wfctl verb performed a push. Now `wfctl store specs`
performs it, so it records its own success the way `wfctl issue` records its
writes. As a result, a person who runs `wfctl store specs` in their own shell
lifts the hold without a second command.

Only `stored` records the action, because it is the only outcome that pushed.
`already_stored` pushed nothing, and the event says an action was taken. A push
made with plain git still needs `wfctl report-action store-specs`, which is
today's rule for any push wfctl did not make.

The same holds for a commit that another branch's store pushes. When a run
here ends `not_pushed` under a block, its commit waits in the spec store, and
the next store from any branch pushes it along with its own commit. A later
`wfctl store specs` here then ends `already_stored`, which records nothing, so
the hold stays until someone runs `wfctl report-action store-specs`.

The routing change is needed because a blocked `implement` with no open tasks
routes to `wfctl verify` today. That is right when verification is what's
missing, and wrong here: a pass reads `in_progress` only once `implement`'s own
reading is `done`, so verification has already passed and the store is what's
missing. Sending the reader to `wfctl verify` would show a green verdict and
leave the hold in place. The block's remedy line already says to take the action
yourself and then record it, which still holds. Running `/store-specs` again from
the agent will be refused again, and the remedy line says that too.

**Alternatives considered**: Recording the action for `already_stored` as
well. We didn't choose this because it would write a push into the log that
never happened, and the log is the only record a restarted session reads.
