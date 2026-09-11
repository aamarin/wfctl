"""Atomic file I/O and event logging for wfctl."""
from __future__ import annotations

import json
import os
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

    An existing file keeps its permissions. A file that does not exist yet has
    none to keep and is created `0600`, which is what every caller writing into
    the state dir gets today.
    """
    if not path.parent.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
    # `mkstemp` creates its file `0600` and `os.replace` installs that inode
    # whole, so without this a rewrite narrows whatever it replaced — a
    # committed `0644` record becomes owner-only, and an executable loses its
    # bit. Read before the temp file exists, so a stat failure orphans nothing.
    #
    # The guarantee lives here rather than at the call sites because all seven
    # want it, and `_write_settings_json` is what the other shape looks like:
    # the same stat-and-chmod written out by hand, correct, and load-bearing on
    # nobody remembering it for the eighth caller.
    mode = path.stat().st_mode & 0o777 if path.exists() else None
    fd, tmp = tempfile.mkstemp(suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", newline=newline) as f:
            f.write(content)
        # Before the replace, not after: a chmod on the far side leaves a window
        # where the file is readable at the wrong mode, which is the half of the
        # defect that a narrowing rewrite does not have but a widening one does.
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
