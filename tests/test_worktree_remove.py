"""Tests for `wfctl hook worktree-remove`, the command workmux runs before it deletes a worktree.

Every test builds a real repository and worktree, since what the hook decides
comes from what git reports.
"""
from __future__ import annotations

import shlex
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.test_archive_unsaved import Repo, make_repo
from tests.test_spec_copy import make_bare_worktree
from tests.test_spec_store import BRANCH, _git, _remote_files, _store_setup, _write
from tests.test_spec_store import _store as store_once
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
    """An exception from the dry-run copy-out reached the catch-all and threw the refusals away."""
    repo = make_repo(tmp_path)
    (repo.worktree / "README.md").write_text("edited, never committed\n")

    def boom(*_a: object, **_k: object) -> None:
        raise RuntimeError("cannot compare")

    monkeypatch.setattr("wfctl._spec_copy.copy_out", boom)

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


# --- Removal stores a spec dir that lives outside the worktree ----------------
#
# The fixtures are a real spec store with a bare remote, from
# `test_spec_store.py`, and a code repository beside it. Everything sits under
# `tmp_path`, and the worktree is passed by path, so the spec store is outside
# it without leaving the directory the remote guard in `conftest.py` allows.


def _removal(monkeypatch: pytest.MonkeyPatch, env: types.SimpleNamespace) -> tuple[int, str]:
    """The removal hook run the way `pre_remove` runs it, with the worktree and
    handle as arguments and the spec store pinned."""
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(env.here))
    monkeypatch.setenv("WFCTL_BRANCH", BRANCH)
    result = runner.invoke(app, ["hook", "worktree-remove", str(env.project), BRANCH])
    return result.exit_code, result.output


def test_removal_stores_what_the_branch_wrote_after_its_last_store(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-022 and User Story 2. Removal used to call a spec dir outside the
    worktree durable without asking git, so a review report written after the
    last store was left uncommitted and the output said it was safe."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md")
    assert store_once(env).outcome == "stored"
    _write(env.spec_dir, "reviews/panel-1.md")

    code, out = _removal(monkeypatch, env)

    sha = _git(env.here, "rev-parse", "--short", "HEAD").strip()
    assert code == 0, out
    assert f"✓ stored 1 file → origin/specs-trunk ({sha})" in out
    assert f"{BRANCH}/reviews/panel-1.md" in _remote_files(env.remote)
    assert "durable" not in out.lower()


def test_removal_of_a_stored_spec_dir_says_so_and_pushes_nothing(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """User Story 2, scenario 2. Most removals come after `/store-specs` ran,
    and one that committed or pushed again would add an empty commit to the
    spec store's history every time a worktree goes."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md")
    store_once(env)
    remote_head = _git(env.remote, "rev-parse", "specs-trunk")

    code, out = _removal(monkeypatch, env)

    assert code == 0, out
    assert "✓ spec dir already stored on origin/specs-trunk" in out
    assert _git(env.remote, "rev-parse", "specs-trunk") == remote_head


def test_a_failed_push_at_removal_warns_and_lets_removal_go_ahead(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-021. `store specs` exits 1 here, and the `pre_remove` hook stops a
    removal on any non-zero exit. The commit stays in the spec store on disk,
    so stopping the removal would protect nothing and strand the worktree."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md")
    env.remote.rename(env.remote.with_name("remote-away.git"))

    code, out = _removal(monkeypatch, env)

    assert code == 0, out
    assert "⚠ committed 1 file, not pushed — origin/specs-trunk is unreachable" in out
    assert _git(env.here, "log", "-1", "--format=%s").startswith("specs(359):")


def test_a_merge_refused_at_removal_warns_and_leaves_the_local_edit(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-021. Another branch's unstored edit to a file the remote changed
    stops the merge, which no retry of this removal can fix. The edit is that
    branch's work, so the store must leave it exactly as it was."""
    env = _store_setup(tmp_path)
    (env.there / "100" / "spec.md").write_text("100 as edited there\n")
    _git(env.there, "commit", "-am", "specs(100): there")
    _git(env.there, "push")
    (env.here / "100" / "spec.md").write_text("100, not stored yet\n")
    _write(env.spec_dir, "spec.md")

    code, out = _removal(monkeypatch, env)

    assert code == 0, out
    assert any(line.startswith("✗ ") for line in out.splitlines()), out
    assert (env.here / "100" / "spec.md").read_text() == "100, not stored yet\n"
    assert not (env.here / ".git" / "MERGE_HEAD").exists()


def test_a_lock_timeout_at_removal_warns_and_lets_removal_go_ahead(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-021. Another store holding the lock is the ordinary case when two
    worktrees are removed together, and the files wait in the spec store for
    the next store either way. The result is built by hand, since this test
    is about what removal does with a `locked` outcome and not about the lock."""
    from wfctl import _spec_store

    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md")
    found = _spec_store.layout(env.here, env.project)

    def locked(spec_dir: object, branch: str, repo_root: object) -> _spec_store.StoreResult:
        return _spec_store.StoreResult("locked", branch, str(spec_dir), False, found)

    monkeypatch.setattr(_spec_store, "store", locked)

    code, out = _removal(monkeypatch, env)

    assert code == 0, out
    assert locked(env.spec_dir, BRANCH, env.project).exit_code == 1
    assert any(line.startswith("✗ ") for line in out.splitlines()), out


def test_a_stored_spec_dir_still_leaves_the_untracked_files_saved(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The store and the save of untracked files both run on one removal. A
    later edit that moved the save under the copy-out branch would leave a
    spec store user's untracked files to be deleted with the worktree."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md")
    (env.project / "notes.md").write_text("notes\n")

    code, out = _removal(monkeypatch, env)

    assert code == 0, out
    assert "✓ stored 1 file → origin/specs-trunk" in out
    assert (state_dir / "unsaved" / "notes.md").read_text() == "notes\n"
    assert not (state_dir / "unsaved" / "specs").exists()


def test_a_store_that_raises_still_saves_the_untracked_files(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The store runs git and the network before the save. An exception it
    does not catch, such as a decode error on a file name, reached the hook's
    catch-all, which exits 0 without saving, and workmux then deleted the
    untracked files."""
    from wfctl import _spec_store

    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md")
    (env.project / "notes.md").write_text("notes\n")

    def raises(spec_dir: object, branch: str, repo_root: object) -> _spec_store.StoreResult:
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr(_spec_store, "store", raises)

    code, out = _removal(monkeypatch, env)

    assert code == 0, out
    assert f"⚠ couldn't store {env.spec_dir}" in out
    assert (state_dir / "unsaved" / "notes.md").read_text() == "notes\n"


def test_a_removal_run_in_the_main_checkout_goes_ahead(tmp_path: Path, state_dir: Path) -> None:
    """The main checkout is never removed, so its own spec dir is safe. The
    copy-out and the store once disagreed about it, and the hook stopped with
    a route ending in `git branch -D main`."""
    repo = make_repo(tmp_path)
    _spec(repo.main, **{"spec.md": "s\n"})

    result = runner.invoke(app, ["hook", "worktree-remove", str(repo.main), repo.branch])

    assert result.exit_code == 0, result.output
    assert "git worktree remove" not in result.output


def test_the_spec_dir_line_survives_a_path_containing_markup(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`[` is legal in a directory name, and rich reads it as a style tag. The
    line exists to name a location, so a silently truncated path is worse
    than no line at all."""
    repo = make_repo(tmp_path)
    outside = tmp_path / "outside[bold]root"
    spec_dir = outside / repo.branch
    _write(spec_dir, "spec.md")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(outside))

    code, out = _remove(repo)

    assert code == 0, out
    assert str(spec_dir) in out, "the path was mangled by markup parsing"


def test_a_plain_folder_outside_the_worktree_is_named_and_never_called_durable(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-022. A spec root that is no git repository survives the removal but
    is backed up nowhere. Removal used to call it durable, and without the path
    the line can't be told apart from a failed lookup."""
    repo = make_repo(tmp_path)
    outside = tmp_path / "outside-specs"
    spec_dir = outside / repo.branch
    _write(spec_dir, "spec.md")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(outside))

    code, out = _remove(repo)

    assert code == 0, out
    assert f"ℹ {spec_dir} is not backed up anywhere" in out
    assert "durable" not in out.lower()


def test_a_spec_dir_inside_the_worktree_is_copied_out_and_never_committed(
    tmp_path: Path, state_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Research R11. A spec dir inside the worktree is #40's copy-out. A commit
    there would find the code repository and land on the code's branch, so the
    spec store must never run for it."""
    from wfctl import _spec_store

    def no_store(*args: object) -> None:
        pytest.fail("removal ran the store for a spec dir inside the worktree")

    monkeypatch.setattr(_spec_store, "store", no_store)
    repo = make_repo(tmp_path)
    _spec(repo.worktree, **{"spec.md": "s\n"})

    code, out = _remove(repo)

    assert code == 0, out
    assert (repo.main / "specs" / "40-feature" / "spec.md").read_text() == "s\n"
