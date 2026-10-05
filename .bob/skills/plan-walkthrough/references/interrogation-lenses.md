# Interrogation Lenses

Use these lenses to find a small number of high-value questions. They are not a
checklist to exhaust.

By the time a walkthrough runs, earlier steps have already decided a lot: the
architecture records, the `Considered` sections of the design records, the
checked and assumed split in `design.md`, and the verification the plan names.
The lenses marked **explain, don't reopen** below ask the person to explain
those decisions. They never ask whether the decision was right. Reopening a
settled decision is the plan review's job, not this check's.

Comprehension leads, because it is the one thing no other step in wfctl tests.

## 1. Comprehension

Use this when generated artifacts may be hiding a weak mental model.

Probes:
- Explain this decision without reading the plan back to me.
- Walk through one concrete request from entry point to durable state.
- If this breaks in production, where would you start and why?
- Which line of reasoning would you revisit first if the assumption proves false?

The goal is not memory recall. It is an operational explanation of the system.

## 2. Intent

Test whether the work solves the actual problem rather than only the literal
wording of a requirement.

Plan probes:
- What user or system outcome must change if this succeeds?
- Which part of the design is essential to that outcome?
- Could the requirement be met literally while still missing the intended behavior?

Change probes:
- Point to the code path that creates the intended behavior.
- What would still pass the tests while violating the real intent?

## 3. Rationale and alternatives (explain, don't reopen)

The design records' `Considered` sections already say why the chosen approach
beat the alternatives. Ask the person to explain that reasoning in their own
words.

Probes:
- The record rejected the simplest alternative. Why does it lose here?
- Which tradeoff made the rejected option worse for this change?
- What new constraint would make you reverse this decision?

Do not ask for an alternatives matrix, and do not argue for an option the record
rejected.

## 4. Assumptions (explain, don't reopen)

`design.md` already splits what was checked from what was assumed. Ask the
person to explain the assumed half.

Probes:
- The design lists this as assumed. What has to stay true for it to hold?
- How would you find out it stopped being true?
- What are you relying on that the repository does not enforce?

Treat "should", "usually", and "the framework handles it" as prompts to ask for
the actual mechanism.

## 5. Boundaries and ownership (explain, don't reopen)

The architecture records already say who owns each piece of truth and why the
other side cannot compute it. Ask the person to explain that ownership.

Probes:
- The record says this side owns the value. Why can't the other side compute it?
- Who is allowed to change this state?
- Which component wins when two sources disagree?
- Does this change add a dependency across a boundary the records drew?

## 6. State and lifecycle

Test transitions, invalidation, cleanup, and long-lived state.

Probes:
- What are the valid states before and after this operation?
- What event moves the system between them?
- What invalidates cached or derived state?
- Can two actors race to perform the same transition?
- What survives a process restart?

## 7. Failure and recovery

Require an operational model of the paths that are not the happy one.

Probes:
- What happens after partial success?
- What happens if the call times out after the remote side commits?
- Is retry safe? What enforces that?
- Which failures are surfaced, retried, compensated, or left for manual repair?
- What would you inspect first during an incident?

## 8. Evidence and verification (explain, don't reopen)

The plan already names how the work is verified. Ask the person to explain what
that verification proves and what it does not.

Probes:
- The plan verifies this with a named test. What behavior does that test prove?
- Which invariant is enforced by code, schema, type, test, or runtime check?
- Which important claim has no verification path in the plan?

Do not accept a passing test suite as the whole answer when the question is
about intent or production failure behavior.

## 9. Edge cases and adversarial inputs

Probe inputs or timing that break the happy path.

Probes:
- Which input shape is valid but unusual?
- What happens at empty, maximum, duplicate, reordered, or concurrent input?
- What happens if an upstream dependency returns stale or contradictory data?

Prefer edge cases from the actual domain over generic null checks.

## 10. Change impact and second-order effects

Test what the decision makes easier or harder later.

Probes:
- What existing behavior can this silently change?
- Which consumers now depend on this representation or timing?
- What migration or rollback path exists?
- What future change becomes expensive because of this boundary or data shape?

## 11. Scope and deliberate non-goals

Test whether the plan solves the right-sized problem.

Probes:
- What did you deliberately leave out?
- Which tempting generalization is unnecessary for this requirement?
- What would make the current narrow solution insufficient?

Use this lens against both under-design and speculative overengineering.
