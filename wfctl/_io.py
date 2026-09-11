"""Atomic file I/O and event logging for wfctl."""
from __future__ import annotations

import json
import os
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def write_atomic(path: Path, content: str, newline: str | None = None) -> None:
    """Write `content` atomically via tempfile + os.replace.

    `newline=""` writes the content's line endings through untranslated, for a
    caller rewriting a file it read verbatim. The default keeps the translating
    behaviour every existing caller was written against.

    One writer for both text and JSON, because atomicity has no opinion about
    what is being written. JSON callers pass `json.dumps(data, indent=2)`: the
    serialisation is theirs, and a writer that took `dict` could not also take
    `newline`, which `_arch` needs.

    An existing file keeps the mode it had, a deliberately widened one included
    — a rewrite no longer narrows that back. A file that does not exist has none
    to keep and is created `0600`. That floor is chosen for the callers writing
    into the state dir, where `session-summary.md` carries whatever the last
    session knew; the callers that create a file *inside* the repo — `arch
    declare`, and `_write_settings` on a first install — get it too, and landing
    `0600` beside committed neighbours at `0644` is its own complaint rather
    than this one's answer.

    A symlink is not followed. `os.replace` swaps the link itself for a regular
    file, carrying the mode read through it; resolve first where the link is
    what the consumer owns, as `cli._write_settings` does.
    """
    if not path.parent.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
    # `mkstemp` creates its file `0600` and `os.replace` installs that inode
    # whole, so without this a rewrite hands its target owner-only permissions
    # and drops an executable bit it had (#324).
    #
    # Set before the replace rather than after it. Not for the window's width —
    # `mkstemp`'s floor means a far-side window can only ever be *narrower* than
    # intended — but because a crash or a failing chmod inside it leaves the
    # file at `0600` permanently, which is this defect back and now intermittent.
    #
    # A guarantee of the function rather than a convention of its callers: they
    # all want it, and `cli._write_settings` is what the other shape looks like
    # — the same stat-and-chmod by hand, on the far side, correct, and
    # load-bearing on whoever adds the next caller remembering.
    try:
        mode: int | None = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        mode = None
    fd, tmp = tempfile.mkstemp(suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", newline=newline) as f:
            f.write(content)
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append_event(agent_dir: Path, event: str, **kwargs: object) -> None:
    """Append a JSONL event line to events.jsonl."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record = {"ts": ts, "event": event, **kwargs}
    with open(agent_dir / "events.jsonl", "a") as f:
        f.write(json.dumps(record) + "\n")
