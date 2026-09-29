---
status: proposed
---

# A plan review grades each finding BLOCKER, MAJOR, or MINOR, and a missing answer is a kind of finding rather than a grade of its own

**What does this record decide?**
Every plan-review finding gets one of three grades: BLOCKER, MAJOR, or MINOR. A question the plan leaves unanswered is not a fourth grade. The reviewer grades it by what it holds up, so one that stops the work is a BLOCKER and holds the pipeline.

## Context

The `the-scan-is-attested-where-the-reviewer-reads` record decides that every
review writes a scan file into the change, with a verdict of `satisfied`,
`unsatisfied`, or `inconclusive`. This means the grade a reviewer gives each
finding decides whether the plan review passes.

Every finding carries two labels. The grade says how urgently the plan owner has
to act on it. The category says what kind of problem it is. The candidate skill
uses four grades: BLOCKER, MAJOR, MINOR, and QUESTION.

Three of those say how urgent a finding is. QUESTION says something different.
It says an answer is missing, which the category `Missing Information` already
says. The candidate's own BLOCKER test covers the same ground as well. One thing
that makes a finding a BLOCKER is a behaviour nobody can build without "making a
consequential product/architecture decision not present in the artifacts". This
means a reviewer holding a missing answer that stops the plan can grade it
BLOCKER or QUESTION, and both are correct.

That overlap matters because the verdict turns on whether a BLOCKER is still
open. A missing answer graded QUESTION passes the verdict, however much it
matters.

Where the scan file lives is decided in that earlier record and isn't repeated
here. #100 is the open question of one shape for every pipeline gate, and this
record gives the plan review a verdict in the words that shape already uses.

## Verified

- The candidate's `SKILL.md:121` - `124` defines the four grades, and
  `SKILL.md:128` lists `Missing Information` as the first category.
- `references/review-rubric.md:129` puts "a consequential product/architecture
  decision not present in the artifacts" under BLOCKER, and `:149` defines
  QUESTION as "the reviewer needs an answer from the author/domain owner and
  existing evidence cannot safely select one".
- `wfctl/agents/skills/code-review/SKILL.md:121` - `123` defines BLOCKER,
  WARNING, and NIT for code. They mean a bug, security hole, or data-loss risk;
  a quality or maintainability cost; and a style or naming preference.
- `wfctl/agents/skills/clean-code/references/review-catalog.md` says of its
  Critical to Low scale and `code-review`'s that "they are different questions
  and this catalog converts between them nowhere".
- `wfctl/agents/skills/writing-a-scan-file/SKILL.md:115` fixes the verdict to
  exactly one of `satisfied`, `unsatisfied`, and `inconclusive`.

## Assumed

- The reviewer grades a missing answer by what it holds up as reliably as any
  other finding. This is wrong if reports show missing answers graded MINOR to
  keep a verdict green. That is grade inflation, and it is no more likely here
  than for any other kind of finding.
- The verdict keeps reading one grade. This is wrong if #100 settles on a gate
  that reads more than one. The case for dropping QUESTION then weakens, because
  a verdict that counts open QUESTIONs becomes as cheap as one that counts
  BLOCKERs.

## Direct baseline

Keep the candidate's four grades as written. The verdict reads open BLOCKERs.
The reviewer counts QUESTIONs in the summary beside the other three, and they
never reach the verdict.

## Decision

The reviewer grades every finding BLOCKER, MAJOR, or MINOR, with the
candidate's own definitions. QUESTION is no longer a grade. The reviewer files a
missing answer under the `Missing Information` category and grades it by what
it holds up. A missing answer that stops the plan from being broken into tasks
is a BLOCKER. One that barely matters is MINOR.

The verdict follows from the grades, in this order:

1. Any BLOCKER still open makes the verdict `unsatisfied`.
2. A missing `spec.md` or `plan.md` makes it `inconclusive`.
3. Anything else is `satisfied`.

The grade names are the candidate's, not `code-review`'s. Both grade the same
kind of thing, and these define it for plans rather than for code.

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

The two sides differ by one grade. On the left, the reviewer can grade a
missing answer QUESTION, and QUESTION never reaches the verdict. On the right,
the reviewer grades every finding on the scale the verdict reads, missing
answers included. This means the only finding that gets past the verdict is one
the reviewer judged not to block.

## Considered

- **The baseline, four grades.** It leaves the candidate unchanged. It loses
  because a critical missing answer graded QUESTION still leaves the verdict
  `satisfied`, and nothing in the rubric tells the reviewer to pick BLOCKER over
  QUESTION for it.
- **Four grades, with the verdict also counting open QUESTIONs.** This closes
  the same gap and keeps a grade that says the plan owner has to supply the
  answer. It loses because every question would then block, including the ones
  that barely matter. Telling those apart means grading a question by what it
  holds up, which is the decision above reached the long way round.
- **`code-review`'s BLOCKER, WARNING, and NIT.** wfctl would use one set of
  names across both reviews. It loses because every definition would have to be
  rewritten for plans, so only the words would be shared. Shared words with
  different meanings look convertible when they aren't. NIT shows it best. In
  `code-review` it means a style preference, while MINOR covers any improvement
  that forces no guess.
- **`clean-code`'s Critical to Low.** It grades a consequence rather than what
  the plan owner has to do, and the catalog itself says it converts to no other
  scale.

## Consequences

The grade and the category now answer separate questions, and the overlap
between BLOCKER's third test and QUESTION is gone.

The plan owner looking for the findings that need their answer filters on the
`Missing Information` category instead of a grade.

The way this fails is the way every graded review fails. A reviewer who wants a
green verdict grades a BLOCKER as MAJOR. Nothing automatic catches that. The
evidence lines in the report are what the plan owner or the pull request
reviewer reads to challenge it.

In the code, the candidate's report format drops its QUESTION line from the
summary counts (`references/report-format.md:32` - `35`) and from the grade
field (`:43`).

## Verification

The shipped report format lists three grades. A test holds the skill's list of
grades against the verdict rule in the `/plan-review` command, so a fourth grade
added to one and not the other fails the test. One question needs human review
on the first real report: does any `Missing Information` finding carry a grade
its evidence doesn't support?

## Log

- 2026-09-26  proposed  — #501 level 3. The candidate's QUESTION grade overlapped
  its own BLOCKER test and could not reach the verdict. Andre chose to fold it
  into the category after comparing it with keeping four grades.
- 2026-09-27  renamed   — from `501-plan-review-severity`. Record names carry no
  issue-number prefix.
- 2026-09-28  rewritten   — plain language first, and an opening question
