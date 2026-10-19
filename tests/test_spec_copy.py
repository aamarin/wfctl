"""Tests for `wfctl._spec_copy` and `wfctl store specs`, which copy a worktree's spec files out before a removal."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.test_archive_unsaved import Repo, make_repo
from wfctl import _spec_copy
from wfctl.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _no_spec_dir_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """The destination is the main checkout's own spec root, so an inherited override would redirect it."""
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    monkeypatch.setenv("NO_COLOR", "1")


def _spec(repo: Repo, **files: str) -> Path:
    spec_dir = repo.worktree / "specs" / "40-feature"
    spec_dir.mkdir(parents=True)
    for name, text in files.items():
        (spec_dir / name).write_text(text)
    return spec_dir


def _dest(repo: Repo) -> Path:
    return repo.main / "specs" / "40-feature"


def test_copying_a_new_spec_dir_does_not_stop_the_removal(tmp_path: Path) -> None:
    """A finished copy is the one case where the worktree's spec dir is safe to delete."""
    repo = make_repo(tmp_path)
    spec_dir = _spec(repo, **{"spec.md": "s\n", "plan.md": "p\n"})

    result = _spec_copy.copy_out(spec_dir, repo.branch, repo.worktree)

    assert result.outcome == "copied"
    assert not result.stops_removal
    assert result.exit_code == 0
    assert (_dest(repo) / "plan.md").read_text() == "p\n"
    assert result.lines[0] == f"✓ copied 2 spec files → {_dest(repo)}"


def test_a_finished_copy_says_nothing_backs_it_up_and_never_says_durable(tmp_path: Path) -> None:
    """The copy lands in a folder git ignores, so calling it durable would promise a backup that isn't there (FR-031)."""
    repo = make_repo(tmp_path)
    spec_dir = _spec(repo, **{"spec.md": "s\n"})

    result = _spec_copy.copy_out(spec_dir, repo.branch, repo.worktree)

    assert "    nothing backs this copy up" in result.lines
    assert "durable" not in " ".join(result.lines).lower()


def test_identical_files_are_reported_as_already_copied(tmp_path: Path) -> None:
    """A second removal attempt must not stop on files the first one already copied."""
    repo = make_repo(tmp_path)
    spec_dir = _spec(repo, **{"spec.md": "s\n"})
    _spec_copy.copy_out(spec_dir, repo.branch, repo.worktree)

    result = _spec_copy.copy_out(spec_dir, repo.branch, repo.worktree)

    assert result.outcome == "already_copied"
    assert not result.stops_removal


def test_a_differing_file_stops_the_removal_and_shows_the_difference(tmp_path: Path) -> None:
    """Copying over a different file would destroy an edit made elsewhere, so a person decides (FR-024)."""
    repo = make_repo(tmp_path)
    spec_dir = _spec(repo, **{"spec.md": "mine\n"})
    _dest(repo).mkdir(parents=True)
    (_dest(repo) / "spec.md").write_text("theirs\n")

    result = _spec_copy.copy_out(spec_dir, repo.branch, repo.worktree)

    assert result.outcome == "differs"
    assert result.stops_removal
    assert result.exit_code == 1
    assert (_dest(repo) / "spec.md").read_text() == "theirs\n"
    text = "\n".join(result.lines)
    assert "spec.md" in text
    assert "-theirs" in text and "+mine" in text
    assert "wfctl store specs --overwrite" in text


def test_overwrite_replaces_the_differing_file(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    spec_dir = _spec(repo, **{"spec.md": "mine\n"})
    _dest(repo).mkdir(parents=True)
    (_dest(repo) / "spec.md").write_text("theirs\n")

    result = _spec_copy.copy_out(spec_dir, repo.branch, repo.worktree, overwrite=True)

    assert result.outcome == "copied"
    assert (_dest(repo) / "spec.md").read_text() == "mine\n"


def test_a_dry_run_reports_the_same_answer_and_writes_nothing(tmp_path: Path) -> None:
    """The hook asks before it copies, and must get the answer the real run would give (#600 item 3)."""
    repo = make_repo(tmp_path)
    spec_dir = _spec(repo, **{"spec.md": "mine\n", "plan.md": "p\n"})
    _dest(repo).mkdir(parents=True)
    (_dest(repo) / "spec.md").write_text("theirs\n")

    blocked = _spec_copy.copy_out(spec_dir, repo.branch, repo.worktree, dry_run=True)
    (_dest(repo) / "spec.md").write_text("mine\n")
    clear = _spec_copy.copy_out(spec_dir, repo.branch, repo.worktree, dry_run=True)

    assert blocked.stops_removal
    assert not clear.stops_removal and clear.outcome == "copied"
    assert not (_dest(repo) / "plan.md").exists()


def test_a_failed_copy_stops_the_removal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Going ahead after a failed copy would delete the only copy (FR-028)."""
    repo = make_repo(tmp_path)
    spec_dir = _spec(repo, **{"spec.md": "s\n"})

    def boom(*_args: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("wfctl._copy_out.apply", boom)

    result = _spec_copy.copy_out(spec_dir, repo.branch, repo.worktree)

    assert result.outcome == "copy_failed"
    assert result.stops_removal
    assert result.exit_code == 1
    assert "disk full" in result.lines[0]


def test_a_spec_file_that_cannot_be_read_stops_the_removal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Comparing the files reads every one, and an error there escaped to the hook's catch-all.

    The catch-all lets the removal go ahead, so an unreadable spec file meant the
    only copy was deleted unchecked (FR-028).
    """
    repo = make_repo(tmp_path)
    spec_dir = _spec(repo, **{"spec.md": "s\n"})

    def unreadable(*_args: object) -> None:
        raise OSError("permission denied")

    monkeypatch.setattr("wfctl._copy_out.plan", unreadable)

    result = _spec_copy.copy_out(spec_dir, repo.branch, repo.worktree)

    assert result.outcome == "copy_failed"
    assert result.stops_removal
    assert "permission denied" in result.lines[0]


def test_the_main_checkout_has_nothing_to_copy(tmp_path: Path) -> None:
    """Run in the main checkout the spec dir is already home, and the answer must not stop anything."""
    repo = make_repo(tmp_path)
    spec_dir = repo.main / "specs" / "40-feature"
    spec_dir.mkdir(parents=True)

    result = _spec_copy.copy_out(spec_dir, repo.branch, repo.main)

    assert result.outcome == "not_applicable"
    assert not result.stops_removal
    assert result.exit_code == 0


def test_a_spec_dir_outside_the_worktree_is_not_applicable(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    elsewhere = tmp_path / "elsewhere" / "40-feature"
    elsewhere.mkdir(parents=True)

    result = _spec_copy.copy_out(elsewhere, repo.branch, repo.worktree)

    assert result.outcome == "not_applicable"
    assert not result.inside
    assert not result.stops_removal


def test_not_applicable_inside_the_worktree_still_stops_the_removal() -> None:
    """The guard #359's research R6 asks for, if a later copy_out() skips the copy by mistake (FR-029)."""
    result = _spec_copy.CopyResult("not_applicable", Path("/wt/specs/x"), True)

    assert result.stops_removal
    assert result.exit_code == 0


def make_bare_worktree(tmp_path: Path, branch: str = "40-feature") -> Path:
    """A linked worktree of a bare repository, which has no main checkout."""
    bare = tmp_path / "project.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True)
    for key, val in (("user.email", "t@t.com"), ("user.name", "T")):
        subprocess.run(["git", "config", key, val], cwd=bare, check=True)
    tree = subprocess.run(
        ["git", "hash-object", "-t", "tree", "-w", "--stdin"],
        cwd=bare, input="", check=True, capture_output=True, text=True,
    ).stdout.strip()
    commit = subprocess.run(
        ["git", "commit-tree", tree, "-m", "init"],
        cwd=bare, check=True, capture_output=True, text=True,
    ).stdout.strip()
    subprocess.run(["git", "update-ref", "refs/heads/main", commit], cwd=bare, check=True)
    worktree = tmp_path / "wt"
    subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(worktree)], cwd=bare, check=True, capture_output=True
    )
    return worktree


def test_a_layout_with_no_main_checkout_sends_the_spec_dir_to_unsaved(tmp_path: Path) -> None:
    """Without a main checkout the spec files travel with the unsaved work and the removal goes ahead (FR-032)."""
    worktree = make_bare_worktree(tmp_path)
    spec_dir = worktree / "specs" / "40-feature"
    spec_dir.mkdir(parents=True)

    result = _spec_copy.copy_out(spec_dir, "40-feature", worktree)

    assert result.outcome == "to_unsaved"
    assert not result.stops_removal
    assert result.exit_code == 0


def test_no_spec_dir_does_not_stop_the_removal(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    result = _spec_copy.copy_out(None, repo.branch, repo.worktree)

    assert result.outcome == "no_spec_dir"
    assert not result.stops_removal
    assert result.exit_code == 0


def test_store_specs_command_copies_and_prints_the_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The command is the by-hand route the stop message names, so it must print what copy_out() returned."""
    repo = make_repo(tmp_path)
    _spec(repo, **{"spec.md": "s\n"})
    monkeypatch.chdir(repo.worktree)

    result = runner.invoke(app, ["store", "specs"])

    assert result.exit_code == 0, result.output
    assert "✓ copied 1 spec file" in result.output
    assert "nothing backs this copy up" in result.output
    assert (_dest(repo) / "spec.md").read_text() == "s\n"


def test_store_specs_command_exits_1_on_a_difference_until_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo(tmp_path)
    _spec(repo, **{"spec.md": "mine\n"})
    _dest(repo).mkdir(parents=True)
    (_dest(repo) / "spec.md").write_text("theirs\n")
    monkeypatch.chdir(repo.worktree)

    stopped = runner.invoke(app, ["store", "specs"])
    replaced = runner.invoke(app, ["store", "specs", "--overwrite"])

    assert stopped.exit_code == 1
    assert "holds different spec files" in stopped.output
    assert replaced.exit_code == 0, replaced.output
    assert (_dest(repo) / "spec.md").read_text() == "mine\n"


def test_a_spec_root_override_inside_the_worktree_sends_the_spec_dir_to_unsaved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`WFCTL_SPEC_DIR` pointing into the worktree made the destination the spec dir itself.

    The comparison then found every file already copied, the hook let the removal
    go ahead, and the worktree's only copy of the specs was deleted with it.
    """
    repo = make_repo(tmp_path)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(repo.worktree / "specs"))
    spec_dir = _spec(repo, **{"spec.md": "s\n"})

    result = _spec_copy.copy_out(spec_dir, repo.branch, repo.worktree)

    assert result.outcome == "to_unsaved"
    assert not result.stops_removal
