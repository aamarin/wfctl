---
name: clean-code
description: 'Express code well once its boundary is already settled — name an identifier honestly, keep a function at one level of abstraction, give a module one reason to change, make failure part of the API. Use during design-levels level 3 for structure and level 4 for mechanism in any language, while reviewing for readability, and while refactoring behaviour-preservingly. Not for drawing or moving a boundary, not for deciding who owns a piece of truth, and not a design loop.'
---

# Clean code

## Route to the guidance

**Read only the reference the unit of work names.** Each one is keyed on what
you are holding right now, not on where the guidance came from.

| You are working on | Read |
|---|---|
| an identifier, a domain term, a type or callable name, a naming dispute | [references/naming.md](references/naming.md) |
| a function's responsibility, its arguments, its side effects | [references/functions.md](references/functions.md) |
| whether a comment earns its place, or how a file is laid out | [references/comments-and-formatting.md](references/comments-and-formatting.md) |
| what a class or module owns, where a decision belongs, how a system is assembled | [references/classes-and-modules.md](references/classes-and-modules.md) |
| failure, absence, cleanup, what a caller can act on | [references/errors.md](references/errors.md) |
| a third-party library, a service, an OS call, a component that does not exist yet | [references/boundaries.md](references/boundaries.md) |
| what a test proves, and which behaviour is worth a test | [references/tests.md](references/tests.md) |
| threads, tasks, async, shared state, cancellation, shutdown | [references/concurrency.md](references/concurrency.md) |
| changing structure while preserving behaviour | [references/refactoring-workflow.md](references/refactoring-workflow.md) |
| reviewing a diff, or auditing for maintainability | [references/review-catalog.md](references/review-catalog.md), plus the reference each finding implicates |
| which chapter of the source material a reference carries | [references/source-map.md](references/source-map.md) |

Everything below this table is reachable after you have chosen. The table is
the only part you have to read before choosing, which is what keeps the cost of
loading this skill proportional to the question.

`design-levels` routes here twice — level 3 for the four structural references,
level 4 for the three about local expression — and `code-review` names the
catalog as a source for its readability pass. Reaching this skill by a
description match rather than by one of those routes changes nothing about what
it says.

## What this skill is for

Improving the code's ability to explain its intent and to accept safe change,
without altering behaviour or project constraints.

Treat what follows as judgment heuristics, not a style law. A locally clean
change that violates an accepted architecture record, a public contract, a
safety property or a performance constraint is not an improvement.

## Authority

- Project instructions and accepted architecture records outrank every
  heuristic here. Read the in-force set with `wfctl arch context`.
- **This skill produces no verdict vocabulary and grants no waiver.** No pass,
  no fail, no outcome class. `design-levels` owns every gate, and a skill that
  produced one would have taken a gate rather than informed it.
- **It runs no design loop.** Ranking drivers and comparing credible approaches
  is `.agents/skills/architecture-design`'s work, and a second loop here would
  mean an agent that loaded both did it twice.
- **It routes to neither record skill.** A choice that draws a boundary is
  `.agents/skills/architecture-decisions`; one that weighed credible
  alternatives and drew none is `.agents/skills/software-design-decisions`.
  Neither routing is this skill's to make.
- **It assumes the boundary is settled.** If you are not sure it is, it is not,
  and `.agents/skills/design-levels` is where you find out which level the
  question belongs to.

The record behind these constraints is
`level-3-owns-structural-heuristics`, which turns on one property: a method
that ends in a record is a design loop, and heuristics that end in nothing are
guidance. This skill writes nothing, which is what lets it sit at level 3
beside `architecture-design` rather than competing with it.

## Priority order

Resolve competing concerns in this order:

1. Requested behaviour and accepted project decisions.
2. Correctness, security, data integrity, concurrency safety, required
   performance.
3. Public compatibility and repository conventions.
4. Testability, changeability, readability.
5. Stylistic preference.

Do not expand the task because nearby code could be cleaner. Keep cleanup
proportional to the requested change and name larger opportunities separately.

## Establish the contract first

Before changing code:

1. Read repository instructions, nearby code, tests, and the accepted records.
2. Identify the observable behaviour, public interfaces, invariants, side
   effects, and important failure modes.
3. Identify what a cleanup must not erase: compatibility, latency, memory,
   transactions, ordering, security, accessibility, deployment behaviour.
4. Decide whether the task is implementation, refactoring, review, or a
   combination. Keep behavioural and structural reasoning distinguishable even
   when they happen in one patch.

Where behaviour is unclear, get evidence from tests, callers, documentation and
runtime behaviour. Do not make code easier to read by silently choosing among
unresolved meanings.

## Heuristics that apply everywhere

Prefer code that:

- uses the project's domain vocabulary consistently;
- makes important state, units, boundaries and side effects explicit;
- keeps each function or module at a coherent level of abstraction;
- places behaviour with the data or responsibility it belongs to;
- minimises hidden ordering, distant knowledge and shared mutable state;
- isolates volatile or external detail behind narrow boundaries;
- has focused tests that explain behaviour and make restructuring safe;
- leaves the touched area no harder to understand than before.

**Avoid proxy metrics.** A function is not good because it has few lines, a
class is not good because it has few methods, and a test is not good because it
has one assertion. Judge whether each unit expresses one coherent concept with
the context needed to understand it.

## Writing new behaviour

1. Express the domain concepts and contracts before optimising the internal
   mechanics.
2. Choose names that make the call site read honestly.
3. Keep the normal path visible; isolate error translation, resource cleanup
   and infrastructure detail.
4. Introduce an abstraction only when it names a real concept or protects a
   meaningful boundary.
5. Add tests at the cheapest level that proves the behaviour, including the
   relevant boundaries and failure paths.
6. Run the focused checks, then the broader ones the change justifies.

## Changing existing behaviour's shape

1. Build or confirm a safety net for the behaviour being preserved.
2. Select one concrete problem — a misleading name, mixed abstraction,
   duplication, a hidden side effect, a misplaced responsibility.
3. Make the smallest structural change that addresses it.
4. Verify behaviour immediately.
5. Re-read the changed call sites and the surrounding module. Stop when the
   code communicates the intended model without speculative machinery.

The full protocol and its stop conditions are in
[references/refactoring-workflow.md](references/refactoring-workflow.md).

## Reviewing

Review for consequences, not rule violations. Prioritise findings that could
produce incorrect behaviour, conceal an important effect, or make the next
change unsafe.

For each material finding, state the location and the observed evidence, the
likely consequence, the smallest credible improvement direction, and any
trade-off or missing information that affects confidence.

Do not report formatter output, personal taste, or a theoretical abstraction
preference as a substantive defect. Do not demand a broad rewrite where a
rename, an extraction, a boundary check or a focused test resolves the risk.

If nothing material is wrong, say so. Do not invent findings to populate a
checklist.

**Severity is `code-review`'s, not this skill's.** The catalog grades a
*consequence* — Critical, High, Medium, Low — and `code-review` grades what the
author must do about it — BLOCKER, WARNING, NIT. They are different scales and
this skill converts between them nowhere. A catalog row is a hypothesis about
consequence; the reviewer classifies the confirmed finding.

## Translate, do not imitate

Apply the intent using the target language's current idioms.

- Treat exception advice as guidance to separate failure handling and preserve
  context. Do not force exceptions into a language or an API where another
  explicit error model is idiomatic.
- Treat avoidance of null-like values as guidance to make absence explicit and
  validated. Use the language's option, result, nullable or precondition
  mechanism.
- Treat object-oriented examples as responsibility and dependency guidance.
  Functional, data-oriented, procedural and actor-based designs may satisfy the
  same goals.
- Treat one-assert advice as one-behavioural-concept guidance, not an assertion
  count.
- Treat smallness as focused responsibility and navigable scope, not a line
  limit.
- Prefer the repository's automated formatting and established conventions over
  recreating any book-specific format.

Do not reproduce or translate a sample program from any source. Where an
example is needed, write a fresh, domain-neutral one.

## Before finishing

- Confirm the requested behaviour and the relevant failure paths.
- Run the repository's formatter, static checks and tests where they exist and
  are in scope.
- Inspect the final diff for accidental behaviour changes, dead code, stale
  comments and public contract drift.
- Distinguish what you verified from what you are recommending.
- Say what became clearer, and cite the evidence you used to conclude the
  change is safe.
