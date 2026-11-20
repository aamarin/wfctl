# Contract: `wfctl timings`

`wfctl timings` prints how long features keep a worktree open and how long and how much memory each verify command takes, across every branch of the project. It reads the event logs and git's worktree folder, and writes nothing.

## Usage

```
wfctl timings [--since <N>d | --since all]
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--since` | `30d` | How far back to count events. `<N>d` is a whole number of days, 1 or more. `all` counts every event. A window reaching back before year 1 also counts every event, and the heading still names the days given |

It runs from any checkout of the project, the main one or a linked worktree, since both resolve the same project state folder.

## Output

Plain text on stdout, with no `--json` (FR-022). The heading names the window and the branch count:

```
wfctl timings — last 30 days, 41 branches

Feature time, worktree created to removed
  spans     23 across 21 branches · median 1d 4h · max 6d 2h
  open now  5 worktrees · oldest 3d 1h
  no span   14 branches: removed before this shipped, or removed by hand

Verify, 18 of 52 runs carry timings
  command                          runs  median  max     largest process, median / max
  uv run pytest -q                   18  2m 01s  3m 40s  870 MB / 1.4 GB
  uv run ruff check wfctl/ tests/    18      2s      4s   46 MB / 51 MB
  uv run mypy                        18     11s     29s  384 MB / 610 MB
  whole run                          18  2m 14s  4m 05s
```

With `--since all`, the heading reads `wfctl timings — all events, 41 branches`. If `WFCTL_STATE_DIR` is set, the heading adds `· one state folder for every branch (WFCTL_STATE_DIR)`, since that log mixes every branch.

The other cases:

| Case | Output |
| --- | --- |
| No spans in the window | `spans     none in the last 30 days` |
| No open worktree | `open now  none` |
| No branch without a span | the no-span line is left out |
| Verify runs, none with timings | `Verify, 0 of 12 runs carry timings` and no table |
| No verify runs in the window | `Verify, no runs in the last 30 days` |
| A command whose every run has a null peak | `—` in the memory column |
| No event logs at all | `Nothing to summarize — no event logs under <path>.` |

## Exit codes

| Code | When |
| --- | --- |
| 0 | The summary printed, including the nothing-to-summarize case |
| 1 | `--since` isn't `all` or `<N>d`. It prints `✗ --since takes a number of days, such as 90d, or all` and no summary |
| 1 | Not inside a git repository, as every repo-scoped command does today |

## Reading rules

1. A line that isn't a JSON object is skipped, as `read_events` does.
2. A `verify` event without `seconds` counts toward M and nowhere else.
3. Failed and inconclusive runs count in every verify figure.
4. A span whose `removed` is before its `created`, or whose times won't parse, is left out of the medians, and its branch counts on the no-span line.
5. A span whose `created` equals an open worktree's creation time is dropped, and of several spans with the same branch and `created`, only the latest `removed` counts.
6. A field with the wrong type is treated as absent: a `verify` event whose `seconds` isn't a number counts toward M only, and a command entry whose `seconds` or `peak_bytes` isn't a number is left out of that figure. A number that is infinite, not a number, or too large to convert counts as absent too. No event line makes the command raise.
7. No figure names a branch (FR-019).
8. The no-span line leaves out the branch checked out in the main checkout, read from `HEAD` in the git common dir, the same way it leaves out a branch open in a linked worktree. The main checkout isn't a worktree git created, so it adds nothing to the open-now count or age.
9. The walk doesn't enter the `unsaved/` and `unsaved.staging/` folders beside a branch's log, since a removal copies a worktree's untracked files there, or an earlier save that a later removal moved aside as `unsaved-<UTC stamp>/`. An `unsaved/` or `unsaved.staging/` folder that holds its own `events.jsonl` is a branch's folder and is walked like any other, because once branch `a` is deleted, git allows a branch named `a/unsaved`, and later `a/unsaved/b`. A removal keeps each file's path in the worktree, so saved work puts a log at that spot only if the worktree had an untracked `events.jsonl` at its top level. In that case, any log in the saved files counts as a branch under `<branch>/unsaved`, and its events count in every figure. One case is still missed: if `a` logged events and `a/unsaved` was never a branch, the walk skips `a/unsaved/` as saved work and never reaches `a/unsaved/b`. Fixing that needs the removal to mark the folders it writes, as described in #834.
