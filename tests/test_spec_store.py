"""The spec store: its layout, which spec dirs are not stored, and the store.

Every fixture here builds a bare remote and its clones under `tmp_path` with
real git, because each claim this module makes is a claim about what git does
to a shared checkout, and a stub would only repeat the claim back.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.conftest import git_repo
from wfctl import _spec_store


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


def _worktree(project: Path, path: Path, *options: str, start: str = "") -> Path:
    _git(project, "worktree", "add", *options, str(path), *([start] if start else []))
    return path


def _project_with_remote(tmp_path: Path) -> tuple[Path, Path]:
    """The code repository and the bare remote its spec store pushes to.

    The remote is the one `_remote_and_clones` builds, with `specs-trunk`
    already holding two folders, and the code repository has it as `origin`,
    which is pfms's shape: the spec store is a worktree of the code
    repository, on a branch that tracks `origin/specs-trunk`.
    """
    remote, _, _ = _remote_and_clones(tmp_path)
    project = git_repo(tmp_path / "project")
    _git(project, "remote", "add", "origin", str(remote))
    _git(project, "fetch", "origin")
    return project, remote


def test_a_worktree_tracking_the_spec_branch_is_a_store(tmp_path: Path) -> None:
    """pfms's layout, and the one kind the store pushes from. The upstream is
    carried so the output can name `origin/specs-trunk` without asking again."""
    project, _ = _project_with_remote(tmp_path)
    store = _worktree(project, tmp_path / "project-specs", "-b", "specs-trunk",
                      start="origin/specs-trunk")

    found = _spec_store.layout(store, project)

    assert found == _spec_store.Layout("store", str(store), "origin", "origin/specs-trunk")


def test_a_clone_of_its_own_with_an_upstream_is_a_store(tmp_path: Path) -> None:
    """A spec store in a repository of its own passes on the repository alone,
    whatever branch it has checked out, the same as the guard lets it commit."""
    _, here, _ = _remote_and_clones(tmp_path)
    project = git_repo(tmp_path / "project")

    assert _spec_store.layout(here, project).kind == "store"


def test_a_store_branch_with_no_upstream_is_store_no_upstream(tmp_path: Path) -> None:
    """It takes commits and has nowhere to push them, which the store has to
    say rather than report a push that never happened."""
    project = git_repo(tmp_path / "project")
    store = _worktree(project, tmp_path / "project-specs", "-b", "specs-trunk")

    assert _spec_store.layout(store, project) == _spec_store.Layout(
        "store_no_upstream", str(store)
    )


def test_the_default_specs_folder_is_in_repo(tmp_path: Path) -> None:
    """`<repo>/specs` is the default spec root. A commit there lands on the
    feature branch, so the store must never make one."""
    project = git_repo(tmp_path / "project")
    (project / "specs").mkdir()

    assert _spec_store.layout(project / "specs", project).kind == "in_repo"


def test_a_worktree_on_the_codes_own_branch_is_in_repo(tmp_path: Path) -> None:
    """The case the top-of-checkout test alone lets through. The root is the
    top of its own worktree, but that worktree has the main checkout's branch,
    so a commit there lands on the code's history."""
    project = git_repo(tmp_path / "project")
    branch = _git(project, "symbolic-ref", "--short", "HEAD").strip()
    store = _worktree(project, tmp_path / "project-specs", "--force", start=branch)

    assert _spec_store.layout(store, project).kind == "in_repo"


def test_a_folder_one_level_inside_a_store_is_not_a_store(tmp_path: Path) -> None:
    """It passes `owns_branch`, since git there finds the store's branch, and a
    commit from it would still take in the whole store. FR-010's
    top-of-checkout test is what turns it away."""
    project, _ = _project_with_remote(tmp_path)
    store = _worktree(project, tmp_path / "project-specs", "-b", "specs-trunk",
                      start="origin/specs-trunk")

    assert _spec_store.layout(store / "100", project).kind not in ("store", "store_no_upstream")


@pytest.mark.parametrize("where", ["plain", "missing", "nested"])
def test_a_folder_git_does_not_tie_to_the_code_is_unmanaged(tmp_path: Path, where: str) -> None:
    """A plain folder has no repository to commit in. A folder nested in some
    other repository has one, and a commit there would land on that
    repository's branch, which the store has no business writing to."""
    project = git_repo(tmp_path / "project")
    if where == "nested":
        root = git_repo(tmp_path / "other") / "specs"
        root.mkdir()
    else:
        root = tmp_path / "specs"
        if where == "plain":
            root.mkdir()

    assert _spec_store.layout(root, project) == _spec_store.Layout("unmanaged", str(root))


def test_a_new_untracked_spec_dir_counts_each_file(tmp_path: Path) -> None:
    """`--untracked-files=all` is what makes a new spec dir count its files.
    Without it git prints one line for the directory, and a branch that wrote
    four files would read as one."""
    _, here, _ = _remote_and_clones(tmp_path)
    new = here / "359-push-specs-to-trunk"
    (new / "checklists").mkdir(parents=True)
    for name in ("spec.md", "plan.md", "tasks.md", "checklists/requirements.md"):
        (new / name).write_text("x\n")

    found = _spec_store.unstored(here, ["."])

    assert found == [_spec_store.Unstored("359-push-specs-to-trunk", 4, False)]
    assert _spec_store.describe(found[0]) == "uncommitted: 4 files"


def test_a_commit_the_upstream_lacks_reads_unpushed(tmp_path: Path) -> None:
    """A store that committed and could not push leaves the spec dir looking
    clean to `git status`. Only the comparison with `@{u}` shows it is not on
    the remote."""
    _, here, _ = _remote_and_clones(tmp_path)
    (here / "100" / "spec.md").write_text("100 edited\n")
    _git(here, "commit", "-am", "specs(100): store spec.md")

    found = _spec_store.unstored(here, ["100"])

    assert found == [_spec_store.Unstored("100", 0, True)]
    assert _spec_store.describe(found[0]) == "committed, not pushed"


def test_an_unpushed_commit_and_new_edits_render_as_the_count(tmp_path: Path) -> None:
    """Both hold at once after a store that could not push and a session that
    kept writing. Committing is the next thing that has to happen, so the
    count is what prints."""
    _, here, _ = _remote_and_clones(tmp_path)
    (here / "100" / "spec.md").write_text("100 edited\n")
    _git(here, "commit", "-am", "specs(100): store spec.md")
    (here / "100" / "spec.md").write_text("100 edited again\n")
    (here / "100" / "plan.md").write_text("new\n")

    found = _spec_store.unstored(here, ["100"])

    assert found == [_spec_store.Unstored("100", 2, True)]
    assert _spec_store.describe(found[0]) == "uncommitted: 2 files"


def test_a_stored_spec_dir_is_not_listed(tmp_path: Path) -> None:
    """An empty list is how a caller learns everything is stored, so a spec dir
    whose commit reached the remote must not appear, and neither must one an
    unrelated folder's edits sit beside."""
    _, here, _ = _remote_and_clones(tmp_path)
    (here / "100" / "spec.md").write_text("100 edited\n")
    _git(here, "commit", "-am", "specs(100): store spec.md")
    _git(here, "push")
    (here / "200" / "tasks.md").write_text("200 edited\n")

    assert _spec_store.unstored(here, ["100"]) == []
    assert _spec_store.unstored(here, ["."]) == [_spec_store.Unstored("200", 1, False)]


def test_a_spec_dir_with_an_unusual_name_keeps_its_name(tmp_path: Path) -> None:
    """Without `-z`, git quotes a path holding a space or a non-ASCII
    character, and the opening quote would become part of the spec dir's
    name, which then matches no branch."""
    _, here, _ = _remote_and_clones(tmp_path)
    (here / "360-café").mkdir()
    (here / "360-café" / "spec.md").write_text("x\n")
    _git(here, "add", "-A")
    _git(here, "commit", "-m", "specs(360): store spec.md")
    (here / "361 two").mkdir()
    (here / "361 two" / "spec.md").write_text("x\n")

    assert _spec_store.unstored(here, ["."]) == [
        _spec_store.Unstored("360-café", 0, True),
        _spec_store.Unstored("361 two", 1, False),
    ]


def test_a_store_with_no_upstream_reports_only_uncommitted_files(tmp_path: Path) -> None:
    """With nothing to compare against, every commit would read as unpushed,
    and no command could ever clear it."""
    store = git_repo(tmp_path / "store")
    (store / "100").mkdir()
    (store / "100" / "spec.md").write_text("x\n")
    _git(store, "add", "-A")
    _git(store, "commit", "-m", "specs(100): store spec.md")
    (store / "200").mkdir()
    (store / "200" / "spec.md").write_text("x\n")

    assert _spec_store.unstored(store, ["."]) == [_spec_store.Unstored("200", 1, False)]


def test_a_staged_rename_counts_in_both_folders(tmp_path: Path) -> None:
    """`-z` prints a rename as two paths, the new one first. Reading only the
    first would miss that the old folder lost a file, and that folder's store
    would never commit the deletion."""
    _, here, _ = _remote_and_clones(tmp_path)
    _git(here, "mv", "100/spec.md", "200/spec.md")

    assert _spec_store.unstored(here, ["."]) == [
        _spec_store.Unstored("100", 1, False),
        _spec_store.Unstored("200", 1, False),
    ]
