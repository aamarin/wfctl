"""Tests for the worktree spans and `wfctl timings` (#828).

Every test that needs a worktree makes a real one with `git worktree add`, since
the creation time comes from a file git writes and nothing else can stand in for
it.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app
from wfctl.evidence._events import worktree_created
from wfctl.evidence._timings import (
    OpenWorktree,
    compute_summary,
    format_duration,
    load_branch_events,
    main_checkout_branch,
    read_open_worktrees,
    render_summary,
)


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def _linked_worktree(tmp_path: Path) -> tuple[Path, Path]:
    """A repository and one linked worktree, returned with that worktree's admin folder."""
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-q", "-b", "main")
    _git(main, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "x")
    linked = tmp_path / "linked"
    _git(main, "worktree", "add", "-q", "-b", "feature", str(linked))
    admin = Path(_git(linked, "rev-parse", "--absolute-git-dir"))
    return linked, admin


def test_worktree_created_floors_commondir_mtime_to_the_whole_second(tmp_path: Path) -> None:
    """Spans and open worktrees must carry the same value, or the read-time drop that
    matches them by creation time compares two differently rounded numbers (PR-010)."""
    _, admin = _linked_worktree(tmp_path)
    os.utime(admin / "commondir", (1_700_000_000.9, 1_700_000_000.9))
    assert worktree_created(admin) == datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)


def test_worktree_created_is_none_without_a_commondir_file(tmp_path: Path) -> None:
    """The main checkout's git folder has no `commondir`, so it has no creation time."""
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-q")
    assert worktree_created(main / ".git") is None


# --- wfctl timings (#828) -----------------------------------------------------
#
# The compute tests pass a fixed clock, so no figure depends on the day the
# suite runs. The CLI reads the real clock, so its tests date their events
# with `_ago` instead. `NO_COLOR` is pinned in conftest.

runner = CliRunner()
NOW = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)
FMT = "%Y-%m-%dT%H:%M:%SZ"


def _at(days: float = 0, hours: float = 0) -> str:
    return (NOW - timedelta(days=days, hours=hours)).strftime(FMT)


def _ago(days: float) -> str:
    """A timestamp `days` before the real clock, for tests that run the CLI.

    Dated from `NOW`, those events left the CLI's 30-day window a month after
    `NOW`, and every CLI test then failed on a tree nobody had changed.
    """
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime(FMT)


def _span(created: str, removed: str) -> dict:
    return {"ts": removed, "event": "worktree-span", "created": created, "removed": removed}


def _verify(ts: str, seconds: object = 10.0, commands: object = None, **extra: object) -> dict:
    event: dict = {"ts": ts, "event": "verify", "exit": 0, "sha": "abc", "failed": [],
                   "inconclusive": False}
    if seconds is not None:
        event["seconds"] = seconds
    if commands is not None:
        event["commands"] = commands
    return {**event, **extra}


def _cmd(command: object, seconds: object, exit: int = 0) -> dict:
    return {"command": command, "exit": exit, "seconds": seconds}


def _lines(events: dict, days: int | None = 30, open_now: tuple = (), trunk: str = "main") -> list[str]:
    return render_summary(compute_summary(events, list(open_now), trunk, days, NOW))


def _write_log(root: Path, branch: str, events: list[object]) -> None:
    folder = root / branch
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "events.jsonl").write_text("".join(
        (e if isinstance(e, str) else json.dumps(e)) + "\n" for e in events
    ))


# T024 — the loader

def test_the_loader_finds_nested_branch_logs_and_skips_issues_and_bad_lines(tmp_path: Path) -> None:
    """A branch named `release/v0.30.0` sits in a nested folder, so a one-level listing
    misses it (research R3). `.issues` holds review tallies, not a branch."""
    _write_log(tmp_path, "feature-a", [{"ts": _at(1), "event": "start"}, "not json", "[1, 2]"])
    _write_log(tmp_path, "release/v0.30.0", [{"ts": _at(1), "event": "start"}])
    _write_log(tmp_path, ".issues/12", [{"ts": _at(1), "event": "start"}])

    loaded = load_branch_events(tmp_path)

    assert set(loaded) == {"feature-a", "release/v0.30.0"}
    assert len(loaded["feature-a"]) == 1


def test_a_pinned_state_folder_is_one_log_split_by_each_events_branch(tmp_path: Path) -> None:
    """With `WFCTL_STATE_DIR` set every branch shares one log, so it's read as that one file."""
    (tmp_path / "events.jsonl").write_text(
        json.dumps({"ts": _at(1), "event": "start", "branch": "a"}) + "\n"
        + json.dumps({"ts": _at(1), "event": "start", "branch": "b"}) + "\n"
    )
    assert set(load_branch_events(tmp_path, pinned=True)) == {"a", "b"}


def test_a_pinned_log_counts_each_branchs_span_and_verify_under_that_branch(tmp_path: Path) -> None:
    """The span and verify writers now name their branch. Before that, a pinned log
    reported branch `a` as having no span and added a nameless third branch.

    Many other events still carry no branch, such as `next` and the restart
    hook's decisions, so a shared log always holds some. They count toward no
    branch, while a branchless verify run, from a wfctl that predates the
    field, still counts toward the verify figures."""
    (tmp_path / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in [
        {"ts": _at(2), "event": "start", "branch": "a"},
        {"ts": _at(2), "event": "start", "branch": "b"},
        {**_span(_at(3), _at(1)), "branch": "a"},
        {**_verify(_at(1), 5.0), "branch": "b"},
        {"ts": _at(1), "event": "next"},
        _verify(_at(1), 7.0),
    ]))
    summary = compute_summary(load_branch_events(tmp_path, pinned=True), [], "main", 30, NOW, pinned=True)
    assert (summary.branch_count, summary.span_branches, summary.no_span_branches) == (2, 1, 1)
    assert summary.verify_runs == 2


def test_the_loader_skips_saved_work_but_finds_a_branch_nested_under_a_deleted_one(
    tmp_path: Path,
) -> None:
    """A removal saves a worktree's untracked files under `<branch>/unsaved/`, and an
    `events.jsonl` copied there isn't a branch. A state folder outlives its branch,
    so once `a` is deleted a later `a/b` sits inside it, and stopping at the first
    folder holding a log hid it."""
    _write_log(tmp_path, "a", [{"ts": _at(1), "event": "start"}])
    _write_log(tmp_path, "a/b", [{"ts": _at(1), "event": "start"}])
    _write_log(tmp_path, "a/unsaved/copied", [{"ts": _at(1), "event": "start"}])
    _write_log(tmp_path, "a/unsaved.staging/copied", [{"ts": _at(1), "event": "start"}])
    assert set(load_branch_events(tmp_path)) == {"a", "a/b"}


def test_a_branch_named_unsaved_under_a_deleted_branch_is_still_found(tmp_path: Path) -> None:
    """Once branch `a` is deleted, git allows a branch named `a/unsaved`, and its log
    sits in the folder where `a`'s saved files go. Skipping every `unsaved/` folder
    hid that branch. A removal copies each file to its path in the worktree, so a
    log directly inside `unsaved/` would need an untracked `events.jsonl` at the
    worktree's top level. That's rare enough to read the folder as a branch's.

    Once it is a branch's folder, it is walked like any other, so a later branch
    `a/unsaved/b` is found too. Stopping at `a/unsaved` hid it. An `unsaved/` that
    holds no log of its own is still saved work, and the walk stays out of it."""
    _write_log(tmp_path, "a", [{"ts": _at(1), "event": "start"}])
    _write_log(tmp_path, "a/unsaved", [{"ts": _at(1), "event": "start"}])
    _write_log(tmp_path, "a/unsaved/b", [{"ts": _at(1), "event": "start"}])
    _write_log(tmp_path, "c", [{"ts": _at(1), "event": "start"}])
    _write_log(tmp_path, "c/unsaved/x", [{"ts": _at(1), "event": "start"}])
    assert set(load_branch_events(tmp_path)) == {"a", "a/unsaved", "a/unsaved/b", "c"}


def test_a_branch_under_an_unsaved_folder_with_no_log_above_it_is_found(tmp_path: Path) -> None:
    """Two code reviewers on #828 suggested filtering saved-work names in every
    folder, not only beside a log. That hides `x/unsaved/y` when no branch `x` or
    `x/unsaved` ever ran wfctl, since both folders are bare parents with no log.
    A removal logs its span right after saving, so saved work almost always sits
    beside a log, and the filter stays there."""
    _write_log(tmp_path, "x/unsaved/y", [{"ts": _at(1), "event": "start"}])
    assert set(load_branch_events(tmp_path)) == {"x/unsaved/y"}


def test_an_earlier_save_moved_aside_is_skipped_too(tmp_path: Path) -> None:
    """A second removal renames the earlier save to `unsaved-<stamp>/`, and the walk
    went into it, so a log the worktree held anywhere in there counted as a branch."""
    _write_log(tmp_path, "a", [{"ts": _at(1), "event": "start"}])
    _write_log(tmp_path, "a/unsaved-20261120T000000000000Z", [{"ts": _at(1), "event": "start"}])
    _write_log(tmp_path, "a/unsaved-20261120T000000000000Z/x", [{"ts": _at(1), "event": "start"}])
    assert set(load_branch_events(tmp_path)) == {"a"}


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    """A repository with a linked worktree, and a state folder holding two branch logs."""
    from wfctl import _paths

    linked, admin = _linked_worktree(tmp_path)
    # Two days and a half hour old, so the open-now age prints as `2d 0h` on both
    # sides of a second boundary. A worktree made moments ago prints in seconds,
    # and two invocations a second apart then disagree.
    aged = time.time() - 2 * 86400 - 1800
    os.utime(admin / "commondir", (aged, aged))
    main = tmp_path / "main"
    xdg = tmp_path / "xdg"
    monkeypatch.setenv("XDG_STATE_HOME", str(xdg))
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    root = _paths.project_state_dir(main)
    _write_log(root, "one", [_verify(_ago(1), 5.0, [_cmd("x", 5.0)])])
    _write_log(root, "two", [{"ts": _ago(2), "event": "start"}])
    return main, linked, root


def test_main_checkout_and_linked_worktree_read_the_same_logs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both resolve one project state folder, so where the command runs can't change the answer (FR-011)."""
    main, linked, _ = _project(tmp_path, monkeypatch)

    monkeypatch.chdir(main)
    from_main = runner.invoke(app, ["timings"])
    monkeypatch.chdir(linked)
    from_linked = runner.invoke(app, ["timings"])

    assert from_main.exit_code == 0, from_main.output
    assert from_main.output == from_linked.output
    assert "2 branches" in from_main.output


def test_a_pinned_state_folder_says_so_in_the_heading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    main, _, _ = _project(tmp_path, monkeypatch)
    pinned = tmp_path / "pinned"
    pinned.mkdir()
    (pinned / "events.jsonl").write_text(json.dumps(_verify(_ago(1), 5.0)) + "\n")
    monkeypatch.setenv("WFCTL_STATE_DIR", str(pinned))
    monkeypatch.chdir(main)

    result = runner.invoke(app, ["timings"])

    assert "one state folder for every branch (WFCTL_STATE_DIR)" in result.output


# T025 — the spans line

def test_the_spans_line_counts_spans_by_when_they_were_removed() -> None:
    """A worktree made 45 days ago and removed 5 days ago belongs to the last 30 days (acceptance 11)."""
    events = {
        "a": [_span(_at(45), _at(5))],
        "b": [_span(_at(3, 6), _at(3))],
        "c": [_span(_at(60), _at(40))],
    }
    lines = _lines(events)
    assert "  spans     2 across 2 branches · median 20d 3h · max 40d 0h" in lines


def test_a_reversed_or_unparseable_span_is_left_out_of_the_figures() -> None:
    events = {
        "a": [_span(_at(1), _at(2)), _span("not a time", _at(1))],
        "b": [_span(_at(2), _at(1))],
    }
    lines = _lines(events)
    assert "  spans     1 across 1 branch · median 1d 0h · max 1d 0h" in lines
    assert "  no span   1 branch: removed before this shipped, or removed by hand" in lines


# T026 — the open-worktree drop and the dedupe

def test_a_span_matching_an_open_worktrees_creation_time_is_dropped(tmp_path: Path) -> None:
    """The hook runs before workmux removes the worktree, so a failed removal leaves a span
    for a worktree that is still there (research R9). It matches by time, whatever folder
    the span sits in, since a mid-rebase worktree writes into a folder named for a commit.
    """
    linked, admin = _linked_worktree(tmp_path)
    os.utime(admin / "commondir", (1_700_000_000, 1_700_000_000))
    (open_one,) = read_open_worktrees(linked)
    stamp = open_one.created.strftime(FMT)
    other = (open_one.created + timedelta(days=1)).strftime(FMT)
    events = {"3f2a9c1": [_span(stamp, other)], "elsewhere": [_span(_at(3), _at(1))]}

    summary = compute_summary(events, [open_one], "main", None, NOW)

    assert len(summary.span_seconds) == 1


def test_two_spans_for_one_worktree_count_once_with_the_later_removal() -> None:
    created = _at(5)
    events = {"a": [_span(created, _at(4)), _span(created, _at(3))]}
    summary = compute_summary(events, [], "main", 30, NOW)
    assert summary.span_seconds == [2 * 86400.0]


# T027 — open now and the branch read

def test_open_now_reports_the_count_and_the_oldest_age() -> None:
    old = NOW - timedelta(days=3, hours=1)
    lines = _lines({}, open_now=(OpenWorktree(old, "a"), OpenWorktree(NOW - timedelta(hours=2), "b")))
    assert "  open now  2 worktrees · oldest 3d 1h" in lines
    assert "  open now  none" in _lines({})


def test_a_worktree_whose_directory_is_gone_is_not_open(tmp_path: Path) -> None:
    linked, admin = _linked_worktree(tmp_path)
    assert len(read_open_worktrees(linked)) == 1
    (admin / "gitdir").write_text(str(tmp_path / "gone" / ".git") + "\n")
    assert read_open_worktrees(tmp_path / "main") == []


def test_a_relative_gitdir_resolves_against_the_admin_folder(tmp_path: Path) -> None:
    """Newer git can write `gitdir` as a relative path. Resolved against the current
    directory it would point nowhere and the worktree would read as gone (research R5)."""
    linked, admin = _linked_worktree(tmp_path)
    relative = os.path.relpath(linked / ".git", admin)
    (admin / "gitdir").write_text(relative + "\n")
    assert len(read_open_worktrees(tmp_path / "main")) == 1


def test_a_worktree_mid_rebase_keeps_its_branch(tmp_path: Path) -> None:
    """A rebase detaches `HEAD`, so the branch is read from `head-name` instead (research R8)."""
    linked, admin = _linked_worktree(tmp_path)
    assert read_open_worktrees(linked)[0].branch == "feature"
    sha = _git(linked, "rev-parse", "HEAD")
    (admin / "HEAD").write_text(sha + "\n")
    assert read_open_worktrees(linked)[0].branch is None
    (admin / "rebase-merge").mkdir()
    (admin / "rebase-merge" / "head-name").write_text("refs/heads/feature\n")
    assert read_open_worktrees(linked)[0].branch == "feature"


# T028 — the no-span line

def test_the_no_span_line_leaves_out_the_trunk_open_branches_and_branches_with_a_span() -> None:
    recent = {"ts": _at(1), "event": "start"}
    events = {
        "main": [recent], "has-span": [_span(_at(3), _at(1))], "open": [recent],
        "orphan": [recent], "old": [{"ts": _at(90), "event": "start"}],
    }
    lines = _lines(events, open_now=(OpenWorktree(NOW - timedelta(days=1), "open"),))
    assert "  no span   1 branch: removed before this shipped, or removed by hand" in lines


def test_a_remote_tracking_trunk_still_leaves_the_trunk_off_the_no_span_line() -> None:
    """`trunk_branch` answers `origin/main` in most clones, and the trunk's log sits
    under `main`. Compared as written, `main` counted as a removed branch whenever
    the main checkout held a feature branch."""
    events = {"main": [{"ts": _at(1), "event": "start"}]}
    summary = compute_summary(events, [], "origin/main", 30, NOW, main_branch="feature")
    assert summary.no_span_branches == 0


def test_the_branch_checked_out_in_the_main_checkout_is_not_on_the_no_span_line(
    tmp_path: Path,
) -> None:
    """The main checkout has no admin folder under `worktrees/`, so a feature branch
    worked on there was reported as removed, when it is still checked out."""
    linked, _ = _linked_worktree(tmp_path)
    _git(tmp_path / "main", "checkout", "-q", "-b", "in-main")
    assert main_checkout_branch(linked) == "in-main"

    events = {"in-main": [{"ts": _at(1), "event": "start"}]}
    summary = compute_summary(events, [], "main", 30, NOW, main_branch="in-main")
    assert summary.no_span_branches == 0


def test_a_branch_with_one_valid_and_one_malformed_span_is_not_on_the_no_span_line() -> None:
    """FR-014: only a branch with no valid span in the window counts there (PR-011)."""
    events = {"a": [_span(_at(3), _at(1)), _span("bad", "bad")]}
    assert not any("no span" in line for line in _lines(events))


# T029 — the verify table

def test_the_verify_table_counts_timed_runs_and_orders_commands_by_first_appearance() -> None:
    events = {
        "a": [
            _verify(_at(3), 100.0, [_cmd("pytest", 90.0), _cmd("ruff", 2.0)],
                    exit=1, inconclusive=True),
            _verify(_at(2), None),
            _verify(_at(1), 200.0, [_cmd("pytest", 190.0), _cmd("ruff", 4.0)]),
        ],
    }
    lines = _lines(events)
    assert "Verify, 2 of 3 runs carry timings" in lines
    table = [ln for ln in lines if ln.startswith("  ")][3:]
    assert [ln.split()[0] for ln in table[1:]] == ["pytest", "ruff", "whole"]
    assert "2m 20s" in table[1] and "3m 10s" in table[1]
    assert table[2].split()[1:] == ["2", "3s", "4s"]
    assert table[3].split()[:3] == ["whole", "run", "2"]


def test_a_command_with_no_numeric_duration_shows_a_dash() -> None:
    events = {"a": [_verify(_at(1), 3.0, [_cmd("odd-tool", "slow")])]}
    row = next(ln for ln in _lines(events) if "odd-tool" in ln)
    assert row.endswith("—")


def test_the_verify_section_has_three_shapes() -> None:
    assert "Verify, no runs in the last 30 days" in _lines({"a": [{"ts": _at(1), "event": "start"}]})
    untimed = _lines({"a": [_verify(_at(1), None)]})
    assert "Verify, 0 of 1 runs carry timings" in untimed
    assert not any(ln.strip().startswith("command") for ln in untimed)


# T030 — wrong-typed and unparseable fields

def test_malformed_shapes_are_handled_without_raising() -> None:
    """Every field is read by type, so no event line can make the command raise (PR-011)."""
    events = {"a": [
        _verify(_at(1), "fast", [_cmd("a", 1.0)]),
        _verify(_at(1), 5.0, "not a list"),
        _verify(_at(1), 6.0, [_cmd(7, 1.0), "junk", _cmd("kept", "slow")]),
        _verify(_at(1), 7.0, [_cmd("kept", 2.0), _cmd("kept", True)]),
        _verify("yesterday", 8.0, [_cmd("never", 1.0)]),
        {"ts": 5, "event": "verify", "seconds": 1.0},
    ]}
    summary = compute_summary(events, [], "main", 30, NOW)

    assert summary.verify_runs == 4 and summary.verify_timed == 3
    assert summary.whole_run == (6.0, 7.0)
    (row,) = summary.commands
    assert row.command == "kept" and row.runs == 3
    assert (row.seconds_median, row.seconds_max) == (2.0, 2.0)


def test_infinite_and_nan_numbers_are_read_as_absent() -> None:
    """`json.loads` turns `Infinity`, `NaN` and `1e400` into floats, and the
    duration formatter raised on them, against the rule that no line raises.
    A 400-digit integer is a valid JSON int that raises converting to float."""
    events = {"a": [
        _verify(_at(1), float("inf"), [_cmd("x", float("nan"))]),
        _verify(_at(1), 10**400, [_cmd("x", 10**400)]),
        _verify(_at(1), 4.0, [_cmd("x", 3.0)]),
    ]}
    summary = compute_summary(events, [], "main", 30, NOW)
    render_summary(summary)
    assert summary.whole_run == (4.0, 4.0)
    assert summary.commands[0].seconds_max == 3.0


@pytest.mark.parametrize("days", [800_000, 10**10])
def test_a_window_reaching_before_year_one_counts_every_event(days: int) -> None:
    """`now - timedelta(days=N)` overflows past about 739,000 days, and the parser
    accepts any whole number, so `--since 800000d` crashed with a traceback."""
    events = {"a": [_verify(_at(40), 1.0)]}
    summary = compute_summary(events, [], "main", days, NOW)
    assert summary.verify_runs == 1
    assert render_summary(summary)[0] == f"wfctl timings — last {days} days, 1 branch"


# T031 — window and command

def test_the_window_defaults_to_30_days_and_all_prints_its_own_heading(tmp_path: Path) -> None:
    events = {"a": [_verify(_at(10), 1.0), _verify(_at(40), 1.0)]}
    assert _lines(events)[0] == "wfctl timings — last 30 days, 1 branch"
    assert "Verify, 1 of 1 runs carry timings" in _lines(events)
    assert _lines(events, days=90)[0].startswith("wfctl timings — last 90 days")
    assert _lines(events, days=None)[0] == "wfctl timings — all events, 1 branch"


def test_an_invalid_since_is_refused_and_prints_no_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    main, _, _ = _project(tmp_path, monkeypatch)
    monkeypatch.chdir(main)
    # 5,000 digits passes the pattern and then exceeds Python's limit on
    # converting a digit string to an int.
    for bad in ("3w", "0d", "d", "-5d", "9" * 5000 + "d"):
        result = runner.invoke(app, ["timings", "--since", bad])
        assert result.exit_code == 1
        assert "✗ --since takes a number of days, such as 90d, or all" in result.output
        assert "wfctl timings —" not in result.output


def test_an_empty_project_says_there_is_nothing_to_summarize(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-q", "-b", "main")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "empty-xdg"))
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    monkeypatch.chdir(main)
    result = runner.invoke(app, ["timings"])
    assert result.exit_code == 0
    assert "Nothing to summarize — no event logs under" in result.output
    assert "and no open worktrees" in result.output


def test_an_open_worktree_is_reported_before_any_event_log_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The open worktree comes from git, and the command returned early on an empty
    state folder, so a project's first feature showed as nothing to summarize."""
    _linked_worktree(tmp_path)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "empty-xdg"))
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    monkeypatch.chdir(tmp_path / "main")
    result = runner.invoke(app, ["timings"])
    assert result.exit_code == 0, result.output
    assert "Nothing to summarize" not in result.output
    assert "open now  1 worktree" in result.output


def test_no_figure_names_a_branch_and_the_state_folder_is_left_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-018 and FR-019: the command reads and prints, and a branch name would invite a ranking."""
    main, _, root = _project(tmp_path, monkeypatch)
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    monkeypatch.chdir(main)

    result = runner.invoke(app, ["timings"])

    assert result.exit_code == 0
    assert "one" not in result.output.replace("one state", "").split("Verify")[0].split()
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before


# T032 — formatting

@pytest.mark.parametrize(
    ("seconds", "text"),
    [(11, "11s"), (121, "2m 01s"), (3 * 3600 + 12 * 60, "3h 12m"), (86400 + 4 * 3600, "1d 4h"),
     (59.6, "1m 00s"), (0, "0s")],
)
def test_durations_print_in_the_unit_that_fits(seconds: float, text: str) -> None:
    assert format_duration(seconds) == text


# T033 — SC-004

def test_200_branch_logs_compute_in_under_two_seconds(tmp_path: Path) -> None:
    """SC-004. The read is uncached on purpose, so this is what keeps that choice honest."""
    for i in range(200):
        _write_log(tmp_path, f"branch-{i}", [
            {"ts": _at(1), "event": "start"},
            _verify(_at(1), 12.0, [_cmd("pytest", 10.0)]),
            _span(_at(5), _at(1)),
        ] * 10)
    started = time.monotonic()
    events = load_branch_events(tmp_path)
    compute_summary(events, [], "main", 30, NOW)
    assert time.monotonic() - started < 2.0
