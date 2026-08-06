"""Tests for `wfctl spec-root` — recording, showing, and removing the spec root."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()

MANIFEST = ".wf-skills-manifest.json"


def _git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    for key, val in (("user.email", "t@t.com"), ("user.name", "T")):
        subprocess.run(["git", "-C", str(path), "config", key, val],
                       check=True, capture_output=True)
    (path / "README.md").write_text("x\n")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "init"], check=True, capture_output=True)
    return path


def _manifest(path: Path) -> dict:
    """The manifest at `path`, or {} when there is none.

    `_save_manifest` deletes a manifest that has become empty, so "the key is
    gone" and "the file is gone" are the same outcome to a caller.
    """
    f = path / MANIFEST
    return json.loads(f.read_text()) if f.exists() else {}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)


def test_set_writes_the_manifest_and_reports_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-009, FR-010: recording is a command, and it says where it wrote."""
    repo = _git_repo(tmp_path / "proj")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))

    result = runner.invoke(app, ["spec-root", "~/Development/pfms-specs"])

    assert result.exit_code == 0, result.output
    assert _manifest(repo)["spec_root"] == "~/Development/pfms-specs"
    assert str(repo / MANIFEST) in result.output


def test_value_is_stored_verbatim_and_nothing_is_created(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-006: `~` survives to disk so the manifest stays portable across
    machines, and a root that does not exist yet is accepted — that case is the
    entire bug, so validating it would rebuild it."""
    repo = _git_repo(tmp_path / "proj")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))
    target = tmp_path / "does-not-exist"

    assert runner.invoke(app, ["spec-root", str(target)]).exit_code == 0
    assert not target.exists()

    assert runner.invoke(app, ["spec-root", "~/portable"]).exit_code == 0
    assert _manifest(repo)["spec_root"] == "~/portable"  # not expanded on write


def test_show_reports_root_and_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Four sources are possible, so naming the root without its origin leaves
    the reader unable to tell configuration from default."""
    repo = _git_repo(tmp_path / "proj")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))

    default = runner.invoke(app, ["spec-root"])
    assert default.exit_code == 0
    assert str(repo / "specs") in default.output
    assert "default" in default.output

    runner.invoke(app, ["spec-root", str(tmp_path / "configured")])
    configured = runner.invoke(app, ["spec-root"])
    assert str(tmp_path / "configured") in configured.output
    assert str(repo / MANIFEST) in configured.output

    monkeypatch.setenv("WFCTL_SPEC_DIR", str(tmp_path / "from-env"))
    env = runner.invoke(app, ["spec-root"])
    assert str(tmp_path / "from-env") in env.output
    assert "WFCTL_SPEC_DIR" in env.output


def test_unset_removes_the_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _git_repo(tmp_path / "proj")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))
    runner.invoke(app, ["spec-root", str(tmp_path / "configured")])

    result = runner.invoke(app, ["spec-root", "--unset"])

    assert result.exit_code == 0, result.output
    assert "spec_root" not in _manifest(repo)
    assert str(repo / "specs") in runner.invoke(app, ["spec-root"]).output


def test_path_with_unset_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contradictory: set it to what, or remove it? Refusing beats picking one."""
    repo = _git_repo(tmp_path / "proj")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))

    result = runner.invoke(app, ["spec-root", "/srv/specs", "--unset"])

    assert result.exit_code == 2, result.output
    assert not (repo / MANIFEST).exists(), "a rejected command writes nothing"


def test_unset_on_a_repo_with_no_manifest_says_so_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Removing what was never set is the state the user asked for — but
    `_save_manifest` drops an emptied manifest, so reporting a written file would
    send the reader looking for a path that is not there. Asserting only on the
    exit code let exactly that ship."""
    repo = _git_repo(tmp_path / "proj")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))
    gitignore_before = (repo / ".gitignore").exists()

    result = runner.invoke(app, ["spec-root", "--unset"])

    assert result.exit_code == 0
    assert "wrote" not in result.output
    assert "nothing to unset" in result.output
    assert not (repo / MANIFEST).exists()
    assert (repo / ".gitignore").exists() == gitignore_before, "a no-op creates no files"


def test_writing_the_gitignore_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`.gitignore` is tracked in most repos, and from a worktree the file being
    edited is in a directory the user is not standing in. An unannounced edit
    there lands in someone's next commit."""
    repo = _git_repo(tmp_path / "proj")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))

    first = runner.invoke(app, ["spec-root", "/srv/specs"])
    assert "gitignored" in first.output
    assert str(repo / ".gitignore") in first.output

    # Idempotent: the second run changes nothing, so it claims nothing.
    second = runner.invoke(app, ["spec-root", "/srv/other"])
    assert "gitignored" not in second.output


def test_setting_from_a_worktree_writes_the_main_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-010: the worktree's manifest is gitignored and dies with the worktree,
    so writing there records a setting that silently evaporates — the failure
    mode this feature exists to remove."""
    main = _git_repo(tmp_path / "proj")
    wt = main / "wt" / "18-spec-root"
    subprocess.run(
        ["git", "-C", str(main), "worktree", "add", "-b", "18-spec-root", str(wt)],
        check=True, capture_output=True,
    )
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(wt))

    result = runner.invoke(app, ["spec-root", str(tmp_path / "shared-specs")])

    assert result.exit_code == 0, result.output
    assert _manifest(main)["spec_root"] == str(tmp_path / "shared-specs")
    assert not (wt / MANIFEST).exists(), "must not write the ephemeral copy"
    assert str(main / MANIFEST) in result.output, "a write elsewhere is never silent"


def test_setting_preserves_other_manifest_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The manifest is shared with the installer; this command owns one key."""
    repo = _git_repo(tmp_path / "proj")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))
    (repo / MANIFEST).write_text(json.dumps({
        "base": {"repo": "x", "ref": "main", "commit": "c", "items": []},
        "tracker": "github",
    }))

    runner.invoke(app, ["spec-root", "/srv/specs"])

    after = _manifest(repo)
    assert after["tracker"] == "github"
    assert after["base"]["commit"] == "c"
    assert after["spec_root"] == "/srv/specs"
