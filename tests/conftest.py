from __future__ import annotations

import os
import subprocess
import types
from pathlib import Path

import pytest

# Set before any wfctl import: `wfctl.cli` builds its `Console()` at module
# scope, and rich resolves the color system there — a fixture would run too
# late. Without this, rich emits ANSI whenever the terminal supports color, so
# `[green]✓[/green] Installed` arrives as `\x1b[32m✓\x1b[0m Installed` and
# assertions like `line.startswith("✓ Installed")` fail locally while passing in
# CI, which has no terminal. Tests must not depend on where they run.
os.environ["NO_COLOR"] = "1"


@pytest.fixture
def agent_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated state dir backed by a real git repo (checkpoint needs git diff)."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@test.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test"],
        check=True, capture_output=True,
    )
    (tmp_path / "README.md").write_text("test\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "README.md"], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "init"],
        check=True, capture_output=True,
    )
    d = tmp_path / ".agent"
    d.mkdir()
    monkeypatch.setenv("WFCTL_STATE_DIR", str(d))
    monkeypatch.setenv("WFCTL_BRANCH", "342-state-workflow")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(tmp_path))
    return d


_STEP_ARTIFACTS: dict[str, object] = {
    "brainstorm": lambda root, spec: root / ".agent" / "spec.md",
    "specify":    lambda root, spec: spec / "spec.md",
    "clarify":    lambda root, spec: spec / "spec.md",
    "plan":       lambda root, spec: spec / "plan.md",
    "tasks":      lambda root, spec: spec / "tasks.md",
    "analyze":    lambda root, spec: spec / "checklists" / "analysis-report.md",
    "decompose":  lambda root, spec: spec / "delivery.md",
    "implement":  lambda root, spec: spec / "tasks.md",
}


@pytest.fixture
def storyctl_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> types.SimpleNamespace:
    """Isolated fixture: git repo + specs layout + env overrides."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@test.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test"],
        check=True, capture_output=True,
    )
    (tmp_path / "README.md").write_text("test\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "README.md"], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "init"],
        check=True, capture_output=True,
    )

    agent_dir = tmp_path / ".agent-runs"
    agent_dir.mkdir()
    spec_dir = tmp_path / "specs" / "418-storyctl"
    spec_dir.mkdir(parents=True)

    monkeypatch.setenv("WFCTL_STATE_DIR", str(agent_dir))
    monkeypatch.setenv("WFCTL_BRANCH", "418-storyctl")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(tmp_path / "specs"))
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(tmp_path))

    def make_spec_artifact(step: str, content: str = "x") -> Path:
        artifact: Path = _STEP_ARTIFACTS[step](tmp_path, spec_dir)  # type: ignore[operator]
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(content)
        return artifact

    return types.SimpleNamespace(
        agent_dir=agent_dir,
        spec_dir=spec_dir,
        repo_root=tmp_path,
        make_spec_artifact=make_spec_artifact,
    )


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """Minimal initialized git repo for tests needing real repo root resolution."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@test.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test"],
        check=True, capture_output=True,
    )
    return tmp_path
