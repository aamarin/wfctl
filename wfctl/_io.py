"""Atomic file I/O and event logging for wfctl."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def write_json_atomic(path: Path, data: dict) -> None:
    """Write JSON atomically via tempfile + os.replace."""
    if not path.parent.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
    fd, tmp = tempfile.mkstemp(suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_md_atomic(path: Path, content: str, newline: str | None = None) -> None:
    """Write markdown atomically via tempfile + os.replace.

    `newline=""` writes the content's line endings through untranslated, for a
    caller rewriting a file it read verbatim. The default keeps the translating
    behaviour every existing caller was written against.
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


def load_agentconfig(agent_dir: Path) -> dict:
    """Read current.json as config dict; returns {} if absent or malformed."""
    path = agent_dir / "current.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
