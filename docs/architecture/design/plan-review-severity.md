---
status: proposed
---

# A plan-review finding is graded BLOCKER, MAJOR, or MINOR, and a missing answer is a category rather than a grade

## Context

Every finding in a plan-review report carries two labels. The priority says how
urgently the finding must be acted on, and the category says what kind of
problem it is. The candidate skill grades on four priorities: BLOCKER, MAJOR,
MINOR, and QUESTION.

Three of those answer the urgency question. QUESTION answers the other one: it
says information is missing, which is also what the category `Missing
Information` says. And the candidate's own BLOCKER test covers the same ground,
since one of its triggers is a required behaviour that cannot be built "without
making a consequential product/architecture decision not present in the
artifacts". A reviewer holding a missing answer that stops the plan can
therefore grade it either BLOCKER or QUESTION, and both readings are correct.

That overlap matters once the grade feeds a verdict. The scan file this pass
writes carries one of `satisfied`, `unsatisfied`, or `inconclusive`, and the
verdict turns on whether a BLOCKER is still open. A missing answer graded
QUESTION passes that verdict however much it matters.

`the-scan-is-attested-where-the-reviewer-reads` places the scan file and is not
restated. #100 is the open question of one shape for pipeline gates, and this
record gives the pass a verdict in the vocabulary that shape already uses.

## Verified

- The candidate's `SKILL.md:121` - `124` defines the four priorities, and
  `SKILL.md:128` lists `Missing Information` as the first category.
- `references/review-rubric.md:129` puts "a consequential product/architecture
  decision not present in the artifacts" under BLOCKER, and `:149` defines
  QUESTION as "the reviewer needs an answer from the author/domain owner and
  existing evidence cannot safely select one".
- `wfctl/agents/skills/code-review/SKILL.md:121` - `123` defines BLOCKER,
  WARNING, and NIT in code terms: a bug, security hole, or data-loss risk; a
  quality or maintainability cost; and a style or naming preference.
- `wfctl/agents/skills/clean-code/references/review-catalog.md` says of its
  Critical to Low scale and `code-review`'s that "they are different questions
  and this catalog converts between them nowhere".
- `wfctl/agents/skills/writing-a-scan-file/SKILL.md:115` fixes the verdict to
  exactly one of `satisfied`, `unsatisfied`, and `inconclusive`.

## Assumed

- That a reviewer grades a missing answer by its consequence as reliably as any
  other finding. Falsified if reports show missing answers graded MINOR to keep
  a verdict green, which is grade inflation and would be no more likely here
  than for any other category.
- That the verdict keeps reading one grade. Falsified if #100 settles a gate
  shape that reads more than one, and then the case for folding QUESTION
  weakens, because a verdict counting open QUESTIONs becomes as cheap as one
  counting BLOCKERs.

## Direct baseline

Keep the candidate's four priorities as written. The verdict reads open
BLOCKERs, and a QUESTION is reported in the summary counts beside the other
three.

## Decision

A finding's priority is BLOCKER, MAJOR, or MINOR, with the candidate's own
definitions. QUESTION leaves the priority line. A missing answer is filed under
the `Missing Information` category and graded by what it blocks, so a missing
answer that stops decomposition is a BLOCKER, and one that barely matters is
MINOR.

The verdict follows from the grades:

1. Any BLOCKER still open makes the verdict `unsatisfied`.
2. A missing `spec.md` or `plan.md` makes it `inconclusive`.
3. Anything else is `satisfied`.

The labels are the candidate's, not `code-review`'s. They grade the same kind of
thing, and they define it for plans rather than for code.

## Diagram

```
             baseline                              decision

stable    ┌────────────────┐                   ┌────────────────┐
          │ finding        │                   │ finding        │
          └────────────────┘                   └────────────────┘
            │ graded          │ filed            │ graded     │ filed
          ┌─▼──────────────┐ ┌▼───────────┐    ┌─▼─────────┐ ┌▼───────────┐
          │ BLOCKER MAJOR  │ │ category   │    │ BLOCKER   │ │ category   │
          │ MINOR QUESTION │ │ incl.      │    │ MAJOR     │ │ incl.      │
          │                │ │ Missing    │    │ MINOR     │ │ Missing    │
          │                │ │ Information│    │           │ │ Information│
          └────────────────┘ └────────────┘    └───────────┘ └────────────┘
            │ BLOCKER only                       │ BLOCKER only
═══ report in FEATURE_DIR / scan file, as the-scan-is-attested ═════════════
            │                                    │
volatile  ┌─▼──────────────┐                   ┌─▼──────────────┐
          │ verdict        │                   │ verdict        │
          └────────────────┘                   └────────────────┘
```

The graphs differ by one grade. In the baseline a missing answer can be graded
QUESTION, and QUESTION never reaches the verdict. In the decision every finding,
a missing answer included, is graded on the scale the verdict reads, so the only
finding that passes the verdict is one the reviewer judged not to block.

## Considered

- **The baseline, four grades.** It keeps the candidate unchanged. It loses
  because a critical missing answer graded QUESTION leaves the verdict
  `satisfied`, and the rubric gives the reviewer no way to prefer BLOCKER over
  QUESTION for it.
- **Four grades, with the verdict also counting open QUESTIONs.** This closes
  the same gap and keeps a grade that says a person has to supply the answer. It loses because every question would then block, including the ones
  that barely matter, and telling those apart means grading a question by
  consequence, which is the decision above reached by a longer route.
- **`code-review`'s BLOCKER, WARNING, and NIT.** It would give wfctl one set of
  labels across both reviews. It loses because the definitions would all be
  rewritten for plans, so only the words would be shared, and shared words with
  different meanings read as convertible when they are not. NIT is the sharpest
  case: it means a style preference in `code-review`, and MINOR covers any
  improvement that forces no guess.
- **`clean-code`'s Critical to Low.** It grades a consequence rather than what
  the author must do, and the catalog itself says it converts to no other scale.

## Consequences

The priority and the category now answer separate questions, and the overlap
between BLOCKER's third trigger and QUESTION is gone.

A reader looking for what needs a person's answer filters on the `Missing
Information` category instead of a grade. The candidate's report format loses
its QUESTION line in the summary counts (`references/report-format.md:32` -
`35`) and in the priority field (`:43`).

The failure mode is the one every graded review has: a reviewer who wants a
green verdict grades a BLOCKER as MAJOR. Nothing mechanical catches that, and
the report's evidence lines are what a human reads to challenge it.

## Verification

The shipped report format lists three priorities, and a test holds the skill's
priority list against the verdict rule in the wrapper, so a fourth grade added
to one and not the other fails. A review question for the first real report:
does any `Missing Information` finding carry a grade its evidence does not
support?

## Log

- 2026-09-26  proposed  — #501 level 3. The candidate's QUESTION grade overlapped
  its own BLOCKER test and could not reach the verdict. Andre chose to fold it
  into the category after comparing it with keeping four grades.
- 2026-09-27  renamed   — from `501-plan-review-severity`. Record names carry no
  issue-number prefix.
