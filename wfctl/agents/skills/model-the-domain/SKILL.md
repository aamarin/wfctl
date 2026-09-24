---
name: model-the-domain
description: 'Find out what a business concept means and who owns it before a boundary is drawn — knowledge crunching over concrete scenarios, a Ubiquitous Language, Bounded Contexts and a Context Map, then the invariants and Aggregates that protect them. Use during design-levels level 2 when a core or supporting capability's complexity is in its business rules rather than its technology — rules that interact and keep growing, vocabulary the code does not have yet — or when one term is doing two jobs anywhere. Not for data entry and display with few rules, not for a generic subdomain better bought or kept simple, not for quality-attribute drivers such as latency or availability, and not for work whose language and boundaries are already settled.'
---

# Model the domain

## Overview

Domain modeling is collaborative discovery. Test the language and the
boundaries against concrete behavior, implementation feedback and contradictory
evidence. Do not start from tables, services, screens or a pattern catalog.

`design-levels` runs design as four passes: 1 behavior (what changes for the
user), 2 architecture (what moves, and who owns the truth), 3 design (how it
is structured), 4 implementation (the code). This skill is one of two methods
at level 2:

```
design-levels               model-the-domain              architecture-decisions
routes by whether the  ───► language → contexts →    ───► writes one proposed record
capability earns it         invariants
                                  │
                                  └─ a crossing that carries a quality driver
                                          ▼
                                   architecture-design
```

`.agents/skills/design-levels` sends a question here from its level-2 gate
when the capability it touches **earns domain modeling** (below), or when a
term is doing two jobs whatever the capability. Everything else at level 2 goes
to `.agents/skills/architecture-design` instead: a **quality** under stated
conditions, and ownership in a capability whose rules are simple. When a
modeled capability also contests a quality, this skill runs first: the driver
loop cannot rank a part nobody has agreed a name for. The routing is the record
`level-2-routes-by-what-is-contested`.

It does not write `design.md`, define gate verdicts, or accept a record.

## Does this capability earn it?

Ask it of the **capability**, not of the question, and start by finding the
core product. Both books place domain modeling where the business is complex
and distinctive and withhold it elsewhere, so the first job is saying which
part is distinctive. Evans treats the alternative as a fork taken at the outset
(*Isolating the Domain*, "The Smart UI Anti-Pattern"), so the answer holds for
every later question in the capability until something on the *What reopens a
model* list changes it.

**Find the core first.** Put these to the person who knows the product, and
write the answers down — they are the value proposition, and nothing else in
the pipeline records it:

1. What does this product do that a customer could not get elsewhere? That
   part is the Core Domain: "distinctive and central to the purposes of the
   intended applications" (Evans, *Distillation*, "Core Domain"); where the
   organization "must excel" (Vernon, *Strategic Design with Subdomains*,
   "Types of Subdomains").
2. If this capability were bought off the shelf tomorrow, what would be lost?
   Nothing distinctive makes it a **generic subdomain** — buy it, reuse a
   published model, or keep it simple (Evans, "Generic Subdomains"; Vernon).
3. Does it need custom work only because nothing off the shelf fits, while
   the product would not suffer from a plain build? That is a **supporting
   subdomain** — custom, but not the heavy investment (Vernon).
4. Does this part keep changing because new rules about it keep being
   discovered, or is it built once and left alone? Ask it with one example of
   each from the product itself — put abstractly ("will you keep learning
   here?") it did not land the first time it was asked. Vernon's test: if
   that long-term commitment cannot be made, is the model
   "truly a strategic differentiator, a Core Domain?"
   (*Strategic Design with Bounded Contexts and the Ubiquitous Language*).
5. Can the value be said in about a page, leaving out everything that does not
   distinguish it? That page is Evans' **domain vision statement**: "Write a
   short description (about one page) of the CORE DOMAIN and the value it will
   bring … Ignore those aspects that do not distinguish this domain model from
   others. … Write this statement early and revise it as you gain new insight."
   (*Distillation*, "Domain Vision Statement").

Evans' own example draws the line: a passenger model that reflects the
relationship an airline builds with repeat customers is in the statement; a
five-second confirmation and a cached animated logo are "important" and are
not. The second kind are qualities, and qualities go to `architecture-design`.

**Then read the signals** for the capability the question touches:

| Signal | Earns it | Does not |
| --- | --- | --- |
| Subdomain (the questions above) | Core; supporting, at lighter depth | generic |
| Where the complexity is | in the business rules — "the business model is more complex than the technical aspects" (Vernon) | in the technology — latency, scale, integration plumbing |
| What the work is | rules that interact, and keep growing | "simple functionality, dominated by data entry and display, with few business rules" (Evans) |
| How the rules sit in code | one rule has to hold across several operations | each rule lives in one screen or one call |
| The language | the people who know the domain use terms the code does not have | the code's names are the business's names, and nobody disputes them |

A core or supporting subdomain plus one more signal on the left earns a
round; the subdomain alone does not. One term doing
two jobs earns a round on its own, in any capability: that is a broken
language, and a simple capability can have one. The right column throughout is
`architecture-design`, or no level-2 method at all when no boundary moves.

Depth follows the subdomain. The Tactical depth below is for the core — Evans:
"Justify investment in any other part by how it supports the distilled CORE".
A supporting subdomain gets Explore or Strategic.

The answers land in the model document's *Domain vision statement* and
*Decision frame*, so the next question in the capability starts from them
rather than asking again.

## When to use

Once a capability earns it, these are the questions that come here:

- A term means different things to different people, screens or modules.
- A rule or invariant exists and nobody can say which side enforces it.
- Two parts of the system hold what they call the same fact, and it is not
  one fact.
- A new capability arrives whose vocabulary is not in the code yet.
- A rule is about to be written a second time, in a second operation.

A screen is evidence, not a starting point. UI copy is where a broken language
shows up for a user. `design-levels`' level-2 example — an empty *filter
window* and an empty *workspace* rendered as one state — is one term doing two
jobs. It belongs here first, even though it ends in an ownership decision about
who computes "is this workspace empty?".

**Not for**: bug fixes, copy edits, refactors that move no boundary, or work
whose language and boundaries an accepted record or spec already settles. Not
for a capability the table above leaves in the right column. Not for quality
drivers, which go to `architecture-design`. Not for how code
expresses a settled model, which is `.agents/skills/clean-code`.

## Authority

- Accepted records outrank this method. Read them with `wfctl arch context`.
- The agent proposes. **A person decides** whether a record is accepted, and
  agent confidence does not stand in for someone who knows the domain.
- **Never invent domain truth.** Escalate contradictions, ownership disputes and
  irreversible boundary choices.
- **No verdicts and no waivers.** `design-levels` owns every gate.
- An output that does not apply is a `none — <reason>` row in the model
  document. A boundary that does not apply is `wfctl arch none`.
- Keep observed evidence, proposed model, decided record and open question
  apart. A decided claim links to its record and is never restated.

## Load what the task needs

| You need | Read |
|---|---|
| to run a round end to end | [references/process.md](references/process.md) |
| to choose a construct or name a Context Map relationship | [references/ddd-heuristics.md](references/ddd-heuristics.md) |
| to draw a Context Map, timeline or Aggregate | [references/visual-language.md](references/visual-language.md) |
| to judge whether a claim is strong enough to hand on | [references/evidence.md](references/evidence.md) |
| to write the durable model | copy [domain-model-template.md](domain-model-template.md) |
| which book chapter a reference carries | [references/source-map.md](references/source-map.md) |

## Select the depth

Depth sets how much of the loop runs. It never picks between this skill and
`architecture-design`.

| Depth | Use when | Smallest output | `process.md` sections |
| --- | --- | --- | --- |
| Explore | the problem or the language is unclear | scenarios, language tensions, one sketch, questions | 1–2 |
| Strategic | scope, ownership or integration changes | contexts, Context Map, a record or `wfctl arch none` | 1–3, 5–6 |
| Tactical | rules or transaction boundaries change | invariants, Aggregate candidates, code feedback | 1–2, 4–6 |
| Review | a model already exists | evidence trace, challenged assumptions, corrected sketches | whichever the model covers |

A question that straddles two rows takes the one that runs fewer sections,
and deepens only when a question stays open. Every row but Explore ends at §6,
which is where the model document is written; §5 is skipped only by Explore,
which `evidence.md` lets skip implementation feedback and nothing else does.

## Run the loop

1. **Frame the decision** the round supports. Keep problem and solution apart.
2. **Gather evidence** — conversations, policies, screens, data, code, tests,
   incidents, records, a published or neighbouring model of the same domain —
   labelled by source.
3. **Crunch scenarios**: happy path, failure, timing, correction. Mark hotspots.
4. **Build the language**: meaning per context, synonyms, forbidden meanings.
5. **Find the contexts** around cohesive language, rules, ownership and rate of
   change — not around modules, services or teams by default.
6. **Map the relationships** — facts first, then the name.
7. **Model consistency**: invariants before Aggregates, the smallest boundary
   that protects each one.
8. **Test the model** against scenarios, code or a thin spike. What contradicts
   a boundary — now or during implementation — reopens level 2 through
   `design-levels`' *The descent is not one-directional*. It does not quietly
   edit the model to match the code.
9. **Distill**: remove what explains nothing, name the Core Domain.
10. **Hand off**, below.

Repeat 3–9 until the scenarios read naturally in the language and the code
shows no material contradiction. `references/process.md` has each step in full.

## Close and hand off

For each question the round was asked, do exactly one of these:

- **No boundary moved** → a `none — <reason>` row in the model document.
  `wfctl arch none` is for the change, not the question: it writes one
  declaration that the whole branch draws no boundary, so run it only when no
  question in the round moved one and nothing else in the change did either.
  Beside a record it is a false claim.
- **Evidence is missing** → name what and who could answer it, and stop.
- **A crossing carries a quality driver** → hand it to `architecture-design`.
  Do not rank drivers here.
- **A boundary with no quality in contention** → hand one proposed ownership
  decision to `.agents/skills/architecture-decisions`. An invariant whose owner
  crosses a context is one of these. The record needs what `architecture-design`
  would otherwise have produced, and the round already has it: the **direct
  baseline** is the language as it stood before the round — one term, one
  owner, nothing split — and **Considered** is the context splits step 5
  weighed and did not take. A round that weighed no second split has not found
  a boundary yet; it is the *evidence is missing* stop.

An Aggregate's internal shape inside one context is **level 3**:
`.agents/skills/software-design-decisions` when alternatives were weighed,
nothing when they were not.

## Where the model lands

`<arch-root>/domain/<capability>.md` — ask `wfctl arch-root` for the parent.
Not `FEATURE_DIR`, which a reviewer never opens, and not beside the records,
the one tier every reader of the arch root takes as decided. `domain/` is excluded from
the design gate on purpose: the document describes, and only the record or
`wfctl arch none` answers level 2.

The core-product answers are the exception, because they are about the
product rather than one capability: they land once, in `domain/vision.md` — the
vision statement and a Subdomains table with one row per capability — and each
capability's model links to it instead of restating it. That page is
deliberately the lighter artifact; the full template is for a capability that
earned a model. wfctl's own is the worked example.

Sketches are ASCII while you answer and mermaid in the document and the record —
`design-levels`' rule. `references/visual-language.md` says what each one shows.

## Failure modes

- Starting from entities, schemas, services or screens before behavior.
- Treating a pattern name or an Event Storming color as a conclusion.
- One glossary for the whole enterprise, erasing contextual meanings.
- One Aggregate per table, one context per microservice.
- A polished diagram hiding an `inferred` claim.
- Restating a record in the model document.

## Verification

- [ ] Every item under `references/evidence.md` *Before handing off* is answered,
      or has a `none — <reason>` row.
- [ ] Each question ended in exactly one of the four hand-offs.
- [ ] The model document is under `<arch-root>/domain/`, links its records, and
      restates none of them.
- [ ] No verdict was produced and no record was accepted.
