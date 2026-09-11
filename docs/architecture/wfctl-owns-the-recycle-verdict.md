---
status: proposed
---

# wfctl decides when a run recycles its window, not the agent

## Context

A run that goes brainstorm → PR does not fit in one context window. What catches
it today is harness compaction: a summary written by the harness, over contents
nobody chose, at a moment nobody picked (#188). wfctl already owns a better
carrier — the `end-session` handoff, written to a template that names
accomplishments, decisions and a Next Session TODO — and fires it once per
session rather than once per task.

Turning that into a cycle needs someone to answer when it fires. The issue
records the threshold as unobservable: "~150K is a number the agent cannot
currently observe about itself". That turns out to be false, and the correction
is what makes this record necessary rather than academic. Two observation points
exist today and both are already wired:

```
   the transcript                        the statusline
   ──────────────                        ──────────────
   last assistant message carries        renders `Context ██░░░ 14%`
   usage: input + cache_read +           to the terminal, for a human
   cache_creation = occupancy            to read
   wfctl already receives its path       the agent never sees it
   on the Stop hook (cli.py:4732)
```

So the question is not whether the number can be had. It is who is allowed to
hold it, given that the act this feature performs destroys whoever was holding
it.

## Direct baseline

Leave the boundary where it is. `speckit-orchestrate` already drives the loop,
already reads the payload twice per pass, and could read the transcript itself:
the path is derivable, the arithmetic is three fields added together, and the
skill could compare the result against a constant written into its own prose. No
wfctl change at all — a paragraph in `speckit-orchestrate/SKILL.md`, and the
agent decides at each task boundary whether it has room for another step.

## Decision

wfctl computes whether this run's window has filled past the point where the
next task should start fresh, from the transcript it is already handed, and
carries the verdict in the one payload every view of pipeline state renders
(`pipeline-state-is-one-payload`). Orchestrate reads that verdict and acts on
it; it does not derive it.

## Owns truth

wfctl owns "has this run's window filled past the point where the next task
should start fresh?".

The agent cannot, and the reason is sharper here than anywhere else in this
repo: the verdict's whole purpose is to destroy the context that computed it. A
tally the agent keeps is lost in the act the tally exists to trigger, so the
session that comes back has no way to tell a window recycled thirty seconds ago
from one that has never recycled — and a second reading taken after the reset
reports near-empty, which is the answer that says "carry on" forever. This is
`wfctl-counts-the-passes`' argument met one turn later: there the count had to
outlive a clear that might happen, here it has to outlive one this feature
performs on purpose.

## Considered

- **The agent reads its own transcript and decides** — the direct baseline.
  Cheapest possible change, and the arithmetic is genuinely available to it. It
  loses the reading at the moment of the reset, which is the only moment the
  feature exists for, and a self-reported occupancy is unfalsifiable in the same
  way a self-reported test result is (`wfctl-runs-the-verification`).
- **A hook reports pressure and the skill decides at the next boundary** —
  option B in #188, and sound: the `Stop` hook already returns
  `additionalContext` to the agent, so the seam is built. It loses on where the
  answer lands rather than on correctness. A fact injected into the agent's
  context is visible to that context only, so `wfctl status` could not answer
  "did this run recycle, and when?" after the scrollback is gone — which is the
  question that separates a run that reset cleanly from one that died.
- **Threshold as a configurable key** — declined, and #188 scopes it out for the
  reason #121 already argues: vocabulary before a second consumer wants a
  different answer. One number, picked once, learned from.
- **Fire on the harness's own compaction signal instead** — rejected because it
  inverts the boundary this feature is about. Compaction fires on a token count
  over contents nobody chose; the whole claim here is that a task boundary is a
  moment someone picked.

## Consequences

`resume` gains a reading per pass, the way it gained an evidence digest for
`wfctl-counts-the-passes`. That is history rather than cached state — a past
pass's occupancy cannot be re-derived, because the window has moved since — and
is what `session-state-is-re-derived` reserves for a session file to hold.

The verdict lands in the payload rather than in orchestrate's output, so
`wfctl status` still answers "where did this get to, and has it recycled?" once
the run's scrollback is gone. That is what makes a run that recycled and
continued distinguishable from one that stopped.

This record answers when the cycle fires. It does not answer who performs it,
and those turn out to be different owners —
`wfctl-names-the-reset-it-cannot-perform`.

## Log

- 2026-09-11  proposed    — #188: the recycle needs an owner before it can be
  given a shape, and the act destroys whoever the agent would have been.
