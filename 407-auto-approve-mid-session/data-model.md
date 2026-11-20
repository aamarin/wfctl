# Data Model: Auto-approve has its own command

No new files. One event gains a field, and one read-time value is added.

## `mode.json` (unchanged)

In the branch's state dir. One writer per direction: the grant helper writes
either value, and the review cap writes only `false`.

```json
{"auto_approve": true}
{"auto_approve": false, "revoked": "<reason>"}
```

Absent, malformed, or unreadable reads as off.

## `mode` event (gains `session`)

One line in `events.jsonl` each time a person changes the mode or the review
cap revokes it. A person's `on` while the mode is already on writes no line
(research.md §3a).

| Field | Written by | Meaning |
| --- | --- | --- |
| `event` | both | `"mode"` |
| `ts` | both | UTC time, written by `append_event` |
| `auto_approve` | both | the value granted |
| `session` | a person's change, when the caller has an identity | the identity of the session that made the change, verbatim |
| `by` | review cap only | `"wfctl"` |
| `reason` | review cap only | why the cap turned the mode off |

Two names are used for these events, and they don't overlap:

1. A grant is a `mode` event with `auto_approve: true` and no `by` field. Only a
   grant restarts the review count (FR-014). A grant is written when the mode
   was off, or when `mode.json` reads on and the newest `mode` event is not a
   grant, as after a hand edit (research.md §3a).
2. A mode change is any `mode` event with no `by` field, so it is either a
   grant or a person turning the mode off.

The grant helper appends the event before it writes `mode.json`. A failed
append then leaves the mode as it was. A failed file write after the append
leaves an event that `mode.json` doesn't match. The bare command reports
"turned off outside wfctl" after a failed `on` and "no grant on record" after
a failed `off`, and the next `on` or `off` repairs either (research.md §3a).

Events written before this change have no `session` field and read as from an
unknown session.

## `ModeChange` (read-time, never stored)

Returned by `last_change(agent_dir)` in `evidence/_mode.py`: the most recent
mode change, whichever value it set, or None when there is none.

| Field | Type | From |
| --- | --- | --- |
| `on` | `bool` | the event's `auto_approve` |
| `ts` | `str` | the event's `ts` |
| `session` | `str \| None` | the event's `session`, or None |

The CLI turns `session` into the relation shown to the reader by comparing it
with the caller's identity (research.md §4). The relation is never stored.

`newest_is_grant(agent_dir)` beside it says whether the newest `mode` event of
any kind, the cap's revocation included, is a grant. The skip in research.md
§3a and the bare command's second line both read it, so they agree on when a
grant stands behind the mode.

## Grant line (in the repository's `.workmux.yaml`)

`install.GRANT_LINE` holds the shipped form, which the note prints.
`install.post_create_grants(text)` reports whether a live line under
`post_create:` contains `auto-approve on`.
