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
    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"])
    assert (Path(repo_root) / ".claude" / "commands" / "test-cmd.md").exists()


def test_install_skills_gitignores_installed_paths(agent_dir: Path, tmp_path: Path) -> None:
    """Installed skill/command paths and the manifest/backup dir land in .gitignore,
    so a sync never dirties whatever branch happens to be checked out."""
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"])
    assert result.exit_code == 0
    gitignore = (repo_root / ".gitignore").read_text().splitlines()
    assert ".agents/skills/test-skill" in gitignore
    assert ".claude/commands/test-cmd.md" in gitignore
    assert ".wf-skills-manifest.json" in gitignore
    assert ".wf-skills-backup/" in gitignore


def test_install_skills_does_not_gitignore_tracker_config(agent_dir: Path, tmp_path: Path) -> None:
    """Tracker config is project-owned and meant to be committed, not managed
    as install-skills output — must not end up in .gitignore."""
    import os
    src = _make_wf_skills_repo(tmp_path)
    tracker_dir = src / ".agents" / "trackers"
    tracker_dir.mkdir(parents=True)
    (tracker_dir / "github.json").write_text("{}\n")
    subprocess.run(["git", "-C", str(src), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "commit", "-m", "tracker"], check=True, capture_output=True)

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--tracker", "github"]
    )
    assert result.exit_code == 0
    gitignore = (repo_root / ".gitignore").read_text() if (repo_root / ".gitignore").exists() else ""
    assert ".agents/trackers/github.json" not in gitignore.splitlines()


def _add_tracker(src: Path, body: str = '{"verbs": {}}\n') -> None:
    tracker_dir = src / ".agents" / "trackers"
    tracker_dir.mkdir(parents=True, exist_ok=True)
    (tracker_dir / "github.json").write_text(body)
    subprocess.run(["git", "-C", str(src), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "commit", "-m", "tracker"], check=True, capture_output=True)


def test_install_skills_no_tracker_without_a_human(agent_dir: Path, tmp_path: Path) -> None:
    """A non-interactive install never commits a tracker config nobody asked for."""
    import json
    import os
    src = _make_wf_skills_repo(tmp_path)
    _add_tracker(src)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert result.exit_code == 0
    assert not (repo_root / ".agents" / "trackers" / "github.json").exists()
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert "tracker" not in manifest


@pytest.mark.parametrize("answer,expected", [("y\n", True), ("n\n", False)])
def test_install_skills_prompts_for_tracker(
    agent_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, answer: str, expected: bool
) -> None:
    """First interactive install offers the GitHub tracker; declining installs nothing.

    Either answer is a choice, so both are recorded — see
    test_declining_the_tracker_is_not_asked_again for why declining writes a
    key at all.
    """
    import json
    import os
    from wfctl import cli
    monkeypatch.setattr(cli, "_interactive", lambda: True)
    src = _make_wf_skills_repo(tmp_path)
    _add_tracker(src)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"], input=answer
    )
    assert result.exit_code == 0
    assert (repo_root / ".agents" / "trackers" / "github.json").exists() is expected
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert manifest["tracker"] == ("github" if expected else None)
    if not expected:  # declining points at both ways back in
        assert "--tracker github" in result.output
        assert "/scaffold-tracker" in result.output


def test_install_skills_keeps_existing_tracker_config(agent_dir: Path, tmp_path: Path) -> None:
    """Once a tracker is chosen, a plain re-install leaves the config alone —
    local edits to it survive."""
    import os
    src = _make_wf_skills_repo(tmp_path)
    _add_tracker(src)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(
        app,
        ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--tracker", "github"],
    )

    cfg = repo_root / ".agents" / "trackers" / "github.json"
    cfg.write_text('{"verbs": {"list": ["gh", "issue", "list", "--limit", "30"]}}\n')
    result = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert result.exit_code == 0
    assert "--limit" in cfg.read_text()


def test_install_skills_tracker_none_opts_out(agent_dir: Path, tmp_path: Path) -> None:
    """--tracker none opts out without a prompt."""
    import json
    import os
    src = _make_wf_skills_repo(tmp_path)
    _add_tracker(src)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--tracker", "none"]
    )
    assert result.exit_code == 0
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert "tracker" not in manifest
    assert not (repo_root / ".agents" / "trackers" / "github.json").exists()


def test_install_skills_skips_native_mirror_by_default(agent_dir: Path, tmp_path: Path) -> None:
    """A skill with no `deployment` marker (or `deployment: command`) stays reference-only."""
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert not (repo_root / ".claude" / "skills").exists()


def test_install_skills_mirrors_native_skill_for_claude(agent_dir: Path, tmp_path: Path) -> None:
    """`deployment: skill` in SKILL.md frontmatter also mirrors to .claude/skills/<name>."""
    import os
    src = _make_wf_skills_repo(tmp_path)
    native = src / ".agents" / "skills" / "native-skill"
    native.mkdir(parents=True)
    (native / "SKILL.md").write_text(
        "---\nname: native-skill\ndeployment: skill\n---\nBody.\n"
    )
    subprocess.run(["git", "-C", str(src), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "commit", "-m", "add native skill"], check=True, capture_output=True)

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"])
    assert result.exit_code == 0
    # Still gets the reference-only mirror every agent gets...
    assert (repo_root / ".agents" / "skills" / "native-skill" / "SKILL.md").exists()
    # ...plus the Claude-native discovery mirror.
    assert (repo_root / ".claude" / "skills" / "native-skill" / "SKILL.md").exists()
    # The command-only skill from the base fixture is not mirrored.
    assert not (repo_root / ".claude" / "skills" / "test-skill").exists()


def test_install_skills_bob_ignores_native_deployment_marker(agent_dir: Path, tmp_path: Path) -> None:
    """The .claude/skills mirror is Claude-specific; bob never gets it."""
    import os
    src = _make_wf_skills_repo(tmp_path)
    native = src / ".agents" / "skills" / "native-skill"
    native.mkdir(parents=True)
    (native / "SKILL.md").write_text("---\ndeployment: skill\n---\nBody.\n")
    subprocess.run(["git", "-C", str(src), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "commit", "-m", "add native skill"], check=True, capture_output=True)

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "bob"]
    )
    assert result.exit_code == 0
    assert not (repo_root / ".claude").exists()


def test_uninstall_removes_native_skill_mirror(agent_dir: Path, tmp_path: Path) -> None:
    import os
    src = _make_wf_skills_repo(tmp_path)
    native = src / ".agents" / "skills" / "native-skill"
    native.mkdir(parents=True)
    (native / "SKILL.md").write_text("---\ndeployment: skill\n---\nBody.\n")
    subprocess.run(["git", "-C", str(src), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "commit", "-m", "add native skill"], check=True, capture_output=True)

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"])
    assert (repo_root / ".claude" / "skills" / "native-skill").exists()

    runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert not (repo_root / ".claude" / "skills" / "native-skill").exists()


def test_install_skills_bad_repo_exits_one(agent_dir: Path) -> None:
    result = runner.invoke(app, ["install-skills", "--repo", "https://github.com/no/such-repo-xyz"])
    assert result.exit_code == 1


def test_install_skills_reports_what_it_installed(agent_dir: Path, tmp_path: Path) -> None:
    """The summary names the source it installed from.

    The single `Installed N item(s)` total this used to assert is gone: N
    conflated skills, commands, runtime files and the tracker config into one
    number that read as a skill count. Per-layer, per-kind counts are asserted
    by test_install_summary_reports_per_layer_counts.
    """
    src = _make_wf_skills_repo(tmp_path)
    result = runner.invoke(
        app,
        ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"],
    )
    assert result.exit_code == 0
    assert "Installed from" in result.output
    assert "master" in result.output


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


def test_uninstall_removes_only_the_named_layer(agent_dir: Path, tmp_path: Path) -> None:
    """Uninstalling an agent drops that agent's items and nothing else.

    Behavior change: `.agents/skills` used to go with `--agent claude`, because
    claude claimed it. The base layer owns it now, so it survives — as does the
    tracker selection, which `wfctl issue` reads without needing skills at all.
    """
    import json
    import os
    src = _make_wf_skills_repo(tmp_path)
    _add_tracker(src)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(
        app,
        ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--tracker", "github"],
    )
    assert (repo_root / ".agents" / "skills" / "test-skill").exists()

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert result.exit_code == 0
    assert not (repo_root / ".claude" / "commands" / "test-cmd.md").exists()
    # Base layer untouched.
    assert (repo_root / ".agents" / "skills" / "test-skill").exists()
    assert (repo_root / ".agents" / "commands" / "test-cmd.md").exists()
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert "claude" not in manifest
    assert "base" in manifest
    assert manifest["tracker"] == "github"


def test_install_backs_up_and_uninstall_restores_pre_existing_file(agent_dir: Path, tmp_path: Path) -> None:
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    # A command of the same name already exists before wf-skills touches it.
    existing_cmd_dir = repo_root / ".claude" / "commands"
    existing_cmd_dir.mkdir(parents=True)
    (existing_cmd_dir / "test-cmd.md").write_text("# my own pre-existing command\n")

    result = runner.invoke(
        app,
        ["install-skills", "--repo", f"file://{src}", "--ref", "master",
         "--agent", "claude", "--yes"],
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
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"], input="n\n"
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
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"], input="y\n"
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
    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"])
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
    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"])

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


def test_layer_destinations_are_disjoint() -> None:
    """No two layers may write the same path.

    This is what makes the backup cross-attribution unreachable rather than
    patched: if the base layer and an agent layer never share a destination,
    one layer's install can never mistake another's files for the user's. The
    invariant is enforced here rather than in a comment, because a future agent
    entry would otherwise reintroduce the collision silently.
    """
    from wfctl import cli

    base = getattr(cli, "_BASE_TARGETS", [])
    assert base, "_BASE_TARGETS must exist and be non-empty"

    seen: dict[str, str] = {}
    collisions: list[str] = []
    for layer, targets in [("base", base), *cli._AGENT_TARGETS.items()]:
        for _src, dst in targets:
            if dst in seen:
                collisions.append(f"{dst!r}: claimed by both {seen[dst]!r} and {layer!r}")
            seen[dst] = layer

    assert not collisions, "layers share destinations:\n  " + "\n  ".join(collisions)


def test_bare_install_writes_agents_only(agent_dir: Path, tmp_path: Path) -> None:
    """FR-001, FR-002, SC-001: no --agent means no assistant-specific files."""
    import json
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert result.exit_code == 0

    assert (repo_root / ".agents" / "skills" / "test-skill").exists()
    assert (repo_root / ".agents" / "commands" / "test-cmd.md").exists()
    assert not (repo_root / ".claude").exists()
    assert not (repo_root / ".bob").exists()
    assert not (repo_root / ".github").exists()

    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert list(manifest) == ["base"]
    for item in manifest["base"]["items"]:
        assert item["path"].startswith((".agents/", ".specify/")), item["path"]


def _summary_layers(output: str) -> dict[str, str]:
    """Parse the per-layer summary block into {layer: counts}.

    Scoped to the block after the ✓ line so assertions cannot be satisfied by
    the opt-in hint below it, which legitimately names the same agents.
    """
    lines = output.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("✓ Installed"))
    # Rich wraps the repo URL onto its own continuation line, so the summary
    # does not necessarily start immediately after the ✓. Take the run of
    # indented lines up to the blank that separates it from the opt-in hint.
    layers = {}
    for line in lines[start + 1:]:
        if not line.strip():
            break
        if not line.startswith("  "):
            continue
        layer, _, counts = line.strip().partition("  ")
        layers[layer] = counts.strip()
    return layers


def test_install_summary_reports_per_layer_counts(agent_dir: Path, tmp_path: Path) -> None:
    """FR-011, SC-004: counts are per layer and per kind, never one total that
    reads as a skill count. A layer contributing nothing is omitted, not `0`."""
    src = _make_wf_skills_repo(tmp_path)
    bare = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert bare.exit_code == 0
    layers = _summary_layers(bare.output)
    assert list(layers) == ["base"], layers
    assert "1 skill" in layers["base"] and "1 command" in layers["base"]
    assert "0 " not in bare.output  # never a zero count anywhere

    claude = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"]
    )
    assert claude.exit_code == 0
    layers = _summary_layers(claude.output)
    assert list(layers) == ["base", "claude"], layers
    assert "1 command" in layers["claude"]


def test_bare_install_prints_agent_optin_hint(agent_dir: Path, tmp_path: Path) -> None:
    """FR-010: after a base-only install, name every agent that has a layer and
    the command to add it. Derived from _AGENT_TARGETS so an agent added later
    is covered without editing this test."""
    from wfctl import cli
    src = _make_wf_skills_repo(tmp_path)
    bare = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    opt_in = [a for a, targets in cli._AGENT_TARGETS.items() if targets]
    assert opt_in, "expected at least one agent with a layer of its own"
    for agent in opt_in:
        assert f"--agent {agent}" in bare.output
    assert "--agent none" not in bare.output  # no layer, nothing to opt into

    claude = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"]
    )
    assert "install-skills --agent" not in claude.output


def test_upgrade_from_pre_layer_manifest_is_silent(agent_dir: Path, tmp_path: Path) -> None:
    """FR-005, SC-002: a repo installed before the layer split upgrades quietly.

    The old shape recorded `.agents/*` under the agent key. This version plans
    those same paths as the base layer, so without unioning items across
    entries they read as files the user wrote — and the first install after
    upgrading would prompt to overwrite content wfctl installed itself, then
    back it up. The prompt aborts when there is no tty, which is how CI and
    workmux hooks would see it.
    """
    import json
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    # Install, then rewrite the manifest into the pre-split shape: one agent
    # entry owning every path, no `base` key.
    runner.invoke(
        app,
        ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"],
    )
    manifest_file = repo_root / ".wf-skills-manifest.json"
    manifest = json.loads(manifest_file.read_text())
    legacy_items = [i for entry in manifest.values() for i in entry.get("items", [])]
    manifest_file.write_text(json.dumps({"claude": {**manifest["claude"], "items": legacy_items}}))

    backups_before = sorted(p.name for p in (repo_root / ".wf-skills-backup").glob("*"))

    # The upgrade path: a bare install, which is what the new default gives you.
    result = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])

    assert result.exit_code == 0, result.output
    assert "will be overwritten" not in result.output
    assert "Backed up" not in result.output
    assert sorted(p.name for p in (repo_root / ".wf-skills-backup").glob("*")) == backups_before


def test_user_authored_file_is_still_backed_up(agent_dir: Path, tmp_path: Path) -> None:
    """FR-006: unioning prior items must not relax detection of real user files.

    The guard on the test above — a path wfctl never installed is still foreign,
    still backed up, and still restored on uninstall.
    """
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    mine = repo_root / ".agents" / "commands" / "test-cmd.md"
    mine.parent.mkdir(parents=True)
    mine.write_text("# mine, not wfctl's\n")

    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--yes"]
    )
    assert result.exit_code == 0
    assert "Backed up 1" in result.output
    assert mine.read_text() == "# test-cmd\n"

    result = runner.invoke(app, ["uninstall-skills", "--agent", "base"])
    assert result.exit_code == 0
    assert mine.read_text() == "# mine, not wfctl's\n"


def test_agent_copilot_writes_github_skills(agent_dir: Path, tmp_path: Path) -> None:
    """FR-003, SC-003: one command, on a repo with no prior install, and the
    skills land unmodified — `.agents/skills/<name>/SKILL.md` is already the
    shape Copilot's skills layout expects, so there is nothing to transform."""
    import json
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app,
        ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "copilot"],
    )
    assert result.exit_code == 0

    installed = repo_root / ".github" / "skills" / "test-skill" / "SKILL.md"
    assert installed.exists()
    assert installed.read_text() == (repo_root / ".agents" / "skills" / "test-skill" / "SKILL.md").read_text()
    # Its own root only — no other agent's paths.
    assert not (repo_root / ".claude").exists()
    assert not (repo_root / ".bob").exists()

    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert sorted(manifest) == ["base", "copilot"]
    assert all(i["path"].startswith(".github/") for i in manifest["copilot"]["items"])


def test_agent_codex_informs_and_installs_base(agent_dir: Path, tmp_path: Path) -> None:
    """FR-008: Codex reads no repo-local command path, so there is nothing to
    install for it — but that is a fact to state, not an error. The base layer
    still lands and the command succeeds."""
    import json
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app,
        ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "codex"],
    )
    assert result.exit_code == 0
    assert "AGENTS.md" in result.output

    assert (repo_root / ".agents" / "skills" / "test-skill").exists()
    assert not (repo_root / ".codex").exists()
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    # No entry of its own, so uninstalling it has nothing to fail on.
    assert list(manifest) == ["base"]


def test_unknown_agent_exits_listing_accepted_names(agent_dir: Path, tmp_path: Path) -> None:
    """FR-009: an unrecognised agent fails loudly and says what is accepted;
    `none` remains a valid way to ask for the base layer explicitly."""
    from wfctl import cli
    src = _make_wf_skills_repo(tmp_path)
    bad = runner.invoke(
        app,
        ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "nope"],
    )
    assert bad.exit_code == 1
    for name in cli._AGENT_TARGETS:
        assert name in bad.output, f"{name} missing from the accepted list"

    ok = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "none"]
    )
    assert ok.exit_code == 0


def test_backup_hint_names_a_command_that_restores(agent_dir: Path, tmp_path: Path) -> None:
    """The restore hint must name the layer that took the backup, not --agent.

    A bare install backs up under `base`, so a hint built from the requested
    agent said `--agent none` — which matches no manifest entry and silently
    does nothing, leaving the user's file overwritten with no working way back.
    """
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    mine = repo_root / ".agents" / "commands" / "test-cmd.md"
    mine.parent.mkdir(parents=True)
    mine.write_text("# mine, not wfctl's\n")

    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--yes"]
    )
    assert "uninstall-skills --agent base" in result.output
    assert "--agent none" not in result.output

    # Follow the printed instruction literally — it has to actually restore.
    assert runner.invoke(app, ["uninstall-skills", "--agent", "base"]).exit_code == 0
    assert mine.read_text() == "# mine, not wfctl's\n"


def test_overwrite_prompt_names_the_owning_layer(agent_dir: Path, tmp_path: Path) -> None:
    """Same hint, on the pre-overwrite confirmation — the earlier of the two."""
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    mine = repo_root / ".agents" / "commands" / "test-cmd.md"
    mine.parent.mkdir(parents=True)
    mine.write_text("# mine\n")

    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"], input="n\n"
    )
    assert "uninstall-skills --agent base" in result.output


def test_legacy_none_entry_is_dropped_once_base_owns_its_paths(
    agent_dir: Path, tmp_path: Path
) -> None:
    """A pre-split `none` entry must not double-book paths `base` now owns.

    Left in place, `uninstall-skills --agent none` deletes files `base` still
    claims — and `doctor` reports a phantom layer. It is dropped only after
    base has recorded every path it held, so nothing is orphaned.
    """
    import json
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    manifest_file = repo_root / ".wf-skills-manifest.json"

    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    base = json.loads(manifest_file.read_text())["base"]
    manifest_file.write_text(json.dumps({"none": base}))  # the pre-split shape

    result = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert result.exit_code == 0
    manifest = json.loads(manifest_file.read_text())
    assert "none" not in manifest
    assert {i["path"] for i in manifest["base"]["items"]} >= {i["path"] for i in base["items"]}


def test_legacy_entry_holding_an_unowned_path_survives(agent_dir: Path, tmp_path: Path) -> None:
    """The guard on the test above: dropping an entry must never orphan a path.

    An entry base does not fully cover still owns something — including the
    backup pointer for a user file — so it stays and remains uninstallable.
    """
    import json
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    manifest_file = repo_root / ".wf-skills-manifest.json"

    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    base = json.loads(manifest_file.read_text())["base"]
    stale = {**base, "items": [*base["items"], {"path": ".elsewhere/thing", "backup": None}]}
    manifest_file.write_text(json.dumps({"none": stale}))

    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert "none" in json.loads(manifest_file.read_text())


def test_declining_the_tracker_is_not_asked_again(
    agent_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-012 — asked once, not once per install.

    Declining used to write nothing, so the question came back on every
    upgrade and there was no way to answer it permanently: `--tracker none`
    clears the key rather than recording an opt-out.
    """
    import os
    from wfctl import cli
    monkeypatch.setattr(cli, "_interactive", lambda: True)
    src = _make_wf_skills_repo(tmp_path)
    _add_tracker(src)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    first = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"], input="n\n"
    )
    assert "No issue tracker configured" in first.output

    # No input at all: a re-prompt would abort on EOF rather than pass.
    again = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert again.exit_code == 0
    assert "No issue tracker configured" not in again.output
    assert not (repo_root / ".agents" / "trackers" / "github.json").exists()


def test_uninstall_defaults_to_the_layer_a_bare_install_writes(
    agent_dir: Path, tmp_path: Path
) -> None:
    """`install-skills` then `uninstall-skills`, both bare, must round-trip.

    The default stayed `claude` after install's moved to the base layer, so a
    bare uninstall reported nothing to remove.
    """
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert (repo_root / ".agents" / "skills" / "test-skill").exists()

    result = runner.invoke(app, ["uninstall-skills"])
    assert result.exit_code == 0
    assert not (repo_root / ".agents" / "skills" / "test-skill").exists()


def test_removing_base_under_an_agent_layer_asks_first(agent_dir: Path, tmp_path: Path) -> None:
    """Agent layers are views of the base, not copies — their command wrappers
    point into .agents/skills. Removing the base underneath one leaves it
    installed and broken, and `uninstall-skills` with no flags now targets the
    base, so this is the least-typed command in the tool.
    """
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"]
    )

    declined = runner.invoke(app, ["uninstall-skills"], input="n\n")
    assert declined.exit_code != 0, "declining must abort"
    assert "claude" in declined.output
    assert (repo_root / ".agents" / "skills" / "test-skill").exists(), "aborted — nothing removed"

    confirmed = runner.invoke(app, ["uninstall-skills"], input="y\n")
    assert confirmed.exit_code == 0
    assert not (repo_root / ".agents" / "skills" / "test-skill").exists()


def test_removing_base_alone_does_not_ask(agent_dir: Path, tmp_path: Path) -> None:
    """The guard is about dependents, not about the base being special: with no
    agent layer installed there is nothing to break, so no prompt."""
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])

    result = runner.invoke(app, ["uninstall-skills"])  # no input to give
    assert result.exit_code == 0
    assert not (repo_root / ".agents" / "skills" / "test-skill").exists()


def test_removing_an_agent_layer_never_asks(agent_dir: Path, tmp_path: Path) -> None:
    """Nothing depends on an agent layer, so removing one is always safe."""
    import os
    src = _make_wf_skills_repo(tmp_path)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--agent", "claude"]
    )
    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert result.exit_code == 0
    assert (repo_root / ".agents" / "skills" / "test-skill").exists(), "base survives"
