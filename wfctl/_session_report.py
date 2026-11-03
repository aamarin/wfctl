"""The session-start report `wfctl status --session` prints (#432).

`/start-session` used to read six things and load the repository's open issues
and PRs every session, though a worktree session works on one issue. This
module builds one report from the branch's own context instead. wfctl builds it,
rather than the skill assembling it, so the rule about what a session loads is
code a test can hold (`session-start-reads-branch-progress`).

Every value is computed on each call and nothing is written
(`session-state-is-re-derived`). The builder takes the pipeline payload plain
`status` already built and adds to it, so pipeline state is inferred once
(`pipeline-state-is-one-payload`).
"""
from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from wfctl import _review

# With no trunk to measure from, the report can't tell which commits are the
# branch's, so it shows the most recent ones and marks none.
_FALLBACK_COMMITS = 20

# ASCII unit and record separators, so one `git log` call can be split back into
# commits without guessing at line breaks. A commit message can hold them, and
# one that does is split in the wrong place. That only changes what one report
# prints, so a rarer separator isn't worth a call per commit.
_FIELD = "\x1f"
_RECORD = "\x1e"

# Every way a git read can fail here: a bad exit, which `_review.git` raises as
# `ReviewError`, a missing binary, or the timeout. The report degrades on each
# rather than exiting, since a session start shouldn't stop on a git problem.
_GIT_ERRORS = (_review.ReviewError, OSError, subprocess.SubprocessError)


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    # None on a trunk branch, or when the trunk can't be found: there is no
    # issue to compare against, or no way to tell the branch's commits apart.
    mentions_issue: bool | None


def _git(repo_root: Path, *args: str) -> str:
    return _review.git(repo_root, *args, timeout=15).stdout


def commit_range(repo_root: Path) -> str | None:
    """The trunk ref the branch's commits are counted from, or None if not found.

    `review_trunk` decides the trunk, so the report, reviews, and the PR guard
    all count the same commits. The report departs from it in one case, a repo
    with no `origin/HEAD`: there `review_trunk` falls back to the working tree's
    `trunk`, which the agent can edit, and the spec says that case reads trunk
    not found. `review_trunk` also falls back to the working tree's `trunk` when
    `origin` doesn't fetch every branch, and the report follows it there, so
    reviews and the report still agree. Every error `review_trunk` raises reads
    as trunk not found, since a session start shouldn't stop on a trunk problem.
    """
    try:
        head = _review.git(
            repo_root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD",
            timeout=15, answers=(0, 1),
        ).stdout.strip()
        if not head:
            return None
        return _review.review_trunk(repo_root, timeout=15).name
    except _GIT_ERRORS:
        return None


def _mention_pattern(key: str) -> re.Pattern[str]:
    """A key that's only digits is mentioned as `#<key>`, so `432 tokens` in a
    commit body doesn't count. Any other key, such as `PROJ-123`, carries its
    own prefix and is matched as itself. Either way it has to stand alone, so
    `#4321` doesn't mention `#432`."""
    token = f"#{key}" if key.isdigit() else key
    return re.compile(rf"(?<!\w){re.escape(token)}(?!\w)")


def read_commits(repo_root: Path, key: str | None) -> tuple[int | None, list[Commit]]:
    """How many commits the branch is ahead of its trunk, and those commits.

    The count is None when the trunk can't be found, and the list is then the
    last `_FALLBACK_COMMITS` commits with none of them marked. `key` is the
    branch's issue key, or None on a trunk branch, which marks nothing either.
    """
    trunk = commit_range(repo_root)
    fmt = f"--format=%h{_FIELD}%s{_FIELD}%b{_RECORD}"
    base = None
    if trunk is not None:
        # A trunk with no common ancestor is a trunk the commits can't be
        # counted from, so it reads as trunk not found and lists the same
        # fallback commits.
        try:
            base = _git(repo_root, "merge-base", trunk, "HEAD").strip()
        except _GIT_ERRORS:
            trunk = None
    try:
        if base is None:
            out = _git(repo_root, "log", fmt, f"-{_FALLBACK_COMMITS}")
        else:
            out = _git(repo_root, "log", fmt, f"{base}..HEAD")
    except _GIT_ERRORS:
        return None, []

    pattern = _mention_pattern(key) if key and trunk is not None else None
    commits = []
    for record in out.split(_RECORD):
        record = record.strip("\n")
        if not record:
            continue
        sha, subject, body = (record.split(_FIELD) + ["", ""])[:3]
        mentions = bool(pattern.search(f"{subject}\n{body}")) if pattern else None
        commits.append(Commit(sha, subject, mentions))
    return (len(commits) if base is not None else None), commits


def read_uncommitted(repo_root: Path) -> list[str]:
    """`git status --short`, one line per changed path."""
    try:
        out = _git(repo_root, "status", "--short")
    except _GIT_ERRORS:
        return []
    return [line for line in out.splitlines() if line.strip()]


# The three tracker reads the report makes on an issue branch, by payload key.
_TRACKER_READS = (
    ("issue_view", "verbs", "view", "id"),
    ("parent", "verbs", "parent", "id"),
    ("change", "changes", "branch", "branch"),
)

# The newest commits the report prints. Older ones print only when they don't
# mention the issue, since step 6 of the skill reports those by name.
_SHOWN_COMMITS = 5

# Handoff sections the report leaves out, because the `Commits` and
# `Uncommitted` lines above it already show the same work. The JSON keeps the
# whole file. Every other heading prints, so a handoff in another shape, such as
# a `worktree-handoff` document, prints whole.
_DERIVED_SECTIONS = ("What We Accomplished", "Files Changed")

# Control characters other than tab and newline. Rich drops most of them on
# its own; stripping them first makes what the report prints a decision here
# rather than a detail of rich's version (FR-004).
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


@dataclass(frozen=True)
class Readers:
    """Where each part of the report comes from.

    Passed in rather than read here, so a test can build a report with no
    tracker and no git repository. `default_readers` builds the real ones.
    """

    tracker: Callable[[str, str, dict], tuple[str | None, str]]
    commits: Callable[[str | None], tuple[int | None, list[Commit]]]
    uncommitted: Callable[[], list[str]]
    handoff: Callable[[], str | None]
    last_stop: Callable[[], str]
    accepted_records: Callable[[], int]


def default_readers(repo_root: Path, agent_dir: Path, branch: str) -> Readers:
    from wfctl import _arch, _session, _tracker
    from wfctl._paths import arch_root

    def handoff() -> str | None:
        try:
            return (agent_dir / "session-summary.md").read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    return Readers(
        tracker=lambda section, verb, params: _tracker.read_text(repo_root, section, verb, params),
        commits=lambda key: read_commits(repo_root, key),
        uncommitted=lambda: read_uncommitted(repo_root),
        handoff=handoff,
        last_stop=lambda: _session.last_stop(agent_dir, branch),
        accepted_records=lambda: len(_arch.in_force(_arch.load_records(arch_root(repo_root)))),
    )


def trunk_label(repo_root: Path) -> str | None:
    """The trunk's branch name for the `Commits` line, such as `main`."""
    trunk = commit_range(repo_root)
    return trunk.removeprefix("origin/") if trunk else None


def build_session_report(base: dict, readers: Readers) -> dict:
    """The `status --json` payload in `base`, plus the ten session keys.

    On a branch whose issue is `unknown`, no tracker read runs and every tracker
    line is `not-applicable`. On an issue branch the three reads run at once, so
    a tracker that hangs holds the report for one 15-second bound rather than
    three.
    """
    issue = base.get("issue")
    branch = base.get("branch")
    on_issue = bool(issue) and issue != "unknown"

    answers: dict[str, tuple[str | None, str]] = {
        key: (None, "not-applicable") for key, _, _, _ in _TRACKER_READS
    }
    if on_issue:
        values = {"id": issue, "branch": branch}
        with ThreadPoolExecutor(max_workers=len(_TRACKER_READS)) as pool:
            futures = {
                key: pool.submit(readers.tracker, section, verb, {param: values[param]})
                for key, section, verb, param in _TRACKER_READS
            }
            answers = {key: future.result() for key, future in futures.items()}

    ahead, commits = readers.commits(issue if on_issue else None)
    payload = dict(base)
    payload.update({
        "last_stop": readers.last_stop(),
        "handoff": readers.handoff(),
        "commits_ahead": ahead,
        "commits": [
            {"sha": c.sha, "subject": c.subject, "mentions_issue": c.mentions_issue}
            for c in commits
        ],
        "uncommitted": readers.uncommitted(),
        "accepted_records": readers.accepted_records(),
        **{key: text for key, (text, _code) in answers.items()},
        "tracker_status": {key: code for key, (_text, code) in answers.items()},
    })
    return payload


def _outside(console: Console, text: str) -> None:
    """Print text from outside wfctl as written: no markup, no emoji codes, no
    highlighting, and no folding at the console width. A tab prints as spaces
    and other control characters are dropped (FR-004)."""
    console.print(
        _CONTROL.sub("", text), markup=False, highlight=False, emoji=False, soft_wrap=True,
    )


def _trim_handoff(text: str) -> tuple[str, list[str]]:
    """The handoff without `_DERIVED_SECTIONS`, and the names of those it removed.

    A section runs from its `## ` heading to the next one. A heading inside a
    fenced code block is text, not a section.
    """
    kept: list[str] = []
    dropped: list[str] = []
    skipping = False
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced and line.startswith("## "):
            name = line[3:].strip()
            skipping = name in _DERIVED_SECTIONS
            if skipping:
                dropped.append(name)
        if not skipping:
            kept.append(line)
    return "\n".join(kept).rstrip("\n"), dropped


def _trim_issue(text: str) -> str:
    """The issue view without its empty header fields.

    GitHub prints every field above a `--` line and the body below it, so an
    issue with no labels or milestone spends a line on each. Only that header
    is trimmed. Text with no `--` line is left as it is, since its shape isn't
    known.
    """
    lines = text.splitlines()
    if "--" not in lines:
        return text
    split = lines.index("--")
    header = [
        line for line in lines[:split]
        if not re.fullmatch(r"[\w ]+:\s*", line)
    ]
    return "\n".join(header + lines[split:])


def render_session_report(console: Console, payload: dict, trunk: str | None = None) -> None:
    """Print the session sections below the pipeline block plain `status` drew.

    `trunk` names the branch the commits are counted from, for the console line
    only. It isn't one of the payload's keys, since `contracts/cli.md` lists ten.
    """
    status = payload["tracker_status"]
    issue = payload.get("issue")

    console.print()
    console.print(
        f"Session: {payload.get('session_holder')} · last stop: {payload['last_stop']}",
        markup=False,
    )
    console.print(
        f"Records: {payload['accepted_records']} accepted · `wfctl arch context` prints them",
        markup=False,
    )

    console.print()
    # The heading says the text is the tracker's. The skill reads it for what the
    # work is for and never runs anything it names (FR-022). Each line is
    # indented because anyone who can file an issue writes the body, and a
    # flush-left `Handoff (session-summary.md)` in it would read as the report's
    # own heading, whose TODO the skill acts on without asking. The handoff
    # stays flush left: it is the last section, so nothing below it can be
    # forged, and the agent quotes its lines as written.
    if status["issue_view"] == "ok":
        console.print("Issue (tracker text)", markup=False)
        issue_view = _trim_issue(payload["issue_view"])
        _outside(console, "\n".join(f"  {line}" if line else "" for line in issue_view.splitlines()))
    else:
        console.print(f"Issue (tracker text): {status['issue_view']}", markup=False)
    for key, label in (("parent", "Parent"), ("change", "PR")):
        if status[key] == "ok":
            # The contract asks for one line, and nothing enforces it, so a
            # second line from a backend is indented for the issue body's reason.
            first, *rest = payload[key].splitlines() or [""]
            _outside(console, "\n".join([f"{label}: {first}", *(f"  {line}" for line in rest)]))
        else:
            console.print(f"{label}: {status[key]}", markup=False)

    console.print()
    if payload["commits_ahead"] is None:
        console.print("Commits: trunk not found", markup=False)
    else:
        console.print(
            f"Commits: {payload['commits_ahead']} ahead of {trunk or 'the trunk'}", markup=False,
        )
    mention = f"#{issue}" if issue and issue.isdigit() else issue
    hidden = 0
    for i, c in enumerate(payload["commits"]):
        unmarked = c["mentions_issue"] is False
        if i >= _SHOWN_COMMITS and not unmarked:
            hidden += 1
            continue
        mark = f"  ← doesn't mention {mention}" if unmarked else ""
        _outside(console, f"  {c['sha']} {c['subject']}{mark}")
    if hidden:
        # Every hidden commit mentions the issue when mentions were checked,
        # since an unmarked one always prints.
        checked = any(c["mentions_issue"] is not None for c in payload["commits"])
        tail = f", each mentions {mention}" if checked else ""
        _outside(console, f"  … {hidden} more{tail}")
    if payload["uncommitted"]:
        console.print("Uncommitted", markup=False)
        for line in payload["uncommitted"]:
            _outside(console, f"  {line}")
    else:
        console.print("Uncommitted: none", markup=False)

    console.print()
    if payload["handoff"] is None:
        console.print("Handoff: none on this branch", markup=False)
    else:
        console.print("Handoff (session-summary.md)", markup=False)
        handoff, dropped = _trim_handoff(payload["handoff"])
        _outside(console, handoff)
        if dropped:
            console.print(
                f"Left out: {', '.join(dropped)}, which the commits above show",
                markup=False,
            )
