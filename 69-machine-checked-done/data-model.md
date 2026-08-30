# Phase 1 Data Model: Machine-checked done

Two entities, one owned by the repository and one by the checkout. Neither
references the other by identifier; the record carries a copy of the command list
so it can be compared without re-reading the config it was produced from.

## Definition of Done

The repository's answer to "what proves this work is finished."

**Home**: `wfctl.json` at the repository root. Tracked by version control.
**Owner**: a human, at configuration time. wfctl never writes or infers it.
**Lifetime**: as long as the repository. Survives clones, worktrees, and teardown.

| Field | Type | Rules |
| --- | --- | --- |
| `verify` | list of argv lists | Optional. Each element is a non-empty list of strings. An absent key, or an empty list, means no verification is configured. |

**Validation**

- The file must parse as a JSON object. A parse failure is an error, never
  "absent" (FR-012).
- `verify`, when present, must be a list. Each element must be a non-empty list
  of strings — a bare string is rejected rather than split, because splitting is
  how a shell injection gets in.
- Unknown top-level keys are ignored, so the file can carry future settings
  without this feature rejecting them.

**Relationship to the tracker config**: same argv-token shape as
`.agents/trackers/<name>.json`, deliberately. Unlike that file, this one takes no
placeholders — there is nothing to substitute — and unlike that file, it is
tracked.

## Verification Record

The outcome of one completed verification run, and the identity of the code it
describes.

**Home**: `verify.json` in the branch's state directory, beside `current.json`
and `events.jsonl`. Never tracked.
**Owner**: wfctl. Written only by `wfctl verify`, only after every
configured command has finished (FR-017).
**Lifetime**: per branch, per checkout. A fresh clone has none, which reads as
never verified — true for that checkout.

| Field | Type | Rules |
| --- | --- | --- |
| `command` | list of argv lists | The definition of done as it stood when the run started. Compared for exact equality against the current config. |
| `exit` | integer | 0 only when every command ran and exited 0. A command that could not be executed makes this non-zero. |
| `failed` | list of argv lists, or empty | Every command that did not complete successfully — exited non-zero, or could not be executed at all (FR-023). Empty when `exit` is 0. |
| `sha` | string | Commit at capture. |
| `dirty` | boolean | Whether the working tree had uncommitted changes, untracked files included. |
| `inconclusive` | boolean | True when identity differed between the capture before the run and the capture after it. Identity is `(sha, dirty)` and `dirty` is a boolean, so a change made to an already-dirty tree does not flip it — sound, because a dirty record never reports complete. |
| `at` | string | UTC timestamp, `%Y-%m-%dT%H:%M:%SZ`, matching `append_event`. |

**Validation**

- A record that fails to parse, or lacks any field above, is treated as absent —
  never verified. There is no migration path and none is needed: re-running the
  command regenerates it.
- `sha` and `dirty` hold the values from the capture *before* the run. The second
  capture is not stored; its only product is `inconclusive`.

### State transitions

The record has no lifecycle of its own — it is replaced whole or not at all. What
has states is the implement step's reading of it.

```
tasks.md absent ──────────────────────────────────────────► ○

no `verify` configured ──► existing behavior, unchanged ───► ● or ▶

`verify` configured
  ├ no record ─────────────────────────────────────────────► ▶ unverified
  ├ inconclusive ──────────────────────────────────────────► ▶ re-run
  ├ exit ≠ 0 ──────────────────────────────────────────────► ▶ failed
  ├ command ≠ configured ──────────────────────────────────► ▶ definition changed
  ├ sha ≠ HEAD ────────────────────────────────────────────► ▶ commit moved
  ├ dirty, or tree dirty now ──────────────────────────────► ▶ tree dirty
  └ all match, tasks complete ─────────────────────────────► ●
```

Order matters where two conditions hold at once: the first matching branch wins,
so a failed run on a moved commit reports failed rather than stale. The failure a
user can act on is named ahead of the staleness that would only be reached after
fixing it.

## Session event

Not an entity — an append to the existing `events.jsonl` (FR-022). One line per
completed run, carrying `event: "verify"`, the verdict, the commit, and the
failing commands. Written through the existing `append_event`, so nothing new
owns the log's format.
