# Saving unsaved work when a worktree is removed

## Problem Statement

How might we make sure that removing a worktree, even with `--force`, never
deletes work that exists nowhere else?

Today the removal hook saves only spec files, into a numbered archive in the
state dir that nobody opens. Everything else is unprotected once someone
passes `--force`. That includes untracked files, uncommitted edits, and
commits that were never pushed or merged, and `--force` is used routinely.

## Recommended Direction

Removing a worktree either saves the work that would be lost or stops the
removal. Work that wfctl can copy somewhere useful is copied. Work it can't
copy safely stops the removal, and the hook prints how to finish it by hand.

Each kind of work has one outcome:

1. Spec files inside the worktree are copied to the branch's spec dir,
   resolved from the main checkout, under their original names. That is where
   every other wfctl command already looks for them. The numbered archive in
   the state dir is no longer written. In this repository and in pfms, the
   spec root is a spec store outside the worktree, so `store specs` commits
   and pushes there instead (#359).
2. Untracked files that are not spec files are copied to `unsaved/` in the
   branch's state dir, at their original relative paths, so you can copy them
   back.
3. Ignored folders that the repository lists in `wfctl.json` are copied to the
   same `unsaved/` folder. Every other ignored file is deleted with the
   worktree, as it is today.
4. Uncommitted edits to tracked files stop the removal. So do commits that are
   on no remote and aren't merged into trunk. Either one might be work someone
   forgot to push or merge. This applies under `--force` too, and there is no
   override. The way through is the manual route the hook already prints:
   `git worktree remove`, then `git branch -D`.
5. If the branch's spec dir already holds files that differ from the
   worktree's copies, the removal stops. The hook lists each file that
   differs and shows the diff. Only you can know whether the older copy has
   something the newer one doesn't. To get through, you run
   `wfctl store specs --overwrite` by hand, or merge the files yourself, and
   then remove the worktree again. Identical files never stop a removal, and
   files that exist only in the spec dir are never touched.

The removal hook calls one command, named for when it runs:

```
wfctl hook worktree-remove  <worktree> <handle>
```

It runs two commands, and each stays visible because you also run them by
hand:

1. `wfctl store specs` handles items 1 and 5. It is #359's command, which
   makes sure a branch's spec files are somewhere safe, and the layout decides
   how. This feature adds the default layout's half: the copy-out to the main
   checkout, `--overwrite`, and the stop for a spec dir that differs.
2. `wfctl archive unsaved` handles items 2 through 4. It starts a new
   `archive` command group.

The workmux template seeds `wfctl hook worktree-remove` into `pre_remove`.
`archive-specs` becomes a hidden alias for it, because `install-config` can't
rewrite a `pre_remove` block that already has entries. As a result, existing
repositories pick up the new behavior when wfctl is updated, without editing
their hook, and so does any job added at removal later.

Removal no longer prints that the spec dir is "durable". In the default layout,
`store specs` says the spec files were copied out and that nothing backs the
copy up.

### How each command behaves

`hook worktree-remove` runs every check from both commands before it copies
anything. As a result, a refused removal leaves nothing half-copied.

A failed copy stops the removal. The issue left this open and leaned toward
best-effort, but once the worktree is gone the copy is the only one left. A
failed push to a spec store only prints a warning, because the commit stays in
the spec store on disk.

When git can't answer a check, the hook prints a warning and lets the removal
go ahead. This keeps the existing rule that an unrelated error never leaves a
worktree stuck.

The "not merged" check uses `git merge-tree --write-tree <trunk> HEAD` and
compares the result to trunk's tree. Checking only whether the commits were
pushed isn't enough. pfms deletes the branch on merge, and both repositories
allow squash merges, so after a squash merge the branch's own commits are on
no remote even though the work is on trunk. Trunk is the branch
`_paths.trunk_branch` already resolves.

If `unsaved/` already exists from an earlier removal of the same branch, it is
moved aside under a timestamp, the way the current archive handles a second
run. The new copy is written to a staging folder first and renamed into place
once it is complete.

There is no size cap. The untracked sets measured across the live worktrees
were small.

The spec dir is left out of the untracked set, so spec files aren't copied
twice. The install manifest isn't read, because every installed path is
gitignored and never shows up as untracked.

When there is no main checkout, as in a bare layout, there is no spec dir
outside the worktree. In that case spec files go to `unsaved/` with the rest.

The remove hook keeps calling the installed `wfctl`, not `uv run wfctl`. With
`uv run`, removing an old worktree would run that branch's old saving code.

## Checked

- git here is 2.44, and `git merge-tree --write-tree` needs 2.38 or later.
- Across four wfctl worktrees and one pfms worktree, the only gitignored
  markdown that wasn't generated was the `.workmux/` handoff. The issue's
  original filter, "all ignored `*.md` minus a few", would have copied 124
  `build/lib/` files in one worktree and 1,637 `node_modules/` files in pfms.
  That is why ignored files are opt-in per folder.
- pfms has `delete_branch_on_merge=true`, and both repositories allow squash
  merges.
- `wfctl/_workmux.py:257`, `wire_pre_remove`, only patches `pre_remove: []`
  and refuses a block that already has entries.
- `wfctl/cli.py:1416-1417` keeps `archive-story` as a hidden alias for the
  same reason `archive-specs` is kept now.

## Key Assumptions to Validate

- [ ] workmux 0.1.268 still runs `pre_remove` under `--force`. This was only
      verified on 0.1.211. Test it in the real removal test below.
- [ ] workmux can't tell the hook whether `--force` or `--keep-branch` was
      passed. If it can, the hook could skip the unpushed-commit check under
      `--keep-branch`, since the branch survives. Check workmux's hook
      environment.

The real removal test needs Andre, because the worktree guard refuses removing
a second worktree from here. Make a scratch worktree holding an untracked file,
a tracked edit, and an unmerged commit. Install wfctl from this branch with
`uv tool install`, then run `wm rm --force`. Run it once through the old
`archive-specs` hook line and once through `wfctl hook worktree-remove`.

## MVP Scope

In scope:

1. `wfctl hook worktree-remove`, the `wfctl archive` group with `unsaved`,
   and `archive-specs` as a hidden alias for the hook command.
2. The default layout's half of `store specs`: spec files copied to the spec
   dir, with the stop and `--overwrite` route for a spec dir that differs.
   Whichever of this branch and #359 merges first creates `store specs` with
   the layout dispatch, and the other merges `main` in.
3. Untracked files and listed ignored folders copied to `unsaved/`.
4. The stops for uncommitted edits and for commits that aren't pushed or
   merged.
5. The new `save_on_remove` key in `wfctl.json`, with `wfctl check config` reporting a listed
   path that points outside the repository.
6. The seeded workmux template calling `wfctl hook worktree-remove`, and
   `pre_remove_wired` accepting the new name.

Out of scope for the first version is anything in the list below.

## Not Doing (and Why)

- Saving tracked edits as a patch, which the issue proposed. A patch only
  helps someone who knows to look for it. Stopping the removal puts the edit
  in front of you while you can still commit it.
- An override for the stops. Andre chose to leave the manual route as the only
  way through.
- Copying every ignored markdown file. The measurements above show it would
  sweep build output and dependencies into the state dir.
- Moving or deleting the numbered archives that older removals wrote. They
  stay where they are.
- Pushing spec dirs to a spec store at removal. That is #359's half of
  `store specs`.
- Remembering the last copy-out, so a later removal could tell your own copy
  from someone else's. The copy-out only runs at removal or by hand, so the
  only case it helps is running it by hand, editing more, and then removing.
  In that case the removal stops and shows the diff, which is acceptable.
- Spec files that are uncommitted or unpushed in a spec root outside the
  worktree. That is #56.
- A size cap, for the reason given above.
- The special rescue for a legacy `.agent/` folder, where wfctl kept spec
  files before they moved to `specs/`. The rescue was meant to be temporary,
  and on 2026-10-14 no `.agent/` folder was left anywhere under Andre's
  Development directory. This change deletes it, along with the notice it
  prints. If a worktree still had one, git doesn't ignore it in this
  repository, so `archive unsaved` would copy it to `unsaved/.agent/` like any
  other untracked file. The hidden `archive-story` alias stays, because an old
  hook may still call it.

## Open Questions

- The issue body still describes the original design, a patch for tracked
  edits and no ignored files. It gets rewritten to match this document before
  the spec is written.

## Architecture decisions

These level-2 records decide what is saved and when the removal stops. Both
are proposed:

- `docs/architecture/worktree-removal-requires-saved-work.md`
- `docs/architecture/removal-copy-destinations.md`

## Software design decisions

- docs/architecture/design/40-archive-is-a-command-group.md — the removal hook calls `wfctl hook worktree-remove`, which runs `wfctl store specs` and then `wfctl archive unsaved`, with `archive-specs` kept as its hidden alias
