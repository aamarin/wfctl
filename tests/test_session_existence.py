"""Whether a session was started, answered from the event log.

`resume` and `end` used to refuse on "`current.json` is missing" — a file whose
other seven fields were all derivable, kept alive for this one boolean. The
`start` event says the same thing and is written as it happens.
"""
from __future__ import annotations

import json
from pathlib import Path

from wfctl._io import append_event
from wfctl._session import session_started


def test_a_branch_with_no_state_dir_has_no_session(tmp_path: Path) -> None:
    """The first read on a fresh worktree, before anything has written anything."""
    assert session_started(tmp_path) is False


def test_a_log_with_events_but_no_start_has_no_session(tmp_path: Path) -> None:
    """`status` and `next` append events without opening a session.

    So the log existing is not the answer — the `start` event in it is. Reading
    the file's presence instead would report every browsed worktree as started.
    """
    append_event(tmp_path, "next", command="/speckit.specify")
    assert session_started(tmp_path) is False


def test_a_start_event_is_the_session(tmp_path: Path) -> None:
    append_event(tmp_path, "start", branch="74-x", step="plan")
    assert session_started(tmp_path) is True


def test_a_truncated_line_does_not_hide_a_started_session(tmp_path: Path) -> None:
    """A half-written final line is a crash, not a closed session.

    Raising here, or returning False, would send a running session back to
    `wfctl start` — which is the failure the whole feature is about.
    """
    append_event(tmp_path, "start", branch="74-x", step="plan")
    with open(tmp_path / "events.jsonl", "a") as f:
        f.write('{"ts": "2026-08-31T00:00:00Z", "eve')
    assert session_started(tmp_path) is True


def test_the_start_event_is_found_wherever_it_sits(tmp_path: Path) -> None:
    """Not just the first line: `end` then `start` again is a reopened session."""
    append_event(tmp_path, "next", command="/speckit.specify")
    append_event(tmp_path, "start", branch="74-x", step="plan")
    lines = (tmp_path / "events.jsonl").read_text().splitlines()
    assert json.loads(lines[0])["event"] == "next"
    assert session_started(tmp_path) is True
