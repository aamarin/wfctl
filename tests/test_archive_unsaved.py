"""Tests for `wfctl archive unsaved`, which stops a removal that would lose work and saves the rest.

Every test builds real git repositories and worktrees under `tmp_path`. What is
under test is what git reports, and a mock of git would only restate our belief
about it.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from wfctl import _archive
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
    (FR-013, research R4). Only `git status` is made to fail. A corrupt index
    would fail the untracked listing too, and that one stops the removal.
    """
    monkeypatch.setenv("NO_COLOR", "1")
    repo = make_repo(tmp_path)
    real_git = _archive._git

    def failing_status(worktree: Path, *args: str) -> subprocess.CompletedProcess[str]:
        if args[0] == "status":
            return subprocess.CompletedProcess(args, 128, "", "fatal: boom\n")
        return real_git(worktree, *args)

    monkeypatch.setattr(_archive, "_git", failing_status)

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    assert "⚠" in result.output
    assert "uncommitted edits" in result.output
    assert "removal goes ahead" in result.output


def _commit(cwd: Path, name: str, text: str, message: str) -> None:
    (cwd / name).write_text(text)
    _git(cwd, "add", name)
    _git(cwd, "commit", "-m", message)


def test_unpushed_unmerged_commit_stops_removal_and_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A commit on no remote that trunk doesn't hold exists nowhere else (FR-010).

    The output names it as `<short sha> <subject>`, so the person can tell which
    commit to push or merge before they go the manual route.
    """
    monkeypatch.setenv("NO_COLOR", "1")
    repo = make_repo(tmp_path)
    _commit(repo.worktree, "new.txt", "new\n", "feat: only here")
    short = _git(repo.worktree, "rev-parse", "--short", "HEAD").strip()

    result = _unsaved(repo.worktree)

    assert result.exit_code == 1, result.output
    assert f"{short} feat: only here" in result.output
    assert repo.worktree.is_dir()


def test_pushed_commit_that_is_not_merged_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A commit on a remote survives the removal, so it doesn't need a stop.

    Without the remote scope, every branch with an open pull request would be
    stopped for work that is already safe (research R3, step 1).
    """
    monkeypatch.setenv("NO_COLOR", "1")
    repo = make_repo(tmp_path)
    _commit(repo.worktree, "new.txt", "new\n", "feat: pushed")
    _git(repo.worktree, "push", "origin", repo.branch)

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output


def test_squash_merged_branch_with_deleted_remote_branch_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After a squash merge the branch's own commits are on no remote and trunk has none of them.

    A squash commit has a different hash from every commit it replaced, so a check
    on hashes stops every removal in a repository that squash merges. The merge
    check asks whether merging would change trunk instead (SC-004).
    """
    monkeypatch.setenv("NO_COLOR", "1")
    repo = make_repo(tmp_path)
    _commit(repo.worktree, "new.txt", "new\n", "feat: the work")
    _commit(repo.main, "new.txt", "new\n", "feat: the work (#1)")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output


def test_squash_merged_branch_stops_when_trunk_later_changed_the_same_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The known limit of the merge check, pinned so it stays a decision and not a surprise.

    Once trunk edits the lines the squash brought in, merging the branch again
    conflicts, and git can't tell the work is already there. The removal stops and
    the manual route is the way through (SC-004, accepted on #600 item 2).
    """
    monkeypatch.setenv("NO_COLOR", "1")
    repo = make_repo(tmp_path)
    _commit(repo.worktree, "new.txt", "new\n", "feat: the work")
    _commit(repo.main, "new.txt", "new\n", "feat: the work (#1)")
    _commit(repo.main, "new.txt", "newer\n", "fix: later change")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 1, result.output
    assert "feat: the work" in result.output


def test_branch_that_would_conflict_with_trunk_stops_removal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A conflict is a refusal, since the branch holds changes trunk doesn't (FR-011)."""
    monkeypatch.setenv("NO_COLOR", "1")
    repo = make_repo(tmp_path)
    _commit(repo.worktree, "README.md", "branch\n", "feat: branch side")
    _commit(repo.main, "README.md", "trunk\n", "feat: trunk side")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 1, result.output
    assert "feat: branch side" in result.output


def test_missing_trunk_warns_by_name_and_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no trunk to merge against the check can't answer, so it says so and passes (FR-013).

    Renaming `main` leaves no `main`, `master`, `dev`, or `origin/HEAD` for
    `trunk_branch` to find.
    """
    monkeypatch.setenv("NO_COLOR", "1")
    repo = make_repo(tmp_path)
    _git(repo.main, "branch", "-m", "main", "elsewhere")
    _commit(repo.worktree, "new.txt", "new\n", "feat: only here")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    assert "couldn't check for unmerged commits" in result.output
    assert "no trunk branch found" in result.output


@pytest.fixture
def state_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The branch's state dir, pointed outside the worktree being removed."""
    d = tmp_path / "state"
    d.mkdir()
    monkeypatch.setenv("WFCTL_STATE_DIR", str(d))
    monkeypatch.setenv("NO_COLOR", "1")
    return d


def test_untracked_files_are_saved_at_their_relative_path_byte_for_byte(
    tmp_path: Path, state_dir: Path
) -> None:
    """The point of `unsaved/` is a plain copy back, so layout and bytes both have to survive (SC-002)."""
    repo = make_repo(tmp_path)
    (repo.worktree / "src").mkdir()
    (repo.worktree / "src" / "new_module.py").write_bytes(b"print('hi')\n\x00\xff")
    (repo.worktree / "notes.md").write_text("notes\n")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    assert "saved 2 files" in result.output
    assert (state_dir / "unsaved" / "src" / "new_module.py").read_bytes() == b"print('hi')\n\x00\xff"
    assert (state_dir / "unsaved" / "notes.md").read_text() == "notes\n"


def test_nested_repository_is_saved_whole_with_its_git_dir(
    tmp_path: Path, state_dir: Path
) -> None:
    """A clone inside the worktree is history as well as files, and the history is the part that can't be rebuilt (FR-019a)."""
    repo = make_repo(tmp_path)
    nested = repo.worktree / "ref-clone"
    nested.mkdir()
    _git(nested, "init", "-b", "main")
    (nested / "a.txt").write_text("a\n")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    assert (state_dir / "unsaved" / "ref-clone" / "a.txt").read_text() == "a\n"
    assert (state_dir / "unsaved" / "ref-clone" / ".git" / "HEAD").is_file()


def test_symlink_is_saved_as_a_link_with_the_same_target(
    tmp_path: Path, state_dir: Path
) -> None:
    """Following a link would copy whatever it points at, which may be outside the worktree (FR-019)."""
    repo = make_repo(tmp_path)
    (repo.worktree / "real").mkdir()
    (repo.worktree / "real" / "f.txt").write_text("f\n")
    (repo.worktree / "to-dir").symlink_to("real", target_is_directory=True)
    (repo.worktree / "to-file").symlink_to("../elsewhere.txt")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    saved = state_dir / "unsaved"
    assert (saved / "to-dir").is_symlink()
    assert os.readlink(saved / "to-dir") == "real"
    assert os.readlink(saved / "to-file") == "../elsewhere.txt"


def test_spec_dir_is_never_saved_even_when_git_does_not_ignore_it(
    tmp_path: Path, state_dir: Path
) -> None:
    """Spec files have their own destination, so saving them here would copy them twice (FR-018)."""
    repo = make_repo(tmp_path)
    spec = repo.worktree / "specs" / repo.branch
    spec.mkdir(parents=True)
    (spec / "spec.md").write_text("spec\n")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    assert "no unsaved files to keep" in result.output
    assert not (state_dir / "unsaved").exists()


def test_an_earlier_save_is_moved_aside_under_a_timestamp(
    tmp_path: Path, state_dir: Path
) -> None:
    """A second removal of the same branch must not destroy the first save (FR-020)."""
    repo = make_repo(tmp_path)
    (repo.worktree / "a.txt").write_text("first\n")
    assert _unsaved(repo.worktree).exit_code == 0
    (repo.worktree / "a.txt").write_text("second\n")

    assert _unsaved(repo.worktree).exit_code == 0

    assert (state_dir / "unsaved" / "a.txt").read_text() == "second\n"
    aside = [p for p in state_dir.glob("unsaved-*") if p.is_dir()]
    assert len(aside) == 1
    assert (aside[0] / "a.txt").read_text() == "first\n"


def test_failed_copy_raises_and_leaves_no_unsaved_or_staging_folder(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A half-written `unsaved/` under the canonical name reads as a complete save (FR-021)."""
    repo = make_repo(tmp_path)
    (repo.worktree / "a.txt").write_text("a\n")
    found = _archive.check(repo.worktree, None)

    def no_space(src: object, dst: object) -> None:
        raise OSError("No space left on device")

    monkeypatch.setattr(_archive.shutil, "copy2", no_space)

    with pytest.raises(_archive.SaveFailed, match="No space left on device"):
        _archive.save(found, state_dir, [])

    assert not (state_dir / "unsaved").exists()
    assert not (state_dir / "unsaved.staging").exists()


def test_failed_copy_stops_the_removal_and_prints_the_route(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The worktree holds the only copy, so a save that failed has to stop the removal (FR-023)."""
    repo = make_repo(tmp_path)
    (repo.worktree / "a.txt").write_text("a\n")

    def no_space(src: object, dst: object) -> None:
        raise OSError("No space left on device")

    monkeypatch.setattr(_archive.shutil, "copy2", no_space)

    result = _unsaved(repo.worktree)

    assert result.exit_code == 1, result.output
    assert "couldn't save unsaved files (No space left on device)" in result.output
    assert "nothing lost" in result.output
    assert "git worktree remove --force" in result.output


def test_nothing_to_save_creates_no_folder(tmp_path: Path, state_dir: Path) -> None:
    """An empty `unsaved/` would read as a save that found nothing it could name (FR-022)."""
    repo = make_repo(tmp_path)

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    assert "no unsaved files to keep" in result.output
    assert not (state_dir / "unsaved").exists()
    assert not (state_dir / "unsaved.staging").exists()


def test_output_prints_twenty_paths_then_how_many_more(
    tmp_path: Path, state_dir: Path
) -> None:
    """The count is the files saved and the list is capped so a nested clone can't flood the terminal (FR-023)."""
    repo = make_repo(tmp_path)
    for i in range(25):
        (repo.worktree / f"f{i:02}.txt").write_text("x\n")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    assert "saved 25 files" in result.output
    assert "    f19.txt" in result.output
    assert "    f20.txt" not in result.output
    assert "    and 5 more" in result.output


def test_untracked_file_and_uncommitted_edit_refuses_and_copies_nothing(
    tmp_path: Path, state_dir: Path
) -> None:
    """A refused removal leaves nothing half-copied, since the person will fix the edit and run it again (spec US2 scenario 5)."""
    repo = make_repo(tmp_path)
    (repo.worktree / "README.md").write_text("changed\n")
    (repo.worktree / "new.txt").write_text("new\n")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 1, result.output
    assert not (state_dir / "unsaved").exists()


def test_failed_untracked_listing_stops_the_removal(
    tmp_path: Path, state_dir: Path
) -> None:
    """If git can't list untracked files, going ahead would delete every one of them (#600 item 5).

    A corrupt index fails the listing for real. The removal stops, which is
    stricter than the edit check, because that one fails open on a lost edit and
    this one would lose files outright.
    """
    repo = make_repo(tmp_path)
    git_dir = Path(_git(repo.worktree, "rev-parse", "--absolute-git-dir").strip())
    (git_dir / "index").write_bytes(b"not an index")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 1, result.output
    assert "couldn't list untracked files" in result.output


def _declare_save_on_remove(repo: Repo, entries: object) -> None:
    """Commit a `wfctl.json` and a `.gitignore`, and push, so the tree is clean and safe.

    Both files have to be committed or the removal would save them as untracked
    files, and the commit has to be on a remote or the unmerged-commit check
    would stop the removal before any folder is copied.
    """
    import json

    (repo.worktree / "wfctl.json").write_text(json.dumps({"save_on_remove": entries}))
    (repo.worktree / ".gitignore").write_text("notes/\nresearch/\n.venv/\nspecs/\n")
    _git(repo.worktree, "add", "wfctl.json", ".gitignore")
    _git(repo.worktree, "commit", "-m", "chore: declare save_on_remove")
    _git(repo.worktree, "push", "origin", repo.branch)


def test_a_listed_ignored_folder_is_saved_and_an_unlisted_one_is_not(
    tmp_path: Path, state_dir: Path
) -> None:
    """Ignored folders are opt-in, since `.venv/` and `node_modules/` would swamp the save (FR-016, SC-003)."""
    repo = make_repo(tmp_path)
    _declare_save_on_remove(repo, ["notes/"])
    (repo.worktree / "notes").mkdir()
    (repo.worktree / "notes" / "idea.md").write_text("idea\n")
    (repo.worktree / ".venv").mkdir()
    (repo.worktree / ".venv" / "lib.py").write_text("junk\n")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    assert (state_dir / "unsaved" / "notes" / "idea.md").read_text() == "idea\n"
    assert not (state_dir / "unsaved" / ".venv").exists()


def test_a_listed_folder_that_does_not_exist_is_skipped_without_a_warning(
    tmp_path: Path, state_dir: Path
) -> None:
    """Most worktrees have no `research/`, and a warning on every one would be noise (FR-016)."""
    repo = make_repo(tmp_path)
    _declare_save_on_remove(repo, ["research/"])

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    assert "⚠" not in result.output
    assert "no unsaved files to keep" in result.output


def test_an_entry_outside_the_repository_is_skipped_with_a_warning(
    tmp_path: Path, state_dir: Path
) -> None:
    """A folder outside the repository isn't deleted by the removal, so skipping it loses nothing (FR-017)."""
    repo = make_repo(tmp_path)
    _declare_save_on_remove(repo, ["../elsewhere"])
    (tmp_path / "elsewhere").mkdir()
    (tmp_path / "elsewhere" / "x.txt").write_text("x\n")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    assert "'../elsewhere'" in result.output
    assert "outside the repository" in result.output
    assert "skipped" in result.output
    assert not (state_dir / "unsaved").exists()


def test_a_listed_folder_git_does_not_ignore_is_saved_once(
    tmp_path: Path, state_dir: Path
) -> None:
    """The same file is on the untracked list and inside the folder, and copying both makes `copytree` raise.

    That would stop every removal in the repository (#600 item 6). The folder copy
    already holds the file, so the file list drops it.
    """
    repo = make_repo(tmp_path)
    _declare_save_on_remove(repo, ["docs-draft/"])
    (repo.worktree / "docs-draft").mkdir()
    (repo.worktree / "docs-draft" / "a.md").write_text("a\n")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    assert "saved 1 file" in result.output
    assert (state_dir / "unsaved" / "docs-draft" / "a.md").read_text() == "a\n"


def test_listing_a_folder_that_holds_the_spec_dir_warns_and_saves_no_spec_files(
    tmp_path: Path, state_dir: Path
) -> None:
    """Spec files have their own destination, so listing `specs/` would save them twice (FR-018)."""
    repo = make_repo(tmp_path)
    _declare_save_on_remove(repo, ["specs/"])
    spec = repo.worktree / "specs" / repo.branch
    spec.mkdir(parents=True)
    (spec / "spec.md").write_text("spec\n")

    result = _unsaved(repo.worktree)

    assert result.exit_code == 0, result.output
    assert "'specs/'" in result.output
    assert "spec dir" in result.output
    assert not (state_dir / "unsaved").exists()


def test_an_orphan_branch_with_a_local_only_commit_stops_the_removal(tmp_path: Path) -> None:
    """The merge check refuses unrelated histories, and that refusal read as "can't answer".

    The removal then went ahead and the commit, which exists nowhere else, was lost.
    """
    repo = make_repo(tmp_path)
    _git(repo.worktree, "checkout", "--orphan", "40-orphan")
    _git(repo.worktree, "rm", "-rfq", ".")
    _commit(repo.worktree, "only-here.txt", "x\n", "add only-here.txt")

    found = _archive.check(repo.worktree, None)

    assert len(found.unmerged) == 1
    assert "add only-here.txt" in found.unmerged[0]
    assert not found.warnings


def test_the_stop_names_only_the_branch_s_commits_when_there_is_no_remote(tmp_path: Path) -> None:
    """`--not --remotes` removes nothing without a remote, so the list was trunk's whole history."""
    repo = make_repo(tmp_path)
    _git(repo.main, "remote", "remove", "origin")
    _commit(repo.main, "trunk-1.txt", "x\n", "add trunk-1.txt")
    _commit(repo.main, "trunk-2.txt", "x\n", "add trunk-2.txt")
    _git(repo.worktree, "merge", "-q", "main")
    _commit(repo.worktree, "feature.txt", "x\n", "add feature.txt")

    found = _archive.check(repo.worktree, None)

    assert [line.split(" ", 1)[1] for line in found.unmerged] == ["add feature.txt"]


def test_a_branch_merged_into_local_trunk_is_not_stopped_before_trunk_is_pushed(
    tmp_path: Path,
) -> None:
    """`workmux merge` merges into local trunk and then removes, before anything is pushed.

    Trunk resolves to origin/main, which does not have the merge yet, so the merge
    check saw a change and stopped a removal that loses nothing.
    """
    repo = make_repo(tmp_path)
    # A clone has origin/HEAD, which makes origin/main the trunk the check merges against.
    _git(repo.main, "remote", "set-head", "origin", "main")
    _commit(repo.worktree, "feature.txt", "x\n", "add feature.txt")
    _git(repo.main, "merge", "-q", "--no-ff", repo.branch)

    found = _archive.check(repo.worktree, None)

    assert found.unmerged == []
