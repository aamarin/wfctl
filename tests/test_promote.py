"""Tests for wfctl promote command (US4 — memory promotion before PR)."""
from __future__ import annotations

import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()

CANDIDATE_A = """\
### Fix commit granularity
**Type:** feedback
**Rationale:** Amend trivial fixes into preceding commit.
"""

CANDIDATE_B = """\
### Use jq for JSON in bash
**Type:** feedback
**Rationale:** Never python3 -c for JSON processing.
"""


@pytest.fixture
def promote_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> types.SimpleNamespace:
    """Isolated state dir with WFCTL_CANDIDATES_FILE pointing to a tmp file."""
    agent_dir = tmp_path / ".agent-runs"
    agent_dir.mkdir()
    candidates_file = tmp_path / "candidates.md"

    monkeypatch.setenv("WFCTL_STATE_DIR", str(agent_dir))
    monkeypatch.setenv("WFCTL_BRANCH", "422-extract-python-tools")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(tmp_path))
    monkeypatch.setenv("WFCTL_CANDIDATES_FILE", str(candidates_file))

    return types.SimpleNamespace(
        agent_dir=agent_dir,
        candidates_file=candidates_file,
    )


# ─── empty / missing candidates ──────────────────────────────────────────────

def test_promote_empty_file_exits_zero(promote_dir: types.SimpleNamespace) -> None:
    promote_dir.candidates_file.write_text("")
    result = runner.invoke(app, ["promote"])
    assert result.exit_code == 0
    assert "No candidates" in result.output


def test_promote_missing_file_exits_zero(promote_dir: types.SimpleNamespace) -> None:
    result = runner.invoke(app, ["promote"])
    assert result.exit_code == 0
    assert "No candidates" in result.output


# ─── approve path ────────────────────────────────────────────────────────────

def test_approve_writes_to_promoted_file(promote_dir: types.SimpleNamespace) -> None:
    promote_dir.candidates_file.write_text(CANDIDATE_A)
    runner.invoke(app, ["promote"], input="a\n")
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    promoted = promote_dir.agent_dir / "promoted" / f"{today}.md"
    assert promoted.exists()
    assert "Fix commit granularity" in promoted.read_text()


def test_approve_removes_entry_from_candidates(promote_dir: types.SimpleNamespace) -> None:
    promote_dir.candidates_file.write_text(CANDIDATE_A)
    runner.invoke(app, ["promote"], input="a\n")
    assert "Fix commit granularity" not in promote_dir.candidates_file.read_text()


def test_approve_first_skip_second(promote_dir: types.SimpleNamespace) -> None:
    promote_dir.candidates_file.write_text(CANDIDATE_A + "\n" + CANDIDATE_B)
    runner.invoke(app, ["promote"], input="a\ns\n")
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    promoted = promote_dir.agent_dir / "promoted" / f"{today}.md"
    assert "Fix commit granularity" in promoted.read_text()
    remaining = promote_dir.candidates_file.read_text()
    assert "Use jq for JSON" in remaining
    assert "Fix commit granularity" not in remaining


# ─── skip path ───────────────────────────────────────────────────────────────

def test_skip_keeps_entry_in_candidates(promote_dir: types.SimpleNamespace) -> None:
    promote_dir.candidates_file.write_text(CANDIDATE_A)
    runner.invoke(app, ["promote"], input="s\n")
    assert "Fix commit granularity" in promote_dir.candidates_file.read_text()


def test_skip_does_not_create_promoted_file(promote_dir: types.SimpleNamespace) -> None:
    promote_dir.candidates_file.write_text(CANDIDATE_A)
    runner.invoke(app, ["promote"], input="s\n")
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    promoted = promote_dir.agent_dir / "promoted" / f"{today}.md"
    assert not promoted.exists()
