# Data model: wfctl measures feature time and verify cost

Every record here is one JSON line in a branch's event log, `<state dir>/events.jsonl`. `append_event` adds `ts` and `event` to each one. Nothing new is written to the repository, the spec folder, or `verify.json`.

## Verify event (extended)

The fields from `exit` to `inconclusive` are unchanged. `seconds` and `commands` are new.

| Field | Type | Meaning |
| --- | --- | --- |
| `ts` | string, UTC to the second | When the run finished |
| `event` | `"verify"` | |
| `exit` | int | 0 when every command passed, else 1 |
| `sha` | string | HEAD before the run |
| `failed` | list of strings | Each failed command, joined with spaces |
| `inconclusive` | bool | Whether the tree changed during the run |
| `seconds` | float, one decimal | The whole run, from the first identity read to the last |
| `commands` | list of command entries | One per command in the `verify` list, in order |

Each command entry:

| Field | Type | Meaning |
| --- | --- | --- |
| `command` | string | The argv joined with spaces, the same form `failed` uses |
| `exit` | int | The command's exit code. 127 when the executable is missing, 126 when it isn't executable |
| `seconds` | float, one decimal | From `Popen` to the end of `os.wait4` |
| `peak_bytes` | int or null | `ru_maxrss` from `os.wait4`, converted to bytes. Null when the command never started |

Validation:

1. `peak_bytes` is `ru_maxrss × 1024` on Linux and `ru_maxrss` on macOS, picked by `sys.platform == "darwin"`.
2. An interrupted run writes no event, as today.

An event without `seconds` predates this change. `wfctl timings` counts it in "N of M runs carry timings" and leaves it out of every median and maximum.

## Worktree span event (new)

| Field | Type | Meaning |
| --- | --- | --- |
| `ts` | string | When the hook wrote the event |
| `event` | `"worktree-span"` | |
| `created` | string, UTC to the second | The worktree's `commondir` modified time |
| `removed` | string, UTC to the second | When the hook let the removal go ahead, the same moment as `ts` |

Validation:

1. The removal hook writes it once on each path that lets the removal go ahead: after `_save_unsaved` on the success path, and in the catch-all after an unexpected error. It never writes one on a refusal.
2. It writes nothing when the worktree has no `commondir` file, such as when the hook runs in the main checkout.
3. A reader leaves out any span whose `removed` is before its `created`, or whose times won't parse, and counts that branch on the no-span line.
4. A reader drops a span whose `created` equals an open worktree's creation time, and keeps only the latest `removed` among spans with the same branch and `created` (research R9).

## Timings summary (computed, never stored)

`wfctl timings` builds this on every run and prints it. Nothing below is saved.

| Part | Computed from |
| --- | --- |
| Window | `--since`: 30 days by default, `<N>d`, or `all` |
| Branch count | Event logs with at least one event in the window |
| Spans | `worktree-span` events whose `removed` falls in the window: their count, the count of branches they came from, and the median and maximum of `removed − created` |
| Open now | Entries under `<git common dir>/worktrees/` whose `gitdir` target exists: their count, and the oldest one's age from its `commondir`. Always current, whatever the window |
| Open worktree's branch | From the admin folder's `HEAD`, or its `rebase-merge/head-name` or `rebase-apply/head-name` when detached mid-rebase. None otherwise (research R8) |
| No span | Branches with an event in the window, no span in the window, no open worktree, and not the trunk |
| Verify runs | `verify` events whose `ts` falls in the window. M counts all of them, and N counts those carrying `seconds` |
| Per command | For each distinct `command` text across the N runs: the run count, and the median and maximum of `seconds` and of `peak_bytes`, leaving out nulls |
| Whole run | The median and maximum of each run's `seconds` |

Formatting:

1. A duration of a day or more prints days and hours (`1d 4h`). Under a day, hours and minutes (`3h 12m`). Under an hour, minutes and zero-padded seconds (`2m 01s`). Under a minute, seconds (`11s`).
2. Memory prints in 1024-based units labeled MB and GB (`870 MB`, `1.4 GB`), since `ru_maxrss` counts binary sizes.
3. The command column is ordered by first appearance in the window, oldest first, so the table reads in `verify` list order.
