---
status: proposed
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

## Diagram

<Optional. Only when the relationship is materially clearer drawn than written.
Delete the section otherwise; an empty diagram section is worse than none.>

## Log

- <YYYY-MM-DD>  proposed  — <why this was written>
- <YYYY-MM-DD>  approved  — <who approved it>
