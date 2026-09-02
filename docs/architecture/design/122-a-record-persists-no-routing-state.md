---
status: proposed
---

# A Level-3 record persists what was decided, never what runs next

## Context

#121 adds a durable Level-3 design record under `<arch-root>/design/`. The
proposal it came from gave the record a six-value `classification` field:
`simple-design`, `catalog-match`, `project-deviation`, `novel-design`,
`architecture-impact`, `insufficient-evidence`.

Three of those are not descriptions of a decision. They describe what the
workflow should do next — escalate to a human, return to Level 2, go find more
evidence. A field holding both kinds of value makes the record the authority on
where control flows, which is a harness concern #121 leaves to #101.

Constrained by `layer-model` (what each layer may own).
`session-state-is-re-derived` argues the same point — position is inferred,
never stored — but is still `proposed`, so it is cited here as reasoning rather
than as an in-force constraint.

## Verified

- `_arch.py:145` — `sorted(root.glob("*.md"), key=lambda p: p.stem)`,
  non-recursive. A record under `design/` is invisible to `wfctl arch context`
  and cannot become binding.
- `cli.py:716` — `path = root / "declarations" / f"{Path(branch).name}.md"`. A
  nested, tracked, non-binding subdir under `arch-root` already exists. The
  `.name` is a traversal guard: the file is committed, so a write escaping the
  arch root would be found after review rather than before.
- `wfctl/agents/skills/architecture-decisions/record-template.md:2` — the
  frontmatter is `status:` alone. No record header in this repo carries a typed
  field today.
- #122 — only a human moves `proposed → approved`, for every record whatever it
  decided. #121 item 6 gives `speckit-analyze` a read-only check that no task
  contradicts an approved record.

## Assumed

- That prose in `Decision` is enough for item 6's check. Falsified if that check
  has to branch on the kind of decision and cannot get what it needs from
  `status` and the record's text.
- That `pattern` is worth keeping as a bare optional name with no catalog behind
  it. Falsified the first time two records use one name for different intents.

## Direct baseline

Take `architecture-decisions/record-template.md`'s frontmatter shape unchanged —
`status:` alone, with what was decided stated in `Decision` like any other prose.
One header shape across both levels, no new vocabulary, and no closed set to
keep in sync across the template, the skill and every record already written.

## Decision

The baseline wins. A Level-3 record's frontmatter carries `status`, plus
`pattern` and `supersedes` where they apply. There is no `classification` field.

Routing outcomes are not persisted anywhere. `insufficient-evidence` means the
pass has not finished — stay at Level 3 and write nothing. `architecture-impact`
means the question was Level 2 all along — return there and write a Level-2
record. `project-deviation` means a human approves before `status` moves, which
`Log` already carries.

`status` runs `proposed | approved | superseded | rejected` — `approved`, not
architecture's `accepted`, because an approved Level-3 record governs one feature
and is not part of the binding set `wfctl arch context` projects.

The graphs under `Diagram` show what this removes.

## Diagram

          decision — the baseline     rejected — six typed values

stable    ┌──────────────────┐        ┌──────────────────┐
          │ record           │        │ record           │
          │   status         │        │   status         │
          └──────────────────┘        │   3 outcomes     │
                 ▲                    │   3 routings     │
                 │ writes             └──────────────────┘
                 │                        ▲          ▲
                 │                        │←writes   │←reads
═════════════════╪═ arch-root ════════════╪══════════╪══════
                 │                        │          │
volatile     ┌───┴─────┐   ┌────────┐ ┌───┴────┐ ┌───┴────┐
             │ Level-3 │──►│ next   │ │Level-3 │ │ next   │
             │ pass    │   │ pass   │ │ pass   │ │ pass   │
             └─────────┘   └────────┘ └────────┘ └────────┘

Both shapes write to `arch-root`; only the rejected one reads back out of it. A
value read out of a durable record to decide what runs next makes that record
the authority on control flow, which is the store #101 has not been started to
build. With no typed field there is nothing to read back, and the routing
outcome reaches the next pass without ever leaving memory.

## Considered

- **The six values as proposed.** Rejected on the grounds in Context: half of
  them are routing, and persisting routing is what makes the record a state
  store.
- **Three values — the outcome-only subset.** The obvious repair, and it fails
  for a different reason. The only check named for it is item 6's, which is
  already answered by `status`; nothing in the codebase reads the field. A typed
  field with no reader is a third copy of a closed set to keep in sync, bought
  with nothing.
- **`catalog-match` as a value name.** Rejected because it asserts a catalog
  exists. #121 ships none, and the name would have been false the day it landed.

## Consequences

- **No machine-readable outcome.** A later check that must branch on the kind of
  decision has to read prose, or add the field back and migrate every record
  written by then. Accepted: no such check exists, and item 6's is satisfied by
  `status`.
- **`pattern` names a pattern nothing defines.** Until cards exist the value is a
  bare noun, and two records may use one name for different intents — the exact
  failure the source review flags for Observer versus Publish/Subscribe.
  Mitigated only by `Considered` and `Consequences` carrying the argument.
- **A decision that escalated leaves no Level-3 trace.** A choice routed to
  Level 2 produces a Level-2 record and nothing here, so "we looked at this at
  Level 3 first" survives only if that record's `Context` says so.

## Verification

- `wfctl arch context` output is unchanged by the presence of `design/`, asserted
  by `test_an_accepted_record_under_design_does_not_join_the_binding_set` in
  `tests/test_arch_records.py`. That test is what makes the non-recursive glob
  load-bearing rather than incidental.
- Every record under `design/` parses with a `status` in the closed set and no
  other typed key, once item 2 gives the skill something to check with.

## Log

- 2026-09-02  proposed  — first record written under the format it describes, as
  the dogfood case for #121 item 1.
