# Data model — #200, is a session open now?

Phase 1. Three entities, one of them new, one gaining a field, one unchanged and
listed because a reader has to know it was considered and left alone.

## Session identity

**What it is**: an opaque string supplied by whatever is calling wfctl, which
distinguishes one conversation from the next.

| Attribute | Value |
| --- | --- |
| Source | `--session-id`, falling back to `WFCTL_SESSION_ID` |
| Type | string, non-empty; no format asserted |
| Owned by | the caller |
| Computed by wfctl | never |

**Validation rules**

- Non-empty after stripping. An empty string, or whitespace only, is treated as
  **absent** rather than as an identity — the same path a caller that presents
  nothing takes. This matters because `${WFCTL_SESSION_ID:+…}` in a hook already
  collapses unset and empty, so the two must not diverge downstream.
- Never parsed, split, matched against a pattern, or interpreted. Equality is the
  only operation wfctl performs on it.
- Never logged anywhere but the event that records it, and never printed in full
  by `status` — the holder is reported as a fact about *whether it is you*, not
  as a value to copy.

**Why wfctl cannot compute it**: wfctl's process is not the conversation. It is
spawned per command and exits, and a sub-agent's process is not its parent's, so
nothing in the process tree distinguishes the two cases that matter. This is the
ownership claim `session-identity-comes-from-the-caller` settles.

## Start event

**What it is**: the existing line the log already carries when a session opens.
It gains one optional key.

```
{"ts": "…", "event": "start", "branch": "…", "step": "…", "session_id": "…"}
```

| Attribute | Change |
| --- | --- |
| `ts`, `event`, `branch`, `step` | unchanged |
| `session_id` | **new, optional** — present only when the caller presented one |

**Validation rules**

- The key is omitted, not written as `null`, when no identity was presented. A
  reader distinguishes "this session had no identity" from "this line predates
  the feature" by neither — both are correctly the same fact, which is why one
  representation serves both.
- Append-only. A takeover appends a new `start` line; no earlier line is ever
  rewritten or removed.
- A malformed line is skipped by every reader, matching `session_started`'s
  existing posture: the log is appended to by every command, and a truncated
  final write must not make a running session look unstarted.

## Branch session record

**What it is**: `events.jsonl` in the branch's XDG state dir, read as a whole.
Unchanged in shape; two new questions are asked of it.

**Derived values** — computed on every read, cached nowhere
(`session-state-is-re-derived`):

| Question | How it is derived |
| --- | --- |
| Has a session ever run here? | first line whose `event` is `start` — unchanged |
| Who holds the branch? | last line whose `event` is `start`, its `session_id`, or absent |
| Is a session open for this caller? | the holder equals the identity the caller presented |

## State transitions

The four states in `design.md` § Level 1, as transitions of the branch record:

```
no start line
  └─► A  never had a session
      · any start, with or without an identity ─► B or D

holder == caller's identity
  └─► B  open, and this conversation holds it

holder present, != caller's identity
  └─► C  open, held by another conversation        ◄── the defect
      · caller runs start ─► takeover, appends a start line ─► B
      · displaced conversation runs start ─► takeover back ─► B for it

holder absent, or caller presents no identity
  └─► D  unwired
      · behaves exactly as the released version, in every gate
      · first identified start ─► takeover ─► B    (FR-012)
```

**Not a state**: "the session ended". `end` appends an `end` line and leaves the
holder where it was, so a branch whose session was wrapped up is still state C to
the next conversation — the same string, the same remedy, which is why
`design.md` calls C one state reached two ways.

## Considered and left alone

`mode.json` — the state dir's other file, holding `auto_approve`. It is the
precedent for storing a value re-derivation cannot reach, and the identity is a
second such value, so putting it there is the obvious move. It is not made:
`mode.json` documents itself as one writer, one reader, overwritten whole, and a
second key would turn every write into a read-merge-write and give a partly
corrupt file a meaning nobody has decided. The same reasoning already produced
`notify.json` as a separate file rather than a second key.
