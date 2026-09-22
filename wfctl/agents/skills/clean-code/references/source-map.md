# Source map and adaptation notes

This skill is an original, language-agnostic synthesis of the principles,
practices and heuristics in Robert C. Martin et al., *Clean Code: A Handbook of
Agile Software Craftsmanship* (Pearson, 2008). It reproduces none of the book's
sample programs.

**The chapters are the key here and nowhere else.** Every other file in this
skill is named for the unit of code an agent is holding — an identifier, a
function, a module, an error path, a test — because that is what the agent
knows at the moment it needs the guidance. This file exists for the other
reader: a maintainer checking whether a chapter was covered or dropped on
purpose, who knows the chapter and not the unit.

| Source section | Reference | Adaptation |
| --- | --- | --- |
| Ch. 1 — Clean Code | `SKILL.md` | Craftsmanship, the cost of disorder, continuous care and leave-it-better recast as priority order and scope guidance. |
| Ch. 2 — Meaningful Names | `naming.md` | Names, context, vocabulary, searchability, abstraction and disinformation generalised beyond Java identifiers. |
| Ch. 3 — Functions | `functions.md` | Coherent responsibility, abstraction levels, argument and side-effect clarity kept; literal size limits dropped. |
| Ch. 4 — Comments | `comments-and-formatting.md`, `review-catalog.md` | Comments treated as durable intent or constraint, neither categorically bad nor a substitute for code. |
| Ch. 5 — Formatting | `comments-and-formatting.md` | Automated project conventions, locality, grouping and reading flow prioritised over book-specific rules. |
| Ch. 6 — Objects and Data Structures | `classes-and-modules.md` | Object/data trade-offs and limited collaborator knowledge generalised to object-oriented, functional and data-oriented designs. |
| Ch. 7 — Error Handling | `errors.md` | Visible normal flow, contextual failures, cleanup and explicit absence kept; exceptions no longer universal and nullable types no longer forbidden. |
| Ch. 8 — Boundaries | `boundaries.md` | Narrow adapters, learning tests, consumer-defined interfaces and isolation of volatile external concepts kept whole. |
| Ch. 9 — Unit Tests | `tests.md`, `review-catalog.md` | Translated into behavioural focus: one concept may require several assertions. |
| Ch. 10 — Classes | `classes-and-modules.md` | Small classes recast as cohesive modules with one coherent change responsibility; line and member limits dropped. |
| Ch. 11 — Systems | `classes-and-modules.md` | Construction/use separation, dependency assembly, cross-cutting policy and standards-chosen-for-value generalised. |
| Ch. 12 — Emergence | `classes-and-modules.md` | Passing tests, reduced duplication, expressiveness and minimal structure kept, with accepted architecture as an explicit constraint. |
| Ch. 13 — Concurrency | `concurrency.md` | Extended from threads to async, tasks, actors, workers, queues, cancellation, backpressure and modern race tooling. |
| Ch. 14 — Successive Refinement | `refactoring-workflow.md` | The practice of small verified transformations and incremental concept discovery, not the source program. |
| Ch. 15 — JUnit Internals | `refactoring-workflow.md` | The practice of cleaning working framework code through tests, names, responsibility moves and small steps. |
| Ch. 16 — Refactoring SerialDate | `refactoring-workflow.md` | Characterisation, correctness before cleanup, API scrutiny and staged improvement, not the source implementation. |
| Ch. 17 — Smells and Heuristics | `review-catalog.md` | Reorganised by review consequence, overlaps merged, Java-only rules omitted. |
| App. A — Concurrency II | `concurrency.md` | Execution paths, method dependencies, throughput, deadlock and concurrent testing generalised. |
| App. B and C | not reproduced | A raw source listing and cross-reference mechanics serve no operational, language-agnostic skill. |

## Deliberate departures

Each of these is intentional rather than an omission.

- Project instructions and accepted architecture records outrank local
  cleanliness heuristics.
- Rules are evaluated by consequence. No numeric threshold is enforced for
  size, arguments, assertions or coverage.
- Exceptions are one error model among several.
- `null`-avoidance becomes explicit absence and boundary validation.
- Polymorphism becomes a broader choice among dispatch, variants, tables,
  pattern matching and direct conditionals.
- Object-oriented examples become responsibility, ownership and dependency
  guidance.
- Formatting is delegated to the repository's tools and conventions.
- Java-specific import, constant-inheritance and enum advice is excluded.
- The review workflow requires evidence and a bounded consequence, so the
  heuristic list cannot become style noise.

## Where the split came from, and why it is not the chapters

Two files in the draft this skill was built from carried several chapters each:
one covered objects, errors, boundaries, tests, classes, system assembly and
simple design together. Asking that file about a class also loaded error models
and test design.

The split is keyed on the unit under work because a router cannot address a
topic inside a file — the reasoning is
`docs/architecture/design/412-the-split-is-keyed-on-the-unit-under-work.md` in
wfctl's own repository, which a consuming project does not receive.

## Maintenance rule

`SKILL.md` stays the operational router. Add depth to the narrowest relevant
reference and make sure the router's table names it.

**Update this table in the same change as any rename.** It is the only file
holding the chapter-to-reference mapping, which is the cost of keeping the
traceability view separate from the routing key — paid in one place rather than
in the router.

Do not add copied source passages, translated sample programs, or a
chapter-by-chapter retelling.
