---
status: <proposed | approved | superseded | rejected — starts proposed; only a human moves it past that>
classification: <simple-design | named-pattern | novel-design>
pattern: <name, only when classification is named-pattern — delete otherwise>
supersedes: <slug of the record this replaces — delete otherwise>
---

# <the decision, as a statement — "the summary strategy is chosen at the call site, not injected">

## Context

<The concrete design pressure: what varies, what currently knows too much, what
it costs to leave alone. Link the architecture records that constrain this —
never restate them. If nothing constrains it, say so.>

## Verified

<Repository facts actually checked, one per line, each with what was read.
"`_arch.py:145` loads with `glob("*.md")` — non-recursive." Not "the loader is
non-recursive.">

## Assumed

<Claims still being bet on, and how each would be tested. An empty section is a
claim in itself — that nothing here is a bet — so say "none" rather than
deleting it.>

## Direct baseline

<The smallest implementation that introduces no new abstraction, described
concretely enough to compare against. This section is mandatory and it is not a
formality: a record whose baseline is a sentence of hand-waving has justified a
decision rather than made one.>

## Decision

<What structure was chosen, in the present tense. When the baseline won, say so
here — that is a decision, not an absence of one.>

## Diagram

<Mandatory, and it sits here because it settles the comparison the two sections
above set up. Both graphs, the same components in each. Boxes are components,
arrows point at what they depend on.

The vertical axis is **stability, not location**: stable above, volatile below.
Something durable is not thereby stable — a file written once and edited every
week is durable and volatile both. Place a component by how often it changes.



The line is not decoration. Where it sits is a claim about who owns the truth
on either side, so a line that appears here for the first time means the
decision was Level 2 — route it up and write a Level-2 record instead, because
`Owns truth` is a Level-2 section. A Level-3 record draws only lines already in
force.

Arrows crossing upward are the design working. A baseline you cannot draw is
one you did not consider.

The drawing carries the structure. The sections above cite it and must not
restate it in prose — that is what keeps a record a page and not a novel.>

## Considered

- <alternative> — <why it fell, in terms of the pressure in Context>
- <alternative> — <why it fell>

<A deliberately rejected pattern belongs here even when the result is
simple-design. "Considered Strategy — one implementation, no second caller" is
the record's most reusable line.>

## Consequences

<What is gained, what is now harder, and the failure mode this introduces. Two
liabilities minimum; a change with no cost was not a decision.>

## Verification

<What would demonstrate this works and expose the failure modes: tests,
measurements, a dependency check, a review question. A performance or scale
claim without a measurement is an assumption — move it to Assumed.>

## Log

- <YYYY-MM-DD>  proposed  — <why this was written>
- <YYYY-MM-DD>  approved  — <who approved it>
