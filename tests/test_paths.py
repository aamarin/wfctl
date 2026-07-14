"""Tests for wfctl._paths — path resolution."""
from __future__ import annotations

from pathlib import Path

import pytest

from wfctl._paths import resolve_agent_dir, resolve_branch, resolve_spec_dir


def test_resolve_branch_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WFCTL_BRANCH", "999-my-feature")
    assert resolve_branch(tmp_path) == "999-my-feature"


def test_resolve_branch_from_git(repo_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WFCTL_BRANCH", raising=False)
    import subprocess
    subprocess.run(["git", "-C", str(repo_root), "checkout", "-b", "422-test-branch"],
                   check=True, capture_output=True)
    result = resolve_branch(repo_root)
    assert result == "422-test-branch"


def test_resolve_spec_dir_finds_prefix_match(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    specs = tmp_path / "specs"
    target = specs / "422-foo-bar"
    target.mkdir(parents=True)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))
    result = resolve_spec_dir("422-something", tmp_path)
    assert result == target


def test_resolve_spec_dir_exact_match(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    specs = tmp_path / "specs"
    target = specs / "422-something"
    target.mkdir(parents=True)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))
    result = resolve_spec_dir("422-something", tmp_path)
    assert result == target


def test_resolve_spec_dir_returns_none_when_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))
    result = resolve_spec_dir("422-missing", tmp_path)
    assert result is None


def test_resolve_agent_dir_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    override = tmp_path / "custom-state"
    monkeypatch.setenv("WFCTL_STATE_DIR", str(override))
    result = resolve_agent_dir(tmp_path, "422-branch")
    assert result == override
    assert result.exists()


def test_resolve_agent_dir_creates_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    override = tmp_path / "nonexistent" / "deep" / "dir"
    monkeypatch.setenv("WFCTL_STATE_DIR", str(override))
    result = resolve_agent_dir(tmp_path, "422-branch")
    assert result.exists()


def test_resolve_agent_dir_xdg_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg"))
    repo = tmp_path / "myrepo"
    repo.mkdir()
    result = resolve_agent_dir(repo, "123-feature")
    assert result == tmp_path / "xdg" / "wfctl" / "repos" / "myrepo" / "stories" / "123-feature"
    assert result.exists()
