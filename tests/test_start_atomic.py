"""Tests for wfctl start — atomicity, idempotency, step inference."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def _make_spec(spec_dir: Path, *steps: str) -> None:
    """Create spec artifacts for the given steps."""
    artifact_map = {
        "brainstorm": spec_dir.parent / ".agent" / "spec.md",
        "specify":    spec_dir / "spec.md",
        "plan":       spec_dir / "plan.md",
        "tasks":      spec_dir / "tasks.md",
        "analyze":    spec_dir / "checklists" / "analysis-report.md",
        "decompose":  spec_dir / "delivery.md",
    }
    for step in steps:
        p = artifact_map[step]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# {step}\n")


def test_start_writes_current_files(storyctl_dir) -> None:
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 0
    assert (storyctl_dir.agent_dir / "current.json").exists()
    assert (storyctl_dir.agent_dir / "current.md").exists()


def test_start_workflow_step_not_start_placeholder(storyctl_dir) -> None:
    """workflow_step must be inferred from artifacts — never the literal 'start'."""
    _make_spec(storyctl_dir.spec_dir, "brainstorm", "specify", "plan")
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 0
    data = json.loads((storyctl_dir.agent_dir / "current.json").read_text())
    assert data["workflow_step"] != "start"
    assert data["workflow_step"] in ["tasks", "analyze", "decompose", "implement", "brainstorm",
                                      "specify", "clarify", "plan", "complete"]


def test_start_infers_tasks_when_plan_done(storyctl_dir) -> None:
    _make_spec(storyctl_dir.spec_dir, "brainstorm", "specify", "plan")
    runner.invoke(app, ["start"])
    data = json.loads((storyctl_dir.agent_dir / "current.json").read_text())
    assert data["workflow_step"] == "tasks"


def test_start_idempotent_no_overwrite(storyctl_dir) -> None:
    runner.invoke(app, ["start"])
    first_json = (storyctl_dir.agent_dir / "current.json").read_text()
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 0
    assert "Already initialized" in result.output
    assert (storyctl_dir.agent_dir / "current.json").read_text() == first_json


def test_start_force_overwrites(storyctl_dir) -> None:
    runner.invoke(app, ["start"])
    _make_spec(storyctl_dir.spec_dir, "brainstorm", "specify", "plan")
    result = runner.invoke(app, ["start", "--force"])
    assert result.exit_code == 0
    data = json.loads((storyctl_dir.agent_dir / "current.json").read_text())
    assert data["workflow_step"] == "tasks"


def test_start_corrupted_json_exits_1_with_message(storyctl_dir) -> None:
    (storyctl_dir.agent_dir / "current.json").write_text("{invalid")
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 1
    assert "current.json" in result.output
    # No Python traceback in output
    assert "Traceback" not in result.output


def test_start_appends_event(storyctl_dir) -> None:
    runner.invoke(app, ["start"])
    events_file = storyctl_dir.agent_dir / "events.jsonl"
    assert events_file.exists()
    record = json.loads(events_file.read_text().splitlines()[0])
    assert record["event"] == "start"


def test_start_current_md_has_step_field(storyctl_dir) -> None:
    _make_spec(storyctl_dir.spec_dir, "brainstorm", "specify", "plan")
    runner.invoke(app, ["start"])
    md = (storyctl_dir.agent_dir / "current.md").read_text()
    assert "**Step**:" in md
    assert "tasks" in md
