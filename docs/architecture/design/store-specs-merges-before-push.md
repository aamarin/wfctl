---
status: proposed
---

# The store merges the spec store's upstream before it pushes

## Context

Every branch stores its spec dir on the same branch of the spec store, and the
store can run on more than one machine. So when the store pushes, the remote
has often moved on since the last fetch, and a plain push is refused. Andre
wants the store to pick up those changes and push, not stop and leave the
branch to a person.

The spec store's checkout is also shared. While one branch stores its folder,
other branches have files sitting in the same checkout. Some of them are new
and untracked, and some are tracked files edited since their last store, such
as a `tasks.md` with tasks ticked off. Whatever the store does to pick up remote
changes must not touch those files.

## Verified

A scratch test (a bare remote, two clones, one branch already pushed from the
second clone, and in the first clone a modified tracked file in folder `200`,
an untracked folder `400`, and a commit for folder `100`):

- `git rebase origin/trunk` refuses with `error: cannot rebase: You have
  unstaged changes.`
- `git merge --no-edit origin/trunk` succeeds. Afterwards `git status --short`
  shows `M 200/tasks.md` and `?? 400/` exactly as before, and `git push`
  succeeds.
- pfms's spec store is a worktree of the pfms repository (`git rev-parse
  --git-common-dir` prints `/Users/andremarin/Development/pfms/.git`), so it
  shares one stash stack with every pfms worktree.

## Assumed

- Each branch writes only its own folder, so a merge conflict means the same
  folder changed on two machines. If two branches start writing one folder, a
  conflict becomes routine and this decision needs revisiting.
- When the merge does conflict, `git merge --abort` puts the checkout back
  without touching other branches' edits. Git refuses to start a merge that
  would touch an edited file, so a conflict can only land in files that were
  clean. A test has to confirm this before the store relies on it.

## Direct baseline

Push, and stop when the push is refused. The store reports that the remote has
moved on and leaves the commit local for a person to merge by hand. This was the
first proposal in the brainstorm.

## Decision

The store fetches, merges the upstream branch with `git merge --no-edit`, and
pushes. It never rebases and never force-pushes.

1. When the fetch fails because GitHub is unreachable, the store keeps its
   commit and reports "committed, not pushed". The next store from any branch
   pushes it, since a push sends every local commit on the branch.
2. When the merge conflicts, the store aborts the merge, keeps its commit, and
   reports the folders in conflict.
3. When the push is refused because the remote moved again during the merge,
   the store reports it and leaves the merge commit for the next run.

## Diagram

```
             baseline                              decision

stable    ┌────────────────────┐               ┌────────────────────┐
          │ upstream branch    │               │ upstream branch    │
          └─────────▲──────────┘               └──────┬──────▲──────┘
                    │ pushes                          │      │ pushes
                    │ (refused when moved)    fetches,│      │
                    │                          merges │      │
═════ the spec store's checkout is shared by every branch ═════════════════════
                    │                                 │      │
volatile  ┌─────────┴──────────┐               ┌──────▼──────┴──────┐
          │ store specs        │               │ store specs        │
          │ commit one folder  │               │ commit one folder  │
          └────────────────────┘               └────────────────────┘
          other branches' edits: untouched     other branches' edits: untouched
```

The decision adds one arrow, from the upstream branch into the checkout, and
nothing else. That arrow is the risk, since it writes into a checkout other
branches are using. A merge writes only the files that changed upstream and
refuses to start if any of them is edited locally, which is why it is safe here
and a rebase is not. The change this absorbs is a remote that moved, which the
baseline handed to a person every time.

## Considered

- **The baseline, push and stop.** It never writes into the shared checkout. We
  didn't choose this because the remote moves every time another machine
  stores, so stopping would be the normal case rather than the rare one.
- **Rebase onto the upstream.** It keeps the history linear. We didn't choose
  this because a rebase refuses to run while any tracked file is edited, and in
  a shared checkout another branch almost always has one.
- **Rebase with `--autostash`.** It gets past the refusal by stashing other
  branches' edits and putting them back afterwards. We didn't choose this
  because in pfms the stash stack is shared with every worktree and every
  session working in them, and a stash that fails to apply back leaves another
  branch's edits half restored.
- **`git push --force-with-lease`.** Andre asked whether this would pick up
  remote changes. It doesn't. It overwrites the remote when the remote still
  matches the local copy, and on this branch an overwrite can only delete
  another branch's specs.

## Consequences

The spec store's history gets merge commits. Nobody reads that history for its
shape, and each folder's own commits stay readable with
`git log -- <folder>`.

The store writes into a checkout other branches are using, which nothing in
wfctl did before. It writes only files that changed upstream, and those belong
to other folders or other machines.

## Verification

- The scratch test above, as a test in wfctl's suite: a modified tracked file
  and an untracked folder from other branches survive a store that merges and
  pushes.
- A store with GitHub unreachable reports "committed, not pushed", and the next
  store pushes both commits.
- A conflict in the branch's own folder aborts the merge, keeps the commit, and
  leaves other branches' edits as they were.

## Log

- 2026-10-14  proposed  — #359 level 3: Andre asked the store to pick up remote
  changes instead of stopping
