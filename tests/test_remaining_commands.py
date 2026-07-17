"""Tests for wfctl resume, end, and checkpoint commands (Phase 7)."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def test_resume_appends_event(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["resume"])
    events = (agent_dir / "events.jsonl").read_text().splitlines()
    event_types = [json.loads(e)["event"] for e in events]
    assert "resume" in event_types


def test_resume_exits_zero(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    result = runner.invoke(app, ["resume"])
    assert result.exit_code == 0


def test_resume_not_initialized_exits_one(agent_dir: Path) -> None:
    result = runner.invoke(app, ["resume"])
    assert result.exit_code == 1


def test_resume_re_infers_step_from_filesystem(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    # Force stale step into current.json
    current_json = agent_dir / "current.json"
    data = json.loads(current_json.read_text())
    data["workflow_step"] = "implement"  # stale — no artifacts to back this up
    current_json.write_text(json.dumps(data))
    runner.invoke(app, ["resume"])
    fresh = json.loads(current_json.read_text())
    assert fresh["workflow_step"] != "implement"  # re-inferred from empty spec dir → brainstorm


def test_end_sets_status_complete(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["end"])
    data = json.loads((agent_dir / "current.json").read_text())
    assert data["status"] == "complete"


def test_end_writes_session_summary(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["end"])
    assert (agent_dir / "session-summary.md").exists()


def test_end_current_json_valid(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["end"])
    # Must be parseable — no corruption
    json.loads((agent_dir / "current.json").read_text())


def test_checkpoint_creates_patch(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    result = runner.invoke(app, ["checkpoint"])
    assert result.exit_code == 0
    assert (agent_dir / "checkpoint-1.patch").exists()


def test_checkpoint_creates_md(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["checkpoint"])
    assert (agent_dir / "checkpoint-1.md").exists()


def test_checkpoint_not_initialized_exits_one(agent_dir: Path) -> None:
    result = runner.invoke(app, ["checkpoint"])
    assert result.exit_code == 1


def test_log_shows_events(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["next"])
    result = runner.invoke(app, ["log"])
    assert result.exit_code == 0
    assert "start" in result.output
    assert "next" in result.output


def test_log_empty_before_start(agent_dir: Path) -> None:
    result = runner.invoke(app, ["log"])
    assert result.exit_code == 0
    assert "No events" in result.output


def test_checkpoint_increments(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["checkpoint"])
    runner.invoke(app, ["checkpoint"])
    assert (agent_dir / "checkpoint-2.patch").exists()


def test_state_dir_path_not_wrapped(agent_dir: Path, monkeypatch) -> None:
    """Output is consumed by $(wfctl state-dir); a wrapped path breaks callers."""
    monkeypatch.setenv("COLUMNS", "40")  # narrower than the path
    result = runner.invoke(app, ["state-dir"])
    assert result.exit_code == 0
    assert result.stdout.strip() == str(agent_dir)
    assert "\n" not in result.stdout.strip()
