# Tests

Use this reference when deciding what a test proves, which behaviour is worth
one, and why a suite is hard to change.

Tests are production assets. Keep them readable, deterministic, and easy to
change alongside legitimate behaviour.

## One behavioural concept

A test tells one coherent story. It may need several assertions to prove that
story — the useful rule is one *concept*, not one `assert`.

Split a test where a failure could represent unrelated behaviour, or where the
setup and the assertions describe independent scenarios. Those are the two
symptoms; the count of assertions is not one.

Use names, fixtures, builders and small helpers to create a domain-specific
testing vocabulary. Keep that vocabulary simpler than the production behaviour
it explains — a test helper that needs its own tests has stopped helping.

## Desirable properties

Prefer tests that are:

- fast enough to run at the intended feedback point;
- independent in state and ordering;
- repeatable across ordinary environments;
- self-checking, needing no manual interpretation;
- written close enough to the behaviour change to guide and protect it.

These are trade-offs across test levels, not properties to force into every
test. A necessary integration or concurrency test may be slower; isolate it and
make its role clear rather than pretending it is a unit test.

## What is worth covering

Use coverage to find unexamined behaviour, not as proof of correctness.
Coverage is evidence about execution, not about assertions.

Prioritise:

- boundaries and off-by-one conditions;
- invalid, empty, missing, maximum and minimum inputs;
- a regression case near a discovered bug, at the mechanism that failed;
- failure translation and cleanup;
- authorisation, ordering, transaction and concurrency invariants;
- code whose change risk is high despite a low branch count.

## What a test should not be coupled to

A test coupled to implementation detail fails when the implementation is
improved and passes when the behaviour breaks in a way the implementation
preserved. Assert on observable behaviour — what a caller can see — rather than
on the steps taken to produce it.

## An ignored test is unresolved evidence

A skipped, ignored or flaky test is a finding nobody closed. Track its reason,
its owner and its exit condition, or fix it. Do not normalise an unexplained
red build: a suite that is expected to be partly red has stopped being a
signal.

## Review prompts

- Is important behaviour untested, and which behaviour specifically?
- Are boundaries and failure paths covered, or only the happy path?
- Does a regression fix have a test near the mechanism that failed?
- Do any tests assert on implementation steps rather than observable
  behaviour?
- Is a slow test sitting at a level where faster evidence would do?
- Does every skipped or flaky test carry a reason, an owner and an exit
  condition?
