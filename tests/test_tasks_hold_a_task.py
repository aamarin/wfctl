"""`tasks.md` earns its step by holding a task, not by existing (#308).

Found by the predicate audit in #300. `tasks` read `done` on any non-empty
file, and `_tasks_open` spelled "finished" as *no open checkbox remains* — so a
file of prose satisfied both, and `implement` walked through to its verification
read at `0/0 done` having proved nothing about the work. Both steps carry
`automatic`, so `speckit-orchestrate` passed each without pausing: one file
clearing two unattended steps.

The reproduction below is the issue's, constructed against `_infer_steps` with
`spec.md`, `plan.md` and `checklists/analysis-report.md` present. Before the fix
it printed `tasks done` and `implement done  0/0 done`.

No spec dir in the durable store has ever held a checkbox-free `tasks.md` — 23
on disk, 30 versions across the history of `specs-trunk`, every one of them with
at least twelve boxes. So the state these tests reject is not a legitimate one
being refused; it is a `tasks` step that produced nothing.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from tests.conftest import CLEAN_SPEC
from wfctl._pipeline import _infer_steps, _PipelineStep, build_report

# The issue's file: a `tasks.md` a step wrote and no task in it.
_PROSE = "prose, no checkboxes\n"


def _feature(spec_tree: Callable[..., Path], tasks: str, **extra: str) -> Path:
    """The reproduction's artifact set, with `tasks.md` swapped per test.

    Everything upstream of `tasks` present and clean, because `_infer_steps`
    cascades — a feature missing `spec.md` reads `tasks pending` for a reason
    that has nothing to do with what the file holds.
    """
    return spec_tree(
        content={
            "spec.md": CLEAN_SPEC,
            "plan.md": "a plan\n",
            "checklists/analysis-report.md": "a report\n",
            "tasks.md": tasks,
            **extra,
        }
    )


def _states(feature: Path, repo_root: Path) -> dict[str, str]:
    return {s.name: s.state for s in _infer_steps(feature, repo_root)}


def _step(feature: Path, repo_root: Path, name: str) -> _PipelineStep:
    return next(s for s in _infer_steps(feature, repo_root) if s.name == name)


def test_a_tasks_file_holding_no_task_does_not_finish_the_tasks_step(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The first half of #308, and the one an eye on the table would catch.

    `done` here says the step ran and left something behind. It left a file; it
    did not leave a task, and the annotation is what tells the two apart.
    """
    feature = _feature(spec_tree, _PROSE)
    step = _step(feature, tmp_path, "tasks")

    assert step.state == "in_progress"
    assert step.annotation == "tasks.md holds no task"


def test_a_tasks_file_holding_no_task_never_reads_implement_done(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The half that executes, and the reason the issue is a bug rather than a smell.

    In a repo with no definition of done configured, `0/0 done` was the entire
    evidence that the story was implemented — #148's shape, a weak predicate
    under a load-bearing `automatic` flag.
    """
    assert _states(_feature(spec_tree, _PROSE), tmp_path)["implement"] != "done"


def test_a_delivery_plan_does_not_carry_a_task_free_file_into_implement(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The configuration where the cascade cannot do the work for us.

    Without `delivery.md`, decompose reads `pending` and everything after it
    cascades, so `implement` is off `done` whatever the implement arm believes.
    With one, decompose reads `done` and the implement arm is evaluated on its
    own — which is where `_tasks_open` has to be the thing that changed.
    """
    feature = _feature(spec_tree, _PROSE, **{"delivery.md": "a delivery plan\n"})
    states = _states(feature, tmp_path)

    assert states["decompose"] == "done"
    assert states["implement"] != "done"


def test_the_tasks_step_is_not_automatic_while_its_file_holds_no_task(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """What `speckit-orchestrate` acts on, which is not the step table.

    A blocked step is never automatic whatever `_STEPS` says
    (`next_step_content`), and the reason is what makes it blocked — so the
    routing read is a separate assertion from the state name, not a rendering
    of it.
    """
    report = build_report(_feature(spec_tree, _PROSE), tmp_path, tmp_path)

    assert (report.current, report.next_command, report.auto) == (
        "tasks",
        "/speckit.tasks",
        False,
    )


def test_a_tasks_file_with_boxes_still_finishes_the_tasks_step(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The rung is raised to 2, not to 3 — nothing here reads what a task says.

    A file whose boxes are all ticked is the ordinary shipped story, and it went
    on reading `done` through this change. Without this the fix is
    indistinguishable from one that blocks every feature in the store.
    """
    feature = _feature(spec_tree, "- [x] T001 write it\n- [ ] T002 test it\n")

    assert _states(feature, tmp_path)["tasks"] == "done"
