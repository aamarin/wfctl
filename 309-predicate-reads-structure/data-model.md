# Phase 1 data model — #309

No persisted data. The feature adds two module-level constants and one field
value to an existing dataclass.

## Required section lists

Two tuples of heading stems, module-level in `_pipeline.py`, beside the
predicates that read them.

| | Source | Members |
|---|---|---|
| `_REQUIRED_SPEC_SECTIONS` | the four headings `spec-template.md` marks `_(mandatory)_` | User Scenarios & Testing · Requirements · Success Criteria · Validation Strategy |
| `_REQUIRED_PLAN_SECTIONS` | wfctl's own choice from `plan-template.md`'s headings; that template marks nothing mandatory | Summary · Technical Context · Constitution Check · Project Structure · Complexity Tracking |

A member is a heading **stem**, not a whole line. `Requirements` matches
`## Requirements` and `## Requirements _(mandatory)_`, and matches neither
`## Functional Requirements` nor `## RequirementsTODO`.

Ordered rather than a set: the annotation lists what is missing, and template
order is the order a reader will look for them in.

## `_PipelineStep.annotation`

Existing field, existing renderer. Three steps already produce one; this adds
two more producers and widens a third.

| Step | When | Value |
|---|---|---|
| `specify` | `spec.md` exists, sections missing | `missing: <names, template order>` |
| `plan` | `plan.md` exists, sections missing | `missing: <names, template order>` |
| `clarify` | `skipped` — no heading, no markers, a plan exists | `scan never ran` |

## `_PipelineStep.reason`

**Unchanged in shape, gains two producers and not three.** The field's stated
contract is that every arm setting `in_progress` *from evidence* records why.
`specify` and `plan` do, so they set it. `clarify`'s skip is not `in_progress`,
and a `skipped` step is never `_current_step_name`, so a reason set there would
reach no consumer — see `research.md`.

## States

```
spec.md / plan.md            state         annotation
─────────────────────────    ───────────   ──────────────────────────
absent                       pending       —
exists, no sections          in_progress   missing: <all of them>
exists, some sections        in_progress   missing: <the absent ones>
exists, all sections         done          —
  (spec.md only) + marker    in_progress   —          unchanged today
```

The last row is untouched: a marked spec is clarify's business, and the marker
check runs as it does today.
