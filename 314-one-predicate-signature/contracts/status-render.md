# Contract: what `wfctl status` renders is unchanged

wfctl exposes a CLI, and the only surface this feature can break is what
inference hands the views. Nothing about the command surface changes — no flag,
no output format, no exit code. What must hold is that the *values* are the same,
at every step, in every state a predicate can reach.

This is the check the test suite cannot perform. The suite asserts on step states
and on console substrings; a restructure that preserved every assertion while
breaking the shape would pass it completely. So the contract is a captured
artifact, not a recollection.

## The contract

For each of the eight steps, in each state that step's predicate can reach, the
payload's `state`, `annotation`, `reason` and `remedy` are byte-identical before
and after the change.

`state` is the field, never the glyph. `wfctl status` spends one symbol on "ran"
and another on "passed by", and once printed they cannot be told apart — so the
comparison reads `wfctl status --json`, and the rendered console output is
compared as a second, weaker check.

## How to capture it

`_infer_steps` takes a directory and resolves nothing, so the states are reached
by building feature directories rather than by moving a real branch through the
pipeline. `tests/conftest.py:260` (`spec_tree`) already builds exactly the named
artifacts and nothing else, which is the property this needs — a fixture that
stages upstream files the case never named would compare a different combination
than the one on disk.

Capture before the first edit:

```bash
uv run python - > /tmp/314-baseline.json   # then again as -after.json
```

...walking the state matrix below through `_infer_steps` and dumping
`(name, state, annotation, reason, remedy)` for each. Diff the two files. Any
difference is a defect unless it is the one documented exception below, and there
are no documented exceptions.

## The state matrix

Each row is one feature directory. The right column is the step under test; the
others must also match, which is why the whole payload is dumped rather than one
step.

| Artifacts present | Exercises |
|---|---|
| *(empty)* | every step `pending`; the cascade |
| `design.md` | brainstorm `in_progress` with the design block, and its remedy |
| `design.md` + a record under the arch root | brainstorm `done` |
| `spec.md` only | brainstorm `skipped`, specify `done` |
| `spec.md` with a `[NEEDS CLARIFICATION:` marker | specify `in_progress`, clarify `in_progress`, and `_current_step_name`'s skip branch |
| `spec.md` with `## Clarifications` and no marker | clarify `done` |
| `spec.md` + `plan.md`, no Clarifications section | clarify `skipped`, plan `done` |
| `tasks.md` with open boxes | tasks `done`, implement `in_progress` |
| `tasks.md` all ticked, no `wfctl.json` | implement `done` |
| `tasks.md` all ticked + a definition of done, unverified | implement `in_progress`, `unverified — run \`wfctl verify\`` |
| `checklists/analysis-report.md` | analyze `done` |
| `delivery.md`, every row keyed | decompose `done` |
| `delivery.md`, `n` rows unkeyed, tasks open | decompose `in_progress`, `n issue rows without a key` |
| `delivery.md`, `n` rows unkeyed, tasks closed | decompose `done`, reason still set — the case `blocks` must not change |
| `delivery.md` with no Issue Grouping Map | decompose `done` — the inconclusive case |
| `delivery.md`, no tracker configured | decompose `done` — the other inconclusive case |
| `tasks.md` all closed, no `delivery.md` | decompose `skipped` |

The last four rows are the ones this change puts at risk: they are `decompose`'s
routing through `blocks`, and `research.md` Q2 predicts all four are unchanged.
A difference in any of them is the finding the handoff says to stop and report,
not a licence to adjust the verdict.

## What is deliberately not in the contract

- Glyphs. They are a rendering `cli` applies to `state`, restylable by design.
- The order of steps. Derived from `_STEPS` insertion order, which this change
  does not reorder — but it is the table's contract, not inference's.
- Timing. `Evidence` is assembled from reads the loop already performs, so this
  is a no-change by construction rather than a measured target.
