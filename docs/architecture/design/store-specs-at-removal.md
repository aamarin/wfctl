---
status: proposed
---

# Worktree removal stores the spec dir through the command its hook already runs

## Context

`spec-storage-read-from-git` says worktree removal runs the store command, as a
last pass for files written after the pipeline's last store. Review reports are
the usual case, because the review panel writes them after `/store-specs` has
already run. That record leaves open how removal reaches the store command.

Two repositories already run wfctl on removal, and both call the same command
from a `pre_remove` hook in `.workmux.yaml`. Any change that needs a new hook
line has to be made by hand in every repository that uses wfctl, because the
config installer can't rewrite a `pre_remove` block that already has entries.

The #40 branch is reshaping that same command at the same time. It adds
`wfctl archive unsaved`, which saves other files removal would destroy. It first
planned a second command, `wfctl archive specs`, to copy a spec dir out of a
worktree before the worktree is deleted. Andre asked why copying a spec dir out
and pushing a spec dir needed two commands, and both branches agreed they don't,
so the copy-out moved into `store specs`.

## Verified

- `.workmux.yaml` in this repository runs
  `wfctl archive-specs "$WM_WORKTREE_PATH" "$WM_HANDLE"` in `pre_remove`, with
  no `|| true`, so a non-zero exit stops the removal.
- pfms's `.workmux.yaml:239` runs the same command in `pre_remove`, also without
  `|| true`.
- `cli.py:1518-1529` prints `✓ spec dir is durable … nothing there was at risk,
  nothing copied` whenever the spec dir is outside the worktree, without asking
  git anything.
- pfms's spec store is a worktree of the pfms repository with `specs-trunk`
  checked out (`git rev-parse --git-common-dir` prints
  `/Users/andremarin/Development/pfms/.git`), and this repository's is a
  separate clone. The store command has to work for both.
- #40's commit `d695ba4` on its own branch says `archive-specs` stays as a
  hidden name "because install-config can't rewrite a pre_remove block that
  already has entries".

## Assumed

- Every repository that uses wfctl on removal calls `archive-specs` from its
  hook. A repository that wrote its own hook line calling something else gets no
  store at removal. `wfctl check specs` still lists its spec dirs as not stored,
  so this would show up rather than fail silently.
- #40 lands `wfctl hook worktree-remove`, with `archive-specs` as its hidden
  alias, and it runs both halves. If it doesn't, this branch keeps
  `archive-specs` running the store itself, and the decision below still holds.

## Direct baseline

Ship `wfctl store specs` as its own command and add a second line to each
repository's `pre_remove` hook that runs it before `archive-specs`. Removal
then runs two commands, the existing one unchanged and the new one beside it.
`archive-specs` keeps copying a spec dir out of the worktree, and `store specs`
only commits and pushes.

## Decision

The command the hook already runs reaches the store. The hook calls
`wfctl hook worktree-remove`, which runs `wfctl store specs` and then
`wfctl archive unsaved`. `archive-specs` becomes its hidden alias, so an existing
repository's hook keeps working without an edit. A new repository is seeded with
one `pre_remove` line:

```
wfctl hook worktree-remove "$WM_WORKTREE_PATH" "$WM_HANDLE"
```

It sits in the `hook` group beside `user-prompt`, `worktree-guard`, and
`session-restart`, which work the same way: the config names a stable command,
and wfctl decides what it runs. As a result, the next job added at removal needs
no hook edit in any repository, new or old. `store specs` and `archive unsaved`
stay visible commands, because a person also runs them by hand, for example
`store specs --overwrite` to get past a spec dir that holds different files.

`store specs` is the one command that answers whether a branch's spec dir is
somewhere safe, and the layout decides how it does that:

1. In a spec store with an upstream branch, it commits this branch's folder,
   merges the upstream, and pushes. This branch owns that half.
2. In the default layout, with the spec dir inside the worktree, it copies the
   spec dir out to the main checkout and says the copy is not backed up. #40
   owns that half, along with `--overwrite` and its guard against overwriting a
   copy that differs.
3. In a plain folder outside any repository, it does nothing and says where the
   files are and that nothing backs them up.

Removal stops only when it would delete something that could not be saved. A
failed copy-out stops it, since once the worktree is gone that copy is the only
one. A failed push prints a warning and lets the removal go ahead, since the
commit stays in the spec store on disk.

Whichever branch merges first creates `store specs` with the layout dispatch,
and the other merges `main` in.

## Diagram

```
             baseline                                 decision

stable    ┌────────────────────┐                  ┌────────────────────┐
          │ pre_remove hook    │                  │ pre_remove hook    │
          │ (each repo's own)  │                  │ (each repo's own)  │
          └──┬──────────────┬──┘                  └─────────┬──────────┘
   calls     │              │ calls (new line)              │ calls
═════ the repository owns its hook, wfctl owns what the command does ═══════════
             │              │                               │
volatile  ┌──▼──────────┐ ┌─▼────────────┐        ┌─────────▼──────────┐
          │archive-specs│ │ store specs  │ (new)  │hook worktree-remove│
          │ copy-out    │ │ commit, push │        │ archive-specs is   │
          └─────────────┘ └──────────────┘        │ its hidden alias   │
                                                  └──┬──────────────┬──┘
                                                     │ calls        │ calls
                                              ┌──────▼───────┐ ┌────▼──────────┐
                                              │ store specs  │ │archive unsaved│
                                              │ copy-out or  │ │ (#40)         │
                                              │ commit, push │ └───────────────┘
                                              └──────────────┘ (new)
```

The baseline crosses the boundary between a repository's hook and wfctl with two
arrows, and the second one is new in every repository. The decision crosses it
with the one arrow that already exists, and everything new sits on wfctl's side.
The change this is built to absorb is the next thing removal has to do. In the
baseline that is one more hook line per repository, and in the decision it is a
change to one command that ships in a wfctl release.

## Considered

- **The baseline, a new hook line.** It keeps each command doing one thing, and
  the hook reads plainly. We didn't choose this because every repository has to
  edit its hook by hand, and one that doesn't gets no store at removal and still
  prints the old "durable" message.
- **Keep `archive specs` and `store specs` as two commands.** Each would have a
  short, single job. We didn't choose this because both answer whether this
  branch's spec dir is somewhere safe, and which one applies depends on a layout
  the reader has to know first. They would also both run at every removal.

## Consequences

Removal no longer prints "durable" in any layout. It says the spec dir was
stored, that it was copied and is not backed up, or where the files are.

The push at removal runs from the hook in the user's own shell, outside the
agent's permission layer, which is the only thing that gates outward actions.
Andre approved pushing at removal knowing that, and the push only sends commits
to the spec store's own branch.

The two branches share one command, so whichever merges second inherits the
other's half and has to merge `main` in rather than rebase.

## Verification

- In this repository, with a review report written after the last store,
  `wm remove` commits and pushes it and the commit shows on
  `origin/specs-trunk`.
- With the network off, the same removal warns that the push failed and the
  worktree is removed. `wfctl check specs` then lists the folder as not pushed.
- In the default layout, a failed copy-out stops the removal.
- Neither repository's `.workmux.yaml` changes.

## Log

- 2026-10-14  proposed  — #359 level 3: how removal reaches the store, agreed
  with Andre and with the #40 session
- 2026-10-14  revised  — the hook calls `wfctl hook worktree-remove`, with
  `archive-specs` as its hidden alias, and `wfctl archive specs` is dropped;
  approved by Andre in the #40 session
