# Data model: storing a branch's spec dir

Nothing here is written to disk by wfctl. Every value below is computed from git
when it is asked for, and thrown away afterwards (`session-state-is-re-derived`,
FR-014). The store writes two things: git history in the spec store and,
when a run ends `stored`, one `store-specs` action event in the session log
(research R15). The `store-specs` pass reads only git.

## Layout

Which kind of folder the spec root is. Computed by
`_spec_store.layout(spec_root, repo_root)` from git, on every call (research R2).

| Kind | When | What the store does |
| --- | --- | --- |
| `store` | The root is the top of its own checkout, on a branch of its own, and that branch has an upstream | commits, merges, pushes |
| `store_no_upstream` | Same, with no upstream branch | commits, says "committed, not backed up" |
| `in_repo` | Git, run in the root, finds the code repository's own checkout | nothing; says the spec dir is inside the code repository and not backed up |
| `unmanaged` | A plain folder, or a folder inside some other repository | nothing; says "not backed up anywhere" with the path |

Carried as a small `NamedTuple`: the kind, the root, and for `store` the remote
name and the upstream ref (`origin/specs-trunk`), which the output prints.

## Spec dir state

Whether one spec dir is stored. Computed by `_spec_store.unstored(root,
paths)` from the two git commands in research R3.

| Field | Meaning |
| --- | --- |
| `name` | The spec dir's folder name under the root |
| `uncommitted` | How many files under it `git status` lists, untracked included |
| `unpushed` | True when a commit touching it is missing from `@{u}` |

A spec dir is stored when `uncommitted` is 0 and `unpushed` is false (FR-015).
Only unstored dirs are returned, so an empty result means everything is stored.

The text each state renders as, shared by the pass, `check specs`, and removal:

| State | Text |
| --- | --- |
| `uncommitted` > 0 | `uncommitted: N files` |
| `uncommitted` = 0, `unpushed` | `committed, not pushed` |

When both hold, the uncommitted count is what prints, since committing is the
next thing that has to happen.

## Store result

What one run of `wfctl store specs` ended with. The CLI prints it and picks the
exit code from it (research R6).

| Outcome | Exit | First line printed |
| --- | --- | --- |
| `stored` | 0 | `✓ stored N files → origin/<branch> (<sha>)` |
| `already_stored` | 0 | `✓ spec dir already stored on origin/<branch>` |
| `not_applicable` | 0 | the layout's sentence from the table above, with the path |
| `no_spec_dir` | 0 | `ℹ no spec dir for <branch>` |
| `committed_not_backed_up` | 0 | `⚠ committed N files, not backed up — <branch> has no upstream branch`, or `⚠ nothing new to commit, …` when the spec dir was already committed |
| `not_pushed` | 1 | `⚠ committed N files, not pushed — origin/<branch> is unreachable` |
| `push_refused` | 1 | `✗ committed N files, push refused — origin/<branch> moved again` |
| `conflict` | 1 | `✗ committed N files, merge conflicts in <folders>` |
| `merge_blocked_staged` | 1 | `✗ committed N files, merge blocked by files staged in <folders>` |
| `merge_refused` | 1 | `✗ committed N files, merge blocked by local edits to <files>`, or `… merge blocked by untracked files the upstream adds: <files>` when the files in the way are new |
| `merge_in_progress` | 1 | `✗ nothing committed, a merge is already in progress in <root>` |
| `locked` | 1 | `✗ another store is running in <root>` |
| `git_failed` | 1 | `✗ store failed: <git's message>` |

Every outcome after the first line that names files prints them on the next
line, indented, as FR-008 asks for `stored`.

`conflict` and `merge_in_progress` each print a remedy that names the git
commands to run in the spec store, and say that every branch's store fails
until it is done (`contracts/cli.md`). `merge_in_progress` is found before the
store commits, and the store leaves that merge in place rather than aborting it.

`StoreResult.stops_removal` is false for every outcome in this table when the
spec dir is outside the worktree. Removal reads that property, never the exit
code, so each exit-1 outcome above prints as a warning at removal and the
removal goes ahead (research R6, FR-021).

It is true for any result where the spec dir is inside the worktree and was not
copied out, since deleting the worktree would delete the only copy. That covers
#40's copy-out refusals in the default layout, and `not_applicable` for a spec
dir inside the worktree. On this branch that `not_applicable` never reaches
removal, because `archive-specs` runs the store only where the spec dir is
outside the worktree (research R11). Once #40 is merged, its copy-out runs first
in the default layout, and its outcome is what removal reads there.

`stops_removal` and the exit code are separate. `not_applicable` still exits 0
when `store specs` is run by hand inside the worktree, since the store has
nothing it can do in that layout (research R6).

`committed_not_backed_up` exits 0 because nothing more can be done for that
layout, and it says so. `<branch>` there is the spec store's own branch, not
the feature branch. The pass reads `skipped` for it rather than
`in_progress`.

## The `store-specs` pass

A built-in `SubStep` under `implement`: name `store-specs`, command
`/store-specs`, `_AUTOMATIC`, reader `_evidence.store_specs`.

The reader asks for the layout, then for this spec dir's state:

| Layout and state | Pass reads | `display` |
| --- | --- | --- |
| `store`, stored | `done` | none |
| `store`, uncommitted | `in_progress` | `uncommitted: N files` |
| `store`, committed, not pushed | `in_progress` | `committed, not pushed` |
| `store_no_upstream` | `skipped` | `no upstream branch; not backed up` |
| `in_repo` | `skipped` | `inside the code repository; not backed up` |
| `unmanaged` | `skipped` | `not backed up anywhere: <root>` |

`reason` is `None` in every row (research R4). A person can still declare the
pass inapplicable with `wfctl step none implement.store-specs --reason "…"`,
and the claim wins over the reader as it does for every pass.

## `check specs` listing

Built from the root's layout, the unstored spec dirs, and the set of spec dirs
some worktree of this repository resolves to (research R10).

| Group | Contains | Counts toward exit 1 |
| --- | --- | --- |
| not stored | unstored spec dirs no worktree resolves to | yes |
| In progress | unstored spec dirs a worktree resolves to | no |

In a layout other than `store`, there is no listing: the command says where the
spec root is and that nothing there can be pushed, and exits 0 (FR-024).

## The lock

A file named `wfctl-store.lock` in the spec store's git directory, held with
`fcntl.flock` for the whole store run (research R5). The file's contents are
never read, and the file is left in place after the run because removing it
would race a second store opening it.
