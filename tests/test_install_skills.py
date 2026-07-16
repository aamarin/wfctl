"""Tests for wfctl install-skills command."""
from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def _make_wf_skills_repo(base: Path) -> Path:
    """Create a minimal wf-skills git repo for testing."""
    src = base / "wf-skills-src"
    src.mkdir()
    subprocess.run(["git", "init", str(src)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "config", "user.email", "t@t.com"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "config", "user.name", "T"], check=True, capture_output=True)

    skill = src / ".agents" / "skills" / "test-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# test-skill\n")

    cmd = src / ".claude" / "commands"
    cmd.mkdir(parents=True)
    (cmd / "test-cmd.md").write_text("# test-cmd\n")

    bob_cmd = src / ".bob" / "commands"
    bob_cmd.mkdir(parents=True)
    (bob_cmd / "test-cmd.md").write_text("# test-cmd\n")

    subprocess.run(["git", "-C", str(src), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "commit", "-m", "init"], check=True, capture_output=True)
    return src


def test_install_skills_copies_skills(agent_dir: Path, tmp_path: Path) -> None:
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = os.environ["WFCTL_REPO_ROOT"]
    result = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert result.exit_code == 0
    assert (Path(repo_root) / ".agents" / "skills" / "test-skill" / "SKILL.md").exists()


def test_install_skills_copies_commands(agent_dir: Path, tmp_path: Path) -> None:
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = os.environ["WFCTL_REPO_ROOT"]
    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert (Path(repo_root) / ".claude" / "commands" / "test-cmd.md").exists()


def test_install_skills_bad_repo_exits_one(agent_dir: Path) -> None:
    result = runner.invoke(app, ["install-skills", "--repo", "https://github.com/no/such-repo-xyz"])
    assert result.exit_code == 1


def test_install_skills_reports_count(agent_dir: Path, tmp_path: Path) -> None:
    src = _make_wf_skills_repo(tmp_path)
    result = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert "Installed 2" in result.output


def test_install_skills_bob_writes_skills_to_bob_dir(agent_dir: Path, tmp_path: Path) -> None:
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "bob"]
    )
    assert result.exit_code == 0
    assert (repo_root / ".bob" / "skills" / "test-skill" / "SKILL.md").exists()
    assert (repo_root / ".bob" / "commands" / "test-cmd.md").exists()
    assert not (repo_root / ".claude").exists()


def test_install_skills_unknown_agent_exits_one(agent_dir: Path, tmp_path: Path) -> None:
    src = _make_wf_skills_repo(tmp_path)
    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "nope"]
    )
    assert result.exit_code == 1


def test_install_skills_warns_on_missing_source_path(agent_dir: Path, tmp_path: Path) -> None:
    """If wf-skills is missing a path an agent expects, warn instead of skipping silently."""
    src = tmp_path / "wf-skills-src"
    src.mkdir()
    subprocess.run(["git", "init", str(src)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "config", "user.email", "t@t.com"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "config", "user.name", "T"], check=True, capture_output=True)
    cmd = src / ".claude" / "commands"
    cmd.mkdir(parents=True)
    (cmd / "test-cmd.md").write_text("# test-cmd\n")
    subprocess.run(["git", "-C", str(src), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "commit", "-m", "init"], check=True, capture_output=True)

    # Bob's target is .agents/skills, which this repo doesn't have.
    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "bob"]
    )
    assert result.exit_code == 0
    assert "not found" in result.output
    assert ".agents/skills" in result.output
