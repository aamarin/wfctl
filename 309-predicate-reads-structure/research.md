# Phase 0 research — #309

No `[NEEDS CLARIFICATION]` markers reached this phase. What follows resolves the
two claims `design.md` carried as **assumed**, plus one finding that changed the
design.

## Claim 5 — nothing outside `_infer_steps` reads `plan` as done in a way this flips

**Resolved: nothing does.** `infer_pipeline` collapses every step with
`state in ("done", "skipped")` to `True` generically; no caller special-cases
`plan`. A grep for a `plan` literal across `wfctl/*.py` outside `_pipeline.py`
returns nothing. Tightening the arm changes one step's state and no consumer's
shape.

## Claim 6 — `reason` gaining a producer breaks no consumer

**Resolved, and it moved the design.** `reason` has three consumers:

| Consumer | Reads | Effect of a new producer |
|---|---|---|
| `_design_remedy` (`_pipeline.py:712`) | `step.reason != DESIGN_BLOCK_REASON` → `None` | none; anything else already returns `None` |
| `cli.py:508` | the reason of the **current** step, to write `next-step.md` | none for a `skipped` step |
| `cli.py:570` | the same, for the report | none for a `skipped` step |

The second row is the finding. `_current_step_name` skips any step whose state
is not `in_progress` or `pending`, so a `skipped` step is never current and its
reason reaches no consumer at all.

`reason` is documented in the file as *"Every arm that can set
`state = "in_progress"` from evidence puts its reason here."* Clarify's skip is
not `in_progress`.

**So clarify's note goes in `annotation` only, and `reason` is left alone.** The
annotation is rendered per step in the status table independently of `blocked`,
which is the surface the answer was chosen for. This makes the folded-in half
smaller than estimated — no change to the `reason` dict, and no change to what
that field means.

`specify` and `plan` do set `in_progress` from evidence, so they set both, which
is the contract the field already states.

## Corpus measurements the plan rests on

Taken against `~/Development/wfctl-specs/`, the durable spec root:

```
spec.md      25 files    22 carry all four mandatory headings
plan.md      24 files    23 carry all five plan headings
the 3 exceptions are the oldest directories on disk, ported in by
"specs: port the last in-repo spec dirs before declaring a spec root"
```

The `_(mandatory)_` suffix reaches real specs verbatim — `## Requirements
_(mandatory)_` appears in 23 of 25 — which is what forces a stem-anchored match
rather than a whole-line one.

## Upstream volatility

`wfctl/specify/templates/spec-template.md` has one commit in its history: the
change that vendored it. No upstream rename has ever landed here. The drift
check is therefore a guard against a thing that has not yet happened, and is
cheap enough to be worth having anyway — it is the condition under which the
level-2 record's coupling was accepted.
