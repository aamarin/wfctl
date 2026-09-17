# Data model: Session restart that writes its handoff first

Two new event kinds in the branch's `events.jsonl`, one existing kind read, one
pure decision over them, and a change to how a managed hook row is identified.

## Events

All events are single JSON lines appended by `_io.append_event`, which adds `ts`
(UTC, second precision) and `event`. Readers skip malformed lines and lines whose
fields have the wrong type. **Order is line position** (research R7).

### `session-restart` — written by the hook

| Field | Type | Meaning |
|---|---|---|
| `session` | str | Stop payload `session_id` the decision was about |
| `decision` | str | one of `end`, `clear`, `hold`, `skip`, `not-taken` |
| `occupancy` | int | tokens read from the transcript at this Stop |
| `threshold` | int | threshold in force at this Stop |
| `handle` | str \| null | workmux handle, on `end` and `clear` |

Written for every decision except *nothing*. `hold`, `skip` and `not-taken` are
the record that the message was shown, which is what makes each one once-only.

### `session-restart-send` — written by the worker

| Field | Type | Meaning |
|---|---|---|
| `session` | str | the session the send was for |
| `text` | str | exactly what was typed: `/end-session restart`, `/clear`, `/start-session` |
| `exit` | int | `workmux send` exit status; `-1` for a timeout or an `OSError` |

One line per text, in send order.

### `end` — existing, written by `wfctl end`

Read for its position only. `continued` is not consulted (clarification Q1).

## Decision

`_restart.decide(inputs) -> Decision`, pure.

**Inputs**

| Field | Source |
|---|---|
| `session` | payload `session_id` |
| `occupancy` | R1; `None` when unreadable |
| `threshold` | R11 |
| `events` | parsed `events.jsonl`, in order |
| `find_handle` | zero-arg callable → handle or `None` (R5); called only on a send path |

**Derived per session S, from `events`**

| Name | Definition |
|---|---|
| `planned_end` | a `session-restart` with `session=S`, `decision=end` |
| `sent_end` | the `session-restart-send` with `session=S`, `text=/end-session restart` |
| `landed` | an `end` event at a position after `sent_end` |
| `planned_clear` | a `session-restart` with `session=S`, `decision=clear` |
| `sent_clear` | the `session-restart-send` with `session=S`, `text=/clear` |
| `reported(d)` | a `session-restart` with `session=S`, `decision=d`, after the latest `planned_*` |

**Rules, first match wins**

```
threshold == 0                                    → nothing
occupancy is None or occupancy < threshold        → nothing
planned_clear
  ├─ no sent_clear                                → nothing        (FR-010a)
  ├─ reported(not-taken)                          → nothing
  └─ else                                         → not-taken, carrying sent_clear.exit
planned_end
  ├─ no sent_end                                  → nothing        (FR-010a)
  ├─ sent_end.exit != 0
  │    ├─ reported(not-taken)                     → nothing
  │    └─ else                                    → not-taken, carrying the exit
  ├─ landed
  │    ├─ find_handle() → h                       → clear to h
  │    ├─ reported(skip)                          → nothing
  │    └─ else                                    → skip
  ├─ reported(hold)                               → nothing
  └─ else                                         → hold
find_handle() → h                                 → end to h
reported(skip)                                    → nothing
else                                              → skip
```

The occupancy check sits second, above the restart branches, so a Stop under the
threshold reads no events (R3). A restart in progress is always over the threshold:
neither `/end-session` nor a `/clear` that did not take shrinks the window, and a
`/clear` that did take starts a session with no events.

**Decision → effect**

| Decision | Event written | Stdout | Worker texts |
|---|---|---|---|
| nothing | — | — | — |
| end | `session-restart` | — | `/end-session restart` |
| clear | `session-restart` | — | `/clear`, `/start-session` |
| hold | `session-restart` | hold message | — |
| skip | `session-restart` | skip message | — |
| not-taken | `session-restart` | sent-and-still-here, or never-sent when exit ≠ 0 | — |

## Managed hook row

| Field | Meaning |
|---|---|
| event | Claude Code event name (`Stop`, …) |
| subcommand | first word after `wfctl hook ` in the row's `command` |
| command | the full string installed |

Identity is `(event, subcommand)`. Shipped set for Claude after this change:

| Event | Subcommand | Command |
|---|---|---|
| `UserPromptSubmit` | `user-prompt` | `wfctl hook user-prompt` |
| `Stop` | `response-shape` | `wfctl hook response-shape 2>/dev/null \|\| true` |
| `Stop` | `session-restart` | `wfctl hook session-restart 2>/dev/null \|\| true` |
| `PreToolUse` | `worktree-guard` | `wfctl hook worktree-guard` (matcher `Bash`) |

Manifest `merged` records keep their shape `{path, event, command, created}`; the
subcommand is read from `command`.
