"""The spec store: its layout, which spec dirs are not stored, and the store.

Every fixture here builds a bare remote and its clones under `tmp_path` with
real git, because each claim this module makes is a claim about what git does
to a shared checkout, and a stub would only repeat the claim back.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True
    ).stdout


def _clone(remote: Path, path: Path) -> Path:
    """A clone of `remote` at `path` that can commit.

    `git clone` copies no identity, and CI has no global one, so the committer
    is set here the way `init_git` sets it in `conftest.py`.
    """
    subprocess.run(["git", "clone", str(remote), str(path)], check=True, capture_output=True)
    for key, val in (("user.email", "test@test.com"), ("user.name", "Test")):
        _git(path, "config", key, val)
    return path


def _remote_and_clones(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A bare remote on `specs-trunk` and two clones of it, `here` and `there`.

    The remote starts with two folders, `100/spec.md` and `200/tasks.md`, the
    shape of two branches that have each stored once. Both clones track
    `origin/specs-trunk`, which is the layout a spec store has on two machines.
    """
    remote = tmp_path / "remote.git"
    subprocess.run(
        ["git", "init", "--bare", "--initial-branch=specs-trunk", str(remote)],
        check=True, capture_output=True,
    )
    there = _clone(remote, tmp_path / "there")
    for folder, name in (("100", "spec.md"), ("200", "tasks.md")):
        (there / folder).mkdir()
        (there / folder / name).write_text(f"{folder} as first stored\n")
    _git(there, "add", "-A")
    _git(there, "commit", "-m", "specs: first store")
    _git(there, "push", "-u", "origin", "specs-trunk")
    here = _clone(remote, tmp_path / "here")
    return remote, here, there


def _snapshot(folder: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(folder)): p.read_bytes()
        for p in sorted(folder.rglob("*")) if p.is_file()
    }


def test_merge_abort_leaves_another_branchs_edits_alone(tmp_path: Path) -> None:
    """The assumption `store-specs-merges-before-push.md` rests on, checked
    against git before any store code relies on it.

    The store aborts a conflicted merge in a checkout other branches are using.
    If `git merge --abort` reset their edits along with the conflict, a store
    in one folder would silently throw away another branch's unstored work,
    and the record's decision to merge rather than stop would have to be
    reopened.
    """
    _, here, there = _remote_and_clones(tmp_path)

    (here / "100" / "spec.md").write_text("100 as edited here\n")
    _git(here, "commit", "-am", "specs(100): here")
    (there / "100" / "spec.md").write_text("100 as edited there\n")
    _git(there, "commit", "-am", "specs(100): there")
    _git(there, "push")

    (here / "200" / "tasks.md").write_text("200 with a task ticked off\n")
    (here / "200" / "notes.md").write_text("200, not stored yet\n")
    before = _snapshot(here / "200")
    status_before = _git(here, "status", "--porcelain", "--", "200")

    _git(here, "fetch")
    merge = subprocess.run(
        ["git", "-C", str(here), "merge", "--no-edit", "@{u}"], capture_output=True, text=True
    )
    assert merge.returncode != 0, "the fixture was meant to conflict in 100/"
    assert (here / ".git" / "MERGE_HEAD").exists()

    _git(here, "merge", "--abort")

    assert not (here / ".git" / "MERGE_HEAD").exists()
    assert _snapshot(here / "200") == before
    assert _git(here, "status", "--porcelain", "--", "200") == status_before
    assert (here / "100" / "spec.md").read_text() == "100 as edited here\n"


@pytest.mark.parametrize("url", [
    "git@github.com:aamarin/wfctl-specs.git",
    "https://github.com/aamarin/wfctl-specs.git",
    "/Users/dev/project-specs.git",
    "../remote.git",
])
def test_a_store_in_a_test_refuses_a_remote_outside_the_tests_tmp_path(url: str) -> None:
    """A test that forgets `WFCTL_SPEC_DIR` would otherwise store into the
    developer's real spec store and push fixture commits to its remote.

    A local path outside `tmp_path` is refused as well as a network URL,
    because the developer's spec store can be a local bare repository too. A
    relative path is refused because git resolves it against the checkout,
    not against this process's working directory.
    """
    from wfctl import _spec_store

    with pytest.raises(pytest.fail.Exception, match="not under the test's tmp_path"):
        _spec_store._check_remote(url)


def test_a_store_in_a_test_reaches_a_remote_under_its_own_tmp_path(tmp_path: Path) -> None:
    """The other half of the guard: without it, a guard that refused every URL
    would pass the test above and fail every store test for the wrong reason."""
    from wfctl import _spec_store

    _spec_store._check_remote(str(tmp_path / "remote.git"))
    _spec_store._check_remote(f"file://{tmp_path / 'remote.git'}")


@pytest.mark.real_remote
def test_the_real_remote_check_lets_every_url_through() -> None:
    """Outside the suite the store pushes wherever the spec store's upstream
    points. A check left in the shipped code would refuse every real push."""
    from wfctl import _spec_store

    assert _spec_store._check_remote("git@github.com:aamarin/wfctl-specs.git") is None
