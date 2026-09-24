---
name: model-the-domain
description: 'Find out what a business concept means and who owns it before a boundary is drawn — knowledge crunching over concrete scenarios, a Ubiquitous Language, Bounded Contexts and a Context Map, then the invariants and Aggregates that protect them. Use during design-levels level 2 when what is contested is the meaning or ownership of a concept: one term doing two jobs, an invariant with no home, a rule nobody can say who enforces. Not for quality-attribute drivers such as latency or availability, not for routine implementation, and not for work whose language and boundaries are already settled.'
---

# Model the domain

## Overview

Domain modeling is collaborative discovery. Test the language and the
boundaries against concrete behavior, implementation feedback and contradictory
evidence. Do not start from tables, services, screens or a pattern catalog.

This skill is one of two methods at level 2:

```
design-levels               model-the-domain              architecture-decisions
routes by what is      ───► language → contexts →    ───► writes one proposed record
contested                   invariants
                                  │
                                  └─ a crossing that carries a quality driver
                                          ▼
                                   architecture-design
```

`.agents/skills/design-levels` sends a question here from its level-2 gate
when what is contested is a **meaning** — one term doing two jobs, an invariant
with no home, a rule nobody can say who enforces. A **quality** under stated
conditions goes to `.agents/skills/architecture-design` instead. When both
apply, this skill runs first: the driver loop cannot rank a part nobody has
agreed a name for. The routing is the record
`level-2-routes-by-what-is-contested`.

It does not write `design.md`, define gate verdicts, or accept a record.

## When to use

- A term means different things to different people, screens or modules.
- A rule or invariant exists and nobody can say which side enforces it.
- Two parts of the system hold the same fact and disagree about who owns it.
- A new capability arrives whose vocabulary is not in the code yet.

A screen is evidence, not a starting point. UI copy is where a broken language
shows up for a user: an empty *filter window* and an empty *workspace*
rendered as one state is one term doing two jobs.

**Not for**: bug fixes, copy edits, refactors that move no boundary, or work
whose language and boundaries an accepted record or spec already settles. Not
for quality drivers, which go to `architecture-design`. Not for how code
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

| Depth | Use when | Smallest output |
| --- | --- | --- |
| Explore | the problem or the language is unclear | scenarios, language tensions, one sketch, questions |
| Strategic | scope, ownership or integration changes | contexts, Context Map, a record or `wfctl arch none` |
| Tactical | rules or transaction boundaries change | invariants, Aggregate candidates, code feedback |
| Review | a model already exists | evidence trace, challenged assumptions, corrected sketches |

## Run the loop

1. **Frame the decision** the round supports. Keep problem and solution apart.
2. **Gather evidence** — conversations, policies, screens, data, code, tests,
   incidents, records — labelled by source.
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

- **No boundary moved** → `wfctl arch none --reason "<why>"`.
- **Evidence is missing** → name what and who could answer it, and stop.
- **A crossing carries a quality driver** → hand it to `architecture-design`.
  Do not rank drivers here.
- **A boundary with no quality in contention** → hand one proposed ownership
  decision to `.agents/skills/architecture-decisions`. An invariant whose owner
  crosses a context is one of these.

An Aggregate's internal shape inside one context is **level 3**:
`.agents/skills/software-design-decisions` when alternatives were weighed,
nothing when they were not.

## Where the model lands

`<arch-root>/domain/<capability>.md` — ask `wfctl arch-root` for the parent.
Not `FEATURE_DIR`, which a reviewer never opens, and not beside the records,
where `wfctl arch context` would read it as agreed. `domain/` is excluded from
the design gate on purpose: the document describes, and only the record or
`wfctl arch none` answers level 2.

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
