---
status: proposed
---

# The step table holds each step's predicate, and the loop stops branching on the step name

## Context

Eight pipeline steps each decide their own state from evidence on disk. None of
them shares a shape with any other: two are named functions taking different
arguments, six are arms of an `if name ==` chain inside the loop that calls them,
and one of those six resolves an inconclusive reading itself instead of asking
`blocks`.

The pressure is that the evidence readers change and the dispatcher does not.
#308, #309, #240 and #299 each change what one or two predicates prove; none of
them changes how the pipeline walks its steps. Today those are the same code, so
every one of those issues edits a 201-line function whose other 190 lines are
about something else, and a reviewer cannot see which arm moved without reading
all of it.

Constrained by `pipeline-state-is-one-payload`, which puts inference on one side
of a line and every view on the other. This decision rearranges the inference
side and does not move that line.

## Verified

- `_pipeline.py:67` declares `_STEPS: dict[str, tuple[str, Continuation]]` — two
  elements, positional, no field names.
- `_infer_steps` spans `_pipeline.py:420-620`, 201 lines, with 11 `if name ==` /
  `elif name ==` arms at lines 474, 496, 502, 531, 534, 537, 544, 583, 590, 592
  and 594.
- `_pipeline.py:63` declares `Continuation = Literal["automatic",
  "review_required"]`; `:20` declares `Verdict` and `:26` declares `Source`, both
  `Literal`. `_PipelineStep.state` at `:408` is annotated `str`.
- `_implement_verdict` at `_pipeline.py:378` is declared
  `-> tuple[str, str | None]` — the state and the reason it is not `done`.
- The `decompose` arm at `_pipeline.py:544-581` reads
  `_tracker.configured_key_pattern(repo_root)` then `_unkeyed_issues(...)` and
  branches on `tasks_open` without calling `blocks`. Every other reader that
  reaches an inconclusive verdict routes through it.
- `_infer_steps` computes `tasks_text`, `tasks_open`, `spec_text` and
  `has_markers` at `:443-461`, before the loop — the union of what the eight arms
  read is already assembled in one place.
- `pyproject.toml:16-19` declares exactly two runtime dependencies, `typer>=0.12`
  and `rich>=13`. `uv run python -c "import pydantic"` raises
  `ModuleNotFoundError`.
- `_STEPS` is unpacked positionally at `_pipeline.py:780` (`_STEPS[step][0]`),
  `:781` (`command, continuation = _STEPS.get(...)`), and in
  `tests/test_pipeline_commands.py:72` (`for step, (cmd, _) in _STEPS.items()`).
- mypy rejects a `_STEPS` row missing its third element with
  `Dict entry 1 has incompatible type … [dict-item]`; it reports nothing for a
  key missing from a parallel `dict[str, Predicate]`. Run against a scratch file
  with `uv run mypy`.

## Assumed

- That the eight predicates need no evidence beyond the six values the loop
  already computes. Falsified by any arm needing a read that is not
  `spec_dir`, `repo_root`, `spec_text`, `has_markers`, `tasks_text` or
  `tasks_open` — which would mean `Evidence` grows a field rather than that the
  signature is wrong, unless the read is expensive enough to want laziness.
- That routing `decompose` through `blocks` leaves its verdict unchanged. #314
  scopes out changing what any predicate proves, so a route that alters the
  verdict is a finding to report rather than a change to make.

## Direct baseline

Give the eight arms one signature and leave them where they are: extract each
into a module-level function taking the same `Evidence` bundle, and keep the
`if name == "brainstorm": … elif name == "specify": …` chain in `_infer_steps`,
each arm now one line calling its function.

This is a real implementation and it satisfies scope item 1 of #314 completely.
It introduces no new abstraction: no table column, no callable type, no dispatch.
The loop keeps its eleven branches and its 201 lines shrink to roughly 60.

## Decision

`_STEPS` carries each step's predicate as a third field, and `_infer_steps`
calls `_STEPS[name].predicate(ev)` instead of branching on the name.

The table becomes a `NamedTuple` so the fields are named rather than positional,
and the step state becomes a `Literal` rather than `str`:

```python
State = Literal["done", "in_progress", "pending", "skipped"]
Predicate = Callable[[Evidence], tuple[State, str | None]]

class Step(NamedTuple):
    command: str
    continuation: Continuation
    predicate: Predicate
```

`NamedTuple` rather than a frozen dataclass because the three existing positional
unpacks keep working unchanged — a `NamedTuple` is a tuple — so naming the fields
costs no call-site sweep.

`Evidence` is a frozen dataclass holding the six values the loop already computes
before it starts. It is the existing prologue given a name, not new work.

## Diagram

Baseline — the dispatcher and the evidence readers are the same code:

```
stable    ┌──────────────────────────┐
          │  _STEPS                  │
          │  command + continuation  │
          └──────────────────────────┘
                      ▲
                      │ reads
          ┌───────────┴──────────────────────────┐
          │  _infer_steps                        │
          │                                      │
          │   11 × `if name ==` arms             │
          │   evidence reads inline, 8 shapes    │
          │                                      │
          └───────────┬──────────────────────────┘
                      │ calls (7 of 8 arms)
                      ▼
          ┌──────────────────────────┐
          │  blocks(verdict, source) │
          └──────────────────────────┘
                      │
                      │ writes payload
══════════ pipeline-state-is-one-payload ═══════════════════════
                      │
                      ▼
volatile  ┌──────────────────────────┐
          │  cli — status, next,     │
          │  resume, --json          │
          └──────────────────────────┘
```

Decision — the dispatcher reads a table; the evidence readers hang off it:

```
stable    ┌──────────────────────────┐
          │  _STEPS                  │
          │  command + continuation  │
          │  + predicate             │
          └───────────┬──────────────┘
                      │ holds
                      ▼
          ┌──────────────────────────┐          ┌──────────────────────────┐
          │  eight predicates        │──calls──►│  blocks(verdict, source) │
          │  (Evidence) -> (State,   │  (8 of 8)└──────────────────────────┘
          │   str | None)            │
          └───────────▲──────────────┘
                      │ calls
          ┌───────────┴──────────────┐
          │  _infer_steps            │
          │  ~20 lines, no branch    │
          │  on the step name        │
          └───────────┬──────────────┘
                      │ writes payload
══════════ pipeline-state-is-one-payload ═══════════════════════
                      │
                      ▼
volatile  ┌──────────────────────────┐
          │  cli — status, next,     │
          │  resume, --json          │
          └──────────────────────────┘
```

The two differ by which component the evidence readers live inside. In the
baseline they are statements within `_infer_steps`, so the loop is the only thing
that can name them and every change to one edits the loop. In the decision they
are values `_STEPS` holds, so the loop names none of them and `#308`, `#309`,
`#240` and `#299` each edit one function the loop never mentions. The divider is
in the same place in both graphs, and nothing crosses it that did not cross it
before — which is what makes this a level-3 record rather than a level-2 one. The
second graph also closes the `decompose` divergence: `blocks` is reached by eight
of eight rather than seven of eight, because taking the shared signature is what
routes it there.

## Considered

- **The direct baseline — one signature, keep the `elif` chain.** Sound, and it
  is the smallest diff that satisfies scope item 1. It loses on the pressure in
  Context rather than on a flaw: the eleven branches are what make a
  single-predicate change unreviewable, and the baseline keeps all eleven. It is
  also the option to fall back to if `Evidence` turns out not to cover all eight.
- **A parallel `_PREDICATES: dict[str, Predicate]` beside `_STEPS`.** Equally
  expressive and it keeps `_STEPS` untouched. Rejected on when the omission is
  caught: mypy flags a `_STEPS` row missing its third element and reports nothing
  for a key missing from a parallel dict, because a dict with fewer keys is
  well-typed. That is the same failure `_STEPS` was collapsed into one table to
  prevent (`_pipeline.py:58-60` — "omitting the command was silent and severe"),
  and it would arrive as a `KeyError` reachable only on a branch whose inference
  gets that far.
- **A `gate: str` field naming a predicate, resolved through a name-to-function
  map** — the shape #100 named when it deferred this. Rejected: the map is the
  registry the epic ruled out, and the indirection costs `grep`. A `Callable` in
  the same slot needs no map and `grep _decompose_state` still finds both the
  definition and the table row.
- **pydantic models for `_STEPS` and the payload, with validators.** Would
  express value invariants no type can — that a command names a slash command
  that ships, that the state names match the record. Rejected on when the check
  fires and what it costs: `_STEPS` is a literal in the source, so its only input
  is a developer typing a row, and that error belongs in `uv run mypy wfctl/`
  before the commit rather than at import time on every `wfctl status` a user
  runs. It would also be the third runtime dependency in a package that declares
  two. The one value invariant worth having — that a step's command still ships —
  is already checked by `tests/test_pipeline_commands.py`, which walks `_STEPS`;
  `a-rule-is-expressed-as-a-check` is satisfied by that test, not by a validator.
- **Splitting the predicates into `_predicates.py` in the same change.** Deferred
  to `design.md`'s structure section rather than rejected — it is scope item 3
  and it is downstream of this record, which is what makes the split describable
  at all.

## Consequences

Gained: a change to what one predicate proves is a diff to one function, and the
dispatcher stops appearing in it. `blocks` is reached by every predicate rather
than seven of eight. Two invariants move from prose to mypy — a step cannot be
declared without a predicate, and a state cannot be a string outside the four
names `pipeline-state-is-one-payload` lists.

Harder: reading one step's behaviour end to end now means following one hop from
the table to the function, where today the arm is inline. `grep` on the step name
still lands in `_STEPS`, and `grep` on the predicate name lands in both places,
so the hop is navigable — but it is a hop that did not exist.

The failure mode this introduces: `Evidence` is computed eagerly for every step,
so a predicate that wants an expensive read forces every invocation to pay for it
whether or not the step is reached. Today's six values are all cheap file reads
the loop already performs unconditionally, so nothing pays more than it does now;
the first predicate wanting a network read or a large parse is the signal to make
that field lazy rather than to widen `Evidence`.

## Verification

- `uv run mypy wfctl/` fails on a `_STEPS` row written without a predicate, and
  on a predicate returning a state name outside `State`. Both demonstrated
  against a scratch file before the decision was written; the check is that they
  still hold against the real table.
- `wfctl status` renders byte-identical annotation and blocked-reason text at all
  eight steps, before and after. The baseline is captured before the first edit,
  because the suite asserts on step states and cannot see the restructure — a
  refactor that broke the shape while preserving every assertion would pass it.
- `grep -rn '_decompose' wfctl/` finds both the function and its `_STEPS` row.
  Zero hits in either place means the registry was rebuilt as strings.
- `decompose`'s verdict is unchanged after routing through `blocks` — checked by
  the existing tests over unkeyed delivery rows, which assert the reason text and
  the `in_progress` / `done` split on `tasks_open`.

## Log

- 2026-09-09  proposed  — #314 scope item 2: what holds the eight predicates,
  once they share a signature. Written before the implementation, so the code is
  written against the record rather than the record against the code.
