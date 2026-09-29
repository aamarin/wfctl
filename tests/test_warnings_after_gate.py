"""A problem a check finds after its gate is a warning (#532, `check-rework-loop`).

The step keeps the state that lets the pipeline advance and carries the problem
as its reason. Before this, that reason reached `wfctl status` and nothing else:
`next`, `resume`, `next-step.md` and the orchestrate skill read the current
step's reason only, and a finished step is never current. So an unattended run
never saw it, which is the gap these tests close.

`decompose` is the one reader on `main` that returns a reason on a finished
step, so it carries the step cases. No pass reader does yet, so the pass cases
patch a probe pass into `_STEPS`, the way `test_plan_review_reader.py` already
does for a display-only pass.

Console assertions rely on `NO_COLOR`, which `conftest.py` pins for the run.
"""
from __future__ import annotations

import copy
import json
import types
from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import SPEC_SECTIONS
from tests.test_decompose_issues import _delivery, _use_tracker
from wfctl import _pipeline
from wfctl._evidence import Assessment, Evidence
from wfctl._paths import STEP_CLAIMS_DIR, arch_root
from wfctl._pipeline import (
    STORY_COMPLETE_FILE,
    StepWarning,
    SubStep,
    _apply_block_hold,
    _infer_steps,
    build_report,
    collect_warnings,
    warnings_payload,
)
from wfctl._session import record_blocked
from wfctl.cli import app

runner = CliRunner()

_UNKEYED = "2 issue rows without a key"
_BRANCH = "418-storyctl"


def _reader(state: str, reason: str | None = None, remedy: str | None = None):
    def read(ev: Evidence) -> Assessment:
        return Assessment(state, reason, remedy=remedy)  # type: ignore[arg-type]
    return read


def _probe(monkeypatch: pytest.MonkeyPatch, step: str, *subs: SubStep) -> None:
    """Append passes to a built-in step for the length of one test."""
    row = _pipeline._STEPS[step]
    monkeypatch.setitem(_pipeline._STEPS, step, row._replace(sub_steps=row.sub_steps + subs))


def _pass(name: str, state: str, reason: str | None = None, remedy: str | None = None,
          *, needs_person: bool = False) -> SubStep:
    return SubStep(name, f"/{name}", "automatic", _reader(state, reason, remedy),
                   needs_person=needs_person)


def _decompose_feature(env: types.SimpleNamespace, *keys: str) -> None:
    """Every task closed and a delivery plan whose rows carry `keys`. With two
    placeholders, `decompose` reads done and still says two rows lack a key."""
    _use_tracker(env.repo_root)
    env.stage_upstream_of("tasks")
    (env.spec_dir / "delivery.md").write_text(_delivery(*keys))


def _warned(env: types.SimpleNamespace) -> None:
    _decompose_feature(env, "_(TBD)_", "_(TBD)_")


def _keyed(env: types.SimpleNamespace) -> None:
    _decompose_feature(env, "#251", "#252")


def _report(env: types.SimpleNamespace) -> _pipeline.PipelineReport:
    return build_report(env.spec_dir, env.repo_root, env.agent_dir)


def _next_step(env: types.SimpleNamespace) -> str:
    return (env.agent_dir / "next-step.md").read_text()


# --- the list -----------------------------------------------------------------


def test_a_finished_step_with_a_reason_is_listed_as_a_warning(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The case the issue exists for, on the one reader that produces it today."""
    _warned(storyctl_dir)

    assert _report(storyctl_dir).warnings == (
        StepWarning("decompose", None, _UNKEYED, None),
    )


def test_a_tally_and_a_skipped_display_line_are_not_warnings(
    storyctl_dir: types.SimpleNamespace, spec_tree: Callable[..., Path], tmp_path: Path,
) -> None:
    """`display` on a finished step is what renders, and it is not a problem.

    `implement`'s `1/1 done` sits in `display` on a done step, and clarify's
    `scan never ran` sits in `display` on a skipped one. Reading either as a
    warning would put a task count in front of an unattended run as if it were
    something to fix.
    """
    _keyed(storyctl_dir)
    assert _report(storyctl_dir).warnings == ()

    unscanned = spec_tree(
        "design.md", "plan.md", content={"spec.md": "# Spec\n\n" + SPEC_SECTIONS},
    )
    steps = _infer_steps(unscanned, tmp_path)
    assert next(s for s in steps if s.name == "clarify").annotation == "scan never ran"
    assert collect_warnings(steps) == ()


def test_a_held_step_is_never_a_warning_whatever_its_reason(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A step that has not passed its gate has a problem to fix, not a warning.

    With a task still open, `decompose` holds on the same unkeyed rows, and the
    list must not repeat the reason `why:` already carries.
    """
    _use_tracker(storyctl_dir.repo_root)
    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    (storyctl_dir.spec_dir / "delivery.md").write_text(_delivery("_(TBD)_", "_(TBD)_"))

    report = _report(storyctl_dir)

    assert report.current == "decompose"
    assert report.warnings == ()


def test_a_step_a_host_block_holds_drops_out_of_the_list(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The list is read after the hold, so a held step's reason is the block's.

    Read before it, `decompose` would be listed as passed while `status` shows
    it held and routes back to it.
    """
    _warned(storyctl_dir)
    record_blocked(storyctl_dir.agent_dir, _BRANCH, "issue-create", "org policy", "decompose")

    assert _report(storyctl_dir).warnings == ()


def test_a_report_with_no_feature_directory_lists_nothing(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Every step is pending there, so the empty list is the whole answer."""
    report = build_report(None, storyctl_dir.repo_root, storyctl_dir.agent_dir)
    assert report.warnings == ()


def test_a_finished_pass_is_listed_with_its_name_and_its_whole_remedy(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The drawing check's shape once it follows the loop: a pass that has
    passed, a reason, and a fix that runs to more than one line, since the
    drawing check lists one `arch accept --dry-run` line per failing record."""
    _probe(monkeypatch, "specify", _pass("probe", "done", "a bad drawing", "  fix one\n  fix two"))
    storyctl_dir.stage_upstream_of("plan")

    assert _report(storyctl_dir).warnings == (
        StepWarning("specify", "probe", "a bad drawing", "  fix one\n  fix two"),
    )


def test_a_steps_own_warning_comes_before_its_passes(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pipeline order, the step's own reading first, so the list reads the way
    the status table does."""
    _probe(monkeypatch, "decompose", _pass("probe", "done", "a pass problem"))
    _warned(storyctl_dir)

    assert [w.where for w in _report(storyctl_dir).warnings] == ["decompose", "decompose.probe"]


def test_a_finished_pass_under_a_held_step_is_still_listed(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pass is judged on its own state, not its step's.

    The warned pass is declared first, because a pass after an outstanding one
    reads `pending` without its reader being called. Once it has passed, what
    holds the step above it is another pass's business, and dropping the
    warning would hide a problem that has nothing to do with the hold.
    """
    _probe(
        monkeypatch, "specify",
        _pass("warned", "done", "a pass problem"),
        _pass("holding", "in_progress"),
    )
    storyctl_dir.stage_upstream_of("plan")

    report = _report(storyctl_dir)

    assert report.current == "specify"
    assert [w.where for w in report.warnings] == ["specify.warned"]


def test_a_finished_pass_under_a_host_held_step_is_still_listed(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same rule when a host block holds the step: `_apply_block_hold`
    rewrites the step and leaves its passes as they read."""
    _probe(monkeypatch, "specify", _pass("warned", "done", "a pass problem"))
    storyctl_dir.stage_upstream_of("plan")
    record_blocked(storyctl_dir.agent_dir, _BRANCH, "push", "no", "specify")

    assert [w.where for w in _report(storyctl_dir).warnings] == ["specify.warned"]


def test_a_steps_own_warning_waits_while_a_pass_holds_the_step(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settled in clarify: the roll-up holds the step, so it has not passed.

    The warning is not lost. It is derived on every read, and it comes back the
    moment the pass clears, which the second half shows.
    """
    original = _pipeline._STEPS["decompose"]
    _probe(monkeypatch, "decompose", _pass("holding", "in_progress"))
    _warned(storyctl_dir)
    assert _report(storyctl_dir).warnings == ()

    monkeypatch.setitem(_pipeline._STEPS, "decompose", original)
    _probe(monkeypatch, "decompose", _pass("holding", "done"))
    assert [w.where for w in _report(storyctl_dir).warnings] == ["decompose"]


def test_a_claimed_pass_and_a_pass_skipped_for_a_person_are_not_warnings(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both read `skipped`, and neither carries a reason, only an annotation.

    A later reader that set a reason on either would turn a settled pass into
    a warning on every report, so the construction argument is pinned here
    rather than left to a comment.
    """
    _probe(
        monkeypatch, "specify",
        _pass("claimed", "done", "would warn if read"),
        _pass("person", "in_progress", needs_person=True),
    )
    storyctl_dir.stage_upstream_of("plan")
    claim = arch_root(storyctl_dir.repo_root) / STEP_CLAIMS_DIR / _BRANCH / "specify.claimed.md"
    claim.parent.mkdir(parents=True, exist_ok=True)
    claim.write_text(f"# specify.claimed does not apply — {_BRANCH}\n\nnot this change\n")

    steps = _infer_steps(storyctl_dir.spec_dir, storyctl_dir.repo_root, auto_approve=True)
    specify = next(s for s in steps if s.name == "specify")

    assert [p.state for p in specify.sub_steps] == ["skipped", "skipped"]
    assert collect_warnings(steps) == ()


def test_the_payload_writes_each_warning_under_the_four_wire_keys() -> None:
    """`pass`, not `pass_name`: the Python name is not the contract."""
    payload = warnings_payload((StepWarning("brainstorm", "architecture", "r", "fix"),))
    assert payload == [
        {"step": "brainstorm", "pass": "architecture", "reason": "r", "remedy": "fix"},
    ]


# --- routing ------------------------------------------------------------------


def test_a_warning_changes_nothing_the_pipeline_routes_on(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The rule the whole loop rests on: a warning never holds and never reroutes.

    One feature read twice, differing only in whether `decompose` carries its
    warning. Every step's reason cannot be compared across the two, since the
    warned step's reason is the warning, so the second half pins what matters
    about it instead: deriving the list leaves every step as inference left it.
    """
    _warned(storyctl_dir)
    warned = _report(storyctl_dir)
    (storyctl_dir.spec_dir / "delivery.md").write_text(_delivery("#251", "#252"))
    keyed = _report(storyctl_dir)

    assert warned.warnings and not keyed.warnings
    for field in ("current", "next_command", "auto", "attention", "stall"):
        assert getattr(warned, field) == getattr(keyed, field), field
    assert [s["state"] for s in warned.steps] == [s["state"] for s in keyed.steps]

    _warned(storyctl_dir)
    steps, _ = _apply_block_hold(
        _infer_steps(storyctl_dir.spec_dir, storyctl_dir.repo_root),
        storyctl_dir.agent_dir, _BRANCH,
    )
    before = copy.deepcopy(steps)
    collect_warnings(steps)
    assert steps == before


# --- status --json ------------------------------------------------------------


def test_status_json_carries_the_warning_and_an_empty_list_without_one(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Always present, so a consumer never has to tell a missing key from a
    wfctl too old to say."""
    _warned(storyctl_dir)
    payload = json.loads(runner.invoke(app, ["status", "--json"]).output)

    assert payload["version"] == "1.2"
    assert payload["warnings"] == [
        {"step": "decompose", "pass": None, "reason": _UNKEYED, "remedy": None},
    ]
    assert set(payload["warnings"][0]) == {"step", "pass", "reason", "remedy"}

    (storyctl_dir.spec_dir / "delivery.md").write_text(_delivery("#251", "#252"))
    assert json.loads(runner.invoke(app, ["status", "--json"]).output)["warnings"] == []


# --- next-step.md -------------------------------------------------------------


@pytest.mark.parametrize("command", ["resume", "next"])
def test_the_story_complete_file_carries_the_warning_after_its_line(
    storyctl_dir: types.SimpleNamespace, command: str,
) -> None:
    """The form `decompose`'s warning nearly always arrives in, since it stops
    holding only once every task is closed. `resume` is the writer the
    orchestrate skill runs, so it is checked as well as `next`."""
    _warned(storyctl_dir)
    runner.invoke(app, ["start"])

    assert runner.invoke(app, [command]).exit_code == 0
    assert _next_step(storyctl_dir) == STORY_COMPLETE_FILE + f"warning: decompose: {_UNKEYED}\n"


@pytest.mark.parametrize("command", ["resume", "next"])
def test_the_command_file_carries_the_warning_after_the_imperative(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, command: str,
) -> None:
    """The command and its `auto` are what they are without the warning, and
    the warning comes after `Run this command to continue.` so it cannot be
    read as the thing to run."""
    _probe(monkeypatch, "specify", _pass("probe", "done", "a bad drawing", "  fix one\n  fix two"))
    storyctl_dir.stage_upstream_of("plan")
    runner.invoke(app, ["start"])

    assert runner.invoke(app, [command]).exit_code == 0
    assert _next_step(storyctl_dir) == (
        "Next step: /plan-review\nauto: false\nRun this command to continue.\n"
        "warning: specify.probe: a bad drawing\n  fix one\n  fix two\n"
    )


def test_the_command_file_is_unchanged_when_nothing_warns(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Byte for byte what it was before warnings existed."""
    storyctl_dir.stage_upstream_of("plan")
    runner.invoke(app, ["start"])
    runner.invoke(app, ["resume"])

    assert _next_step(storyctl_dir) == (
        "Next step: /plan-review\nauto: false\nRun this command to continue.\n"
    )


# --- the console --------------------------------------------------------------


def test_resume_prints_the_warning_under_its_line_and_above_the_mode_notice(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The warning is a fact about the pipeline like the line it follows; the
    mode notice is about the session and stays last, where it was."""
    _warned(storyctl_dir)
    runner.invoke(app, ["start", "--auto-approve"])

    lines = runner.invoke(app, ["resume"]).output.splitlines()

    resumed = next(i for i, line in enumerate(lines) if line.startswith("↺ Resumed"))
    assert lines[resumed + 1] == f"  ⚠ decompose: {_UNKEYED}"
    notice = next(i for i, line in enumerate(lines) if line.startswith("auto-approve"))
    assert resumed + 1 < notice


def test_next_prints_the_warning_under_the_story_complete_line(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    _warned(storyctl_dir)
    runner.invoke(app, ["start"])

    lines = runner.invoke(app, ["next"]).output.splitlines()

    assert lines[-1] == f"  ⚠ decompose: {_UNKEYED}"
    assert lines[-2].startswith("Story complete")


def test_a_bracketed_reason_prints_literally_and_is_written_verbatim(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A reason is repo-supplied text, and `[wip]` is a legal slug. Unescaped,
    rich reads it as markup and drops it from the console."""
    _probe(monkeypatch, "specify", _pass("probe", "done", "record [wip] draws nothing"))
    storyctl_dir.stage_upstream_of("plan")
    runner.invoke(app, ["start"])

    output = runner.invoke(app, ["next"]).output

    assert "  ⚠ specify.probe: record [wip] draws nothing" in output
    assert "warning: specify.probe: record [wip] draws nothing\n" in _next_step(storyctl_dir)


def test_status_console_marks_the_warned_row_and_leaves_the_tally_alone(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A problem on a finished row read exactly like `implement`'s tally
    beside it. The mark is what tells them apart."""
    _warned(storyctl_dir)

    output = runner.invoke(app, ["status"]).output

    assert f"decompose    ●  ⚠ {_UNKEYED}" in output
    assert "implement    ●  1/1 done" in output
    assert "implement    ●  ⚠" not in output


def test_status_console_prints_a_pass_warnings_remedy_under_its_row(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The fix is printed where the problem is, since a finished step is never
    current and the current step's remedy line cannot carry it."""
    _probe(monkeypatch, "specify", _pass("probe", "done", "a bad drawing", "  fix one\n  fix two"))
    storyctl_dir.stage_upstream_of("plan")

    lines = runner.invoke(app, ["status"]).output.splitlines()

    row = next(i for i, line in enumerate(lines) if line.startswith("  probe"))
    assert "⚠ a bad drawing" in lines[row]
    assert lines[row + 1:row + 3] == ["  fix one", "  fix two"]


def test_status_console_shows_a_skipped_pass_only_when_it_carries_a_warning(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hiding a settled pass is what the `--all` filter is for; hiding a
    problem is not."""
    _probe(
        monkeypatch, "specify",
        _pass("warned", "skipped", "still wrong"),
        _pass("settled", "skipped"),
    )
    storyctl_dir.stage_upstream_of("plan")

    output = runner.invoke(app, ["status"]).output

    assert "  warned" in output and "⚠ still wrong" in output
    assert "  settled" not in output
