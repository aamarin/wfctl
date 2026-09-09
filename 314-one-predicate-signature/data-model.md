# Data model: one predicate signature

Phase 1. Nothing here is persisted — these are the values inference holds for
the length of one call. Every one of them exists today; what changes is that
four of them gain a name and two gain a closed type.

## Evidence

Everything the eight predicates read, assembled once per `_infer_steps` call,
before any predicate runs. Frozen: a predicate that mutated it would make the
step order significant, and the order is a rendering concern.

| Field | Type | Today |
|---|---|---|
| `spec_dir` | `Path` | the parameter |
| `repo_root` | `Path` | the parameter |
| `spec_text` | `str` | `_pipeline.py:453-458` — `spec.md` with fenced blocks and inline spans blanked; `""` when absent |
| `has_markers` | `bool` | `:461` — `"[NEEDS CLARIFICATION" in spec_text` |
| `tasks_text` | `str` | `:443` — `tasks.md`, or `""` when absent |
| `tasks_open` | `bool` | `:445` — `_tasks_open(tasks_text, spec_dir)` |

**Validation**: none. Each field is either a path the caller supplied or the
result of a read that already tolerates absence by returning `""` / `False`.
A missing file is a legitimate state at every step — it is how `pending` is
reached — so there is nothing to reject.

**The `spec_dir is None` case never reaches a predicate.** `_infer_steps`
returns eight `pending` steps before building `Evidence`, exactly as today
(`:439`). So `Evidence.spec_dir` is `Path`, not `Path | None`, and no predicate
carries a guard for it.

## State

```
"done" | "in_progress" | "pending" | "skipped"
```

The four names `pipeline-state-is-one-payload` writes out. A `Literal` replacing
`str` on `_PipelineStep.state` and on every predicate's return.

**Transitions**: none within a run. Each step's state is computed once from
`Evidence` and never revised. The `cascade` flag is the one cross-step rule —
the first `pending` step makes every later step `pending` — and it belongs to the
walk, not to any predicate, because it is a fact about position rather than
about evidence.

## Predicate

```
(Evidence) -> tuple[State, str | None]
```

The state, and the reason it is not complete. `None` when nothing blocks.

**Why the reason and not a bool**: `verification_block` and `_implement_verdict`
already return it, for the reason both docstrings give — the caller renders the
string, and a caller that only needs to know *whether* the step is blocked reads
it as truthy. Returning a bool would put the reason back at a second site and
reintroduce #265.

## Step

One row of `_STEPS`, as a `NamedTuple` rather than a positional tuple.

| Field | Type | Today |
|---|---|---|
| `command` | `str` | element 0 |
| `continuation` | `Continuation` | element 1 |
| `predicate` | `Predicate` | inline in `_infer_steps` |

**Validation**: by the type checker, at author time. A row missing `predicate`
is a `[dict-item]` error; a predicate returning an unlisted state name is a
return-type error. Neither is checked at runtime, deliberately — the table is a
literal in the source and cannot change after the wheel is built.

**`NamedTuple`, not a frozen dataclass**: the three existing positional unpacks
(`_pipeline.py:780`, `:781`, `tests/test_pipeline_commands.py:72`) keep working
untouched, so naming the fields costs no call-site sweep.

## Verdict and Source

Unchanged. `Verdict` is `satisfied | unsatisfied | inconclusive`; `Source` is
`repo-declared | accepted-record | human | ambient`; `blocks(verdict, source)`
owns whether an inconclusive reading stops a step. They move to
`_predicates.py` with the readers that consult them and are not otherwise
touched.

`decompose` becomes the eighth caller of `blocks`, with `source="ambient"` —
`research.md` Q2 carries the mapping and why the verdict is unchanged.
