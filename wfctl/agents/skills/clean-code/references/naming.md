# Naming

Use this reference when naming a new identifier, evaluating an existing name,
or resolving a naming dispute.

## What a name has to accomplish

A useful name reduces how much surrounding code a reader must inspect. It
reveals the concept at the identifier's own level of abstraction and creates
accurate expectations at the call site.

Ask:

- What does this represent or do?
- Why does it exist here?
- What distinctions matter to a caller?
- Does it expose a unit, boundary, lifecycle or side effect that would
  otherwise be hidden?
- Is the term from the problem domain, an established technical concept, or the
  repository's shared vocabulary?

A type name is normally a noun or noun phrase. A callable name normally
describes an action, a question, a conversion or a retrieval. Booleans and
predicates read as claims that can be true or false.

## Semantic truth before brevity

Reject a short name when it makes a false promise. The common false promises:

- a name implying ordering or magnitude for a nominal category;
- `get` or another retrieval verb for an operation that creates, mutates,
  performs I/O, blocks or caches;
- a collection type encoded into a name when the abstraction is not about that
  container;
- `result`, `success` or `error` when the value does not represent that outcome
  model;
- an implementation term used for a stable domain abstraction;
- a generic suffix — `data`, `info`, `object`, `manager`, `processor` — that
  creates no meaningful distinction.

Read candidate names in representative expressions. The best one makes the
expression honest without a comment or a mental translation.

## Use the right abstraction level

Name an abstraction for the promise it offers, not for one current
implementation. A transport-independent concept is not named for today's
protocol. A domain decision is not named for the file or the query used to
infer it.

Conversely, do not hide a mechanism callers must reason about. If an operation
allocates, persists, retries, schedules or crosses a trust boundary, and that
fact affects safe use, express it in the API or in its name.

## Build a consistent vocabulary

Use one term for one concept across the repository. Before introducing a
synonym:

1. Search declarations, call sites, records, commands, tests and user-facing
   language.
2. Identify what each existing term already owns.
3. Reuse the established term when the semantics match.
4. Choose a distinct term when they differ. Do not force consistency by making
   one word carry two meanings.

Prefer a problem-domain term where a domain expert would recognise the concept,
and an established technical term for a technical mechanism. Avoid jokes, local
metaphors and culturally dependent shorthand.

## Context without noise

Let modules, namespaces, types and containing functions supply context. Add a
prefix or suffix only where the identifier would otherwise be ambiguous at its
use sites.

Do not repeat context the container already guarantees. A wrapper type need not
restate every field it contains; a `state` field can name the scale while the
wrapper names the interpretation.

Long-lived or widely imported names need more precision than tiny local ones. A
short index or accumulator is fine where its scope makes its meaning immediate.
Searchability matters more as scope grows.

## Evaluate candidates systematically

For a consequential rename, compare candidates against this table:

| Criterion | Question |
| --- | --- |
| Semantic accuracy | Could the name cause a reader to infer a property the value does not have? |
| Abstraction | Does it name the concept rather than an incidental implementation? |
| Call-site clarity | Does a representative assignment, condition or invocation read naturally? |
| Vocabulary fit | Does the repository already use the word, for this concept or a different one? |
| Distinction | Does it explain how this symbol differs from its neighbours? |
| Scope | Is its precision proportional to how widely it is visible? |
| Searchability | Can a maintainer find the symbol without wading through unrelated matches? |
| Stability | Will the name stay true if the implementation changes within the abstraction? |

Weight semantic accuracy and call-site clarity above occurrence counts. A noisy
search is an inconvenience; a misleading identifier is a permanent
comprehension cost.

## Naming smells

- names that need a glossary only the original author has;
- near-identical names whose difference is hard to see;
- several verbs for one operation, or one verb reused for unrelated ones;
- type or scope encodings the language or the tooling already supplies;
- vague containers named `thing`, `value`, `payload`, `data` or `result` where
  a stable concept exists;
- names describing only the happy path while hiding a side effect or a
  fallback;
- names that drifted as the behaviour evolved;
- longer compound names that stack context rather than adding precision.

## Recommending a name

1. State the concept in one plain sentence.
2. Show two or three representative call sites.
3. Eliminate semantically false candidates before discussing taste.
4. Compare the survivors against the repository's vocabulary.
5. Recommend one, and state its principal cost.

Do not present a long synonym inventory without a decision.
