"""Tests for `wfctl hook worktree-remove`, the command workmux runs before it deletes a worktree.

Every test builds a real repository and worktree, since what the hook decides
comes from what git reports.
"""
from __future__ import annotations

import shlex
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.test_archive_unsaved import Repo, make_repo
from tests.test_spec_store import make_bare_worktree
from wfctl.cli import app

runner = CliRunner()


@pytest.fixture
def state_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The branch's state dir, outside the worktree being removed."""
    d = tmp_path / "state"
    d.mkdir()
    monkeypatch.setenv("WFCTL_STATE_DIR", str(d))
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    monkeypatch.delenv("WM_WORKTREE_PATH", raising=False)
    monkeypatch.delenv("WM_HANDLE", raising=False)
    return d


def _spec(worktree: Path, **files: str) -> Path:
    spec_dir = worktree / "specs" / "40-feature"
    spec_dir.mkdir(parents=True)
    for name, text in files.items():
        (spec_dir / name).write_text(text)
    return spec_dir


def _remove(repo: Repo, *extra: str, name: str = "worktree-remove") -> tuple[int, str]:
    args = ["hook", name] if name == "worktree-remove" else [name]
    result = runner.invoke(app, [*args, str(repo.worktree), repo.branch, *extra])
    return result.exit_code, result.output


def test_a_clean_worktree_copies_its_spec_files_and_saves_untracked_files(
    tmp_path: Path, state_dir: Path
) -> None:
    """The ordinary removal: both copies are made and the hook lets workmux go on (FR-001)."""
    repo = make_repo(tmp_path)
    _spec(repo.worktree, **{"spec.md": "s\n"})
    (repo.worktree / "notes.md").write_text("notes\n")

    code, out = _remove(repo)

    assert code == 0, out
    assert (repo.main / "specs" / "40-feature" / "spec.md").read_text() == "s\n"
    assert (state_dir / "unsaved" / "notes.md").read_text() == "notes\n"
    assert "✓ copied 1 spec file" in out
    assert "✓ saved" in out


def test_differing_spec_files_and_an_uncommitted_edit_are_both_listed(
    tmp_path: Path, state_dir: Path
) -> None:
    """A person who fixes the first finding and reruns to meet the second has been refused twice."""
    repo = make_repo(tmp_path)
    _spec(repo.worktree, **{"spec.md": "mine\n", "plan.md": "p\n"})
    dest = repo.main / "specs" / "40-feature"
    dest.mkdir(parents=True)
    (dest / "spec.md").write_text("theirs\n")
    (repo.worktree / "README.md").write_text("edited\n")
    (repo.worktree / "notes.md").write_text("notes\n")

    code, out = _remove(repo)

    assert code == 1
    assert "uncommitted edits:" in out and "README.md" in out
    assert "holds different spec files:" in out
    assert "wfctl store specs --overwrite" in out
    assert "git worktree remove --force" in out
    assert not (dest / "plan.md").exists(), "a stopped removal must copy nothing (FR-002)"
    assert not (state_dir / "unsaved").exists()


def test_an_uncommitted_edit_alone_copies_no_spec_files(tmp_path: Path, state_dir: Path) -> None:
    """Copying before the other checks run would leave files behind for a removal that never happened (FR-002)."""
    repo = make_repo(tmp_path)
    _spec(repo.worktree, **{"spec.md": "s\n"})
    (repo.worktree / "README.md").write_text("edited\n")

    code, out = _remove(repo)

    assert code == 1
    assert "wfctl store specs --overwrite" not in out, "the keep route is for differing spec files only"
    assert not (repo.main / "specs").exists()


def test_a_layout_with_no_main_checkout_saves_the_spec_dir_under_unsaved(
    tmp_path: Path, state_dir: Path
) -> None:
    """With nowhere to copy to, the spec files travel with the unsaved work (FR-032)."""
    worktree = make_bare_worktree(tmp_path)
    _spec(worktree, **{"spec.md": "s\n"})
    repo = Repo(remote=tmp_path, main=tmp_path, worktree=worktree, branch="40-feature")

    code, out = _remove(repo)

    assert code == 0, out
    assert (state_dir / "unsaved" / "specs" / "40-feature" / "spec.md").read_text() == "s\n"


@pytest.mark.parametrize("name", ["archive-specs", "archive-story"])
def test_the_former_names_do_the_same_work(tmp_path: Path, state_dir: Path, name: str) -> None:
    """Repositories whose `.workmux.yaml` predates the rename must still be able to remove a worktree."""
    repo = make_repo(tmp_path)
    _spec(repo.worktree, **{"spec.md": "s\n"})
    (repo.worktree / "notes.md").write_text("notes\n")

    code, out = _remove(repo, name=name)

    assert code == 0, out
    assert (repo.main / "specs" / "40-feature" / "spec.md").is_file()
    assert (state_dir / "unsaved" / "notes.md").is_file()
    assert ("invoked as `archive-story`" in out) == (name == "archive-story")
    assert "wfctl hook worktree-remove" in out or name == "archive-specs"


def test_archive_specs_prints_no_notice(tmp_path: Path, state_dir: Path) -> None:
    repo = make_repo(tmp_path)

    _, out = _remove(repo, name="archive-specs")

    assert "invoked as" not in out


def test_an_unexpected_error_warns_and_lets_the_removal_go_on(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A bug here must not strand a worktree, since a failing hook is what aborts a removal."""
    repo = make_repo(tmp_path)

    def boom(*_a: object, **_k: object) -> None:
        raise RuntimeError("disk on fire")

    monkeypatch.setattr("wfctl._archive.check", boom)

    code, out = _remove(repo)

    assert code == 0
    assert "worktree-remove failed (disk on fire) — continuing so the removal is not blocked" in out


def test_a_state_dir_that_cannot_be_created_stops_the_removal(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Creating the state dir ran outside the save's `try`, so a failure there fell into the catch-all.

    The catch-all exits 0, which let the removal delete untracked files that had
    not been saved.
    """
    repo = make_repo(tmp_path)
    (repo.worktree / "notes.md").write_text("notes\n")

    def unwritable(*_a: object, **_k: object) -> Path:
        raise OSError("read-only file system")

    monkeypatch.setattr("wfctl.cli.resolve_agent_dir", unwritable)

    code, out = _remove(repo)

    assert code == 1, out
    assert "couldn't save unsaved files (read-only file system)" in out
    assert "continuing so the removal is not blocked" not in out


def test_a_manifest_that_will_not_parse_does_not_skip_the_checks(
    tmp_path: Path, state_dir: Path
) -> None:
    """Looking up the spec dir reads the manifest, and it raised before any check ran.

    The catch-all exits 0, so a worktree with an uncommitted edit was removed
    unchecked because of a lookup the checks don't need.
    """
    repo = make_repo(tmp_path)
    (repo.worktree / ".wf-skills-manifest.json").write_text("{not json")
    (repo.worktree / "README.md").write_text("edited, never committed\n")

    code, out = _remove(repo)

    assert code == 1, out
    assert "couldn't find the spec dir" in out
    assert "uncommitted edits:" in out
    assert "README.md" in out


def test_a_comparison_that_fails_is_listed_beside_the_refusals_already_found(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An exception from the dry-run store reached the catch-all and threw the refusals away."""
    repo = make_repo(tmp_path)
    (repo.worktree / "README.md").write_text("edited, never committed\n")

    def boom(*_a: object, **_k: object) -> None:
        raise RuntimeError("cannot compare")

    monkeypatch.setattr("wfctl._spec_store.store", boom)

    code, out = _remove(repo)

    assert code == 1, out
    assert "uncommitted edits:" in out
    assert "couldn't compare spec files:" in out
    assert "cannot compare" in out


def test_a_non_git_checkout_still_exits_zero(
    state_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`get_repo_root` raises SystemExit, which `except Exception` alone does not catch."""

    def not_a_repo() -> Path:
        raise SystemExit("wfctl: not a git repository")

    monkeypatch.setattr("wfctl.cli.get_repo_root", not_a_repo)

    result = runner.invoke(app, ["hook", "worktree-remove"])

    assert result.exit_code == 0
    assert "worktree-remove failed" in result.output


def test_a_missing_worktree_is_reported_and_does_not_fail(tmp_path: Path, state_dir: Path) -> None:
    result = runner.invoke(app, ["hook", "worktree-remove", str(tmp_path / "gone")])

    assert result.exit_code == 0
    assert "no worktree" in result.output


def test_explicit_arguments_win_over_the_environment(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """workmux passes both positionally, and they must beat `WM_*` and the current directory."""
    repo = make_repo(tmp_path)
    (tmp_path / "other").mkdir()
    other = make_repo(tmp_path / "other")
    _spec(repo.worktree, **{"spec.md": "s\n"})
    monkeypatch.setenv("WM_WORKTREE_PATH", str(other.worktree))
    monkeypatch.setenv("WM_HANDLE", "999-other")

    code, out = _remove(repo)

    assert code == 0, out
    assert (repo.main / "specs" / "40-feature" / "spec.md").is_file()


def test_the_manual_route_survives_a_path_with_spaces(tmp_path: Path, state_dir: Path) -> None:
    """The route is meant to be pasted, so a space in the path has to arrive as one argument."""
    spaced = tmp_path / "a dir with spaces"
    spaced.mkdir()
    repo = make_repo(spaced)
    (repo.worktree / "README.md").write_text("edited\n")

    _, out = _remove(repo)

    line = next(ln for ln in out.splitlines() if "git worktree remove" in ln)
    parsed = shlex.split(line.split("git worktree remove --force", 1)[1].split("&&")[0])
    assert parsed == [str(repo.worktree)]


def test_a_path_with_brackets_is_printed_intact(tmp_path: Path, state_dir: Path) -> None:
    """`[draft]` is legal in a file name, and rich would read it as a style tag and drop it."""
    repo = make_repo(tmp_path)
    (repo.worktree / "[draft] notes.md").write_text("n\n")

    code, out = _remove(repo)

    assert code == 0, out
    assert "[draft] notes.md" in out


def test_a_numbered_archive_from_an_earlier_removal_is_left_alone(
    tmp_path: Path, state_dir: Path
) -> None:
    """The old `archive/` folder is history now, and nothing reads or rewrites it (FR-033)."""
    repo = make_repo(tmp_path)
    old = state_dir / "archive"
    old.mkdir()
    (old / "2-spec.md").write_text("old\n")

    code, _ = _remove(repo)

    assert code == 0
    assert (old / "2-spec.md").read_text() == "old\n"


def test_neither_former_name_is_listed_but_the_hook_group_lists_worktree_remove() -> None:
    """The aliases are a compatibility shim, not a second supported spelling (FR-008)."""
    top = runner.invoke(app, ["--help"]).output
    hook = runner.invoke(app, ["hook", "--help"]).output

    assert "archive-specs" not in top
    assert "archive-story" not in top
    assert "worktree-remove" in hook
