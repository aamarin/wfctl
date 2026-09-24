# DDD constructs and cautions

Load this when choosing a strategic or tactical construct, or naming a Context
Map relationship. These are working heuristics synthesized from the DDD
literature — `source-map.md` names the books. They do not replace evidence or
project records.

## Knowledge and language

- Model through repeated collaboration between the people who know the domain
  and the people who build it.
- The model is not a diagram beside the code; it is the structure of the code.
  Whoever changes the model has to be able to touch the implementation, and
  whoever writes the code is changing the model.
- Bind the language, the sketches, the tests and the implementation so each one
  challenges the others.
- Look for behavior and rules, not only data.
- Add, reshape and remove concepts as understanding improves.
- Spend effort on the Core Domain.

## Strategic constructs

- A **Bounded Context** is an explicit boundary of meaning. The same word can
  validly mean different things in different contexts.
- A **subdomain** belongs to the problem space and a context to the solution
  space. One subdomain per context is a useful target, not a law.
- Inside one context, the model stays coherent only if the people changing it
  merge and reconcile their work often. When that stops, a context is quietly
  splitting — decide whether the split is real.
- Organizational boundaries are evidence, not automatic boundaries of meaning.
- A Context Map is descriptive until accepted ownership and contracts back it.

### The nine Context Map relationships

Describe the facts first — direction, power, who translates — and name the
relationship last.

| Relationship | The fact it names |
| --- | --- |
| Partnership | two contexts succeed or fail together and coordinate their changes |
| Shared Kernel | a small, explicitly agreed part of the model both contexts own |
| Customer–Supplier | downstream needs shape upstream's plans, and upstream agrees to meet them |
| Conformist | downstream adopts upstream's model as is, because it has no leverage to change it |
| Anticorruption Layer | downstream translates upstream's model into its own, so the foreign one does not leak in |
| Open Host Service | upstream offers one well-defined protocol to every consumer |
| Published Language | a documented shared language for exchange, often paired with an Open Host Service |
| Separate Ways | no integration; each context solves its own problem |
| Big Ball of Mud | a region with no enforced boundary. Draw a line around it and do not let its model spread |

Partnership and Big Ball of Mud come from Vernon; the other seven from Evans.

## Tactical building blocks

Choose by responsibility, not by matching nouns.

| Construct | Use it for |
| --- | --- |
| Entity | something whose identity continues while its attributes change, and which the domain has to track |
| Value Object | something defined only by its attributes — immutable, and interchangeable with an equal one |
| Aggregate | a consistency boundary around the invariants that must hold together, with one root |
| Domain Event | a business fact that has happened, named in the past tense |
| Domain Service | domain behavior that belongs to no single Entity or Value Object |
| Application Service | orchestration of a use case, with no business rules of its own |
| Specification | a business rule as a named predicate — tested against an object, combined with others, or used to select |
| Factory | creating a complex Aggregate whole, with its invariants satisfied from the start |
| Repository | the persistence port for one Aggregate type, presented as a collection |
| Module | a named grouping in the language, cohesive in story and loosely coupled to the rest |
| Policy or process | a decision or coordination that runs across time or across boundaries |

Rules for telling them apart:

- **Prefer a Value Object.** Promote to an Entity only when the domain must
  follow something's continuity through change.
- **A rule that is reused, combined or queried against a collection** —
  eligibility, matching, selection — **is a Specification**, named in the
  language. Scattered conditionals are the same rule with no name.
- **Keep associations to what the scenarios traverse.** Give each one a
  direction, add a qualifier, or drop it, before it turns into a dependency
  across Aggregates.
- **Name Modules in the language**, not by technical layer.
- **Keep domain rules out of controllers, schemas and scripts.** Where they have
  leaked there, that is a modeling finding. Drawing the layer boundary itself is
  `architecture-design`'s work.
- **How the code expresses a settled model** — intention-revealing names,
  functions free of side effects, stated assertions — is
  `.agents/skills/clean-code`, at levels 3 and 4.

## Cautions

- DDD earns its cost where domain complexity and change justify it.
- A pattern name can hide weak reasoning. Describe the forces first.
- Eventual consistency is a business decision with consequences users can see.
- Start event-oriented discovery from what happened, then find the commands,
  actors, policies, hotspots and Aggregate candidates. Colors on sticky notes
  are a notation, not a conclusion.
- Model risky behavior without infrastructure when that shortens the learning
  loop.
