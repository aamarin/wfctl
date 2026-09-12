# Recycle context between tasks

## Problem Statement

How might we let a run that spans brainstorm → PR discard its own context at a
task boundary it chose, instead of having the harness compact it at a token
threshold over contents nobody picked?

## Recommended Direction

Option C from #188, with one correction the issue could not make because it had
not run the experiment. The issue treats two things as unknown — whether an
agent can reset its own window, and whether the threshold is observable — and
leans C on the assumption that both resolve together. They do not. The threshold
is observable today and the reset is refused today, so C splits into a half wfctl
owns outright and a half it can only name.

wfctl computes the verdict from the transcript it is already handed on the `Stop`
hook, and carries it as `recycle` on `PipelineReport`, beside `stall`. That keeps
the mechanism in the one payload every view renders
(`pipeline-state-is-one-payload`) and keeps the answer legible to
`wfctl status` after the scrollback is gone, which is what separates a run that
recycled and continued from one that died. `speckit-orchestrate` gains a fifth
arm in step 5, between `stall` and `auto`.

The cycle itself is delegated, because neither party can perform it. The harness
refuses `/clear` to the agent by name, and wfctl declines to shell out by a rule
`_workmux.py` states about itself. What performs the cycle is whatever the run
has: a workmux-managed pane can be sent `/end-session`, then `/clear`, then
`/start-session`; a run without one prints those three commands and waits for a
person. The second is option A, kept as the floor rather than rejected as a
rival — a run with no pane has no better answer, and saying so in the payload is
what makes an unattended run that stopped distinguishable from one that never
recycled.

What makes throwing the window away lossless is `session-state-is-re-derived`:
everything derivable from artifacts is derived at read time, so only the
deliberate prose survives, and the prose is exactly what re-derivation cannot
reach. That record is cited rather than re-argued.

## Behavior — what each state renders

Three reachable states at a task boundary, read in that state and judged:

```
recycle: null                      (the common case)
  nothing renders; the loop proceeds exactly as today            ✓ true


recycle present, pane registered
  "Recycling: 152K of 200K used, and `plan` just completed.
   Handing off, clearing, and resuming — this session ends here." ✓ true
                                                        └─ says the session
                                                           ends, which it does


recycle present, no pane registered
  "Window at 152K of 200K. Run `/end-session`, then `/clear`,
   then `/start-session` to continue from `tasks`."               ✓ true
                                                        └─ names the step the
                                                           next session resumes
                                                           at, not "continue"
```

And the state that only exists after the cycle, rendered by `wfctl status` on a
branch whose run has recycled:

```
  recycled once this sitting — 14:22, at the `plan` boundary       ✓ true
```

The level-3 consequence generated here, which is what says level 1 is finished:
the third string names the step to resume at, so the payload has to carry the
*current step at the moment of the verdict* and not merely a boolean. The fourth
string names a time and a boundary, so the event log has to carry one line per
recycle rather than a flag that is set and read back.

## Boundaries and Ownership

Level 2 was answered and both answers are records, not sections here.

wfctl owns "has this run's window filled past the point where the next task
should start fresh?". The agent cannot: the verdict's purpose is to destroy the
context that computed it, so a tally the agent keeps is lost in the act the tally
exists to trigger, and a reading taken after the reset reports near-empty
forever. Recorded as `wfctl-owns-the-recycle-verdict`.

wfctl owns "should this run recycle now, and what exactly performs the cycle?"
and owns *nothing* about "the window is now empty" — the harness owns that, and
only a keystroke at its prompt makes it true. The agent cannot: verified, it is
refused `/clear` by name. wfctl cannot: `_workmux.py` is pure `str -> str` and
says so as a constraint rather than an accident. Recorded as
`wfctl-names-the-reset-it-cannot-perform`.

## Key Assumptions to Validate

- [ ] A `/clear` delivered by `workmux send` executes as a slash command rather
      than landing as literal text — test by sending one to a throwaway pane and
      reading what the transcript holds afterwards.
- [ ] `workmux wait` can hold until the pane is idle, and a detached process
      outliving the agent's turn can then send — test by sending a marker
      through `wait` and confirming it arrives at a boundary rather than
      mid-turn, which is how probe 7731 arrived.
- [ ] Occupancy read from the last assistant message is stable across two
      adjacent task boundaries with no work between them — test by reading it
      twice and comparing.
- [ ] A recycle does not loop: the session that comes back reads a fresh window
      and does not immediately recycle again — this is the acceptance test, and
      it cannot be asserted in `pytest`.

## Checked and assumed

```
   checked                                 assumed
   ───────                                 ───────
   agent is refused `/clear` by name       a sent `/clear` executes rather
     (Skill tool, verbatim refusal)          than arriving as text
   wfctl holds transcript_path on Stop     `workmux wait` fires at idle
     (cli.py:4732)                           rather than mid-turn
   transcript carries occupancy            the reading is stable between
     (89,765 read live; statusline 14%)      two adjacent boundaries
   `workmux send` reaches this pane
     (probe 7731 arrived)
   the guard already allows `workmux`
   `_workmux.py` forbids subprocess
     (its own docstring)
   `stall` is the field precedent
     (_pipeline.py:355)
```

The asymmetry is the finding: everything about *deciding* is checked, and
everything about *performing* is still a bet. That is the shape of the split the
Recommended Direction describes, seen from the evidence side.

## MVP Scope

In: `_recycle.py` reading occupancy from the transcript; `recycle` on
`PipelineReport`; one event line per recycle in `events.jsonl`; orchestrate's
fifth arm rendering the three strings above; the sent form where a pane is
registered and the printed form where it is not.

Out: everything in the next section.

## Not Doing (and Why)

- **Changing what `end-session` writes** — settled, and #188 scopes it out. This
  changes when it runs, not what it says.
- **A configurable threshold** — one number, picked once, learned from. A key
  before a second repo wants a different answer is the vocabulary-before-use
  failure #121 argues against.
- **Durable runs across a dead host** — #101, behind its own entry conditions.
  This is a live session discarding its own context, which needs none of #101's
  `Run` entity.
- **wfctl shelling out to `workmux`** — would make a tool wfctl does not depend
  on a prerequisite for a pipeline step, and would put the first `subprocess`
  call in the module that documents its absence.
- **Treating this as smarter compaction** — the whole claim is that a task
  boundary is a moment someone picked and a token threshold is not.

## Open Questions

- Which number is the threshold, and measured against what denominator? The
  transcript gives occupancy in tokens; the window size is not in it. The
  statusline renders a percentage, so the denominator is known to something.
- Does `/end-session` need to run before the clear, or does the handoff it
  writes duplicate what `/start-session` re-derives? The records say only the
  prose survives, which argues for running it — but that is a claim about this
  cycle that has not been tested at a mid-run boundary.
- If a new predicate lands, #335 is in `wfctl/_predicates.py` and should rebase
  rather than conflict. Nothing here proposes one yet.

## Software design decisions

- docs/architecture/design/188-the-recycle-is-a-payload-field.md — the verdict is
  a field on `PipelineReport` shaped like `stall`, not a reason on the current
  step and not a ninth pipeline step.

Level 2 was answered with two records rather than none, and they are named in
*Boundaries and Ownership* above rather than listed here:
`wfctl-owns-the-recycle-verdict` and
`wfctl-names-the-reset-it-cannot-perform`. They are level-2 and binding once
accepted, so listing them as entries here would present them as level-3.
