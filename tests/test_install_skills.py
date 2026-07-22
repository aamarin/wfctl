"""Tests for wfctl install-skills command."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


@pytest.fixture
def stub_version_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate the skills-drift tests from doctor's wfctl-tool version check
    (which does a real network ls-remote)."""
    monkeypatch.setattr("wfctl.cli._check_wfctl_version", lambda: 0)


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

    cmd = src / ".agents" / "commands"
    cmd.mkdir(parents=True)
    (cmd / "test-cmd.md").write_text("# test-cmd\n")

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
    cmd = src / ".agents" / "commands"
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


def test_uninstall_removes_freshly_installed_items(agent_dir: Path, tmp_path: Path) -> None:
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert (repo_root / ".agents" / "skills" / "test-skill").exists()

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert result.exit_code == 0
    assert not (repo_root / ".agents" / "skills" / "test-skill").exists()
    assert not (repo_root / ".claude" / "commands" / "test-cmd.md").exists()
    assert not (repo_root / ".wf-skills-manifest.json").exists()


def test_install_backs_up_and_uninstall_restores_pre_existing_file(agent_dir: Path, tmp_path: Path) -> None:
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    # A command of the same name already exists before wf-skills touches it.
    existing_cmd_dir = repo_root / ".claude" / "commands"
    existing_cmd_dir.mkdir(parents=True)
    (existing_cmd_dir / "test-cmd.md").write_text("# my own pre-existing command\n")

    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--yes"]
    )
    assert result.exit_code == 0
    assert "Backed up 1" in result.output
    # Overwritten with wf-skills' version after install.
    assert (existing_cmd_dir / "test-cmd.md").read_text() == "# test-cmd\n"

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert result.exit_code == 0
    assert "restored 1" in result.output
    # Original content is back, not just deleted.
    assert (existing_cmd_dir / "test-cmd.md").read_text() == "# my own pre-existing command\n"
    assert not (repo_root / ".wf-skills-backup").exists()


def test_uninstall_with_nothing_installed_is_a_noop(agent_dir: Path) -> None:
    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert result.exit_code == 0
    assert "Nothing installed" in result.output


def test_reinstall_does_not_re_backup_already_tracked_item(agent_dir: Path, tmp_path: Path) -> None:
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    existing_cmd_dir = repo_root / ".claude" / "commands"
    existing_cmd_dir.mkdir(parents=True)
    (existing_cmd_dir / "test-cmd.md").write_text("# my own pre-existing command\n")

    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--yes"])
    # Second install of the same item should not report a fresh backup.
    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--yes"]
    )
    assert "Backed up" not in result.output

    # The original pre-existing content must still be recoverable.
    runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert (existing_cmd_dir / "test-cmd.md").read_text() == "# my own pre-existing command\n"


def test_install_prompts_before_overwriting_and_declining_aborts(
    agent_dir: Path, tmp_path: Path
) -> None:
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    existing_cmd_dir = repo_root / ".claude" / "commands"
    existing_cmd_dir.mkdir(parents=True)
    (existing_cmd_dir / "test-cmd.md").write_text("# my own pre-existing command\n")

    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"], input="n\n"
    )
    assert result.exit_code != 0
    assert "test-cmd.md" in result.output
    # Declined — nothing touched, no manifest written.
    assert (existing_cmd_dir / "test-cmd.md").read_text() == "# my own pre-existing command\n"
    assert not (repo_root / ".wf-skills-manifest.json").exists()


def test_install_prompts_before_overwriting_and_confirming_proceeds(
    agent_dir: Path, tmp_path: Path
) -> None:
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    existing_cmd_dir = repo_root / ".claude" / "commands"
    existing_cmd_dir.mkdir(parents=True)
    (existing_cmd_dir / "test-cmd.md").write_text("# my own pre-existing command\n")

    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"], input="y\n"
    )
    assert result.exit_code == 0
    assert (existing_cmd_dir / "test-cmd.md").read_text() == "# test-cmd\n"


def test_install_no_prompt_when_nothing_would_be_overwritten(
    agent_dir: Path, tmp_path: Path
) -> None:
    src = _make_wf_skills_repo(tmp_path)
    # No --yes, no input supplied — would hang/fail on an unexpected prompt.
    result = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert result.exit_code == 0


def test_install_pins_resolved_commit(agent_dir: Path, tmp_path: Path) -> None:
    """The manifest records the clone's resolved HEAD, not just the --ref name."""
    import json
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    head = subprocess.run(
        ["git", "-C", str(src), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    assert manifest["claude"]["commit"] == head


def test_doctor_reports_up_to_date(agent_dir: Path, tmp_path: Path, stub_version_check: None) -> None:
    """A fresh install's pinned commit matches upstream's tip — nothing to flag."""
    src = _make_wf_skills_repo(tmp_path)
    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "up to date" in result.output


def test_doctor_reports_behind_with_diff(agent_dir: Path, tmp_path: Path, stub_version_check: None) -> None:
    """When upstream moves past the pinned commit, doctor exits 1 and shows what changed."""
    src = _make_wf_skills_repo(tmp_path)
    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])

    # Upstream moves on after the install.
    (src / ".agents" / "skills" / "test-skill" / "SKILL.md").write_text("# test-skill v2\n")
    subprocess.run(["git", "-C", str(src), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "commit", "-m", "update skill"], check=True, capture_output=True)

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "behind" in result.output
    assert "SKILL.md" in result.output
    assert "install-skills" in result.output  # the update hint


def test_doctor_with_nothing_installed(agent_dir: Path, stub_version_check: None) -> None:
    """No manifest yet — doctor reports that plainly instead of erroring."""
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Nothing installed" in result.output


def test_doctor_warns_when_no_commit_pinned(agent_dir: Path, tmp_path: Path, stub_version_check: None) -> None:
    """A manifest from before commit-pinning existed is skipped with a warning, not a crash."""
    import json
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])

    manifest_path = repo_root / ".wf-skills-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    del manifest["claude"]["commit"]
    manifest_path.write_text(json.dumps(manifest))

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "no pinned commit" in result.output


# --- wfctl tool version check (doctor's first line) ---

def _fake_ls_remote_tags(*tags: str):
    """A subprocess.run stand-in that returns the given tags as `git ls-remote --tags` output."""
    def run(argv, **kwargs):
        if "ls-remote" in argv:
            out = "".join(f"{'0'*40}\trefs/tags/{t}\n" for t in tags)
            return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
    return run


def _plain(s: str) -> str:
    """Strip ANSI so assertions don't break on rich's number highlighting."""
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def test_check_wfctl_version_upgrade_available(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    import importlib.metadata
    from wfctl.cli import _check_wfctl_version
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "0.9.0")
    monkeypatch.setattr(subprocess, "run", _fake_ls_remote_tags("v0.9.0", "v0.10.0"))
    rc = _check_wfctl_version()
    assert rc == 1
    assert "0.10.0 available" in _plain(capsys.readouterr().out)


def test_check_wfctl_version_latest(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    import importlib.metadata
    from wfctl.cli import _check_wfctl_version
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "0.10.0")
    monkeypatch.setattr(subprocess, "run", _fake_ls_remote_tags("v0.9.0", "v0.10.0"))
    rc = _check_wfctl_version()
    assert rc == 0
    assert "latest" in _plain(capsys.readouterr().out)
