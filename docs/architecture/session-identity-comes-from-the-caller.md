---
status: accepted
---

# A session's identity comes from the caller, never from wfctl's process tree

## Context

`session_started` answers "has `wfctl start` ever run on this branch". It scans
`events.jsonl` for any `start` line (`_session.py:41`), nothing ever clears it,
and `build_report` puts it on the payload the agent reads. So it is true for the
rest of the branch's life after its first session.

`speckit-orchestrate`'s step-0 gate reads that field to decide whether the
conversation it is running inside opened a session. The gate therefore covers a
branch's first session and nothing after, and says so in its own prose — a
second conversation that skips `/start-session` walks through it and does the
work #117 describes.

Closing that needs a fact nobody currently holds: which conversation is asking.
Three things were measured on this branch while deciding, and they bound the
answer between them:

```
wfctl's own shell        pid 13835 → 13935 across two calls   new every call
the agent process        88665, alive since Sep 11 22:16      outlives the work
  ├─ conversation 20336301…   Sep 12 00:31
  ├─ conversation 513763ff…   Sep 13 08:50
  └─ conversation 1d3da976…   Sep 13 09:16
environment variables    set in one call, unset in the next   die with the shell
```

A conversation begins and ends without touching any artifact or process wfctl
can read. `/clear` starts a new one over a process two days older than it.

## Direct baseline

Leave the boundary where it is: keep `session_started`, keep the gate reading
it, and keep the paragraph in `speckit-orchestrate/SKILL.md` that names the
limit. No new state, no new flag, no new field on the payload.

It costs nothing and closes nothing. The defect is the current behaviour, so the
baseline is #200 restated — and the warning carrying it lives in a file
`install-skills` rewrites from the bundle, which is not where a constraint
survives.

## Decision

The caller supplies its own session identity and wfctl records it verbatim.
`wfctl start` takes an opaque id — `--session-id`, falling back to
`WFCTL_SESSION_ID` in the environment — and a later command reports a session
open only when the caller presents the same id. wfctl never derives the id from
its own process tree, never parses it, and never names the variable a particular
host exports it from.

Where neither side carries an id, the payload keeps reporting the weaker fact it
reports today rather than guessing. An unconfigured repo is no worse off than
before; a configured one gets an answer the gate can use.

## Owns truth

The agent's host owns **"which conversation is this?"**.

wfctl cannot compute it. Everything wfctl can observe of its own execution is
either newer than the conversation or older than it: the shell it runs under is
replaced on every call, and the agent process above that shell served three
conversations across two days. There is no third thing to read — a conversation
boundary is not written to any artifact, and the one identifier that does track
it is held by the host and handed out only through the environment.

wfctl owns **"is the caller of this command inside the session recorded on this
branch?"**.

The agent cannot. Its answer would be a memory of an earlier turn, offered by
the same conversation the gate exists to test — the self-certification shape
`wfctl-runs-the-verification` rejects one level up. A skill computing it from
`events.jsonl` is refused for a second reason: that is a second inference path
over a question one payload already answers
(`pipeline-state-is-one-payload`), and it is what `session-state-is-re-derived`
means by deriving at read time inside wfctl rather than beside it.

The stored id is an identifier, not a cached conclusion. The verdict is
re-derived on every read by comparing it to what the caller presents, so nothing
here is a value that goes stale unnoticed.

## Considered

- **Liveness of a recorded process id** — record `<pid, start-time>` at `start`
  and check the pair is still alive. Sound mechanism at the wrong granularity:
  it identifies a process, and a process holds many conversations. Measured
  above — one agent process, three conversations, two days. It would report a
  session open for a `/clear` that just discarded the context `/start-session`
  exists to restore, which is the defect surviving its own fix.
- **wfctl walks its own ancestry to find the agent** — needs wfctl to recognise
  an agent, by name or by shape. `no-hardcoded-agent` governs committed config
  rather than process inspection, so this is not forbidden by its letter; its
  reasoning still holds, and more cheaply than an exception would. "One clone
  runs Claude, the next runs something else" is as true of a process name as of
  a config key, and a wrong guess here produces a wrong answer rather than an
  error.
- **A token wfctl mints and the agent echoes back** — equally capable of binding
  a caller, and it fails the same test it would be added to enforce. The token
  is readable in the state dir, and the conversation that would skip
  `/start-session` is the one that would read it from there. An id the host
  issues is not the agent's to forge.
- **Require the id and refuse without it** — makes a host integration mandatory
  for every command that does not need one, on a tool whose commands mostly
  don't. `no-hardcoded-agent` took the same fork and chose the degrading form;
  this follows it.
- **Branch-level liveness — "is any session open on this branch"** — answers a
  real question and not this one. The conversation that skipped the gate would
  see the *other* conversation's open session and pass, which is worse than the
  current flag because it reads as a fix.

## Consequences

The id has to be branch-scoped where it is stored. `resolve_agent_dir` allows
one `WFCTL_STATE_DIR` to serve several branches, which is why `_stall.py`
filters its own reads by branch; an owner record that skipped that would let one
branch's session answer for another.

The host integration is per-developer and uncommitted, in the same place
`WFCTL_AGENT` already lives. Nothing in the repository names it, and a clone
that sets nothing has to stay usable.

That leaves three situations where a boolean can carry two: the caller presents
the id `start` recorded; the caller presents a different id, or none, against a
branch that has one recorded; and no host wiring exists anywhere, so wfctl holds
no basis for either answer. Folding the third into the first reproduces #200 on
every unwired host and says nothing about it. Folding it into the second refuses
the conversation that *did* run `/start-session`, which is a regression rather
than a degradation. So what the payload carries is a name, and `unknown` is one
of its values — `pipeline-state-is-one-payload` took this same fork for a step's
state, and for the same reason. What a gate then does with `unknown` is the
gate's decision rather than this record's; what this record owes it is the
ability to tell `unknown` apart from a refusal.

`wfctl end` gains a reason to write its event beyond recording that it ran: a
reader has to fold it into the holder relation, so that a session wrapped up
deliberately does not read as open to the conversation that follows it in the
same process. [[200-session-id-rides-on-the-start-event]] settles this by an
`ended` flag over the append-only log rather than by clearing anything —
consistent with this record's own `session_started` never rescinding once true.

Codex was the worked case, and it arrived by the same route as the decision. The
adversarial review that recommended this pattern named its own cost — "explicit
integration by each agent host, and plain terminals need an explicit
wrapper/token workflow" — while running under an agent that was later measured to
export one of its own. The cost it named is real and smaller than it reads: a
tool that takes an opaque id from the environment is agent-agnostic in its mechanism and per-host in its coverage, and
those are not the same property.

Every agent host measured on 2026-09-13 already supplies what this needs, so
the integration is a mapping rather than a feature request: Claude Code exports
`CLAUDE_CODE_SESSION_ID` (observed changing across `/clear`), Codex exports
`CODEX_SESSION_ID`, and the Copilot CLI exports `COPILOT_AGENT_SESSION_ID` —
each matching the id that host itself uses to resume a conversation. Three
different spellings for one concept is the reason wfctl reads its own name and
never theirs; a host that arrives later brings a fourth spelling and no change
here.

A nested agent inherits the outer host's variable. Measured: a Codex run and a
Copilot run launched from a Claude conversation each carried
`CLAUDE_CODE_SESSION_ID` alongside their own, and both runs were made under a
Claude conversation that also carried `CLAUDE_CODE_CHILD_SESSION=1`. So the
mapping has to resolve the innermost host's own variable rather than the first
one it finds set, or a sub-agent presents its parent's identity and passes a
gate it never checked in at — #200 one level down, and reached by inheritance
rather than by skipping anything.

**`CLAUDE_CODE_CHILD_SESSION=1` is not itself the nesting signal this record
first read it as.** Measured again on 2026-09-14, in an ordinary top-level
`/start-session` conversation with no parent Claude conversation anywhere above
it: the flag was still `1`. `200-session-id-rides-on-the-start-event.md` § Assumed
names exactly this as the falsifying case for "the flag carries no nesting
signal" and, having now been observed, that is the reading that stands — the
flag says something else about how this host launches a session, not whether
one is nested inside another. The paragraph above is unaffected in its
conclusion: a nested agent still inherits the outer host's variable, verified
independently by the Codex and Copilot measurement, which named no flag as its
evidence. What is retracted is only the claim that the flag is how a mapping
would *detect* nesting; nothing here has proposed a replacement.

## Log

- 2026-09-13  proposed    — #200; the level-2 answer for what a gate can ask
- 2026-09-13  accepted    — Andre, in the #200 session on 2026-09-13 — https://claude.ai/code/session_01GAgg3JT1W3Dxh81GZXMfG6
- 2026-09-14  amended     — #200 implement session, T031: retracted the reading
  of `CLAUDE_CODE_CHILD_SESSION=1` as the nesting signal, per the falsifying
  measurement `200-session-id-rides-on-the-start-event.md` § Assumed named in
  advance. The nested-inheritance conclusion is unaffected.
