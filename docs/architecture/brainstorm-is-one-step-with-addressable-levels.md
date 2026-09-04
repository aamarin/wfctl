---
status: proposed
---

# `brainstorm` stays one step, and the levels inside it become addressable

## Context

`_STEPS` (`_pipeline.py:21`) has eight entries, each a slash command and one
`auto` flag. The first entry runs four gates:

```
   _STEPS                        design-levels
   ──────                        ─────────────
   brainstorm                    level 1  behavior        gate
     /speckit.brainstorm    ───► level 2  architecture    gate — writes a record
     auto: False                 level 3  design          gate — writes a record
                                 level 4  implementation  gate
```

One flag governs four gates, and two of them write durable records. The step
named after the most exploratory activity in the pipeline contains the two
decisions in it that are most expensive to reverse.

The cost is not the name. It is that a routing outcome both #122's record format
and #127 emit — **"return to level 2"** — names a destination nothing can
address. `next_step_content` maps a step name to a command; there is no step
name for a level, so a caller handed that outcome cannot compute what to run.

The evidence against splitting is in the module itself, `_pipeline.py:16-20`:

> One table rather than three keyed by the same names: a step defined here
> carries both values or it does not parse. Split across separate tables,
> omitting the command was silent and severe — `next_step_content` returned
> `""`, which `next_cmd` treats as a finished pipeline, so a step with no
> command announced "story complete" with half the pipeline unrun.

#100 cites that same line refusing to split a step's command from its policy.
Any answer here has to survive that failure mode.

## Decision

`brainstorm` remains one entry in `_STEPS` with one command and one `auto` flag.
The four levels become addressable as a separate concern that a switch can name,
owned by `design-levels` rather than by the step table.

`_STEPS` keeps answering exactly one question — which command advances this
step — and gains no second axis. A per-level authority switch reads the level
vocabulary, not the step table.

The mechanism for that addressability is #127's and #151's to design. This
record fixes only which side owns the question.

## Owns truth

`design-levels` owns *"which gates run inside `brainstorm`, what each one
decides, and what returning to one means?"*.

`_STEPS` cannot compute it. Its entries are keyed by the command that advances
them, and a level is not advanced by a command — level 2 completes when a record
exists under `wfctl arch-root`, level 1 when `speckit.clarify` passes. A table
whose value type is `(command, auto)` has no way to express a gate whose exit
condition is a written artifact, so representing the levels there would mean
inventing four commands to carry four flags. That is the split
`_pipeline.py:16` records the failure of, and it would get four fresh chances to
recur.

Conversely `design-levels` cannot own the step order: it names no commands and
does not know that `specify` follows `brainstorm`.

## Considered

- **Four steps: `behavior`, `architecture`, `design` become table entries.** It
  is the direct reading of the mismatch and it makes "return to level 2" a
  plain step name, which is the cleanest possible answer to the routing problem.
  Rejected on the recorded failure: four new entries need four new slash
  commands, and wfctl already ships a skill set that does not include every
  command it names (#61). A step whose command does not ship reports "story
  complete" with the pipeline unrun, silently.
- **One step, unchanged — the four levels stay internal.** The status quo, and
  it is not incoherent: granting authority for `brainstorm` as a unit is a
  defensible policy, and the single `auto` flag then expresses it exactly.
  It loses because #127 and #122 have already committed to the finer
  granularity in their own vocabulary. "Return to level 2" is written down in a
  record format today and resolves to nothing, so the choice is between making
  it addressable and retracting it from two other designs.
- **Rename the step so the label stops misleading.** Set aside, and not because
  it is cosmetic. The level vocabulary is used 69 times across 13 files and two
  *accepted* records carry it in dated `Log` lines — `session-state-is-re-derived`
  and `wfctl-runs-the-verification` — which an accepted record's immutability
  puts out of reach. A rename would relabel the mismatch without addressing it.
- **A second flag on `_STEPS` entries, one per level.** Rejected as the shape
  #100 warns about: it puts a second axis in the table whose first axis is the
  command, and an entry could then carry level policy for a step that has no
  levels.

## Consequences

#151 and #127 unblock on the ownership question and inherit the design problem:
how a level is named and where per-level authority is stored. Neither may put it
in `_STEPS`.

`brainstorm` keeps a name that undersells what it contains. That is accepted
here rather than fixed, and the current-state view says so where a reader will
meet it.

## Log

- 2026-09-04  proposed    — #149 phase 1: `brainstorm` addressability, per #151
