---
status: proposed
---

# One status mutation, parameterized by the transition — `supersede` and `accept` are its two callers

## Context

`a-human-accepts-a-decision` puts a second status transition into `_arch`:
`proposed → accepted`, alongside the `→ superseded` that `supersede()` already
performs. The two rewrite the same file in the same two places — one frontmatter
key, one appended `Log` line — and the machinery in between is where the file
format's sharp edges live.

Nothing about the level-2 record forces a shape here. It says a human accepts and
wfctl records; whether that is one function or two is this record's question.

## Verified

- `_arch.py:404` `supersede(record, date, reason)` is the module's only status
  mutation, and `grep` finds no caller outside `tests/test_arch_records.py` — it
  has never been reachable from the CLI.
- `_arch.py:59` `_frontmatter_end`'s docstring: *"The single place that knows how
  far frontmatter extends, so the parser and `supersede` cannot disagree about
  which lines are settings and which are body prose."*
- `_arch.py:74` `_key_value`'s docstring: *"The single rule for what counts as a
  key, shared by the parser and by `supersede`."*
- `supersede` carries four hazards in its body, each with its comment: `newline=""`
  so a CRLF record is not rewritten whole; the `status` key found **backwards**
  because `_frontmatter` takes the last of a repeated key; a missing trailing
  newline welded onto the previous line if not fixed; and `write_atomic` because
  a torn write loses a hand-authored decision.
- `_log_bounds` (`_arch.py:374`) returns the end of the `## Log` section, not end
  of file, "because `Log` is last by convention only".
- Every `Log` line in `docs/architecture/` pads the status to a 12-character
  column — `accepted` + 4 spaces, `proposed` + 4, `superseded` + 2 — and
  `supersede` writes that column as two literal spaces after the word
  `superseded`, naming no width.

## Assumed

- No third status transition arrives soon. `rejected` and `retired` have no
  consumer and no demand (#321 scope), so the parameterized function has two
  callers and not five. Falsified by a fourth transition needing per-transition
  behaviour rather than a different word — at which point the parameter is the
  wrong seam and a per-transition function is right.
- The 12-column `Log` field is a convention worth preserving rather than an
  accident of the first record. Falsified by finding a record whose column is a
  different width and was written by hand deliberately; a `grep` over the
  existing records found none.

## Direct baseline

Write `accept()` beside `supersede()` as a second, independent function: open
with `newline=""`, find the frontmatter end, scan backwards for the `status` key,
find the `Log` bounds, fix a missing trailing newline, insert, `write_atomic`.
Around forty lines, most of them identical to their neighbours above.

It is the smallest thing that works and it introduces no abstraction. What it
costs is a third reader of the file format that has to agree with the other two.
`_frontmatter_end` and `_key_value` both say in their own docstrings that they
exist so the parser and `supersede` *cannot* disagree; a copy of `supersede`'s
body is a place for the disagreement to reappear, and each of the four hazards
above is one a copy can lose silently — a dropped `newline=""` rewrites every
line of a CRLF record, and a forwards scan for `status` edits a line the parser
ignores, so the log records a transition the record does not carry.

## Decision

One private `_set_status(record, status, date, note)` performs the mutation.
`supersede` and `accept` are two-line callers that name their transition and pass
their note through.

`accept` carries the one guard that is not shared: it refuses a record whose
current status is anything but `proposed`.

## Diagram

```
          baseline                          decision

stable    ┌──────────────────┐              ┌──────────────────┐
          │ _frontmatter_end │              │ _frontmatter_end │
          │ _key_value       │              │ _key_value       │
          │ _log_bounds      │              │ _log_bounds      │
          └──────────────────┘              └──────────────────┘
              ▲          ▲                        ▲
              │ calls    │ calls                  │ calls
════ the file format is _arch's ══════════════════╪═══════════════
              │          │                        │
volatile  ┌───┴─────┐ ┌──┴─────┐            ┌─────┴───────┐
          │supersede│ │ accept │            │ _set_status │
          └─────────┘ └────────┘            └─────────────┘
                                              ▲          ▲
                                              │ calls    │ calls
                                          ┌───┴─────┐ ┌──┴─────┐
                                          │supersede│ │ accept │
                                          └─────────┘ └────────┘
```

The graphs differ by how many components hold the four hazards. In the baseline
each transition holds its own copy and the format helpers are called twice from
two bodies that must stay in step by hand; in the decision one body holds them
and the transitions hold only their own word and their own guard.

## Considered

- **The direct baseline, two independent functions** — honest, and the diff is
  easier to read because each function is whole. It loses on the pressure named
  in Context: the format helpers were written to stop the parser and `supersede`
  disagreeing, and a second copy of `supersede`'s body is where that guarantee
  is spent.
- **Make `supersede` itself take a status argument, with no wrapper** — fewer
  names, and the call sites read `supersede(record, "accepted", …)`, which is a
  sentence that is not true. A function named for one transition performing
  another is the kind of thing a reader trusts and is wrong about.
- **A `Transition` class or table, one row per status, carrying its own guard** —
  the shape the assumed fourth transition would want, and correct if it arrives.
  Two rows do not pay for it, and a table of two makes the guard on `accept` look
  like a field every transition has rather than the one exception it is.
- **Put the `proposed`-only guard in the CLI rather than in `accept`** — keeps
  `_arch` free of policy, which is a real principle here. Rejected because the
  guard exists to stop a second `Log` line claiming a second agreement, which is
  a fact about the record, and a second caller of `accept()` reaching it through
  the module would not carry the CLI's copy.

## Consequences

`supersede`'s body moves to `_set_status` with its four comments, so a reviewer
reading this change sees a rename of a working function rather than new logic —
and a regression in it would be a regression in `supersede`, which the existing
tests already cover.

The `Log` column width becomes a named constant rather than two literal spaces.
That is a real change to `supersede`'s output only if the constant is wrong;
`superseded` padded to 12 is the two spaces it already writes.

What is now harder: a transition needing something `_set_status` does not do has
to either widen the parameter list for every caller or step outside the shared
body. With two callers that is cheap to notice; the assumption above is where it
would bite.

## Verification

- The existing `supersede` tests pass unchanged — they are the regression suite
  for `_set_status`, which is why the body moves rather than being rewritten.
- A test that a superseded, rejected, retired or already-accepted record is
  refused by `accept` and gains no second `Log` line.
- A test that a CRLF record accepted through `accept` has exactly two changed
  lines, which is the hazard a copied body loses first.

## Log

- 2026-09-09  proposed  — #321's level-3 gate: the second status transition and
  where its shared machinery lives
