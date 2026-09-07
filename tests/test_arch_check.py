"""`wfctl arch check` answers whether a reviewer will read a record.

The question is the level-3 record format's only load-bearing one, and every way
it fails is silent: the file is on disk, the session reports success, and the
reviewer is shown nothing. Every test here is a state a review panel found some
version of this check reporting wrongly.

Three near-misses have been written into this command and each was wrong in its
own direction. `git ls-files --error-unmatch` reads the index, so a record
staged and never committed passes. `git cat-file -e HEAD:<path>` reads the path,
so a record edited after its commit passes. And both exit 128 for a path outside
the repository and for no repository at all alike, which is a failure and its
own exemption sharing one code. Most tests below are one of those mistakes,
written as the outcome it must not produce.
"""

import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def _repo(root: Path) -> Path:
    """A git repo with one commit on `main`, so a trunk exists to compare to."""
    root.mkdir(parents=True, exist_ok=True)
    for args in (
        ["init", "-q", "-b", "main"],
        ["config", "user.email", "t@example.com"],
        ["config", "user.name", "t"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)
    (root / "README.md").write_text("x\n")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
    return root


def _record(repo: Path, name: str = "1-x.md") -> Path:
    path = repo / "docs" / "architecture" / "design" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\nstatus: proposed\n---\n\n# x\n")
    return path


def _commit(repo: Path, path: Path, message: str = "r") -> None:
    subprocess.run(["git", "add", str(path)], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", message], cwd=repo, check=True)


def test_a_committed_record_on_a_branch_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The state the whole feature is for: committed, and added by the change a
    reviewer is about to open."""
    repo = _repo(tmp_path / "r")
    path = _record(repo)
    subprocess.run(["git", "checkout", "-qb", "feat"], cwd=repo, check=True)
    _commit(repo, path)
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["arch", "check", str(path)])

    assert result.exit_code == 0, result.output
    assert "this change adds it" in result.output


def test_a_staged_record_is_not_a_committed_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`git ls-files --error-unmatch` exits 0 here, which is why it cannot be the
    check. A commit that fails — a hook, a missing identity, a rejected
    signature — leaves the record staged, and `git push` moves commits, so the
    change opens without it while the session reported success.
    """
    repo = _repo(tmp_path / "r")
    path = _record(repo)
    subprocess.run(["git", "add", str(path)], cwd=repo, check=True)
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["arch", "check", str(path)])

    assert result.exit_code == 1
    assert "not committed as it stands" in result.output


def test_a_record_edited_after_its_commit_is_not_committed_as_it_stands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`git cat-file -e HEAD:<path>` exits 0 here, which is why it cannot be the
    check either. It answers about the path, and the path was committed; what a
    reviewer reads is the version in HEAD, not the one on disk.

    The same class as the staged case one step along, and the state that survived
    the first fix for it — `touched_on_this_branch` returns True precisely
    *because* the file is dirty, so the two checks cancelled.
    """
    repo = _repo(tmp_path / "r")
    path = _record(repo)
    subprocess.run(["git", "checkout", "-qb", "feat"], cwd=repo, check=True)
    _commit(repo, path)
    path.write_text("---\nstatus: proposed\n---\n\n# edited since\n")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["arch", "check", str(path)])

    assert result.exit_code == 1
    assert "not committed as it stands" in result.output


def test_a_record_in_another_checkout_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The case every path comparison passes. A second checkout is a git
    repository, its files are not ignored, and a commit there succeeds — and
    reaches no branch the change is opened from.
    """
    repo = _repo(tmp_path / "here")
    elsewhere = _repo(tmp_path / "elsewhere")
    path = _record(elsewhere)
    _commit(elsewhere, path)
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["arch", "check", str(path)])

    assert result.exit_code == 1
    assert "outside this working tree" in result.output


def test_the_trunk_branch_is_not_a_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A record committed on the trunk itself is read by anyone who opens the
    repo, and there is no change under review for it to be part of.
    `touched_on_this_branch` compares `trunk...HEAD`, which is empty here — so
    reading its answer as a verdict refuses a working setup.

    The caller in `arch none` never meets this: it asks while the file is still
    uncommitted, where `git status --porcelain` answers first. Committing before
    the question is what removes that shortcut.
    """
    repo = _repo(tmp_path / "r")
    path = _record(repo)
    _commit(repo, path)
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["arch", "check", str(path)])

    assert result.exit_code == 0, result.output
    assert "may be the trunk" in result.output


def test_no_repository_is_not_a_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """There is no review to reach, so a record written here is not one written
    wrong. Exit 1 would refuse the one case the skill is told to proceed through
    — and the commands named in this file's docstring cannot tell this state
    from the one above, because both exit 128.
    """
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "r.md").write_text("# x\n")
    monkeypatch.chdir(plain)

    result = runner.invoke(app, ["arch", "check", "r.md"])

    assert result.exit_code == 0, result.output
    assert "No git repository here" in result.output


def test_a_broken_repository_is_refused_not_exempted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A `.git` file naming a gitdir that is gone is a broken repository, not the
    absence of one — and git says so in a sentence containing "not a git
    repository", so the obvious substring exempts it and the check becomes a
    silent no-op inside a real project. A bare repo and `safe.directory`
    refusing the tree are the same shape.

    The discriminator is git's parenthetical, which it prints only when it really
    walked to the root and found nothing.
    """
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / ".git").write_text("gitdir: /nonexistent\n")
    (broken / "r.md").write_text("# x\n")
    monkeypatch.chdir(broken)

    result = runner.invoke(app, ["arch", "check", "r.md"])

    assert result.exit_code == 1
    assert "git cannot read this tree" in result.output
