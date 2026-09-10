---
status: proposed
---

# The four facts render as their own block in the console, not as annotation text a human never reads

## Context

`readiness-is-not-a-step-state` decides that the payload carries four facts, each
read from its own owner. It does not decide where a reader meets them, and the
two scope items #299 states pull against each other: `status` must show *which*
fact is missing (item 2), and nothing may collapse back into one field (item 3).

The pressure is the console view. It is scanned for "where am I", eight rows
deep, and it is the only surface most readers ever see. `--json` is where a
consumer asks a precise question, and no human opens it. So a fact that reaches
only `--json` satisfies item 3 and fails the reason the issue was filed: a person
could not tell two situations apart.

The handoff for this branch recommended the `--json`-only shape and said so
explicitly as a recommendation rather than a decision, naming the counter-argument
above as real. It is the baseline below.

## Verified

- `wfctl/cli.py:65` — `_STATE_GLYPH` maps four state names to a glyph and a rich
  style, with the comment "The only place a state is drawn."
- `wfctl/cli.py:460` — the step loop renders `name`, glyph, `annotation`,
  `← current`, one line per step, and nothing else.
- `wfctl/_predicates.py:861` — `implement` composes `f"{tally}  {blocked}"` when
  a verification block holds, so its annotation already carries two facts joined
  by whitespace.
- `tests/test_pipeline_payload_snapshot.py:44` imports `_infer_steps` alone, so
  the pinned snapshot covers step dicts and not `PipelineReport` fields.
- `wfctl/_predicates.py:490` — `design_block`'s docstring: "A record anywhere
  under the arch root answers, whatever its status: a `proposed` record still
  means the question was put."
- `wfctl/_session.py:380` — `resolved_notify` returns `NotifyGrant(False,
  "unset")` when no line resolved one, and the grant carries a `source` naming
  which of the seven answers applied.

## Assumed

- Four extra console lines do not make `wfctl status` too long to scan. What
  would falsify it: a reader who starts piping `status` through `head` to find
  the step table, or asks for a flag that hides the block.
- ~~The longest fact line — a slug plus a detail — fits 80 columns.~~
  **Falsified during implementation, and the line is kept anyway.** One waiting
  record fits; two do not, because each is named with its own status. The
  alternative was to truncate the list, and truncating drops which record is
  waiting — the exact thing this feature exists to say. A wrapped line naming
  every waiting record beats a short line naming some of them, so what changes is
  the claim rather than the design.
- Four extra lines is the block's steady-state height. Falsified by a branch with
  several un-ruled records, where the architecture line wraps; that branch has a
  real problem and the extra line is the report of it.
- ~~Resolving the arch root and asking git per `status` is cheap enough to leave
  unconditional.~~ **Measured by the review panel, and it was not.** The first
  implementation took `build_report` from 10 git subprocesses to 19, because the
  `implement` predicate and the definition-of-done fact each asked
  `verification_block` — the seam `build_report`'s own comment says it exists to
  collapse. Hoisting that read onto `Evidence` removes the duplicate. What is
  still spent is the branch's record set and the trunk question, both local, on
  every caller of `build_report` rather than on `status` alone.

## Direct baseline

Put the four facts in `--json` only, and let the console keep exactly the output
it has: one glyph per step, and the existing annotation where a step already
carries one. Where a fact is unmet and the current step is `implement`, its
reason string gains a clause, the way `implement` already joins a tally to a
verification block.

No new console structure, no new glyph table, one payload field, and every
existing console assertion in the suite keeps passing untouched.

## Decision

The console renders the four facts as their own block between the step table and
the `next:` line — one line per fact, each with its own glyph, the fact's name,
and one detail phrase. `--json` carries the same four as a `facts` list beside
`steps`. Neither view composes a fact; both render what inference already
decided.

The block is per feature and sits beside the step table rather than inside it,
because three of the four facts are about the branch and only the first is about
a step.

## Diagram

```
              baseline                             decision

stable   ┌──────────────────────┐            ┌──────────────────────┐
         │   PipelineReport     │            │   PipelineReport     │
         │   steps[]            │            │   steps[]            │
         │   facts[]            │            │   facts[]            │
         └──────────────────────┘            └──────────────────────┘
              ▲             ▲                     ▲             ▲
════ pipeline-state-is-one-payload ════════════════════════════════════
        reads │             │ reads         reads │             │ reads
volatile ┌─────────┐   ┌────────┐            ┌─────────┐   ┌────────┐
         │ console │   │ --json │            │ console │   │ --json │
         └─────────┘   └────────┘            └─────────┘   └────────┘
              │              │                    │              │
              │ renders      │ renders            │ renders      │ renders
              ▼              ▼                    ▼              ▼
         step table      steps[]              step table     steps[]
         one clause      facts[]              facts block    facts[]
         on one step
```

Both graphs carry `facts[]` in the payload — that is settled one level up and is
not what this record decides. They differ in the bottom-left box. In the baseline
the console renders one clause, attached to whichever step happens to be current,
and three of the four facts have no rendering at all; in the decision the console
renders all four, always, in the same place. The argument is that difference:
`--json` is identical on both sides, so everything this choice buys is bought for
the reader who never opens it.

## Considered

- `--json` only, per **Direct baseline** — the cheapest shape, and it satisfies
  both scope items as written. It loses on the pressure in *Context*: the fact a
  human never sees is the fact the issue was filed about, and the definition of
  done for #299 asks for the difference in `wfctl status` and not only in
  `--json`.
- Four columns across the eight step rows — the shape that reads as "four facts,
  four columns" and the one the handoff warned nobody reads. Beyond width, it is
  wrong about what the facts are: three of them are branch facts, so seven rows
  would repeat one value and the table would assert a per-step variation that
  does not exist.
- One summary line — "3 of 4 settled" — scannable, and it is scope item 3's
  collapse with a counter in front of it. A reader still cannot say which one.
- Render the block only when a fact is unmet — quieter on a settled branch, and
  it makes the block's absence carry meaning. A reader who has never seen the
  block cannot tell "all four met" from "this wfctl is too old to know", which
  is the distinction `notify` is present-and-false for (FR-004).
- Reuse `_STATE_GLYPH` for the fact values — the four state names and the three
  fact values are different sets, and sharing the table would let a fact render
  as `▶`. A sibling table keeps `cli` the only place either is drawn without
  claiming the two vocabularies are one.

## Consequences

`cli` gains a second glyph table, and the rule that a glyph exists for exactly
one console line now has two instances to hold to rather than one.

Console output grows by four lines plus a rule. Every test asserting on `wfctl
status` output keeps passing — the additions are new lines, not changed ones —
but a test asserting the *absence* of a phrase across the whole output could now
match inside the block. `NO_COLOR` stays pinned as the suite already requires.

The failure mode this introduces: a fact whose detail phrase is composed at the
console rather than in inference. That is the boundary `pipeline-state-is-one-payload`
draws, and the block's four detail strings are exactly the shape that invites
crossing it — the same way the design remedy was composed in `cli` until it was
moved back into the payload.

## Verification

The situation #299 was filed over, built twice and read twice: a branch whose
tests pass with an architecture record still `proposed`, and the same branch
after `wfctl arch accept`. The `wfctl status` console output must differ between
the two. A test that asserts only on `--json` does not demonstrate this decision
— it demonstrates the baseline.

## Log

- 2026-09-10  proposed  — #299. Where the four facts meet a reader, given that
  only one of the two views has one.
