"""Where the pipeline stops around a plan review, in both approval modes.

Research R4 gives the table this file reproduces, one test per row, each run
with auto-approve off and on. FR-003 needs two stops when nobody granted the
mode: after a review with an open BLOCKER, and after a clean review before
`tasks`. Both have to be in the payload, since `speckit-orchestrate` acts on
`auto` and on nothing a skill remembers, so every assertion here is on what
`build_report` returns rather than on a reader's state.
"""
from __future__ import annotations

import json
import types

import pytest
from typer.testing import CliRunner

from tests.conftest import CLEAN_PLAN, CLEAN_SPEC, write_plan_review
from wfctl import _session
from wfctl._pipeline import PipelineReport, build_report
from wfctl.cli import app

runner = CliRunner()

_MODES = pytest.mark.parametrize("granted", [False, True], ids=["attended", "auto-approve"])


def _planned(storyctl_dir: types.SimpleNamespace, granted: bool) -> None:
    """A feature whose plan is complete and whose `tasks.md` is not written,
    in the approval mode the test names. No `design.md`, so `brainstorm` reads
    `skipped` and the only step a test here can hold is `plan`."""
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    storyctl_dir.make_spec_artifact("plan", content=CLEAN_PLAN)
    if granted:
        _session.grant_auto_approve(storyctl_dir.agent_dir, True)


def _review(storyctl_dir: types.SimpleNamespace, blockers: int) -> None:
    """A report of the plan as it is now, with `blockers` open."""
    write_plan_review(storyctl_dir.spec_dir, blockers)


def _report(storyctl_dir: types.SimpleNamespace) -> PipelineReport:
    return build_report(storyctl_dir.spec_dir, storyctl_dir.repo_root, storyctl_dir.agent_dir)


def _plan(report: PipelineReport) -> dict:
    return next(s for s in report.steps if s["name"] == "plan")


@_MODES
def test_a_plan_nobody_has_reviewed_names_the_review(
    storyctl_dir: types.SimpleNamespace, granted: bool
) -> None:
    """R4's first row, after `/speckit.plan` (FR-002). Attended, the pipeline
    stops and names `/plan-review`; granted, the loop runs it. The pass being
    current is the whole of the first review happening at all, since a pass
    that read `pending` here would let `tasks` become current and skip it."""
    _planned(storyctl_dir, granted)

    report = _report(storyctl_dir)

    assert (report.current, report.next_command, report.auto) == ("plan", "/plan-review", granted)
    assert _plan(report)["reason"] is None


@_MODES
def test_a_review_with_an_open_blocker_names_the_review_again(
    storyctl_dir: types.SimpleNamespace, granted: bool
) -> None:
    """R4's second row (FR-026). The command is the same in both modes, and
    what the wrapper does with it (revise, or review a changed input) is its
    own business (R5). What wfctl owes is that `tasks` is not the answer and
    that `auto` is the grant, so an attended run stops for a person here."""
    _planned(storyctl_dir, granted)
    _review(storyctl_dir, blockers=2)

    report = _report(storyctl_dir)

    assert (report.current, report.next_command, report.auto) == ("plan", "/plan-review", granted)
    assert _plan(report)["annotation"] == "2 BLOCKER findings open"
    assert _plan(report)["reason"] is None


@_MODES
def test_a_revised_plan_names_the_review_again(
    storyctl_dir: types.SimpleNamespace, granted: bool
) -> None:
    """R4's third row, after a revision. The report still counts the BLOCKER
    it found in the plan before the edit, and routing anywhere but
    `/plan-review` would either run `tasks` over an unreviewed plan or send the
    reader to `/speckit.plan`, which copies the template over `plan.md` (R3).

    An edit to a plan whose review was clean is the other half of this row,
    and it needs the stale reading, so it is tested with that reading
    (rows 4 and 5 of data-model.md § Pass state)."""
    _planned(storyctl_dir, granted)
    _review(storyctl_dir, blockers=1)
    plan_md = storyctl_dir.spec_dir / "plan.md"
    plan_md.write_text(plan_md.read_text() + "\nRevised against the open BLOCKER.\n")

    report = _report(storyctl_dir)

    assert (report.current, report.next_command, report.auto) == ("plan", "/plan-review", granted)


@_MODES
def test_a_clean_review_stops_before_tasks_unless_the_mode_was_granted(
    storyctl_dir: types.SimpleNamespace, granted: bool
) -> None:
    """R4's fourth row (FR-003). `tasks` requires review, so an attended run
    stops here for a person even though the review found nothing blocking; a
    grant answers that stop. Before this feature `tasks` was automatic, and a
    clean review ran straight into it with nobody there."""
    _planned(storyctl_dir, granted)
    _review(storyctl_dir, blockers=0)

    report = _report(storyctl_dir)

    assert (report.current, report.next_command, report.auto) == (
        "tasks", "/speckit.tasks", granted,
    )
    assert _plan(report)["state"] == "done"


def test_no_run_of_resume_reaches_tasks_while_a_blocker_is_open(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """SC-008: with auto-approve on, zero runs reach `tasks` while the review
    of the current plan has a BLOCKER open. The grant makes every stop
    automatic, so an open BLOCKER is the only thing between an unattended
    loop and `tasks`, and a reader that let it through on the second or third
    pass would pass a single-call test. Each call re-reads the disk, and
    nothing a `resume` writes may move the answer."""
    _planned(storyctl_dir, granted=False)
    assert runner.invoke(app, ["start", "--auto-approve"]).exit_code == 0
    _review(storyctl_dir, blockers=1)

    for _ in range(5):
        result = runner.invoke(app, ["resume"])
        assert result.exit_code == 0, result.output
        written = (storyctl_dir.agent_dir / "next-step.md").read_text()
        assert "/speckit.tasks" not in written
        assert "Next step: /plan-review" in written
        assert "auto: true" in written

        payload = json.loads(runner.invoke(app, ["status", "--json"]).output)
        assert payload["next_command"] == "/plan-review"
        assert payload["auto"] is True
