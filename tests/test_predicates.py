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
from pathlib import Path
from typing import get_args

import pytest

from wfctl import _predicates
from wfctl._pipeline import _STEP_NAMES, _STEPS
from wfctl._predicates import Evidence, Reading, State, build_evidence

STATES = set(get_args(State))


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
        assert params == ["ev"], f"{name} takes {params}"


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
