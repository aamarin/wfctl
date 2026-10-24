"""Review records: which commits each review group has covered on a branch.

Everything lives in the branch's state directory under `reviews/`, beside
`verify.json`, so `wfctl store specs` never commits it and removing a worktree
keeps it (`622-review-records-in-state-dir.md`):

    reviews/<group>/last-reviewed.json     the group's last reviewed commit
    reviews/<group>/runs/<NNN>/run.json    a run's expected reviewers and commits
    reviews/<group>/runs/<NNN>/<id>.md     one report per reviewer

wfctl, not the coordinating agent, decides whether a report counts and whether
a run is complete, since the agent would otherwise be grading its own panel
(`review-covers-unreviewed-commits`). Only the last reviewed commit, the run
records, and the reports are stored. Which commits are unreviewed is derived
from git on every read.

The guard imports this module on a matched command, so it imports nothing that
loads `typer` or `rich`, and every `git` call takes the caller's timeout.
"""
from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from wfctl import _paths
from wfctl._io import append_event, write_atomic
from wfctl._review_config import Group, Reviewer

TRUNK_MESSAGE = "can't find the trunk branch; set trunk in wfctl.json"

# Matched with `fullmatch`, never `match` and `$`, since `$` also matches
# before a trailing newline and the id becomes a file name.
REVIEWER_ID = re.compile(r"[a-z][0-9]+")

# Seven hex digits is what `git log --oneline` prints, so it is what a reviewer
# copies. Anything shorter can match more than one commit.
_MIN_SHA = 7
_REVIEWED = re.compile(r"^[^A-Za-z0-9\n]*Reviewed:[*_` \t]*([0-9A-Fa-f]+)", re.M)

# The anchor `fanning-out-code-review` has used since #368. It allows
# decoration before the word, so `**Verdict: Approve**` and `## Verdict` both
# count, and refuses other words, so prose that mentions a verdict doesn't.
_VERDICT_ANCHOR = re.compile(r"^[^A-Za-z]*Verdict")
# No letter before the word, so `Disapprove` isn't read as `Approve`. Nothing
# is required after it, so `Approved` and `_Approve_` still count.
_VERDICT_WORD = re.compile(r"(?<![A-Za-z])(?:Approve|Request changes)", re.I)
_FENCE = re.compile(r"`{3,}|~{3,}")

_RELAYED = "Relayed: "


class ReviewError(Exception):
    """A question git or a record couldn't answer. The message names which."""


class NoTrunk(ReviewError):
    def __init__(self) -> None:
        super().__init__(TRUNK_MESSAGE)


class NoRun(ReviewError):
    def __init__(self, group: str) -> None:
        super().__init__(f"{group} has no run; run wfctl review start {group}")


class RelayRefused(ReviewError):
    """A relay wfctl won't save. The message is the line the person reads."""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(
    repo_root: Path, *args: str, timeout: float | None, answers: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[str]:
    """Run git in `repo_root`. An exit code outside `answers` is an error.

    `merge-base --is-ancestor` and `show-ref --verify` exit 1 to say no, which
    is an answer rather than a failure, so their callers pass `(0, 1)`.
    """
    r = subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True, timeout=timeout,
    )
    if r.returncode not in answers:
        detail = r.stderr.strip() or f"exit {r.returncode}"
        raise ReviewError(f"git {args[0]} failed: {detail}")
    return r


# --- the commits a run covers ----------------------------------------------------


@dataclass(frozen=True)
class Range:
    """The commits a group hasn't reviewed, newest first, and the commit they
    follow."""

    base: str
    commits: tuple[str, ...]


def head_commit(repo_root: Path, timeout: float | None = None) -> str:
    return _git(repo_root, "rev-parse", "HEAD", timeout=timeout).stdout.strip()


def _has_ref(repo_root: Path, ref: str, timeout: float | None) -> bool:
    found = _git(
        repo_root, "show-ref", "--verify", "--quiet", ref, timeout=timeout, answers=(0, 1),
    )
    return found.returncode == 0


def trunk_refs(repo_root: Path, timeout: float | None = None) -> list[str]:
    """The trunk branch on `origin` and its local branch, each when it exists,
    by full ref name.

    The remote ref comes first because a person's local `main` usually trails
    it, and excluding only the local branch would list everything merged since
    as the branch's own work. The local one is added because a commit can reach
    the local `main` before it is pushed. `_paths.trunk_branch` names either
    one, since a remote added with `git remote add` has no `origin/HEAD` and
    the trunk then resolves to the local name, so both are looked up.

    Full names because git resolves a short `main` to a tag of that name before
    the branch, and a tag on one of the branch's own commits made that work read
    as already on the trunk. A trunk found under neither name is used as named.
    """
    trunk = _paths.trunk_branch(repo_root, timeout=timeout)
    if trunk is None:
        raise NoTrunk()
    local = trunk.removeprefix("origin/")
    refs = [
        ref for ref in (f"refs/remotes/origin/{local}", f"refs/heads/{local}")
        if _has_ref(repo_root, ref, timeout)
    ]
    return refs or [trunk]


def _is_commit(repo_root: Path, sha: str, timeout: float | None) -> bool:
    """Whether this repository has the commit. One it has never seen is no
    ancestor of anything, and asking `merge-base` about it is an error rather
    than a no."""
    r = _git(
        repo_root, "cat-file", "-e", f"{sha}^{{commit}}", timeout=timeout, answers=(0, 1, 128),
    )
    return r.returncode == 0


def _is_ancestor(repo_root: Path, older: str, newer: str, timeout: float | None) -> bool:
    r = _git(
        repo_root, "merge-base", "--is-ancestor", older, newer,
        timeout=timeout, answers=(0, 1),
    )
    return r.returncode == 0


def commit_range(
    repo_root: Path, head: str, last_reviewed: str | None, timeout: float | None = None,
) -> Range:
    """The commits a group hasn't reviewed at `head` (research.md R3).

    The range starts at the last reviewed commit when it is an ancestor of the
    head, and at the merge base with the trunk otherwise. A rebase leaves the
    last reviewed commit off the branch, and starting there would list commits
    from a history the branch no longer has. Falling back costs one larger
    review and lets nothing through.

    A head that is the last reviewed commit, or one of its ancestors, has
    nothing to review. That happens when reviewed commits aren't pushed yet and
    a merge is judged at the pushed head, and every ancestor of a reviewed
    commit was covered by an earlier complete run.

    `--not` drops every commit that came in from the trunk, and a merge is
    dropped only when git would have made it on its own, so merging `main`
    doesn't force a round. A conflict resolution exists only in the merge
    commit, and dropping every merge would leave it unreviewed. Each merge in
    the range costs up to two more git calls, each under the same timeout.

    The arguments end with `--`, since git otherwise reads a bare `main` as a
    path when one exists and refuses the range as ambiguous.
    """
    refs = trunk_refs(repo_root, timeout)
    base = None
    if last_reviewed is not None and _is_commit(repo_root, last_reviewed, timeout):
        if _is_ancestor(repo_root, head, last_reviewed, timeout):
            return Range(last_reviewed, ())
        if _is_ancestor(repo_root, last_reviewed, head, timeout):
            base = last_reviewed
    if base is None:
        base = _git(repo_root, "merge-base", head, refs[0], timeout=timeout).stdout.strip()
    listed = _git(
        repo_root, "rev-list", "--parents", f"{base}..{head}", "--not", *refs, "--",
        timeout=timeout,
    ).stdout.splitlines()
    commits = []
    for line in listed:
        sha, *parents = line.split()
        if len(parents) < 2 or _has_own_edits(repo_root, sha, parents, timeout):
            commits.append(sha)
    return Range(base, tuple(commits))


def _has_own_edits(
    repo_root: Path, merge: str, parents: list[str], timeout: float | None,
) -> bool:
    """Whether a merge differs from the one git makes from its parents unaided.

    `merge-tree` redoes the merge and exits 1 on a conflict, so any conflict
    counts, whichever side the person kept. A clean redo whose tree differs
    from the merge's own is a merge someone edited, `-s ours` included, which
    drops the trunk's changes without a conflict. `diff-tree --cc` answered
    this before and got both wrong: a conflict resolved by keeping one side
    printed nothing, and a clean merge of nearby lines printed a hunk.

    A merge with more than two parents has no single redo to compare against,
    so it stays in the range.

    The redo passes `--allow-unrelated-histories`, since `git subtree add` and a
    merged orphan branch both make a merge whose parents share no commit.
    Without the flag, git refuses the redo, and every `review start` on that
    branch failed.
    """
    if len(parents) != 2:
        return True
    redone = _git(
        repo_root, "merge-tree", "--write-tree", "--allow-unrelated-histories", *parents,
        timeout=timeout, answers=(0, 1),
    )
    if redone.returncode == 1:
        return True
    own = _git(repo_root, "rev-parse", f"{merge}^{{tree}}", timeout=timeout).stdout.strip()
    return redone.stdout.split("\n", 1)[0].strip() != own


# --- records ---------------------------------------------------------------------


def group_dir(agent_dir: Path, group: str) -> Path:
    return agent_dir / "reviews" / group


def _read_json(path: Path) -> dict[str, object]:
    """A record wfctl wrote, or a `ReviewError` naming the file.

    A half-written or hand-edited record is an error rather than a missing one.
    Read as missing, a broken `last-reviewed.json` would restart the range at
    the merge base and look like a reset nobody asked for.
    """
    try:
        data = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ReviewError(f"can't read {path}: {e}") from e
    if not isinstance(data, dict):
        raise ReviewError(f"can't read {path}: not a JSON object")
    return data


def last_reviewed(agent_dir: Path, group: str) -> str | None:
    """The group's last reviewed commit, or None when no run has completed."""
    path = group_dir(agent_dir, group) / "last-reviewed.json"
    if not path.exists():
        return None
    sha = _read_json(path).get("sha")
    if not isinstance(sha, str) or not sha:
        raise ReviewError(f"can't read {path}: no sha")
    return sha


@dataclass(frozen=True)
class Run:
    number: int
    path: Path
    record: dict[str, object]

    @property
    def head(self) -> str:
        return str(self.record["head"])

    @property
    def reviewers(self) -> list[dict[str, str]]:
        found = self.record.get("reviewers")
        return [r for r in found if isinstance(r, dict)] if isinstance(found, list) else []


def latest_run(agent_dir: Path, group: str) -> Run | None:
    """The highest-numbered run of `group`, or None when it has never started.

    `check` and `relay` act on this run only. An earlier run that never
    completed stays on disk for reading, and its reports never count toward a
    later one.

    A folder with no `run.json` is a start that was interrupted, or one still
    writing, and is passed over. Read as the latest run, it would fail every
    `start`, `check` and `relay` on the group until someone deleted it.
    """
    runs = group_dir(agent_dir, group) / "runs"
    numbers = sorted(
        int(p.name) for p in runs.glob("[0-9][0-9][0-9]*")
        if p.name.isdigit() and (p / "run.json").is_file()
    ) if runs.is_dir() else []
    if not numbers:
        return None
    path = runs / f"{numbers[-1]:03d}"
    record = _read_json(path / "run.json")
    if not isinstance(record.get("head"), str):
        raise ReviewError(f"can't read {path / 'run.json'}: no head")
    return Run(numbers[-1], path, record)


# --- start -----------------------------------------------------------------------


@dataclass(frozen=True)
class Started:
    """What `review start` did. `run` is None when the group was up to date."""

    group: str
    base: str
    head: str
    commits: tuple[str, ...]
    run: Run | None
    reviewers: tuple[dict[str, str], ...]
    # Each model that can't run, with the reason, in the order the group lists it.
    unavailable: dict[str, str]

    @property
    def expected(self) -> list[str]:
        return [r["id"] for r in self.reviewers if r["state"] == "expected"]


def _availability(
    reviewers: Sequence[Reviewer], which: Callable[[str], str | None],
) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Each reviewer as `run.json` records it, and why each missing model can't run.

    wfctl looks a model's command up on `PATH` itself, so the coordinator can't
    simply declare a reviewer unavailable. The lookup runs on the agent's
    `PATH`, which the agent can change, so this is visible rather than
    enforced: the roster and the `⚠` line both name a model left out
    (research.md R7).
    """
    unavailable: dict[str, str] = {}
    entries: list[dict[str, str]] = []
    for r in reviewers:
        entry = {"id": r.id, "model": r.model, "state": "expected"}
        if r.command is not None:
            entry["command"] = r.command
            if r.model not in unavailable:
                # `_review_config.load` refuses a command `shlex` can't split.
                program = (shlex.split(r.command) or [""])[0]
                if not program or which(program) is None:
                    unavailable[r.model] = f"`{program}` not found on PATH"
            if r.model in unavailable:
                entry["state"] = "unavailable"
                entry["reason"] = unavailable[r.model]
        entries.append(entry)
    return entries, unavailable


def start(
    repo_root: Path,
    agent_dir: Path,
    group: Group,
    *,
    timeout: float | None = None,
    which: Callable[[str], str | None] | None = None,
) -> Started:
    """Write the next run record for `group`, or nothing when it's up to date.

    A run is never started with no commits, since there's nothing to review and
    a record would read as a review waiting on reports. A run where no reviewer
    can run is still written, and `check` never completes it.
    """
    head = head_commit(repo_root, timeout)
    found = commit_range(repo_root, head, last_reviewed(agent_dir, group.name), timeout)
    # Resolved when called rather than bound as the default, so `shutil.which`
    # is whatever the module holds at the time.
    reviewers, unavailable = _availability(group.reviewers, which or shutil.which)
    if not found.commits:
        return Started(group.name, found.base, head, (), None, tuple(reviewers), unavailable)

    runs = group_dir(agent_dir, group.name) / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    previous = latest_run(agent_dir, group.name)
    number = (previous.number if previous else 0) + 1
    # `exist_ok=False` so two starts racing for one number can't share a folder.
    while True:
        path = runs / f"{number:03d}"
        try:
            path.mkdir()
            break
        except FileExistsError:
            number += 1
    record: dict[str, object] = {
        "group": group.name,
        "run": number,
        "base": found.base,
        "head": head,
        "commits": list(found.commits),
        "reviewers": reviewers,
        "started_at": _now(),
        "completed_at": None,
    }
    write_atomic(path / "run.json", json.dumps(record, indent=2) + "\n")
    started = Started(
        group.name, found.base, head, found.commits, Run(number, path, record),
        tuple(reviewers), unavailable,
    )
    append_event(
        agent_dir, "review-start", group=group.name, run=number, head=head,
        reviewers=len(started.expected),
    )
    return started


# --- reports ---------------------------------------------------------------------


def judge(text: str, head: str) -> str | None:
    """None when a report counts, or the reason it doesn't (research.md R2).

    A report counts when a `Reviewed: <sha>` line names the run's head, with at
    least seven digits, and its last non-blank line holds `Approve` or
    `Request changes` with the verdict anchor on that line or the non-blank
    line before it. The verdict has to be at the end, so a report cut off after
    an early mention of one carries none. The whole report is read, since a
    reviewer may put the `Reviewed:` line after its findings.
    """
    named = [m.group(1).lower() for m in _REVIEWED.finditer(text)]
    if not named:
        return "no Reviewed: line"
    if not any(len(sha) >= _MIN_SHA and head.lower().startswith(sha) for sha in named):
        return f"names {named[-1][:_MIN_SHA]}, not {head[:_MIN_SHA]}"
    # A reviewer that wraps its report in a code fence ends on the fence, and
    # the verdict is the line inside it.
    lines = [
        line for line in text.splitlines() if line.strip() and not _FENCE.fullmatch(line.strip())
    ]
    last = lines[-1] if lines else ""
    before = lines[-2] if len(lines) > 1 else ""
    if not _VERDICT_WORD.search(last) or not (
        _VERDICT_ANCHOR.match(last) or _VERDICT_ANCHOR.match(before)
    ):
        return "no verdict at the end"
    return None


def _relay_reason(text: str) -> str | None:
    first = text.split("\n", 1)[0]
    return first.removeprefix(_RELAYED).strip() if first.startswith(_RELAYED) else None


@dataclass(frozen=True)
class Entry:
    """One line of the roster. `note` is the reason a report didn't count, or
    the relay reason on a report that did. `expected` is False for a reviewer
    whose model couldn't run, which the run doesn't wait for."""

    id: str
    model: str
    counted: bool
    note: str | None
    expected: bool = True


@dataclass(frozen=True)
class Checked:
    group: str
    run: Run
    entries: tuple[Entry, ...]
    expected: int
    complete: bool

    @property
    def missing(self) -> int:
        return sum(1 for e in self.entries if e.expected and not e.counted)


def _roster(run: Run) -> list[Entry]:
    entries: list[Entry] = []
    for r in run.reviewers:
        rid, model = str(r.get("id", "?")), str(r.get("model", "?"))
        if r.get("state") == "unavailable":
            entries.append(
                Entry(rid, model, False, f"unavailable: {r.get('reason', '')}", expected=False)
            )
            continue
        path = run.path / f"{rid}.md"
        if not REVIEWER_ID.fullmatch(rid) or not path.is_file():
            entries.append(Entry(rid, model, False, "no report"))
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError as e:
            entries.append(Entry(rid, model, False, f"can't read report: {e.strerror}"))
            continue
        reason = judge(text, run.head)
        if reason is not None:
            entries.append(Entry(rid, model, False, reason))
            continue
        relayed = _relay_reason(text)
        entries.append(Entry(rid, model, True, f"relayed: {relayed}" if relayed else None))
    return entries


def check(agent_dir: Path, group: str) -> Checked:
    """Judge the latest run's reports and complete the run when every expected
    reviewer has a counted report.

    The expected reviewers come from the run record, never from the config. A
    config read again here would let a repository drop a reviewer whose report
    was bad and complete the run without it.

    Completion moves `last-reviewed.json` to the run's head, then sets
    `completed_at` and changes nothing else in the run record. A run already
    complete is judged again and left as it is, so `check` is safe to run
    twice. The order matters for a write that fails halfway: a run marked
    complete is never completed again, so `last-reviewed.json` goes first, and
    a failure before the second write leaves a run the next `check` completes.

    A run stays complete when a report changes afterwards. The last reviewed
    commit has already moved, so calling the run incomplete again would
    contradict the record the next run starts from. The roster still shows the
    changed report, and `missing` counts it.
    """
    run = latest_run(agent_dir, group)
    if run is None:
        raise NoRun(group)
    entries = _roster(run)
    expected = sum(1 for e in entries if e.expected)
    if run.record.get("completed_at") is not None:
        return Checked(group, run, tuple(entries), expected, True)
    complete = expected > 0 and all(e.counted for e in entries if e.expected)
    if complete:
        at = _now()
        record = {**run.record, "completed_at": at}
        write_atomic(
            group_dir(agent_dir, group) / "last-reviewed.json",
            json.dumps({"sha": run.head, "run": run.number, "at": at}, indent=2) + "\n",
        )
        write_atomic(run.path / "run.json", json.dumps(record, indent=2) + "\n")
        append_event(agent_dir, "review-complete", group=group, run=run.number, head=run.head)
        run = Run(run.number, run.path, record)
    return Checked(group, run, tuple(entries), expected, complete)


def roster_lines(entries: Sequence[Entry]) -> list[str]:
    """One line per reviewer, such as `s2 claude ✓ relayed: write denied`.

    The model column is padded to the widest model in the run, so a ✓ or ✗
    lines up under the others.
    """
    id_width = max((len(e.id) for e in entries), default=0)
    width = max((len(e.model) for e in entries), default=0)
    lines = []
    for e in entries:
        mark = "✓" if e.counted else "✗"
        note = f" {e.note}" if e.note else ""
        lines.append(f"{e.id:<{id_width}} {e.model:<{width}} {mark}{note}")
    return lines


# --- relay -----------------------------------------------------------------------


def relay(
    agent_dir: Path, groups: Sequence[Group], reviewer: str, reason: str, text: str,
) -> str:
    """Save a blocked reviewer's report as that reviewer's, marked as relayed.

    The report is saved under the reviewer's id in its group's latest run, with
    a header naming the reason, so the roster can show a relay rather than pass
    it off as a report the reviewer wrote
    (`622-blocked-reviewer-relays-report.md`). The group is found by the id's
    letter, which no two groups share. Returns the reason as saved, collapsed to
    one line so it can't add a line to the header.
    """
    reason = " ".join(reason.split())
    if not reason:
        raise RelayRefused("a relay needs --reason saying why the reviewer couldn't write")
    group = next((g for g in groups if g.name[0] == reviewer[:1]), None)
    if group is None or not REVIEWER_ID.fullmatch(reviewer):
        raise RelayRefused(f"{reviewer} isn't a reviewer in any review group")
    run = latest_run(agent_dir, group.name)
    if run is None:
        raise NoRun(group.name)
    listed = {str(r.get("id")) for r in run.reviewers if r.get("state") == "expected"}
    if reviewer not in listed:
        raise RelayRefused(f"{reviewer} isn't a reviewer in {group.name} run {run.number:03d}")
    path = run.path / f"{reviewer}.md"
    if path.exists():
        raise RelayRefused(f"{reviewer} already has a report in run {run.number:03d}")
    write_atomic(path, f"{_RELAYED}{reason}\nRelayed-at: {_now()}\n\n{text}")
    append_event(
        agent_dir, "review-relay", group=group.name, run=run.number, id=reviewer, reason=reason,
    )
    return reason
