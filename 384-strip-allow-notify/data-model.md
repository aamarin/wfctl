# Data Model: Strip allow-notify

This change adds no storage. What it touches is the branch's event log,
`$(wfctl state-dir)/events.jsonl`, with one JSON object per line.

## Events still written

| Event | Written by | Fields | Meaning |
| --- | --- | --- | --- |
| `notify-action` | `wfctl report-action`, and `wfctl issue <verb>` on success | `ts`, `action` | This run took `action`. Lifts a standing hold on the same action. |
| `blocked` | `wfctl report-block` | `ts`, `branch`, `action`, `reason`, `step` (nullable) | The host refused `action`. Holds `step` until a later `notify-action` for the same action. |

## Events no longer written, still tolerated in old logs

| Event | Still read by | Effect |
| --- | --- | --- |
| `block-cleared` | `standing_blocks` | Lifts a hold, as before. |
| `notify-declined` | nothing (dropped from `_restart._LATE_EVENTS`) | none |
| `notify-resolved`, `notify-grant`, `notify-refused` | nothing | none. `wfctl log` prints them. |

## Action names

| Written by | Name |
| --- | --- |
| `wfctl issue comment / create / label / close` | `issue-comment`, `issue-create`, `issue-label`, `issue-close` |
| `wfctl issue start / stop / list / view / labels / fields` | not recorded |
| `report-action` / `report-block` | whatever the caller passes. The skills pass `push` or `issue-<verb>`. |

## Hold lifecycle, per action

```
 no hold ──report-block A──► held(step) ──notify-action A──► no hold
                                │           (report-action A, or a
                                │            successful wfctl issue verb)
                                └──block-cleared A (old logs only)──► no hold
```

For each action, the most recent of these events decides, scoped to the
branch the way `standing_blocks` already scopes it.

## Removed from `PipelineReport` and the status payload

- `notify: bool`
- `notify_source: str`
- `facts[3]` ("outward actions authorized")
