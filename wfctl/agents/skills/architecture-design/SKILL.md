---
name: architecture-design
description: 'Run one driver-to-structure architecture design iteration and hand a proposed boundary decision to architecture-decisions. Use during design-levels level 2 when a feature may draw or move a component boundary, ownership rule, public contract, data boundary, or deployment relationship, or when it must preserve a quality under stated conditions. Not for diff review, implementation verification, local pattern selection, or work whose boundaries are already settled.'
---

# Architecture design

## Overview

Turn **what must remain true** into a proposed structural decision. Elicit and
rank the drivers for one iteration, compare credible approaches, draw the
responsibilities and crossings, and analyze the result before a boundary is
accepted.

This skill runs inside `design-levels` level 2, before
`architecture-decisions`:

```
design-levels              architecture-design          architecture-decisions
selects level 2       ───► driver → structure loop ───► writes one proposed record
owns the level gates       proposes; never accepts      owns the durable decision
```

It does not write `design.md`, run verification, review a diff, define gate
verdicts, or accept a record. An observation is not policy: a dependency graph
can find a cycle, but only an accepted decision can say which property that
cycle violates.

## When to use

Use this skill when level 2 is active and the change may:

- draw, move, remove, or expose a component or deployment boundary;
- assign or move authority for state, a derived value, or persisted data;
- establish or change a public API, protocol, event, or compatibility promise;
- introduce coupling whose failure, release, scaling, or ownership consequences
  cross components;
- depend on a quality such as availability, latency, security, modifiability,
  deployability, or integrability under specific conditions.

File size, unfamiliar code, a named pattern, or an unfavorable metric is not by
itself an architecture question.

If the change is local and preserves every existing boundary and contract,
declare **no architecture decision** and return to `design-levels`. A declared
absence is the result; do not manufacture a boundary to complete the method.

## Authority

- Project instructions and accepted architecture records outrank this method.
- Read the in-force set through `wfctl arch context`; do not treat proposed,
  rejected, retired, or superseded records as binding.
- The agent may derive observations, compare options, and draft a proposal. A
  human decides whether a proposed record becomes accepted.
- Unknown driver priority or conflicting accepted constraints requires a human
  answer. Do not assign equal weights or quietly choose one.
- This skill consumes the gate and inconclusive-evidence rules owned elsewhere.
  It does not mint a verdict vocabulary or grant a waiver.
- Escalation is always available; waiving required review is not.

## Inputs

Before choosing structure, gather only what this iteration needs:

1. The behavior already agreed at level 1.
2. Project instructions and the accepted records from `wfctl arch context`.
3. The current-state architecture view, if the repository has one. Locate it;
   do not assume a path.
4. Relevant code, contracts, deployment facts, and constraints checked against
   the repository rather than recalled.
5. Open questions and assumptions that could change the boundary.

For greenfield work, declare that there is no current structure. In an existing
system with no trustworthy current-state view, establish only the affected
boundary from checked repository evidence. If the decision depends on structure
outside that verified scope, name the missing input and stop. Do not infer a
whole architecture from directory names.

## Run one iteration

One iteration answers one architectural question. Do not design the whole
system because one boundary is open.

### 1. State the iteration goal

Write one sentence naming:

- the element or boundary being designed;
- the drivers this pass must address;
- the decision this pass must make.

If the sentence contains several independent decisions, split them and run one
at a time.

### 2. Elicit and rank the drivers

A driver must be specific enough to be disproved. Capture the smallest fields
that make the pressure concrete:

```
driver
  stimulus       what happens or changes
  condition      the operating state in which it happens
  affected part  the element or boundary under pressure
  response       what the system must do
  criterion      how someone could tell whether it did
  source         checked evidence or named stakeholder assumption
```

Constraints may instead state a choice the design is not free to make and its
source. Do not turn every desirable quality into a driver.

Rank the drivers **for this iteration** and explain the ordering. Keep only the
few that can change the decision. "Must be scalable," "must be maintainable,"
and an unranked list of `-ilities` are not usable inputs.

When no honest numeric threshold exists, use an observable review criterion.
Do not invent a number merely to make the driver look measurable.

### 3. Compare credible approaches

Compare at least two approaches that could actually satisfy the behavior. One
must be the current or direct **no-new-structure baseline**. If literally doing
nothing cannot satisfy the required behavior, say so; an impossible option is
not a credible alternative.

For each approach, state:

- responsibilities and their owners;
- structures or interfaces added, removed, or changed;
- which ranked drivers it addresses and which it compromises;
- the property gained;
- at least two material liabilities or costs;
- checked evidence, assumptions, and the cheapest way to resolve uncertainty;
- what makes the choice hard or easy to reverse.

Use patterns, tactics, frameworks, or platform features only when they explain a
real structural choice. A pattern name is vocabulary, not an argument. Do not
consult or create a catalog merely to fill this step.

If no known concept fits, there are two honest outcomes:

- choose the direct design because more structure earns no property the drivers
  require; or
- escalate because the problem is significant and the available approaches do
  not satisfy the ranked drivers.

Never invent an abstraction as a third outcome.

### 4. Draw responsibilities and crossings

For each credible approach, show:

- which side owns each responsibility or piece of truth;
- why the other side cannot compute or own it;
- what crosses the boundary, in which direction, and under whose contract;
- failure, release, data, and deployment coupling when they affect a driver.

Follow `design-levels` rendering rules: a compact ASCII boundary sketch, not
Mermaid and not a table chosen by default. Label current and proposed views.
Arrows mean only actual crossings; state their meaning if it is not obvious.

Do not place schemas, classes, functions, or implementation machinery into the
sketch unless one is itself the public boundary being decided.

### 5. Analyze against the drivers

Walk the ranked drivers through the proposed structure:

- Does the response criterion still hold in the stated condition?
- Which claim was checked against code, a contract, measurement, or accepted
  record?
- Which claim remains an assumption?
- What could falsify the recommendation?
- Did a lower-level finding invalidate behavior or an existing boundary?

Performance, scale, latency, availability, and cost claims require measurement
or remain explicitly marked assumptions. A metric is diagnostic evidence; it
does not choose the architecture.

If a finding invalidates an earlier level, return to that level and revise. Do
not work around the contradiction inside this iteration.

### 6. Close and hand off

Recommend one approach only when the evidence supports it. Present:

```
iteration goal
ranked drivers
current/direct baseline
credible alternatives and trade-offs
proposed boundary sketch
checked evidence | assumptions | open questions
recommended decision and why
```

Then do exactly one of the following:

- If no boundary was drawn or moved, declare **no record** and return to
  `design-levels`.
- If evidence is missing, name what must be checked and pause or escalate under
  the existing gate policy.
- If a boundary is proposed, invoke `.agents/skills/architecture-decisions` and
  hand it one proposed ownership decision. That skill resolves `wfctl
  arch-root`, writes the record, and owns its status lifecycle.

Drivers remain feature-local design input until promotion. Where they land is
`.agents/skills/design-levels`' "Where the levels land", not this skill's to
decide: levels 1 and 3 land in `specs/<branch>/design.md`, level 2 lands in a
record under `wfctl arch-root`. Carry the ranked drivers there in context, and
pass only the decision-specific rationale to the record. Do not create a
separate drivers artifact or restate the full decision in two places.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "All of these qualities are high priority." | Then none is prioritized. Ask which failure costs more in this iteration. |
| "The pattern solves the architecture." | A name does not show which driver it satisfies or which coupling it introduces. |
| "We can document the current architecture while proposing the new one." | That makes an unverified inference the baseline. Establish current state first. |
| "The metric is bad, so the boundary must move." | A metric is evidence. Only drivers and accepted constraints make the choice. |
| "The direct solution has no architecture." | Preserving the current boundary can be the correct architectural decision. |
| "We can write the record after implementation." | Then it describes what happened instead of constraining what happens next. |
| "The answer is obvious, so I can accept it." | Obviousness does not transfer authority from the human to the proposing agent. |

## Verification

Before handing off from this skill:

- [ ] The question is architecture-significant, or its absence was declared.
- [ ] The current-state view and accepted records were read, or missing evidence
      stopped the iteration.
- [ ] The iteration has one goal and one decision.
- [ ] The few drivers that can change the decision are specific and ranked.
- [ ] At least two credible approaches were compared, including the direct
      no-new-structure baseline.
- [ ] Every approach names the property gained and at least two material
      liabilities.
- [ ] Responsibilities, ownership, and actual boundary crossings are visible.
- [ ] Evidence, assumptions, and open questions are separated.
- [ ] No pattern, abstraction, threshold, or artifact was invented to complete
      the method.
- [ ] The skill produced no verification verdict and accepted no decision.
- [ ] A proposed boundary was handed to
      `.agents/skills/architecture-decisions`, or **no record** was explicitly
      declared.
