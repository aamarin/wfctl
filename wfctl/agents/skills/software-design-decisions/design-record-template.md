---
status: proposed
pattern: <name of the pattern that shaped this, only when one did — delete otherwise>
supersedes: <slug of the record this replaces — delete otherwise>
---

<!-- Where this goes: <arch-root>/design/<issue>-<decision>.md, numbered for the
issue being implemented, not its epic. The filename without `.md` is the slug
other records cite in `supersedes`, which is why a record is never renamed once
approved.

Write one whenever the choice weighed credible alternatives — selecting or
rejecting a pattern counts, whether or not it draws a line or adds state. An
implementation with no credible alternative needs no record, and saying so is an
answer.

`status` runs proposed -> approved -> superseded | rejected. Only a human moves
it past proposed. Delete this comment. -->

# <the decision, as a statement — "the summary strategy is chosen at the call site, not injected">

## Context

<The concrete design pressure: what varies, what currently knows too much, what
it costs to leave alone. Link the architecture records that constrain this —
never restate them. If nothing constrains it, say so.>

## Verified

<Repository facts actually checked, one per line, each with what was read.
"`loader.py:88` loads with `glob("*.md")` — non-recursive." Not "the loader is
non-recursive." Quote what the line says, not what you remember it saying, and
list only the facts the decision rests on.>

## Assumed

<Claims still being bet on, and what would falsify each. `Verification` covers
what would confirm the structure; this covers what would break the bet. An empty
section is a claim in itself — that nothing here is a bet — so say "none" rather
than deleting it.>

## Direct baseline

<The smallest implementation that introduces no new abstraction, described
concretely enough to compare against. A baseline that is a sentence of
hand-waving justifies a decision rather than making one.>

## Decision

<What structure was chosen, in the present tense. When the baseline won, say so
here — that is a decision, not an absence of one.>

## Diagram

<Two graphs — baseline and decision — with the same components in each. A
baseline you cannot draw is one you did not consider. When the baseline won,
the second graph is the strongest alternative it beat: two identical graphs
say nothing.

Boxes are components. Draw each boundary already in force as a horizontal
divider and label it. The vertical axis is stability, not location: place a
component by how often it changes, stable above the divider and volatile below.
Durable is not stable — a file written once and edited every week is both.

Label every arrow with the relation it carries — `reads`, `writes`, `calls`. An
unlabelled arrow means "depends on", and points at what it depends on.

The divider is an ownership claim: it says which side owns the truth. A Level-3
record draws only dividers already in force. One appearing here for the first
time means the decision was Level 2 — stop, route it up, and write a Level-2
record instead.

          baseline                  decision

stable                              ┌───────────┐
                                    │ Formatter │
                                    └───────────┘
                                      ▲       ▲
════ boundary in force ═══════════════╪═══════╪════
                                      │       │
volatile  ┌────────┐   ┌──────┐     ┌─┴────┐ ┌┴─────┐
          │ Report │──►│ CSV  │     │Report│ │ CSV  │
          └────────┘   └──────┘     └──────┘ └──────┘

Then one paragraph naming what the two graphs differ by. That difference is the
argument, and the sections above cite this drawing rather than restating it —
which is what keeps a record a page and not a novel.>

## Considered

- <alternative> — <why it fell, in terms of the pressure in Context>
- <alternative> — <why it fell>

<A deliberately rejected pattern belongs here even when no pattern was used.
"Considered Strategy — one implementation, no second caller" is worth a line.>

## Consequences

<What is gained, what is now harder, and the failure mode this introduces.>

## Verification

<What would demonstrate the decision works once it is built: a test, a
measurement, a dependency check, a review question. A performance or scale claim
without a measurement is an assumption — move it to `Assumed`.>

## Log

- <YYYY-MM-DD>  proposed  — <why this was written>
- <YYYY-MM-DD>  approved  — <who approved it>
