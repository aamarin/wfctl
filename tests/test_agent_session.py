"""The session commands, after the resume point stopped being a file.

`wfctl start` used to write `current.json` and `current.md`, and every later
read answered from them. Both were written once and never again, so a session
that ran a pipeline step and came back was told where it had been, not where it
was (#42). These assert the shape that replaced them: nothing is written but the
event log and the handoff prose, and every other value is computed when asked.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import CLEAN_SPEC
from wfctl.cli import app

runner = CliRunner()


def _run(*args: str) -> str:
    result = runner.invoke(app, list(args))
    assert result.exit_code == 0, result.output
    return result.output


# ─── Nothing is written that could go stale ──────────────────────────────────

def test_start_writes_no_resume_point(agent_dir: Path) -> None:
    """The two files whose staleness is #42. Neither is written by anything now."""
    _run("start")
    assert not (agent_dir / "current.json").exists()
    assert not (agent_dir / "current.md").exists()


def test_no_command_recreates_the_files_it_no_longer_reads(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Walks the session commands, not just `start`.

    A single write left anywhere in the lifecycle brings the stale resume point
    back, and it would be invisible to a test that only ran the first command.
    """
    for args in (["start"], ["status"], ["next"], ["resume"], ["end"]):
        runner.invoke(app, args)
        for name in ("current.json", "current.md"):
            assert not (storyctl_dir.agent_dir / name).exists(), f"{name} after {args}"


# ─── The position is computed on every read ──────────────────────────────────

def test_the_position_follows_the_artifacts_with_no_command_in_between(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """#42 stated as a test: the artifacts move, nothing is run, the answer moves.

    Under the old shape `status` reported the step written at `wfctl start`, so
    an agent that ran `/speckit.brainstorm` and asked again was sent to
    brainstorm a second time.
    """
    _run("start")
    assert "brainstorm   ○  ← current" in _run("status")

    storyctl_dir.make_spec_artifact("brainstorm")

    assert "brainstorm   ●" in _run("status")
    assert "specify      ○  ← current" in _run("status")


def test_switching_branch_is_reflected_without_a_command_in_between(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The branch was seeded into `current.json` at start and never re-read.

    A worktree switched underneath a live session kept answering about the branch
    it opened on.
    """
    _run("start")
    assert "#418  418-storyctl" in _run("status")

    monkeypatch.setenv("WFCTL_BRANCH", "999-somewhere-else")

    assert "#999  999-somewhere-else" in _run("status")


# ─── Every field the deleted file carried is still answered (FR-011) ─────────

def test_each_field_the_session_file_carried_is_still_answered(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Named field by field, because a field can vanish without a line changing.

    `current.json` held issue, branch, repo, workflow_step, next_command,
    updated and status. Deleting the file is only safe if each is reachable from
    somewhere else, and a rendered-output test cannot show that — it asserts the
    lines it knows about and is silent on the field nobody printed.

    `status` is the exception and is deliberately not here: it had no reader at
    all, and work status is the pipeline.
    """
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    _run("start")

    status = _run("status")
    assert "#418" in status                    # issue — extract_issue_key, on every read
    assert "418-storyctl" in status            # branch — resolve_branch, on every read
    assert "plan         ○  ← current" in status   # workflow_step — _infer_steps
    assert "next: /speckit.plan" in status     # next_command — next_step_content

    # repo — resolved from git, and what the state dir is keyed by
    assert storyctl_dir.agent_dir.exists()

    # updated — the last event's timestamp, recorded as it happens rather than
    # rewritten to stay true
    last = json.loads((storyctl_dir.agent_dir / "events.jsonl").read_text().splitlines()[-1])
    assert last["ts"]


# ─── start ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "branch,expected",
    [
        ("342-state-workflow", "342"),
        ("419_auth_lifecycle_update", "419"),
        ("dev", "unknown"),
        ("no-number-here", "unknown"),
    ],
)
def test_the_issue_key_is_read_off_the_branch_on_every_read(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, branch: str, expected: str
) -> None:
    monkeypatch.setenv("WFCTL_BRANCH", branch)
    assert f"#{expected}" in _run("status")


def test_start_infers_the_step_rather_than_naming_a_placeholder(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """It must never report the literal 'start' — that is a placeholder, not a position."""
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    storyctl_dir.make_spec_artifact("plan")

    output = _run("start")

    assert "step: tasks" in output
    assert "next: /speckit.tasks" in output


def test_start_appends_the_event_that_is_now_the_session(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The one fact re-derivation cannot reach, so it is the one thing recorded."""
    _run("start")
    first = json.loads(
        (storyctl_dir.agent_dir / "events.jsonl").read_text().splitlines()[0]
    )
    assert first["event"] == "start"


def test_start_is_idempotent(storyctl_dir: types.SimpleNamespace) -> None:
    _run("start")
    events_before = (storyctl_dir.agent_dir / "events.jsonl").read_text()

    assert "Already initialized" in _run("start")
    assert (storyctl_dir.agent_dir / "events.jsonl").read_text() == events_before


def test_start_force_opens_a_session_over_an_existing_one(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    _run("start")
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    storyctl_dir.make_spec_artifact("plan")

    assert "step: tasks" in _run("start", "--force")


def test_start_outside_a_git_repo_exits_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    monkeypatch.delenv("WFCTL_BRANCH", raising=False)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 1
    assert "git" in result.output.lower()


# ─── resume and end refuse on the event log, not on a file ───────────────────

@pytest.mark.parametrize("command", ["resume", "end"])
def test_a_branch_with_no_start_event_has_no_session(
    agent_dir: Path, command: str
) -> None:
    result = runner.invoke(app, [command])
    assert result.exit_code == 1
    assert "No session found for this branch" in result.output


def test_end_writes_the_summary_once(agent_dir: Path) -> None:
    """Second `end` must not overwrite prose a human or agent filled in."""
    _run("start")
    _run("end")
    original = (agent_dir / "session-summary.md").read_text()

    _run("end")

    assert (agent_dir / "session-summary.md").read_text() == original
