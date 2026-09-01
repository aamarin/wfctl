"""Filesystem round-trip for the merge install mode, through the CLI.

`test_settings_merge.py` proves `_settings`'s dict-in/dict-out rules; this file
proves the commands that call it — install writes only on change, uninstall
restores what it didn't own, doctor reports drift — against a real settings
file on a real repo. `agent_dir` (conftest) is a git repo with
`WFCTL_REPO_ROOT` pointed at it; `bundle` (autouse) fakes the installed tree so
nothing here depends on wf-skills' real content.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from typer.testing import CliRunner

from wfctl.cli import HOOK_COMMAND, app

runner = CliRunner()


def _settings_path(repo_root: Path) -> Path:
    return repo_root / ".claude" / "settings.json"


def _manifest(repo_root: Path) -> dict:
    return json.loads((repo_root / ".wf-skills-manifest.json").read_text())


# --- US1: install merges without disturbing what's already there -----------

def test_install_preserves_foreign_permissions_and_hooks_and_adds_one_entry(
    agent_dir: Path,
) -> None:
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    foreign = {
        "permissions": {"allow": ["Bash(git status:*)"]},
        "hooks": {
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": "./scripts/mine.sh"}]}
            ],
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "./guard.sh"}]}
            ],
        },
    }
    settings_path.write_text(json.dumps(foreign, indent=2) + "\n")

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0, result.output

    after = json.loads(settings_path.read_text())
    assert after["permissions"] == foreign["permissions"]
    assert after["hooks"]["PreToolUse"] == foreign["hooks"]["PreToolUse"]
    assert after["hooks"]["UserPromptSubmit"][0] == foreign["hooks"]["UserPromptSubmit"][0]
    managed = [
        h["command"]
        for g in after["hooks"]["UserPromptSubmit"]
        for h in g["hooks"]
        if h["command"] == HOOK_COMMAND
    ]
    assert managed == [HOOK_COMMAND]


def test_install_creates_a_valid_settings_file_when_none_exists(agent_dir: Path) -> None:
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    assert not _settings_path(repo_root).exists()

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0, result.output

    after = json.loads(_settings_path(repo_root).read_text())
    assert after == {
        "hooks": {
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": HOOK_COMMAND}]}
            ]
        }
    }


def test_install_warns_on_invalid_json_and_still_completes_every_other_target(
    agent_dir: Path,
) -> None:
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text("{not valid json")

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0, result.output
    assert "settings.json" in result.output
    assert "left untouched" in result.output
    # Untouched means untouched: the malformed bytes are exactly what was there.
    assert settings_path.read_text() == "{not valid json"
    # Every other target still lands.
    assert (repo_root / ".agents" / "skills" / "test-skill" / "SKILL.md").exists()
    assert (repo_root / ".claude" / "commands" / "test-cmd.md").exists()


def test_install_is_claude_only_no_other_agent_merges_a_hook(agent_dir: Path) -> None:
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    for agent in ("codex", "bob"):
        result = runner.invoke(app, ["install-skills", "--agent", agent])
        assert result.exit_code == 0, result.output
        assert not _settings_path(repo_root).exists()
        manifest = _manifest(repo_root)
        assert "merged" not in manifest.get(agent, {})


# --- US2: reinstalling converges, never duplicates --------------------------

def test_reinstall_with_a_current_entry_does_not_reopen_the_file(agent_dir: Path) -> None:
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    before_mtime = settings_path.stat().st_mtime_ns
    before_text = settings_path.read_text()

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0, result.output
    assert settings_path.stat().st_mtime_ns == before_mtime
    assert settings_path.read_text() == before_text


def test_reinstall_replaces_a_hand_edited_stale_entry_in_place(agent_dir: Path) -> None:
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    settings = json.loads(settings_path.read_text())
    settings["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"] = "wfctl hook old-name"
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0, result.output

    after = json.loads(settings_path.read_text())
    groups = after["hooks"]["UserPromptSubmit"]
    assert len(groups) == 1
    assert groups[0]["hooks"][0]["command"] == HOOK_COMMAND


def test_doctor_is_silent_on_the_managed_hook_when_current(agent_dir: Path) -> None:
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    result = runner.invoke(app, ["doctor"])
    assert "settings.json" not in result.output


def test_doctor_reports_a_missing_managed_hook_and_names_the_fix(agent_dir: Path) -> None:
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    _settings_path(repo_root).write_text(json.dumps({}, indent=2) + "\n")

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "settings.json" in result.output
    assert "wfctl install-skills --agent claude" in result.output


def test_doctor_reports_a_behind_managed_hook_and_names_the_fix(agent_dir: Path) -> None:
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    settings = json.loads(settings_path.read_text())
    settings["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"] = "wfctl hook old-name"
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "settings.json" in result.output
    assert "wfctl install-skills --agent claude" in result.output


# --- US3: uninstall removes only what wfctl owns -----------------------------

def test_uninstall_prunes_the_group_when_wfctls_entry_was_alone(agent_dir: Path) -> None:
    """wfctl's entry was the only content — install created the file, so an
    uninstall that empties it deletes it rather than leaving a `{}` scaffold
    wfctl invented (data-model.md's `created` field)."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert _settings_path(repo_root).exists()

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])
    assert result.exit_code == 0, result.output

    assert not _settings_path(repo_root).exists()


def test_uninstall_keeps_a_foreign_hook_sharing_the_same_group(agent_dir: Path) -> None:
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    settings = json.loads(settings_path.read_text())
    settings["hooks"]["UserPromptSubmit"].append(
        {"hooks": [{"type": "command", "command": "./my-hook.sh"}]}
    )
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])
    assert result.exit_code == 0, result.output

    after = json.loads(settings_path.read_text())
    commands = [h["command"] for g in after["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
    assert commands == ["./my-hook.sh"]


def test_uninstall_with_no_managed_entry_does_not_open_the_file(agent_dir: Path) -> None:
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    # Simulate the consumer already having removed wfctl's entry by hand.
    settings = json.loads(settings_path.read_text())
    settings["hooks"] = {}
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    before_mtime = settings_path.stat().st_mtime_ns

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])
    assert result.exit_code == 0, result.output
    assert settings_path.stat().st_mtime_ns == before_mtime
