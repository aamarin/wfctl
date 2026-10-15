"""The spec store: its layout, which spec dirs are not stored, and the store.

Every fixture here builds a bare remote and its clones under `tmp_path` with
real git, because each claim this module makes is a claim about what git does
to a shared checkout, and a stub would only repeat the claim back.
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import threading
import time
import types
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


@pytest.mark.parametrize("shape", ["clone", "worktree"])
def test_a_spec_store_with_a_detached_head_is_detached(tmp_path: Path, shape: str) -> None:
    """The first draft of `layout` read a detached clone as
    `store_no_upstream`, so the store would have committed onto no branch.
    The second read it as `unmanaged`, and a detached worktree of the code
    repository as `in_repo`, so the store said "inside the code repository"
    about a folder outside it and the pass read `skipped`."""
    if shape == "clone":
        _, store, _ = _remote_and_clones(tmp_path)
        project = git_repo(tmp_path / "project")
    else:
        project, _ = _project_with_remote(tmp_path)
        store = _worktree(project, tmp_path / "project-specs", "-b", "specs-trunk",
                          start="origin/specs-trunk")
    _git(store, "checkout", "--detach")

    assert _spec_store.layout(store, project) == _spec_store.Layout("detached", str(store))


def test_a_detached_spec_store_fails_the_store_and_commits_nothing(tmp_path: Path) -> None:
    """A commit there sits on no branch, so nothing pushes it. Exit 0 with
    "not backed up" told a script there was nothing to do, when a person
    only has to check the branch out again."""
    env = _store_setup(tmp_path)
    _git(env.here, "checkout", "--detach")
    head = _git(env.here, "rev-parse", "HEAD")
    _write(env.spec_dir, "spec.md")

    result = _store(env)

    assert result.outcome == "git_failed"
    assert result.exit_code == 1
    assert _git(env.here, "rev-parse", "HEAD") == head
    assert _spec_store.report_lines(result) == [
        "✗ store failed: the spec store has no branch checked out",
        f"    check out its branch in {env.here}, then run `wfctl store specs` again",
    ]


def test_git_missing_from_path_raises_rather_than_reading_unmanaged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`unmanaged` is a layout a repository chooses, and the pass reads it
    `skipped`. A machine with no git read that way finished `implement` with
    nothing stored and no word about why."""
    _, here, _ = _remote_and_clones(tmp_path)
    project = git_repo(tmp_path / "project")
    monkeypatch.setenv("PATH", str(tmp_path / "no-git-here"))

    with pytest.raises(OSError):
        _spec_store.layout(here, project)
    result = _spec_store.store(here / "100", BRANCH, project)

    assert result.outcome == "git_failed"
    assert "git" in (result.message or "")


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


BRANCH = "359-push-specs-to-trunk"


def _store_setup(tmp_path: Path) -> types.SimpleNamespace:
    """A spec store with an upstream, a code repository beside it, and an
    empty spec dir for `BRANCH` in the store.

    The store is `here` from `_remote_and_clones`, a clone of its own, so it
    reads `store` against the code repository. `there` is the second machine,
    which the tests use to move the remote.
    """
    remote, here, there = _remote_and_clones(tmp_path)
    project = git_repo(tmp_path / "project")
    spec_dir = here / BRANCH
    spec_dir.mkdir()
    return types.SimpleNamespace(
        remote=remote, here=here, there=there, project=project, spec_dir=spec_dir,
    )


def _write(folder: Path, *names: str, text: str = "x\n") -> None:
    for name in names:
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def _store(env: types.SimpleNamespace, branch: str = BRANCH) -> _spec_store.StoreResult:
    folder = env.here / branch
    return _spec_store.store(folder, branch, env.project)


def _remote_files(remote: Path) -> set[str]:
    return set(_git(remote, "ls-tree", "-r", "--name-only", "specs-trunk").split())


def _move_remote_away(env: types.SimpleNamespace) -> Path:
    away = env.remote.with_name("remote-away.git")
    env.remote.rename(away)
    return away


def test_the_commit_holds_only_this_folder_and_another_staged_path_stays_staged(
    tmp_path: Path,
) -> None:
    """FR-001. The spec store is shared, and another branch may have staged a
    file there. A plain `git commit` would carry that file into this branch's
    commit, and a store that reset the index would throw the staging away."""
    env = _store_setup(tmp_path)
    (env.here / "200" / "tasks.md").write_text("200 with a task ticked off\n")
    _git(env.here, "add", "200/tasks.md")
    _write(env.spec_dir, "spec.md", "plan.md")

    result = _store(env)

    assert result.outcome == "stored"
    committed = _git(env.here, "show", "--name-only", "--format=", "HEAD").split()
    assert committed == [f"{BRANCH}/plan.md", f"{BRANCH}/spec.md"]
    assert _git(env.here, "diff", "--cached", "--name-only").split() == ["200/tasks.md"]


def test_a_moved_remote_is_merged_and_pushed(tmp_path: Path) -> None:
    """`store-specs-merges-before-push.md`: the remote moves every time another
    machine stores, so a store that stopped on a moved remote would stop on
    the ordinary case."""
    env = _store_setup(tmp_path)
    (env.there / "100" / "spec.md").write_text("100 as edited there\n")
    _git(env.there, "commit", "-am", "specs(100): there")
    _git(env.there, "push")
    _write(env.spec_dir, "spec.md")

    result = _store(env)

    assert result.outcome == "stored"
    assert f"{BRANCH}/spec.md" in _remote_files(env.remote)
    assert _git(env.remote, "show", "specs-trunk:100/spec.md") == "100 as edited there\n"
    parents = _git(env.here, "rev-list", "--parents", "-n", "1", "HEAD").split()
    assert len(parents) == 3, "the store merges rather than rebasing"


def test_a_deleted_file_is_committed_as_a_deletion(tmp_path: Path) -> None:
    """`git commit -- <dir>` builds its commit from the paths it is given, and
    a file already gone from the working tree is one a careless pathspec
    leaves behind on the remote."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md", "notes.md")
    assert _store(env).outcome == "stored"
    (env.spec_dir / "notes.md").unlink()

    result = _store(env)

    assert result.outcome == "stored"
    assert result.files == ("notes.md",)
    assert f"{BRANCH}/notes.md" not in _remote_files(env.remote)
    assert f"{BRANCH}/spec.md" in _remote_files(env.remote)


def test_an_already_stored_spec_dir_creates_no_commit(tmp_path: Path) -> None:
    """FR-009. The pass names `/store-specs` once per finished `implement`, and
    a store that committed an empty change each time would fill the spec
    store's history with commits that say nothing."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md")
    _store(env)
    head = _git(env.here, "rev-parse", "HEAD")

    result = _store(env)

    assert result.outcome == "already_stored"
    assert _git(env.here, "rev-parse", "HEAD") == head


@pytest.mark.parametrize("names, subject", [
    (("spec.md",), "specs(359): store spec.md"),
    (("spec.md", "plan.md", "tasks.md"), "specs(359): store plan.md and 2 others"),
])
def test_the_subject_names_the_issue_and_the_files(
    tmp_path: Path, names: tuple[str, ...], subject: str,
) -> None:
    """FR-002. The existing commits on the spec branch start `specs(<issue>):`,
    and `git log --oneline` is how a person finds which branch stored what."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, *names)

    _store(env)

    assert _git(env.here, "log", "-1", "--format=%s").strip() == subject


def test_the_count_takes_in_files_from_an_earlier_unpushed_commit(tmp_path: Path) -> None:
    """Research R9. "Stored 3 files" has to mean the three files that just
    reached the remote, and two of them were committed by a store that could
    not push."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md", "plan.md")
    away = _move_remote_away(env)
    assert _store(env).outcome == "not_pushed"
    away.rename(env.remote)
    _write(env.spec_dir, "tasks.md")

    result = _store(env)

    assert result.outcome == "stored"
    assert result.files == ("plan.md", "spec.md", "tasks.md")


def _cli(monkeypatch: pytest.MonkeyPatch, spec_root: Path, project: Path,
         branch: str = BRANCH) -> tuple[int, str, Path]:
    """`wfctl store specs` run the way a session runs it, with every root
    pinned so nothing resolves the developer's own spec store."""
    from typer.testing import CliRunner

    from wfctl.cli import app

    state = project.parent / "state"
    state.mkdir(exist_ok=True)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(spec_root))
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(project))
    monkeypatch.setenv("WFCTL_BRANCH", branch)
    monkeypatch.setenv("WFCTL_STATE_DIR", str(state))
    result = CliRunner().invoke(app, ["store", "specs"])
    return result.exit_code, result.output, state


def _recorded_actions(state: Path) -> list[str]:
    events = state / "events.jsonl"
    if not events.exists():
        return []
    return [
        e["action"] for e in map(json.loads, events.read_text().splitlines())
        if e.get("event") == "notify-action"
    ]


def test_the_success_output_is_two_lines_counting_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-008 and `contracts/cli.md`. The noun is asserted rather than "specs"
    being absent, because the same line names `origin/specs-trunk`, and the
    first draft counted "specs" where it meant files."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md", "plan.md")

    code, out, state = _cli(monkeypatch, env.here, env.project)

    sha = _git(env.here, "rev-parse", "--short", "HEAD").strip()
    assert code == 0
    assert out.splitlines() == [
        f"✓ stored 2 files → origin/specs-trunk ({sha})",
        "    plan.md, spec.md",
    ]
    assert _recorded_actions(state) == ["store-specs"]


def test_an_unreachable_remote_keeps_the_commit_and_reads_not_pushed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-006 and PR-007. The files are committed, so nothing is lost, and the
    spec dir is still not backed up, which is why this exits 1. The remedy
    line has to hold for a branch with nothing new to store, which pushes
    nothing, so it names the next store with files to push."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md", "plan.md")
    _move_remote_away(env)

    code, out, state = _cli(monkeypatch, env.here, env.project)

    assert code == 1
    assert out.splitlines() == [
        "⚠ committed 2 files, not pushed — origin/specs-trunk is unreachable",
        "    plan.md, spec.md",
        "    the next `wfctl store specs` with files to push sends it",
    ]
    assert _git(env.here, "log", "-1", "--format=%s").startswith("specs(359):")
    assert _spec_store.unstored(env.here, [BRANCH]) == [_spec_store.Unstored(BRANCH, 0, True)]
    assert _recorded_actions(state) == []


def test_the_next_store_from_another_branch_pushes_both_commits(tmp_path: Path) -> None:
    """`store-specs-merges-before-push.md`, decision 1. A push sends every
    local commit on the branch, so the commit an offline store left behind
    goes out with the next branch's."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md")
    away = _move_remote_away(env)
    assert _store(env).outcome == "not_pushed"
    away.rename(env.remote)
    _write(env.here / "360-other", "spec.md")

    result = _store(env, "360-other")

    assert result.outcome == "stored"
    assert result.files == ("spec.md",)
    assert {f"{BRANCH}/spec.md", "360-other/spec.md"} <= _remote_files(env.remote)
    assert _spec_store.unstored(env.here, ["."]) == []


def test_a_push_refused_after_the_merge_keeps_the_merge_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Decision 3. The remote can move again between the merge and the push.
    The merge commit is the work the next run builds on, and a store that
    reset it would have to merge the same changes twice."""
    env = _store_setup(tmp_path)
    (env.there / "100" / "spec.md").write_text("100, first move\n")
    _git(env.there, "commit", "-am", "specs(100): first move")
    _git(env.there, "push")
    _write(env.spec_dir, "spec.md")

    real = subprocess.run
    moved = []

    def move_before_the_push(args: list[str], *a: object, **kw: object) -> object:
        if not moved and args[:1] == ["git"] and "push" in args and str(env.here) in args:
            moved.append(True)
            (env.there / "100" / "spec.md").write_text("100, second move\n")
            real(["git", "-C", str(env.there), "commit", "-qam", "second"], check=True, capture_output=True)
            real(["git", "-C", str(env.there), "push", "-q"], check=True, capture_output=True)
        return real(args, *a, **kw)  # type: ignore[call-overload]

    monkeypatch.setattr(subprocess, "run", move_before_the_push)

    result = _store(env)

    assert result.outcome == "push_refused"
    assert result.exit_code == 1
    parents = _git(env.here, "rev-list", "--parents", "-n", "1", "HEAD").split()
    assert len(parents) == 3, "the merge commit is kept"
    assert not (env.here / ".git" / "MERGE_HEAD").exists()


def test_an_authentication_failure_reads_git_failed_with_gits_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PR-010. "Unreachable" sends a person to check their network, and a
    rejected key is not fixed by waiting. The `ssh` here is a stand-in on
    `PATH` that refuses the way GitHub refuses a key it does not know."""
    env = _store_setup(tmp_path)
    url = "ssh://git@example.invalid/specs.git"
    _git(env.here, "remote", "set-url", "origin", url)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "ssh"
    fake.write_text("#!/bin/sh\necho 'git@example.invalid: Permission denied (publickey).' >&2\nexit 255\n")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.delenv("GIT_SSH_COMMAND", raising=False)
    monkeypatch.delenv("GIT_SSH", raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)

    def only_the_stand_in(seen: str) -> None:
        assert seen == url

    monkeypatch.setattr(_spec_store, "_check_remote", only_the_stand_in)
    _write(env.spec_dir, "spec.md")

    result = _store(env)

    assert result.outcome == "git_failed"
    assert result.exit_code == 1
    assert result.message is not None
    assert "Permission denied (publickey)" in result.message
    lines = _spec_store.report_lines(result)
    assert lines[0].startswith("✗ store failed: ")
    assert not any("unreachable" in line for line in lines)


def test_every_git_call_runs_without_a_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PR-003 and research R7. The store runs from a removal hook and from an
    unattended pass, where nobody is at the terminal, and a credential prompt
    there hangs with no output. Fetch and push also carry a timeout, since a
    dead network hangs the same way."""
    env = _store_setup(tmp_path)
    (env.there / "100" / "spec.md").write_text("100 as edited there\n")
    _git(env.there, "commit", "-am", "specs(100): there")
    _git(env.there, "push")
    _write(env.spec_dir, "spec.md")

    real = subprocess.run
    calls: list[tuple[list[str], dict[str, object]]] = []

    def record(args: list[str], *a: object, **kw: object) -> object:
        if args[:1] == ["git"]:
            calls.append((list(args), kw))
        return real(args, *a, **kw)  # type: ignore[call-overload]

    monkeypatch.setattr(subprocess, "run", record)

    assert _store(env).outcome == "stored"

    verbs = {args[3] for args, _ in calls}
    assert {"add", "commit", "fetch", "merge", "push"} <= verbs
    for args, kw in calls:
        env_ = kw.get("env")
        assert isinstance(env_, dict), args
        assert env_.get("GIT_TERMINAL_PROMPT") == "0", args
        assert "-o BatchMode=yes" in env_.get("GIT_SSH_COMMAND", ""), args
        if args[3] in ("fetch", "push"):
            assert kw.get("timeout") == 60, args


def test_a_spec_dir_outside_the_worktree_never_stops_removal(tmp_path: Path) -> None:
    """Research R6. A spec dir in a spec store survives the worktree's
    removal whatever the store did, so every outcome there, a failed push
    included, has to let removal go ahead."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md")
    away = _move_remote_away(env)
    not_pushed = _store(env)
    away.rename(env.remote)
    stored = _store(env)
    already = _store(env)

    assert [r.outcome for r in (not_pushed, stored, already)] == [
        "not_pushed", "stored", "already_stored",
    ]
    assert not any(r.stops_removal for r in (not_pushed, stored, already))


def test_a_spec_dir_inside_the_worktree_stops_removal_and_still_exits_0_by_hand(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Research R6. Inside the worktree, deleting the worktree deletes the only
    copy, so `not_applicable` there has to stop removal. Run by hand, the
    store has nothing it can do in that layout, and an exit of 1 would fail
    every run in every repository on the default layout."""
    project = git_repo(tmp_path / "project")
    spec_dir = project / "specs" / BRANCH
    _write(spec_dir, "spec.md")

    result = _spec_store.store(spec_dir, BRANCH, project)
    code, out, state = _cli(monkeypatch, project / "specs", project)

    assert result.outcome == "not_applicable"
    assert result.stops_removal is True
    assert result.exit_code == 0
    assert code == 0
    assert out.startswith(f"ℹ {spec_dir} is inside the code repository")
    assert _git(project, "log", "--format=%s").splitlines() == ["init"]
    assert _recorded_actions(state) == []


@pytest.mark.parametrize("outcome, code", [
    ("stored", 0), ("already_stored", 0), ("not_applicable", 0), ("no_spec_dir", 0),
    ("committed_not_backed_up", 0), ("not_pushed", 1), ("push_refused", 1),
    ("conflict", 1), ("merge_blocked_staged", 1), ("merge_refused", 1),
    ("merge_in_progress", 1), ("locked", 1), ("git_failed", 1),
])
def test_each_outcome_carries_the_exit_code_the_data_model_gives_it(
    outcome: _spec_store.Outcome, code: int,
) -> None:
    """`data-model.md §Store result`. The pass reads `in_progress` in every
    exit-1 case, so a 0 there would tell a script the store worked when the
    pipeline says it did not (research R6)."""
    result = _spec_store.StoreResult(outcome, BRANCH, "/specs/x", False)

    assert result.exit_code == code


def test_already_stored_exits_0_and_records_no_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Research R15. The action event says a push happened, and the log is the
    only record a restarted session reads, so a store that pushed nothing
    must not write one."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md")
    _store(env)

    code, out, state = _cli(monkeypatch, env.here, env.project)

    assert code == 0
    assert out.splitlines() == ["✓ spec dir already stored on origin/specs-trunk"]
    assert _recorded_actions(state) == []


def test_a_refused_push_exits_1_and_records_no_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI half of `push_refused`: the exact lines, the exit code, and no
    action recorded for a push that did not land."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md")
    real = subprocess.run
    moved = []

    def move_before_the_push(args: list[str], *a: object, **kw: object) -> object:
        if not moved and args[:1] == ["git"] and "push" in args and str(env.here) in args:
            moved.append(True)
            (env.there / "100" / "spec.md").write_text("100 moved\n")
            real(["git", "-C", str(env.there), "commit", "-qam", "moved"], check=True, capture_output=True)
            real(["git", "-C", str(env.there), "push", "-q"], check=True, capture_output=True)
        return real(args, *a, **kw)  # type: ignore[call-overload]

    monkeypatch.setattr(subprocess, "run", move_before_the_push)

    code, out, state = _cli(monkeypatch, env.here, env.project)

    assert code == 1
    assert out.splitlines() == [
        "✗ committed 1 file, push refused — origin/specs-trunk moved again",
        "    spec.md",
        "    run `wfctl store specs` again to merge and push",
    ]
    assert _recorded_actions(state) == []


@pytest.mark.parametrize("branch", ["361-never-specified", "main"])
def test_a_branch_with_no_spec_dir_says_so_and_commits_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, branch: str,
) -> None:
    """Spec §Edge Cases. The removal hook runs on every worktree, including
    one that never wrote a spec, and `main` has no spec dir at all. Neither
    is a failure, and neither may commit."""
    env = _store_setup(tmp_path)
    head = _git(env.here, "rev-parse", "HEAD")

    code, out, state = _cli(monkeypatch, env.here, env.project, branch)

    assert code == 0
    assert out.splitlines() == [f"ℹ no spec dir for {branch}"]
    assert _git(env.here, "rev-parse", "HEAD") == head
    assert _recorded_actions(state) == []


def _move_remote(env: types.SimpleNamespace, folder: str, name: str, text: str) -> None:
    """Another machine stores `folder/name`, so the remote is one commit ahead."""
    _write(env.there / folder, name, text=text)
    _git(env.there, "add", "-A")
    _git(env.there, "commit", "-m", f"specs({folder}): there")
    _git(env.there, "push")


def test_a_merge_and_push_leaves_another_branchs_edits_and_new_folder_alone(
    tmp_path: Path,
) -> None:
    """SC-005, and the scratch test `store-specs-merges-before-push.md` asks
    for in the suite. The merge writes into a checkout other branches are
    using, and an edited `tasks.md` or a folder nobody stored yet is unstored
    work that only exists there."""
    env = _store_setup(tmp_path)
    _move_remote(env, "100", "spec.md", "100 as edited there\n")
    (env.here / "200" / "tasks.md").write_text("200 with a task ticked off\n")
    _write(env.here / "400", "spec.md", "notes/one.md", text="400, never stored\n")
    before = {f: _snapshot(env.here / f) for f in ("200", "400")}
    status_before = _git(env.here, "status", "--porcelain", "--untracked-files=all", "--", "200", "400")
    _write(env.spec_dir, "spec.md")

    result = _store(env)

    assert result.outcome == "stored"
    assert len(_git(env.here, "rev-list", "--parents", "-n", "1", "HEAD").split()) == 3
    assert {f: _snapshot(env.here / f) for f in ("200", "400")} == before
    assert _git(env.here, "status", "--porcelain", "--untracked-files=all", "--", "200", "400") == status_before
    assert not any(p.startswith("400/") for p in _remote_files(env.remote))
    assert _git(env.remote, "show", "specs-trunk:200/tasks.md") == "200 as first stored\n"


def test_a_conflict_in_this_folder_is_aborted_and_named_even_though_the_index_lists_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-007 and research R8. A started merge stages what it merged, so a
    store that read the index first would call this a staged file, skip the
    abort, and leave the spec store mid-merge, which stops every branch's
    store. The spy proves the index really does list paths at that moment,
    so the outcome comes from the `MERGE_HEAD` check and not from luck."""
    env = _store_setup(tmp_path)
    _write(env.there / BRANCH, "spec.md", text="as written there\n")
    _move_remote(env, "100", "spec.md", "100 as edited there\n")
    _write(env.spec_dir, "spec.md", text="as written here\n")
    real = subprocess.run
    staged_mid_merge: list[str] = []

    def look_at_the_index_after_the_merge(args: list[str], *a: object, **kw: object) -> object:
        out = real(args, *a, **kw)  # type: ignore[call-overload]
        if args[:1] == ["git"] and args[3:5] == ["merge", "--no-edit"]:
            staged_mid_merge.extend(_git(env.here, "diff", "--cached", "--name-only").split())
        return out

    monkeypatch.setattr(subprocess, "run", look_at_the_index_after_the_merge)

    result = _store(env)

    assert staged_mid_merge, "the fixture was meant to leave paths in the index"
    assert result.outcome == "conflict"
    assert result.exit_code == 1
    assert result.folders == (BRANCH,)
    assert not (env.here / ".git" / "MERGE_HEAD").exists()
    assert _git(env.here, "log", "-1", "--format=%s").startswith("specs(359):")
    assert _git(env.here, "show", f"HEAD:{BRANCH}/spec.md") == "as written here\n"
    assert _spec_store.report_lines(result) == [
        f"✗ committed 1 file, merge conflicts in {BRANCH}/",
        "    the merge was aborted and your commit is kept",
        "    every branch's store fails until a person resolves this conflict",
        f"    to resolve it, run `git merge @{{u}}` in {env.here}, fix the files, run"
        " `git commit`, then `wfctl store specs`",
    ]


def test_a_file_staged_in_another_folder_blocks_the_merge_until_its_branch_stores(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Research R8, kind 2. Git refuses any merge that is not a fast-forward
    while the index differs from `HEAD`, and FR-001 leaves another branch's
    staged file in place on purpose. "Local edits" would send a person
    looking for an unstaged change that is not there, and the remedy has to
    actually work: the owning branch's store commits the staged file and
    carries the first branch's kept commit out with its own."""
    env = _store_setup(tmp_path)
    _move_remote(env, "100", "spec.md", "100 as edited there\n")
    (env.here / "200" / "tasks.md").write_text("200 with a task ticked off\n")
    _git(env.here, "add", "200/tasks.md")
    _write(env.spec_dir, "spec.md")

    code, out, _ = _cli(monkeypatch, env.here, env.project)

    assert code == 1
    assert out.splitlines() == [
        "✗ committed 1 file, merge blocked by files staged in 200/",
        "    run `wfctl store specs` from the branch that owns that folder, or unstage",
        "    the files, then run `wfctl store specs` again",
    ]
    assert _git(env.here, "log", "-1", "--format=%s").startswith("specs(359):")
    assert not (env.here / ".git" / "MERGE_HEAD").exists()

    owner = _store(env, "200")

    assert owner.outcome == "stored"
    assert _git(env.here, "diff", "--cached", "--name-only") == ""
    assert f"{BRANCH}/spec.md" in _remote_files(env.remote)
    assert _git(env.remote, "show", "specs-trunk:200/tasks.md") == "200 with a task ticked off\n"
    assert _store(env).outcome == "already_stored"


@pytest.mark.parametrize("kind", ["edited", "untracked"])
def test_a_merge_refused_for_a_file_in_the_way_names_the_file_and_says_why(
    tmp_path: Path, kind: str,
) -> None:
    """Research R8 kind 3, and PR-015. With nothing staged, git refuses a merge
    that would overwrite a file the upstream changed. An edited file and an
    untracked one need different remedies, and calling a new file an edit
    sends a person looking for a change that was never made."""
    env = _store_setup(tmp_path)
    if kind == "edited":
        _move_remote(env, "200", "tasks.md", "200 as edited there\n")
        (env.here / "200" / "tasks.md").write_text("200 as edited here\n")
        blocked = "200/tasks.md"
    else:
        _move_remote(env, "300", "notes.md", "300 as written there\n")
        _write(env.here / "300", "notes.md", text="300 as written here\n")
        blocked = "300/notes.md"
    before = (env.here / blocked).read_bytes()
    _write(env.spec_dir, "spec.md")

    result = _store(env)

    assert result.outcome == "merge_refused"
    assert result.exit_code == 1
    assert (env.here / blocked).read_bytes() == before
    assert not (env.here / ".git" / "MERGE_HEAD").exists()
    expected = {
        "edited": [
            f"✗ committed 1 file, merge blocked by local edits to {blocked}",
            "    store or discard that edit, then run `wfctl store specs` again",
        ],
        "untracked": [
            f"✗ committed 1 file, merge blocked by untracked files the upstream adds: {blocked}",
            "    move those files aside, then run `wfctl store specs` again",
        ],
    }
    assert _spec_store.report_lines(result) == expected[kind]


def test_merge_autostash_in_the_store_config_does_not_stash_another_branchs_edit(
    tmp_path: Path,
) -> None:
    """FR-004 and SC-005. With `merge.autoStash` set, a plain `git merge`
    stashed the other branch's edit, popped it back as conflict markers, and
    the store still printed ✓. Every later store then failed at `git commit`
    on the unmerged file, with nothing saying why."""
    env = _store_setup(tmp_path)
    _git(env.here, "config", "merge.autoStash", "true")
    _move_remote(env, "200", "tasks.md", "200 as edited there\n")
    (env.here / "200" / "tasks.md").write_text("200 as edited here\n")
    _write(env.spec_dir, "spec.md")

    result = _store(env)

    assert result.outcome == "merge_refused"
    assert (env.here / "200" / "tasks.md").read_text() == "200 as edited here\n"
    assert _git(env.here, "stash", "list") == ""
    assert _git(env.here, "diff", "--name-only", "--diff-filter=U") == ""


def test_merge_ff_only_in_the_store_config_still_merges_a_moved_remote(tmp_path: Path) -> None:
    """With `merge.ff=only` set, every store failed with git's hint about
    diverging branches as soon as another machine had stored anything."""
    env = _store_setup(tmp_path)
    _git(env.here, "config", "merge.ff", "only")
    _move_remote(env, "100", "spec.md", "100 as edited there\n")
    _write(env.spec_dir, "spec.md")

    result = _store(env)

    assert result.outcome == "stored"
    assert f"{BRANCH}/spec.md" in _remote_files(env.remote)


def test_reading_the_store_leaves_its_index_alone(tmp_path: Path) -> None:
    """A plain `git status` refreshes the index under `index.lock`, and the
    pass runs one on every `wfctl status`. A store whose `git add` landed in
    that window failed with "index.lock: File exists", which at removal left
    the branch's last files uncommitted."""
    _, here, _ = _remote_and_clones(tmp_path)
    tracked = here / "100" / "spec.md"
    later = time.time() + 5
    os.utime(tracked, (later, later))
    index = here / ".git" / "index"
    before = index.stat().st_mtime_ns

    _spec_store.unstored(here, ["."])
    _spec_store.layout(here, git_repo(tmp_path / "project"))

    assert index.stat().st_mtime_ns == before


def test_a_merge_already_in_progress_is_reported_and_left_for_the_person(
    tmp_path: Path,
) -> None:
    """PR-011. A store killed mid-merge, or a person partway through resolving
    a conflict by hand, leaves `MERGE_HEAD`, and `git commit -- <dir>` fails
    there with a message that names neither cause. The store does not abort
    it either, since that would throw away a resolution a person is making."""
    env = _store_setup(tmp_path)
    (env.here / "100" / "spec.md").write_text("100 as edited here\n")
    _git(env.here, "commit", "-am", "specs(100): here")
    _move_remote(env, "100", "spec.md", "100 as edited there\n")
    _git(env.here, "fetch")
    merge = subprocess.run(
        ["git", "-C", str(env.here), "merge", "--no-edit", "@{u}"], capture_output=True, text=True,
    )
    assert merge.returncode != 0, "the fixture was meant to conflict in 100/"
    head = _git(env.here, "rev-parse", "HEAD")
    _write(env.spec_dir, "spec.md")

    result = _store(env)

    assert result.outcome == "merge_in_progress"
    assert result.exit_code == 1
    assert _git(env.here, "rev-parse", "HEAD") == head
    assert (env.here / ".git" / "MERGE_HEAD").exists()
    assert _spec_store.unstored(env.here, [BRANCH]) == [_spec_store.Unstored(BRANCH, 1, False)]
    assert _spec_store.report_lines(result) == [
        f"✗ nothing committed, a merge is already in progress in {env.here}",
        "    every branch's store fails until that merge is finished or aborted",
        f"    to finish it, fix the files and run `git commit` in {env.here},"
        " or run `git merge --abort` there",
    ]


def _hold_the_lock(env: types.SimpleNamespace) -> int:
    """The lock as another store holds it. flock locks belong to an open file
    description, so a second `open` in this process contends like another
    process would."""
    fd = os.open(env.here / ".git" / "wfctl-store.lock", os.O_RDWR | os.O_CREAT, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return fd


def test_a_second_store_gives_up_after_the_timeout_and_commits_nothing(tmp_path: Path) -> None:
    """FR-027. Two removals finishing together would otherwise interleave in
    one index, and a store waiting forever would hang the removal hook."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md")
    head = _git(env.here, "rev-parse", "HEAD")
    fd = _hold_the_lock(env)
    try:
        started = time.monotonic()
        result = _spec_store.store(env.spec_dir, BRANCH, env.project, lock_timeout=0.5)
        waited = time.monotonic() - started
    finally:
        os.close(fd)

    assert result.outcome == "locked"
    assert result.exit_code == 1
    assert waited >= 0.5
    assert _git(env.here, "rev-parse", "HEAD") == head
    assert _spec_store.report_lines(result) == [f"✗ another store is running in {env.here}"]


def test_a_second_store_waits_for_the_first_and_then_stores(tmp_path: Path) -> None:
    """Research R5. The other half of the timeout: a store that gave up at
    once would fail every time two worktrees are removed together."""
    env = _store_setup(tmp_path)
    _write(env.spec_dir, "spec.md")
    fd = _hold_the_lock(env)
    threading.Timer(0.3, os.close, [fd]).start()

    started = time.monotonic()
    result = _spec_store.store(env.spec_dir, BRANCH, env.project, lock_timeout=5)

    assert result.outcome == "stored"
    assert time.monotonic() - started >= 0.3
    assert (env.here / ".git" / "wfctl-store.lock").exists()
    assert "wfctl-store.lock" not in _git(env.here, "status", "--porcelain", "--ignored")


def test_a_store_with_no_upstream_commits_and_exits_0_by_hand(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-012, research R6 and PR-029. The commit is all the store can do
    there, since choosing a remote is the person's call. An exit of 1 would
    fail every run in that layout with no command that could ever pass, and
    a second run with nothing new must not claim a commit it did not make."""
    project = git_repo(tmp_path / "project")
    store = git_repo(tmp_path / "store")
    store_branch = _git(store, "symbolic-ref", "--short", "HEAD").strip()
    _write(store / BRANCH, "spec.md", "plan.md")

    code, out, state = _cli(monkeypatch, store, project)

    assert code == 0
    assert out.splitlines() == [
        f"⚠ committed 2 files, not backed up — {store_branch} has no upstream branch",
    ]
    assert _git(store, "log", "-1", "--format=%s").strip() == "specs(359): store plan.md and 1 other"
    assert _spec_store.unstored(store, [BRANCH]) == []
    assert _recorded_actions(state) == []

    code, out, _ = _cli(monkeypatch, store, project)

    assert code == 0
    assert out.splitlines() == [
        f"⚠ nothing new to commit, not backed up — {store_branch} has no upstream branch",
    ]


@pytest.mark.parametrize("kind", ["in_repo", "unmanaged"])
def test_a_layout_with_nowhere_to_commit_says_where_the_files_are_and_commits_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str,
) -> None:
    """FR-011 and FR-013. Inside the code repository a commit would land on
    the feature branch, and a plain folder has no repository at all, so the
    store only says where the files are. Both exit 0, for the reason the
    no-upstream layout does."""
    project = git_repo(tmp_path / "project")
    root = project / "specs" if kind == "in_repo" else tmp_path / "notes" / "specs"
    spec_dir = root / BRANCH
    _write(spec_dir, "spec.md")
    head = _git(project, "rev-parse", "HEAD")

    code, out, _ = _cli(monkeypatch, root, project)

    assert code == 0
    assert out.splitlines() == [{
        "in_repo": f"ℹ {spec_dir} is inside the code repository — not committed, not backed up",
        "unmanaged": f"ℹ {spec_dir} is not backed up anywhere",
    }[kind]]
    assert _git(project, "rev-parse", "HEAD") == head
    assert _git(project, "diff", "--cached", "--name-only") == ""
    assert not (tmp_path / "notes" / ".git").exists()
