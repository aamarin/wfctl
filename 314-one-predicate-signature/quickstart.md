# Quickstart: one predicate signature

For whoever picks this up. It assumes `/start-session` has run.

## The shape, in one screen

```python
# wfctl/_predicates.py

State = Literal["done", "in_progress", "pending", "skipped"]

@dataclass(frozen=True)
class Evidence:
    spec_dir: Path
    repo_root: Path
    spec_text: str        # spec.md, fences and inline spans blanked
    has_markers: bool
    tasks_text: str
    tasks_open: bool

Predicate = Callable[[Evidence], tuple[State, str | None]]


def specify(ev: Evidence) -> tuple[State, str | None]:
    if not _file_exists(ev.spec_dir / "spec.md"):
        return "pending", None
    return ("in_progress" if ev.has_markers else "done"), None
```

```python
# wfctl/_pipeline.py

class Step(NamedTuple):
    command: str
    continuation: Continuation
    predicate: Predicate

_STEPS: dict[str, Step] = {
    "specify": Step("/speckit.specify", _AUTOMATIC, predicates.specify),
    ...
}
```

and the loop stops branching:

```python
for name, step in _STEPS.items():
    if cascade:
        steps.append(_PipelineStep(name, "pending", None))
        continue
    state, reason = step.predicate(ev)
    ...
```

## Do this first, before any edit

Capture the baseline. `contracts/status-render.md` has the state matrix and says
why the suite cannot stand in for it. A run that skipped this cannot tell a
correct restructure from a broken one, and neither can its reviewer.

## The three places this is easy to get wrong

**`decompose`'s two questions.** `blocks(verdict, "ambient")` answers *is this a
finding*; `ev.tasks_open` answers *does the finding stop the step*. They are
separate today and stay separate. Folding `tasks_open` into `blocks` changes
behaviour — see `research.md` Q2 for the full mapping and the four cases at risk.

**`implement`'s annotation is not its reason.** Every other step's annotation is
its reason; `implement` prefixes `"{done}/{total} done"`. The tally reads
`tasks_text`, which `Evidence` carries, so it can go in the predicate or stay in
the loop. Pick whichever leaves `_infer_steps` shorter; both satisfy FR-002.

**`cascade` belongs to the walk, not to a predicate.** The first `pending` step
makes every later step `pending`. That is a fact about position, and a predicate
that knew about it would need to know the step order.

## Definition of done

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
uv run wfctl doctor
```

All four, and `uv run` is not optional — this repo has two wfctls on PATH and
only `uv run` answers "does the installed tree match the source I am editing".

Then the render diff from `contracts/status-render.md`, and one deliberately
incomplete `_STEPS` row confirmed to fail `mypy` before you delete it again.

## What not to touch

`#308`, `#309`, `#240` and `#299` each change what a predicate proves. None of
them is this branch's. If routing `decompose` through `blocks` cannot be done
without changing its verdict, stop and report it — that is a finding, not a
licence.
