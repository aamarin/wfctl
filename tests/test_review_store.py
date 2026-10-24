"""Review records stay out of the spec store (SC-004, US2 scenario 5)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.test_review import commit, git, report, review_repo
from wfctl.cli import app


def _spec_store(tmp_path: Path, branch: str) -> Path:
    """A clone tracking `specs-trunk` on a bare remote under `tmp_path`, holding
    a spec dir for `branch` that hasn't been stored yet."""
    remote = tmp_path / "specs.git"
    subprocess.run(
        ["git", "init", "-q", "--bare", "--initial-branch=specs-trunk", str(remote)], check=True,
    )
    store = tmp_path / "specs"
    subprocess.run(["git", "clone", "-q", str(remote), str(store)], check=True,
                   capture_output=True)
    for key, val in (("user.email", "test@test.com"), ("user.name", "Test")):
        git(store, "config", key, val)
    git(store, "checkout", "-q", "-b", "specs-trunk")
    (store / "README.md").write_text("specs\n")
    git(store, "add", "README.md")
    git(store, "commit", "-q", "-m", "init")
    git(store, "push", "-q", "-u", "origin", "specs-trunk")
    (store / branch).mkdir()
    (store / branch / "spec.md").write_text("# spec\n")
    return store


def test_a_completed_review_puts_nothing_under_reviews_in_the_stored_specs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The panel used to write its reports into the spec dir, and `wfctl store
    specs` committed 376 of them to `specs-trunk` where nobody reads them. The
    records now live in the state directory, so the store never sees them,
    with no change to the store itself."""
    repo = review_repo(tmp_path, monkeypatch)
    store = _spec_store(tmp_path, "637-x")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(store))
    monkeypatch.chdir(repo)
    head = commit(repo, "a")
    runner = CliRunner()

    started = runner.invoke(app, ["review", "start", "security"])
    assert started.exit_code == 0, started.output
    reports = Path(started.output.splitlines()[1].removeprefix("reports: "))
    for rid in ("s1", "s2", "s3"):
        (reports / f"{rid}.md").write_text(report(head))
    checked = runner.invoke(app, ["review", "check", "security"])
    assert checked.exit_code == 0, checked.output

    stored = runner.invoke(app, ["store", "specs"])

    assert stored.exit_code == 0, stored.output
    committed = git(store, "show", "--name-only", "--format=", "HEAD").split()
    assert committed == ["637-x/spec.md"], stored.output
    assert not any("reviews/" in path for path in
                   git(store, "ls-tree", "-r", "--name-only", "HEAD").split())
    assert (reports / "s1.md").exists()
    assert not (store / "637-x" / "reviews").exists()
