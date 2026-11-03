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
from dataclasses import dataclass
from pathlib import Path

from wfctl import _review

# With no trunk to measure from, the report can't tell which commits are the
# branch's, so it shows the most recent ones and marks none.
_FALLBACK_COMMITS = 20

# Separators git can't emit inside a subject or body, so one `git log` call can
# be split back into commits without guessing at line breaks.
_FIELD = "\x1f"
_RECORD = "\x1e"


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
    all count the same commits. The one case the report doesn't follow it is a
    repo with no `origin/HEAD`: there `review_trunk` falls back to the working
    tree's `trunk`, which the agent can edit, and the spec says that case reads
    trunk not found. Every error `review_trunk` raises reads the same way, since
    a session start shouldn't stop on a trunk problem.
    """
    try:
        head = _review.git(
            repo_root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD",
            timeout=15, answers=(0, 1),
        ).stdout.strip()
        if not head:
            return None
        return _review.review_trunk(repo_root, timeout=15).name
    except (_review.ReviewError, OSError, subprocess.SubprocessError):
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
    try:
        if trunk is None:
            out = _git(repo_root, "log", fmt, f"-{_FALLBACK_COMMITS}")
            base = None
        else:
            base = _git(repo_root, "merge-base", trunk, "HEAD").strip()
            out = _git(repo_root, "log", fmt, f"{base}..HEAD")
    except (_review.ReviewError, OSError, subprocess.SubprocessError):
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
    except (_review.ReviewError, OSError, subprocess.SubprocessError):
        return []
    return [line for line in out.splitlines() if line.strip()]
