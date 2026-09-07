"""`wfctl arch check` answers whether a record reached the change under review.

The question is the level-3 record format's only load-bearing one, and every way
it fails is silent: the file is on disk, the session reports success, and the
reviewer is shown nothing. Each test here is a state a review panel found the
first version of this check reporting wrongly.

The near-miss is `git ls-files --error-unmatch`, which is wrong twice — it reads
the index, and it exits 128 for a path outside the repository and for no
repository at all alike. Two of the four tests below are that command's two
mistakes, written as the outcomes they must not produce.
"""

import subprocess
from pathlib import Path

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


def test_a_committed_record_passes(tmp_path: Path, monkeypatch) -> None:
    """The state the whole feature is for, and the only one that exits 0 inside
    a repository."""
    repo = _repo(tmp_path / "r")
    path = _record(repo)
    subprocess.run(["git", "checkout", "-qb", "feat"], cwd=repo, check=True)
    subprocess.run(["git", "add", str(path)], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "r"], cwd=repo, check=True)
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["arch", "check", str(path)])

    assert result.exit_code == 0, result.output
    assert "committed on this branch" in result.output


def test_a_staged_record_is_not_a_committed_one(tmp_path: Path, monkeypatch) -> None:
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
    assert "never reached a commit" in result.output


def test_a_record_in_another_checkout_fails(tmp_path: Path, monkeypatch) -> None:
    """The case every path comparison passes. A second checkout is a git
    repository, its files are not ignored, and a commit there succeeds — and
    reaches no branch the change is opened from.
    """
    repo = _repo(tmp_path / "here")
    elsewhere = _repo(tmp_path / "elsewhere")
    path = _record(elsewhere)
    subprocess.run(["git", "add", str(path)], cwd=elsewhere, check=True)
    subprocess.run(["git", "commit", "-qm", "r"], cwd=elsewhere, check=True)
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["arch", "check", str(path)])

    assert result.exit_code == 1
    assert "outside this working tree" in result.output


def test_no_repository_is_not_a_failure(tmp_path: Path, monkeypatch) -> None:
    """There is no review to reach, so a record written here is not one written
    wrong. Exit 1 would refuse the one case the skill is told to proceed through
    — and `git ls-files` cannot tell this state from the one above, because both
    exit 128.
    """
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "r.md").write_text("# x\n")
    monkeypatch.chdir(plain)

    result = runner.invoke(app, ["arch", "check", "r.md"])

    assert result.exit_code == 0, result.output
    assert "No git repository here" in result.output
