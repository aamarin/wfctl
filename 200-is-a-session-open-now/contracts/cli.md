# CLI contract — #200, is a session open now?

wfctl's public interface is its commands and the JSON `status` emits. Both are
read by shipped skills and by other projects' hooks, so both are contracts.

## `wfctl start`

**New option**

```
--session-id TEXT    Opaque identity for the calling conversation.
                     Falls back to WFCTL_SESSION_ID. Recorded verbatim;
                     never parsed.
```

**Behaviour by case**

| Branch state | Identity presented | Effect | Console |
| --- | --- | --- | --- |
| no session | any, or none | session opens, `start` appended | `✓ Session started — step: …` (unchanged) |
| holder == presented | same | idempotent; log unchanged unless a sitting boundary is due | `ℹ Already initialized …` (unchanged) |
| holder != presented | different | **takeover**: `start` appended with the new id | `✓ Session started — took over from another conversation` |
| holder absent | an identity | **takeover** (FR-012): `start` appended with the id | `✓ Session started — took over from another conversation` |
| holder present | none | no takeover; behaves exactly as the released version | `ℹ Already initialized …` (unchanged) |

The last row is the one that carries FR-006. A caller presenting nothing must
never displace a holder, or an unwired repository would take the branch from a
wired one on every `start`.

**Exit code**: 0 in every row. A takeover is not an error.

## `wfctl status --json`

**New fields**, beside the existing `session_started`:

```json
{
  "session_started": true,
  "session_open": true,
  "session_holder": "self"
}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `session_started` | bool | **unchanged** — has a session ever run on this branch |
| `session_open` | bool | is a session open for the caller presenting this identity |
| `session_holder` | `"self"` \| `"other"` \| `"none"` \| `"unknown"` | who holds the branch, relative to the caller |

`session_holder` never carries the identity itself. `"unknown"` is the unwired
case — the caller presented nothing, so the question has no answer and
`session_open` mirrors `session_started` to keep FR-006.

| Branch state | `session_started` | `session_open` | `session_holder` |
| --- | --- | --- | --- |
| A — never had a session | `false` | `false` | `"none"` |
| B — open, caller holds it | `true` | `true` | `"self"` |
| C — open, another holds it | `true` | `false` | `"other"` |
| D — caller presented no identity | unchanged | mirrors `session_started` | `"unknown"` |

**Compatibility**: a reader that knows only `session_started` sees no change in
any row. That is the whole of SC-006, and it is why the field was not repurposed.

## `wfctl resume` and `wfctl end`

Both currently refuse when `session_started` is false, printing `_NO_SESSION` and
exiting 1. Both gain the second check.

| Caller | `resume` | `end` |
| --- | --- | --- |
| holds the branch | proceeds | proceeds |
| does not hold it | refuses, exit 1 | refuses, exit 1 |
| presented no identity | proceeds, as released | proceeds, as released |
| branch never had a session | refuses, exit 1 (unchanged) | refuses, exit 1 (unchanged) |

**Two refusal strings, never one** (FR-007):

```
never had a session   No wfctl session for this branch. Run `/start-session` first.
held by another       No wfctl session for this conversation — the last session on
                      this branch was opened by a different one. Run `/start-session`.
```

The second names the conversation; the first names the branch. A reader must be
able to tell a fresh branch from a held one from the string alone (SC-005), so a
test asserts they are distinct rather than asserting either one's wording.

**`end` stays refused rather than taking over.** Taking a branch over is `start`'s
move, and it is the reversible one. Ending a session someone else opened writes
their handoff, which nothing recovers.

## Shipped skills

**`start-session`** presents the host's identity, in the shape
`no-hardcoded-agent` already established for `--agent`:

```bash
wfctl start ${WFCTL_SESSION_ID:+--session-id "$WFCTL_SESSION_ID"}
```

The host's own variable is mapped to `WFCTL_SESSION_ID` in the reader's shell
profile, not in committed config — the same place `WFCTL_AGENT` is set, and for
the same reason.

**`speckit-orchestrate`** step 0 reads `session_open` instead of
`session_started`, and renders the second refusal string when `session_holder` is
`"other"`. The gate's existing behaviour for state A is untouched.
