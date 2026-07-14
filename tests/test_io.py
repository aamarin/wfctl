"""Tests for wfctl._io — atomic writes and event log."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from wfctl._io import append_event, write_json_atomic, write_md_atomic


def test_write_json_atomic_writes_valid_json(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    data = {"key": "value", "n": 42}
    write_json_atomic(target, data)
    assert target.exists()
    assert json.loads(target.read_text()) == data
    assert list(tmp_path.glob("*.tmp")) == []


def test_write_json_atomic_no_parent_raises(tmp_path: Path) -> None:
    target = tmp_path / "nonexistent" / "data.json"
    with pytest.raises(FileNotFoundError):
        write_json_atomic(target, {"x": 1})
    # No partial file left behind
    assert not target.exists()


def test_write_json_atomic_target_unchanged_on_failure(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    original = {"original": True}
    write_json_atomic(target, original)

    # Simulate os.replace failing mid-write
    with patch("os.replace", side_effect=OSError("simulated failure")):
        with pytest.raises(OSError):
            write_json_atomic(target, {"corrupted": True})

    assert json.loads(target.read_text()) == original
    assert list(tmp_path.glob("*.tmp")) == []


def test_write_md_atomic_writes_content(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    write_md_atomic(target, "# Hello\n")
    assert target.read_text() == "# Hello\n"
    assert list(tmp_path.glob("*.tmp")) == []


def test_write_md_atomic_no_parent_raises(tmp_path: Path) -> None:
    target = tmp_path / "missing" / "doc.md"
    with pytest.raises(FileNotFoundError):
        write_md_atomic(target, "content")


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
    append_event(tmp_path, "checkpoint", n=1)
    append_event(tmp_path, "end")
    lines = (tmp_path / "events.jsonl").read_text().splitlines()
    assert len(lines) == 3
    events = [json.loads(l)["event"] for l in lines]
    assert events == ["start", "checkpoint", "end"]
