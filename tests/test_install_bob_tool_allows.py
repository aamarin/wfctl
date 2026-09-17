"""Filesystem round-trip for Bob Shell's `tools.allowed` merge, through the
CLI. Sibling to `test_install_hook_merge.py` (Claude's `permissions.deny`),
scoped to the load-bearing cases rather than its full breadth: the schema and
the merge/unmerge/drift functions are unit-tested in
`test_bob_settings_merge.py`; this proves the commands that call them — install
writes only on change, uninstall restores what it didn't own, doctor reports
drift — against a real settings file on a real repo.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from typer.testing import CliRunner

from wfctl.cli import _BOB_APPROVAL_ENTRIES, app

runner = CliRunner()


def _settings_path(repo_root: Path) -> Path:
    return repo_root / ".bob" / "settings.json"


def _manifest(repo_root: Path) -> dict:
    return json.loads((repo_root / ".wf-skills-manifest.json").read_text())


def _tools(repo_root: Path) -> list[dict]:
    return _manifest(repo_root)["bob"].get("tools", [])


def test_install_merges_the_starter_entries_and_keeps_what_was_there(
    agent_dir: Path,
) -> None:
    """The acceptance criterion for the whole mode: everything the consumer
    had is where they left it, and wfctl added only its own entries."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"tools": {"allowed": ["execute_command(npm test)"]}}, indent=2) + "\n"
    )

    result = runner.invoke(app, ["install-skills", "--agent", "bob"])
    assert result.exit_code == 0, result.output

    after = json.loads(settings_path.read_text())["tools"]["allowed"]
    assert "execute_command(npm test)" in after
    for entry in _BOB_APPROVAL_ENTRIES:
        assert entry in after


def test_install_is_idempotent(agent_dir: Path) -> None:
    """A second install must not duplicate what the first one added."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "bob"])
    runner.invoke(app, ["install-skills", "--agent", "bob"])

    after = json.loads(_settings_path(repo_root).read_text())["tools"]["allowed"]
    assert after.count(_BOB_APPROVAL_ENTRIES[0]) == 1


def test_agent_claude_never_touches_bob_settings(agent_dir: Path) -> None:
    """`.bob/settings.json` is Bob's schema; installing Claude's layer must not
    create or edit a file that belongs to an agent that was not asked for."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0, result.output
    assert not _settings_path(repo_root).exists()


def test_a_receipt_of_theirs_is_recorded_as_not_wfctls(agent_dir: Path) -> None:
    """An entry the repo already had is indistinguishable from one wfctl
    installed, so the only moment authorship is observable is the install that
    first looks."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    entry = _BOB_APPROVAL_ENTRIES[0]
    settings_path.write_text(json.dumps({"tools": {"allowed": [entry]}}, indent=2) + "\n")

    result = runner.invoke(app, ["install-skills", "--agent", "bob"])
    assert result.exit_code == 0, result.output
    record = next(r for r in _tools(repo_root) if r["entry"] == entry)
    assert record["added"] is False


def test_uninstall_leaves_an_entry_the_repo_wrote_themselves(agent_dir: Path) -> None:
    """Losing an approval the repo wrote, to an uninstall that believed it was
    cleaning up after itself, is the failure the receipt exists to prevent."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    entry = _BOB_APPROVAL_ENTRIES[0]
    settings_path.write_text(json.dumps({"tools": {"allowed": [entry]}}, indent=2) + "\n")

    runner.invoke(app, ["install-skills", "--agent", "bob"])
    result = runner.invoke(app, ["uninstall-skills", "--agent", "bob", "--yes"])
    assert result.exit_code == 0, result.output
    assert entry in json.loads(settings_path.read_text())["tools"]["allowed"]


def test_uninstall_removes_every_entry_wfctl_added(agent_dir: Path) -> None:
    """The other half: a receipt that never licensed a removal would leave
    wfctl's own entries with nothing left to explain why."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"tools": {"allowed": ["execute_command(npm test)"]}}, indent=2) + "\n"
    )

    runner.invoke(app, ["install-skills", "--agent", "bob"])
    result = runner.invoke(app, ["uninstall-skills", "--agent", "bob", "--yes"])
    assert result.exit_code == 0, result.output
    after = json.loads(settings_path.read_text())
    assert after == {"tools": {"allowed": ["execute_command(npm test)"]}}


def test_install_refuses_over_an_entry_the_repo_removed(agent_dir: Path) -> None:
    """Re-adding it silently makes 'you may remove this' theatre; stepping
    over it silently hides a decision someone made."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "bob"])
    settings_path = _settings_path(repo_root)
    settings_path.write_text(json.dumps({}, indent=2) + "\n")

    result = runner.invoke(app, ["install-skills", "--agent", "bob"])
    assert result.exit_code == 1, result.output
    assert _BOB_APPROVAL_ENTRIES[0] in result.output
    assert "--force" in result.output
    assert json.loads(settings_path.read_text()) == {}


def test_force_restores_a_removed_entry(agent_dir: Path) -> None:
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "bob"])
    settings_path = _settings_path(repo_root)
    settings_path.write_text(json.dumps({}, indent=2) + "\n")

    result = runner.invoke(app, ["install-skills", "--agent", "bob", "--force"])
    assert result.exit_code == 0, result.output
    after = json.loads(settings_path.read_text())["tools"]["allowed"]
    for entry in _BOB_APPROVAL_ENTRIES:
        assert entry in after


def test_doctor_warns_when_a_managed_entry_is_gone(agent_dir: Path) -> None:
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "bob"])
    settings_path = _settings_path(repo_root)
    settings_path.write_text(json.dumps({}, indent=2) + "\n")

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0, result.output
    assert _BOB_APPROVAL_ENTRIES[0] in result.output
    assert "Bob Shell will prompt for approval" in result.output
