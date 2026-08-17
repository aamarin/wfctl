# Pull Request

## Summary

<!--
Two or three sentences, readable on their own by someone who will not scroll
further. What can someone do after this merges that they could not before.

Product perspective, not engineering: no file paths, no branch conventions, no
slicing rationale, no task IDs. Those belong in Implementation Details, and a
reviewer who needs them will read that far.
-->

**What:** [The capability added or changed, as a user would describe it]
**Why:** [The gap it closes — what was broken, missing, or painful before]
**Impact:** [Who benefits, and what they can now do]

## Before / After
<!--
Strongly recommended, and usually the highest-value part of the description. One
picture of the problem and the shape of the fix replaces the three paragraphs a
reviewer would otherwise have to assemble in their head — and it is easier to
disagree with, which is the point of a review.

Pick whatever the change actually is:
- **UI** → a wireframe or a before/after screenshot. ASCII boxes are fine; the
  point is the layout and the flow, not the pixels.
- **A flow, a state machine, an architecture** → a `mermaid` fenced block. GitHub
  renders it inline; keep it to the nodes that changed.
- **A CLI** → the terminal before and the terminal after, verbatim.
- **A data shape** → the record before and after, trimmed to the fields that moved.

Two small diagrams beat one that tries to be complete. If a diagram takes longer
to read than the prose it replaced, delete it.
-->

---

## Type of Change
<!-- Check the box that applies. Put an 'x' in the box like this: [x] -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Code refactor/cleanup
- [ ] Performance improvement
- [ ] Testing improvements

## Issue Links
<!--
Use GitHub closing keywords for every issue this PR fully resolves. They
auto-close only on merge into the default branch.

One PR closes exactly one issue. A PR that is the final one for a parent epic may
also close the parent — but only when every parent acceptance criterion is
satisfied, including any manual step the code cannot do. If the epic still has
outstanding work, list it under Related and close it by hand.

An issue referenced for context or partial progress goes under Related, without a
closing keyword.

Before submitting, check for issues this work already finished: the ones that get
missed are from an older spec that was since renamed or split. For each file you
touched, ask whether a pre-existing issue tracked that exact task.
-->

### Closes
- Closes #(issue number)

### Related
- Related: #(issue number)

## What Changed?

### Changes Made
-
-
-

### Implementation Details
<!--
Engineering rationale: architectural choices, trade-offs, scope boundaries, what
was deliberately deferred and why, and why this approach over the alternatives.

Also the place for a premise that turned out wrong — a task whose assumption did
not hold, or a check that could not mean what it was written to mean. Saying so
is worth more than a table of green ticks.
-->

## How Has This Been Tested?

- [ ] Unit tests added/updated
- [ ] Manual testing performed
- [ ] Edge cases considered and tested
- [ ] Tested across the environments/browsers this affects (if applicable)

### Test Details
<!--
What you ran, and what it proved. Name the tests that cover each claim rather
than restating that the suite is green.

A negative case verified by hand — the check failing when it should — is worth
more here than the passing run, because it is the half that is usually skipped.

Proof belongs here rather than in Before / After: that section explains the
change, this one shows it working. A screenshot or a GIF counts.
-->

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings or errors
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
- [ ] Every fully completed issue is under `Closes` with a closing keyword, not only `Related`

## Documentation

- [ ] README updated (if needed)
- [ ] Code comments added/updated
- [ ] API documentation updated (if applicable)
- [ ] No documentation changes needed

## Deployment Notes
<!-- Migrations, environment variables, dependency or version bumps, ordering
constraints against another PR. -->

## Additional Context
<!-- Anything else a reviewer should know: open questions, follow-ups you are
deliberately leaving, concerns you could not resolve. -->
