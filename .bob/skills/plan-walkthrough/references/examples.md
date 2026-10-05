# Walkthrough Examples

These show the shape of a good walkthrough. Adapt them to the actual artifacts
rather than copying them.

## Timeout and retry

Claim: "Retry the payment registration call up to three times."

Question:
> The client can time out after the server commits. What makes replay safe?

Weak answer:
> The endpoint should be idempotent.

Follow-up:
> What actually makes it idempotent: a request key, a database constraint, a
> transaction rule, or something else?

Grounded answer:
> Each command carries an operation id. The database has a unique constraint on
> that id, and a duplicate submission returns the existing result inside the same
> transaction boundary.

Evidence to look for:
- the schema constraint;
- the command contract;
- the transaction implementation;
- a retry test covering replay after a lost response.

## Cache invalidation

Claim: "Cache resolved workflow state."

Question:
> What event makes the cache stale, and which component observes that event?

Weak answer:
> It becomes stale when the spec changes.

Follow-up:
> How does this component know the spec changed if another agent edits the file?

The question is not whether caching is reasonable in general. It is whether the
invalidation rule can actually run.

## Requirement intent versus literal behavior

Claim: "The change satisfies the ticket because all acceptance tests pass."

Question:
> What outcome is the requirement trying to produce, and where does the code
> guarantee that outcome rather than only the literal test cases?

Use this when generated code may satisfy the written examples while missing the
purpose behind them.

## Boundary ownership

Claim: "The API layer normalizes and persists the account classification."

Question:
> Which layer owns the classification rule, and what stops another caller from
> persisting a conflicting value without going through this API?

The answer should name who holds authority and what enforces it, not only the
current call path.

## Change walkthrough before merge

The change adds a background job and a new status field.

Question:
> Walk me through the state after the job writes the external side effect but
> crashes before updating the local status. What happens on restart?

Possible follow-ups:
- What notices the mismatch?
- Is the operation safe to replay?
- Which invariant prevents a duplicate side effect?
- Which test proves that recovery path?

## Scope control

Claim: "Create a generic plugin registry because more providers may be added
later."

Question:
> Which current requirement needs providers found at runtime rather than one
> explicit boundary?

If none does, the walkthrough may show speculative generalization rather than a
capability the work needs.
