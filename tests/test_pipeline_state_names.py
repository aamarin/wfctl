"""The four state names, and the guarantee that inference produces nothing else.

`_infer_steps` used to carry `● ▶ ○ –` directly. Two of those, `●` and `–`, both
mean "does not block" — so a caller holding only the value could not tell a step
that ran from one that was passed by. That was tolerable while the drawing was
for a human beside the code; it stopped being tolerable when the pipeline report
became the agent's only read.

These pin each name to the artifact combination that earns it. The rendering
tests live in `test_pipeline_commands.py`; nothing here asserts on a glyph,
because a glyph reaching this layer is the defect.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import json
import types

import pytest
from typer.testing import CliRunner

from tests.conftest import CLEAN_SPEC
from wfctl import cli
from wfctl.cli import app
from wfctl._pipeline import PipelineReport, _infer_steps, build_report

# Every symbol the renderer can emit. Asserted against *values*, never source
# text: `_pipeline.py` names these in comments, and `_verify` prints some of them
# in its own output, so a grep-based check would fail for reasons it does not mean.
GLYPHS = "●▶○–"

runner = CliRunner()


def _states(spec_dir: Path, repo_root: Path) -> dict[str, str]:
    return {s.name: s.state for s in _infer_steps(spec_dir, repo_root)}


def test_a_step_with_its_artifact_present_is_done(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """`done` means the step ran and left something behind."""
    assert _states(spec_tree("design.md"), tmp_path)["brainstorm"] == "done"


def test_a_step_passed_by_without_running_is_skipped(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """`skipped` is the state `done` used to be indistinguishable from.

    A change that draws no new boundary is allowed to have no design — that is
    `design-levels`, not a defect. Rendered, this and `done` are `–` and `●`;
    named, a reader can tell which of the two histories it has.
    """
    assert _states(spec_tree(content={"spec.md": CLEAN_SPEC}), tmp_path)["brainstorm"] == "skipped"


def test_a_step_with_work_still_open_is_in_progress(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """`in_progress` is the step a reader is sent to, not one they are past."""
    marked = spec_tree(content={"spec.md": "# Spec\n\n[NEEDS CLARIFICATION: which?]\n"})
    assert _states(marked, tmp_path)["specify"] == "in_progress"


def test_a_step_nothing_has_reached_yet_is_pending(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """`pending` and `skipped` are both "no artifact here" and mean opposites.

    Pending is ahead of the reader; skipped is behind them. Collapsing the two
    is what sent a brand-new feature to the middle of the pipeline.
    """
    assert _states(spec_tree(content={"spec.md": CLEAN_SPEC}), tmp_path)["plan"] == "pending"


def test_no_value_in_the_report_is_a_glyph(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """Every field of the report, not just `state` on a step.

    A glyph in an annotation, in `current`, or in `next_command` is the same
    defect as a glyph in `state`: a value a caller cannot act on without knowing
    how it was drawn. Walking the whole payload covers a field added later
    without this test being touched.

    The four names are spelled out here rather than imported from the module
    under test — an expectation that reads its subject proves only that the
    subject is self-consistent, and a fifth state added to both would pass.
    """
    feature = spec_tree("design.md", "plan.md", content={
        "spec.md": CLEAN_SPEC,
        "tasks.md": "- [ ] T001 open\n",
    })
    report = build_report(feature, tmp_path, tmp_path)

    for step in report.steps:
        assert step["state"] in ("done", "in_progress", "pending", "skipped")
        for value in step.values():
            assert not (isinstance(value, str) and set(value) & set(GLYPHS))

    for value in (report.current, report.next_command):
        assert not (isinstance(value, str) and set(value) & set(GLYPHS))


def test_every_reachable_state_is_one_of_the_four_names(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """Sweeps the artifact combinations, so a branch returning a fifth thing fails.

    `_infer_steps` assigns a state in ten places. A test that only checked the
    combinations it happened to name would be silent on the one branch someone
    edits next.
    """
    combinations = [
        (),
        ("design.md",),
        ("design.md", "plan.md"),
        ("design.md", "plan.md", "delivery.md", "checklists/analysis-report.md"),
    ]
    contents = [
        {},
        {"spec.md": CLEAN_SPEC},
        {"spec.md": "# Spec\n\n[NEEDS CLARIFICATION: which?]\n"},
        {"spec.md": CLEAN_SPEC, "tasks.md": "- [ ] T001 open\n"},
        {"spec.md": CLEAN_SPEC, "tasks.md": "- [x] T001 done\n"},
    ]
    seen = set()
    for names in combinations:
        for content in contents:
            for step in build_report(spec_tree(*names, content=content), tmp_path, tmp_path).steps:
                assert step["state"] in ("done", "in_progress", "pending", "skipped")
                seen.add(step["state"])

    # All four have to be reachable, or the sweep is asserting over three states
    # and calling it four.
    assert seen == {"done", "in_progress", "pending", "skipped"}


def test_changing_the_glyph_map_changes_the_drawing_and_nothing_else(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """User Story 3's second acceptance scenario, stated as code.

    The symbols are a rendering choice and live in exactly one place. Swapping
    them must move the console output and leave every inferred state where it
    was — if an inferred state moved too, the map is being consulted somewhere
    it should not be.
    """
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)

    before = json.loads(runner.invoke(app, ["status", "--json"]).output)
    assert "specify      ●" in runner.invoke(app, ["status"]).output

    monkeypatch.setitem(cli._STATE_GLYPH, "done", ("✔", "green"))

    assert "specify      ✔" in runner.invoke(app, ["status"]).output
    assert json.loads(runner.invoke(app, ["status", "--json"]).output) == before


# --- the report's one invariant (#42) -----------------------------------------


def test_a_current_step_always_carries_the_command_that_advances_it(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The pairing `_STEPS` was collapsed into one table to guarantee.

    A step that is current with no command to advance it read as a finished
    pipeline at the call site, so `wfctl next` announced "story complete" with
    half the pipeline unrun.
    """
    report = build_report(spec_tree(content={"spec.md": CLEAN_SPEC}), tmp_path, tmp_path)
    assert report.current == "plan"
    assert report.next_command == "/speckit.plan"


def test_a_finished_story_has_neither_a_current_step_nor_a_command(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The other half of the same invariant: both None, never one of them."""
    done = spec_tree(
        "design.md", "plan.md", "delivery.md", "checklists/analysis-report.md",
        content={"spec.md": CLEAN_SPEC, "tasks.md": "- [x] T001 done\n"},
    )
    report = build_report(done, tmp_path, tmp_path)
    assert report.current is None
    assert report.next_command is None


def test_a_report_with_a_current_step_and_no_command_cannot_be_built(
    tmp_path: Path
) -> None:
    """Unconstructible, not merely untested.

    Every branch that builds a report goes through `__init__`, so the pairing
    holds for code written after this one without that code knowing the rule.
    """
    with pytest.raises(ValueError):
        PipelineReport(steps=[], current="plan", next_command=None, session_started=True)
