"""Tests for `wfctl feature-paths` — the speckit runtime's path source of truth."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def _configure_tracker(repo_root: Path, name: str, config: dict) -> None:
    tdir = repo_root / ".agents" / "trackers"
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / f"{name}.json").write_text(json.dumps(config))
    (repo_root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": name}))


def test_feature_paths_honors_tracker_key_pattern(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The regression guard: a non-numeric tracker key resolves its spec dir.

    Upstream spec-kit's `^[0-9]{1,7}-` would reject `PROJ-123-auth`; wfctl's
    key_pattern must win.
    """
    repo_root = agent_dir.parent
    _configure_tracker(repo_root, "jira", {"key_pattern": r"PROJ-\d+", "verbs": {}})
    (repo_root / "specs" / "PROJ-123-auth").mkdir(parents=True)
    monkeypatch.setenv("WFCTL_BRANCH", "PROJ-123-auth")
    result = runner.invoke(app, ["feature-paths"])
    assert result.exit_code == 0
    assert f"FEATURE_DIR='{repo_root}/specs/PROJ-123-auth'" in result.output
    assert f"IMPL_PLAN='{repo_root}/specs/PROJ-123-auth/plan.md'" in result.output


def test_feature_paths_numeric_prefix_match(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Default numeric key: a branch resolves to its `specs/<key>-*` dir by prefix."""
    repo_root = agent_dir.parent
    (repo_root / "specs" / "342-foo").mkdir(parents=True)
    monkeypatch.setenv("WFCTL_BRANCH", "342-bar")  # same key, different slug
    result = runner.invoke(app, ["feature-paths"])
    assert result.exit_code == 0
    assert f"FEATURE_DIR='{repo_root}/specs/342-foo'" in result.output


def test_feature_paths_exact_branch_match(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-key branch resolves via exact `specs/<branch>` match."""
    repo_root = agent_dir.parent
    (repo_root / "specs" / "install-specify-runtime").mkdir(parents=True)
    monkeypatch.setenv("WFCTL_BRANCH", "install-specify-runtime")
    result = runner.invoke(app, ["feature-paths"])
    assert result.exit_code == 0
    assert f"FEATURE_DIR='{repo_root}/specs/install-specify-runtime'" in result.output


def test_feature_paths_fallback_when_no_spec_dir(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No spec folder yet → the conventional `specs/<branch>` path is emitted."""
    repo_root = agent_dir.parent
    monkeypatch.setenv("WFCTL_BRANCH", "999-nothing")
    result = runner.invoke(app, ["feature-paths"])
    assert result.exit_code == 0
    assert f"FEATURE_DIR='{repo_root}/specs/999-nothing'" in result.output
    # A complete, eval-able payload.
    for var in ("REPO_ROOT", "CURRENT_BRANCH", "HAS_GIT", "FEATURE_SPEC", "TASKS"):
        assert f"{var}='" in result.output
