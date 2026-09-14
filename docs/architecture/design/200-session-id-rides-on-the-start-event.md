---
status: accepted
---

# The caller's session id rides on the `start` event, and `start` appends one whenever the id is new

## Context

`wfctl status` reports `session_started`, and six speckit skills gate on it. It
is true from the first `start` event a branch ever recorded and nothing rescinds
it, so it answers "has a session ever run here?" while every caller reads it as
"is a session open now?" (#200). Closing that gap means wfctl has to hold a
value that distinguishes one sitting from the next, and the accepted record
[[session-identity-comes-from-the-caller]] settles where that value comes from:
the caller presents an opaque id, wfctl stores it verbatim.

What it does not settle is *where wfctl puts it*. That is this record.

The pressure is lifetime. The id has to be durable enough to survive between two
commands in one session, and short-lived enough that the next conversation does
not inherit it — and the process that would clear it is the one most likely to
die without running.

## Verified

- `wfctl/_session.py:41` — `session_started` returns `True` on the first line
  whose `event` is `"start"`, and no branch of it returns `False` afterwards.
- `wfctl/cli.py:370` — `if report.session_started and not force:` is the path
  every session after a branch's first one takes.
- `wfctl/cli.py:410-426` — on that path (past the takeover branch) a `start`
  event is appended only when `opens_a_new_sitting(agent_dir, branch)` is true.
- `wfctl/_stall.py:174-207` — `opens_a_new_sitting` returns true only when a
  `resume` event follows the last `start` or `end` for this branch.
- `tests/test_agent_session.py:175` — `test_start_is_idempotent` asserts
  `events.jsonl` is byte-for-byte unchanged after a second `start`.
- The state dir for this branch holds `events.jsonl`, `notify.json` and
  `session-summary.md`. There is no `session.json` and no `mode.json`.
- Measured in this worktree across a `/clear`, same pane:
  `CLAUDE_CODE_SESSION_ID` changed (`1fabf802-…` to `e41205e2-…`);
  `CLAUDE_CODE_BRIDGE_SESSION_ID` did not.
- `ps eww` on two running `claude` processes shows neither carries
  `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_CHILD_SESSION` or
  `CLAUDE_CODE_SESSION_ATTENDED` in its own environment — those are injected
  into tool subprocesses, not inherited from a parent.

## Assumed

- **The host exports an id that changes exactly when the conversation's context
  is lost.** Falsified by a host that rotates it more often than that — per tool
  call, per pane resize — which would make every command look like a new
  session. The `/clear` measurement above confirms one host at one boundary; it
  does not establish the id is stable *within* a session across hours.
- **A dedicated file would go stale on a crash.** Not checkable here, because no
  such file exists to observe. Falsified by a host that reliably runs a cleanup
  on abnormal exit.
- **`CLAUDE_CODE_CHILD_SESSION` carries no nesting signal.** The environment
  evidence above says it cannot be inherited, which is weaker than saying it is
  meaningless. Falsified by a genuinely nested agent whose shell reports a value
  differing from its parent's.

## Direct baseline

A `session.json` in the state dir beside `notify.json`, holding the id
presented by the last `wfctl start`. `start` writes it, `end` deletes it, and
every other command reads it and compares. Roughly fifteen lines, no new
concepts, and it is what a reader reaches for first.

## Decision

The id is a field on the `start` event in `events.jsonl`. `wfctl start` appends
a `start` event when there is no session on the branch, when
`opens_a_new_sitting()` is true, **or when the id presented differs from the
last one recorded**. A session is open when the id a command presents matches
the id on the most recent `start` event, and no `end` event follows it.

The third append condition is the amendment this record exists to carry. Without
it the store is correct and unreachable: a fresh conversation on a branch that
has not yet run `resume` takes `cli.py:370`, finds `opens_a_new_sitting()` false
because no `resume` has ever been written, and appends nothing — so the session
that most needs a new id recorded records none.

## Diagram

```
              baseline                          decision

stable   ┌──────────────┐                  ┌──────────────┐
         │ `/start-…`   │                  │ `/start-…`   │
         │  the caller  │                  │  the caller  │
         └──────────────┘                  └──────────────┘
                 │ presents id                     │ presents id
═══ caller owns the id ═══════════════════════════════════════════
    (session-identity-comes-from-the-caller, accepted)
                 │                                 │
volatile         ▼                                 ▼
         ┌──────────────┐                  ┌──────────────┐
         │ wfctl start  │                  │ wfctl start  │
         └──────────────┘                  └──────────────┘
           │          │                           │ appends
   writes  │          │ deletes                   ▼
           ▼          ▼                    ┌──────────────┐
     ┌──────────────┐ ▲                    │ events.jsonl │
     │ session.json │ │                    │ append-only  │
     └──────────────┘ │                    └──────────────┘
           ▲          │                           ▲
    reads  │      ┌───┴────┐             reads    │
           └──────│ wfctl  │                      └───── every command
                  │  end   │
                  └────────┘
```

The graphs differ by one component and one arrow direction. The baseline has a
second store whose truth depends on a *deletion* arriving; the decision has one
store that only ever grows, so no command has to succeed for the record to stay
honest. A crashed session leaves the baseline claiming a session is open
forever, and leaves the decision with a `start` event the next conversation's
differing id supersedes on its own.

The divider is the one `session-identity-comes-from-the-caller` already drew. No
new boundary appears here, which is what keeps this a level-3 record.

## Considered

- **`session.json`, the direct baseline** — sound, and loses on the deletion
  arrow. Its correctness rests on `end` running, and the session that most needs
  clearing is the one that was killed.
- **Append a `start` event unconditionally** — simpler than the three-way
  condition, and breaks `test_start_is_idempotent` (`tests/test_agent_session.py:174`).
  `/start-session` runs `wfctl start` on every handoff, so the log would grow a
  line per invocation rather than per conversation.
- **Use the stable id (`CLAUDE_CODE_BRIDGE_SESSION_ID`)** — it survives a
  `/clear`, which is exactly wrong here: a cleared agent has lost its context and
  must re-run `/start-session`, and a stable id would tell it a session is
  already open. That reproduces #200 in a new form.
- **Derive the id from wfctl's own process tree** — refused by
  [[session-identity-comes-from-the-caller]], which is in force.

## Consequences

Gained: the "is a session open now?" question is answerable, and nothing has to
be cleaned up for the answer to stay true.

Harder: `events.jsonl` now carries a value that is meaningful to compare rather
than only to count, so a reader of the log has to know that only the *most
recent* `start` is live. `session_started`'s existing first-match read stays
correct for the question it actually answers and must not be repointed at this.

New failure mode: a host that rotates its id within a single conversation makes
every command look like a takeover. wfctl cannot detect this — it stores the id
verbatim by record — so the symptom surfaces as a session that can never stay
open, and the fix is a host mapping rather than a wfctl change.

## Verification

- A test that runs `start`, presents a different id to `start`, and asserts a
  second `start` event was appended carrying the new id.
- `test_start_is_idempotent` still green: a second `start` presenting the *same*
  id appends nothing.
- A test that `session_started` is unchanged by all of the above, since six
  skills read it.
- On a branch whose log holds `start`/`end`/`start`, a command presenting the
  first id reports no open session.
- `wfctl start` itself appends that second `start` line when the *same* caller
  reopens a branch it just ended — `test_a_session_that_ended_can_start_again_
  with_the_same_identity`. The takeover check has to compare the holder
  *relation* (`report.session_holder`), not raw identity: `last_session_id`
  does not know about an intervening `end`, so a caller re-presenting its own id
  read as already holding the branch, took over nothing, and was then refused by
  every later gate as `"other"` — locked out of the session it just reopened.

## Log

- 2026-09-13  proposed  — written at the `design-levels` level-3 gate for #200,
  after checking the four claims under the chosen structure and finding the
  append condition false.
- 2026-09-14  accepted  — Andre, in the #200 implement session on 2026-09-14 —
  https://claude.ai/code/session_01GAgg3JT1W3Dxh81GZXMfG6
