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

from wfctl.cli import (
    DENY_RULE,
    GUARD_HOOK_COMMAND,
    HOOK_COMMAND,
    STOP_HOOK_COMMAND,
    app,
)

runner = CliRunner()


def _settings_path(repo_root: Path) -> Path:
    return repo_root / ".claude" / "settings.json"


def _manifest(repo_root: Path) -> dict:
    return json.loads((repo_root / ".wf-skills-manifest.json").read_text())


# --- US1: install merges without disturbing what's already there -----------

def test_install_preserves_foreign_permissions_and_hooks_and_adds_its_own(
    agent_dir: Path,
) -> None:
    """The acceptance criterion for the whole mode: everything the consumer had
    is where they left it, and wfctl added only its own rows.

    A managed mirror would have replaced the file. The diff excluding wfctl's
    entries has to be empty, or the mode has cost the consumer the settings it
    exists to preserve. Their `PreToolUse` group matters most here — it is the
    event wfctl now writes to as well, so theirs has to survive beside it rather
    than be adopted or replaced."""
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
    assert after["permissions"]["allow"] == foreign["permissions"]["allow"]
    assert after["permissions"]["deny"] == [DENY_RULE]
    # Their guard script keeps its own group, its matcher and its position.
    assert after["hooks"]["PreToolUse"][0] == foreign["hooks"]["PreToolUse"][0]
    assert after["hooks"]["UserPromptSubmit"][0] == foreign["hooks"]["UserPromptSubmit"][0]
    managed = [
        h["command"]
        for g in after["hooks"]["UserPromptSubmit"]
        for h in g["hooks"]
        if h["command"] == HOOK_COMMAND
    ]
    assert managed == [HOOK_COMMAND]
    assert after["hooks"]["PreToolUse"][1] == {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": GUARD_HOOK_COMMAND}],
    }


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
            ],
            "Stop": [
                {"hooks": [{"type": "command", "command": STOP_HOOK_COMMAND}]}
            ],
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": GUARD_HOOK_COMMAND}],
                }
            ],
        },
        "permissions": {"deny": [DENY_RULE]},
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
    wfctl invented (data-model.md's `created` field).

    Two managed events share this one file since #212, and that is the failure
    this now catches: sampling `created` per target rather than per pass, the
    second event sees the file the first one just created, records `created:
    False`, and uninstall — which unlinks only when the record clearing the last
    entry says the file is wfctl's — leaves the `{}` behind."""
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
    # Simulate the consumer already having removed wfctl's entries by hand —
    # every one of them, hooks and the deny rule alike. Clearing only the hooks
    # would leave a rule wfctl still owns in the file, and removing that is work
    # uninstall is supposed to do.
    settings = json.loads(settings_path.read_text())
    settings["hooks"] = {}
    settings.pop("permissions", None)
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


def test_a_broken_symlink_at_the_settings_path_is_still_the_consumers(
    agent_dir: Path,
) -> None:
    """`path.exists()` follows the link, so a symlink whose target does not exist
    yet read as "no file here" and wfctl recorded the file as one it created.
    Uninstall then unlinks what it created — which is the consumer's symlink, not
    the settings inside it.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    target = repo_root / "real-settings.json"
    settings_path.symlink_to(target)
    assert not target.exists()

    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    assert HOOK_COMMAND in target.read_text()

    runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])
    assert settings_path.is_symlink(), "uninstall removed the consumer's symlink"


def test_the_stop_entry_cannot_block_a_stop_when_wfctl_cannot_run_it() -> None:
    """A non-zero exit means the opposite thing on `Stop` than on
    `UserPromptSubmit`: it blocks the stop, so the agent is told to keep going
    and stops again. A wfctl older than the settings file — or gone from PATH
    without `uninstall-skills` — would answer with a usage banner and exit 2, and
    turn that into a loop at the end of every turn.

    Pinned rather than left to the reader of the string, because the `|| true`
    looks like sloppiness until you know which event it is on."""
    assert STOP_HOOK_COMMAND.endswith("|| true")


def test_uninstall_prunes_the_file_after_an_upgrade_added_a_second_event(
    agent_dir: Path,
) -> None:
    """The sequence every existing consumer takes: installed when wfctl managed
    one event, re-installed once it managed two. `created` answers "did wfctl
    bring this file into existence", which is a fact about the *file* — sampled
    per entry, the `Stop` record written on the upgrade says `False`, and
    uninstall, which unlinks on the record that empties the file, leaves the `{}`
    behind. The test above installs once and cannot see it."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])

    # Roll the install back to what the previous wfctl left: one entry, one
    # record. Editing the manifest rather than pinning a released wfctl, because
    # what is under test is how *this* install reads a record it did not write.
    settings_path = _settings_path(repo_root)
    settings = json.loads(settings_path.read_text())
    del settings["hooks"]["Stop"]
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    manifest_path = repo_root / ".wf-skills-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["claude"]["merged"] = [
        r for r in manifest["claude"]["merged"] if r["event"] != "Stop"
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])
    assert result.exit_code == 0, result.output

    assert not settings_path.exists(), settings_path.read_text()


def test_uninstall_counts_settings_files_not_managed_entries(agent_dir: Path) -> None:
    """Two events share one file. Counting records reported "2 settings file(s)"
    where there is one — the same bug the install summary was deduped for, on the
    half that did not get the pass."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    # Pre-existing content, so uninstall reports the file rather than deleting it.
    settings_path.write_text(json.dumps({"permissions": {"allow": ["Bash"]}}) + "\n")
    runner.invoke(app, ["install-skills", "--agent", "claude"])

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])
    assert result.exit_code == 0, result.output
    assert "from 1 settings file(s)" in result.output, result.output


def test_doctor_names_what_a_missing_stop_hook_costs(agent_dir: Path) -> None:
    """Each event loses something different, and "the managed hook is gone" tells
    the reader neither. Pinned per event because two assertions matching only the
    shared prefix leave the branch that picks between them uncovered."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    settings = json.loads(settings_path.read_text())
    del settings["hooks"]["Stop"]
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    result = runner.invoke(app, ["doctor"])
    assert "nothing looks at a reply once it is written" in result.output
    assert "decay again mid-session" not in result.output


def test_doctor_reports_a_managed_event_the_recorded_install_never_had(
    agent_dir: Path,
) -> None:
    """A repo installed when wfctl managed one event has no `Stop` record, so a
    record-driven check would never look for the entry — and the bundle hash
    cannot see it either, since the hook adds nothing under `wfctl/agents/`. The
    feature would ship to nobody who already had wfctl."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    settings = json.loads(settings_path.read_text())
    del settings["hooks"]["Stop"]
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    manifest_path = repo_root / ".wf-skills-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["claude"]["merged"] = [
        r for r in manifest["claude"]["merged"] if r["event"] != "Stop"
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    result = runner.invoke(app, ["doctor"])
    assert "managed Stop hook" in result.output, result.output


def test_a_manifest_record_without_created_does_not_crash_the_install(
    agent_dir: Path,
) -> None:
    """The manifest is gitignored and hand-editable, so a record can arrive
    without every key an install expects. Reading `created` as a subscript turned
    that into a crash on the install path — and the safe answer when it is absent
    is that wfctl did not create the file, since that costs an empty `{}` left
    behind where the other guess costs a consumer's file."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps({"permissions": {"allow": ["Bash"]}}) + "\n")
    runner.invoke(app, ["install-skills", "--agent", "claude"])

    manifest_path = repo_root / ".wf-skills-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for record in manifest["claude"]["merged"]:
        del record["created"]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0, result.output
    after = json.loads(manifest_path.read_text())
    assert all(r["created"] is False for r in after["claude"]["merged"]), after

    # And the consumer's file survives, which is what the safe side buys.
    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])
    assert result.exit_code == 0, result.output
    assert settings_path.exists()


# --- The receipt: who added the rule that cannot say so itself --------------

def _permissions(repo_root: Path) -> list[dict]:
    return _manifest(repo_root)["claude"].get("permissions", [])


def test_a_rule_the_repo_already_had_is_recorded_as_not_wfctls(agent_dir: Path) -> None:
    """The entire reason a receipt exists. `Bash(cd:*)` in a repo that wrote it
    themselves is indistinguishable from one wfctl installed, so the only moment
    authorship is observable is the install that first looks."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"permissions": {"deny": [DENY_RULE]}}, indent=2) + "\n"
    )

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0, result.output
    assert _permissions(repo_root) == [
        {"path": ".claude/settings.json", "rule": DENY_RULE, "added": False}
    ]


def test_uninstall_leaves_a_rule_the_repo_wrote_themselves(agent_dir: Path) -> None:
    """SC-004. Losing a security rule the repo wrote, to an uninstall that
    believed it was cleaning up after itself, is the failure the receipt is
    built to prevent."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"permissions": {"deny": [DENY_RULE]}}, indent=2) + "\n"
    )

    runner.invoke(app, ["install-skills", "--agent", "claude"])
    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])
    assert result.exit_code == 0, result.output
    assert json.loads(settings_path.read_text())["permissions"]["deny"] == [DENY_RULE]


def test_uninstall_removes_a_rule_wfctl_added(agent_dir: Path) -> None:
    """The other half. A receipt that never licensed a removal would leave
    wfctl's own entry denying `cd` with nothing left to explain why."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"permissions": {"allow": ["Bash(npm test)"]}}, indent=2) + "\n"
    )

    runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert _permissions(repo_root)[0]["added"] is True

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])
    assert result.exit_code == 0, result.output
    after = json.loads(settings_path.read_text())
    assert after == {"permissions": {"allow": ["Bash(npm test)"]}}


def test_uninstall_says_when_it_leaves_an_edited_rule_behind(agent_dir: Path) -> None:
    """FR-020. Silence here would leave "your own entries were left alone"
    standing over an entry descended from wfctl's, which is the one reading of
    that line this feature must not allow."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    settings = json.loads(settings_path.read_text())
    settings["permissions"]["deny"] = ["Bash(cd:/tmp/*)"]
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])
    assert result.exit_code == 0, result.output
    assert "Bash(cd:/tmp/*)" in result.output
    assert DENY_RULE in result.output
    assert json.loads(settings_path.read_text())["permissions"]["deny"] == [
        "Bash(cd:/tmp/*)"
    ]


# --- The refusal -----------------------------------------------------------

def test_install_refuses_over_a_rule_the_repo_removed(agent_dir: Path) -> None:
    """FR-017. Re-adding it silently makes "you may remove this" theatre;
    stepping over it silently hides a decision someone made."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    settings = json.loads(settings_path.read_text())
    del settings["permissions"]
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 1, result.output
    assert DENY_RULE in result.output
    assert "--force" in result.output
    assert "permissions" not in json.loads(settings_path.read_text())


def test_the_refusal_copies_nothing(agent_dir: Path) -> None:
    """The placement is the risk, not the logic. `_merge_permissions` runs past
    the skill copies, so a check written beside it would refuse over a tree it
    had already half-installed."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    settings = json.loads(settings_path.read_text())
    del settings["permissions"]
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    skill = repo_root / ".agents" / "skills" / "test-skill" / "SKILL.md"
    skill.write_text("edited by hand\n")

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 1, result.output
    # Untouched, not merely unreported: a half-install would have overwritten it.
    assert skill.read_text() == "edited by hand\n"


def test_a_receipt_of_theirs_refuses_the_same_way(agent_dir: Path) -> None:
    """A receipt is wfctl's record that it looked at this entry, not a claim of
    ownership. The repo is equally entitled to delete a rule wfctl installed and
    one it merely noticed, and both are changes only a person can explain."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"permissions": {"deny": [DENY_RULE]}}, indent=2) + "\n"
    )
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert _permissions(repo_root)[0]["added"] is False

    settings = json.loads(settings_path.read_text())
    del settings["permissions"]
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 1, result.output


def test_force_reasserts_the_rule_and_records_it_as_wfctls(agent_dir: Path) -> None:
    """`--force` is the person answering the refusal. A run that re-asserted the
    rule did add it, so a receipt still reading `added: false` afterwards would
    have uninstall leave wfctl's own entry behind."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"permissions": {"deny": [DENY_RULE]}}, indent=2) + "\n"
    )
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings = json.loads(settings_path.read_text())
    del settings["permissions"]
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    result = runner.invoke(app, ["install-skills", "--agent", "claude", "--force"])
    assert result.exit_code == 0, result.output
    assert json.loads(settings_path.read_text())["permissions"]["deny"] == [DENY_RULE]
    assert _permissions(repo_root)[0]["added"] is True


def test_an_unreadable_settings_file_warns_rather_than_refusing(agent_dir: Path) -> None:
    """FR-014 outranks FR-017. Drift is not established by failing to read, and
    refusing here would hold the whole skills tree hostage to a stray comma."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    settings_path.write_text("{not valid json")

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0, result.output
    assert settings_path.read_text() == "{not valid json"
    assert (repo_root / ".agents" / "skills" / "test-skill" / "SKILL.md").exists()


def test_a_fresh_install_never_trips_the_refusal(agent_dir: Path) -> None:
    """The one genuinely unattended install is worktree creation, whose
    `.claude/` is made by that same install. This is what makes a refusal safe
    to put in a command a `post_create` hook runs with nobody watching."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0, result.output


# --- The two that would otherwise hold by omission -------------------------

def test_the_base_layer_installs_no_guard_entry_and_no_rule(agent_dir: Path) -> None:
    """FR-016. `PreToolUse` and `permissions` are Claude Code's schema, and the
    base layer is agent-agnostic. Nothing fails today if that stops being true,
    which is exactly why it is pinned."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0, result.output
    assert not _settings_path(repo_root).exists()
    assert "permissions" not in _manifest(repo_root).get("base", {})


def test_a_drifted_hook_is_still_corrected_without_refusing(agent_dir: Path) -> None:
    """FR-018. The refusal covers the entry that cannot say whose it is, and
    stops there. A managed hook announces itself with `wfctl hook `, so
    re-asserting one is wfctl correcting its own row — extending the refusal to
    hooks would change behaviour for every existing consumer."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    settings = json.loads(settings_path.read_text())
    settings["hooks"]["PreToolUse"][0]["matcher"] = "*"
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0, result.output
    after = json.loads(settings_path.read_text())
    assert after["hooks"]["PreToolUse"][0]["matcher"] == "Bash"


def test_uninstall_deletes_a_file_both_passes_emptied(agent_dir: Path) -> None:
    """`created` is one fact about the file, and the hook pass and the permission
    pass each hold only half of what is in it. Answered separately, whichever ran
    first saw entries the other had yet to remove and left an empty `{}` behind."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    assert "permissions" in json.loads(settings_path.read_text())

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])
    assert result.exit_code == 0, result.output
    assert not settings_path.exists(), settings_path.read_text()


# --- doctor's second vocabulary --------------------------------------------

def test_doctor_warns_about_a_removed_rule_without_failing_the_run(
    agent_dir: Path,
) -> None:
    """The whole reason a second tier exists. A missing hook is breakage — the
    guard does not run at all. A missing deny rule narrows its reach and leaves a
    working guard, and `cd` is an ordinary command a repo may have decided it
    needs. Exiting 1 would turn their build red for as long as that decision
    stands, and `doctor` only reads."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    settings = json.loads(settings_path.read_text())
    del settings["permissions"]
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0, result.output
    assert DENY_RULE in result.output
    assert "is gone" in result.output


def test_a_missing_hook_still_fails_the_run(agent_dir: Path) -> None:
    """The other side of the same tier. Both entries live in one file, and a
    check that reported them alike would either fail a build over a decision or
    stay quiet about a guard that is not running."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings_path = _settings_path(repo_root)
    settings = json.loads(settings_path.read_text())
    del settings["hooks"]["PreToolUse"]
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "nothing stops a Bash call reaching into a sibling worktree" in result.output


def test_doctor_says_nothing_about_a_rule_the_repo_wrote_themselves(
    agent_dir: Path,
) -> None:
    """A receipt of `added: false` is wfctl recording that the entry is not its
    business. Reporting its removal would be wfctl claiming an entry it had
    explicitly disclaimed."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"permissions": {"deny": [DENY_RULE]}}, indent=2) + "\n"
    )
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    settings = json.loads(settings_path.read_text())
    del settings["permissions"]
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    result = runner.invoke(app, ["doctor"])
    assert DENY_RULE not in result.output
