# What a DDD sketch shows

This file says what to draw. It does not say in which format: while an answer is
being given the sketch is ASCII, and in a record or a domain document it is
mermaid. That is `design-levels`' rule, and a record's drawing is also governed
by `the-drawing-is-required-at-acceptance` and
`the-author-declares-the-diagram-kind`.

A sketch in this skill is one of two things, and the reader has to be able to
tell which. A model sketch shows the structure the code follows or will follow;
its boxes are terms from the Ubiquitous Language, and a record can draw the
same thing. An explanatory sketch teaches the domain; it can show what the code
never models, such as a timeline of what a person does in a day, and it uses a
notation that does not look like the code's structure so that nobody mistakes
it for one (Evans, *Domain-Driven Design*, ch. 2, "Explanatory Models"). Label
an explanatory sketch as one in its caption.

## Every sketch answers a named question

Say the question before the sketch and the conclusion or open tension after it.
A sketch with no question in front of it is decoration, and a polished one hides
uncertainty.

When a boundary moves, keep the before and after sketches both, rather than
replacing the first. The first one is the evidence of what was learned.

## Context Map

Draw each context as a container, with the language or capability it owns
inside it. Label each relationship with its direction and the semantic mechanism
— a published contract, a translation, a conformist dependency.

```
┌─ Sales context ─┐                        ┌─ Billing context ─┐
│ Quote           │ ── AcceptedQuote v1 ─► │ Invoice           │
└─────────────────┘    published language  └───────────────────┘
```

- Never overlap two containers unless a Shared Kernel has actually been agreed.
  Overlap implies shared ownership.
- Draw an Anticorruption Layer as a named translation boundary of its own, not
  as a label on an arrow.
- Keep the team relationship and the runtime transport out of the drawing and
  in the companion table. They change for different reasons.

| Relationship | Upstream | Downstream | Team relationship | Translation owner | Mechanism | Consistency |
| --- | --- | --- | --- | --- | --- | --- |

## Event timeline

Business time runs one way, left to right or top to bottom. An actor is a noun,
a command is an imperative, an event is a past-tense fact, a policy is a
decision phrase, and a hotspot is an explicit question.

```
Owner ─► Approve invoice ─► Invoice approved ─► ⟨payment policy⟩ ─► Schedule payment
                                                        ?  what if the invoice is disputed
```

## Aggregate and its invariants

Draw the transaction boundary explicitly. Only the root and what it owns go
inside. Another Aggregate is shown by its identity, outside the line. Attach
each invariant to the boundary or the behavior that enforces it.

```
┌─ Booking Aggregate ─────────────────────┐
│ Booking (root)                          │
│   └─ Seat hold ── Seat number (value)   │   ··· venue id ···► Venue Aggregate
│ enforces: at most ten holds             │
│           no hold added once confirmed  │
└─────────────────────────────────────────┘
```

Every invariant inside the line is decided from data inside the line. A rule
that needs data from outside — "no seat held by two Bookings" — is not the
Booking's to enforce in one transaction. It is a policy across Aggregates, and
either its consistency is stated as eventual or it moves the boundary.

Below the sketch, list the transaction boundary, concurrency control, the
invariants enforced, the events emitted, and the mutations that must never
happen from outside.

## State and data flow

Use a state diagram only where legal and illegal transitions matter. Label each
transition with the command or cause, and each guard with the invariant or
policy it checks.

Use a data-flow sketch when several contexts observe, translate or derive the
same information. Mark the authoritative source, derived copies, commands,
events and queries. Never draw an unexplained two-way arrow.

## Meaning, not color

- Never carry meaning by color alone; use labels, shape and borders.
- Keep labels short and put the detail in prose or a table.
- Use the same identifiers in the sketch as in the tables.
- Ask the person who knows the domain to narrate the sketch back, and record
  where their story and the drawing disagree.
