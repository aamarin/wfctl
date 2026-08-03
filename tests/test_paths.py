"""Tests for wfctl._paths — path resolution."""
from __future__ import annotations

from pathlib import Path

import pytest

from wfctl._paths import project_name, resolve_agent_dir, resolve_branch, resolve_spec_dir


def test_resolve_branch_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WFCTL_BRANCH", "999-my-feature")
    assert resolve_branch(tmp_path) == "999-my-feature"


def test_resolve_branch_from_git(repo_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WFCTL_BRANCH", raising=False)
    import subprocess
    subprocess.run(["git", "-C", str(repo_root), "checkout", "-b", "422-test-branch"],
                   check=True, capture_output=True)
    result = resolve_branch(repo_root)
    assert result == "422-test-branch"


def test_resolve_spec_dir_finds_prefix_match(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    specs = tmp_path / "specs"
    target = specs / "422-foo-bar"
    target.mkdir(parents=True)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))
    result = resolve_spec_dir("422-something", tmp_path)
    assert result == target


def test_resolve_spec_dir_exact_match(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    specs = tmp_path / "specs"
    target = specs / "422-something"
    target.mkdir(parents=True)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))
    result = resolve_spec_dir("422-something", tmp_path)
    assert result == target


def test_resolve_spec_dir_returns_none_when_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))
    result = resolve_spec_dir("422-missing", tmp_path)
    assert result is None


def _init_commit(repo_root: Path) -> None:
    """First commit on the repo_root fixture's unborn HEAD, giving it a real branch."""
    import subprocess

    (repo_root / "README.md").write_text("test\n")
    subprocess.run(["git", "-C", str(repo_root), "add", "README.md"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-m", "init"], check=True, capture_output=True
    )


def test_resolve_spec_dir_falls_back_to_epic_planning_branch(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Child issue worktree branched off the epic's planning branch (which
    carries specs/{feature}/) should resolve to that spec dir, even though the
    child branch's own issue number has no matching specs/ entry."""
    import subprocess

    _init_commit(repo_root)
    # The epic's planning branch carries specs/{feature}/ — that unmerged spec
    # commit is what marks it as a live parent rather than finished history.
    subprocess.run(
        ["git", "-C", str(repo_root), "checkout", "-b", "440-editable-table-row"],
        check=True, capture_output=True,
    )
    specs = repo_root / "specs" / "440-editable-table-row"
    specs.mkdir(parents=True)
    (specs / "tasks.md").write_text("x")
    subprocess.run(["git", "-C", str(repo_root), "add", "specs"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-m", "spec"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "checkout", "-b", "464-period-nav-pill"],
        check=True, capture_output=True,
    )
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)

    result = resolve_spec_dir("464-period-nav-pill", repo_root)
    assert result == specs


def test_resolve_spec_dir_ignores_unrelated_branches(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A same-named specs/ dir on a branch that isn't an ancestor must not match."""
    import subprocess

    _init_commit(repo_root)
    base = subprocess.run(
        ["git", "-C", str(repo_root), "branch", "--show-current"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()

    subprocess.run(
        ["git", "-C", str(repo_root), "checkout", "-b", "999-unrelated"],
        check=True, capture_output=True,
    )
    specs = repo_root / "specs" / "999-unrelated"
    specs.mkdir(parents=True)
    (specs / "tasks.md").write_text("x")
    subprocess.run(["git", "-C", str(repo_root), "add", "specs"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-m", "unrelated spec"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "checkout", base],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "checkout", "-b", "464-no-relation"],
        check=True, capture_output=True,
    )
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)

    result = resolve_spec_dir("464-no-relation", repo_root)
    assert result is None


def test_resolve_spec_dir_ignores_merged_sibling_branch(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A finished feature branch, merged into the trunk, is an ancestor of every
    branch cut afterward — and its specs/ dir is still in the tree. Inheriting it
    would report a completed story's pipeline on an unrelated new branch."""
    import subprocess

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    _init_commit(repo_root)
    trunk = git("branch", "--show-current")

    git("checkout", "-b", "install-config-workmux")
    specs = repo_root / "specs" / "install-config-workmux"
    specs.mkdir(parents=True)
    (specs / "tasks.md").write_text("x")
    git("add", "specs")
    git("commit", "-m", "spec")

    git("checkout", trunk)
    git("merge", "--no-ff", "-m", "merge", "install-config-workmux")
    git("checkout", "-b", "005-brand-new")
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)

    assert resolve_spec_dir("005-brand-new", repo_root) is None


def test_resolve_agent_dir_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    override = tmp_path / "custom-state"
    monkeypatch.setenv("WFCTL_STATE_DIR", str(override))
    result = resolve_agent_dir(tmp_path, "422-branch")
    assert result == override
    assert result.exists()


def test_resolve_agent_dir_creates_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    override = tmp_path / "nonexistent" / "deep" / "dir"
    monkeypatch.setenv("WFCTL_STATE_DIR", str(override))
    result = resolve_agent_dir(tmp_path, "422-branch")
    assert result.exists()


def test_resolve_agent_dir_xdg_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg"))
    repo = tmp_path / "myrepo"
    repo.mkdir()
    result = resolve_agent_dir(repo, "123-feature")
    assert result == tmp_path / "xdg" / "wfctl" / "myrepo" / "123-feature"
    assert result.exists()


def test_resolve_agent_dir_keys_on_main_checkout_not_worktree(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A linked worktree's directory is named after its branch, so keying state on
    it would fabricate a repo per branch and split one project's state across all
    of them. The main checkout's name is the project's name from anywhere."""
    import subprocess

    def git(*args: str, cwd: Path | None = None) -> str:
        return subprocess.run(
            ["git", "-C", str(cwd or repo_root), *args],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    _init_commit(repo_root)
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))

    wt = tmp_path / "wt" / "440-editable-table-row"
    git("worktree", "add", "-b", "440-editable-table-row", str(wt))

    from_main = resolve_agent_dir(repo_root, "440-editable-table-row")
    from_worktree = resolve_agent_dir(wt, "440-editable-table-row")

    assert from_main == from_worktree
    assert from_worktree.parent.name == repo_root.name


def test_project_name_from_a_worktree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The project's name, not the worktree's directory name.

    `--show-toplevel` returns the *worktree* path, so its basename is the branch
    handle. Deriving the name that way would write `window_prefix:
    '9-align-node-versions__'` into a committed file from a seed-once command.
    `--git-common-dir` points at the main checkout's .git from anywhere in the
    repo, which is what makes both call sites below agree.

    This is the regression guard the helper never had — it shipped with one
    caller and zero tests.
    """
    import subprocess

    # Not the `repo_root` fixture: this test needs the checkout directory to have
    # a name distinguishable from the worktree's, which is the whole point.
    repo_root = tmp_path / "myproject"
    repo_root.mkdir()
    subprocess.run(["git", "init", str(repo_root)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.email", "test@test.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.name", "Test"],
        check=True, capture_output=True,
    )
    _init_commit(repo_root)

    wt = tmp_path / "myproject" / "wt" / "9-align-node-versions"
    subprocess.run(
        ["git", "-C", str(repo_root), "worktree", "add", "-b", "9-align-node-versions", str(wt)],
        check=True, capture_output=True,
    )

    assert project_name(repo_root) == "myproject"
    assert project_name(wt) == "myproject"
    assert project_name(wt) != wt.name, "would be the branch handle, not the project"
