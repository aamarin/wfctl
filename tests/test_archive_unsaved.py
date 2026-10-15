"""Tests for `wfctl archive unsaved`, which stops a removal that would lose work and saves the rest.

Every test builds real git repositories and worktrees under `tmp_path`. What is
under test is what git reports, and a mock of git would only restate our belief
about it.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from wfctl.cli import _print_removal_stop, app

runner = CliRunner()


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    )
    return done.stdout


@dataclass
class Repo:
    """A bare remote, a clone on trunk, and one linked worktree on a feature branch."""

    remote: Path
    main: Path
    worktree: Path
    branch: str


def make_repo(tmp_path: Path, branch: str = "40-feature") -> Repo:
    """Build the layout a removal runs in.

    The bare remote is part of it because "on no remote" is half of the unmerged
    commit check, and a repository without a remote cannot tell a pushed commit
    from an unpushed one. Trunk is `main` and is pushed, so `origin/main` exists
    to merge against.
    """
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", "-b", "main", str(remote))

    main = tmp_path / "main"
    _git(tmp_path, "init", "-b", "main", str(main))
    for key, val in (("user.email", "test@test.com"), ("user.name", "Test")):
        _git(main, "config", key, val)
    (main / "README.md").write_text("x\n")
    _git(main, "add", "README.md")
    _git(main, "commit", "-m", "init")
    _git(main, "remote", "add", "origin", str(remote))
    _git(main, "push", "-u", "origin", "main")

    worktree = tmp_path / "wt"
    _git(main, "worktree", "add", "-b", branch, str(worktree))
    return Repo(remote=remote, main=main, worktree=worktree, branch=branch)


def _untracked(worktree: Path) -> list[str]:
    out = _git(worktree, "ls-files", "--others", "--exclude-standard", "-z")
    return out.split("\0")[:-1]


def test_ls_files_lists_a_nested_repository_as_one_folder_entry(tmp_path: Path) -> None:
    """Research R5's copy rules assume git does not descend into a nested repository.

    If git listed the files inside, the folder rule (`copytree` of a `dir/` entry)
    would never fire and the nested `.git` would be left out of the save. This runs
    before any copy code exists, so a wrong assumption fails here and not in a
    removal that has already lost history.
    """
    repo = make_repo(tmp_path)
    nested = repo.worktree / "ref-clone"
    nested.mkdir()
    _git(nested, "init", "-b", "main")
    (nested / "a.txt").write_text("a\n")

    assert _untracked(repo.worktree) == ["ref-clone/"]


def test_ls_files_lists_an_untracked_symlink_as_a_path(tmp_path: Path) -> None:
    """A link is listed as itself and never expanded, including a link to a folder.

    The save recreates links with `os.readlink` instead of following them, which
    only works when git hands over the link's own path. The link to a folder is
    the case worth pinning, since it is the one a recursive listing would expand.
    """
    repo = make_repo(tmp_path)
    (repo.worktree / "real").mkdir()
    (repo.worktree / "real" / "f.txt").write_text("f\n")
    (repo.worktree / "to-file").symlink_to("../elsewhere.txt")
    (repo.worktree / "to-dir").symlink_to("real", target_is_directory=True)

    assert sorted(_untracked(repo.worktree)) == ["real/f.txt", "to-dir", "to-file"]


def test_archive_help_lists_unsaved() -> None:
    """The `archive` group exists and `unsaved` is reachable under it (FR-008)."""
    result = runner.invoke(app, ["archive", "--help"])

    assert result.exit_code == 0, result.output
    assert "unsaved" in result.output


def test_removal_stop_prints_paths_with_brackets_and_spaces_intact(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A path like `[draft] notes.md` is legal, and rich reads `[draft]` as a style tag.

    The stop block exists to name files and print a route a person pastes into a
    shell. A swallowed bracket names a file that isn't there, and a route with an
    unquoted space runs against the wrong path (research R13).
    """
    monkeypatch.setenv("NO_COLOR", "1")
    worktree = Path("/tmp/my wt [x]")

    _print_removal_stop(
        worktree,
        "40-feature",
        [("uncommitted edits:", ["[draft] notes.md"])],
    )

    out = capsys.readouterr().out
    assert "✗ removal stopped" in out
    assert "    [draft] notes.md" in out
    assert (
        "git worktree remove --force '/tmp/my wt [x]' && git branch -D 40-feature" in out
    )


def _unsaved(worktree: Path) -> Result:
    return runner.invoke(app, ["archive", "unsaved", str(worktree)])


def test_unstaged_edit_stops_removal_and_names_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An edit to a tracked file exists nowhere else, so removal has to stop (FR-009).

    The output has to name the file and print the manual route, since the route
    is the only way through and there is no override (FR-014).
    """
    monkeypatch.setenv("NO_COLOR", "1")
    repo = make_repo(tmp_path)
    (repo.worktree / "README.md").write_text("changed\n")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 1, result.output
    assert "removal stopped" in result.output
    assert "README.md" in result.output
    assert "git worktree remove --force" in result.output
    assert "git branch -D 40-feature" in result.output
    assert repo.worktree.is_dir()


def test_staged_edit_stops_removal_and_names_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A staged edit is as unsaved as an unstaged one.

    `git status` without `--porcelain` can hide this behind a different heading,
    and a check that only diffed the working tree would let it through.
    """
    monkeypatch.setenv("NO_COLOR", "1")
    repo = make_repo(tmp_path)
    (repo.worktree / "README.md").write_text("staged\n")
    _git(repo.worktree, "add", "README.md")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 1, result.output
    assert "README.md" in result.output
    assert repo.worktree.is_dir()


def test_failing_git_status_warns_and_lets_removal_go_ahead(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A check git can't answer warns by name and passes, so a worktree is never stuck on it.

    Without this an unrelated git error would strand every worktree, which is why
    the hook keeps its rule that only a refusal it can name stops a removal
    (FR-013, research R4). A corrupt index is the failure that `git status`
    reports and `git rev-list` doesn't.
    """
    monkeypatch.setenv("NO_COLOR", "1")
    repo = make_repo(tmp_path)
    git_dir = Path(_git(repo.worktree, "rev-parse", "--absolute-git-dir").strip())
    (git_dir / "index").write_bytes(b"not an index")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    assert "⚠" in result.output
    assert "uncommitted edits" in result.output
    assert "removal goes ahead" in result.output
