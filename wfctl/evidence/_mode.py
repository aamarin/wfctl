"""The approval mode: whether a feature's design gates and review stops may be
answered without a human.

Session state is otherwise re-derived on every read, and nothing caches a
conclusion about it (`session-state-is-re-derived`). The mode is the one
carve-out, because no artifact implies it. It is a person's choice, stored in
`mode.json`, and every grant and revocation is also appended to the event log.

It lives in evidence because the pipeline reads it to decide whether a gate
needs a person, and evidence may not import session continuity.
"""
from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from wfctl._io import append_event, write_atomic

from ._events import read_events


# The one per-feature setting, and the only file in the state dir that holds a
# choice rather than a reading. `verify.json` is the shape it copies: named,
# JSON, one writer, one reader, and its name spelled in the module that means
# something by it rather than in `_io`.
MODE_NAME = "mode.json"


@contextmanager
def _mode_lock(agent_dir: Path) -> Iterator[None]:
    """Hold `mode.lock` while one mode change writes the file and the event.

    Each change is two writes, and a grant puts the event first while turning
    the mode off puts the file first. Without the lock, an `on` paused between
    its two writes lets an `off` finish in between, and the `on` then leaves
    the file on while the newest event says off.

    `fcntl.flock` for the reason `_spec_store._lock` gives: the OS drops the
    lock when the process exits, so a killed command leaves nothing to delete.
    """
    # Imported here because `fcntl` is POSIX only.
    import fcntl

    agent_dir.mkdir(parents=True, exist_ok=True)
    fd = os.open(agent_dir / "mode.lock", os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        # Closing the descriptor is what releases the lock.
        os.close(fd)


def auto_approve(agent_dir: Path) -> bool:
    """Whether this feature's design gates and review stops may be answered
    without a human. A review stop is a `review_required` pass or step, which
    since #501 includes the plan review and the stop before `tasks`.

    The one value here that is not re-derived, and the module docstring's
    carve-out is why: no artifact implies it, so there is nothing to recompute it
    from and nothing for it to go stale against. `current.json` rotted because
    every field on it had a live answer elsewhere; this has none.

    Absent, malformed or unreadable reads as `False`, never as granted. The
    conservative direction is the whole point — a state dir that lost this file
    must fall back to stopping for a human, not to running without one.

    Three ways to be unreadable, and the shape is the one that bites. `ValueError`
    rather than `JSONDecodeError` because an invalid UTF-8 byte raises
    `UnicodeDecodeError`, which is a `ValueError` and not an `OSError`; and
    `isinstance` because `null`, `3` and `[]` all parse successfully and have no
    `.get`. Every caller reaches this through `build_report`, so an uncaught
    raise here is not a bad read of one field — it is `status`, `start`, `resume`
    and `end` all failing for that branch until someone deletes the file by hand.
    `_verify.load_record` guards the same way for the same reason.
    """
    path = agent_dir / MODE_NAME
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and data.get("auto_approve") is True


def grant_auto_approve(agent_dir: Path, granted: bool, session: str | None = None) -> None:
    """Record the mode a person chose, and record that they chose it.

    Two writes for two questions. The file answers "what mode is this feature in
    now", which is what every later report reads. The event answers "when was
    the mode changed, and by which session", which the file can't: it holds one
    value and is overwritten, so a grant leaves no trace in it.

    That second question exists because the setter isn't necessarily a person.
    An agent can run `wfctl auto-approve on` as easily as a person can type it,
    and nothing here can tell the two apart. `session` is the caller's identity,
    passed in because evidence can't import session continuity, and it's what
    lets a reviewer check afterwards which session made the grant. A caller with
    no identity writes no `session` key, the same shape events written before
    #407 have.

    For a grant, the event goes first. A failed append then changes nothing,
    where the other order would leave the mode on with no grant for the review
    cap to count from. A failed file write after the append leaves the old mode
    in place, which after `on` is off, and the bare `wfctl auto-approve` reports
    the mismatch until the next change repairs it.

    Turning the mode off goes the other way, file first. With the event first,
    an unwritable event log would keep the mode on after `off`, and lowering
    autonomy should never depend on the log. A failed append after the write
    still raises, so the caller says the change wasn't recorded.

    `on` writes nothing when the mode is already on and the newest `mode` event
    is a grant. Every grant restarts `review_count`, so an `on` that appended
    each time would let an agent reset the review cap by asking again. The
    check reads the newest event, revocation included, rather than any grant:
    after a hand edit, with or without an earlier revocation, no grant stands
    behind the mode, and this `on` is the one that gives the cap its start.
    """
    with _mode_lock(agent_dir):
        if granted and auto_approve(agent_dir) and newest_is_grant(agent_dir):
            return
        fields: dict[str, object] = {"auto_approve": granted}
        if session is not None:
            fields["session"] = session
        mode = json.dumps({"auto_approve": granted}, indent=2)
        if not granted:
            write_atomic(agent_dir / MODE_NAME, mode)
        append_event(agent_dir, "mode", **fields)
        if granted:
            write_atomic(agent_dir / MODE_NAME, mode)


def revoke_auto_approve(agent_dir: Path, reason: str) -> None:
    """Turn auto-approve off because the review cap fired, and say why.

    wfctl is the mode's second writer, and it only ever writes `false`
    (`approval-mode-is-stored-intent`). Raising the bar needs no person;
    lowering it does, so a grant stays `grant_auto_approve`'s alone.

    The file gains `revoked`, which `grant_auto_approve` never writes, so a new
    grant clears it and a person's `--no-auto-approve` never carries it.
    `status` and `resume` print the reason while it stands. The event carries
    `by` and the reason because the log is the only record of who turned the
    mode off once the file is overwritten again.
    """
    with _mode_lock(agent_dir):
        write_atomic(
            agent_dir / MODE_NAME,
            json.dumps({"auto_approve": False, "revoked": reason}, indent=2),
        )
        append_event(agent_dir, "mode", auto_approve=False, by="wfctl", reason=reason)


def revoked(agent_dir: Path) -> str | None:
    """Why wfctl turned auto-approve off, or None when it did not.

    Read with `auto_approve`'s guards, since both read one file and a damaged
    file must not raise here either. A `revoked` value that is not a string
    reads as none, so the line printed from it is always a sentence.
    """
    try:
        data = json.loads((agent_dir / MODE_NAME).read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("auto_approve") is True:
        return None
    reason = data.get("revoked")
    return reason if isinstance(reason, str) and reason.strip() else None


@dataclass(frozen=True)
class ModeChange:
    """The last change a person made to the mode, read from the event log.

    Never stored. The relation a reader sees ("this session", "another
    session") comes from comparing `session` with the caller's identity at read
    time, per `session-state-is-re-derived`.
    """

    on: bool
    ts: str
    session: str | None


def _mode_events(agent_dir: Path) -> list[dict]:
    """Every `mode` event in the log, oldest first, with malformed lines skipped."""
    return [e for e in read_events(agent_dir) if e.get("event") == "mode"]


def last_change(agent_dir: Path) -> ModeChange | None:
    """The newest `mode` event a person made, or None when there is none.

    A person's change is any `mode` event with no `by` field, so the review
    cap's revocation is skipped. After the cap fires, the reader wants the grant
    it ended, which names the session that turned the mode on.
    """
    for event in reversed(_mode_events(agent_dir)):
        if "by" in event:
            continue
        session = event.get("session")
        ts = event.get("ts")
        return ModeChange(
            on=event.get("auto_approve") is True,
            ts=ts if isinstance(ts, str) else "",
            session=session if isinstance(session, str) and session else None,
        )
    return None


def newest_is_grant(agent_dir: Path) -> bool:
    """Whether the newest `mode` event of any kind is a grant.

    A grant is a `mode` event turning the mode on with no `by` field. The
    revocation counts as newest, which keeps a hand edit after the cap fired
    from reading as a mode with a grant behind it. The repeat-`on` skip and the
    bare command's second line both read this, so they agree.
    """
    events = _mode_events(agent_dir)
    if not events:
        return False
    newest = events[-1]
    return newest.get("auto_approve") is True and "by" not in newest
