# Phase 1 data model: notify authority (#280)

Two persisted shapes and one derived value. Nothing here is a database; the
"model" is two files in the XDG state dir and one line appended to a log.

## Persisted: `notify.json`

Beside `mode.json` in the per-branch state dir (`wfctl state-dir`). One writer,
one reader — the shape `mode.json` documents about itself and `verify.json`
established.

```json
{ "state": "granted", "source": "local", "at": "2026-09-08T14:02:11Z" }
```

| Field | Values | Notes |
|---|---|---|
| `state` | `granted` \| `denied` | Tri-state reaches storage as *file absent* = unset. `denied` is not the absence of `granted` |
| `source` | `local` | Only the local command writes this file. The label is read live, never cached here |
| `at` | ISO-8601 UTC | When it was written. Not the authority for "when was it granted" — the event log is |

**Absent file is the default and means unset**, which resolves to refused
without meaning anyone said no. That distinction is the whole reason this is not
a boolean: `denied` beats a label, `unset` does not.

**Unreadable reads as refused** — absent, malformed, invalid UTF-8, or a JSON
scalar where an object was expected. `auto_approve()` already guards exactly
these three shapes and its docstring says why; this reader copies it rather than
inventing a fourth posture.

## Read live, never persisted: the label

`authority:notify` on the branch's issue, read through the tracker's existing
`view` verb at run start. Present or absent — the label has no deny form, by
decision in `clarify`; removing it returns the issue to silent.

Not cached in `notify.json` on purpose. Caching it would make the file's
`source` field lie the moment someone removed the label, and re-deriving beats
carrying a conclusion forward (`session-state-is-re-derived`).

## Derived at run start: the resolved grant

```
                 label absent        label present
local unset      refused / unset     granted / label
local granted    granted / local     granted / local
local denied     refused / deny      refused / deny
```

Read once per run (FR-014). The pair — verdict and source — travels together,
because FR-005 requires the status line to name where the authority came from
and a bare verdict cannot.

A fourth verdict exists and is not in the grid: **unreadable**, when the tracker
could not be reached. It resolves to refused like `unset` does, and is recorded
distinctly (FR-015), because a failed read decides the entire run and must not
be filed as though a person withheld authority.

## Appended: events

Three event kinds, all into the existing `events.jsonl`.

```
{"ts": "…", "event": "notify-grant",  "state": "granted", "source": "local"}
{"ts": "…", "event": "notify-action", "action": "issue-create", "count": 6}
{"ts": "…", "event": "notify-unread", "detail": "gh: HTTP 401 Bad credentials"}
```

`notify-unread` is where the tracker's stderr lands. The console line stays the
fixed `couldn't reach GitHub to check`, because `status` is glanced at and an
unbounded stderr wraps. Both are needed: the line tells you the run refused, the
event tells you whether it was auth, network, or a missing `gh` scope.

`notify-grant` answers *when was authority given* — which `notify.json` cannot,
since it holds one value and is overwritten. This mirrors `grant_auto_approve`'s
existing two-writes-for-two-questions split, and for the same stated reason.

`notify-action` is FR-010's required destination. It is the record; the session
summary and the PR body are renderings of it and are not required by this
feature.

## What this feature does not store

- **Per-step or per-action grants.** Authority is granted by class, not per
  step (#131 principle 1, carried into the accepted decision record).
- **Anything on `main`.** FR-008 — the state dir is per-branch, so this is
  structural rather than enforced, but a read on `main` returns refused
  regardless of what any branch's file holds.
- **A cached label value.** See above.
- **Who the person was.** wfctl cannot observe it —
  `approval-mode-is-stored-intent` established that nothing separates a person
  typing a flag from an agent running it. `source` names the *place*, not the
  actor, and the decision record is explicit that the human-only property is
  owned by rule rather than by observation.
