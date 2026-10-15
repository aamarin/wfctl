# Feature Specification: wfctl stores a branch's spec dir on its spec store's remote

**Feature Branch**: `359-push-specs-to-trunk`
**Created**: 2026-10-14
**Status**: Draft
**Input**: User description: "From the brainstorm output at design.md (issue #359: nothing pushes a spec dir to specs-trunk, and wm remove calls it durable either way)"

## Clarifications

### Session 2026-10-14

- Q: How does `wfctl check specs` treat a spec dir whose branch still has a
  worktree? Every branch in the pipeline has an unstored spec dir, because the
  store runs only after `implement`. → A: It lists those dirs under a separate
  "In progress" heading that doesn't count toward exit 1. Exit 1 then means a
  spec dir was left behind, and the active ones stay visible.
- Q: What does a store do when another store is already running against the
  same spec store? → A: It waits up to 10 seconds for the other store to
  finish, then fails with a message saying another store is running. A store
  takes a second or two, so the wait clears almost every collision.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - An unattended run stores its own spec dir before it opens a pull request (Priority: P1)

A spec dir holds everything the pipeline wrote for one branch: the design, the
spec, the plan, the tasks, and the review reports. In this repository and in
pfms, it lives in a spec store, which is a git checkout of its own outside the
working tree. A spec dir only reaches the remote when someone commits and
pushes it inside the spec store. Today nobody is told to, and most branches
never did.

After this change, once `implement` is done, `wfctl status` names
`/store-specs` as the next command until the spec dir is stored. The command
runs `wfctl store specs`, which commits this branch's folder, picks up any
changes on the remote, and pushes. An unattended run that follows the next
command stores its specs with nobody typing a git command.

For example, after `implement` finishes with an uncommitted `tasks.md`:

```
implement    ●
  store-specs   ▶  ← current
next: /store-specs
```

And after the store:

```
✓ stored 4 files → origin/specs-trunk (8c1d0e2)
    reviews/panel-1.md, reviews/panel-2.md, tasks.md, plan.md
```

**Why this priority**: This is the bug. Two sweeps found close to 60 spec dirs
each that had never been committed, and an unattended run has nobody to notice.

**Independent Test**: In a repository whose spec store has an upstream branch,
finish `implement` with an uncommitted file in the spec dir. `wfctl status
--json` names `/store-specs`. Run `wfctl store specs`, and the commit is on the
upstream branch and the pass reads done.

**Acceptance Scenarios**:

1. **Given** `implement` is done and the spec dir has an uncommitted file,
   **When** `wfctl status --json` is read, **Then** the next command is
   `/store-specs` and the pass reads `in_progress`.
2. **Given** the same state, **When** `wfctl store specs` runs, **Then** a
   commit containing only this branch's folder is on the upstream branch, and
   the output names each file it stored.
3. **Given** every file in the spec dir is committed and pushed, **When**
   `wfctl status --json` is read, **Then** the pass reads `done` and wfctl made
   no network call to decide it.
4. **Given** every file is committed but the commit is not on the upstream
   branch, **When** `wfctl status --json` is read, **Then** the pass reads
   `in_progress`.
5. **Given** the agent's host refuses the push, **When** `/store-specs` runs,
   **Then** it runs `wfctl report-block store-specs --reason "…"` and does not
   try another way to push.

---

### User Story 2 - Removing a worktree stores what is left and never calls an unstored spec dir safe (Priority: P1)

The review panel writes its reports after the pipeline's last store, so a
branch usually has a few files left unstored when its worktree is removed.
Today removal prints `✓ spec dir is durable — nothing there was at risk` for
any spec dir outside the worktree, whether it was ever committed or not.

After this change, removal runs `wfctl store specs` through the
`archive-specs` command every removal hook already calls. No repository edits
its hook. Removal never prints "durable". It says what it stored, or why it
couldn't push.

When the push fails, removal prints a warning and goes ahead, because the
commit is already in the spec store on disk and removing the worktree can't
delete it. For example, with GitHub unreachable:

```
⚠ committed 2 files, not pushed — origin/specs-trunk is unreachable
    reviews/panel-1.md, reviews/panel-2.md
    the next `wfctl store specs` from any branch pushes it
```

**Why this priority**: The "durable" message is what stopped anyone looking.
Removal is also the last moment a branch's files are written, so it is the
only place that catches them.

**Independent Test**: In this repository, write a file to the spec dir after
the last store, then remove the worktree with `wm remove`. The file is on
`origin/specs-trunk` afterwards, and neither repository's `.workmux.yaml`
changed.

**Acceptance Scenarios**:

1. **Given** a spec dir with a file written after the last store, **When** the
   worktree is removed, **Then** the file is committed and pushed and removal
   names it.
2. **Given** a spec dir that is fully stored, **When** the worktree is removed,
   **Then** removal says it is stored and pushes nothing.
3. **Given** GitHub is unreachable, **When** the worktree is removed, **Then**
   the store commits locally, prints a warning saying it is not pushed, and the
   worktree is removed.
4. **Given** any layout, **When** the worktree is removed, **Then** the output
   does not contain the word "durable".

---

### User Story 3 - A person can list every spec dir that isn't stored (Priority: P2)

A finding is only useful if someone can ask for it. Today the only way to find
an unstored spec dir is to run `git status` inside the spec store and read it.

After this change, `wfctl check specs` lists every spec dir in the spec store
that has uncommitted files or unpushed commits. It reads git's local copy of
the remote, so it never touches the network.

Every branch still in the pipeline has an unstored spec dir, because the store
runs only after `implement`. So the list has two sections. A spec dir whose
branch still has a worktree goes under "In progress", and those never change
the exit code. Every other unstored spec dir goes under "Not stored", and any
one of them makes the command exit 1. As a result, exit 1 means something was
left behind, and you still see the work in flight.

For example, with two dirs left behind and two branches in progress:

```
✗ 2 spec dirs not stored
    188-check-rework-loop      uncommitted: 12 files
    552-bob-command-rename     committed, not pushed

In progress (2 spec dirs, still have a worktree):
    359-push-specs-to-trunk    uncommitted: 4 files
    470-capability-modeling    uncommitted: 2 files
```

With only the in-progress dirs unstored, it exits 0:

```
✓ every spec dir without a worktree is stored

In progress (2 spec dirs, still have a worktree):
    359-push-specs-to-trunk    uncommitted: 4 files
    470-capability-modeling    uncommitted: 2 files
```

**Why this priority**: It is how the gap stays visible after this ships. It is
P2 because the store in stories 1 and 2 closes the gap for new branches, and
this reports the ones it missed.

**Independent Test**: Leave one spec dir with an uncommitted file and another
with an unpushed commit, neither with a worktree. `wfctl check specs` lists
both under "not stored" with the right reason and exits 1. Store both, leave a
third dir unstored whose branch has a worktree, and it lists that dir under
"In progress" and exits 0.

**Acceptance Scenarios**:

1. **Given** a spec dir with an uncommitted file and no worktree, **When**
   `wfctl check specs` runs, **Then** it lists that dir under "not stored" with
   the count of uncommitted files and exits 1.
2. **Given** a spec dir with a commit not on the upstream branch, **When**
   `wfctl check specs` runs, **Then** it lists that dir as committed, not
   pushed.
3. **Given** every spec dir is stored, **When** `wfctl check specs` runs,
   **Then** it says so and exits 0.
4. **Given** an unstored spec dir whose branch has a worktree, and no other
   unstored spec dir, **When** `wfctl check specs` runs, **Then** it lists
   that dir under "In progress" with its reason and exits 0.
5. **Given** the spec root is not a spec store with an upstream branch,
   **When** `wfctl check specs` runs, **Then** it says where the spec root is
   and that nothing there can be pushed, and exits 0.

---

### User Story 4 - The store picks up changes on the remote without touching other branches' files (Priority: P2)

Every branch stores to the same branch of the spec store, from more than one
machine. So the remote has often moved on when a store pushes, and a plain
push would be refused. The spec store's checkout is also shared, so while one
branch stores, other branches have new or edited files sitting in it.

After this change, the store fetches, merges the remote, and pushes. A rebase
would refuse whenever another branch has an edited file, and a force push could
delete another branch's specs, so the store never does either.

**Why this priority**: Without it, stories 1 and 2 fail on most runs once more
than one machine stores. It is P2 because a single machine never sees it.

**Independent Test**: With the remote one commit ahead, another branch's
tracked file edited, and another branch's folder untracked, run
`wfctl store specs`. The push succeeds, and the edited and untracked files are
exactly as they were.

**Acceptance Scenarios**:

1. **Given** the remote has a commit the local branch lacks, **When** the store
   runs, **Then** it merges that commit and pushes.
2. **Given** another branch has an edited tracked file and an untracked folder
   in the spec store, **When** the store runs, **Then** both are unchanged and
   neither is in the commit.
3. **Given** the merge conflicts in this branch's own folder, **When** the
   store runs, **Then** it aborts the merge, keeps its own commit, names the
   folder in conflict, and exits non-zero.

---

### User Story 5 - Layouts with nowhere to push say where the files are (Priority: P3)

Not every repository keeps its spec dirs in a spec store with a remote. The
default layout keeps `specs/` inside the code repository, and some
repositories point the spec root at a plain folder.

After this change, wfctl never commits in those layouts. It says plainly where
the files are and that nothing backs them up, and the pass after `implement`
reads `skipped` with that reason, so the pipeline finishes.

| Layout | What wfctl says |
|---|---|
| Spec store with no upstream branch | committed, not backed up |
| `specs/` inside the code repository | copied to the main checkout at removal, not backed up |
| Plain folder outside any repository | not backed up anywhere, with the path |

**Why this priority**: Neither repository that uses wfctl today is in these
layouts. It matters so that no repository reads a green tick over a folder
nothing backs up.

**Independent Test**: With the spec root set to a plain folder, finish
`implement`. The pass reads `skipped` with a reason naming the folder, and the
pipeline reads finished.

**Acceptance Scenarios**:

1. **Given** a spec root inside the code repository, **When** the store runs,
   **Then** nothing is committed on the feature branch.
2. **Given** a spec store with no upstream branch, **When** the store runs,
   **Then** it commits and says the commit is not backed up.
3. **Given** a plain folder, **When** the pass after `implement` is read,
   **Then** it reads `skipped` with a reason naming the folder.

---

### Edge Cases

- **Another branch committed but never pushed.** A push sends every local
  commit on the spec store's branch, so its commit goes up too. Every commit on
  that branch belongs on the remote, so this is accepted.
- **Someone deletes or force-pushes the remote branch.** wfctl's local copy of
  the remote still shows the spec dir as pushed until the next fetch. Accepted
  while one person writes to the branch.
- **A file in the spec dir is deleted.** The store commits the deletion, since
  the folder on the remote should match the folder on disk.
- **The branch has a worktree on another machine only.** `check specs` sees
  only this machine's worktrees, so it lists that spec dir as not stored and
  exits 1. Accepted while one person works across machines, since the other
  machine's next store clears it.
- **Two stores run at once.** Every branch commits into the same spec store,
  so two removals or two unattended runs that finish together would collide.
  The second store waits for the first, and fails after 10 seconds. At
  removal that failure is a warning, the same as a failed push, because the
  files stay in the spec store outside the worktree and removal cannot delete
  them.
- **The spec dir does not exist yet.** The store does nothing and says there is
  no spec dir for the branch. `check specs` doesn't list it.
- **The merge succeeds and the push is refused because the remote moved again.**
  The store reports it and keeps the merge commit for the next run.
- **The store runs on `main` or another branch with no issue.** There is no
  spec dir for it, so the store says so and does nothing.
- **A hook runs a bare `wfctl` older than this change.** Its `archive-specs`
  prints the old message. Nothing breaks, and `check specs` from a current
  wfctl still lists the spec dir.

## Requirements _(mandatory)_

### Functional Requirements

**Storing**

- **FR-001**: `wfctl store specs` MUST commit only the current branch's folder
  in the spec store, leaving any other path already staged in the spec store's
  index staged and uncommitted.
- **FR-002**: The commit subject MUST start with `specs(<issue>):`, matching the
  existing commits on the spec store's branch, followed by the files it stored,
  such as `specs(359): store tasks.md and 3 others`. Existing commits carry
  hand-written summaries, and a generated one can only say what changed.
- **FR-003**: After committing, the store MUST fetch the upstream branch, merge
  it with no editor, and push the spec store's checked-out branch to its
  upstream.
- **FR-004**: The store MUST NOT rebase, stash, or force-push.
- **FR-005**: The store MUST NOT name `specs-trunk`. It pushes whatever branch
  the spec store has checked out.
- **FR-006**: When the fetch or the push fails because the remote is
  unreachable, the store MUST keep its commit and report "committed, not
  pushed".
- **FR-007**: When the merge conflicts, the store MUST abort the merge, keep its
  own commit, name the folders in conflict, and exit non-zero.
- **FR-008**: On success the store MUST print the count of files stored, the
  upstream branch, and the short commit id on one line, and the file names on
  the next. It says "files", never "specs".
- **FR-009**: When nothing in the spec dir is uncommitted or unpushed, the store
  MUST say the spec dir is already stored and create no commit.
- **FR-027**: Only one store MUST run against a spec store at a time. When
  another store is running, the store MUST wait up to 10 seconds for it to
  finish, then exit non-zero with a message saying another store is running.

**Layouts**

- **FR-010**: The store MUST commit and push only when the spec root is the top
  of its own git repository and that repository's checked-out branch has an
  upstream.
- **FR-011**: When the spec root is inside the code repository, the store MUST
  NOT commit anything. The copy-out at removal belongs to the #40 branch.
- **FR-012**: When the spec store has no upstream branch, the store MUST commit
  and report "committed, not backed up".
- **FR-013**: When the spec root is a plain folder outside any repository, the
  store MUST commit nothing and report "not backed up anywhere" with the path.

**Reading whether a spec dir is stored**

- **FR-014**: wfctl MUST decide whether a spec dir is stored by asking git each
  time, and MUST NOT record the answer.
- **FR-015**: A spec dir is stored when it has no uncommitted or untracked files
  and no commit touching it is missing from the local remote-tracking branch.
- **FR-016**: Reading whether a spec dir is stored MUST NOT touch the network.

**The pipeline pass**

- **FR-017**: `implement` MUST carry a built-in pass named `store-specs`, with
  `/store-specs` as its command and no review required.
- **FR-018**: The pass MUST read `done` when the spec dir is stored,
  `in_progress` when it is not, and `skipped` with a reason naming the layout
  when the layout has nowhere to push.
- **FR-019**: wfctl MUST ship a `/store-specs` command wrapper that runs
  `wfctl store specs` and, when the host refuses the push, runs
  `wfctl report-block store-specs --reason "…"`.

**Removal**

- **FR-020**: `archive-specs` MUST run the store for the branch being removed.
  No repository's `pre_remove` hook changes.
- **FR-021**: When the store's push fails at removal, removal MUST print a
  warning and go ahead.
- **FR-022**: Removal MUST NOT print "durable" in any layout.

**Checking**

- **FR-023**: `wfctl check specs` MUST list every spec dir in the spec store
  that is not stored, with "uncommitted: N files" or "committed, not pushed".
  It MUST list a spec dir whose branch has a worktree in this repository under
  a separate "In progress" heading, and exit 1 only when a spec dir outside
  that heading is listed.
- **FR-024**: `wfctl check specs` MUST exit 0 and say where the spec root is
  when the layout has nowhere to push.
- **FR-025**: The `check` group's help MUST describe both of its commands, not
  only a repository's configuration.

**Instructions**

- **FR-026**: The end-of-session instruction that says not to stage, commit, or
  push anything in the spec root MUST change, so that it no longer forbids the
  store in a spec store with an upstream branch.

### Key Entities

- **Spec dir**: one branch's folder of pipeline output, named for the branch,
  under the spec root.
- **Spec root**: the folder holding every branch's spec dir, resolved by
  `wfctl feature-paths`.
- **Spec store**: a spec root that is the top of its own git repository. In
  this repository it is a separate clone, and in pfms it is a worktree of the
  code repository. Both have `specs-trunk` checked out.
- **Upstream branch**: the remote branch the spec store's checked-out branch
  tracks. wfctl reads git's local copy of it, which a push updates.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A branch that runs its pipeline through `implement` and follows
  each next command has its spec dir on the remote, with no git command typed
  by a person or by the agent.
- **SC-002**: A branch whose worktree is removed with a file written after the
  last store has that file on the remote after removal, in 100% of removals
  where the remote is reachable.
- **SC-003**: Zero removal messages contain "durable".
- **SC-004**: `wfctl check specs` lists every spec dir with an uncommitted file
  or an unpushed commit, with no false negatives, against this repository's
  spec store.
- **SC-005**: A store run while another branch has edited and untracked files in
  the spec store leaves all of them byte-for-byte unchanged.
- **SC-006**: `wfctl status` takes no more than 0.5 seconds longer with the pass
  than without it, against this repository's spec store.

## Validation Strategy _(mandatory)_

The definition of done for a code change in this repository:

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
uv run wfctl doctor
```

The tests build a bare remote and two clones in a temporary directory, as the
brainstorm's scratch tests did, and cover:

1. A commit that includes only this branch's folder, with another path already
   staged.
2. A merge that leaves another branch's edited tracked file and untracked folder
   unchanged, then pushes.
3. A conflict in the branch's own folder that aborts, keeps the commit, and
   leaves other files unchanged.
4. An unreachable remote that keeps the commit and reports "committed, not
   pushed".
5. The pass reading `done`, `in_progress`, and `skipped` for each layout.
6. `check specs` listing uncommitted and unpushed dirs and exiting 1, and
   listing a dir whose branch has a worktree under "In progress" and exiting 0.
7. `archive-specs` running the store, warning on a failed push, and never
   printing "durable".
8. A second store waiting while the first runs, and failing with a message
   after 10 seconds when the first never finishes.

A fixture can't reproduce this repository's separate clone of an orphan branch
outside the tree, so the change is also run for real:

1. `wfctl store specs` on this branch's own spec dir, and the commit shown on
   `origin/specs-trunk`.
2. `wfctl check specs` reporting a spec dir that isn't stored.
3. `uv run wfctl install-skills`, then `/store-specs` run from the installed
   wrapper.
4. `time wfctl status` with and without the pass, for SC-006.

## Assumptions

- Pre-specify design context loaded from `design.md` in this spec dir.
- The #40 branch owns the copy-out for a spec dir inside the worktree, its
  `--overwrite` flag, its guard against overwriting a copy that differs, and
  `archive unsaved`. Whichever branch merges first creates `store specs` with
  the layout dispatch, and the other merges `main` in.
- Each branch writes only its own folder in the spec store, so a merge conflict
  means one folder changed on two machines.
- One person writes to the spec store's remote branch, so wfctl's local copy of
  it is only stale after a deletion or a force push.
- The push from the removal hook runs in the user's shell, outside the agent's
  permission layer. Andre approved pushing at removal on that basis.
- The 58 older untracked spec dirs in this repository's spec store are not this
  branch's to commit. They are what `check specs` should report.
