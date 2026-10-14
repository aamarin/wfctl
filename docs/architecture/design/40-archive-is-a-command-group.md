---
status: proposed
---

# Saving a worktree before removal is split into `wfctl archive specs` and `wfctl archive unsaved`

## Context

Removing a worktree now does two different jobs. The first is saving spec
files, which now go to the branch's spec dir instead of a numbered archive in
the state dir. The second is new: saving the other untracked files and the
ignored folders a repository lists, and refusing the removal when there are
uncommitted edits or commits that aren't pushed or merged. The two records
that decide what is saved and where are
`worktree-removal-requires-saved-work` and `removal-copy-destinations`. This
record decides which commands do those jobs and what they are called.

Today one command, `archive-specs`, is the whole of what the removal hook
runs. If it took on the second job, its name would describe only half of what
it does. And it wouldn't archive anything in the old sense either, because the
numbered archive is no longer written.

The name of the command the hook runs is hard to change. Every repository's
`.workmux.yaml` names it, that file belongs to the repository once it is
seeded, and wfctl doesn't rewrite it afterwards.

## Verified

- `.workmux.yaml:125` runs `wfctl archive-specs "$WM_WORKTREE_PATH"
  "$WM_HANDLE"` in `pre_remove`, and `wfctl/_workmux.py:76` seeds the same line
  into new repositories.
- `wfctl/_workmux.py:257`, `wire_pre_remove`, only patches a `pre_remove: []`
  line. Its docstring says a `pre_remove` that already has entries is refused,
  and the caller prints manual instructions. So `install-config` can't move an
  existing repository's hook to a new command name.
- `wfctl/_workmux.py:229`, `pre_remove_wired`, decides whether the hook is
  wired by looking for `archive-specs` or `archive-story` in the live lines of
  `pre_remove`.
- `wfctl/cli.py:1416-1417` registers `archive-specs` and keeps `archive-story`
  as a hidden alias. That alias was kept when the command was renamed, because
  an unknown name in the hook would make every removal in that repository fail.
- `wfctl/cli.py` already groups commands with `add_typer`: `arch`, `step`,
  `check`, `contract`, and `hook`. No `archive` group exists yet.
- The installer documents the seed-once rule in `install-modes`: a seeded file
  like `.workmux.yaml` belongs to the repository from the moment it is written,
  so a fix to the template reaches only repositories seeded afterwards.

## Assumed

- workmux runs the `pre_remove` entries in order and stops at the first one
  that exits non-zero. If it runs all of them regardless, a refusal from
  `archive unsaved` still stops the removal, but the order guarantee below
  weakens.
- Nobody calls `archive-specs` from anywhere except the hook. If a script does,
  it now gets both jobs instead of one. It would need to be changed to
  `archive specs`.

## Direct baseline

Keep `archive-specs` as the single command and give it both jobs. The hook
doesn't change, every repository gets the new saving behavior as soon as wfctl
is updated, and no command is added.

## Decision

A new `archive` command group holds one command per job:

```
wfctl archive specs    <worktree> <handle>
wfctl archive unsaved  <worktree> <handle>
```

`archive specs` copies spec files that live inside the worktree to the
branch's spec dir. It stops the removal when that spec dir already holds
different files for the branch. `archive unsaved` checks for uncommitted
edits and for commits that aren't pushed or merged, and it stops the removal
if it finds any. When the checks pass, it copies the other untracked files and
the listed ignored folders to `unsaved/` in the state dir.

The template seeds both commands into `pre_remove`, `specs` first, as one
block with two lines. `archive-specs` stays as a hidden command that runs
`specs` and then `unsaved`, which is what the template's two lines do. As a
result, existing repositories get both jobs when wfctl is updated, without
editing their hook. Unlike the `archive-story` alias, it prints no warning,
because the only fix would be a hand edit that changes nothing about what
runs. `pre_remove_wired` accepts the new names as well as the old ones.

## Diagram

```
          baseline                               decision

repo-owned, seeded once
     ┌─────────────────────────┐          ┌────────────────────────────┐
     │ .workmux.yaml           │          │ .workmux.yaml (new repos)  │
     │  pre_remove:            │          │  pre_remove:               │
     │   wfctl archive-specs   │          │   wfctl archive specs      │
     └─────────────────────────┘          │   wfctl archive unsaved    │
                │ calls                   └────────────────────────────┘
                │                             │ calls        │ calls
════ seeded config / wfctl release ═══════════╪══════════════╪═════════════
                │                             │              │
wfctl, changes  ▼                             ▼              ▼
every release                          ┌────────────┐ ┌──────────────┐
     ┌─────────────────────────┐       │ archive    │ │ archive      │
     │ archive-specs           │       │  specs     │ │  unsaved     │
     │  spec copy              │       │ spec copy  │ │ (new) checks │
     │  + checks               │       └────────────┘ │ (new) copy   │
     │  + untracked copy       │              ▲       └──────────────┘
     └─────────────────────────┘              │ runs       ▲
                                              │            │ runs
                                       ┌──────┴────────────┴──┐
                                       │ archive-specs        │
                                       │  (hidden, old hooks) │
                                       └──────────────────────┘
```

The divider is the one `install-modes` already draws: a seeded file belongs
to the repository, and the commands it calls ship with wfctl.

The two graphs differ by one command name more on the wfctl side, plus a
hidden name that runs both commands. Both graphs absorb the change this
feature makes, a new job at removal, without anyone editing a seeded hook.
The baseline does it by putting the new job inside a name that describes the
old one. The decision does it with the hidden name. The difference is what
happens with the next job, such as pushing spec files to `specs-trunk` at
removal, which #359 is weighing. In the baseline, that job also goes inside
`archive-specs`, and the name describes less every time. In the decision,
it becomes a third command in the group, and only the hidden name has to
learn about it.

## Considered

- One command with both jobs, the direct baseline. It needs no new names and
  no alias. We didn't choose it because the command would no longer do what
  its name says. It would save more than spec files and would no longer write
  an archive.
- A third visible command, such as `wfctl archive worktree`, that runs both,
  with the hook calling only that. That keeps the hook at one line and runs
  every check before any copy in one process. We didn't choose it because the
  hidden `archive-specs` already is that entry point for existing repositories.
  A visible third name would give a person three commands to choose between
  for one removal, and a repository could no longer drop one of the two jobs
  by deleting a line.
- `wfctl archive files`, `archive work`, or `archive uncommitted` for the
  second command. Andre chose `unsaved`, because it is the only one of the four
  that accurately describes untracked files, uncommitted edits, and unpushed
  commits alike. `files` overlaps with spec files, `work` is vague about what
  is saved, and `uncommitted` doesn't fit a commit that was made but never
  pushed.

## Consequences

The command names now match what each one does, and a later removal job has
an obvious place to go. The cost is a hidden command that will likely never
be retired, because nothing can move an existing repository's hook off it.

The two-line hook doesn't run every check before any copy. `archive specs`
runs first, so a refusal from `archive unsaved` can come after spec files were
already copied. That is harmless: the copies are identical on the next
attempt, and an identical file never stops a removal. The hidden command
runs both in one process, so it can check everything first. That gap only
exists in repositories seeded after this change.

## Verification

- A test that the seeded template's `pre_remove` calls `archive specs` and
  then `archive unsaved`, and that `pre_remove_wired` reports it as wired.
- A test that `archive-specs` runs both jobs and exits non-zero when either
  one refuses.
- A test that `wfctl --help` doesn't list `archive-specs`, and that
  `wfctl archive --help` lists `specs` and `unsaved`.
- The real removal test from the #40 handoff, run once through the old hook
  line and once through the new one.

## Log

- 2026-10-14  proposed  — #40 level 3. Andre asked for a separate command for
  each job instead of one command doing both, and chose the name `unsaved`.
