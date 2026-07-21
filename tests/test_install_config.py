"""Tests for `wfctl install-config` — seed standardized repo config."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()

_WORKMUX_YAML = "worktree_dir: wt\nagent: claude\n"


def _make_wf_skills_repo_with_config(base: Path) -> Path:
    src = base / "wf-skills-cfg"
    src.mkdir()
    subprocess.run(["git", "init", str(src)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "config", "user.email", "t@t.com"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "config", "user.name", "T"], check=True, capture_output=True)
    cfg = src / ".agents" / "configs" / "workmux"
    cfg.mkdir(parents=True)
    (cfg / ".workmux.yaml").write_text(_WORKMUX_YAML)
    subprocess.run(["git", "-C", str(src), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "commit", "-m", "init"], check=True, capture_output=True)
    return src


def _install(src: Path, *extra: str):
    return runner.invoke(
        app, ["install-config", "workmux", "--repo", f"file://{src}", "--ref", "master", *extra]
    )


def test_seed_writes_workmux_and_gitignores_wt(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    result = _install(_make_wf_skills_repo_with_config(tmp_path))
    assert result.exit_code == 0
    assert "worktree_dir: wt" in (repo_root / ".workmux.yaml").read_text()
    assert "wt/" in (repo_root / ".gitignore").read_text().splitlines()  # created (absent before)


def test_gitignore_appended_when_line_missing(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".gitignore").write_text("*.log\n")
    _install(_make_wf_skills_repo_with_config(tmp_path))
    lines = (repo_root / ".gitignore").read_text().splitlines()
    assert "*.log" in lines and "wt/" in lines


def test_gitignore_no_duplicate_when_present(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".gitignore").write_text("wt/\n")
    _install(_make_wf_skills_repo_with_config(tmp_path))
    assert (repo_root / ".gitignore").read_text().splitlines().count("wt/") == 1


def test_refuses_existing_without_force(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".workmux.yaml").write_text("mine: true\n")
    result = _install(_make_wf_skills_repo_with_config(tmp_path))
    assert result.exit_code != 0
    assert ".workmux.yaml" in result.output
    assert (repo_root / ".workmux.yaml").read_text() == "mine: true\n"  # untouched


def test_force_overwrites(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".workmux.yaml").write_text("mine: true\n")
    result = _install(_make_wf_skills_repo_with_config(tmp_path), "--force")
    assert result.exit_code == 0
    assert "worktree_dir: wt" in (repo_root / ".workmux.yaml").read_text()


def test_unknown_config_name(agent_dir: Path) -> None:
    result = runner.invoke(app, ["install-config", "nope"])
    assert result.exit_code != 0
    assert "workmux" in result.output


def test_not_a_git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WFCTL_REPO_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)  # a fresh, non-git directory
    result = runner.invoke(app, ["install-config", "workmux"])
    assert result.exit_code != 0


def test_agent_flag_substituted(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    _install(_make_wf_skills_repo_with_config(tmp_path), "--agent", "bob")
    text = (repo_root / ".workmux.yaml").read_text()
    assert "agent: bob" in text
    assert "agent: claude" not in text


def test_agent_defaults_from_manifest(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".wf-skills-manifest.json").write_text(json.dumps({"bob": {"items": []}}))
    _install(_make_wf_skills_repo_with_config(tmp_path))
    assert "agent: bob" in (repo_root / ".workmux.yaml").read_text()
