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
from pathlib import Path

from wfctl._io import append_event, write_atomic


# The one per-feature setting, and the only file in the state dir that holds a
# choice rather than a reading. `verify.json` is the shape it copies: named,
# JSON, one writer, one reader, and its name spelled in the module that means
# something by it rather than in `_io`.
MODE_NAME = "mode.json"


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


def grant_auto_approve(agent_dir: Path, granted: bool) -> None:
    """Record the mode, and record that it was granted.

    Two writes for two questions. The file answers "what mode is this feature in
    now", which is what every later report reads. The event answers "when was
    autonomy granted", which the file cannot: it holds one value and is
    overwritten, so a grant leaves no trace in it.

    That second question exists because the setter is not necessarily a person.
    `/start-session` runs `wfctl start` on every worktree spin-up and handoff and
    its allowlist admits any flag, so an agent can grant itself the mode. Nothing
    available here prevents that — the event is what makes it visible afterwards,
    beside the `start` and `resume` lines that say what the session did next.
    """
    write_atomic(agent_dir / MODE_NAME, json.dumps({"auto_approve": granted}, indent=2))
    append_event(agent_dir, "mode", auto_approve=granted)


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
