"""Tests for wfctl session commands (migrated from pfms scripts/tests/test_agent_session.py)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


# ─── Session start ────────────────────────────────────────────────────────────

def test_init_seeds_from_branch(agent_dir: Path) -> None:
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 0
    assert (agent_dir / "current.json").exists()
    assert (agent_dir / "current.md").exists()
    data = json.loads((agent_dir / "current.json").read_text())
    assert data["issue"] == "342"
    assert data["status"] == "in_progress"
    # workflow_step must never be the "start" placeholder
    assert data["workflow_step"] != "start"


@pytest.mark.parametrize(
    "branch,expected",
    [
        ("342-state-workflow", "342"),
        ("419_auth_lifecycle_update", "419"),
        ("dev", "unknown"),
        ("no-number-here", "unknown"),
    ],
)
def test_init_seeds_issue_from_either_separator(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, branch: str, expected: str
) -> None:
    monkeypatch.setenv("WFCTL_BRANCH", branch)
    result = runner.invoke(app, ["start", "--force"])
    assert result.exit_code == 0
    data = json.loads((agent_dir / "current.json").read_text())
    assert data["issue"] == expected


def test_init_idempotent(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    content_json = (agent_dir / "current.json").read_text()
    content_md = (agent_dir / "current.md").read_text()
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 0
    assert "Already initialized" in result.output
    assert (agent_dir / "current.json").read_text() == content_json
    assert (agent_dir / "current.md").read_text() == content_md


def test_init_no_git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    monkeypatch.delenv("WFCTL_BRANCH", raising=False)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 1
    assert "git" in result.output.lower()


def test_init_current_md_word_count(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    text = (agent_dir / "current.md").read_text()
    assert len(text.split()) <= 1000


# ─── Checkpoint & End ────────────────────────────────────────────────────────


def test_end_writes_summary(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    result = runner.invoke(app, ["end"])
    assert result.exit_code == 0
    assert (agent_dir / "session-summary.md").exists()
    data = json.loads((agent_dir / "current.json").read_text())
    assert data["status"] == "complete"


def test_end_idempotent_summary(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["end"])
    original = (agent_dir / "session-summary.md").read_text()
    runner.invoke(app, ["end"])
    assert (agent_dir / "session-summary.md").read_text() == original
