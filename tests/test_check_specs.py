"""`wfctl check specs`: every spec dir in the spec store that is not stored.

The spec store and its remote are real git under `tmp_path`, built by the
fixtures in `test_spec_store.py`, and the code repository's worktrees are
real too. Which spec dirs count as in progress comes from `git worktree list`,
and a stub would only repeat back what the test told it.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import git_repo
from tests.test_spec_store import _git, _remote_and_clones, _write
from wfctl.cli import app


def _check(monkeypatch: pytest.MonkeyPatch, spec_root: Path, project: Path) -> tuple[int, str]:
    """`wfctl check specs` with both roots pinned, so nothing resolves the
    developer's own spec store."""
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(spec_root))
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(project))
    result = CliRunner().invoke(app, ["check", "specs"])
    return result.exit_code, result.output


def _setup(tmp_path: Path) -> tuple[Path, Path]:
    """A spec store with an upstream, `here`, and a code repository beside it
    with no worktrees but its main checkout."""
    _, here, _ = _remote_and_clones(tmp_path)
    project = git_repo(tmp_path / "project")
    return here, project


def _worktree_on(project: Path, branch: str) -> Path:
    path = project.parent / f"wt-{branch}"
    _git(project, "worktree", "add", "-b", branch, str(path))
    return path


def _commit_unpushed(here: Path, name: str) -> None:
    _write(here / name, "spec.md")
    _git(here, "add", "--", name)
    _git(here, "commit", "-m", f"specs: {name}", "--", name)


def test_unstored_spec_dirs_split_by_whether_a_worktree_resolves_to_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-016 and FR-023. A spec dir whose worktree is gone has nobody left
    to store it, so it is what this command exists to find. One whose branch
    still has a worktree is ordinary work in progress, and listing it with
    the others would make the exit code fail on every branch being worked on."""
    here, project = _setup(tmp_path)
    _write(here / "188-check-rework-loop", "spec.md", "plan.md")
    _commit_unpushed(here, "552-bob-command-rename")
    _write(here / "359-push-specs-to-trunk", "spec.md", "plan.md", "tasks.md")
    _worktree_on(project, "359-push-specs-to-trunk")

    code, out = _check(monkeypatch, here, project)

    assert code == 1, out
    assert out.splitlines() == [
        "✗ 2 spec dirs not stored",
        "    188-check-rework-loop      uncommitted: 2 files",
        "    552-bob-command-rename     committed, not pushed",
        "",
        "In progress (1 spec dir, still have a worktree):",
        "    359-push-specs-to-trunk    uncommitted: 3 files",
    ]


def test_a_spec_dir_with_a_worktree_alone_exits_0_under_in_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-023. The branch can still store its own spec dir, so the command
    says so and passes."""
    here, project = _setup(tmp_path)
    _write(here / "359-push-specs-to-trunk", "spec.md")
    _worktree_on(project, "359-push-specs-to-trunk")

    code, out = _check(monkeypatch, here, project)

    assert code == 0, out
    assert out.splitlines() == [
        "✓ every spec dir without a worktree is stored",
        "",
        "In progress (1 spec dir, still have a worktree):",
        "    359-push-specs-to-trunk    uncommitted: 1 file",
    ]


def test_a_spec_dir_resolved_by_issue_key_is_in_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Research R10. The branch and its spec dir can differ after the issue
    key, and `resolve_spec_dir` matches on the key. Comparing folder names to
    branch names would call this one abandoned while its branch is open."""
    here, project = _setup(tmp_path)
    _write(here / "359-push-specs-to-trunk", "spec.md")
    _worktree_on(project, "359-store-at-removal")

    code, out = _check(monkeypatch, here, project)

    assert code == 0, out
    assert "    359-push-specs-to-trunk    uncommitted: 1 file" in out.splitlines()


def test_a_prunable_worktree_does_not_keep_its_spec_dir_in_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Research R10. A worktree folder deleted by hand keeps its entry in
    `git worktree list`, marked prunable. Counting it would hide the spec dir
    under "In progress" for good, though nothing will ever store it."""
    here, project = _setup(tmp_path)
    _write(here / "470-capability-modeling", "spec.md")
    shutil.rmtree(_worktree_on(project, "470-capability-modeling"))

    code, out = _check(monkeypatch, here, project)

    assert code == 1, out
    assert out.splitlines() == [
        "✗ 1 spec dir not stored",
        "    470-capability-modeling    uncommitted: 1 file",
    ]


def test_every_spec_dir_stored_prints_one_line_and_exits_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`contracts/cli.md`. The "In progress" block is left out when it is
    empty, so a clean store reads as one line."""
    here, project = _setup(tmp_path)
    _worktree_on(project, "359-push-specs-to-trunk")

    code, out = _check(monkeypatch, here, project)

    assert code == 0, out
    assert out.splitlines() == ["✓ every spec dir is stored"]


def test_the_in_progress_block_is_left_out_when_it_is_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`contracts/cli.md`. An empty heading would read as a count of zero that
    the person has to check against the list above it."""
    here, project = _setup(tmp_path)
    _write(here / "188-check-rework-loop", "spec.md")

    code, out = _check(monkeypatch, here, project)

    assert code == 1, out
    assert "In progress" not in out
    assert out.splitlines()[-1] == "    188-check-rework-loop    uncommitted: 1 file"


@pytest.mark.parametrize("kind, sentence", [
    ("in_repo", "is inside the code repository"),
    ("store_no_upstream", "is in a spec store with no upstream branch"),
    ("unmanaged", "is not in a spec store"),
])
def test_a_layout_with_nowhere_to_push_names_the_root_and_exits_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str, sentence: str,
) -> None:
    """FR-024. Nothing can be stored in these layouts, so an exit of 1 would
    fail on every run with no command that could make it pass. The line
    still names the root, so a person can see where the files are."""
    project = git_repo(tmp_path / "project")
    if kind == "in_repo":
        root = project / "specs"
        root.mkdir()
    elif kind == "store_no_upstream":
        root = tmp_path / "project-specs"
        _git(project, "worktree", "add", "-b", "specs-trunk", str(root))
    else:
        root = tmp_path / "notes"
        root.mkdir()
    _write(root / "188-check-rework-loop", "spec.md")

    code, out = _check(monkeypatch, root, project)

    assert code == 0, out
    assert out.splitlines() == [f"ℹ spec root {root} {sentence} — nothing there can be pushed"]


def test_no_git_call_in_the_run_reaches_the_remote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-016. The command is a quick local check a person runs at any time,
    including offline, and a fetch would make it hang on a dead network or
    ask for a password. It compares against git's local copy of the remote."""
    here, project = _setup(tmp_path)
    _write(here / "188-check-rework-loop", "spec.md")
    _commit_unpushed(here, "552-bob-command-rename")
    _worktree_on(project, "359-push-specs-to-trunk")

    real = subprocess.run
    calls: list[list[str]] = []

    def record(args: list[str], *a: object, **kw: object) -> object:
        if args[:1] == ["git"]:
            calls.append(list(args))
        return real(args, *a, **kw)  # type: ignore[call-overload]

    monkeypatch.setattr(subprocess, "run", record)

    code, _ = _check(monkeypatch, here, project)

    assert code == 1
    assert calls, "the check ran no git at all"
    reaching = {"fetch", "pull", "push", "ls-remote", "remote"}
    assert not [c for c in calls if reaching & set(c)]


def test_the_check_group_help_names_the_spec_store() -> None:
    """FR-025. `check` held only `config` until now, and its help line said
    so. A person looking for the spec store check reads this line first."""
    result = CliRunner().invoke(app, ["check", "--help"])

    assert result.exit_code == 0
    assert "Check a repository's configuration and its spec store." in result.output
    assert "specs" in result.output


def test_git_missing_from_path_is_a_one_line_failure_not_a_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The pass reader caught `OSError` from the first draft, and `check specs`
    caught only a failed git command, so a machine with no git on PATH got a
    traceback from the one command meant to report what was left behind."""
    here, project = _setup(tmp_path)
    from wfctl import _spec_store

    def no_git(*_: object, **__: object) -> list[_spec_store.Unstored]:
        raise FileNotFoundError("[Errno 2] No such file or directory: 'git'")

    monkeypatch.setattr(_spec_store, "unstored", no_git)

    code, out = _check(monkeypatch, here, project)

    assert code == 1
    assert out.splitlines() == [
        f"✗ git could not read {here}: [Errno 2] No such file or directory: 'git'"
    ]
