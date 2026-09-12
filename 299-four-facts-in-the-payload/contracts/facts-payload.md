# Contract — the four facts, in both views

One inference, two renderings. Neither view composes a detail string.

## Console — `wfctl status`

The block sits between the step table and the `next:` line, in every state.

```
brainstorm   ●
specify      ●
clarify      ●
plan         ●
tasks        ●
analyze      ●
decompose    ●
implement    ●  12/12 done
────────────────────────────────────
artifacts written       ●  spec.md, plan.md, tasks.md
definition of done      ●  passed at 47e3e9c
architecture accepted   ○  readiness-is-not-a-step-state (proposed)
outward actions authorized  ○  nobody has allowed it for this work
next: Story complete — open PR or run `/end-session`.
```

Name column is left-justified to 22 characters — the width of the longest of the
four, `outward actions authorized`. Glyph, two spaces, detail.

### Glyphs

`cli._FACT_GLYPH`, a sibling of `_STATE_GLYPH` and not a widening of it.

| Value | Glyph | Style |
| --- | --- | --- |
| `met` | `●` | green |
| `unmet` | `○` | yellow |
| `n/a` | `–` | dim |

`unmet` is yellow rather than dim: it names something the reader must act on, and
`pending`'s dim would file it beside "not yet". `n/a` shares `skipped`'s glyph and
style because it is the same kind of statement — this one was passed by.

Every detail string is `escape()`d on the way out, for the reason the design
remedy is: a record slug and a repo-declared path are repo-supplied, and `[wip]`
is legal in both.

## `--json` — `wfctl status --json`

`facts` sits beside `steps`, always present, always four entries, always in the
same order.

```json
{
  "issue": "299",
  "branch": "299-four-facts-in-the-payload",
  "steps": [ … ],
  "facts": [
    {"name": "artifacts written",      "value": "met",   "detail": "spec.md, plan.md, tasks.md"},
    {"name": "definition of done",     "value": "met",   "detail": "passed at 47e3e9c"},
    {"name": "architecture accepted",  "value": "unmet", "detail": "readiness-is-not-a-step-state (proposed)"},
    {"name": "outward actions authorized", "value": "unmet", "detail": "nobody has allowed it for this work"}
  ]
}
```

`value` is one of `met`, `unmet`, `n/a`. `detail` is a non-empty string in every
entry, in every state.

Present and complete on every branch, including one with no feature directory and
including the trunk. A consumer reading a missing `facts` key learns that this
wfctl predates the feature; a consumer reading a short list learns nothing, which
is why the list is never filtered.

## Invariants a test can assert

1. `len(facts) == 4` and `[f.name for f in facts]` is the fixed order, on every
   input including no spec dir and the trunk.
2. `f.detail` is truthy for all four, in every state.
3. Two branches whose `steps` payloads are byte-identical and whose touched
   record statuses differ produce different `facts` — and different console
   output. This is the issue, stated as an assertion.
4. `tests/pipeline_payload_snapshot.json` needs no regeneration.
5. No `Fact` is constructed from a `_PipelineStep`. Structural: the derivations
   take `Evidence`, `Path` and the grant, and none takes a step.
