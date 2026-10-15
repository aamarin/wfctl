# CLI contract: storing and checking spec dirs

The commands below are what this feature exposes. Output examples are exact
apart from paths, counts, and commit ids. Tests assert on them with `NO_COLOR`
set.

## `wfctl store specs`

Stores the current branch's spec dir. Takes no arguments and reads the branch
and spec dir the same way `wfctl feature-paths` does.

```
$ wfctl store specs
✓ stored 4 files → origin/specs-trunk (8c1d0e2)
    reviews/panel-1.md, reviews/panel-2.md, tasks.md, plan.md
```

```
$ wfctl store specs
✓ spec dir already stored on origin/specs-trunk
```

```
$ wfctl store specs            # GitHub unreachable, or the fetch timed out
⚠ committed 2 files, not pushed — origin/specs-trunk is unreachable
    reviews/panel-1.md, reviews/panel-2.md
    the next `wfctl store specs` with files to push sends it
```

```
$ wfctl store specs            # the remote moved again between merge and push
✗ committed 2 files, push refused — origin/specs-trunk moved again
    reviews/panel-1.md, reviews/panel-2.md
    run `wfctl store specs` again to merge and push
```

```
$ wfctl store specs            # this branch's folder changed on two machines
✗ committed 2 files, merge conflicts in 359-push-specs-to-trunk/
    the merge was aborted and your commit is kept
    every branch's store fails until a person resolves this conflict
    to resolve it, run `git merge @{u}` in /Users/andremarin/Development/wfctl-specs, fix the files, run `git commit`, then `wfctl store specs`
```

The conflict stops every branch's store, not only this one. Each store merges
the same upstream into the same checkout, so each one meets the same conflict
until a person resolves it.

```
$ wfctl store specs            # a merge was left unfinished, by a killed store or by hand
✗ nothing committed, a merge is already in progress in /Users/andremarin/Development/wfctl-specs
    every branch's store fails until that merge is finished or aborted
    to finish it, fix the files and run `git commit` in /Users/andremarin/Development/wfctl-specs, or run `git merge --abort` there
```

The store doesn't abort a merge it finds in progress, because a person may be
halfway through resolving it.

```
$ wfctl store specs            # a file in another folder is staged, and the remote moved
✗ committed 2 files, merge blocked by files staged in 188-check-rework-loop/
    run `wfctl store specs` from the branch that owns that folder, or unstage
    the files, then run `wfctl store specs` again
```

```
$ wfctl store specs            # nothing staged, but an unstaged edit is in the way
✗ committed 2 files, merge blocked by local edits to 188-check-rework-loop/tasks.md
    store or discard that edit, then run `wfctl store specs` again
```

```
$ wfctl store specs            # nothing staged, but a new file the upstream adds is in the way
✗ committed 2 files, merge blocked by untracked files the upstream adds: 188-check-rework-loop/notes.md
    move those files aside, then run `wfctl store specs` again
```

When git names both an edited file and an untracked one, the edit is reported
first, and the next run reports the untracked file.

A successful store that pushed records a `store-specs` action, the same one
`wfctl report-action store-specs` writes, so it lifts a host block the
`/store-specs` wrapper filed. `already_stored` records nothing (research R15).

```
$ wfctl store specs            # another store held the lock for 10 seconds
✗ another store is running in /Users/andremarin/Development/wfctl-specs
```

Layouts with nowhere to push:

```
$ wfctl store specs            # spec store with no upstream branch
⚠ committed 3 files, not backed up — specs-trunk has no upstream branch
```

```
$ wfctl store specs            # the same, run again with nothing new
⚠ nothing new to commit, not backed up — specs-trunk has no upstream branch
```

```
$ wfctl store specs            # specs/ inside the code repository
ℹ /repo/specs/359-push-specs-to-trunk is inside the code repository — not committed, not backed up
```

```
$ wfctl store specs            # a plain folder
ℹ /notes/specs/359-push-specs-to-trunk is not backed up anywhere
```

**Exit codes**: 0 when the spec dir is stored, already stored, or the layout has
nowhere to push. 1 for every `✗` line and for "not pushed" (research R6).

**Never**: rebases, stashes, force-pushes, names `specs-trunk` in its own code,
or stages a path outside this branch's spec dir (FR-001, FR-004, FR-005).

## `wfctl check specs`

Lists every spec dir in the spec store that is not stored. Reads no network.

```
$ wfctl check specs
✗ 2 spec dirs not stored
    188-check-rework-loop      uncommitted: 12 files
    552-bob-command-rename     committed, not pushed

In progress (2 spec dirs, still have a worktree):
    359-push-specs-to-trunk    uncommitted: 4 files
    470-capability-modeling    uncommitted: 2 files
```

Exit 1, because the first group is not empty.

```
$ wfctl check specs
✓ every spec dir without a worktree is stored

In progress (2 spec dirs, still have a worktree):
    359-push-specs-to-trunk    uncommitted: 4 files
    470-capability-modeling    uncommitted: 2 files
```

```
$ wfctl check specs
✓ every spec dir is stored
```

Both exit 0. The "In progress" block is left out when it is empty.

```
$ wfctl check specs            # any layout other than a spec store with an upstream
ℹ spec root /repo/specs is inside the code repository — nothing there can be pushed
```

Exit 0 (FR-024). The sentence after the path is the layout's, as in `store
specs` above.

## `wfctl check --help`

The group's help line changes from "Validate a repository's own configuration."
to "Check a repository's configuration and its spec store." (FR-025).

## `wfctl archive-specs` (removal)

#40 makes this a hidden alias of `wfctl hook worktree-remove`, which calls
`store specs` and then `archive unsaved`. If that lands first, the output below
comes from `store specs` through that command, and this section describes it
unchanged (research R11).

Unchanged where the spec dir is inside the worktree (research R11). Where it is
outside, the line

```
✓ spec dir is durable (<path>) — nothing there was at risk, nothing copied
```

is replaced by whatever `wfctl store specs` printed, and a failed store becomes
a warning that lets removal go ahead:

```
⚠ committed 2 files, not pushed — origin/specs-trunk is unreachable
    reviews/panel-1.md, reviews/panel-2.md
    the next `wfctl store specs` with files to push sends it
```

Where the spec dir is outside the worktree, no store outcome makes removal exit
non-zero. The word "durable" appears in no output (FR-022).

That rule covers the store's half only. Once #40 is merged, `archive unsaved`
runs after the store and keeps its own refusals, so removal still exits non-zero
on a worktree with uncommitted edits or unpushed commits. The removal tests
moved onto the hook therefore start from a clean worktree, so that a failure
they see comes from the store.

## `wfctl status --json`

`implement` gains one entry in `sub_steps`:

```json
{"name": "store-specs", "state": "in_progress", "annotation": "uncommitted: 4 files",
 "command": "/store-specs", "manual": false, "claimed": null,
 "needs_person": false, "is_current": true}
```

`next_command` is `/store-specs` while it reads `in_progress`. That includes
while a host block on `store-specs` holds `implement`, where `auto` is `false`
and the step carries the block's remedy (research R15). A block filed for any
other action routes as it does today, whatever the pass reads. The payload's shape does
not change, so its version stays 1.3 (research R13).

## `/store-specs`

A command wrapper at `wfctl/agents/commands/store-specs.md`. It runs `wfctl
store specs` and nothing else that writes. When the host refuses to run it, the
wrapper runs `wfctl report-block store-specs --reason "…"` and stops, and it
never tries another way to push (FR-019). When the store exits 1, the wrapper
reports what it printed and doesn't retry. Either way it then invokes
`speckit-orchestrate`, like every pipeline command, and orchestrate's stall
count is what stops a run that keeps failing to push.
