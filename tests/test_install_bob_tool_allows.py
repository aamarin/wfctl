"""`install-skills --agent bob` leaves Bob Shell's `.bob/settings.json` alone,
and takes back out the tool approvals an older wfctl merged into it.

Bob Shell gives that project file precedence over the user's global
`~/.bob/settings/settings.json`, so a starter allow-list written into a repo
replaced whatever the user had approved globally. The removal itself is
unit-tested in `test_bob_settings_merge.py`; this proves the commands that run
it against a real settings file on a real repo.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl import cli
from wfctl.cli import app

runner = CliRunner()

# What the older install merged, as its receipts recorded it.
_LEGACY_ENTRIES = (
    "read_file",
    "list_files",
    "glob",
    "grep",
    "execute_command(git)",
    "execute_command(uv run)",
    "run_shell_command(git)",
    "run_shell_command(uv run)",
)


def _settings_path(repo_root: Path) -> Path:
    return repo_root / ".bob" / "settings.json"


def _manifest_path(repo_root: Path) -> Path:
    return repo_root / ".wf-skills-manifest.json"


def _record_legacy_install(repo_root: Path, theirs: list[str]) -> None:
    """Leave the repo as an older wfctl's bob install did: the starter entries
    merged into the settings file beside `theirs`, and a receipt for each in
    the manifest. An entry already in `theirs` is recorded as not wfctl's, the
    way the older install recorded it."""
    result = runner.invoke(app, ["install-skills", "--agent", "bob", "--yes"])
    assert result.exit_code == 0, result.output

    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    allowed = list(theirs) + [e for e in _LEGACY_ENTRIES if e not in theirs]
    settings_path.write_text(json.dumps({"tools": {"allowed": allowed}}, indent=2) + "\n")

    manifest = json.loads(_manifest_path(repo_root).read_text())
    manifest["bob"]["tools"] = [
        {"path": ".bob/settings.json", "entry": e, "added": e not in theirs}
        for e in _LEGACY_ENTRIES
    ]
    _manifest_path(repo_root).write_text(json.dumps(manifest, indent=2) + "\n")


def test_agent_bob_leaves_an_existing_settings_file_byte_identical(
    agent_dir: Path,
) -> None:
    """The project file outranks the user's global one, so anything wfctl
    wrote here would override what the user approved for every repo."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    settings_path = _settings_path(repo_root)
    settings_path.parent.mkdir(parents=True)
    original = '{"tools": {"allowed": ["execute_command(npm test)"]}}\n'
    settings_path.write_text(original)

    result = runner.invoke(app, ["install-skills", "--agent", "bob", "--yes"])
    assert result.exit_code == 0, result.output

    assert settings_path.read_text() == original
    manifest = json.loads(_manifest_path(repo_root).read_text())
    assert "tools" not in manifest["bob"]


def test_agent_bob_does_not_create_a_settings_file(agent_dir: Path) -> None:
    """The old merge created `.bob/settings.json` in a repo that had none, and
    that file then outranked the user's global settings in every session."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills", "--agent", "bob", "--yes"])
    assert result.exit_code == 0, result.output
    assert not _settings_path(repo_root).exists()


def test_reinstall_removes_what_an_older_install_added_and_keeps_the_rest(
    agent_dir: Path,
) -> None:
    """Stopping the merge alone would leave every repo installed before it
    still overriding the user's global approvals. The receipts say which
    entries were wfctl's, and an entry the repo already had stays."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _record_legacy_install(repo_root, theirs=["execute_command(npm test)", "grep"])

    result = runner.invoke(app, ["install-skills", "--agent", "bob", "--yes"])
    assert result.exit_code == 0, result.output

    after = json.loads(_settings_path(repo_root).read_text())
    assert after == {"tools": {"allowed": ["execute_command(npm test)", "grep"]}}
    assert "Removed the tool approvals an older wfctl added" in result.output
    manifest = json.loads(_manifest_path(repo_root).read_text())
    assert "tools" not in manifest["bob"]


def test_a_second_reinstall_says_nothing_about_tool_approvals(agent_dir: Path) -> None:
    """The removal runs once. Announcing it on every later install would
    describe a change that did not happen."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _record_legacy_install(repo_root, theirs=[])
    runner.invoke(app, ["install-skills", "--agent", "bob", "--yes"])

    result = runner.invoke(app, ["install-skills", "--agent", "bob", "--yes"])
    assert result.exit_code == 0, result.output
    assert "tool approvals" not in result.output


def test_an_unparseable_file_keeps_its_receipts_for_the_next_install(
    agent_dir: Path,
) -> None:
    """Dropping the receipts with the file unreadable would leave wfctl's
    entries in it with nothing to say they were wfctl's, and from then on
    they would read as the user's."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _record_legacy_install(repo_root, theirs=[])
    settings_path = _settings_path(repo_root)
    good = settings_path.read_text()
    settings_path.write_text(good.rstrip() + ",\n")

    result = runner.invoke(app, ["install-skills", "--agent", "bob", "--yes"])
    assert result.exit_code == 0, result.output
    assert "the next install tries again" in result.output
    assert result.output.count("the next install tries again") == 1
    manifest = json.loads(_manifest_path(repo_root).read_text())
    assert len(manifest["bob"]["tools"]) == len(_LEGACY_ENTRIES)

    settings_path.write_text(good)
    result = runner.invoke(app, ["install-skills", "--agent", "bob", "--yes"])
    assert result.exit_code == 0, result.output
    assert json.loads(settings_path.read_text()) == {}


def test_an_unwritable_file_keeps_its_receipts_and_install_finishes(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The removal runs after the copy loop and before the manifest write. A
    write error raised from there left the copied files unrecorded, and
    `/start-session` runs this install unattended."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _record_legacy_install(repo_root, theirs=[])
    before = _settings_path(repo_root).read_text()

    def refuse(path: Path, settings: dict) -> None:
        raise PermissionError(13, "Permission denied", str(path))

    monkeypatch.setattr(cli, "_write_settings", refuse)
    result = runner.invoke(app, ["install-skills", "--agent", "bob", "--yes"])

    assert result.exit_code == 0, result.output
    assert result.output.count("the next install tries again") == 1
    assert _settings_path(repo_root).read_text() == before
    manifest = json.loads(_manifest_path(repo_root).read_text())
    assert len(manifest["bob"]["tools"]) == len(_LEGACY_ENTRIES)


def _point_receipts_outside(
    repo_root: Path, tmp_path_factory: pytest.TempPathFactory, form: str
) -> Path:
    """Point every receipt at a settings file outside the repo that holds the
    entries the receipts name, and return that file. `form` says whether the
    manifest spells the path as an absolute path or as a relative one that
    climbs out with `..`."""
    outside = tmp_path_factory.mktemp("outside") / "settings.json"
    outside.write_text(json.dumps({"tools": {"allowed": list(_LEGACY_ENTRIES)}}) + "\n")
    rel = str(outside) if form == "absolute" else os.path.relpath(outside, repo_root)
    manifest = json.loads(_manifest_path(repo_root).read_text())
    for receipt in manifest["bob"]["tools"]:
        receipt["path"] = rel
    _manifest_path(repo_root).write_text(json.dumps(manifest, indent=2) + "\n")
    return outside


@pytest.mark.parametrize("form", ["absolute", "traversal"])
def test_install_leaves_a_receipt_path_outside_the_repo_alone(
    agent_dir: Path, tmp_path_factory: pytest.TempPathFactory, form: str
) -> None:
    """The removal joined a receipt's path onto the repo root as written, so a
    hand-edited or committed manifest could make `install-skills --agent bob`
    rewrite a JSON file anywhere on disk. Install also runs unattended from
    `/start-session`, so nobody would see it happen."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _record_legacy_install(repo_root, theirs=[])
    outside = _point_receipts_outside(repo_root, tmp_path_factory, form)
    before = outside.read_text()

    result = runner.invoke(app, ["install-skills", "--agent", "bob", "--yes"])

    assert result.exit_code == 0, result.output
    assert outside.read_text() == before
    assert result.output.count("is recorded as a path outside this repo") == 1
    manifest = json.loads(_manifest_path(repo_root).read_text())
    assert "tools" not in manifest["bob"]


@pytest.mark.parametrize("form", ["absolute", "traversal"])
def test_uninstall_leaves_a_receipt_path_outside_the_repo_alone(
    agent_dir: Path, tmp_path_factory: pytest.TempPathFactory, form: str
) -> None:
    """Uninstall already refused an outside path for the files it deletes,
    but still followed one for the settings entries it removes."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _record_legacy_install(repo_root, theirs=[])
    outside = _point_receipts_outside(repo_root, tmp_path_factory, form)
    before = outside.read_text()

    result = runner.invoke(app, ["uninstall-skills", "--agent", "bob", "--yes"])

    assert result.exit_code == 0, result.output
    assert outside.read_text() == before
    assert result.output.count("is recorded as a path outside this repo") == 1


def test_agent_claude_leaves_the_bob_receipts_for_the_bob_install(
    agent_dir: Path,
) -> None:
    """A claude install does not rewrite the bob layer's manifest entry, so it
    has no reason to touch the file those receipts describe."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _record_legacy_install(repo_root, theirs=[])
    before = _settings_path(repo_root).read_text()

    result = runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    assert result.exit_code == 0, result.output

    assert _settings_path(repo_root).read_text() == before
    manifest = json.loads(_manifest_path(repo_root).read_text())
    assert len(manifest["bob"]["tools"]) == len(_LEGACY_ENTRIES)


def test_uninstall_removes_what_an_older_install_added(agent_dir: Path) -> None:
    """A repo can go straight from the older install to an uninstall, and the
    receipts are deleted with the manifest entry either way."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _record_legacy_install(repo_root, theirs=["execute_command(npm test)"])

    result = runner.invoke(app, ["uninstall-skills", "--agent", "bob", "--yes"])
    assert result.exit_code == 0, result.output
    after = json.loads(_settings_path(repo_root).read_text())
    assert after == {"tools": {"allowed": ["execute_command(npm test)"]}}
