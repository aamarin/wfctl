# Plan review report format

Write the report to the report path the invoking command names, and replace any
earlier report whole. Use the structure below. A section may say `None
identified`, and `## Reviewed inputs` and `## Summary` are never left out.

## Two lines have to be exact

Whatever reads this report after the review reads two lines of it, and matches
them character for character. In a review that ran, both are written exactly as
below; a review that could not run writes neither, as § A review that could not
run says.

1. The `plan.md` row under `## Reviewed inputs`. Its first cell is exactly
   `plan.md`, and its second is the identity from
   `git hash-object --no-filters`, 40 lowercase hex characters, with nothing
   else in the cell.
2. The `BLOCKER: <n>` line under `## Summary`, alone on its line, where `<n>`
   counts the findings in this report whose status is `open` and whose priority
   is BLOCKER. A finding marked `fixed` is not counted, and neither is a finding
   only an earlier report carried.

A report that spells either line differently reads as a review that recorded no
plan or no count, and holds whatever waits on it. So `BLOCKER: 0 (none open)`,
`**BLOCKER:** 0`, and a `plan.md` row with a placeholder in place of the hash
are all wrong.

The other rows of `## Reviewed inputs` follow the same two-cell rule: a path in
the first cell, and in the second either the identity or `absent` for an input
the review looked for and did not find. The invoking command compares these rows
with the files to decide what kind of run comes next, so `missing`, `none`, a
placeholder, or an abbreviated hash in that cell reads as an input that changed.

## Example

A re-review, after an earlier review found one BLOCKER and the plan was revised
against it:

```markdown
# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 9f2c1e0d4b6a8c2e1f3a5b7d9e0c2a4f6b8d0e1c | technical strategy |
| spec.md | 3b7e0a9c1d5f2e8a4c6b0d2f9e1a3c5b7d9f0e2a | requirements |
| design.md | 5d8e2f4a6c0b1d3e5f7a9c2e4b6d8f0a1c3e5b7d | design-record index |
| docs/architecture/design/plan-review-boundaries.md | 7c1d3e5f9a0b2c4d6e8f1a3b5c7d9e0f2a4b6c8d | design record |
| research.md | 2a4c6e8f0b1d3f5a7c9e1b3d5f7a9c0e2b4d6f8a | planning evidence |
| docs/constitution.md | absent | constitution |
| plan-review.plan.md | 8e0a2c4f6b8d1e3a5c7f9b0d2e4a6c8f1b3d5e7a | base of this re-review |

## Review scope

- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification
- Conditional lenses: security and reliability did not apply, since the feature
  reads local files only and crosses no trust boundary
- Changed since the earlier report: `plan.md §Reader` and `plan.md §Verification`,
  reviewed together with `plan.md §Data model`, which names the reader's states
- Existing code inspected: `src/reader.py`
- Reviewers: the three lenses above, run in sequence by one agent

## Summary

BLOCKER: 0
MAJOR: 2
MINOR: 5

No BLOCKER findings identified in this review. PR-001 is fixed. The two MAJOR
findings are about retry behavior the plan leaves to the implementer.

## Findings

### PR-001: The reader has no state for a report with no count

- Priority: BLOCKER
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-004`: a report missing a line is promised evidence gone silent
  - `plan.md §Reader`: now lists the missing-count state and its reason text
- Finding: The earlier plan listed four reader states and none for a report
  with no count, so a report that dropped the line read as clean.
- Why it matters: A review that never wrote the count would have read as
  clean.
- Suggested response: Fixed by the revised `plan.md §Reader`.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-002: Retry after a partial write is unspecified

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `spec.md §FR-011`: the report records every input it read
  - `plan.md §Writing`: writes the report, then the copy, with no order on failure
- Finding: A run that stops between the two writes leaves a report whose copy is
  the previous plan.
- Why it matters: The next run diffs against a copy that does not match, and has
  to fall back to a full review.
- Suggested response: State the write order and what the next run does when the
  copy does not match.
- Corroborated by: single reviewer

One entry per finding, open and fixed alike. This example shows two of the
eight.

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-004 | plan.md §Reader | covered |
| FR-011 | plan.md §Writing | PR-002 |

## Assumptions challenged

- The report is written by one run at a time. Explicit in `plan.md §Writing`,
  and not verified.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- `plan.md §Reader` checks the identity before the count, so an edited plan
  never reads as reviewed on the strength of an old count.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
```

## The header lines

`Review state` is `completed`, or `not run` for a review that could not run.
`Review type` is `full` or `re-review`, and on a review that could not run it is
`not run (<input> missing)`, with no full-review reason. A full review that ran because a
re-review was not possible says why on a line of its own under
`## Review scope`:

```text
- Full review: the plan copy's identity does not match the earlier report's
  plan.md row, so the copy was treated as missing
```

The three reasons are no earlier report, no plan copy, and a copy whose identity
does not match the earlier report's `plan.md` row.

## A finding

Each finding carries these fields, in this order: `Priority` (BLOCKER, MAJOR, or
MINOR), `Category`, `Status` (`open` or `fixed`), `Evidence`, `Finding`, `Why it
matters`, `Suggested response`, and `Corroborated by`. A finding keeps its ID
across re-reviews, and a fixed finding stays in the report with its status
changed, so a reader can see what the revision addressed.

## A review that could not run

When `spec.md` or `plan.md` is missing, the report says so and records what it
could. Write `Review state: not run`, give the missing input's row the identity
`absent`, and name the missing input under `## Review scope`. Write no count
lines under `## Summary`, only a sentence saying the review did not run. A count
of zero would read as a review that ran and found nothing, which is the opposite
of what happened.

## Evidence location style

Prefer stable headings or requirement IDs over raw line numbers, since markdown
line numbers move during ordinary editing. Where a line range is available and
useful, give both the heading or ID and the range.

A weak evidence line:

> Architecture seems tightly coupled.

A strong one:

> `plan.md §Write path` makes `ReportingService` create and mutate ledger rows
> directly, while the design record `ledger-owns-postings.md §Decision` assigns
> posting ownership to the ledger boundary alone. The plan crosses the accepted
> ownership boundary without an integration contract.
