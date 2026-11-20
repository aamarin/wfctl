# Contract: the event log lines this feature writes

Both lines go in a branch's `events.jsonl` through `append_event`. `data-model.md` lists each field's type and meaning, and this file shows the exact shape a reader can rely on.

## `verify`, extended

```json
{"ts": "2026-11-20T15:04:12Z", "event": "verify", "exit": 1, "sha": "8ac5dcb",
 "failed": ["nosuchtool --check"], "inconclusive": false, "seconds": 131.4,
 "commands": [
   {"command": "uv run pytest -q", "exit": 0, "seconds": 118.2, "peak_bytes": 912261120},
   {"command": "nosuchtool --check", "exit": 127, "seconds": 0.0, "peak_bytes": null}
 ]}
```

Compatibility: every field the event carried before stays, with the same meaning. A reader written before this change ignores `seconds` and `commands`.

## `worktree-span`, new

```json
{"ts": "2026-11-22T10:15:03Z", "event": "worktree-span",
 "created": "2026-11-19T18:31:46Z", "removed": "2026-11-22T10:15:03Z"}
```

Written by `wfctl hook worktree-remove` when the hook lets the removal go ahead, on its success path or after an unexpected error, and the worktree's `commondir` file exists. The hook runs before workmux removes the worktree, so a span can describe a worktree whose removal later failed. Readers drop such a span as `wfctl-timings.md` describes. If reading the file or writing the line fails, the hook prints `⚠ couldn't record this worktree's lifetime (<reason>)` and exits as it would have without this feature.
