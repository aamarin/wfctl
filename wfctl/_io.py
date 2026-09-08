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

    One writer for both text and JSON. The two used to be separate functions
    with the same twenty-line body, and the duplication is what let them drift:
    only one of them grew the `newline` argument, so a JSON caller needing it
    would have had to copy the block a third time. JSON callers pass
    `json.dumps(data, indent=2)` — the serialisation is theirs, the atomicity is
    this function's, and neither has an opinion about the other.
    """
    if not path.parent.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
    fd, tmp = tempfile.mkstemp(suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", newline=newline) as f:
            f.write(content)
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
