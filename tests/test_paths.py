"""Tests for wfctl._paths — path resolution."""
from __future__ import annotations

import json
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


# --- spec_root: where a repo's specs live (issue #18) ------------------------


def _write_manifest(repo_root: Path, **keys: str) -> None:
    """Write a manifest carrying a realistic layer entry plus the given keys."""
    import json
    payload: dict = {"base": {"repo": "x", "ref": "main", "commit": "c", "items": []}}
    payload.update(keys)
    (repo_root / ".wf-skills-manifest.json").write_text(json.dumps(payload))


def test_spec_root_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Precedence: env override > manifest > repo_root/specs.

    The env var stays a per-invocation escape hatch — it is process-global, so
    exporting it from a shell profile would redirect every repo wfctl touches.
    That is why the persistent setting lives in the manifest instead.
    """
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    assert spec_root(tmp_path) == tmp_path / "specs"

    _write_manifest(tmp_path, spec_root=str(tmp_path / "from-manifest"))
    assert spec_root(tmp_path) == tmp_path / "from-manifest"

    monkeypatch.setenv("WFCTL_SPEC_DIR", str(tmp_path / "from-env"))
    assert spec_root(tmp_path) == tmp_path / "from-env"


def test_spec_root_empty_value_is_not_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty string means "not recorded", not "resolve to the repo root"."""
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    _write_manifest(tmp_path, spec_root="")
    assert spec_root(tmp_path) == tmp_path / "specs"


def test_spec_root_never_creates_the_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A root that does not exist yet is the case that broke the create
    path — `resolve_spec_dir` returned None for it and the hardcoded fallback
    took over. Resolving must never validate or create it."""
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    target = tmp_path / "not-created-yet"
    _write_manifest(tmp_path, spec_root=str(target))
    assert spec_root(tmp_path) == target
    assert not target.exists()


def test_spec_root_path_forms(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Absolute as-is; `~` expanded at read time; relative anchored to
    the manifest's own directory, never cwd — so one relative value declared
    once means one shared location from every worktree."""
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)

    _write_manifest(tmp_path, spec_root="/srv/specs")
    assert spec_root(tmp_path) == Path("/srv/specs")

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    _write_manifest(tmp_path, spec_root="~/Development/pfms-specs")
    assert spec_root(tmp_path) == home / "Development" / "pfms-specs"

    _write_manifest(tmp_path, spec_root="../shared-specs")
    monkeypatch.chdir(home)  # cwd must not influence the result
    assert spec_root(tmp_path) == (tmp_path / ".." / "shared-specs").resolve()


def test_feature_paths_uses_spec_root_when_no_spec_dir_exists(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The core regression.

    `resolve_spec_dir` honored WFCTL_SPEC_DIR, but `feature-paths` hardcoded
    `repo_root/specs/<branch>` when nothing existed yet — so reads were
    redirectable and creates were not. Every speckit script routes through this
    command, so that one line decided where every new spec was written.
    """
    from typer.testing import CliRunner

    from wfctl.cli import app

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo_root))
    monkeypatch.setenv("WFCTL_BRANCH", "18-spec-root")
    monkeypatch.setenv("WFCTL_STATE_DIR", str(tmp_path / "state"))
    elsewhere = tmp_path / "outside-the-repo"
    _write_manifest(repo_root, spec_root=str(elsewhere))

    result = CliRunner().invoke(app, ["feature-paths"])

    assert result.exit_code == 0, result.output
    assert f"FEATURE_DIR='{elsewhere / '18-spec-root'}'" in result.output
    assert str(repo_root / "specs") not in result.output


def test_recorded_root_does_not_fall_back_to_in_repo_specs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The recorded root is the only root.

    Falling back would let one feature's artifacts split across two locations —
    spec.md found in the old root while plan.md is written to the new one.
    """
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    (tmp_path / "specs" / "18-legacy").mkdir(parents=True)
    _write_manifest(tmp_path, spec_root=str(tmp_path / "configured"))

    assert resolve_spec_dir("18-legacy", tmp_path) is None


def test_spec_root_matches_by_issue_key_under_the_configured_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the root moves. Exact-name and issue-key matching are
    unchanged, and still apply under a configured root."""
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    configured = tmp_path / "configured"
    target = configured / "18-recorded-name"
    target.mkdir(parents=True)
    _write_manifest(tmp_path, spec_root=str(configured))

    assert resolve_spec_dir("18-different-slug", tmp_path) == target


def test_unparseable_manifest_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A malformed manifest is a broken repo, not a missing setting.

    Defaulting silently would put specs back inside the worktree with no signal
    — the exact failure this feature removes.
    """
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    (tmp_path / ".wf-skills-manifest.json").write_text("{not json")

    with pytest.raises(json.JSONDecodeError):
        spec_root(tmp_path)


def _worktree_project(tmp_path: Path) -> tuple[Path, Path]:
    """A real main checkout plus a linked worktree. Returns (main, worktree).

    Real git, no mocking: the fallback keys on `git rev-parse --git-common-dir`,
    and the layout it must distinguish (`.git` file in a worktree pointing at the
    main checkout's `.git` dir) is not something a fake reproduces faithfully.
    """
    import subprocess

    main = tmp_path / "myproject"
    main.mkdir()
    subprocess.run(["git", "init", str(main)], check=True, capture_output=True)
    for key, val in (("user.email", "test@test.com"), ("user.name", "Test")):
        subprocess.run(["git", "-C", str(main), "config", key, val],
                       check=True, capture_output=True)
    _init_commit(main)

    wt = main / "wt" / "18-spec-root"
    subprocess.run(
        ["git", "-C", str(main), "worktree", "add", "-b", "18-spec-root", str(wt)],
        check=True, capture_output=True,
    )
    return main, wt


def test_worktree_inherits_spec_root_from_main_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The whole reason the fallback exists.

    The manifest is gitignored and `install-skills` regenerates it in every
    fresh worktree, so a worktree-local spec_root cannot exist at the moment the
    pipeline first runs there. Without this, specs fall back into the worktree
    and die with it — the failure this feature removes.
    """
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    main, wt = _worktree_project(tmp_path)
    _write_manifest(main, spec_root=str(tmp_path / "shared-specs"))
    _write_manifest(wt)  # what install-skills writes: layers, no spec_root

    assert spec_root(wt) == tmp_path / "shared-specs"


def test_worktree_own_spec_root_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The fallback is a fallback: a worktree that declares its own is not
    overridden by the main checkout's."""
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    main, wt = _worktree_project(tmp_path)
    _write_manifest(main, spec_root=str(tmp_path / "main-specs"))
    _write_manifest(wt, spec_root=str(tmp_path / "worktree-specs"))

    assert spec_root(wt) == tmp_path / "worktree-specs"


def test_no_main_checkout_reads_no_outside_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The guard on reading a manifest outside this repo.

    In a bare or separate-gitdir layout the common dir is `<name>.git`, and its
    parent is a container directory that may hold an unrelated project's
    manifest. Reading that would silently apply another repo's spec root, so a
    common dir not named exactly `.git` gets no fallback at all.
    """
    import subprocess

    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    container = tmp_path / "container"
    container.mkdir()
    # The sibling manifest that must NOT be read.
    _write_manifest(container, spec_root=str(tmp_path / "someone-elses-specs"))

    repo = container / "checkout"
    repo.mkdir()
    gitdir = container / "myproject.git"
    subprocess.run(
        ["git", "init", "--separate-git-dir", str(gitdir), str(repo)],
        check=True, capture_output=True,
    )
    _write_manifest(repo)  # layers only, no spec_root

    assert spec_root(repo) == repo / "specs"


def test_unparseable_main_checkout_manifest_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Raising covers both manifests. The current-repo half is pinned above;
    this is the half that only exists once the fallback does."""
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    main, wt = _worktree_project(tmp_path)
    (main / ".wf-skills-manifest.json").write_text("{not json")
    _write_manifest(wt)  # the worktree's own is fine and declares nothing

    with pytest.raises(json.JSONDecodeError):
        spec_root(wt)


def test_relative_spec_root_in_main_checkout_is_one_shared_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Relative values across worktrees: one anchors to the manifest that
    declared it, so main checkout and worktree resolve to the same directory —
    the property that makes `../pfms-specs` usable at all."""
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    main, wt = _worktree_project(tmp_path)
    _write_manifest(main, spec_root="../shared-specs")
    _write_manifest(wt)

    assert spec_root(wt) == spec_root(main) == (main / ".." / "shared-specs").resolve()


def test_issue_key_match_ignores_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The key glob returns a spec *directory*, never a file that shares the key.

    The exact-name branch has always checked `is_dir()`; the glob branch took
    `matches[0]` blind. A stray `42-notes.md` beside `42-feature/` sorts first
    and was handed back as the feature dir, making FEATURE_SPEC a path *inside*
    a file: `specs/42-notes.md/spec.md`.
    """
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    specs = tmp_path / "specs"
    real = specs / "42-feature"
    real.mkdir(parents=True)
    (specs / "42-aaa-notes.md").write_text("stray")

    # Branch name differs from the dir name, so resolution goes through the glob.
    assert resolve_spec_dir("42-renamed", tmp_path) == real


def test_issue_key_match_with_no_matching_directory_is_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Files alone are not a match — better no spec dir than a bogus one."""
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "42-notes.md").write_text("stray")

    assert resolve_spec_dir("42-renamed", tmp_path) is None
