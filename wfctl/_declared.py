"""Read and validate a repository's own declared pipeline passes.

`wfctl.json`'s `steps` key, parsed here and nowhere else — inference and
`wfctl check config` must not disagree about what a file declares, and a
second parser of the same file is how they would (research.md R8). `_pipeline`
consumes what `load` returns to build the payload; `check config` renders what
it returns as problems. Neither reads `wfctl.json` itself.

Imports `_pipeline` at module scope — the built-in passes under a step are
part of the ordering question `before`/`after` answers, so this module needs
their names. The arrow points one way: `_pipeline` reaches back into this
module only from inside a function (`_infer_steps`), never at import time, so
the two modules do not cycle.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from wfctl._evidence import build_file_exists_reader
from wfctl._pipeline import _STEP_NAMES, _STEPS, Continuation, SubStep

CONFIG_PATH = "wfctl.json"

_ON_FINISH_VALUES: tuple[Continuation, ...] = ("automatic", "review_required")

# A declared pass defaults to requiring review: wfctl cannot vouch for a
# command it does not ship (contracts/wfctl-json.md). A tool-shipped pass
# never goes through this default — its `on_finish` is set directly on its
# `SubStep` in `_STEPS`.
_DECLARED_DEFAULT: Continuation = "review_required"


def load(
    repo_root: Path, *, is_installed: Callable[[str], bool] | None = None
) -> tuple[dict[str, list[SubStep]], list[str]]:
    """Return (passes by step, problems).

    The dict carries every step that has a pass at all — wfctl's own, a
    repository's, or both — fully ordered, `before`/`after` overrides applied.
    A step with neither is absent, not an empty list, so a caller counting
    passes does not have to filter zero-length entries out of eight.

    `is_installed` is asked once per declared command and never for wfctl's
    own — there is nothing to ask about a command this tool ships. `None`
    skips that one rule, which is what `_pipeline` wants: it reads the passes
    back into the payload and does not care whether a command is installed,
    only `wfctl check config` does, and only it has a repository's installed
    layers to check against.

    A step whose declaration cannot be fully ordered is not loaded — the step
    still carries wfctl's own passes, if it has any, and the finding says why
    the repository's did not join them. A single malformed pass is narrower:
    only that pass is dropped (FR-004), its siblings still load.
    """
    path = repo_root / CONFIG_PATH
    if not path.exists():
        return _builtin_only(), []
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return _builtin_only(), [f"{CONFIG_PATH}: not valid JSON ({e})"]

    if not isinstance(data, dict):
        return _builtin_only(), [f"{CONFIG_PATH}: top level must be an object"]

    declared = data.get("steps")
    if declared is None:
        return _builtin_only(), []
    if not isinstance(declared, dict):
        return _builtin_only(), [f"{CONFIG_PATH}: 'steps' must be an object"]

    passes = _builtin_only()
    problems: list[str] = []

    for key, entries in declared.items():
        if key not in _STEP_NAMES:
            problems.append(
                f"'{key}' is not a pipeline step — one of: {', '.join(_STEP_NAMES)}"
            )
            continue
        if not isinstance(entries, list):
            problems.append(f"{CONFIG_PATH}: '{key}' must be a list of passes")
            continue

        ordered, step_problems = _load_step(key, entries, is_installed)
        problems.extend(step_problems)
        if ordered is not None:
            passes[key] = ordered
        elif key not in passes:
            # Nothing loaded for this step at all — neither built-in (it has
            # none) nor declared (the order could not be satisfied). An empty
            # key would read the same as "declared nothing"; absence is correct.
            pass

    return passes, problems


def _builtin_only() -> dict[str, list[SubStep]]:
    """The payload every repository starts from: wfctl's own passes, nothing
    declared. Its own function so every early return above shares one copy
    rather than each re-deriving it — and a fifth built-in pass added later
    changes one place.
    """
    return {name: list(step.sub_steps) for name, step in _STEPS.items() if step.sub_steps}


def _load_step(
    step: str, entries: list, is_installed: Callable[[str], bool] | None
) -> tuple[list[SubStep] | None, list[str]]:
    """Parse and order one step's declared list.

    Returns `(None, problems)` when the step's declared passes cannot be
    loaded at all — a name collision within the step, or an order the
    `before`/`after` graph cannot satisfy. Per-entry problems (a bad pass
    among otherwise-good ones) drop only that entry and keep going, per FR-004.
    """
    problems: list[str] = []
    parsed: list[tuple[SubStep, str | None, str | None]] = []
    seen: set[str] = {s.name for s in _STEPS[step].sub_steps}

    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            problems.append(f"{step}: each pass must be an object")
            continue

        name = entry.get("name")
        if not name or not isinstance(name, str):
            problems.append(f"{step}[{i}] has no 'name'")
            continue
        qualified = f"{step}.{name}"
        if name != Path(name).name or name == "..":
            # `step_none_cmd` builds a claim file from this name unvalidated
            # (`STEP_CLAIMS_DIR / branch / f"{step}.{name}.md"`) — a name
            # containing '/' or '..' walks that write outside the directory
            # it is meant to land in, and a name split across path segments
            # is never read back by `_step_claims`'s single-level glob either
            # way. Caught here so `check config` reports it before
            # `step none` ever runs.
            problems.append(f"{qualified} is not a valid pass name — '/' and '..' are rejected")
            continue
        if name in seen:
            problems.append(f"{qualified} is declared twice under one step")
            continue

        if "steps" in entry or "sub_steps" in entry or "passes" in entry:
            problems.append(
                f"{qualified} declares passes of its own; passes nest one level below a step"
            )
            continue

        has_command = "command" in entry and entry.get("command") is not None
        manual = entry.get("manual") is True
        if has_command and manual:
            problems.append(f"{qualified} declares a command and 'manual' — one or the other")
            continue
        if not has_command and not manual:
            problems.append(
                f"{qualified} declares no command and is not marked manual — say which"
            )
            continue

        command = entry.get("command") if has_command else None
        if command is not None and not isinstance(command, str):
            # Unchecked, this reaches `is_installed`'s `str.lstrip` call below
            # (or, with no checker supplied, `_pipeline`'s runtime read) and
            # raises `TypeError` instead of landing as a `check config`
            # finding like every other malformed field here.
            problems.append(f"{qualified} has a 'command' that is not a string")
            continue
        if command is not None and is_installed is not None and not is_installed(command):
            problems.append(
                f"{qualified} names {command}, which is not installed in this repository"
            )
            continue

        evidence = entry.get("evidence")
        if not evidence or not isinstance(evidence, str):
            problems.append(f"{qualified} has no 'evidence'")
            continue

        on_finish = entry.get("on_finish", _DECLARED_DEFAULT)
        if on_finish not in _ON_FINISH_VALUES:
            problems.append(
                f"{qualified} has on_finish '{on_finish}' — one of: "
                f"{', '.join(_ON_FINISH_VALUES)}"
            )
            continue

        before = entry.get("before")
        if before is not None and not isinstance(before, str):
            problems.append(f"{qualified} has a 'before' that is not a string")
            continue
        after = entry.get("after")
        if after is not None and not isinstance(after, str):
            problems.append(f"{qualified} has an 'after' that is not a string")
            continue

        seen.add(name)
        sub = SubStep(name=name, command=command, on_finish=on_finish,
                      reads=build_file_exists_reader(evidence))
        parsed.append((sub, before, after))

    ordered, order_problems = _ordered(step, parsed)
    problems.extend(order_problems)
    return ordered, problems


def _ordered(
    step: str, declared: list[tuple[SubStep, str | None, str | None]]
) -> tuple[list[SubStep] | None, list[str]]:
    """Combine `step`'s built-in passes with `declared`, `before`/`after` applied.

    Written order is the base: wfctl's own first, then the declared passes in
    the order `wfctl.json` lists them (FR-003). `before`/`after` may reference
    any sibling under the step, built-in or declared (research.md R9) — moving
    a declared pass ahead of one of wfctl's own is what T018 exercises. An
    unresolvable sibling or an unsatisfiable order is reported and the whole
    step's *declared* passes are not loaded; wfctl's own are unaffected,
    because they carry no order that can conflict with themselves.
    """
    builtin = list(_STEPS[step].sub_steps)
    by_name: dict[str, SubStep] = {s.name: s for s in builtin}
    by_name.update({sub.name: sub for sub, _, _ in declared})
    order = [s.name for s in builtin] + [sub.name for sub, _, _ in declared]

    if not declared:
        return (builtin or None), []

    problems: list[str] = []
    successors: dict[str, set[str]] = {n: set() for n in order}

    def _known(owner: str, sibling: str) -> bool:
        """Whether `sibling` is a real, distinct pass under `step` — records
        the finding for `owner` (always `sub.name`) when it is not.

        A pass naming itself is caught here rather than left to `_toposort`:
        the self-loop edge it would add is never violated (an item's own
        index never exceeds itself), so it settles silently on the first pass
        instead of surfacing as the unsatisfiable order it actually is.
        """
        if sibling == owner:
            problems.append(f"{step}.{owner} names itself as a sibling")
            return False
        if sibling in by_name:
            return True
        problems.append(
            f"{step}.{owner} names sibling '{sibling}', which is not declared under {step}"
        )
        return False

    for sub, before, after in declared:
        if before is not None and _known(sub.name, before):
            successors[sub.name].add(before)
        if after is not None and _known(sub.name, after):
            successors[after].add(sub.name)

    if problems:
        return (builtin or None), problems

    resolved = _toposort(order, successors)
    if resolved is None:
        return (builtin or None), [
            f"{step}: the stated order cannot be satisfied — {', '.join(order)}"
        ]
    return [by_name[n] for n in resolved], []


def _toposort(order: list[str], successors: dict[str, set[str]]) -> list[str] | None:
    """`order`, with each `first` moved immediately ahead of every `second` it
    must precede — the minimal disturbance that satisfies every edge, not
    merely *a* topological order. `None` on a cycle.

    A textbook Kahn's algorithm was tried here first and rejected: breaking
    ties by original position picks the *lexicographically* smallest valid
    order, which is a different thing. Given `architecture, design-doc,
    ui-design` with only `ui-design before architecture` declared, it placed
    `design-doc` — under no constraint at all — ahead of both, because nothing
    tied it to `architecture`'s new position. FR-003's "written order is the
    default" means *unconstrained* passes keep their relative order, which only
    a repair pass over the written sequence, rather than a rebuild from
    scratch, can guarantee.

    Bounded rather than run until a fixed point with no ceiling: a genuine
    cycle oscillates forever, and `len(order)` repair passes is already more
    than an acyclic graph of `before`/`after` edges over this many nodes can
    need — each pass resolves at least one edge that was still violated, or
    the graph was never going to converge.
    """
    result = list(order)
    edges = [(a, b) for a, bs in successors.items() for b in bs]
    for _ in range(len(order) + 1):
        settled = True
        for first, second in edges:
            if result.index(first) > result.index(second):
                result.remove(first)
                result.insert(result.index(second), first)
                settled = False
        if settled:
            return result
    return None
