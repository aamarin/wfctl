"""`wfctl timings`: how long features keep a worktree open and what verify costs.

Everything here is computed from the event logs and git's worktree folder each
time it runs, and nothing is stored (`session-state-is-re-derived`). A stored
median would go stale as soon as another run landed.

The module has three jobs, kept as three functions so each can be tested without
the others: load every branch's events, compute the summary from them, and
render it. The compute function takes `now` as an argument so a test fixes the
clock. The renderer prints no branch name, since the figures are for sizing a
machine and a name would invite reading them as a ranking (FR-019).

Every field is read by type. A line that parses but holds the wrong shape counts
as absent, and no event line can make the command raise.
"""
from __future__ import annotations

import math
import os
import statistics
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import NamedTuple

from wfctl._paths import SAVED_WORK_DIR, SAVED_WORK_STAGING_DIR, is_moved_save

from ._events import read_events, worktree_created

_TS = "%Y-%m-%dT%H:%M:%SZ"
_ISSUES_DIR = ".issues"
_SAVED_WORK_DIRS = frozenset({SAVED_WORK_DIR, SAVED_WORK_STAGING_DIR})


class OpenWorktree(NamedTuple):
    """A worktree git still has: when it was made and which branch it holds, if known."""

    created: datetime
    branch: str | None


class CommandRow(NamedTuple):
    """The verify figures for one distinct command text."""

    command: str
    runs: int
    seconds_median: float | None
    seconds_max: float | None


@dataclass
class Summary:
    """What `wfctl timings` prints, as values. Never written anywhere."""

    window_days: int | None
    pinned: bool
    branch_count: int
    span_seconds: list[float] = field(default_factory=list)
    span_branches: int = 0
    open_count: int = 0
    open_oldest_seconds: float | None = None
    no_span_branches: int = 0
    verify_runs: int = 0
    verify_timed: int = 0
    commands: list[CommandRow] = field(default_factory=list)
    whole_run: tuple[float, float] | None = None


def _parse(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, _TS).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _number(value: object) -> float | None:
    """A finite JSON number, and not a bool, which Python would otherwise accept as 0 or 1.

    `json.loads` reads `Infinity`, `NaN` and `1e400` as floats, and the
    formatters can't print them. A JSON integer with hundreds of digits is valid
    and raises converting to a float.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if math.isfinite(number) else None


def load_branch_events(root: Path, pinned: bool = False) -> dict[str, list[dict]]:
    """Every branch's events, keyed by the branch's path under the project state folder.

    A branch name with a slash, such as `release/v0.30.0`, sits in a nested
    folder, so this walks the whole tree instead of listing one level
    (research R3). `.issues` holds review tallies and no branch, and git refuses
    a branch name that starts with a dot, so skipping it can't hide one.

    The walk doesn't enter the `unsaved/` and `unsaved.staging/` folders beside a
    branch's log, or an earlier save moved aside as `unsaved-<stamp>/`. A removal
    copies a worktree's untracked files there, so they can be large and can hold
    an `events.jsonl` that isn't a branch's. Every other folder is walked,
    because a state folder outlives its branch, and once `a` is deleted a later
    branch `a/b` sits inside it.

    That later branch can be named `a/unsaved`, so an `unsaved/` or
    `unsaved.staging/` folder that holds its own `events.jsonl` is a branch's
    folder and is walked like any other, which also finds `a/unsaved/b`. A
    removal keeps each file's path in the worktree, so saved work puts a log
    there only if the worktree had an untracked `events.jsonl` at its top level.
    In that case the saved files under it are walked too, and any log in them
    adds a branch and its events to every figure.

    The folder name is the only way to tell saved work from a branch, so one
    case is still missed. If `a` logged events and `a/unsaved` was never a
    branch, a later branch `a/unsaved/b` sits under an `unsaved/` with no log of
    its own, and the walk skips it as saved work. Telling the two apart needs
    the removal to mark the folders it writes, as described in #834.

    A folder with no log of its own is walked without this filter. A removal
    writes its `worktree-span` event right after it saves, so saved work sits
    beside a log in most cases. On a branch that never logged an event, it
    doesn't when the span write failed or was skipped, when a wfctl that
    predates the span event did the removal, or when someone ran `wfctl archive
    unsaved` by hand, which saves without writing a span. A folder with no log
    is usually a bare parent, such as `x/` above a branch `x/unsaved/y`, or a
    branch that hasn't logged yet, and filtering it would hide a branch below.

    With `WFCTL_STATE_DIR` set, every branch shares the one log in `root`. Its
    events are split by their own `branch` field, and the ones that carry none
    stay together under one name.
    """
    if pinned:
        by_branch: dict[str, list[dict]] = {}
        for event in read_events(root):
            name = event.get("branch")
            by_branch.setdefault(name if isinstance(name, str) else "", []).append(event)
        return by_branch
    logs: dict[str, list[dict]] = {}
    for folder, subfolders, files in os.walk(root):
        relative = Path(folder).relative_to(root)
        if relative.parts and relative.parts[0] == _ISSUES_DIR:
            subfolders.clear()
            continue
        if "events.jsonl" in files:
            subfolders[:] = [
                s for s in subfolders
                if not is_moved_save(s)
                and (s not in _SAVED_WORK_DIRS or (Path(folder) / s / "events.jsonl").is_file())
            ]
            logs[relative.as_posix()] = read_events(Path(folder))
    return dict(sorted(logs.items()))


def _admin_branch(admin: Path) -> str | None:
    """The branch a worktree holds, read from its admin folder (research R8).

    `HEAD` names the branch directly. A rebase in progress detaches `HEAD` and
    records the branch in `rebase-merge/head-name` or `rebase-apply/head-name`,
    so reading it keeps a branch mid-rebase off the no-span line.
    """
    try:
        head = (admin / "HEAD").read_text().strip()
    except OSError:
        return None
    prefix = "ref: refs/heads/"
    if head.startswith(prefix):
        return head[len(prefix):]
    for name in ("rebase-merge", "rebase-apply"):
        try:
            recorded = (admin / name / "head-name").read_text().strip()
        except OSError:
            continue
        if recorded.startswith("refs/heads/"):
            return recorded[len("refs/heads/"):]
    return None


def read_open_worktrees(repo_root: Path) -> list[OpenWorktree]:
    """The worktrees git still has, from `<git common dir>/worktrees/*/` (research R5).

    An entry is open when its `gitdir` file names a path that exists. That's the
    same test `git worktree list` uses to mark an entry `prunable`. A relative
    path, which newer git can write, resolves against the admin folder holding
    the file, not against the current directory.
    """
    probe = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=repo_root, capture_output=True, text=True,
    )
    if probe.returncode != 0 or not probe.stdout.strip():
        return []
    admin_root = Path(probe.stdout.strip()) / "worktrees"
    try:
        entries = sorted(p for p in admin_root.iterdir() if p.is_dir())
    except OSError:
        return []
    found = []
    for admin in entries:
        try:
            target = Path((admin / "gitdir").read_text().strip())
        except OSError:
            continue
        if not (admin / target).exists():
            continue
        created = worktree_created(admin)
        if created is not None:
            found.append(OpenWorktree(created, _admin_branch(admin)))
    return found


def main_checkout_branch(repo_root: Path) -> str | None:
    """The branch checked out in the main checkout, which `worktrees/` doesn't list.

    The main checkout's admin folder is the git common dir itself, so the same
    `HEAD` and rebase reads apply. A feature branch worked on there is still
    checked out, and leaving it off would report it as removed.
    """
    probe = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=repo_root, capture_output=True, text=True,
    )
    if probe.returncode != 0 or not probe.stdout.strip():
        return None
    return _admin_branch(Path(probe.stdout.strip()))


def _stats(values: list[float]) -> tuple[float, float] | None:
    return (statistics.median(values), max(values)) if values else None


def compute_summary(
    events_by_branch: dict[str, list[dict]],
    open_worktrees: list[OpenWorktree],
    trunk: str | None,
    window_days: int | None,
    now: datetime,
    pinned: bool = False,
    main_branch: str | None = None,
) -> Summary:
    """Build the summary from the loaded events, the open worktrees, and the trunk name.

    A window reaching back before year 1 can't be a datetime, and it covers every
    event there is, so it counts the same as `all`.
    """
    try:
        start = None if window_days is None else now - timedelta(days=window_days)
    except OverflowError:
        start = None

    def in_window(moment: datetime | None) -> bool:
        return moment is not None and (start is None or moment >= start) and moment <= now

    open_created = {w.created for w in open_worktrees}
    open_branches = {w.branch for w in open_worktrees if w.branch}
    if main_branch:
        open_branches.add(main_branch)

    active: set[str] = set()
    spans: dict[tuple[str, datetime], datetime] = {}
    verifies: list[tuple[datetime, dict]] = []
    for branch, events in events_by_branch.items():
        for event in events:
            moment = _parse(event.get("ts"))
            # A shared `WFCTL_STATE_DIR` log puts every event without a `branch`
            # field under `""`. Many event kinds carry none, so that key names
            # no branch and stays out of the branch counts, while its verify
            # runs still count toward the verify figures.
            if branch and in_window(moment):
                active.add(branch)
            kind = event.get("event")
            if kind == "worktree-span":
                created, removed = _parse(event.get("created")), _parse(event.get("removed"))
                if created is None or removed is None or removed < created:
                    continue
                if created in open_created:
                    # The hook runs before workmux deletes the worktree, so this
                    # span can describe one that is still there (research R9).
                    # The match ignores the branch, since a detached worktree's
                    # span is written under a short sha (PR-009). Two worktrees
                    # made in the same second can therefore hide a removed one's
                    # span behind an open one.
                    continue
                if in_window(removed):
                    key = (branch, created)
                    spans[key] = max(removed, spans.get(key, removed))
            elif kind == "verify" and moment is not None and in_window(moment):
                verifies.append((moment, event))

    summary = Summary(window_days=window_days, pinned=pinned, branch_count=len(active))
    summary.span_seconds = [(r - c).total_seconds() for (_, c), r in spans.items()]
    summary.span_branches = len({branch for branch, _ in spans})
    summary.open_count = len(open_worktrees)
    if open_worktrees:
        summary.open_oldest_seconds = (now - min(open_created)).total_seconds()
    with_span = {branch for branch, _ in spans}
    # `trunk_branch` usually answers `origin/main`, and the trunk's log is
    # keyed by the local name.
    local_trunk = trunk.removeprefix("origin/") if trunk else None
    summary.no_span_branches = len(
        {b for b in active if b not in with_span and b not in open_branches and b != local_trunk}
    )

    summary.verify_runs = len(verifies)
    summary.verify_timed, summary.whole_run, summary.commands = _verify_figures(
        [event for _, event in sorted(verifies, key=lambda pair: pair[0])]
    )
    return summary


def _verify_figures(
    runs: list[dict],
) -> tuple[int, tuple[float, float] | None, list[CommandRow]]:
    """How many runs carry timings, the whole-run spread, and one row per command.

    `runs` arrive oldest first, so the rows come out in first-appearance order,
    which reads as the order of the repository's `verify` list. A run without a
    numeric `seconds` predates the timings and is left out of every figure here.
    A command entry with the wrong shape is dropped, and one whose `seconds` has
    the wrong type counts as a run with no duration (PR-011).
    """
    whole: list[float] = []
    order: list[str] = []
    seconds: dict[str, list[float]] = {}
    counts: dict[str, int] = {}
    for event in runs:
        total = _number(event.get("seconds"))
        if total is None:
            continue
        whole.append(total)
        entries = event.get("commands")
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("command"), str):
                continue
            name = entry["command"]
            if name not in counts:
                order.append(name)
                counts[name], seconds[name] = 0, []
            counts[name] += 1
            if (duration := _number(entry.get("seconds"))) is not None:
                seconds[name].append(duration)
    rows = []
    for name in order:
        sec = _stats(seconds[name])
        rows.append(
            CommandRow(name, counts[name], sec[0] if sec else None, sec[1] if sec else None)
        )
    return len(whole), _stats(whole), rows


def format_duration(seconds: float) -> str:
    """Days and hours, hours and minutes, minutes and seconds, or seconds, by size."""
    total = int(round(seconds))
    days, rest = divmod(total, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def _plural(count: int, word: str) -> str:
    if count == 1:
        return f"{count} {word}"
    return f"{count} {word}{'es' if word.endswith('ch') else 's'}"


def render_summary(summary: Summary) -> list[str]:
    """The lines `contracts/wfctl-timings.md` shows, with no branch named."""
    days = summary.window_days
    scope = "all events" if days is None else f"last {days} days"
    heading = f"wfctl timings — {scope}, {_plural(summary.branch_count, 'branch')}"
    if summary.pinned:
        heading += " · one state folder for every branch (WFCTL_STATE_DIR)"
    lines = [heading, "", "Feature time, worktree created to removed"]

    if summary.span_seconds:
        median, top = statistics.median(summary.span_seconds), max(summary.span_seconds)
        lines.append(
            f"  spans     {len(summary.span_seconds)} across "
            f"{_plural(summary.span_branches, 'branch')} · "
            f"median {format_duration(median)} · max {format_duration(top)}"
        )
    else:
        lines.append("  spans     none" + ("" if days is None else f" in the last {days} days"))
    if summary.open_count:
        oldest = format_duration(summary.open_oldest_seconds or 0)
        lines.append(
            f"  open now  {_plural(summary.open_count, 'worktree')} · oldest {oldest}"
        )
    else:
        lines.append("  open now  none")
    if summary.no_span_branches:
        lines.append(
            f"  no span   {_plural(summary.no_span_branches, 'branch')}: "
            "removed before this shipped, or removed by hand"
        )

    lines.append("")
    if not summary.verify_runs:
        lines.append("Verify, no runs" + ("" if days is None else f" in the last {days} days"))
        return lines
    lines.append(
        f"Verify, {summary.verify_timed} of {summary.verify_runs} runs carry timings"
    )
    if not summary.verify_timed:
        return lines

    header = ("command", "runs", "median", "max")
    rows = [
        (
            row.command, str(row.runs),
            format_duration(row.seconds_median) if row.seconds_median is not None else "—",
            format_duration(row.seconds_max) if row.seconds_max is not None else "—",
        )
        for row in summary.commands
    ]
    if summary.whole_run is not None:
        whole_median, whole_max = summary.whole_run
        rows.append(
            ("whole run", str(summary.verify_timed),
             format_duration(whole_median), format_duration(whole_max))
        )
    widths = [max(len(header[i]), *(len(r[i]) for r in rows)) for i in range(4)]

    def line(cells: tuple[str, ...]) -> str:
        left = cells[0].ljust(widths[0])
        numbers = "  ".join(cells[i].rjust(widths[i]) for i in (1, 2, 3))
        return f"  {left}  {numbers}"

    lines.append(line(header))
    lines.extend(line(r) for r in rows)
    return lines
