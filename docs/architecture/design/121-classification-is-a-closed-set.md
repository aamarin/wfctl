---
status: proposed
classification: simple-design
---

# A Level-3 record classifies its outcome, never its routing

## Context

#121 adds a durable Level-3 design record under `<arch-root>/design/`. The
proposal it came from gave the record a six-value `classification` field:
`simple-design`, `catalog-match`, `project-deviation`, `novel-design`,
`architecture-impact`, `insufficient-evidence`.

Three of those are not descriptions of a decision. They are descriptions of what
the workflow should do next — escalate to a human, return to Level 2, go find
more evidence. A field that holds both kinds of value makes the record the
authority on where control flows, which is a harness concern #121 explicitly
leaves to #101.

Constrained by `layer-model` (what each layer may own). `session-state-is-re-derived`
argues the same point — position is inferred, never stored — but is still
`proposed` and so is cited as reasoning, not as an in-force constraint.

## Verified

- `_arch.py:145` — `sorted(root.glob("*.md"))`, non-recursive. A record under
  `design/` is invisible to `wfctl arch context` and cannot become binding.
- `cli.py:716` — `root / "declarations" / f"{branch}.md"`. A nested, tracked,
  non-binding subdir under `arch-root` already exists.
- `architecture-decisions/record-template.md` frontmatter is `status:` alone.
  There is no precedent in this repo for a typed field in a record header.
- `_paths.py:294` — `arch_root` resolves through `WFCTL_ARCH_DIR`, then this
  repo's manifest, then the main checkout's. It can point outside the tree.

## Assumed

- That three values cover the decisions this repo actually makes. Tested by use:
  if a fourth is reached for twice in the pilot, the set was wrong.
- That `named-pattern` is worth distinguishing from `simple-design` before any
  pattern card exists. Tested by whether the field is ever read.

## Direct baseline

Reuse `architecture-decisions/record-template.md` unchanged — `status:` in the
frontmatter, no classification at all, the outcome stated in the `Decision`
section like any other. One template, one format, nothing new to learn.

## Decision

The record carries `classification` with exactly three values, all of which
describe what was decided:

```
simple-design   direct composition or local structure won
named-pattern   a named pattern materially shaped the result
novel-design    a new reusable abstraction was approved
```

Routing outcomes are not values of this field and are not persisted anywhere.
`insufficient-evidence` means the pass has not finished — stay at Level 3 and
write nothing. `architecture-impact` means the question was Level 2 all along —
return there and write a Level-2 record. `project-deviation` means a human
approves before `status` moves to `approved`, which the `Log` already carries.

`status` is `proposed | approved | superseded | rejected` — `approved`, not
`accepted`, because an approved Level-3 record governs one feature and is not
part of the binding set `wfctl arch context` projects.

## Diagram

          baseline — 6 values       decision — 3 values

stable    ┌──────────────────┐      ┌──────────────────┐
          │ record           │      │ record           │
          │   3 outcomes     │      │   3 outcomes     │
          │   3 routings     │      └──────────────────┘
          └──────────────────┘             ▲
              ▲          ▲                 │ writes
              │←writes   │←reads
══════════════╪══════════╪═ arch-root ═════╪════════
              │          │                 │
volatile  ┌───┴────┐ ┌───┴────┐        ┌───┴─────┐   ┌────────┐
          │Level-3 │ │ next   │        │ Level-3 │──►│ next   │
          │ pass   │ │ pass   │        │ pass    │   │ pass   │
          └────────┘ └────────┘        └─────────┘   └────────┘

Stable above, volatile below: a record is approved once and then read, while a
pass is rewritten whenever the pipeline changes. The line is `arch-root` —
above it what the repo persists and tracks, below it state that lives only as
long as the pass. This record does not draw that line; it already exists, and
`session-state-is-re-derived` argues who should own what crosses it while still
being `proposed`, so it is reasoning here rather than an in-force constraint.

The baseline crosses that line twice. The second crossing is the objection: a
value read back out of `arch-root` to decide what runs next makes a durable
record the authority on control flow, which is the store #101 has not been
started to build. In the decision only the write crosses, and the routing
outcome is handed to the next pass without ever leaving memory.

## Considered

- **The baseline — no classification field.** Rejected because item 6 of #121
  has `speckit-analyze` check that no task contradicts an approved record, and
  the check it can actually run differs by outcome: a `novel-design` needs human
  approval evidence, a `simple-design` needs none. Prose in `Decision` is not
  something a check can read.
- **The proposal's six values.** Rejected on the grounds above: it makes the
  record the store for pipeline routing, which `session-state-is-re-derived`
  refuses and #101 has not been started to build.
- **`catalog-match` instead of `named-pattern`.** Rejected because it asserts a
  catalog exists. #121 ships none, and the name would be false on the day it
  landed.

## Consequences

**A decision that escalated leaves no Level-3 trace.** A pattern considered and
routed to Level 2 produces a Level-2 record and nothing here, so "we looked at
this at Level 3 first" survives only if the Level-2 record's `Context` says so.
Accepted: the alternative is a record whose subject is a decision that was not
made at this level.

**`named-pattern` names a pattern no card defines.** Until cards exist, the
value is a bare noun, and two records may use one name for different intents —
the exact failure the source review flags for Observer versus Publish/Subscribe.
Mitigated only by `Considered` and `Consequences` carrying the actual argument.

## Verification

- Every record under `design/` parses with a `classification` in the closed set,
  once item 2 gives the skill something to check with.
- `wfctl arch context` output is unchanged by the presence of `design/`. This is
  the check that the non-recursive glob is load-bearing rather than incidental,
  and it belongs in the test suite before item 3.
- The set is right if the pilot never reaches for a fourth value. Two reaches
  reopen this record.

## Log

- 2026-09-02  proposed  — first record written under the format it describes,
  as the dogfood case for #121 item 1.
