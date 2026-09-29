---
name: python-pattern-selection
description: 'Choose the Python mechanism an implementation reaches for once its boundary is already settled — a callable before a Strategy hierarchy, a session transaction before a Unit of Work. Use during design-levels level 4, while writing Python and a pattern name arrives before the pressure that would justify it. Not for drawing or moving a boundary, not for deciding who owns a piece of truth, and not a design loop.'
---

# Python pattern selection

## Overview

This skill fires at the moment an implementer picks a mechanism, which is the
moment no other skill in this tree is awake for.

`design-levels` sends level 4 to `verification-before-completion` and
`code-review`. Both fire after the code exists — one when work is claimed
complete, the other before a merge. A Strategy hierarchy that should have been a
function is caught by `code-review`'s over-engineering lens, as rework, and only
when a review actually runs.

```
boundary settled
      │
      ▼
  ┌────────────────────────────────────────────────┐
  │  pick the mechanism   ◄── this skill           │
  └────────────────────────────────────────────────┘
      │
      ▼
  claim complete ──► verification-before-completion
      │
      ▼
  before merge   ──► code-review  (over-engineering lens)
```

`level-4-owns-pattern-selection` is the accepted record behind that placement.

## When to Use

Use it while writing Python, when:

- a pattern name arrives before the pressure that would justify it;
- an interface is about to be added, and the only caller that needs it is a test;
- a wrapper is about to be added around something that already works — a
  Repository over a session, a Factory over a constructor;
- a change introduces process-wide state, retries, caching, or a message bus.

**Not for**: drawing or moving a boundary, deciding who owns a piece of truth, or
work whose structure is still open. Those are level 2 and level 3 — use
`.agents/skills/design-levels` to find out which, and it will route you.

This skill assumes the boundary is settled. If you are not sure it is, it is not,
and this is the wrong skill.

## Authority

- Project instructions and accepted architecture records outrank these
  constraints. Read the in-force set with `wfctl arch context`.
- **This skill mints no verdict vocabulary and grants no waiver.** It produces no
  pass, no fail, and no outcome class. `design-levels` owns the gates.
- **It runs no design loop.** Ranking drivers and comparing credible approaches
  is `.agents/skills/architecture-design`'s method, and running a second one here
  would mean an agent that loads both does the same work twice.
- **It routes to neither record skill.** A choice that draws a boundary goes to
  `.agents/skills/architecture-decisions`; one that weighed credible alternatives
  and drew no boundary goes to `.agents/skills/software-design-decisions`.
  Neither routing is this skill's to make, and filing a level-4 note in either
  puts an implementation note where a reader is looking for a binding decision.
- A constraint below is a default, not a rule. Departing from one is fine, and
  **the departure is what gets written down.**

## Writing down a departure

A constraint here names the cheaper shape. Choosing the expensive one is a
decision, and it is the reasoning nobody can reconstruct from the code later —
the wrapper is visible, the invariant it exists to hold is not.

Where it goes turns on whether anyone would go looking for it:

```
departed from a constraint
      │
      ├─ a one-off, nobody would look it up later
      │     └─► the commit message. Name the pressure.
      │
      └─ deliberate, and the next reader of this code will ask why
            └─► <arch-root>/implementation/<issue>-<slug>.md
                  what the cheaper shape was, what it could not hold,
                  what the expensive one costs
```

The pressure that justified the expensive shape is usually a size; the number of
backends, callers, or rules. When it is, the note says what that size is today
and at what size the cheaper shape stops holding. Where the two are close, draw
the cost of each shape over that size and mark where they cross; it is the one
drawing an implementation note ever needs, and it is the argument the next
reader will want when the size changes.

`wfctl arch-root` prints the parent; a repo can declare it elsewhere, so ask
rather than writing `docs/architecture` in. The file is prose, not a form — it
carries the three things above and stops.

**`implementation/` is a sibling of `design/`, and the two are told apart by
whether an alternative was weighed** — not by what the thing is. A Repository
wrapper over an ORM session is a structural choice and a mechanism choice at
once, so naming the subject settles nothing. If two approaches were compared and
one won on a stated criterion, there is a loser to write down and it is a level-3
record under `design/`, written with `.agents/skills/software-design-decisions`.
If a constraint above named the cheaper shape and a pressure overrode it, there
is no loser — only a default you walked away from — and it lands here.

That definition is stated here rather than only in a record because the record
does not travel: `install-skills` mirrors the skills tree into a project and
never `docs/architecture/`, so a repo that installs this skill receives the
instruction and no definition of the shelf.

**Name the file and the symbol in its first line.** Without that the note is
reachable only by a reader who already knows the shelf exists and guesses the
issue number, which is less than `git blame` gives them for free.

**This is not a verdict and not a gate.** Nothing here blocks on the file
existing, and writing one grants no waiver. `design-levels` still owns every
gate.

The reasoning behind the shelf is `level-4-reasoning-gets-its-own-shelf` in
wfctl's own arch root, which is `proposed` and therefore not in force — so it is
cited as an argument someone can read, never as authority. Nothing above depends
on its status: the convention is stated here in full, and a repo that prefers a
different destination is choosing between two shelves rather than disobeying a
record.

## Pattern selection constraints

Each one names the cheaper shape first. The expensive shape earns its place by a
pressure you can state, not by the name being familiar.

- Prefer a function or callable before a Strategy or Template Method class
  hierarchy.
- Prefer direct construction and named arguments before Factory or Builder
  machinery.
- Prefer an explicit call before an event, observer chain, or message bus.
- Treat an ORM session transaction as a viable baseline before adding Repository
  or Unit of Work wrappers.
- Add a rich domain model only for meaningful behavior and invariants, not for
  CRUD ceremony.
- Define an aggregate from a consistency invariant, not from an object graph or a
  database relationship.
- Separate command intent from event facts when messaging is justified.
- Keep in-process dispatch distinct from durable cross-process delivery.
- Consider ordinary query code before CQRS and a separate read store.
- Reject hidden Singleton access. Give a process-wide dependency an explicit
  construction and lifetime owner.
- Do not conclude microservices from code size, several clients, several
  functional areas, or database access alone.
- Require measured pressure before caching, Flyweight, or other
  performance-oriented complexity.
- Treat retry, circuit breaker, throttling, and cache-aside as operational
  policies with explicit failure and observability costs, not as decorators to
  add by habit.

The first two constraints follow from Python itself. Functions are first-class
values, so a Strategy can be a callable and a Command can be a function, and
named parameters remove the telescopic constructor problem a Builder solves in
other languages (Ayeva and Kasampalis, *Mastering Python Design Patterns*, pp.
27, 119, and 152). The Singleton and microservices constraints depart from the
same book, which offers global state and several clients as reasons to reach
for them.

Most of these constraints are the costs Percival and Gregory list in
*Architecture Patterns with Python*, at the end of the chapter that builds each
pattern; the Repository and domain model in chapter 2, Unit of Work in chapter
6, Aggregates in chapter 7, the message bus in chapters 8 - 10, event
integration in chapter 11, CQRS in chapter 12, and dependency injection in
chapter 13. The book adopts every one of those patterns, and it does so only
after the simpler code in front of it has failed. That order is the one this
skill asks for.

## Red flags

Each of these is a sign the mechanism was chosen before the pressure was named.
Finding one is not a verdict — it is a question to answer in the change itself.

- The pattern name appears before the pressure.
- Every application receives the same layered folder structure.
- Interfaces are added only to enable mocks.
- A fake is assumed equivalent to the real adapter without contract evidence.
- Domain objects import the web framework, ORM, broker, or transport types
  without an accepted reason.
- Controllers contain duplicated business rules or transaction policy.
- A repository mirrors every ORM method and leaks query details.
- An aggregate is chosen from table relationships rather than from consistency.
- A message bus hides a call graph that would be clearer explicitly.
- An external publish is treated as atomic with a database commit without a
  delivery design.
- Events, retries, or decorators hide failure and ordering semantics.
- `pickle` is used for untrusted or durable external data.
- A process-wide dependency is reached through hidden global state.
- "Pythonic" is used as a substitute for a trade-off.

The last one is the one that survives review most often, because it sounds like a
reason. It names a preference for a shape; a trade-off names what the shape costs
and what it buys. If a choice is defended as Pythonic and the sentence cannot be
rewritten to say what it buys, the pressure was never found.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The pattern is standard, so it needs no justification." | Standard says other people had this pressure. It does not say you do. |
| "The interface makes it testable." | A test that needs an interface no caller needs is testing the interface. Check whether the real adapter has a contract test instead. |
| "We'll need the abstraction later." | Later is when it is cheap to add, because the pressure will be visible. Now it is a guess with a maintenance cost. |
| "A Repository keeps the ORM out of the domain." | Sometimes. It also duplicates the session's API and leaks queries. Name the invariant the session cannot hold. |
| "It's only one more layer." | Layers compose multiplicatively for the reader, not additively. |

## Verification

Before the change is done:

- [ ] Every pattern in the change has a stated pressure, and the pressure was
      checked rather than assumed.
- [ ] The cheaper shape named in the constraint above was considered and the
      reason it lost is stateable.
- [ ] No interface exists whose only consumer is a test.
- [ ] Every process-wide dependency has an explicit construction and lifetime
      owner.
- [ ] No performance-oriented structure was added without a measurement.
- [ ] No verdict, gate, or waiver was produced by this skill.
- [ ] Every departure from a constraint above is written down — in the commit
      message, or under `<arch-root>/implementation/` if the next reader of this
      code would ask why.
