---
status: rejected
---

# wfctl names the reset, and something outside it performs one

## Context

`wfctl-owns-the-recycle-verdict` settles when a run should discard its window.
It leaves open the half #188 calls the hard one: the reset itself. The issue
records it as unverified — "`/clear` is a harness command. Whether an agent can
invoke one, or can only ask a human to, is unverified and decides which option
below is even available."

It was verified rather than reasoned about, and the answer came from the harness
in its own words. Asking for `/clear` by name returns:

```
clear is a built-in CLI command, not a skill. Ask the user to run /clear
yourself — it cannot be invoked via the Skill tool.
```

wfctl cannot perform one either, and that is a constraint it chose. Its runtime
dependencies are `typer` and `rich`; `_workmux.py` — the one module that knows
anything about the tool managing these panes — is pure `str -> str` and states
in its own docstring that it "imports nothing from `wfctl.*` and never calls
`subprocess`". A reset is a keystroke delivered to a terminal, and neither party
to the pipeline can deliver one.

A third party can. This worktree's pane is registered with workmux, and a prompt
sent to it arrives:

```
   workmux send <handle> "<text>"
     └─► queued at the pane's prompt
         └─► surfaced to the running agent as a user message   ✓ verified,
                                                                 probe 7731
```

The `PreToolUse` guard wfctl itself installs already allows `workmux` while
refusing other cross-worktree commands, so the channel is sanctioned rather than
discovered.

## Direct baseline

Leave the boundary where it is and let the instruction be the whole feature —
option A in #188. `end-session` prints "now `/clear`, then `/start-session`", a
person reads it and types both. Nothing new is owned, nothing is performed, and
the cycle happens exactly as often as someone is watching. This works today and
is the behaviour every attended run already has.

## Decision

wfctl emits the cycle as a named instruction in the payload and never executes
it. Who executes it is decided outside wfctl, by what the run has available: a
workmux-managed pane can be sent `/clear` and then `/start-session`; a run
without one prints the instruction and waits for a person. The baseline is not
replaced — it is the floor that the sent form rises above where a pane exists.

**The sent form was refused after this was written** — see *The performer cannot
be summoned by the agent either* below. What survives is the first sentence; the
performer is a supervisor outside the run or a person, never the agent.

## Owns truth

wfctl owns "what exactly performs the cycle?". Whether this run should recycle
now is the sibling record's — `wfctl-owns-the-recycle-verdict` — and claiming it
here too would give one fact two homes, which `knowledge-placement` rules out at
its line 36: "A fact with two homes has no owner."

wfctl does not own "the window is now empty" either — the harness does, and only
a keystroke at its prompt makes that true.

The agent cannot own the reset: verified above, it is refused the command by
name. wfctl cannot own it either, and for a reason worth stating as a
constraint rather than a limitation — reaching for `subprocess` to drive tmux
would put a terminal multiplexer in the dependency path of a tool whose config
edits are deliberately line scans, and `_workmux.py` exists to hold that line.
What is left is a third party that already has the pane, which is why the
decision names the performer instead of becoming one.

## Considered

- **Print the instruction and stop** — the direct baseline, and it is not wrong.
  It loses only the unattended case, which is the case #188 exists for and the
  case #147's acceptance test needs. It stays as the fallback rather than being
  rejected, because a run with no pane has no better answer.
- **wfctl shells out to `workmux send` itself** — equally sound in outcome, and
  rejected on placement. It would make a tool wfctl does not depend on a
  prerequisite for a pipeline step, and it would put the first `subprocess` call
  into the module that documents its absence as the reason its tests are cheap.
  The instruction reaches the same pane either way; only the dependency differs.
- **Spawn a fresh `claude -p` for each task** — a genuine reset, and unattended
  by construction. Rejected as the wrong problem: a new process is a new run,
  which is #101's `Run` entity and its durable-session machinery, and #188 is
  explicit that it is not that. It also discards the interactive session's tools
  rather than recycling its window.
- **Delegate each task to a subagent so the parent's window stays small** —
  sound for bulk work and already available. It does not solve this: the parent
  still accumulates every result it reads back, so the run that has to hold the
  pipeline together fills anyway, only more slowly.
- **A `Stop` hook that blocks and re-injects** — the seam exists and wfctl
  already uses it for `conversation-response-shape`. It can inject text and
  cannot empty a window, so it reaches the announcement half of this and none of
  the performing half.

## The performer cannot be summoned by the agent either

Driving the cycle was attempted and refused, by a layer neither the issue nor
the rest of this record anticipated. The harness's own permission classifier
declines an agent that scripts sends to its own pane:

```
Permission for this action was denied by the Claude Code auto mode
classifier. Reason: [Tmux Self Drive].
```

A single `workmux send` carrying plain text is allowed — probe 7731 went
through. What is refused is the agent assembling the cycle: wait for my own
pane to go idle, then reset it, then restart it. That is a policy boundary
rather than a mechanical one, and it is the right one — an agent that can
restart itself unsupervised is a different safety question from an agent that
can send a message.

So the reset has three refusals stacked on it, and only the first two were known
when this record was opened:

```
   agent invokes /clear          ✗ harness refuses by name
   wfctl shells out to workmux   ✗ declined by construction (_workmux.py)
   agent drives its own pane     ✗ refused by the permission classifier
   ─────────────────────────────────────────────────────────────────────
   a supervisor outside the run  — the only remaining performer
   a human at the prompt         — the baseline, and it still works
```

What survives is the decision as written — wfctl names the cycle and does not
perform one — and what changes is who the named performer can be. It is not the
agent under any arrangement. It is a process outside the run that watches for
the marker, or it is a person. #147's unattended acceptance test therefore needs
a supervisor it does not currently have, and that is a dependency this issue
should hand back rather than absorb.

## Consequences

The cycle's two sends cannot be issued mid-turn and left to land. Probe 7731
arrived while the agent was still working and was surfaced into the running
turn rather than executed at a boundary, so a `/clear` delivered the same way
would interrupt rather than reset. The performer has to wait for the pane to go
idle first — `workmux wait` is the verb that does it — which makes the cycle a
detached two-step rather than a single call, and makes "the pane is idle" a
precondition the design has to state.

A run whose pane is not registered with workmux is not a degraded case to be
fixed later. It is the baseline, and `wfctl status` says which of the two this
run is in, so an unattended run that stopped for a person is distinguishable
from one that silently never recycled.

## Log

- 2026-09-11  proposed    — #188: the reset was the open question; the harness
  refuses it to the agent and wfctl declines it by construction, so the
  performer is a third party and the decision is to name one.
- 2026-09-11  rejected    — #188 closed as completed by `aamarin`, on the design
  pass's recommendation rather than for lack of work. The decision was right and
  its performer turned out not to exist: the permission classifier refuses an
  agent authoring pane-driving automation at all, not merely self-targeted
  automation, and every remaining mechanism is Claude Code specific. The hook
  moves to the developer's own agent layer, which `install-modes` already
  requires independently — its line 60 puts a hook schema that "belongs to
  Claude Code, not to wfctl's base layer" in the agent layer, which is this case
  exactly. (`no-hardcoded-agent` agrees but decides a narrower question: which
  agent a committed flag may name, not where an agent-specific mechanism lives.)
- 2026-09-11  amended     — `Decision` asserted a performer the appended section
  refutes, with no pointer between them; a forward reference now sits in the
  `Decision`. `Owns truth` claimed the sibling record's question as well as its
  own and was narrowed to the performer half.
