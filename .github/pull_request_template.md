# Pull Request

## Summary

<!--
Context first, then the drawing, then the three fields — the drawing leads and
the prose covers only what the picture cannot say. Readable on its own by
someone who will not scroll further.

Product perspective, not engineering: no file paths, no branch conventions, no
slicing rationale, no task IDs. Those belong in Implementation Details, and a
reviewer who needs them will read that far.
-->

**Context:** [What the thing is, for a reader who has never seen it. One or two
sentences, none of them about this change. No paths, no issue numbers. A
reviewer who cannot resolve the nouns in **What** cannot use **Why** or
**Impact** at all.]

### Before / After
<!--
Strongly recommended, and usually the highest-value part of the description. One
picture of the problem and the shape of the fix replaces the three paragraphs a
reviewer would otherwise have to assemble in their head — and it is easier to
disagree with, which is the point of a review.

Draw whenever the reader has to hold a structure — a set, a location, a count, a
branch, a dependency. Short prose still earns a drawing; the question is whether
the structure survives being read one clause at a time, not whether the drawing
is quicker than the sentence.

This section is rendered on github.com, so the terminal-ASCII rule from
`design-levels` and `architecture-design` does not reach it — those govern skills
and records, which agents read as source.

That is one surface, not every surface. The GitHub mobile app shows a mermaid
fence as its own source, and the two forms fail differently when they do not
render: clipped ASCII is still a partial picture, clipped mermaid is syntax.

So prefer mermaid when you want the graph laid out for you and the reader is at a
desk. Prefer ASCII when the drawing has to survive a phone or a terminal, when
your placement carries meaning a layout engine would discard — grouping,
alignment, or counts positioned to be compared — and for terminal output shown
verbatim.

Pick whatever the change actually is:
- **UI** → a wireframe or a before/after screenshot. ASCII boxes are fine; the
  point is the layout and the flow, not the pixels.
- **A flow, a state machine, a sequence** → a `mermaid` fenced block, where the
  reader is on the web. github.com renders it inline; keep it to the nodes that
  changed. ASCII if it has to read on a phone.
- **An architecture** → usually ASCII. Band membership and nesting are the
  content, and an edge into a grouped box forces every member out into its own
  node before a layout engine can anchor it.
- **A CLI** → the terminal before and the terminal after, verbatim.
- **A data shape** → the record before and after, trimmed to the fields that moved.

Which drawing the material calls for is decided by the form-selection table in
the `conversation-response-shape` skill; that table is the single owner, so pick
from it rather than restating it here.
-->

**What:** [The capability added or changed, as a user would describe it]
**Why:** [The gap it closes — what was broken, missing, or painful before]
**Impact:** [Who benefits, and what they can now do]

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

## Review Panel
<!--
The reconciled disposition table from `fanning-out-code-review`: every finding
from every reviewer, what was done about it, and why. The roster line goes with
it — a reviewer that returned nothing and a reviewer that found nothing are the
same silence, and only the roster tells them apart.

A panel that found nothing still fills this in: who reviewed, what each checked,
no findings. An empty section here and a panel that never ran read identically,
and the second is what this section exists to make visible.
-->

| # | Reviewer | Finding | Disposition |
|---|---|---|---|
|   |          |         |             |

roster:

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings or errors
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
- [ ] Every fully completed issue is under `Closes` with a closing keyword, not only `Related`
- [ ] Anything this change turned up in passing is named under Additional Context, with whether it was filed

## Documentation

- [ ] README updated (if needed)
- [ ] Code comments added/updated
- [ ] API documentation updated (if applicable)
- [ ] No documentation changes needed

## Deployment Notes
<!-- Migrations, environment variables, dependency or version bumps, ordering
constraints against another PR. -->

## Additional Context
<!--
Anything else a reviewer should know: open questions, follow-ups you are
deliberately leaving, concerns you could not resolve.

Then the other half, which is not about this change at all: what did working on
it turn up? A defect noticed in passing, a claim in the issue that proved wrong,
a reference that 404s, a second instance of the bug somewhere else. Name each
one and say whether it was filed. An unfiled finding lives only in a session
transcript that is discarded, and a filed one outlives this PR — nobody searches
merged bodies.

Where a finding is a measurement, write the measurement and the conclusion as
two things. "Nothing else scores above 1%" is a number; "nothing else is
derived" is a claim about the world that the number does not establish, and the
second is where a correct measurement goes wrong.
-->
