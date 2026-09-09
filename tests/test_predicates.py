"""The properties #314 bought, asserted so a later change cannot quietly spend them.

The snapshot beside this file pins what the predicates *conclude*. This pins
their *shape* — that all eight still share one signature, that the step table
still holds one for every step, and that the one rule about inconclusive
evidence is still reached by everything that can produce an inconclusive
reading.

None of it would fail today. That is the point: each property held before this
file existed and was held by nothing, which is how `decompose` came to resolve
two inconclusive readings itself without anyone noticing for the length of an
epic.
"""
from __future__ import annotations

import ast
import dataclasses
import inspect
import subprocess
import sys
from pathlib import Path
from typing import get_args

import pytest

from wfctl import _pipeline, _predicates
from wfctl._pipeline import _STEP_NAMES, _STEPS
from wfctl._predicates import Evidence, Reading, State, build_evidence

STATES = set(get_args(State))


def _pipeline_source() -> str:
    """The file `_STEPS` is declared in."""
    return _pipeline.__file__


def _evidence(tmp_path: Path) -> Evidence:
    """An empty feature dir — every predicate's `pending` arm, and none of its reads."""
    feature = tmp_path / "specs" / "314-feature"
    feature.mkdir(parents=True)
    return build_evidence(feature, tmp_path)


def test_every_step_declares_a_predicate() -> None:
    """A step cannot be half-declared, and the table is what makes that checkable.

    mypy rejects a row missing its third element outright; this covers the case
    mypy cannot see — a row present in `_STEPS` but absent from `_STEP_NAMES`, or
    a predicate that is not callable because something rebound it.
    """
    assert set(_STEPS) == set(_STEP_NAMES)
    for name, step in _STEPS.items():
        assert callable(step.predicate), f"{name} has no predicate"


def test_every_predicate_takes_evidence_and_returns_a_reading(tmp_path: Path) -> None:
    """One signature, asserted by calling all eight the same way.

    The shared signature is the whole of #314's scope item 1, and it is exactly
    what the rest of the suite cannot see: every existing assertion would still
    pass if one predicate quietly took a second argument.
    """
    ev = _evidence(tmp_path)
    for name, step in _STEPS.items():
        reading = step.predicate(ev)
        assert isinstance(reading, Reading), f"{name} did not return a Reading"
        assert reading.state in STATES, f"{name} returned state {reading.state!r}"


def test_a_predicate_takes_exactly_one_argument() -> None:
    """No predicate has grown a second parameter with a default.

    Calling them all in the test above would not catch that — a defaulted
    parameter is invisible at the call site and is how one predicate would drift
    back out of the shared shape.
    """
    for name, step in _STEPS.items():
        params = list(inspect.signature(step.predicate).parameters)
        # Arity, not the name. `params == ["ev"]` reads the same and fails on a
        # rename, which is a test about spelling wearing a test about shape.
        assert len(params) == 1, f"{name} takes {params}"


def test_the_annotation_is_the_reason_except_where_a_predicate_says_otherwise() -> None:
    """`Reading.renders()` is the one place that decision is made.

    Seven steps leave `annotation` unset and render their reason; `implement`
    sets it because it prefixes a tally its reason cannot be recovered from.
    A view that recomposed this itself would be the second inference path
    `pipeline-state-is-one-payload` forbids.
    """
    assert Reading("done").renders() is None
    assert Reading("in_progress", "because").renders() == "because"
    assert Reading("in_progress", "because", "1/2 done  because").renders() == (
        "1/2 done  because"
    )
    # An annotation that is deliberately empty is still an answer, and must not
    # fall back to the reason.
    assert Reading("done", "because", "").renders() == ""


def test_every_inconclusive_verdict_goes_through_blocks() -> None:
    """Nothing decides for itself whether silence stops a step.

    `decompose` did, which is the divergence #314 was opened to close: it read
    "no tracker" and "no issue map" as proceed without consulting the rule that
    owns that question, so the rule and the exception could drift apart with
    nothing to notice.

    Asserted over the source rather than by calling, because the property is
    "no other function reaches this conclusion", and a call-based test can only
    show that the paths it happened to exercise did the right thing.
    """
    tree = ast.parse(Path(_predicates.__file__).read_text())

    constructs_verdict: set[str] = set()
    calls_blocks: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for inner in ast.walk(node):
            # `verdict: Verdict = …` or a literal "inconclusive" anywhere in the body
            if isinstance(inner, ast.Constant) and inner.value == "inconclusive":
                constructs_verdict.add(node.name)
            if (
                isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Name)
                and inner.func.id == "blocks"
            ):
                calls_blocks.add(node.name)

    # `blocks` itself names the value in its own body; it is the rule, not a caller.
    constructs_verdict.discard("blocks")

    assert constructs_verdict, "the scan found nothing — it has stopped checking"
    assert constructs_verdict <= calls_blocks, (
        f"these reach an inconclusive verdict without asking `blocks`: "
        f"{sorted(constructs_verdict - calls_blocks)}"
    )


def test_evidence_is_frozen() -> None:
    """A predicate cannot change what a later predicate sees.

    Mutable, the step order would become load-bearing — and the order is the
    walk's business. Each predicate decides its own step from evidence, and
    nothing else.
    """
    ev = Evidence(Path("."), Path("."), "", False, "", False)
    with pytest.raises(dataclasses.FrozenInstanceError):
        ev.tasks_text = "changed"  # type: ignore[misc]


@pytest.mark.runs_mypy
def test_the_step_table_rejects_a_row_without_a_predicate(tmp_path: Path) -> None:
    """FR-003 is a type error, and this is what re-checks that it still is.

    The invariant was demonstrated by hand when #314 landed — a `_STEPS` row
    missing its predicate reports `[dict-item]` — but nothing re-ran it, so
    replacing `Step` with a plain tuple or widening the annotation to
    `dict[str, tuple]` would pass the whole suite while spending the property
    the table was chosen for.

    Shelled rather than asserted in prose because the check *is* mypy. Marked so
    the cost is visible: this is seconds, where the rest of the file is
    milliseconds.
    """
    # Against the real annotation, not a scratch one. A module that declares its
    # own `dict[str, Step]` type-checks the same whatever `_pipeline` says, so
    # this asserts the table's own declaration first — re-annotating `_STEPS` as
    # `dict[str, tuple]` spends the property while leaving a scratch check green.
    tree = ast.parse(Path(_pipeline_source()).read_text())
    declared = next(
        ast.unparse(n.annotation)
        for n in ast.walk(tree)
        if isinstance(n, ast.AnnAssign)
        and isinstance(n.target, ast.Name)
        and n.target.id == "_STEPS"
    )
    assert declared == "dict[str, Step]", f"_STEPS is declared {declared}"

    module = tmp_path / "bad_table.py"
    module.write_text(
        "from wfctl._pipeline import Step, _AUTOMATIC\n"
        "from wfctl import _predicates\n"
        "rows: dict[str, Step] = {\n"
        '    "ok": Step("/x", _AUTOMATIC, _predicates.specify),\n'
        '    "bad": ("/y", _AUTOMATIC),\n'
        "}\n"
    )
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-error-summary", str(module)],
        capture_output=True, text=True, cwd=Path(__file__).parent.parent,
    )
    assert result.returncode != 0, "a row without a predicate type-checked"
    assert "dict-item" in result.stdout, result.stdout


@pytest.mark.runs_mypy
def test_a_predicate_cannot_return_a_state_outside_the_four(tmp_path: Path) -> None:
    """FR-004, re-checked for the reason above.

    `State` narrows `str`, so widening it back — or annotating a predicate's
    return as `tuple[str, ...]` — is invisible at runtime and to every other
    test here.
    """
    module = tmp_path / "bad_state.py"
    module.write_text(
        "from wfctl._predicates import Evidence, Reading\n"
        "def broken(ev: Evidence) -> Reading:\n"
        '    return Reading("finished")\n'
    )
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-error-summary", str(module)],
        capture_output=True, text=True, cwd=Path(__file__).parent.parent,
    )
    assert result.returncode != 0, '"finished" type-checked as a state'
    assert "arg-type" in result.stdout, result.stdout
