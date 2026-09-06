"""Session lifecycle operations — start, end, resume.

What a session file holds is what re-derivation cannot reach. Everything else —
the issue, the branch, the pipeline step, the next command, when it last moved —
is computed from artifacts on every read, so nothing here caches a conclusion
about it (`session-state-is-re-derived`).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from wfctl._io import append_event, write_md_atomic


class Observations(NamedTuple):
    """What `end` could see at the moment it ran. No conclusion among them.

    Each field is a reading, not a verdict: where the pipeline stands, whether
    the boundary question was answered, whether the tree has uncommitted work.
    "Complete" is not here because it is not observable — that is #70.
    """

    step: str
    boundary: str
    tree: str


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def session_started(agent_dir: Path) -> bool:
    """Whether `wfctl start` has run for this branch.

    Read from the event log rather than from a file's existence. `current.json`
    used to answer this by being there, which made one fact the reason a whole
    cache of derivable fields had to be kept alive. The `start` event records the
    same thing as it happens, and is append-only, so nothing has to be rewritten
    to keep it true.

    A malformed line is skipped rather than raising: the log is appended to by
    every command, and a truncated final write must not make the session look
    unstarted — that would send the reader to `wfctl start` on a session that is
    running.
    """
    events = agent_dir / "events.jsonl"
    if not events.exists():
        return False
    for line in events.read_text().splitlines():
        try:
            if json.loads(line).get("event") == "start":
                return True
        except json.JSONDecodeError:
            continue
    return False


def _render_session_summary(branch: str, observed: Observations) -> str:
    """The handoff, headed by what `end` could see rather than what it hoped.

    `**Status**: complete` used to sit here. Nothing observed it — `end` wrote
    the word on every run, including one that closed a session with half the
    tasks open and a dirty tree (#70). What replaces it is three facts and no
    conclusion drawn from them; the reader draws their own, which is the whole
    difference.

    Prose below stays as it is. A handoff whose sections were never filled in
    must read as unfilled, and nothing above them may claim otherwise.
    """
    now = _now_utc()
    return (
        f"# Session Summary: {now[:10]} — {branch}\n\n"
        f"**End**: {now}\n"
        f"**Step**: {observed.step}\n"
        f"**Boundary**: {observed.boundary}\n"
        f"**Tree**: {observed.tree}\n\n"
        f"## What We Accomplished\n\n"
        f"- (fill in)\n\n"
        f"## Next Session TODO\n\n"
        f"- [ ] (fill in)\n"
    )


def end(agent_dir: Path, branch: str, observed: Observations) -> tuple[Path, bool]:
    """Write session-summary.md if absent; return its path and whether it wrote.

    The observations are passed in rather than taken here: the caller has
    already built the report, and a second inference is a second chance to
    disagree with the line it is about to print.

    Written once. A second `end` must not overwrite prose a human or agent
    filled in between the two.

    The flag is returned because only this function knows which of the two
    happened, and the caller reports it. Whether the file was written is not
    re-derivable afterwards: the kept file and a freshly written one are both
    just a `session-summary.md` sitting there, and the mtime cannot separate
    them either — `worktree-handoff` copies a handoff in after the branch's
    first `start` event, so "older than the session" classifies a handoff as
    stale (#239).
    """
    summary_file = agent_dir / "session-summary.md"
    written = not summary_file.exists()
    if written:
        write_md_atomic(summary_file, _render_session_summary(branch, observed))

    append_event(agent_dir, "end", step=observed.step)
    return summary_file, written
