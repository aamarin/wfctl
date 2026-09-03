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

import pytest
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
    """The acceptance criterion for the whole mode: everything the consumer had
    is byte-for-byte where they left it, and wfctl added exactly one row.

    A managed mirror would have replaced the file. The diff excluding wfctl's
    entry has to be empty, or the mode has cost the consumer the settings it
    exists to preserve."""
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
    """A consumer who has never written a settings file gets a valid one, not a
    fragment the harness rejects — and `created` is recorded so uninstall knows
    the file is wfctl's to delete rather than theirs to edit."""
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
    """One malformed settings file must not cost the consumer the whole install.
    A refusal here would trade a working skills tree for a file they have to fix
    before they can have either — FR-010."""
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
    """The schema is Claude Code's and no other agent shares it, so a merge for
    `codex` would write a hook into a file whose format it invented — FR-015."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    for agent in ("codex", "bob"):
        result = runner.invoke(app, ["install-skills", "--agent", agent])
        assert result.exit_code == 0, result.output
        assert not _settings_path(repo_root).exists()
        manifest = _manifest(repo_root)
        assert "merged" not in manifest.get(agent, {})


# --- US2: reinstalling converges, never duplicates --------------------------

def test_reinstall_with_a_current_entry_does_not_reopen_the_file(agent_dir: Path) -> None:
    """A rewrite reflows the consumer's file, losing key order and array layout.
    That cost is acceptable once, on the install that adds the entry; paying it
    again on every reinstall that changes nothing is not."""
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
    """Converge on exactly one managed entry. Appending instead of replacing
    would leave the consumer running two wfctl hooks per turn, one of them a
    command that no longer exists."""
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


def _with_command(command: str):
    """Rewrite the managed entry's command, for the "behind" drift case."""

    def rewrite(settings: dict) -> dict:
        settings["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"] = command
        return settings

    return rewrite


def test_doctor_is_silent_on_the_managed_hook_when_current(agent_dir: Path) -> None:
    """doctor reports drift, not presence — a correct entry must produce no line,
    or every clean run carries noise about a hook that is fine."""
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    result = runner.invoke(app, ["doctor"])
    assert "settings.json" not in result.output


@pytest.mark.parametrize(
    "break_it, expected_state",
    [
        (lambda s: {}, "is gone"),
        (_with_command("wfctl hook old-name"), "is behind this wfctl"),
    ],
    ids=["removed-by-hand", "installed-by-an-older-wfctl"],
)
def test_doctor_names_which_way_the_managed_hook_drifted(
    agent_dir: Path, break_it, expected_state: str
) -> None:
    """Missing and behind are different repairs — one says the consumer deleted
    the entry, the other that wfctl renamed the command underneath it. Asserted
    on the differing text because two tests checking only the shared exit code,
    path and fix command left the branch that picks between them uncovered.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    settings_path.write_text(
        json.dumps(break_it(json.loads(settings_path.read_text())), indent=2) + "\n"
    )

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "settings.json" in result.output
    assert "wfctl install-skills --agent claude" in result.output
    assert expected_state in result.output


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
    """The prune is per-entry, not per-group. A consumer who put their own hook
    in the same group as wfctl's must keep it — FR-006."""
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
    """Uninstall touches nothing it does not own. A consumer who removed the
    entry by hand has a file wfctl has no reason to rewrite, and rewriting it
    would reflow their formatting for no change at all."""
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


# --- Failures during merge must not cost the consumer the install ----------

def test_a_failed_merge_keeps_the_prior_record_so_uninstall_still_finds_the_hook(
    agent_dir: Path,
) -> None:
    """The manifest layer is rewritten wholesale on every install, and the merge
    record was re-attached only when that install produced one. A single failed
    pass therefore dropped wfctl's claim on an entry that was still in the file:
    uninstall reported success, left the hook wired, and doctor said nothing.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    # A file the consumer already owns, so uninstall must edit it rather than
    # delete it — the case where a stranded entry actually stays stranded.
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}}))
    assert runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"]).exit_code == 0
    assert HOOK_COMMAND in settings_path.read_text()

    settings_path.chmod(0o000)
    try:
        runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    finally:
        settings_path.chmod(0o644)

    assert _manifest(repo_root)["claude"].get("merged"), "ownership was dropped"

    runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])
    remaining = settings_path.read_text()
    assert HOOK_COMMAND not in remaining
    assert "Bash(ls:*)" in remaining, "uninstall took the consumer's own settings"


def test_a_settings_write_that_fails_is_reported_not_raised(
    agent_dir: Path, monkeypatch
) -> None:
    """`_write_settings` was the one call in the merge with no guard around it,
    so an OSError escaped after the skills were copied and before the manifest
    was saved. The copies then existed with nothing recording them, and
    uninstall answered "Nothing installed" — unreachable without a manual rm.

    Fault-injected rather than driven by permissions: a read-only `.claude`
    makes the *copy loop* raise first (#143, predating this feature), and the
    test would pass without the guard it exists to pin.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    def boom(*args: object, **kwargs: object) -> None:
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr("wfctl.cli._write_settings", boom)
    result = runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    assert result.exit_code == 0
    assert (repo_root / ".wf-skills-manifest.json").exists(), "install left no manifest"
    assert "settings.json" in result.output


# --- What the merge owes a file it does not own ----------------------------

def test_the_merge_leaves_non_ascii_in_the_consumers_file_as_they_wrote_it(
    agent_dir: Path,
) -> None:
    """`json.dumps` defaults to `ensure_ascii=True`, so an accented path or a
    checkmark in a consumer's own permission came back as `\\uXXXX`. The file is
    committed and reviewed by a human — a diff that escapes every non-ASCII byte
    in it is the churn this mode exists to avoid.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"permissions": {"allow": ["Bash(echo café ✓ 日本:*)"]}}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    assert "café ✓ 日本" in settings_path.read_text(encoding="utf-8")


def test_the_merge_keeps_the_consumers_file_mode(agent_dir: Path) -> None:
    """The write goes through mkstemp + os.replace, which installs a fresh file
    carrying the temp file's 0600 rather than the mode the consumer chose. A
    settings file that was group-readable stopped being so after an install."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(json.dumps({}, indent=2) + "\n")
    settings_path.chmod(0o664)

    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    assert settings_path.stat().st_mode & 0o777 == 0o664


def test_a_symlinked_settings_file_is_written_through_not_replaced(
    agent_dir: Path,
) -> None:
    """`os.replace` onto a symlink swaps the link for a regular file. The
    consumer's real settings never received the hook, and the link they had
    deliberately set up was gone with nothing saying so."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    real = repo_root / "real-settings.json"
    real.write_text(json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}}, indent=2))
    settings_path.symlink_to(real)

    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    assert settings_path.is_symlink(), "the consumer's symlink was replaced"
    assert HOOK_COMMAND in real.read_text()


def test_a_settings_file_with_a_utf8_bom_still_merges(agent_dir: Path) -> None:
    """A BOM made the file permanently unmergeable — every install reported
    "Unexpected UTF-8 BOM" and named no remedy, so the hook could never install
    into a file an editor on Windows had written."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text("﻿" + json.dumps({}, indent=2), encoding="utf-8")

    result = runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    assert result.exit_code == 0
    assert HOOK_COMMAND in settings_path.read_text(encoding="utf-8-sig")


def test_a_failed_merge_does_not_claim_no_hook_is_installed(
    agent_dir: Path, monkeypatch
) -> None:
    """The warning read "left untouched, no hook installed" on every merge
    problem, including a reinstall where the entry is already in the file. A
    consumer who trusted it would go looking for a hook that was there."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    assert HOOK_COMMAND in _settings_path(repo_root).read_text()

    def boom(*args: object, **kwargs: object) -> None:
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr("wfctl.cli._write_settings", boom)
    _settings_path(repo_root).write_text(json.dumps({}, indent=2))
    result = runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    assert "no hook installed" not in result.output


def test_uninstall_reports_a_settings_file_it_could_not_parse(agent_dir: Path) -> None:
    """Uninstall skipped an unparseable file and then deleted the record naming
    it, on the reasoning that a broken file holds nothing of wfctl's. It does —
    one stray comma leaves the entry in place, now with nothing recording it."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    settings_path = _settings_path(repo_root)
    settings_path.write_text('{"hooks": {,}')

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])

    assert "settings.json" in result.output
