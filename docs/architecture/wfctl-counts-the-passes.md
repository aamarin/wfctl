---
status: proposed
---

# wfctl counts the pipeline's passes, not the agent

## Context

`speckit-orchestrate` runs the pipeline as a loop: it reads the payload,
executes whatever `next_command` names, and the command it ran invokes
orchestrate again when it finishes. Nothing counts the passes. A step whose
evidence is produced by an agent's judgment rather than by a file appearing can
complete, change nothing, and leave itself exactly as current as it found it —
and the loop re-enters it with the same inputs, indefinitely (#332).

Giving the loop a bound means something has to hold how many passes a step has
had and what the last one left behind. That is a piece of state, and it needs an
owner before it can be given a shape.

## Direct baseline

Leave the boundary where it is. Orchestrate already drives the loop and already
holds both payload reads of the current pass in its own context, so it could
carry a tally forward in conversation: remember which step was emitted last,
compare it to this one, and stop on the third match. No wfctl change at all —
prose in `speckit-orchestrate/SKILL.md` and nothing else.

## Decision

wfctl computes whether the run has stopped making progress, from the event log
it already writes, and carries the verdict in the one payload every view of
pipeline state renders. Orchestrate reads that verdict and acts on it; it does
not derive it.

## Owns truth

wfctl owns "has this run stopped making progress, and on which step?".

The agent cannot: the count has to survive longer than the agent's memory of it.
A run unattended enough to need a bound is a run whose conversation gets cleared
or compacted partway, and a session that picks the branch up tomorrow has no
memory of today's passes at all. Both reset the tally to zero at exactly the
moment the bound was supposed to fire. The event log has every pass on disk and
is read the same way on the tenth pass as on the first.

## Considered

- **The agent counts passes in its own conversation** — the direct baseline. It
  is the cheapest possible change and it is sound while the conversation lasts;
  it loses the count precisely when a run is long enough to need one, which is
  the only case the feature exists for.
- **A per-step guard recording that the step already ran** — rejected in #332
  before this record. It cannot be derived from artifacts on disk, so it would
  have to be written and read back, which is what `session-state-is-re-derived`
  exists to prevent.
- **A blocking `reason` on the branch that finds open markers** — would report
  `auto: false` for exactly the state `clarify` exists to handle, and widens what
  `reason` means: every other reason names something re-entering the step cannot
  fix, and a standing marker is the opposite.

## Consequences

`resume` records enough about each pass to compare two of them, which its event
does not carry today. That is history rather than cached state — a past pass's
evidence cannot be re-derived, because the artifacts have moved since — and it is
what `session-state-is-re-derived` reserves for a session file: what
re-derivation cannot reach.

The verdict lands in the payload rather than in orchestrate's output, so
`wfctl status` still answers "where did this get to?" after the run's scrollback
is gone. That is what makes an unattended run that stopped distinguishable from
one that finished.

## Log

- 2026-09-10  proposed    — #332: the orchestrate loop has no bound, and the
  count needs an owner before it can be given a shape.
