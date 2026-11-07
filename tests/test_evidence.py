"""The properties #314 bought, asserted so a later change cannot quietly spend them.

The snapshot beside this file pins what the readers *conclude*. This pins
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

from wfctl import _pipeline, _evidence

from wfctl.arch import _contexts
from wfctl._pipeline import _STEP_NAMES, _STEPS
from wfctl._evidence import Evidence, Assessment, State, build_evidence
from wfctl._review import HeadCoverage

STATES = set(get_args(State))


def _pipeline_source() -> str:
    """The file `_STEPS` is declared in."""
    return _pipeline.__file__


def _evidence_for(tmp_path: Path) -> Evidence:
    """An empty feature dir — every reader's `pending` arm, and none of its reads."""
    feature = tmp_path / "specs" / "314-feature"
    feature.mkdir(parents=True)
    return build_evidence(feature, tmp_path)


def test_every_step_declares_a_predicate() -> None:
    """A step cannot be half-declared, and the table is what makes that checkable.

    mypy rejects a row missing its third element outright; this covers the case
    mypy cannot see — a row present in `_STEPS` but absent from `_STEP_NAMES`, or
    a reader that is not callable because something rebound it.
    """
    assert set(_STEPS) == set(_STEP_NAMES)
    for name, step in _STEPS.items():
        assert callable(step.reads), f"{name} has no evidence reader"


def test_every_predicate_takes_evidence_and_returns_a_reading(tmp_path: Path) -> None:
    """One signature, asserted by calling all eight the same way.

    The shared signature is the whole of #314's scope item 1, and it is exactly
    what the rest of the suite cannot see: every existing assertion would still
    pass if one reader quietly took a second argument.
    """
    ev = _evidence_for(tmp_path)
    for name, step in _STEPS.items():
        reading = step.reads(ev)
        assert isinstance(reading, Assessment), f"{name} did not return an Assessment"
        assert reading.state in STATES, f"{name} returned state {reading.state!r}"


def test_a_reader_can_take_a_heading_inside_another_steps_artifact(
    tmp_path: Path,
) -> None:
    """FR-008: a `SubStep.reads` is a plain callable, not `evidence`'s
    file-exists sugar alone — `clarify` already reads a heading inside
    `spec.md` rather than a file of its own, and a declared pass that could
    only express "this file exists" would be a real narrowing of what a
    built-in pass can do. Neither `architecture` nor `design-doc` exercises
    this today; a regression to a path-only signature would not fail either
    of them, which is exactly why the capability needs its own reader here."""
    from wfctl._pipeline import SubStep

    def reads_a_heading(ev: Evidence) -> Assessment:
        return Assessment("done" if "## Approved" in ev.spec_text else "in_progress")

    sub = SubStep(name="approval", command=None, on_finish="review_required",
                  reads=reads_a_heading)

    feature = tmp_path / "specs" / "314-feature"
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text("# Spec\n\n## Approved\n\nyes\n")
    ev = build_evidence(feature, tmp_path)

    assert sub.reads(ev).state == "done"


def test_a_predicate_takes_exactly_one_argument() -> None:
    """No reader has grown a second parameter with a default.

    Calling them all in the test above would not catch that — a defaulted
    parameter is invisible at the call site and is how one reader would drift
    back out of the shared shape.
    """
    for name, step in _STEPS.items():
        params = list(inspect.signature(step.reads).parameters)
        # Arity, not the name. `params == ["ev"]` reads the same and fails on a
        # rename, which is a test about spelling wearing a test about shape.
        assert len(params) == 1, f"{name} takes {params}"


def test_the_display_string_is_the_reason_except_where_a_reader_says_otherwise() -> None:
    """`Assessment.renders()` is the one place that decision is made.

    Seven steps leave `display` unset and render their reason; `implement`
    sets it because it prefixes a tally its reason cannot be recovered from.
    A view that recomposed this itself would be the second inference path
    `pipeline-state-is-one-payload` forbids.
    """
    assert Assessment("done").renders() is None
    assert Assessment("in_progress", "because").renders() == "because"
    assert Assessment("in_progress", "because", "1/2 done  because").renders() == (
        "1/2 done  because"
    )
    # A display string that is deliberately empty is still an answer, and must not
    # fall back to the reason.
    assert Assessment("done", "because", "").renders() == ""


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
    tree = ast.parse(Path(_evidence.__file__).read_text())

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
    """A reader cannot change what a later reader sees.

    Mutable, the step order would become load-bearing — and the order is the
    walk's business. Each reader decides its own step from evidence, and
    nothing else.
    """
    # Positional, so a field added to `Evidence` breaks this line rather than
    # silently defaulting — which is how #299's `verification` was caught before
    # it could ship as an optional the builder might forget to fill.
    ev = Evidence(Path("."), Path("."), "", False, False, "", False, "", False, 0, 0, None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        ev.tasks_text = "changed"  # type: ignore[misc]


@pytest.mark.runs_mypy
def test_the_step_table_rejects_a_row_without_a_predicate(tmp_path: Path) -> None:
    """FR-003 is a type error, and this is what re-checks that it still is.

    The invariant was demonstrated by hand when #314 landed — a `_STEPS` row
    missing its reader reports `[dict-item]` — but nothing re-ran it, so
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
        "from wfctl import _evidence\n"
        "rows: dict[str, Step] = {\n"
        '    "ok": Step("/x", _AUTOMATIC, _evidence.specify),\n'
        '    "bad": ("/y", _AUTOMATIC),\n'
        "}\n"
    )
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-error-summary", str(module)],
        capture_output=True, text=True, cwd=Path(__file__).parent.parent,
    )
    assert result.returncode != 0, "a row without a reader type-checked"
    assert "dict-item" in result.stdout, result.stdout


@pytest.mark.runs_mypy
def test_a_predicate_cannot_return_a_state_outside_the_four(tmp_path: Path) -> None:
    """FR-004, re-checked for the reason above.

    `State` narrows `str`, so widening it back — or annotating a reader's
    return as `tuple[str, ...]` — is invisible at runtime and to every other
    test here.
    """
    module = tmp_path / "bad_state.py"
    module.write_text(
        "from wfctl._evidence import Evidence, Assessment\n"
        "def broken(ev: Evidence) -> Assessment:\n"
        '    return Assessment("finished")\n'
    )
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-error-summary", str(module)],
        capture_output=True, text=True, cwd=Path(__file__).parent.parent,
    )
    assert result.returncode != 0, '"finished" type-checked as a state'
    assert "arg-type" in result.stdout, result.stdout


# --- review --------------------------------------------------------------------

REVIEWED = "3f2a1c9d0e1f2a3b4c5d6e7f8091a2b3c4d5e6f7"
C1, C2, C3, C4 = (f"{n}" * 40 for n in "1234")


def _implemented(tmp_path: Path, coverage: HeadCoverage | None) -> Evidence:
    """Evidence whose `implement` reads done: every task closed, no definition
    of done blocking, and `coverage` as the review field."""
    return Evidence(
        spec_dir=tmp_path, repo_root=tmp_path, spec_text="", has_markers=False,
        spec_is_template=False, plan_text="", plan_is_template=False,
        tasks_text="- [x] T001 done\n", tasks_open=False, tasks_done=1, tasks_total=1,
        verification=None, review=coverage,
    )


def _coverage(
    pending: dict[str, tuple[str, ...]] | None = None,
    since: dict[str, str | None] | None = None,
    capped: tuple[str, ...] = (),
    error: str | None = None,
    remedy: str | None = None,
    cap: int | None = None,
) -> HeadCoverage:
    return HeadCoverage(
        pending or {}, since or {}, capped, "refs/remotes/origin/main", error, remedy, cap,
    )


def test_review_is_pending_until_implement_is_done(tmp_path: Path) -> None:
    ev = dataclasses.replace(_implemented(tmp_path, None), tasks_open=True)

    assert _evidence.review(ev) == Assessment("pending")


def test_review_holds_on_an_error_with_its_remedy(tmp_path: Path) -> None:
    """A person has to fix the cause, so the reason blocks the step and the
    remedy names the fix rather than the panel, which fails the same way."""
    ev = _implemented(tmp_path, _coverage(error="can't read the review config: x", remedy="fix"))

    assert _evidence.review(ev) == Assessment(
        "in_progress", "can't read the review config: x", remedy="fix",
    )


def test_review_holds_on_a_group_with_no_rounds_left(tmp_path: Path) -> None:
    """`review start` refuses a capped group until a person approves, so the
    row blocks rather than sending an unattended run into that refusal."""
    ev = _implemented(tmp_path, _coverage(
        pending={"security": (C1,)}, since={"security": REVIEWED}, capped=("security",), cap=3,
    ))

    reading = _evidence.review(ev)

    assert reading.state == "in_progress"
    assert reading.reason == "security has used its 3 review rounds, so a person has to sign off"
    assert reading.display is None
    assert reading.remedy == "  Ask the user to run `wfctl review sign-off` in their own terminal."


def test_review_names_every_capped_group_together(tmp_path: Path) -> None:
    ev = _implemented(tmp_path, _coverage(
        pending={"security": (C1,), "code": (C1,)}, since={"security": None, "code": None},
        capped=("security", "code"), cap=2,
    ))

    assert _evidence.review(ev).reason == (
        "security, code have used their 2 review rounds, so a person has to sign off"
    )


def test_review_holds_at_a_cap_of_zero(tmp_path: Path) -> None:
    ev = _implemented(tmp_path, _coverage(
        pending={"security": (C1,), "code": (C1,)}, since={"security": None, "code": None},
        capped=("security", "code"), cap=0,
    ))

    assert _evidence.review(ev).reason == "review.rounds is 0, so a person has to sign off"


def test_review_is_done_when_no_group_has_unreviewed_commits(tmp_path: Path) -> None:
    assert _evidence.review(_implemented(tmp_path, _coverage())) == Assessment("done")


def test_review_in_progress_carries_no_reason_so_an_unattended_run_starts_the_panel(
    tmp_path: Path,
) -> None:
    ev = _implemented(tmp_path, _coverage(
        pending={"security": (C1, C2, C3, C4), "code": (C1, C2, C3, C4)},
        since={"security": None, "code": None},
    ))

    assert _evidence.review(ev) == Assessment(
        "in_progress", None, "security, code: not reviewed yet (4 commits)",
    )


def test_review_display_counts_from_the_newest_reviewed_commit(tmp_path: Path) -> None:
    ev = _implemented(tmp_path, _coverage(
        pending={"security": (C1,), "code": (C1,)},
        since={"security": REVIEWED, "code": REVIEWED},
    ))

    assert _evidence.review(ev).display == "security, code: 1 commit unreviewed since 3f2a1c9"


def test_review_display_gives_each_state_its_own_part(tmp_path: Path) -> None:
    """The console prints a step's note on the step's own line, so two states
    share that line, one part each."""
    ev = _implemented(tmp_path, _coverage(
        pending={"security": (C1, C2, C3, C4), "code": (C3, C4)},
        since={"security": None, "code": REVIEWED},
    ))

    assert _evidence.review(ev).display == (
        "security: not reviewed yet (4 commits); code: 2 commits unreviewed since 3f2a1c9"
    )


def test_build_evidence_reads_no_review_while_implement_is_not_done(tmp_path: Path) -> None:
    """The review reading costs git calls, so a branch earlier in the pipeline
    pays nothing for it (research R2)."""
    assert _evidence_for(tmp_path).review is None


# --- records_for_branch ------------------------------------------------------


def _for_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, design: str | None
) -> _contexts.Selection:
    """An arch root with a name list and two accepted records, and a spec root
    holding the branch's folder with `design` as its design.md, or no folder at
    all when `design` is None."""
    arch, specs = tmp_path / "arch", tmp_path / "specs"
    (arch / "domain").mkdir(parents=True)
    (arch / "domain" / "wfctl.md").write_text(
        "# wfctl\n\nState: accepted\nContexts: install-and-drift, session-continuity\n\n## Body\n"
    )
    (arch / "everywhere.md").write_text("---\nstatus: accepted\n---\n\n# E\n")
    (arch / "session.md").write_text(
        "---\nstatus: accepted\ngoverns: session-continuity\n---\n\n# S\n"
    )
    (arch / "draft.md").write_text("---\nstatus: proposed\n---\n\n# D\n")
    specs.mkdir()
    if design is not None:
        (specs / "700-x").mkdir()
        (specs / "700-x" / "design.md").write_text(design)
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(arch))
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))
    return _evidence.records_for_branch(tmp_path, "700-x")


def test_records_for_branch_with_no_spec_folder_prints_every_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A branch's first session has no spec folder, so nothing says which
    contexts it changes, and every accepted record binds it."""
    selection = _for_branch(tmp_path, monkeypatch, None)

    assert sorted(r.slug for r in selection.records) == ["everywhere", "session"]
    assert selection.unlisted and not selection.narrowed


def test_records_for_branch_narrows_on_the_design_contexts_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The proposed record is never counted, so it is neither printed nor left
    out."""
    selection = _for_branch(tmp_path, monkeypatch, "# t\n\nContexts: install-and-drift\n")

    assert [r.slug for r in selection.records] == ["everywhere"]
    assert selection.left_out == 1
    assert selection.contexts == ("install-and-drift",)


def test_records_for_branch_reads_an_unreadable_design_as_no_contexts_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A design.md that isn't text can't say which contexts the branch lists,
    so the branch is treated as listing none rather than as narrowed."""
    _for_branch(tmp_path, monkeypatch, "")
    (tmp_path / "specs" / "700-x" / "design.md").write_bytes(b"\xff\xfe\x00bad")

    selection = _evidence.records_for_branch(tmp_path, "700-x")

    assert selection.unlisted and selection.left_out == 0
