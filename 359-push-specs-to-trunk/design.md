# Storing a branch's spec dir on its spec store's remote

## Problem Statement

How might we make sure every branch's spec dir reaches the spec store's remote,
with nobody typing a git command, and make any spec dir that didn't get there
show up as a finding instead of a green tick?

Today nothing in wfctl commits or pushes a spec dir. Each branch's agent has to
remember to do it by hand, and twice now that has failed for most branches. A
sweep found 58 spec dirs that were never committed, and weeks after they were
recovered, 59 entries were untracked again. Worktree removal printed
`✓ spec dir is durable — nothing there was at risk` over every one of them. That
message only meant that removing the worktree doesn't delete a folder outside
it, and readers took it to mean the specs were backed up.

## Recommended Direction

wfctl stores the spec dir itself, and it reads whether a spec dir is stored from
git every time it is asked. The agent never reports it. The level-2 record
`spec-storage-read-from-git` holds that decision.

Two commands do the work:

```
wfctl store specs     commit this branch's folder, merge the upstream, push
wfctl check specs     list every spec dir that is not stored
```

Storing happens in two places:

1. The pipeline. Once `implement` is done, a built-in pass names `/store-specs`
   as the next command until the spec dir is stored. An unattended run stores
   its own specs before it opens a pull request.
2. Worktree removal. The `archive-specs` command every removal hook already
   calls runs `store specs`, which picks up files written after the pipeline's
   last store. Review reports are the usual case, because the review panel
   writes them after the store.

`store specs` answers one question, whether this branch's spec dir is somewhere
safe, and the layout decides how:

1. In a spec store with an upstream branch, it commits only this branch's
   folder, fetches, merges the upstream, and pushes. It never rebases and never
   force-pushes.
2. In the default layout, with `specs/` inside the worktree, it copies the spec
   dir out to the main checkout at removal and says the copy is not backed up.
   The #40 branch owns this half.
3. In a plain folder outside any repository, it does nothing and says where the
   files are.

### What you see

A store that pushed names what it stored:

```
✓ stored 4 files → origin/specs-trunk (8c1d0e2)
    reviews/panel-1.md, reviews/panel-2.md, tasks.md, plan.md
```

The output says "files", not "specs", because "4 specs" reads as four features'
folders. `wfctl check specs` counts folders, so it says "spec dirs".

The other layouts say plainly what happened:

| Layout | Removal says |
|---|---|
| Spec store, pushed | `✓ stored N files → origin/<branch> (<sha>)` |
| Spec store, GitHub unreachable | committed, not pushed |
| Spec store with no upstream branch | committed, not backed up |
| `specs/` inside the worktree | copied to the main checkout, not backed up |
| Plain folder outside any repository | not backed up anywhere, with the path |

"Durable" is gone from every removal message.

### When something fails

Removal stops only when it would delete something that could not be saved. A
failed copy-out stops the removal, because once the worktree is gone that copy
is the only one. A failed push prints a warning and lets the removal go ahead,
because the commit stays in the spec store on disk. `wfctl check specs` then
lists it as not pushed, and the next store from any branch pushes it. So you can
remove a worktree while GitHub is down, and nothing is lost.

When the remote has moved on, the store merges it and pushes. When the merge
conflicts, it aborts, keeps its own commit, and names the folders in conflict.

### What "on GitHub" means

wfctl checks whether the commit is on git's local copy of the remote branch,
`origin/<branch>`, which a push updates. So `wfctl status` never touches the
network. That local copy goes stale only if someone deletes or force-pushes the
remote branch, and Andre accepted that while he is the only one writing to it.

## Key Assumptions to Validate

Checked:

- [x] `git add -A -- <dir>` followed by `git commit -m … -- <dir>` commits only
  that folder, and leaves another path that was already staged in the index.
- [x] `git log @{u}..HEAD -- <dir>` lists the unpushed commits that touch the
  folder, and is empty right after a push, with no fetch.
- [x] With another branch's tracked file edited and another's folder untracked,
  `git rebase` refuses and `git merge --no-edit` succeeds, leaving both exactly
  as they were. The push after the merge succeeds.
- [x] pfms's spec store is a worktree of the pfms repository, and this
  repository's is a separate clone. Both run `archive-specs` from `pre_remove`
  with no `|| true`.

Assumed:

- [ ] Reading git on every `wfctl status` stays cheap with hundreds of folders in
  the store. Test by timing `wfctl status` against this repository's spec store.
- [ ] `git merge --abort` after a conflict leaves other branches' edits alone.
  Test it in the suite before the store relies on it.
- [ ] Each branch writes only its own folder, so a conflict means one folder
  changed on two machines. Two branches sharing a folder would break this.
- [ ] Nothing treats "`implement` is done" as "the pipeline is finished". The
  orchestrate skill is the first place to check.

## MVP Scope

In:

1. `wfctl store specs` for a spec store with an upstream branch: commit one
   folder, fetch, merge, push, and the five messages above.
2. The `store-specs` pass under `implement`, its reader, and the `/store-specs`
   wrapper, which runs `wfctl report-block` when the host refuses the push.
3. `wfctl check specs`, and a wider help line for the `check` group.
4. `archive-specs` running `store specs`, with the push warning and the
   "durable" message removed.
5. The end-of-session instruction "Report only. Do not stage, commit, push, or
   delete anything in the spec root" changed for a spec store with an upstream.
6. A real run: store this branch's own spec dir and show the commit on
   `origin/specs-trunk`, then show `wfctl check specs` reporting a folder that
   isn't there.

Out, and owned by #40: the copy-out for `specs/` inside the worktree, its
`--overwrite` flag, its guard against overwriting a copy that differs, and
`archive unsaved`.

## Not Doing (and Why)

- Naming `specs-trunk` anywhere in wfctl. The store pushes whatever branch the
  spec store has checked out, so a separate clone and a worktree of the code
  repository both work.
- Committing a spec root inside the code repository. The commit would land on
  the feature branch.
- Rebasing or force-pushing. A rebase refuses while another branch has an edited
  file in the shared checkout, `--autostash` would put other branches' edits on a
  stash stack pfms shares with every worktree, and a force push can only delete
  other branches' specs.
- Reporting unstored spec dirs from `wfctl doctor`. Doctor reports drift between
  what wfctl installed and what it ships, and a spec store is neither.
- Sweeping the 58 older untracked spec dirs. Andre hasn't decided whether to
  commit them, and they are the evidence for what `check specs` should report.
- An override for a failed copy-out at removal. A person should look at it.

## Open Questions

- Which branch merges first. Whichever does creates `store specs` with the
  layout dispatch, and the other merges `main` in.

## Software design decisions

- docs/architecture/design/store-specs-implement-pass.md — storing the spec dir is a built-in pass under `implement`, not a step or a fact
- docs/architecture/design/store-specs-at-removal.md — removal reaches the store through `wfctl hook worktree-remove`, with `archive-specs` as its hidden alias so existing hooks keep working, and the copy-out moves under `store specs`
- docs/architecture/design/store-specs-merges-before-push.md — the store merges the upstream before it pushes, and never rebases or forces
