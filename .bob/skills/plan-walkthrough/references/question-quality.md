# Question Quality

A good walkthrough question is specific enough that a shallow answer is visible,
and important enough that the answer can affect the work.

## Selection rule

Prefer the question that best meets all three conditions:

1. The answer could change the design, the implementation, the verification
   strategy, or the risk accepted.
2. The current artifacts do not already establish the answer.
3. A wrong assumption would be expensive, hard to debug, or likely to spread into
   later work.

## Ask one question at a time

Do not send a wall of questions. Asking one at a time lets the next probe depend
on the actual answer.

If several concerns exist, keep a private queue and ask the highest-impact
unresolved one first.

## Ask about mechanisms

Weak:
- Did you consider failure handling?
- Is this scalable?
- Are retries idempotent?
- Did you think about edge cases?

Strong:
- The worker can retry after losing the response. What prevents the same command
  from applying twice?
- Two writers can update this record. Which operation wins when they race, and
  where is that enforced?
- This cache lives for ten minutes. What event makes a value stale before then,
  and how is that event observed?

## Challenge assertions

Treat these answers as signals for a follow-up:

- "should"
- "normally"
- "probably"
- "the framework handles it"
- "the tests cover it"
- "we can add that later"
- naming a pattern without naming the mechanism that enforces it

Useful follow-ups:
- Where is that guaranteed?
- What concrete evidence establishes that?
- Walk me through the failure case.
- Which component owns that decision?
- What happens if that assumption is false?

Push at most twice on the same issue. Then record the gap.

## Tell explanation from recitation

Generated plans and code comments can be read back without being understood.
When understanding is uncertain, ask for a concrete walkthrough of an execution
or a failure.

Prefer:
- Walk through what happens from the request arriving to the commit.
- Show me the system state after dependency B succeeds and C times out.
- If this alert fires at 2 AM, what evidence would you look at first?

Avoid trivia unless it is needed to explain the decision.

## Skip what is already established

Do not ask a question only because it appears in the lens catalog. Skip it when
accepted architecture records, tests, schemas, or clear code already establish
the answer and nothing contradicts them.

The walkthrough is a pressure test, not a ritual.

## Stop conditions

End the walkthrough when:

- the material decisions are grounded;
- required revisions are identified clearly;
- intentional deferrals have an owner or a trigger;
- unresolved blockers are explicit.

Do not keep asking low-value questions to make the walkthrough feel thorough.
