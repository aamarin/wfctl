# A loop bound for speckit-orchestrate

## Problem Statement

`speckit-orchestrate` runs the pipeline as a loop: read the payload, execute
whatever `next_command` names, and the command that ran invokes orchestrate again
when it finishes. Nothing counts the passes.

While a step's predicate flips to `done` on its first pass this is invisible. It
stops being invisible for steps whose evidence comes from an agent's judgment
rather than from a file appearing — those can complete, change nothing, and leave
the step exactly as current as it found it. The loop then re-enters with the same
inputs, and does so until something external interrupts it.

Verified against a real inference run (#332): a spec with standing
`[NEEDS CLARIFICATION]` markers reports `clarify` as current, `blocked: None`,
`next_command: /speckit.clarify`. Nothing there is wrong. The pass simply cannot
finish, and nothing notices it has been asked to do so before.

## Recommended Direction

Count the passes, in wfctl, and stop after three consecutive ones that changed
nothing. A run that stops names the step that repeated and what did not move,
and hands the work to a person.

The count is not carried in the agent's memory. It is derived on every read from
the event log `wfctl resume` already appends to — one line per pass, already
carrying the step and the command. Nothing new is written to remember "I tried
this"; what is added is enough about each pass to compare two of them.

Three passes rather than one repeat: a step that legitimately takes a second run
is common, and stopping on the first repeat would fire on healthy work. Any pass
that moves something resets the count to zero.

## Boundaries and Ownership

- `docs/architecture/wfctl-counts-the-passes.md` — wfctl owns "has this run
  stopped making progress, and on which step?". The agent cannot: a run
  unattended enough to need a bound is one whose conversation gets cleared or
  compacted partway, and a session resuming the branch tomorrow has no memory of
  today's passes. Both reset the tally at exactly the moment it was meant to
  fire.

The verdict lands in the payload rather than only in orchestrate's output, so
`wfctl status` still answers "where did this get to?" once the run's scrollback
is gone. That is what separates an unattended run that stopped from one that
finished.

## Key Assumptions to Validate

- An artifact edit that changes bytes without advancing the work is rare enough
  to ignore. A step that rewrites a timestamp or reflows a heading every pass
  would reset the count forever and the bound would never fire.
- `spec_text`, `plan_text` and `tasks_text` cover every step whose progress
  matters. `decompose` reads `delivery.md` inside its own predicate, so a stall
  there is outside this fingerprint.
- Older wfctl wrote two `resume` lines per pass with identical timestamps
  (verified in the `59-deployment-key-metadata` log); current wfctl writes one.
  Counting logic has to tolerate both, or it double-counts on any branch with
  history.

## MVP Scope

1. `resume` records a digest of the artifact text beside the step it already
   logs.
2. `build_report` reads back the recent `resume` events and computes whether the
   last three passes on the current step share a digest.
3. The payload carries that verdict, with the step that repeated and what did
   not change.
4. `speckit-orchestrate` reads the verdict at step 5 and stops instead of
   emitting `EXECUTE_COMMAND`, displaying the step and the unchanged evidence.

## Not Doing (and Why)

- **An iteration cap on the whole run.** Sound and far cheaper — one integer, no
  fingerprint. A long legitimate pipeline and a stuck one are the same number, so
  the cap has to sit high enough never to fire on real work, which is high enough
  to be most of a night.
- **A per-step guard remembering that the step already ran.** Cannot be derived
  from artifacts on disk, so it would have to be written and read back —
  `session-state-is-re-derived` exists to prevent exactly that.
- **A blocking `reason` on the branch that finds open markers.** Would report
  `auto: false` for the one state `clarify` exists to handle.
- **Touching `wfctl/_pipeline.py`'s step-mode table.** #325 owns that file. This
  change reaches the same loop through `brainstorm`, automatic since #283, and
  needs nothing from it.

## Open Questions

- Whether the stop is reported as a distinct payload state or as an existing
  blocked step carrying a new reason. Either satisfies the behavior approved at
  level 1; the choice is `/speckit.plan`'s.
- Whether three is configurable. Fixed for now — a knob invites tuning the
  symptom instead of the stall.

## Software design decisions

- docs/architecture/design/332-progress-is-measured-in-artifacts.md — a pass made
  progress when the artifacts changed, not when the rendered step line changed.

Level 1 was answered in this document's behavior sections. Level 2 was answered
by the record listed under Boundaries and Ownership above.
