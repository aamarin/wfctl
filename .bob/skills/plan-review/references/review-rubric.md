# Plan review rubric

This rubric keeps a critique specific and grounded in evidence. Not every
question applies to every feature, and a concern is flagged only when it
materially affects the change the plan proposes.

## Lens 1: Requirements and traceability

Ask:

- Can each functional requirement and success criterion in `spec.md` be traced
  to a concrete part of the plan?
- Does the plan preserve the scope boundaries and non-goals?
- Does the plan add behavior, actors, data, APIs, or deployment obligations the
  spec does not authorize?
- Are negative-path requirements handled, and not only the happy path?
- Are the acceptance criteria observable rather than subjective?
- Would an implementer have to invent product behavior to finish the plan?

A strong finding:

> `spec.md §FR-7` requires interrupted imports to resume without duplication,
> but `plan.md §Import Pipeline` defines retries without an idempotency key or a
> persisted checkpoint. An implementer must choose semantics the spec makes
> visible to the user.

A weak finding:

> Consider making the import pipeline more robust.

## Lens 2: Architecture, ownership, and accepted decisions

Ask:

- Does the plan honor the constitution and the design records `design.md`
  lists?
- Do dependencies point in the accepted direction?
- Is each piece of state owned by one authoritative boundary?
- Are changes to a public API, an event, a persisted schema, or a contract
  between contexts made explicit?
- Does the plan duplicate an existing source of truth, or introduce a second
  representation without a contract that keeps the two in step?
- Are transaction boundaries and consistency expectations clear where the plan
  touches more than one store or aggregate?
- Is each new abstraction justified by a present need rather than by
  speculative reuse?

When an accepted decision and the plan conflict, cite both. Do not resolve the
conflict by preference; report it as an `Architecture / Decision Conflict`.

## Lens 3: Adversarial implementation and ambiguity

Imagine a competent implementing agent that has only the durable artifacts, and
ask:

- Where can two reasonable implementers make incompatible choices?
- Which terms are underspecified, such as `fast`, `secure`, `graceful`,
  `supported`, `sync`, or `current`?
- Which state transitions lack preconditions, an ordering, or conflict
  behavior?
- What happens on retry, partial failure, timeout, duplicate delivery,
  cancellation, or restart, where those conditions are plausible?
- Is it clear who owns an error: the caller, the domain, persistence, the
  transport, or an operator?
- Are defaults and fallbacks explicit where they change behavior?
- Are assumptions labeled as assumptions, or buried as if they were
  requirements?

When the artifacts contain no safe answer to one of these, file a `Missing
Information` finding and grade it by what it holds up, as § Missing information
below says. Do not answer the question yourself to make the plan complete.

## Lens 4: Verification and evidence

Ask:

- Does every material behavior have a route by which it can be observed?
- Are the failure paths and boundary conditions testable?
- Does the plan name the right test layer for the risk: unit, contract,
  integration, end-to-end, migration, or operational?
- Are the tests likely to prove behavior rather than implementation details?
- For a migration or a compatibility change, is there a way to verify existing
  data and existing clients?
- Where a requirement is verified by inspection rather than by execution, is the
  inspection target explicit?
- Where the workflow requires evidence for every verification dimension, are
  the dimensions that do not apply marked as not applicable?

Do not demand a test for every line of the plan. Demand evidence for the
behavior and the risks the feature says matter.

## Lens 5: Risk, failure, and recovery

Apply this lens when it is relevant:

- What is the blast radius if the operation fails halfway?
- Can the operation be retried safely?
- Is rollback possible, and when it is not, is forward recovery explicit?
- Are destructive actions bounded and authorized?
- Are concurrency and stale-write behavior defined?
- Are resource limits, backpressure, or timeouts relevant, and addressed?
- Is there enough observability to diagnose the failure mode the plan
  introduces?

A rollback strategy is not required everywhere. Flag its absence only when a
failed partial change would otherwise leave an unsafe or unrecoverable state.

## Lens 6: Security and trust boundaries

Apply this lens when the feature touches authentication or authorization,
secrets, sensitive data, externally supplied input, privileged operations,
tenant boundaries, public endpoints, or data under compliance rules.

Ask:

- Where is authorization enforced, and is that point inside the trusted
  boundary?
- Can a caller bypass enforcement by invoking a lower layer directly?
- Is tenant or owner scoping preserved through reads and writes?
- Are inputs validated at the boundary that must distrust them?
- Are secrets and sensitive fields kept out of logs and error messages?
- Does the plan introduce a new path to data exposure or to privilege?
- Are audit requirements explicit where an action is sensitive?

Prefer the threat boundaries of this project over a generic recital of the OWASP
(Open Worldwide Application Security Project) lists.

## Lens 7: Dependency and feasibility

Ask:

- Does the plan depend on an API, command, feature flag, schema field,
  permission, service capability, or library behavior that has been verified?
- Are version assumptions explicit?
- Are constraints on deployment or migration order known?
- Does the approach need infrastructure or an operational capability the
  repository does not have today?
- Is an open research question presented as a settled fact?
- Does the plan assume an external dependency can take part in a transaction or
  a consistency model it does not support?

Do not invent duration estimates. Feasibility is whether the proposed mechanism
can work under the known constraints.

## Lens 8: Scope and simplicity

Ask:

- Is every new component needed for a current requirement?
- Does the plan replace a local problem with a platform or framework project?
- Are extension points being built with no present caller?
- Does the plan change unrelated architecture while it solves the feature?
- Is there a smaller design that satisfies the same accepted constraints?

File a speculative improvement as an `Enhancement Suggestion`, never as a
BLOCKER.

## Priority tests

### BLOCKER

Use BLOCKER only when one of these is true:

- two durable sources of truth materially contradict each other
- the plan violates an accepted non-negotiable invariant or constitutional rule
- required behavior cannot be implemented without making a consequential product/architecture decision not present in the artifacts
- a required state/data transition is internally impossible or undefined in a way that can corrupt, expose, or lose data
- verification of a critical requirement is impossible as written

### MAJOR

Use MAJOR when one of these is true:

- a consequential assumption is unstated
- a likely failure mode lacks handling and would cause substantial rework or
  unsafe behavior
- an important dependency or capability is unverified
- the plan crosses a significant boundary without defining the contract
- implementation can proceed, but only by choosing among materially different
  interpretations

### MINOR

Use MINOR for a bounded improvement to clarity, maintainability, or
verification that forces no consequential choice.

### Missing information

A missing answer is a category, not a priority. When the reviewer needs an
answer from the author or the domain owner, and the existing evidence cannot
safely select one, file the finding under `Missing Information` and grade it by
what it holds up:

1. BLOCKER, when required behavior cannot be implemented without the answer.
   This is the third BLOCKER test above, and it is the reason a missing answer
   is not a grade of its own: a separate grade would let a reviewer file a
   blocking question where the verdict never reads it.
2. MAJOR, when implementation can proceed only by guessing the answer, and a
   wrong guess costs substantial rework.
3. MINOR, when the answer changes nothing consequential.

## Synthesis across reviewers

When independent reviewers are available, give each a set of lenses rather than
asking every reviewer the same general question. A useful panel is:

1. Reviewer A, on requirements, traceability, and scope.
2. Reviewer B, on architecture, boundaries, and dependencies.
3. Reviewer C, on adversarial implementation, verification, and failure modes.
4. Reviewer D, on security and reliability, when that lens applies.

The synthesis follows five rules:

1. Evidence outranks votes.
2. Agreement between reviewers is corroboration, not proof.
3. A single objective contradiction can be a BLOCKER.
4. A minority finding is not discarded because the other reviewers missed it.
5. Incompatible recommendations stay in the report as a disagreement until a
   person or a decision record resolves them.
