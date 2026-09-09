# One predicate signature for the eight pipeline steps

## Problem Statement

How might we let a change to what one pipeline step proves be a diff to one
function, when today all eight steps decide their state inside the same 201-line
loop and no two of them share a shape?

## Recommended Direction

Give the eight predicates one signature — `(Evidence) -> tuple[State, str | None]`
— and hang them off `_STEPS` as a third field, so `_infer_steps` stops branching
on the step name.

The signature is not designed, it is extracted. Every value the eight arms read
is already computed in the twenty lines before the loop starts: `spec_dir`,
`repo_root`, `spec_text`, `has_markers`, `tasks_text`, `tasks_open`. `Evidence`
is that prologue with a name on it. And `_implement_verdict` already returns
`tuple[str, str | None]` — the state and the reason it is not `done` — so one of
the eight is already written in the shape the other seven need.

The table holds them rather than a parallel dict, because that is the arrangement
mypy can check: a `_STEPS` row missing its third element is a `[dict-item]`
error before the commit, and a key missing from a `dict[str, Predicate]` is a
well-typed dict that raises `KeyError` at runtime on whichever branch first
reaches that step. `_STEPS` was collapsed into one table to prevent exactly that
failure for the command field; this is the same argument, one field along.

Two invariants move from prose into the type system on the way. The step state
becomes `Literal["done", "in_progress", "pending", "skipped"]` rather than `str`
— the four names `pipeline-state-is-one-payload` writes out by hand, enforced
nowhere until now — and `_STEPS` becomes a `NamedTuple`, so `("/speckit.plan",
_AUTOMATIC, _plan)` reads as `command`, `continuation`, `predicate` instead of as
three positional values. `NamedTuple` and not a dataclass because the three
existing positional unpacks keep working untouched.

## Boundaries and Ownership

No boundary is drawn or moved, and that is the level-2 gate's answer rather than
a skipped gate.

`pipeline-state-is-one-payload` is the divider in force: inference computes the
payload, every view transforms it, and no view computes a fact of its own. This
change rearranges the inference side entirely and leaves the divider where it is.
Nothing crosses it that did not cross it before — which is the test for whether a
structural choice was really a level-2 one, and this one fails that test in the
direction that keeps it level 3.

The one ownership question the change touches is already settled and is being
honoured rather than reopened: `blocks(verdict, source)` owns whether an
inconclusive reading stops a step, and `decompose` currently answers that
question itself. Routing it through `blocks` is part of taking the shared
signature. What `decompose` concludes does not change; if it cannot be routed
without changing the verdict, that is a finding to report, not a licence — #240
owns the verdict.

## Software design decisions

- docs/architecture/design/314-the-step-table-holds-the-predicate.md — `_STEPS`
  holds each step's predicate as a third field, and the loop stops branching on
  the step name.

Level 2 answered with no record: no ownership decision was made, and the divider
already in force is unmoved.

## Key Assumptions to Validate

- [ ] The six values in `Evidence` cover all eight predicates. Test: extract the
      eight functions and see whether any needs a read outside the bundle. A
      seventh field is a widened `Evidence`, not a failed signature — unless the
      read is expensive, in which case that field becomes lazy.
- [ ] Routing `decompose` through `blocks` leaves its verdict unchanged. Test:
      the existing tests over unkeyed delivery rows, which pin the reason text
      and the `in_progress` / `done` split on `tasks_open`.
- [ ] `wfctl status` renders byte-identical annotation and blocked-reason text at
      all eight steps. Test: capture the eight renderings before the first edit,
      diff after. The suite cannot see this — it asserts on step states, so a
      refactor that broke the shape while preserving every assertion would pass.
- [ ] `implement`'s annotation stays composable from `(state, reason)`. It is the
      only step whose annotation is not its reason — it prefixes a task tally —
      so it is the one that decides whether `(State, str | None)` is wide enough.

## MVP Scope

In:

- `Evidence`, a frozen dataclass over the six values the loop already computes.
- `State` as a `Literal`, replacing `str` on `_PipelineStep.state` and on every
  predicate's return.
- Eight module-level predicate functions, one per step, sharing the signature.
- `Step` as a `NamedTuple`; `_STEPS` re-typed to `dict[str, Step]` with the
  predicate as its third field.
- `_infer_steps` reduced to the loop, the cascade, and the annotation
  composition — no `if name ==`.
- `decompose` routed through `blocks`, its verdict unchanged.
- Scope item 3: `_predicates.py` split out, holding `Evidence`, the eight
  functions, `blocks`, `Verdict`, `Source` and `State`. `_pipeline.py` keeps
  `_STEPS`, inference, the report and the command inventory.

Out — and each of these is a named issue rather than a deferral of convenience:

- Changing what any predicate proves (#308, #309).
- Flipping any continuation flag, including `decompose` to automatic (#240).
- Widening the payload to say which of four facts a step answered (#299, blocked
  on #86).

## Not Doing (and Why)

- **A predicate registry keyed by a `gate: str` field** — the shape #100 assumed
  when it deferred this. The string needs a name-to-function map to resolve, and
  that map is the registry the epic ruled out. It also costs `grep`: a callable
  in the same slot is found by name in both the definition and the table row.
- **pydantic models with validators over `_STEPS` and the payload** — raised in
  review and rejected on when the check fires, not on cost. `_STEPS` is a literal
  in the source; its only input is a developer typing a row, so the error belongs
  in `uv run mypy wfctl/` before the commit, not at import time on every `wfctl
  status` a user runs, validating a table that cannot have changed since the
  wheel was built. It would also be the third runtime dependency in a package
  that declares two. The one value invariant worth having — that a step's command
  still ships — is already a test that walks `_STEPS`.
- **Splitting `_pipeline.py` three ways along its docstring** — the docstring
  names "step inference and display, and the commands wfctl names", but splitting
  display from inference is what `pipeline-state-is-one-payload` forbids. Two
  files, not three.
- **Making `Evidence` lazy** — every field is a cheap file read the loop already
  performs unconditionally, so laziness would buy nothing today. The first
  predicate wanting a network read or a large parse is the signal.
- **Fixing what #300 found while restructuring** — the audit deliberately did not
  fix what it found, because a change that moves a rung and restructures at once
  is unreviewable: nobody can tell which half a behaviour change came from. The
  same argument binds here in reverse.

## Open Questions

- Does `implement`'s task tally belong in the predicate's return or stay composed
  in the loop? The tally is a rendering of `tasks_text`, which `Evidence` already
  carries, so either works. Leaving it in the loop keeps the signature at two
  values; moving it makes `implement` the only predicate returning three. Settle
  it at implementation, against whichever keeps `_infer_steps` shorter.
- Does `_predicates.py` take `_STEPS` with it, or does `_pipeline.py` keep the
  table and import the eight functions? The record decides that the table holds
  the predicates; it does not decide which module the table lives in. Circular
  import is the constraint that answers it.
