# Research: saving unsaved work when a worktree is removed

Each entry is one decision the plan rests on. The spec and the two level-2
records decide what is saved and when removal stops. The level-3 record
`40-archive-is-a-command-group` decides the command shape. This file decides how
the code does it.

## R1. Three modules, split so the second merge with #359 stays small

**Decision**: The work lands in three places.

1. `wfctl/_archive.py` is rewritten as the module behind `wfctl archive
   unsaved`. It holds the two checks, the list of what to save, and the copy
   into `unsaved/`. The numbered archive, `_SPEC_MAP`, the index renderer and
   the `.agent/` rescue are deleted from it. `is_inside` stays, since the store
   uses it too.
2. `wfctl/_copy_out.py` is new. It holds the default layout's copy of spec
   files out to the main checkout: the comparison, the copy, and `--overwrite`.
3. `wfctl/_spec_store.py` is new and small. It holds `StoreResult` and a
   `store()` that picks which half runs. On this branch the only halves are the
   copy-out and "nothing to do here".

**Rationale**: #359 plans `_spec_store.py` with `StoreResult` and `store()` in
it, and has written no code yet. Whichever branch merges second meets an add/add
conflict on that file. Keeping the copy-out in its own module means the
conflicting file is a few dozen lines of dispatch and a result type, and both
branches already agree on the result's field names (R7). The git work #359 adds
stays in its own functions inside that file.

**Alternatives considered**: Putting the copy-out in `_spec_store.py` too. We
didn't choose it because the add/add conflict would then cover every line of
both features' store code. A separate `_store_result.py` that both branches
import was also possible, but #359's plan already names `_spec_store.py` as the
home of `StoreResult`, and moving it would make #359 revise a reviewed plan for
no gain.

## R2. Every check runs before anything is copied, and every finding is printed

**Decision**: `wfctl hook worktree-remove` works in two phases.

1. Checks. It resolves the spec dir and the layout, compares the worktree's
   spec files against the main checkout's copy, checks for uncommitted edits,
   and checks for unmerged commits. Nothing is written.
2. Copies. Only when no check refused, it runs `store()` and then the copy into
   `unsaved/`.

When more than one check refuses, the output lists all of them in one block, so
you don't fix one problem, retry, and only then hear about the next.

**Rationale**: FR-002 requires that a stopped removal leaves nothing
half-copied. The copy-out comparison is a check like the other two, so it runs
in phase 1, and `store()` repeats it in phase 2 as part of copying. That repeat
costs a second read of a handful of markdown files.

A failure in phase 2 can still leave the spec files copied out and `unsaved/`
not written, for example when the disk fills during the second copy. That is
acceptable: the copied-out files sit where every wfctl command reads them, and a
retry finds them identical and copies nothing (FR-025).

**Alternatives considered**: Calling `store()` first and `archive unsaved`
second, each with its own checks. We didn't choose it because a refusal from
the second would come after the first had already copied, which is the case
FR-002 rules out.

## R3. "Not merged" is answered with `git merge-tree`, scoped to commits on no remote

**Decision**: The check runs three git commands in the worktree.

1. `git rev-list HEAD --not --remotes` lists the commits that are on no remote
   branch. When it is empty, the check passes and stops there.
2. `git merge-tree --write-tree <trunk> HEAD` computes the tree a merge would
   produce. Exit 0 with a tree id is a clean merge. Exit 1 is a conflict.
3. `git rev-parse <trunk>^{tree}` reads trunk's own tree.

The branch passes when the merge is clean and its tree equals trunk's tree,
since merging would change nothing. A conflict, or a different tree, stops the
removal and names the commits from step 1 as `<short sha> <subject>`.

`<trunk>` is `_paths.trunk_branch(worktree)`, the same answer `wfctl start`
uses (FR-012). When that is None, or any of the three commands fails in a way
other than a conflict, the check prints a warning naming it and passes (FR-013).
git older than 2.38 rejects `--write-tree`, and that lands in the same warning.

**Rationale**: A squash merge leaves the branch's own commits on no remote once
the remote branch is deleted, so step 1 alone would stop every removal after a
squash merge in pfms. Step 2 asks whether trunk already holds the work,
whichever way it got there. Step 1 keeps the common case fast and keeps a branch
that was pushed and never merged from being stopped: its commits are on a
remote, so they survive the removal.

**Alternatives considered**: `git cherry`, which compares patch ids. We didn't
choose it because a squash commit's patch id matches none of the branch's own
commits, so it reports every commit as unmerged. Asking the tracker whether the
pull request merged is rejected in the level-2 record.

## R4. Uncommitted edits come from `git status`, with untracked files left out

**Decision**: `git status --porcelain=v1 -z --untracked-files=no` in the
worktree. Any entry stops the removal, and the output names each path. That
covers staged and unstaged edits, deletions, renames, and a submodule with
changes.

**Rationale**: `-z` keeps paths with spaces or newlines intact. Leaving
untracked files out is the point: they are saved, not refused.

When the command fails, the check warns and passes (FR-013).

## R5. What `unsaved/` holds, and how a nested repository and a symlink are copied

**Decision**: The list of what to save is built from two sources.

1. `git ls-files --others --exclude-standard -z` in the worktree, which lists
   every untracked file that isn't ignored. A separate git repository inside
   the worktree is listed once, as its folder with a trailing `/`, because git
   doesn't descend into it.
2. Each folder listed under `save_on_remove` in the worktree's `wfctl.json`
   that exists (R10).

Anything under the spec dir is dropped from the list (FR-018). The spec dir is
usually gitignored and never appears, but a repository that doesn't ignore it
would otherwise save it twice.

Copying follows three rules.

1. A file is copied with `shutil.copy2`, keeping its timestamps.
2. A symlink is recreated as a link with the same target, using `os.readlink`
   and `os.symlink`, and is never followed (FR-019).
3. A folder, which is either a nested repository or a `save_on_remove` folder,
   is copied with `shutil.copytree(symlinks=True)`, so its history and its own
   links come across as they are (FR-019a).

The copy goes into `unsaved.staging` first. When it is complete, an existing
`unsaved/` is renamed to `unsaved-<UTC timestamp with microseconds>`, and the
staging folder is renamed to `unsaved/` (FR-020, FR-021). Any exception in the
copy or either rename removes the staging folder and becomes a refusal. This is
the same pattern `_archive.archive` uses today, and its comments carry over.

The saved-file count, and the first 20 paths printed after it (FR-023), come
from walking the staging folder once the copy is complete. A folder therefore
counts as the files inside it, and the paths printed are files, sorted.

**Rationale**: Listing from the finished copy rather than from git's list means
the count is what actually landed. A nested clone of 3,000 files counts as
3,000, which is true, and the 20-line cap keeps that from flooding the output.

**To verify first**: that `git ls-files --others` lists a nested repository as
one `dir/` entry, and lists an untracked symlink as a path. Both are the first
two tests written, before the copy code, since the copy rules above rest on
them.

**Alternatives considered**: `git status --porcelain`, which collapses an
untracked folder to one `dir/` entry. We didn't choose it because a folder
holding one untracked file among tracked ones then has to be expanded by hand,
and `ls-files` already lists files.

## R6. Copying spec files out compares bytes, and shows a diff when they differ

**Decision**: In the default layout the copy-out works on one spec dir.

- The source is the spec dir inside the worktree.
- The destination is `spec_root(main checkout) / <spec dir name>`. That is the
  folder `wfctl feature-paths` resolves from the main checkout for the same
  branch.
- Each file under the source is compared with the file at the same relative
  path in the destination, byte for byte.

A file missing from the destination is copied. An identical file is left alone.
A file that differs makes the copy-out refuse: the result lists each differing
file and carries a unified diff of each, made with `difflib.unified_diff`,
destination first. A file that exists only in the destination is never touched
(FR-025). With `--overwrite`, differing files are replaced by the worktree's
copies (FR-027).

When nothing differs, the copy happens file by file with `shutil.copy2`. A
failure partway leaves the files already copied, which is harmless since each is
a complete copy of the worktree's file, and becomes a `copy_failed` result that
stops the removal (FR-028).

A spec file that is not valid UTF-8 is reported as differing with the line
"binary file differs" instead of a diff.

**Rationale**: Comparing bytes is exact and needs no git. The diff is what lets
you decide whether the older copy has something the newer one lacks, which is
the reason the removal stops at all.

**Alternatives considered**: `git diff --no-index`. We didn't choose it because
it adds a subprocess for what `difflib` does in-process, and its exit code mixes
"differs" with "failed".

## R7. `StoreResult` carries the outcome and whether the spec dir is in the worktree

**Decision**: `StoreResult` has the fields #359's data model names, plus the
ones the copy-out needs:

| Field | Meaning |
| --- | --- |
| `outcome` | One of the names in the data model |
| `spec_dir` | The spec dir it acted on, or None |
| `inside` | True when the spec dir is inside the worktree being removed |
| `lines` | The output, already formatted, printed as is |

`stops_removal` is a property. It is true when `inside` is true and the outcome
is not `copied`, `already_copied`, or `to_unsaved`. That is FR-029 written as
code, and it is the rule #359's research R6 describes.

`exit_code` is a property too. It is 1 for `differs` and `copy_failed`, and 0
for everything else (FR-030).

The layout with no main checkout gets its own outcome, `to_unsaved`. The hook
reads it and tells the copy into `unsaved/` to include the spec dir as a folder
(FR-032). It doesn't stop the removal, because the spec files are then saved by
the same copy as the rest of the unsaved work, and a failure there stops the
removal anyway.

**Rationale**: Putting the rule on the result rather than in the hook means
`store specs` by hand and the hook can't disagree, which is the same reason
#359 gives. The outcome names for the copy-out are new, so they can't clash
with #359's `stored` and `already_stored`.

## R8. `wfctl hook worktree-remove` is a normal typer command, with two hidden aliases

**Decision**: The command goes in `hook_app` as `worktree-remove`, taking
`<worktree>` and `<handle>` as optional arguments that default to
`$WM_WORKTREE_PATH` and `$WM_HANDLE`, as `archive-specs` does today. The same
function is registered on the top-level app as `archive-specs` and
`archive-story`, both hidden (FR-004, FR-005).

`archive-specs` prints no notice. `archive-story` keeps its notice, which now
names `wfctl hook worktree-remove` as the command to put in `pre_remove`, and
tells you to edit `.workmux.yaml` by hand, since `install-config` can't rewrite
a `pre_remove` block that has entries.

The exit code follows three rules.

1. A check refused, or a copy failed: exit 1, so workmux stops the removal.
2. A check git couldn't answer: a warning, and exit 0.
3. Any other exception: a warning naming it, and exit 0. This keeps the
   existing rule that an unrelated bug never leaves a worktree stuck.

It doesn't go through `_entry.py`'s fast path. That path exists for hooks that
run on every prompt or tool call, and this one runs once per removal.

**Rationale**: Registering one function under three names is what `archive-specs`
and `archive-story` already do, so there is no new mechanism.

## R9. The seeded template gets the block that can stop a removal

**Decision**: The template's `pre_remove` entry changes from

```
- command -v wfctl >/dev/null && wfctl archive-specs "$WM_WORKTREE_PATH" "$WM_HANDLE" || true
```

to the block scalar `_workmux.ARCHIVE_HOOK` already holds, with the command
changed to `wfctl hook worktree-remove` and the warning changed to say unsaved
work was not saved. The constant is renamed `REMOVE_HOOK`, and a test asserts
the template's `pre_remove` block contains it, so the two can't drift again.

`pre_remove_wired` accepts `hook worktree-remove`, `archive-specs`, and
`archive-story` (FR-007). `doctor`'s `_check_workmux_hook` names the new command
in its warning and prints the `unsaved/` destination instead of `archive/`.

**Rationale**: The `|| true` in today's template means a repository seeded from
it can never stop a removal, whatever the command exits. Neither live repository
has it, since both were wired by hand, but the next one seeded would. FR-006
already asks for the block that falls back to a warning, so this is the template
catching up with the spec rather than a new requirement.

## R10. `save_on_remove` is read leniently at removal and strictly by `check config`

**Decision**: One reader, `_archive.declared_folders(repo_root)`, returns the
usable folder paths and a list of problems, the same shape as
`_paths.declared_trunk`. An entry is a problem when it isn't a string, is
empty, is absolute, or resolves outside the repository. The key being present
and not a list is a problem too.

- `wfctl check config` adds those problems to its findings (FR-034).
- Removal skips a problem entry and prints it as a warning. A folder outside
  the repository isn't deleted by the removal anyway, so skipping it loses
  nothing.
- A listed folder that doesn't exist is neither a problem nor a warning
  (FR-016, FR-034).

The file read is the worktree's own `wfctl.json`, since it is committed and the
worktree has it.

**Rationale**: A malformed config shouldn't refuse a removal, and `check config`
is where its author learns about it, which is how `trunk` already works.

## R11. What is deleted

- The numbered archive: `_SPEC_MAP`, `_render_index`, `_plan`, and `archive` in
  `_archive.py` (FR-033). Archives already on disk are left alone.
- The `.agent/` rescue, `_LEGACY_DEST_PREFIX`, and its notice (FR-035).
- The "durable" line in `archive_specs_cmd` (FR-031).
- The comment in `_completion.py` that says `_archive._SPEC_MAP` keeps its own
  copy of a path.
- In `docs/ponytail-debt.md`, row 6 (the `.agent/` rescue) is resolved, and
  row 5 (the `archive-story` alias) is updated to point at the new notice.
- In `docs/reference.md`, the `archive-specs` row is replaced by rows for
  `hook worktree-remove`, `archive unsaved`, and `store specs`.

## R12. Order of merging with #359

**Decision**: Whichever branch merges second merges `main` in and resolves
`_spec_store.py` and the `store` group in `cli.py`. If #40 is second, three
things are checked.

1. `store()` runs the copy-out before it would return #359's `not_applicable`
   for the `in_repo` layout, when the spec dir is inside the worktree and a main
   checkout exists.
2. The hook reads `stops_removal`, never `exit_code`.
3. #359's removal tests, moved onto the hook, start from a clean worktree,
   because `archive unsaved` refuses a dirty one regardless of what the store
   returned.

If #40 is first, #359's plan step 7 already says what it does.

## R13. The output is plain lines with `soft_wrap` and no markup in paths

**Decision**: Every printed path goes through `rich.markup.escape` or is printed
with `markup=False`, and every line carrying a path uses `soft_wrap=True`. The
manual route is quoted with `shlex.quote`, as it is today.

**Rationale**: These are the rules the current `archive_specs_cmd` comments
explain, and the reasons still hold: a `[` in a path is legal and rich swallows
it, and a wrapped route can't be pasted.
