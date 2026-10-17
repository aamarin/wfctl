---
status: proposed
---

# Worktree removal runs one hook command, which stores the spec dir and then saves unsaved work

## Context

Removing a worktree now does two different jobs. The first is making sure the
branch's spec files are somewhere safe, which `wfctl store specs` does (#359).
The second is new: saving the other untracked files and the ignored folders a
repository lists, and refusing the removal when there are uncommitted edits or
commits that aren't pushed or merged. The two records that decide what is
saved and where are `worktree-removal-requires-saved-work` and
`removal-copy-destinations`. This record decides which command does the second
job, and which command the removal hook calls to run both.

Today one command, `archive-specs`, is the whole of what the removal hook
runs. If it took on the second job, its name would describe only half of what
it does. And it wouldn't archive anything in the old sense either, because the
numbered archive is no longer written.

The name of the command the hook runs is hard to change. Every repository's
`.workmux.yaml` names it, that file belongs to the repository once it is
seeded, and wfctl doesn't rewrite it afterwards. As a result, whatever the hook
calls has to keep its name while the jobs behind it change.

## Verified

- `.workmux.yaml:125` runs `wfctl archive-specs "$WM_WORKTREE_PATH"
  "$WM_HANDLE"` in `pre_remove`, and `wfctl/_workmux.py:60` names the same
  command in the block it seeds into new repositories.
- `wfctl/_workmux.py:257`, `wire_pre_remove`, only patches a `pre_remove: []`
  line. Its docstring says a `pre_remove` that already has entries is refused,
  and the caller prints manual instructions. So `install-config` can't move an
  existing repository's hook to a new command name.
- `wfctl/_workmux.py:229`, `pre_remove_wired`, decides whether the hook is
  wired by looking for `archive-specs` or `archive-story` in the live lines of
  `pre_remove`.
- `wfctl/cli.py:1416` registers `archive-specs` and keeps `archive-story` as a
  hidden alias. That alias was kept when the command was renamed, because an
  unknown name in the hook would make every removal in that repository fail.
- `wfctl/cli.py:6286` defines the `hook` group, which holds `user-prompt`,
  `worktree-guard`, and `session-restart`. Each is what a config file calls, so
  the config names a stable command and wfctl decides what it runs. The
  group's help text describes only agent hooks called from `settings.json`.
- The installer documents the seed-once rule in `install-modes`: a seeded file
  like `.workmux.yaml` belongs to the repository from the moment it is written,
  so a fix to the template reaches only repositories seeded afterwards.

## Assumed

- Nobody calls `archive-specs` from anywhere except the hook. If a script does,
  it now gets both jobs instead of one, and it would need to call
  `store specs` instead.
- #359's `store-specs-at-removal` lands with the same entry point. Both records
  describe `wfctl hook worktree-remove` and were revised together on
  2026-10-14.

## Direct baseline

Keep `archive-specs` as the single command and give it both jobs. The hook
doesn't change, every repository gets the new saving behavior as soon as wfctl
is updated, and no command is added.

## Decision

The removal hook calls one command, named for when it runs rather than what it
does:

```
wfctl hook worktree-remove  <worktree> <handle>
```

It runs two commands in order, and each of them stays visible because a person
also runs them by hand:

1. `wfctl store specs` makes sure the spec files are somewhere safe. In the
   default layout, with `specs/` inside the worktree, it copies them out to
   the main checkout, and it stops the removal when the destination already
   holds different files for the branch. You get past that stop by running
   `store specs --overwrite` by hand, or by merging the files yourself.
2. `wfctl archive unsaved` checks for uncommitted edits and for commits that
   aren't pushed or merged, and it stops the removal if it finds any. When the
   checks pass, it copies the other untracked files and the listed ignored
   folders to `unsaved/` in the state dir.

`archive unsaved` starts a new `archive` command group, which holds only that
command for now.

The hook command calls the store as a function and decides from its result,
not from the exit code of `store specs`. The store's result says whether the
outcome stops the removal. A failed push, a lock timeout, or a merge conflict
in a spec store doesn't stop it, because the commit or the files stay in the
spec store on disk, and deleting the worktree can't touch them. In those cases
the hook prints the store's output as a warning and goes ahead. The copy-out
outcomes in the default layout do stop it, such as a destination that holds
different files, because there the worktree holds the only copy. For the same
reason, any result for a spec dir inside the worktree that isn't a finished
copy-out stops the removal, so a store that skips that spec dir as not its
concern can't delete the only copy. `store specs`
run by hand still exits 1 for a copy-out refusal and for a spec-store failure,
so a script can tell the spec files aren't backed up yet. It exits 0 when it
reports a spec dir as not applicable, because in that layout no command could
make it pass. `archive unsaved` keeps its own refusals
as they are.

The template seeds `wfctl hook worktree-remove` into `pre_remove` as the one
call in its block. `archive-specs` becomes a hidden alias for it, so an
existing repository's hook runs both jobs when wfctl is updated, without
anyone editing it. Unlike the `archive-story` alias, it prints no warning,
because the only fix would be a hand edit that changes nothing about what
runs. `pre_remove_wired` accepts the new name as well as the old ones, and the
`hook` group's help text is widened to cover workmux hooks.

## Diagram

```
          baseline                               decision

repo-owned, seeded once
     ┌─────────────────────────┐          ┌─────────────────────────────┐
     │ .workmux.yaml           │          │ .workmux.yaml               │
     │  pre_remove:            │          │  pre_remove:                │
     │   wfctl archive-specs   │          │   wfctl hook worktree-remove│
     └─────────────────────────┘          │   (old repos: archive-specs,│
                │ calls                   │    its hidden alias)        │
                │                         └──────────────┬──────────────┘
                │                                        │ calls
════ seeded config / wfctl release ══════════════════════╪═════════════════
                │                                        │
wfctl, changes  ▼                                        ▼
every release                             ┌─────────────────────────────┐
     ┌─────────────────────────┐          │ hook worktree-remove        │
     │ archive-specs           │          └──────┬───────────────┬──────┘
     │  spec copy              │                 │ runs          │ runs
     │  + checks               │          ┌──────▼──────┐ ┌──────▼───────┐
     │  + untracked copy       │          │ store specs │ │ archive      │
     └─────────────────────────┘          │ (#359)      │ │  unsaved     │
                                          │ spec copy   │ │ (new) checks │
                                          └─────────────┘ │ (new) copy   │
                                                          └──────────────┘
```

The divider is the one `install-modes` already draws: a seeded file belongs
to the repository, and the commands it calls ship with wfctl.

Both graphs cross the divider with one arrow per repository, so both absorb
the change this feature makes, a new job at removal, without anyone editing a
seeded hook. The baseline does it by putting the new job inside a name that
describes the old one. The decision does it with a name that describes when
the command runs, so the name stays accurate whatever runs behind it. The
difference shows with the next job. #359's push of spec files at removal was
that next job, and in the decision it went into `store specs` without touching
the hook command at all. In the baseline it would also have gone inside
`archive-specs`, and the name would describe less every time.

## Considered

- One command with both jobs, the direct baseline. It needs no new names and
  no alias. We didn't choose it because the command would no longer do what
  its name says. It would save more than spec files and would no longer write
  an archive.
- Two lines in the seeded hook, one per job, with `archive-specs` as a hidden
  command that runs both. This was the first version of this record. It lets a
  repository drop a job by deleting a line. We didn't choose it because the
  next job added at removal would then need a hook edit in every repository
  seeded with two lines, which is the cost #359's record exists to avoid.
- A visible `wfctl archive worktree` that runs both. We didn't choose it
  because the entry point is called by a config file, not by a person, and the
  `hook` group is where wfctl already keeps those. A visible name in the
  `archive` group would also put a third command in front of a person for one
  removal.
- `wfctl archive specs` beside `archive unsaved`, for the spec copy-out. We
  didn't choose it because `store specs` already answers whether a branch's
  spec files are safe, and which half applies depends on the layout. Two
  commands would make the reader know the layout first, and both would run at
  every removal.
- `wfctl archive files`, `archive work`, or `archive uncommitted` for the
  second command. Andre chose `unsaved`, because it is the only one of the four
  that accurately describes untracked files, uncommitted edits, and unpushed
  commits alike. `files` overlaps with spec files, `work` is vague about what
  is saved, and `uncommitted` doesn't fit a commit that was made but never
  pushed.

## Consequences

The command names now match what each one does, and a later removal job is a
change inside `hook worktree-remove` that ships in a wfctl release, with no
hook edit in any repository. The cost is a hidden alias that will likely never
be retired, because nothing can move an existing repository's hook off it.

Because one process runs both jobs, it can run every check before any copy.
So a refusal from `archive unsaved` doesn't come after spec files were already
copied. A repository can no longer drop one job by deleting a hook line,
though. To skip a job, it would need a setting in `wfctl.json`, and none is
planned.

## Verification

- A test that the seeded template's `pre_remove` calls
  `wfctl hook worktree-remove`, and that `pre_remove_wired` reports it as
  wired.
- A test that `archive-specs` runs both jobs, and exits non-zero when
  `archive unsaved` refuses or the store's result says the removal stops.
- A test that a failed push at removal prints a warning and exits 0.
- A test that a spec dir inside the worktree, which the store reports as not
  applicable instead of copying it out, stops the removal.
- A test that `wfctl --help` doesn't list `archive-specs`, that
  `wfctl hook --help` lists `worktree-remove`, and that `wfctl archive --help`
  lists `unsaved`.
- The real removal test from the #40 handoff, run once through the old hook
  line and once through the new one.

## Log

- 2026-10-14  proposed  — #40 level 3. Andre asked for a separate command for
  each job instead of one command doing both, and chose the name `unsaved`.
- 2026-10-14  revised   — the spec copy-out moved into #359's `store specs`,
  and the hook calls `wfctl hook worktree-remove` with `archive-specs` as its
  hidden alias, instead of two seeded lines. Andre approved both, and #359
  revised its record to match.
