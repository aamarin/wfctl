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


def linked_worktree(repo: Path, branch: str, *, tracker: bool = True) -> Path:
    """A linked worktree on `branch`, as `workmux add` leaves one. The manifest is
    what tells wfctl the repository has a tracker, so the refusal applies."""
    wt = repo.parent / "wt"
    git(repo, "worktree", "add", "-q", "-b", branch, str(wt))
    if tracker:
        (wt / ".wf-skills-manifest.json").write_text('{"tracker": "github"}')
    return wt


def test_a_worktree_branch_naming_no_issue_cannot_start_a_round(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The bypass the issue-keyed folder leaves: `git branch -m 626-x scratch` names
    no issue, so the count would restart in the branch's own empty folder. A
    worktree needs an issue to start a session, and a round needs one too."""
    monkeypatch.chdir(linked_worktree(repo, "scratch"))

    result = run("review", "start", "security")

    assert result.exit_code == 1, result.output
    assert "'scratch' names no issue" in result.output
    assert "git branch -m <key>-scratch" in result.output


def test_a_worktree_branch_naming_an_issue_can_start_a_round(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(linked_worktree(repo, "628-other"))

    assert run("review", "start", "security").exit_code == 0


def test_a_repository_with_no_tracker_is_never_asked_for_an_issue(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`wfctl start` makes the same exemption, since a repo that declined a tracker
    has no issues to name."""
    monkeypatch.chdir(linked_worktree(repo, "scratch", tracker=False))

    assert run("review", "start", "security").exit_code == 0


def test_the_main_checkout_can_start_a_round_on_any_branch(repo: Path) -> None:
    git(repo, "branch", "-m", "scratch")

    assert run("review", "start", "security").exit_code == 0


def test_a_detached_worktree_is_refused_with_a_remedy_that_works(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A detached HEAD has no branch to rename, so `git branch -m` fails there.
    `resolve_branch` also hands back the short hash, and an all-digit hash parses
    as an issue key, so the detached test has to run before the key test."""
    wt = linked_worktree(repo, "628-other")
    git(wt, "checkout", "-q", "--detach")
    monkeypatch.chdir(wt)

    result = run("review", "start", "security")

    assert result.exit_code == 1, result.output
    assert "detached HEAD" in result.output
    assert "git switch -c <key>-<slug>" in result.output
    assert "git branch -m" not in result.output


def test_the_state_override_exempts_a_keyless_worktree_branch(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The override pins one folder for every branch, so a rename can't reset the
    count there and the refusal has nothing to protect."""
    monkeypatch.chdir(linked_worktree(repo, "scratch"))
    monkeypatch.setenv("WFCTL_STATE_DIR", str(tmp_path / "pinned"))

    assert run("review", "start", "security").exit_code == 0
