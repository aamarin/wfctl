"""Tests for configurable issue-key resolution (key_pattern)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from wfctl._paths import DEFAULT_KEY_PATTERN, extract_issue_key, resolve_spec_dir
from wfctl._tracker import load_key_pattern


def _configure_key_pattern(repo_root: Path, pattern: str) -> None:
    tdir = repo_root / ".agents" / "trackers"
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / "custom.json").write_text(json.dumps({"key_pattern": pattern, "verbs": {}}))
    (repo_root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "custom"}))


# --- extract_issue_key: default \d+ -------------------------------------------

@pytest.mark.parametrize(
    "branch,expected",
    [
        ("342", "342"),                 # bare number, no slug
        ("342-state-workflow", "342"),  # hyphen slug
        ("342_state_workflow", "342"),  # underscore slug
        ("feature-123-x", "unknown"),   # no leading digit — not mis-read
        ("PROJ-123-x", "unknown"),      # letter-prefixed key needs config
        ("detached", "unknown"),
    ],
)
def test_extract_default(branch: str, expected: str) -> None:
    assert extract_issue_key(branch, DEFAULT_KEY_PATTERN) == expected


# --- extract_issue_key: custom Jira-style pattern -----------------------------

@pytest.mark.parametrize(
    "branch,expected",
    [
        ("PROJ-123-auth", "PROJ-123"),
        ("PROJ-123", "PROJ-123"),
        ("PROJ-123_auth", "PROJ-123"),
        ("feature-x", "unknown"),
    ],
)
def test_extract_custom(branch: str, expected: str) -> None:
    assert extract_issue_key(branch, r"[A-Z]+-\d+") == expected


def test_extract_bad_pattern_degrades() -> None:
    # An un-compilable pattern must not raise.
    assert extract_issue_key("342-x", r"[unterminated") == "unknown"


# --- load_key_pattern ---------------------------------------------------------

def test_load_default_when_no_tracker(tmp_path: Path) -> None:
    assert load_key_pattern(tmp_path) == DEFAULT_KEY_PATTERN


def test_load_configured(tmp_path: Path) -> None:
    _configure_key_pattern(tmp_path, r"[A-Z]+-\d+")
    assert load_key_pattern(tmp_path) == r"[A-Z]+-\d+"


def test_load_uncompilable_falls_back(tmp_path: Path) -> None:
    _configure_key_pattern(tmp_path, r"[unterminated")
    assert load_key_pattern(tmp_path) == DEFAULT_KEY_PATTERN


# --- resolve_spec_dir end-to-end ----------------------------------------------

def test_resolve_spec_dir_custom_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_key_pattern(tmp_path, r"[A-Z]+-\d+")
    specs = tmp_path / "specs"
    (specs / "PROJ-123-demo").mkdir(parents=True)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))

    assert resolve_spec_dir("PROJ-123-demo", tmp_path) == specs / "PROJ-123-demo"


def test_resolve_spec_dir_underscore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_key_pattern(tmp_path, r"[A-Z]+-\d+")
    specs = tmp_path / "specs"
    (specs / "PROJ-123_demo").mkdir(parents=True)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))

    # branch has no exact dir; falls back to key glob, which matches [-_].
    assert resolve_spec_dir("PROJ-123-other", tmp_path) == specs / "PROJ-123_demo"
