"""`wfctl blocked` — the verb an agent uses to report a host refusal
wfctl never ran (#364).

Both modes, exit codes, no-grant, no-feature. The pipeline effect of a block —
whether it holds a step — is `test_blocked_holds_step.py`; this file is the
command surface alone.
"""
from __future__ import annotations

import json
import types

from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def _payload() -> dict:
    return json.loads(runner.invoke(app, ["status", "--json"]).output)


def test_a_run_holding_no_grant_can_still_report_a_block(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-006. The case the rejected `--blocked`-on-notify baseline fails,
    stated as a test rather than as an argument: this branch has never had
    `wfctl start --allow-notify` run on it, and the report still succeeds."""
    result = runner.invoke(
        app, ["blocked", "issue-comment", "--reason", "host classifier: External System Writes"]
    )
    assert result.exit_code == 0, result.output

    log = (storyctl_dir.agent_dir / "events.jsonl").read_text()
    events = [json.loads(line) for line in log.splitlines() if line.strip()]
    blocked = [e for e in events if e.get("event") == "blocked"]
    assert len(blocked) == 1
    assert blocked[0]["action"] == "issue-comment"
    assert blocked[0]["reason"] == "host classifier: External System Writes"


def test_notify_still_refuses_a_run_holding_no_grant(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Pins that this feature did not widen the gate it declined to reopen —
    `wfctl notify` on the same branch, with the same no-grant state, still
    exits 1 after `wfctl blocked` has run."""
    runner.invoke(app, ["blocked", "issue-comment", "--reason", "refused"])
    result = runner.invoke(app, ["notify", "push"])
    assert result.exit_code == 1


def test_no_spelling_of_blocked_records_a_success(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-009, stated as a property of the surface rather than as prose an
    agent has to have read: the command's own parameter set can only record a
    block or a clearing, so a success-shaped mode added later fails this test
    instead of shipping quietly."""
    import inspect

    from wfctl.cli import app as cli_app

    command = next(c for c in cli_app.registered_commands if c.name == "blocked")
    assert command.callback is not None
    params = inspect.signature(command.callback).parameters
    # The only spellings this command's own signature admits: an action, a
    # reason (the failure it witnessed) and a --clear flag (a person releasing
    # it). Nothing shaped like a --succeeded or a bare positive mode.
    assert set(params) == {"action", "reason", "clear"}


def test_a_block_with_no_reason_is_refused_and_stores_nothing(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-007. A block with no reason would hold a step and say nothing about
    why — refused before anything is written."""
    result = runner.invoke(app, ["blocked", "issue-comment"])
    assert result.exit_code == 1
    events = storyctl_dir.agent_dir / "events.jsonl"
    assert not events.exists() or "blocked" not in events.read_text()


def test_both_reason_and_clear_are_refused_together(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The two modes are opposites — a report and a release — and passing both
    names neither."""
    result = runner.invoke(
        app, ["blocked", "issue-comment", "--reason", "refused", "--clear"]
    )
    assert result.exit_code == 1


def test_the_step_comes_from_inference_not_from_the_caller(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-010. The agent supplies only the two facts it alone witnessed —
    `action` and `reason` — and never gets to name which step is held; the
    command has no parameter for it."""
    import inspect

    from wfctl.cli import app as cli_app

    command = next(c for c in cli_app.registered_commands if c.name == "blocked")
    assert command.callback is not None
    assert "step" not in inspect.signature(command.callback).parameters


def test_a_branch_with_no_feature_still_stores_the_report(
    storyctl_dir: types.SimpleNamespace, monkeypatch,
) -> None:
    """FR-008. A trunk branch, or any branch resolving to no feature
    directory. The report is stored anyway — the fact is about the run, not
    about the pipeline — and the response says plainly that nothing is held."""
    import subprocess

    trunk = subprocess.run(
        ["git", "-C", str(storyctl_dir.repo_root), "branch", "--show-current"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    monkeypatch.setenv("WFCTL_BRANCH", trunk)

    result = runner.invoke(app, ["blocked", "push", "--reason", "refused on trunk"])
    assert result.exit_code == 0, result.output
    assert "no step is being held" in result.output

    log = json.loads(
        "[" + ",".join(
            line for line in (storyctl_dir.agent_dir / "events.jsonl").read_text().splitlines()
            if line.strip()
        ) + "]"
    )
    blocked = [e for e in log if e.get("event") == "blocked"]
    assert len(blocked) == 1
    assert blocked[0]["step"] is None


def test_a_block_filed_once_the_pipeline_reads_complete_still_holds_the_last_step(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A block after every step is `done` used to read as `step: null` —
    indistinguishable from the no-feature-branch case above — because
    `build_report.current` is `None` for both "no feature claims this branch"
    and "nothing is left to run". `end-session/SKILL.md`'s own worked example
    is `wfctl blocked issue-close` run after implementation and verification
    both finish, which is exactly this state. It has to hold the pipeline's
    last step, or the promised "the next session reads it as unfinished"
    never happens."""
    storyctl_dir.stage_upstream_of("tasks")
    assert _payload()["current"] is None

    result = runner.invoke(app, ["blocked", "issue-close", "--reason", "host refused"])
    assert result.exit_code == 0, result.output
    assert "no step is being held" not in result.output
    assert "holding `implement`" in result.output

    held = next(s for s in _payload()["steps"] if s["name"] == "implement")
    assert held["state"] == "in_progress"
    assert held["reason"] == "host refused"


def test_clearing_works_for_a_run_holding_no_grant(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-013. The path `notify-action` cannot reach — this branch never had
    `wfctl start --allow-notify` run on it, and `--clear` still releases."""
    runner.invoke(app, ["blocked", "issue-comment", "--reason", "refused"])
    result = runner.invoke(app, ["blocked", "issue-comment", "--clear"])
    assert result.exit_code == 0, result.output

    log = (storyctl_dir.agent_dir / "events.jsonl").read_text()
    events = [json.loads(line) for line in log.splitlines() if line.strip()]
    cleared = [e for e in events if e.get("event") == "block-cleared"]
    assert len(cleared) == 1
    assert cleared[0]["action"] == "issue-comment"


def test_clearing_an_action_with_no_block_standing_says_so(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-014. Changes nothing and says there was nothing to clear — a person
    who mistypes the action otherwise reads a clean exit as a release that did
    not happen."""
    result = runner.invoke(app, ["blocked", "issue-comment", "--clear"])
    assert result.exit_code == 0
    assert "nothing to clear" in result.output

    events = storyctl_dir.agent_dir / "events.jsonl"
    assert not events.exists() or "block-cleared" not in events.read_text()
