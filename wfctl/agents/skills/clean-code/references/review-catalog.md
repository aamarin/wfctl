# Review catalog

Use this catalog to generate review hypotheses, ordered by what a finding
costs. Confirm each hypothesis against the code's actual contract and context
before reporting it.

## Severity is about consequence, and it is not the author's action

| Priority | Typical consequence |
| --- | --- |
| Critical | Data loss, security failure, corruption, deadlock, or broadly incorrect behaviour |
| High | Missing required behaviour, unsafe boundary, hidden destructive effect, race, or absent protection for a critical path |
| Medium | Coupling, duplication, mixed responsibility, or ambiguity that materially raises change risk |
| Low | A local clarity or consistency issue with limited consequence |

**This scale grades a consequence. `code-review`'s BLOCKER / WARNING / NIT
grades what the author must do.** They are different questions and this catalog
converts between them nowhere — the reviewer classifies a confirmed finding
under `code-review`'s scale.

Do not inflate severity because a rule has a memorable name. A misleading
identifier can be Critical where it conceals destructive behaviour; a long
function can be no issue at all where it stays coherent.

## Comments and documentation

- information in a comment that belongs in version control, an issue, or user
  documentation;
- obsolete, redundant, misleading or badly located comments;
- commented-out code;
- comments compensating for names or structure that could be made clear;
- public contracts with missing or inaccurate documentation;
- rationale or a safety constraint existing only in a maintainer's memory.

## Build and test environment

- a build or a test requiring an undocumented manual step;
- different commands producing inconsistent results with no declared reason;
- hidden environmental assumptions;
- tests that cannot be run independently at their intended level;
- slow feedback caused by avoidable setup or uncontrolled external
  dependencies.

The goal is a simple, deterministic entry point, not necessarily one literal
command for every repository.

## Functions and APIs

- an argument list concealing a missing concept;
- output arguments or implicit mutation where an explicit result would be
  clearer;
- mode or boolean arguments combining distinct behaviours;
- dead or unreachable functions;
- a name hiding creation, mutation, I/O, blocking, caching, retry or fallback;
- one function mixing policy, mechanics and error translation;
- several abstraction levels forcing the reader to alternate between intent and
  detail.

Do not count arguments or lines without explaining the resulting comprehension
or change risk.

## Missing and unsafe behaviour

- obvious cases implied by the API and not implemented;
- boundary values, empty values, overflow, encoding or off-by-one cases wrong;
- a guard, validation, type check, compiler warning, test, authorisation rule
  or transaction safeguard bypassed with no replacement;
- precision lost through vague types, silent coercion, unclear units, or
  ambiguous time and currency handling.

## Duplication and clutter

- repeated knowledge that could drift across locations;
- similar-looking code representing different concepts, abstracted together
  prematurely;
- dead code, unused configuration, ceremonial comments or redundant
  intermediates obscuring the behaviour;
- magic literals encoding a domain rule or repeated configuration that deserves
  a name or a type.

Remove duplication of knowledge, not every repeated token sequence.

## Abstraction and dependency

- high-level policy containing low-level detail that changes for a different
  reason;
- a stable base or core depending on a volatile derivative or adapter;
- internal types, constants or configuration exposed beyond the consumers that
  need them;
- artificial coupling placing unrelated concepts together by convenience;
- a caller navigating through a collaborator's internal structure;
- a convention carrying an invariant the structure or the type system could
  enforce.

## Responsibility and locality

- behaviour far from the state or the knowledge it interprets;
- related declarations separated with no stronger organisational reason;
- a module with several unrelated reasons to change;
- a static or global function owning behaviour that depends on one instance's
  state or lifecycle;
- a condition or a boundary calculation repeated rather than named once in the
  right place.

## Intent and consistency

- similar concepts using inconsistent words or structures;
- a dense expression hiding meaningful intermediate concepts;
- a negative condition or a nested conditional obscuring the primary path;
- a selector choosing types of behaviour that should be separate operations,
  handlers or variants;
- code patched until the tests passed, with no clear understanding of the
  governing algorithm;
- an implicit dependency or ordering rule that should be represented in data
  flow, parameters, state or types;
- an arbitrary choice with no rationale, conflicting with a neighbouring
  convention.

Repeated type or mode switching may indicate a polymorphic, table-driven,
pattern-matching or dispatch-based design. Choose the mechanism natural to the
language and to whether the variants are closed or open. A direct conditional
is often clearer for one stable decision.

## Names

Investigate whether a name reveals the concept and stays true as the
implementation evolves, operates at its container's abstraction level, uses the
repository's vocabulary, is unambiguous at representative call sites, has
precision proportional to its scope, avoids unnecessary type or scope
encodings, exposes important side effects, and makes no false semantic promise
about order, success, retrieval or purity.

Read [naming.md](naming.md) before recommending a consequential rename.

## Tests

- important behaviour with no effective test;
- untested boundaries and failure paths;
- a regression fix with no test near the failure mechanism;
- skipped, ignored or flaky tests with no tracked explanation;
- patterns in failures suggesting one underlying defect;
- coverage gaps in high-risk paths;
- a slow test where faster evidence would suffice;
- tests coupled to implementation detail rather than observable behaviour.

Coverage is evidence about execution, not proof of correct assertions.

## Concurrency

- shared mutable state with no clear ownership;
- a non-atomic sequence built from individually safe operations;
- inconsistent lock ordering, or oversized critical sections;
- unbounded queues, retries or task creation;
- missing cancellation and shutdown semantics;
- background failures that cannot reach an owner;
- tests assuming one favourable schedule.

Read [concurrency.md](concurrency.md) for any material finding here.

## The finding gate

Report a finding only where all four are present:

1. a specific location or pattern in the code;
2. evidence that the behaviour or the design has the suspected property;
3. a plausible consequence in this repository;
4. a bounded improvement direction that respects accepted decisions.

State the uncertainty where a caller, a contract or a runtime fact is missing.
Ask a question instead of asserting a defect where the answer would reverse the
recommendation.
