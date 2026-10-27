"""A group's review rounds belong to the issue a branch names, not to the branch name.

Before this, `wfctl review start` counted run folders under a state folder named
after the full branch. Renaming the branch with `git branch -m` gave an agent at
the cap an empty folder and three more rounds, and nothing recorded that the cap
was passed (#666). These tests rename a real branch, since a test that never
renames can't see the failure.

`WFCTL_STATE_DIR` stays unset because it pins one folder for every branch, which
is the one setup where the bug can't happen.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from tests.test_review import commit, git, review_repo
from wfctl import _paths, _review
from wfctl.cli import app


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = review_repo(tmp_path, monkeypatch)
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.chdir(repo)
    git(repo, "branch", "-m", "626-review-round-cap")
    commit(repo, "a")
    return repo


def run(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def start_rounds(n: int) -> None:
    for _ in range(n):
        assert run("review", "start", "security").exit_code == 0


def test_a_rename_keeps_the_round_count(repo: Path) -> None:
    """The reproduction from #666: security is at 3 of 3, then the branch is renamed."""
    start_rounds(3)
    git(repo, "branch", "-m", "626-round-cap")

    result = run("review", "start", "security")

    assert result.exit_code == 1, result.output
    assert "security has run 3 of 3 rounds" in result.output


def test_a_second_branch_on_the_same_issue_shares_the_count(repo: Path) -> None:
    """A stacked PR for issue 626 with another slug is not a way past the cap.
    The cost is that it starts with the rounds the first branch used."""
    start_rounds(3)
    git(repo, "checkout", "-q", "-b", "626-hotfix-typo")
    commit(repo, "b")

    result = run("review", "start", "security")

    assert result.exit_code == 1, result.output


def test_another_issue_starts_its_own_count(repo: Path) -> None:
    start_rounds(3)
    git(repo, "checkout", "-q", "-b", "627-unrelated")
    commit(repo, "b")

    result = run("review", "start", "security")

    assert result.exit_code == 0, result.output
    assert "run 001 · round 1 of 3" in result.output


def test_a_rename_keeps_the_sign_off(repo: Path) -> None:
    """The sign-off is what lets a branch past the cap. If the count survived a
    rename and the sign-off didn't, the user would have to sign off twice."""
    start_rounds(3)
    head = git(repo, "rev-parse", "HEAD")
    _review.sign_off(_paths.resolve_review_dir(repo, "626-review-round-cap"), head)
    git(repo, "branch", "-m", "626-round-cap")

    result = run("review", "start", "security")

    assert result.exit_code == 0, result.output
    assert f"the sign-off at {head[:7]} covers every commit left to review" in result.output


def test_a_branch_naming_no_issue_keeps_its_own_state(repo: Path) -> None:
    """`main` and similar branches carry no key to share, so they stay keyed by name."""
    assert _paths.resolve_review_dir(repo, "scratch") == _paths.resolve_agent_dir(repo, "scratch")


def test_the_issue_folder_cannot_collide_with_a_branch_folder(repo: Path) -> None:
    """Branch folders sit beside the issue folder under the project. git refuses a
    ref name that starts with a dot, so no branch can take the issue folder's name."""
    shared = _paths.resolve_review_dir(repo, "626-review-round-cap", create=False)
    holder = shared.parent

    assert holder.name.startswith(".")
    assert holder.parent == _paths.project_state_dir(repo)
    refused = subprocess.run(
        ["git", "check-ref-format", f"refs/heads/{holder.name}"], cwd=repo,
    )
    assert refused.returncode != 0


def test_the_state_override_still_pins_one_folder(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WFCTL_STATE_DIR", str(tmp_path / "pinned"))

    assert _paths.resolve_review_dir(repo, "626-x") == tmp_path / "pinned"
