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


def test_checkpoint_increments(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["checkpoint"])
    runner.invoke(app, ["checkpoint"])
    assert (agent_dir / "checkpoint-2.patch").exists()
