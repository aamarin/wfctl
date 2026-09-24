# The modeling round

Load this for a full discovery or design round. An Explore round needs only
sections 1 and 2.

## 1. Framing and evidence

Start from a decision, not from "do DDD". Record the capability and the outcome
wanted, the concrete decision, the people who know the domain, how reversible
the decision is, the existing model and constraints, and what is excluded.

Keep an evidence table. Classify each source as an observation, a statement by a
named person, a policy, an example, implementation behavior, or a prior record.
`evidence.md` has the labels. Note contradictions; do not resolve them by vote.

## 2. Knowledge crunching

1. Pick one scenario that is valuable or contested.
2. Ask what the actor wants and what starts it.
3. Walk it in business time.
4. Capture commands as intentions and events as facts that have happened.
5. Ask which rules reject or change each step.
6. Find the information each rule needs at the moment it decides.
7. Retell the story in the candidate language.
8. Sketch the behavior and the boundaries.
9. Replay a counterexample and a correction.
10. Revise the language, the rules or the boundaries, and test with code or a
    worked example.

Look for verbs, policies, calculations, constraints, rules about time, and
exceptions. Nouns alone produce an inventory with no behavior in it.

When the model feels awkward — a rule that needs three special cases, a term
people keep qualifying — press on that spot rather than smoothing it over. It is
often one missing concept away from a much simpler model, and finding that
concept is worth a short slowdown. Make the concept explicit when you find it: a
constraint, a process or a rule that people talk about but the model only
implies should get a name in the language and a place in the model.

| Scenario field | Meaning |
| --- | --- |
| Actor and intent | who wants what outcome |
| Trigger and preconditions | why it starts, and what must already be true |
| Command | the requested action, as an imperative |
| Rules | invariants, policy, authorization, timing |
| Outcome and events | business facts, in the past tense |
| Alternatives and failures | rejections, retries, cancellations, corrections |
| Evidence and questions | the evidence rows it rests on, and what is unanswered |

## 3. Strategic design

Group behavior into capabilities by business purpose, specialized knowledge,
ownership, vocabulary and what drives change. Classify a subdomain as core,
supporting or generic only to guide where effort goes, and record why and when
that should change.

For each candidate Bounded Context, define its purpose, the language it owns,
the behavior it includes and excludes, the information it is authoritative for,
who decides for it, its contracts, and what pushes it to change. Incompatible
meanings, different invariant sets, different authorities, different rates of
change and a need to translate are all clues to a boundary. None of them is an
automatic cut.

For each relationship between contexts, answer:

- Who is upstream and who is downstream, and who influences the contract?
- Where does translation of meaning happen?
- Is the interaction synchronous, asynchronous, batch or manual?
- What consistency and ordering are needed?
- How do timeout, duplication, drift and partial failure behave?
- What evidence supports all of this?

Only then name the relationship — `ddd-heuristics.md` lists the nine. Record the
team relationship and the technical one separately.

## 4. Tactical design

Write each invariant as a business statement that could be false, with the
moment it is decided, the information it needs, who enforces it, the concurrency
window, and what a violation costs. Then propose the smallest consistency
boundary that protects it. An Aggregate is a boundary of behavior and
transaction, not an object graph.

- Protect true invariants inside the Aggregate.
- Keep Aggregates small.
- Refer to another Aggregate by its identity only.
- Update another Aggregate by eventual consistency — events or a process —
  when the business can accept the delay.
- Name the root after the conceptual whole it controls.
- State the transaction, concurrency and failure behavior.

Challenge every transaction that spans Aggregates: is it one invariant, a
process, reporting convenience, or an implementation shortcut?

Choose each building block by its responsibility. `ddd-heuristics.md` has the
palette and the rules for telling them apart.

## 5. Implementation feedback

Bind the model to the implementation with an executable scenario, a domain-only
spike, a code trace, a persistence or concurrency test, or a contract example.
Compare the terms across sketches, documents, APIs, code, tests and UI copy, and
record each deliberate translation.

Existing code may preserve obsolete rules and accidental constraints. Treat it
as evidence, not automatic truth. What it contradicts goes back up to level 2
through `design-levels`, not into a quiet edit of the model.

## 6. Distillation

Remove concepts that explain no behavior, enforce no rule and support no
decision. Name the Core Domain — the smallest set of concepts carrying what
makes this system worth building — and keep it from being diluted by the rest.

Two cheap tools help. A **domain vision statement**, a few sentences on what the
core is and why it matters, aligns people without a design document. And a
capability that is necessary but not distinctive can be marked a **generic
subdomain**: a candidate to buy, reuse or keep simple, so effort goes to the
core instead.

Then write the model document from `domain-model-template.md`. The record stays
authoritative; the document links to it and draws it.
