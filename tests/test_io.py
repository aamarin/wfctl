"""Tests for wfctl._io — atomic writes and event log."""
from __future__ import annotations

import json
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


def test_write_atomic_no_parent_raises_for_text_too(tmp_path: Path) -> None:
    target = tmp_path / "missing" / "doc.md"
    with pytest.raises(FileNotFoundError):
        write_atomic(target, "content")


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
