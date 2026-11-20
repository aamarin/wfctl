# Research: wfctl measures feature time and verify cost

Each entry answers one question the plan depended on. The two probes below ran on 2026-11-19 on macOS with git 2.44.0 and Python 3.13.

## R1. Which git commands rewrite a worktree's `commondir` file

**Decision**: Read the creation time from the modified time of `<git common dir>/worktrees/<name>/commondir`, as `worktree-span-read-from-git` decides. No change to the record is needed.

**Rationale**: A probe created a repository and a linked worktree, then ran each command below and checked the modified time of `commondir` and of its sibling `gitdir` after each one:

| Command | `commondir` | `gitdir` |
| --- | --- | --- |
| commit in the worktree | unchanged | unchanged |
| `git worktree lock`, then `unlock` | unchanged | unchanged |
| `git worktree repair`, from the main checkout and from the worktree | unchanged | unchanged |
| `git gc` | unchanged | unchanged |
| `git worktree prune` | unchanged | unchanged |
| `git worktree move` | unchanged | rewritten |
| checkout of a new branch in the worktree | unchanged | unchanged |
| a manual `mv`, then `git worktree repair <new path>` | unchanged | rewritten |

Git writes `commondir` once, in `git worktree add`, and every command that updates a worktree's location rewrites `gitdir` instead. That's why `gitdir` is the wrong file to read and `commondir` is the right one.

**Not verified**: git 2.48 added `git worktree repair --relative-paths` and the `worktree.useRelativePaths` setting. The probe machine runs git 2.44, which lacks both. If a later git rewrites `commondir` when converting to relative paths, the span starts at the conversion instead of the creation. The spec's edge cases already cover a later creation time, and the plan adds no guard for it.

**Alternatives considered**: `gitdir`'s modified time, which `git worktree move` and `repair` rewrite. The file's birth time, which Python can't read on Linux.

## R2. How each verify command is measured

**Decision**: `subprocess.Popen` plus `os.wait4(pid, 0)`, as `828-verify-measures-each-child` decides.

**Rationale**: That record's own probe covers macOS and Linux. It shows bytes on macOS and kilobytes on Linux, a grandchild's peak counted, and the largest single process reported rather than the sum.

**Implementation details the record leaves to the plan**:

1. A command that can't start records exit 127 when the executable is missing and 126 when it isn't executable. Those are the codes a POSIX shell uses for the same two failures, so the `exit` field stays an integer on every entry.
2. On `KeyboardInterrupt` during `os.wait4`, `run_verification` kills the child, reaps it with a second `os.wait4`, sets `Popen.returncode`, and re-raises. No event is written, as today.
3. Every successful `os.wait4` sets `Popen.returncode` from `os.waitstatus_to_exitcode(status)`, so the `Popen` object never tries to reap the child again.

**Alternatives considered**: listed in the record's Considered section.

## R3. How `wfctl timings` finds every branch's event log

**Decision**: Walk `project_state_dir(repo_root)` for every `events.jsonl` and name each branch by its path relative to that folder, skipping the `.issues` folder.

**Rationale**: A branch whose name holds a slash, such as `release/v0.30.0` or `chore/ponytail-audit-cuts`, gets a nested folder, so a one-level listing misses it. This repository's state folder holds 260 event logs, 9 of them nested. `.issues` holds review round tallies keyed by issue, and git refuses a branch name starting with a dot, so no branch can collide with it.

If `WFCTL_STATE_DIR` is set, every branch shares that one folder, so `wfctl timings` reads that single log and says so in its heading.

**Alternatives considered**: `iterdir()` one level deep, which misses the nested branches.

## R4. Whether reading every log meets SC-004

**Decision**: Read and parse every log on each run, with no cache.

**Rationale**: Reading this repository's 260 logs (9,689 events, 1.2 MB) and parsing every line took 0.11 seconds. SC-004 allows 2 seconds for 200 branches, so a cache would add stored state for no measurable gain, against `session-state-is-re-derived`.

## R5. Where the open-now line comes from

**Decision**: List `<git common dir>/worktrees/*/`. A worktree is open when its `gitdir` file names a path that exists, and its age is now minus its `commondir` modified time.

A relative `gitdir` path, which git 2.48's `--relative-paths` option can write, is resolved against the admin folder that holds the file, not against the current directory.

**Rationale**: This reads the same file the span reads, so an open worktree's age and its eventual span agree. It needs one `git rev-parse --git-common-dir` call rather than one call per worktree. An entry whose `gitdir` target is gone is the same one `git worktree list` marks `prunable`, and `worktree_branches` already drops those.

**Alternatives considered**: `git worktree list --porcelain`, which prints each worktree's path but not its admin folder, so the age would need a second lookup per worktree.

## R6. Which branches the no-span line leaves out

**Decision**: Leave out the branch `trunk_branch(repo_root)` names, and any branch with an open worktree.

**Rationale**: A trunk branch never has its worktree removed through the hook, and an open worktree's span isn't written yet. Every other branch with an event in the window and no span counts, including state folders that aren't real branches, such as `0-next-steps`. The line names both causes rather than guessing which applies.

## R8. Which branch an open worktree belongs to

**Decision**: Read the branch from the worktree's admin folder:

1. If `HEAD` holds `ref: refs/heads/<branch>`, that's the branch.
2. If `HEAD` holds a commit, the worktree is detached. If `rebase-merge/head-name` or `rebase-apply/head-name` exists, the branch is the one it names, since a rebase in progress detaches `HEAD` and records the branch there.
3. Otherwise the worktree has no branch. It still counts on the open-now line, and leaves no branch out of the no-span line.

**Rationale**: These are file reads in the same folder R5 already lists, so open-now needs no subprocess per worktree. `git worktree list --porcelain` prints `detached` and no branch for a worktree mid-rebase, so a branch being rebased would land on the no-span line while its worktree is open. Reading `head-name` keeps it off.

**Alternatives considered**: `worktree_branches`, which drops detached worktrees, including the mid-rebase case above.

## R9. A span for a worktree that's still there

**Decision**: `wfctl timings` drops a span whose `created` equals an open worktree's creation time, and keeps only the latest `removed` among spans with the same branch and `created`.

**Rationale**: workmux runs the hook as `pre_remove`, before it removes the worktree. If the removal fails afterward, or someone runs the hook by hand, the span describes a worktree that still exists. The next removal then writes a second span with the same `created`, and both would count in the median. The hook can't tell whether the removal later succeeded, so the reader fixes it at read time with what it already has. Two worktrees created in the same second with the same branch is the only case this merges wrongly, and that can't happen, since git refuses a second worktree on a branch that's already checked out.

**Alternatives considered**: A post-removal hook that writes the span after the fact. workmux has `pre_remove` and no hook after removal, so this would need a workmux change, which this feature avoids.

## R7. Where the new code lives

**Decision**:

1. The span writer goes in `wfctl/evidence/_events.py`, beside the other event writers.
2. The summary goes in a new `wfctl/evidence/_timings.py`.
3. The measurement change stays in `wfctl/_verify.py`, which the import baseline already places in evidence.
4. `cli.py` wires both through the `wfctl.evidence` package.

**Rationale**: The domain page puts the event log in evidence and derivation. `cli.py` may import any context's package, and evidence may import `core` (`_io`, `_paths`), so the change adds no baseline line and no arrow to the Context Map. That keeps it out of the five changes that wait for `approve-imports`.
