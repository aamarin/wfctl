"""`wfctl status --session` prints one report about the branch (#432).

`/start-session` used to read six things and load the repository's open issues
and PRs on every session, though a worktree session works on one issue. The
report reads only the branch's own context, and wfctl builds it so the rule
about what to load is code a test can hold, not skill prose an agent can skip
(`session-start-reads-branch-progress`).

`NO_COLOR` is set once in `conftest.py`, since these assert on console text.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from wfctl import _session_report, _tracker


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True,
    ).stdout


def _repo(tmp_path: Path, *, origin: bool = True, trunk: str | None = None) -> Path:
    """A clone of a bare origin whose default branch is `main`, checked out on
    `432-x` with one commit of its own.

    `trunk`, when set, is committed to `main`'s `wfctl.json` before the clone,
    which is where reviews and the report read it from.
    """
    seed = tmp_path / "seed"
    seed.mkdir()
    _git(seed, "init", "-b", "main")
    _git(seed, "config", "user.email", "t@t")
    _git(seed, "config", "user.name", "T")
    (seed / "README.md").write_text("x\n")
    if trunk is not None:
        (seed / "wfctl.json").write_text(json.dumps({"trunk": trunk}))
    _git(seed, "add", ".")
    _git(seed, "commit", "-m", "init")
    if trunk is not None:
        _git(seed, "branch", trunk)
        _git(seed, "checkout", trunk)
        (seed / "dev.txt").write_text("d\n")
        _git(seed, "add", ".")
        _git(seed, "commit", "-m", "dev only")
        _git(seed, "checkout", "main")
    bare = tmp_path / "origin.git"
    _git(tmp_path, "clone", "--bare", str(seed), str(bare))
    root = tmp_path / "work"
    _git(tmp_path, "clone", str(bare), str(root))
    _git(root, "config", "user.email", "t@t")
    _git(root, "config", "user.name", "T")
    start = f"origin/{trunk}" if trunk else "origin/main"
    _git(root, "checkout", "-b", "432-x", start)
    (root / "a.txt").write_text("a\n")
    _git(root, "add", "a.txt")
    _git(root, "commit", "-m", "feat: a (#432)")
    if not origin:
        _git(root, "remote", "set-head", "origin", "--delete")
    return root


# --- the trunk the commit count runs from (PR-033) ---


def test_a_declared_trunk_counts_from_its_merge_base_on_origin(tmp_path: Path) -> None:
    """A repo that ships from `develop` declares it on the default branch, and
    the count runs from `origin/develop`. Counting from `main` instead would
    include `develop`'s own commit and overstate the branch by one."""
    root = _repo(tmp_path, trunk="develop")
    assert _session_report.commit_range(root) == "origin/develop"
    ahead, commits = _session_report.read_commits(root, "432")
    assert ahead == 1
    assert [c.subject for c in commits] == ["feat: a (#432)"]


def test_no_declaration_counts_from_the_default_branch(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert _session_report.commit_range(root) == "origin/main"
    ahead, _ = _session_report.read_commits(root, "432")
    assert ahead == 1


def test_no_origin_head_is_trunk_not_found_even_with_a_local_main(tmp_path: Path) -> None:
    """`review_trunk` falls back to the working tree's `trunk` here, which the
    agent can edit, so the report doesn't follow it: the spec's last edge case
    says a repo with no `origin/HEAD` reads trunk not found."""
    root = _repo(tmp_path, origin=False)
    assert _git(root, "rev-parse", "--verify", "main")
    assert _session_report.commit_range(root) is None
    ahead, commits = _session_report.read_commits(root, "432")
    assert ahead is None
    assert len(commits) == 2
    assert all(c.mentions_issue is None for c in commits)


@pytest.mark.parametrize("problem", ["missing-ref", "declared-missing"])
def test_every_trunk_error_reads_as_not_found(tmp_path: Path, problem: str) -> None:
    """`review_trunk` raises `ReviewError` or its subclass `NoTrunk` for a trunk
    the clone can't find. The report maps each to trunk not found rather than
    exiting non-zero, since a session start can't stop on a trunk problem."""
    if problem == "missing-ref":
        root = _repo(tmp_path)
        _git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/gone")
    else:
        root = _repo(tmp_path, trunk="develop")
        _git(root, "update-ref", "-d", "refs/remotes/origin/develop")
    assert _session_report.commit_range(root) is None


def test_trunk_not_found_lists_the_last_twenty_commits(tmp_path: Path) -> None:
    root = _repo(tmp_path, origin=False)
    for i in range(25):
        _git(root, "commit", "--allow-empty", "-m", f"c{i}")
    ahead, commits = _session_report.read_commits(root, "432")
    assert ahead is None
    assert len(commits) == 20
    assert commits[0].subject == "c24"


# --- read_text: one reason code per way a tracker line has no answer ---


def _tracker_repo(tmp_path: Path, config: object | None, *, name: str = "fake") -> Path:
    (tmp_path / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": name}))
    if config is not None:
        d = tmp_path / ".agents" / "trackers"
        d.mkdir(parents=True)
        (d / f"{name}.json").write_text(
            config if isinstance(config, str) else json.dumps(config)
        )
    return tmp_path


def test_ok_returns_the_output_as_written(tmp_path: Path) -> None:
    root = _tracker_repo(tmp_path, {"verbs": {"parent": ["printf", "#619 [x] :warning:\\n"]}})
    assert _tracker.read_text(root, "verbs", "parent", {"id": "432"}) == ("#619 [x] :warning:", "ok")


@pytest.mark.parametrize("argv", [["true"], ["printf", "  \\n\\t\\n"]])
def test_exit_zero_with_no_output_or_only_whitespace_is_none(tmp_path: Path, argv: list) -> None:
    """A line of blanks is no answer, and printed as one it would read as a
    parent nobody can name."""
    root = _tracker_repo(tmp_path, {"verbs": {"parent": argv}})
    assert _tracker.read_text(root, "verbs", "parent", {"id": "1"}) == (None, "none")


def test_a_verb_the_backend_leaves_out_is_unsupported(tmp_path: Path) -> None:
    root = _tracker_repo(tmp_path, {"verbs": {"view": ["true"]}})
    assert _tracker.read_text(root, "verbs", "parent", {"id": "1"}) == (None, "unsupported")


def test_a_repo_with_no_tracker_is_no_tracker(tmp_path: Path) -> None:
    (tmp_path / ".wf-skills-manifest.json").write_text("{}")
    assert _tracker.read_text(tmp_path, "verbs", "view", {"id": "1"}) == (None, "no-tracker")


@pytest.mark.parametrize("config", [
    "{not json",
    {"verbs": {"parent": "true"}},
    {"verbs": {"parent": ["echo", "{title}"]}},
])
def test_an_unreadable_or_malformed_config_is_bad_config(tmp_path: Path, config: object) -> None:
    """An unparseable file, a verb that isn't a list, and a placeholder wfctl
    has no value for are all a config to fix, not a tracker that's down."""
    root = _tracker_repo(tmp_path, config)
    assert _tracker.read_text(root, "verbs", "parent", {"id": "1"}) == (None, "bad-config")


def test_a_non_zero_exit_with_no_output_is_failed(tmp_path: Path) -> None:
    root = _tracker_repo(tmp_path, {"verbs": {"parent": ["false"]}})
    assert _tracker.read_text(root, "verbs", "parent", {"id": "1"}) == (None, "failed")


def test_a_command_that_cannot_launch_is_failed(tmp_path: Path) -> None:
    """An `OSError` at launch, such as a missing `gh`, is a lookup that didn't
    happen, which the report must not show as `none`."""
    root = _tracker_repo(tmp_path, {"verbs": {"parent": ["/no/such/binary"]}})
    assert _tracker.read_text(root, "verbs", "parent", {"id": "1"}) == (None, "failed")


def test_no_answer_within_the_bound_is_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _tracker_repo(tmp_path, {"verbs": {"parent": ["sleep", "5"]}})

    def slow(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, kwargs.get("timeout", 15))

    monkeypatch.setattr(_tracker.subprocess, "run", slow)
    assert _tracker.read_text(root, "verbs", "parent", {"id": "1"}) == (None, "timeout")
