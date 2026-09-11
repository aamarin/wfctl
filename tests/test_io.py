"""Tests for wfctl._io — atomic writes and event log."""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from unittest.mock import patch

import pytest

from wfctl._io import append_event, write_atomic


def test_write_atomic_writes_valid_json(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    data = {"key": "value", "n": 42}
    write_atomic(target, json.dumps(data, indent=2))
    assert target.exists()
    assert json.loads(target.read_text()) == data
    assert list(tmp_path.glob("*.tmp")) == []


def test_write_atomic_no_parent_raises(tmp_path: Path) -> None:
    target = tmp_path / "nonexistent" / "data.json"
    with pytest.raises(FileNotFoundError):
        write_atomic(target, json.dumps({"x": 1}, indent=2))
    # No partial file left behind
    assert not target.exists()


def test_write_atomic_target_unchanged_on_failure(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    original = {"original": True}
    write_atomic(target, json.dumps(original, indent=2))

    # Simulate os.replace failing mid-write
    with patch("os.replace", side_effect=OSError("simulated failure")):
        with pytest.raises(OSError):
            write_atomic(target, json.dumps({"corrupted": True}, indent=2))

    assert json.loads(target.read_text()) == original
    assert list(tmp_path.glob("*.tmp")) == []


def test_write_atomic_writes_plain_text(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    write_atomic(target, "# Hello\n")
    assert target.read_text() == "# Hello\n"
    assert list(tmp_path.glob("*.tmp")) == []


def test_write_atomic_rewrite_keeps_the_existing_files_mode(tmp_path: Path) -> None:
    """#324: every rewrite narrowed its target to 0600.

    `mkstemp` creates its file owner-only and `os.replace` installs that inode
    whole, so `wfctl arch accept` turned a committed 0644 record into one only
    its author could read. This is the issue's reproduction, without the CLI.
    """
    target = tmp_path / "record.md"
    target.write_text("# before\n")
    target.chmod(0o644)

    write_atomic(target, "# after\n")

    assert stat.S_IMODE(target.stat().st_mode) == 0o644
    assert target.read_text() == "# after\n"


def test_write_atomic_rewrite_keeps_an_executable_bit(tmp_path: Path) -> None:
    """#324's second half: a rewritten script stopped being runnable.

    Narrowing to 0600 drops the x bit, which the mode-preserving fix has to
    carry rather than merely widening read access back to 0644.
    """
    target = tmp_path / "hook.sh"
    target.write_text("#!/bin/sh\ntrue\n")
    target.chmod(0o755)

    write_atomic(target, "#!/bin/sh\nfalse\n")

    assert stat.S_IMODE(target.stat().st_mode) == 0o755
    assert os.access(target, os.X_OK)


def test_write_atomic_creates_a_new_file_owner_only(tmp_path: Path) -> None:
    """The new-file case is deliberately left at mkstemp's 0600.

    A file that does not exist has no mode to preserve, and the callers that
    create one all write into the state dir — `session-summary.md` carries
    whatever the last session knew, and `_session.end` only ever creates it.
    A fix for #324 that widened this would publish a handoff to every local
    account, which is why it is pinned rather than left to follow the umask.
    """
    target = tmp_path / "session-summary.md"

    write_atomic(target, "# handoff\n")

    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_write_atomic_sets_the_mode_before_it_replaces(tmp_path: Path) -> None:
    """Ordering, not just the end state.

    A chmod after `os.replace` reaches the same mode and leaves a window where
    the file is live at the wrong one. That is harmless while the wrong mode is
    the narrow 0600, and is a disclosure the moment a 0600 target is rewritten
    — so the assertion is on what the mode already is when replace is called.
    """
    target = tmp_path / "record.md"
    target.write_text("# before\n")
    target.chmod(0o644)

    seen: list[int] = []
    real_replace = os.replace

    def recording_replace(src: str, dst: str) -> None:
        seen.append(stat.S_IMODE(os.stat(src).st_mode))
        real_replace(src, dst)

    with patch("os.replace", recording_replace):
        write_atomic(target, "# after\n")

    assert seen == [0o644]


def test_append_event_writes_jsonl(tmp_path: Path) -> None:
    append_event(tmp_path, "start", branch="422-test")
    lines = (tmp_path / "events.jsonl").read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["event"] == "start"
    assert record["branch"] == "422-test"
    assert "ts" in record


def test_append_event_appends_multiple_lines(tmp_path: Path) -> None:
    append_event(tmp_path, "start")
    append_event(tmp_path, "resume", n=1)
    append_event(tmp_path, "end")
    lines = (tmp_path / "events.jsonl").read_text().splitlines()
    assert len(lines) == 3
    events = [json.loads(line)["event"] for line in lines]
    assert events == ["start", "resume", "end"]
