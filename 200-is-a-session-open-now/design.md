# Design — #200, is a session open now?

`wfctl status` reports `session_started`, six speckit skills gate on it, and it
answers a different question than every one of them asks. It is true from the
first `start` event a branch ever recorded and nothing rescinds it, so it means
"has a session ever run here?" while every caller reads "is a session open now?"

## Level 1 — behavior

Four reachable states, each with the string the gate renders in it, judged in
that state. The gate's wording is `speckit-orchestrate` step 0.

**A — the branch has never had a session.**

```
No wfctl session for this branch. Run `/start-session` first.
```

True today, unchanged.

**B — a session is open and this conversation is the one that opened it.**

```
(the gate passes, silently)
```

True today, unchanged.

**C — a session ran on this branch; this conversation is not it.**

Reached two ways — a new conversation that skipped `/start-session`, and a
conversation that resumed after `wfctl end` — and both render the same string
because both take the same remedy. One state, two paths.

```
today:     (the gate passes, silently)
```

False. This is the defect. The gate reports an open session to a conversation
that has none, and the six skills that invoke the gate *last* do their work
before finding out (#201).

```
accepted:  No wfctl session for this conversation — the last session on this
           branch was opened by a different one. Run `/start-session`.
```

True. Names what is actually wrong rather than reusing A's string, which would
tell a reader the branch is fresh when it is not.

**D — the host exports no session id.**

```
(every gate behaves exactly as it does today)
```

True, and deliberately so. A repo with no host wiring sees wfctl 0.20.0's exact
behavior. Treating an absent id as a refusal would regress every unwired repo,
which is a larger blast radius than the defect being fixed.

## Level 2 — architecture

Answered and committed. Do not restate it here:
`docs/architecture/session-identity-comes-from-the-caller.md` (accepted).

The caller presents an opaque id; wfctl records it verbatim, never derives it
from its own process tree, never parses it, and never names the variable a
particular host exports it from.

## Level 3 — design

The structural choice and its rejected alternative are committed at
`docs/architecture/design/200-session-id-rides-on-the-start-event.md`
(`proposed`). The claims split, which stays here:

```
checked                                    assumed
─────────────────────────────────────      ─────────────────────────────────────
_session.py:41 — session_started           The host exports an id that changes
returns True on the first line whose       exactly when the conversation's
event is "start"; no branch returns        context is lost. Falsified by a host
False afterwards                           that rotates it more often — per tool
                                           call, per pane resize
cli.py:310 — the already-initialized
path carries every session after the       A dedicated file would go stale on a
branch's first                             crash. Not checkable here; no such
                                           file exists to observe
cli.py:322-324 — a start event is
appended on that path only when            CLAUDE_CODE_CHILD_SESSION carries no
opens_a_new_sitting() is true              nesting signal. The environment
                                           evidence says it cannot be inherited,
_stall.py:174-207 — that returns true      which is weaker than meaningless
only when a resume follows the last
start or end for this branch

tests/test_agent_session.py:174 —
test_start_is_idempotent asserts
events.jsonl is byte-identical after
a second start

state dir holds events.jsonl,
notify.json, session-summary.md.
No session.json, no mode.json

measured across /clear, same pane:
CLAUDE_CODE_SESSION_ID changed,
CLAUDE_CODE_BRIDGE_SESSION_ID did not

ps eww on two claude processes —
neither carries SESSION_ID,
CHILD_SESSION or SESSION_ATTENDED in
its own environment
```

The asymmetry is the point: eight checked against three assumed, and the three
that remain are all about the *host*, not about wfctl. That is what
`session-identity-comes-from-the-caller` bought — wfctl stores an opaque value,
so a wrong guess about the host is a mapping to fix rather than a design to
redo.

One checked claim was false when this gate ran and is why the design changed:
`wfctl start` does **not** write a `start` event every session. The amendment —
append when the presented id differs from the last recorded one — is carried in
the record with the flow and the case table.

## Decisions ledger

| # | Level | Decision |
|---|---|---|
| 1 | behavior | an absent id → every gate behaves exactly as today; an unwired repo is no worse off |
| 2 | behavior | `wfctl start` with a new id takes over the branch; `end` stays gated |
| 3 | behavior | state C gets its own string, not A's — "this conversation", not "this branch" |
| 4 | architecture | the caller supplies the id; wfctl records it verbatim (record, accepted) |
| 5 | design | the id rides on the `start` event, not a new file (record, proposed) |
| 6 | design | `start` appends when the presented id differs, closing the case where nothing was appended at all |
| 7 | design | `wfctl resume` keeps its own session guard — it is also typed by hand, and that path reaches no gate |

## Open questions

- **Which host variable `/start-session` presents.** The measurement says
  `CLAUDE_CODE_SESSION_ID`, because it changes across `/clear` and the stable
  bridge id does not. What is unmeasured is whether it is stable *within* a long
  session across hours; a rotation there makes every command look like a
  takeover.
- **`CLAUDE_CODE_CHILD_SESSION` is set with no parent.** The environment
  evidence rules out inheritance through the process tree. It does not establish
  what the flag means, and `session-identity-comes-from-the-caller` builds a
  paragraph on reading it as a nesting marker. That paragraph needs revisiting
  or removing.
- **Nothing writes a session's state before `/clear`** (#371). Out of scope
  here, and it is why this file exists at all rather than living in a summary.
