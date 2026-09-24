# Evidence, and what it takes to hand a claim on

A plausible diagram is not evidence that a boundary or an invariant is right.
This file says how strong a claim is and when a round has enough to hand on.

It mints no verdicts. `design-levels` owns every gate, and a proposed record
becomes accepted only when a person accepts it. What follows is what to check
before handing off, not a gate.

## How strong a claim is

Label every claim in the model with one of these:

| Label | Means |
| --- | --- |
| `observed` | seen in behavior, data, code or a test |
| `stated` | said by a named person who knows the domain |
| `inferred` | the agent's reading of the evidence, not yet confirmed |
| `open` | a question nobody has answered yet |

A claim that has been **decided** is not labelled; it links to the record that
decided it. That keeps one vocabulary for decisions — the record's own status —
instead of a second one living in the model document.

Never turn `inferred` into `stated` or decided by repeating it. Keep what the
code does apart from what the business intends: existing code can preserve an
obsolete rule or an accidental constraint.

Record contradictions. Do not resolve them by majority vote.

## Before handing off

Each of these is a question to answer in the model document. When one does not
apply, write a `none — <reason>` row rather than leaving it out.

- **The decision is framed.** The decision the round supports, its outcome,
  scope, the people who know the domain, and what is out of scope.
- **Scenarios were replayed.** At least a normal one, an alternative or failure,
  and a correction or timing one.
- **The language holds.** Key terms have a meaning per context, material
  synonyms and overloads are resolved or visible, and the scenarios read
  naturally in the language.
- **Each boundary is justified.** Each context has evidence from language,
  rules, ownership or rate of change, and each relationship names its direction
  and who owns the translation.
- **Each invariant is protected.** Aggregates trace to the invariants they
  protect, the information each invariant needs is available when it is decided,
  transaction and concurrency behavior are stated, and effects across Aggregates
  state their consistency.
- **Implementation pushed back.** A representative path was checked against
  code, an executable test, a thin spike or a contract example. Only an
  exploration round with no implementation decision skips this, and it says so.
- **A person who knows the domain reviewed it.** Without that review, the round
  names the risk and the record stays `proposed`.

When one of these cannot be answered, say which kind of stop it is: the round
is exploration only, it needs a reversible spike, or it has to pause for a
person's decision.

## What reopens a model

A model is reopened by new terminology, a policy change, a translation that
keeps being repeated, pressure for a transaction across a boundary, a
concurrency failure, drift between integrations, a change of ownership, or a
scenario that cannot be told naturally in the language. Write the ones that
apply into the model document, so the next reader knows what should bring them
back.
