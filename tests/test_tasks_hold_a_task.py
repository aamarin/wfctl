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

from tests.conftest import CLEAN_PLAN, CLEAN_SPEC
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
            "plan.md": CLEAN_PLAN,
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


def test_decompose_is_not_passed_by_on_a_task_free_file(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The other transition `_tasks_open` moved, raised by a reviewer as unpinned.

    `skipped` there means the pipeline went past decompose because the tasks
    were all closed. They were not closed; there were none. `pending` is the
    state that says so, and it is what cascades `implement` in the reproduction
    above — so the test one row up would go on passing if this quietly changed
    back.
    """
    assert _states(_feature(spec_tree, _PROSE), tmp_path)["decompose"] == "pending"


def test_the_implementation_sentinel_passes_by_a_task_free_tasks_step(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The trap two reviewers found: a shipped story with nowhere left to go.

    `/speckit.tasks` rewrites `tasks.md` from a template, so a story already
    declared implemented was being sent to a command that cannot help it, with
    no route to `/end-session` while the step blocked — the same shape #8's
    review caught on the decompose row.

    `skipped`, never `done`. The step still produced no task, and the sentinel is
    written by hand at the end of implementation, which is the declaration that
    was missing when a bare file cleared both steps unattended.
    """
    feature = _feature(
        spec_tree, _PROSE, **{"checklists/implement-complete.md": "done 2026-09-09\n"}
    )
    report = build_report(feature, tmp_path, tmp_path)

    assert _states(feature, tmp_path)["tasks"] == "skipped"
    assert (report.current, report.next_command) == (None, None)


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


def test_a_worked_example_is_not_a_task(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """Raised on the open change: the tally now gates an automatic step.

    A file that documents what a task line looks like holds no task, and the
    unanchored match would have counted the example — clearing the step the
    example is explaining. The spec arm has read past fences and inline spans
    since it had markers to find; this is the same reading, on the file whose
    count became load-bearing.

    The ticked example is the one that matters: an open one leaves `implement`
    blocked anyway, so only `- [x]` reaches the end of the pipeline on nothing.
    """
    fenced = "How to write a task:\n\n```\n- [x] T001 do the thing\n```\n"
    inline = "A task line reads `- [x] T001 do the thing`.\n"

    for tasks in (fenced, inline):
        feature = _feature(spec_tree, tasks)
        assert _states(feature, tmp_path)["tasks"] == "in_progress"
        assert _states(feature, tmp_path)["implement"] != "done"


def test_a_checkpoint_line_counts_as_a_task(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The half of that review comment the store contradicts.

    Anchoring the match to a list bullet was the other half of the fix
    suggested for the example above. Real files write a merge gate as
    `**Checkpoint**: [X] T006 …`, and `43-vendor-wf-skills/tasks.md` carries two
    — so anchoring would drop real work rather than a worked example.
    """
    tasks = "**Checkpoint**: [X] T006 Validate setup — merge gate.\n"

    assert _states(_feature(spec_tree, tasks), tmp_path)["tasks"] == "done"


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
