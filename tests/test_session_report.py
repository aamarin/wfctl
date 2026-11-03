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


# --- the report: build and render (US1) ---


from io import StringIO  # noqa: E402

from rich.console import Console  # noqa: E402

from wfctl._session_report import Commit, Readers  # noqa: E402

_BASE = {"version": "1.3", "issue": "432", "branch": "432-x", "session_holder": "self"}


def _readers(**over) -> Readers:
    answers = {
        ("verbs", "view"): ("title:\tSession start\n\nbody text", "ok"),
        ("verbs", "parent"): ("#619 Epic: Faster session start", "ok"),
        ("changes", "branch"): ("#712 Report · checks: failing · 2 unresolved review threads", "ok"),
    }
    answers.update(over.pop("answers", {}))
    calls = over.pop("calls", [])

    def tracker(section, verb, params):
        calls.append((section, verb, params))
        return answers[(section, verb)]

    defaults = dict(
        tracker=tracker,
        commits=lambda key: (1, [Commit("706fc29", "feat: a (#432)", True)]),
        uncommitted=lambda: [],
        handoff=lambda: "# Session Summary\n\n## In Flight\n- asked a question\n",
        last_stop=lambda: "continued",
        accepted_records=lambda: 27,
    )
    defaults.update(over)
    return Readers(**defaults)


def _render(payload: dict) -> str:
    buf = StringIO()
    # Not a terminal, and narrow: how the agent reads the report.
    console = Console(file=buf, width=60, force_terminal=False, color_system=None)
    _session_report.render_session_report(console, payload, trunk="main")
    return buf.getvalue()


def test_an_issue_branch_prints_its_issue_parent_and_pr() -> None:
    payload = _session_report.build_session_report(_BASE, _readers())
    out = _render(payload)
    assert "Issue (tracker text)\ntitle:\tSession start" in out or "Issue (tracker text)\ntitle:" in out
    assert "Parent: #619 Epic: Faster session start" in out
    assert "PR: #712 Report · checks: failing · 2 unresolved review threads" in out
    assert payload["tracker_status"] == {"issue_view": "ok", "parent": "ok", "change": "ok"}


def test_no_parent_and_no_pr_print_none() -> None:
    payload = _session_report.build_session_report(_BASE, _readers(answers={
        ("verbs", "parent"): (None, "none"), ("changes", "branch"): (None, "none"),
    }))
    out = _render(payload)
    assert "Parent: none" in out
    assert "PR: none" in out


@pytest.mark.parametrize("code", ["none", "unsupported", "no-tracker", "bad-config", "failed", "timeout"])
def test_every_reason_code_prints_on_its_line_and_none_is_left_out(code: str) -> None:
    """A branch whose PR has failing checks would otherwise look the same as a
    branch with no PR (`tracker-reads-report-failure`)."""
    payload = _session_report.build_session_report(_BASE, _readers(answers={
        ("verbs", "view"): (None, code), ("verbs", "parent"): (None, code),
        ("changes", "branch"): (None, code),
    }))
    out = _render(payload)
    assert f"Issue (tracker text): {code}" in out
    assert f"Parent: {code}" in out
    assert f"PR: {code}" in out
    assert payload["tracker_status"] == {"issue_view": code, "parent": code, "change": code}
    assert payload["issue_view"] is None and payload["parent"] is None and payload["change"] is None


def test_the_three_reads_run_at_once() -> None:
    """Three 15-second timeouts in a row would hold a session start for 45
    seconds on a network that hangs."""
    import threading
    import time

    barrier = threading.Barrier(3, timeout=5)

    def tracker(section, verb, params):
        barrier.wait()
        time.sleep(0.01)
        return (None, "none")

    _session_report.build_session_report(_BASE, _readers(tracker=tracker))


def test_the_whole_handoff_prints_and_a_missing_one_says_so() -> None:
    out = _render(_session_report.build_session_report(_BASE, _readers()))
    assert "Handoff (session-summary.md)\n# Session Summary\n\n## In Flight\n- asked a question" in out
    out = _render(_session_report.build_session_report(_BASE, _readers(handoff=lambda: None)))
    assert "Handoff: none on this branch" in out


def test_records_print_as_a_count_and_no_list_appears() -> None:
    payload = _session_report.build_session_report(_BASE, _readers())
    out = _render(payload)
    assert "Records: 27 accepted · `wfctl arch context` prints them" in out
    assert payload["accepted_records"] == 27
    for listing in ("issue list", "change list", "OPEN\t"):
        assert listing not in out


def test_the_session_line_carries_the_holder_and_the_last_stop() -> None:
    """Step 8 reads both, and they used to come from two separate reads."""
    payload = _session_report.build_session_report(_BASE, _readers(last_stop=lambda: "wrapped"))
    assert "Session: self · last stop: wrapped" in _render(payload)
    assert payload["last_stop"] == "wrapped" and payload["session_holder"] == "self"


def test_uncommitted_lines_print_under_their_heading() -> None:
    dirty = _session_report.build_session_report(
        _BASE, _readers(uncommitted=lambda: [" M wfctl/cli.py", "?? new.txt"])
    )
    out = _render(dirty)
    assert "Uncommitted\n   M wfctl/cli.py\n  ?? new.txt" in out
    clean = _render(_session_report.build_session_report(_BASE, _readers()))
    assert "Uncommitted: none" in clean


def test_commits_print_with_the_count_and_an_unmentioned_one_marked() -> None:
    payload = _session_report.build_session_report(_BASE, _readers(commits=lambda key: (2, [
        Commit("706fc29", "docs: x (#432)", True), Commit("ab12cd3", "fix typo", False),
    ])))
    out = _render(payload)
    assert "Commits: 2 ahead of main" in out
    assert "  706fc29 docs: x (#432)\n" in out
    assert "  ab12cd3 fix typo  ← doesn't mention #432" in out
    assert payload["commits_ahead"] == 2
    assert payload["commits"][1] == {"sha": "ab12cd3", "subject": "fix typo", "mentions_issue": False}


def test_trunk_not_found_prints_in_place_of_the_count() -> None:
    payload = _session_report.build_session_report(
        _BASE, _readers(commits=lambda key: (None, [Commit("1", "c", None)]))
    )
    assert "Commits: trunk not found" in _render(payload)


_HOSTILE = "- [x] done [/x] :warning: tab\there bell\x07 cr\r end " + "w" * 120


def test_outside_text_prints_as_written_through_a_non_terminal_console() -> None:
    """Through rich's default `console.print`, `[x]` disappears, `[/x]` raises,
    `:warning:` turns into ⚠, and a long line is folded at the console width.
    A tab prints as spaces and control characters are dropped, since neither
    changes what the agent reads (FR-004)."""
    payload = _session_report.build_session_report(_BASE, _readers(
        handoff=lambda: _HOSTILE,
        answers={("verbs", "view"): (_HOSTILE, "ok")},
        commits=lambda key: (1, [Commit("abc", _HOSTILE, True)]),
    ))
    out = _render(payload)
    expected = _HOSTILE.replace("\x07", "").replace("\r", "").replace("\t", "    ")
    assert out.count("- [x] done [/x] :warning:") == 3
    assert "\x07" not in out and "\r" not in out
    assert out.count("w" * 120) == 3
    assert expected.split("tab")[0] in out
    assert payload["handoff"] == _HOSTILE


def test_a_trunk_branch_makes_no_tracker_call_and_prints_not_applicable() -> None:
    """Sessions on `main` are usually exploratory, so a tracker line there
    would be a network call for nothing (US2)."""
    calls: list = []
    base = {**_BASE, "issue": "unknown", "branch": "main"}
    payload = _session_report.build_session_report(base, _readers(calls=calls))
    assert calls == []
    out = _render(payload)
    for line in ("Issue (tracker text): not-applicable", "Parent: not-applicable", "PR: not-applicable"):
        assert line in out
    assert set(payload["tracker_status"].values()) == {"not-applicable"}


# --- which commits mention the branch's issue (US5) ---


@pytest.mark.parametrize(("key", "text", "expected"), [
    ("432", "feat: a (#432)", True),
    ("432", "#432", True),
    ("432", "fix: b (#4321)", False),
    ("432", "costs 432 tokens", False),
    ("432", "fix: c (#43)", False),
    ("PROJ-123", "PROJ-123: thing", True),
    ("PROJ-123", "PROJ-1234: other", False),
])
def test_an_issue_key_is_mentioned_only_as_a_whole_token(key: str, text: str, expected: bool) -> None:
    """A bare `432` matches "432 tokens" in a commit body, so a key that's only
    digits has to be `#432`. A key with its own prefix is matched as itself."""
    assert bool(_session_report._mention_pattern(key).search(text)) is expected


def test_a_mention_in_the_body_counts(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _git(root, "commit", "--allow-empty", "-m", "refactor: tidy", "-m", "Part of #432.")
    _git(root, "commit", "--allow-empty", "-m", "fix typo")
    _, commits = _session_report.read_commits(root, "432")
    assert [(c.subject, c.mentions_issue) for c in commits] == [
        ("fix typo", False), ("refactor: tidy", True), ("feat: a (#432)", True),
    ]


def test_a_trunk_branch_marks_no_commit(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _git(root, "commit", "--allow-empty", "-m", "fix typo")
    _, commits = _session_report.read_commits(root, None)
    assert all(c.mentions_issue is None for c in commits)
