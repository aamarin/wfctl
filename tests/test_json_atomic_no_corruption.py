"""Tests for write_json_atomic atomicity under failure."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from wfctl._io import write_json_atomic


def test_atomic_write_no_corruption_on_replace_failure(tmp_path: Path) -> None:
    """Target file unchanged when os.replace raises mid-write."""
    target = tmp_path / "data.json"
    original = {"safe": True}
    write_json_atomic(target, original)

    with patch("os.replace", side_effect=OSError("disk full")):
        with pytest.raises(OSError):
            write_json_atomic(target, {"corrupted": True})

    assert json.loads(target.read_text()) == original


def test_atomic_write_no_leftover_tmp_on_failure(tmp_path: Path) -> None:
    """No .tmp orphan left when write_json_atomic fails."""
    target = tmp_path / "data.json"
    write_json_atomic(target, {})  # create target first

    with patch("os.replace", side_effect=OSError("simulated")):
        with pytest.raises(OSError):
            write_json_atomic(target, {"new": 1})

    assert list(tmp_path.glob("*.tmp")) == []


def test_atomic_write_creates_valid_json(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    write_json_atomic(target, {"a": 1, "b": [1, 2, 3]})
    parsed = json.loads(target.read_text())
    assert parsed == {"a": 1, "b": [1, 2, 3]}
