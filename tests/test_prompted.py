"""The table of spellings the host asks for, and the host check.

The guard lets a person-only command through only when `prompted_match` finds
it, so a match the host's rule wouldn't make runs the command with no prompt.
"""
from __future__ import annotations

import pytest

from wfctl.evidence import PROMPTED, prompted_host, prompted_match


@pytest.mark.parametrize("entry", PROMPTED, ids=lambda e: e.text)
def test_each_entry_matches_its_plain_form_alone_and_with_arguments(entry) -> None:
    """Claude Code's `Bash(<words>:*)` rule matches both, so the guard has to."""
    assert prompted_match(entry.text) == entry
    assert prompted_match(entry.text + " some-slug --agreed x") == entry
    assert prompted_match(entry.text + "   \n") == entry


@pytest.mark.parametrize("text", [
    " wfctl arch accept s",
    'wfctl "arch" accept s',
    "wfctl ar\\ch accept s",
    "WFCTL arch accept s",
    "wfctl arch accepted s",
    "wfctl  arch accept s",
    "uv run wfctl arch approve-imports",
    "uv run wfctl arch accept s",
    "uv run wfctl review sign-off",
    "env wfctl review sign-off",
    "wfctl arch accept\ts",
])
def test_a_form_the_host_rule_wouldnt_match_matches_nothing(text: str) -> None:
    """Each of these runs the command in the shell, or nothing at all, but none
    starts with an entry's literal words and a space. Matching one would let
    it past the guard with no prompt."""
    assert prompted_match(text) is None


@pytest.mark.parametrize(("value", "expected"), [
    (None, False), ("", False), ("  ", False), ("1", True), ("yes", True),
])
def test_prompted_host_reads_a_non_blank_claudecode(
    monkeypatch: pytest.MonkeyPatch, value: str | None, expected: bool
) -> None:
    """A blank value set by hand is not Claude Code, and a value other than
    `1` still is, so the check survives Claude Code changing it."""
    if value is None:
        monkeypatch.delenv("CLAUDECODE", raising=False)
    else:
        monkeypatch.setenv("CLAUDECODE", value)
    assert prompted_host() is expected


@pytest.mark.parametrize("marker", ["CODEX_THREAD_ID", "CODEX_SANDBOX"])
def test_a_codex_agent_started_from_claude_code_is_not_a_prompted_host(
    monkeypatch: pytest.MonkeyPatch, marker: str,
) -> None:
    """The review panel runs Codex reviewers from Claude Code's shell, and
    each one inherits `CLAUDECODE=1`. Codex shows no prompt and runs no guard,
    so a reviewer that copied a sign-off from a skill would write a CI-trusted
    note nobody approved (security panel s2, #833)."""
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv(marker, "x")
    assert prompted_host() is False


def test_no_person_only_command_has_a_uv_run_spelling() -> None:
    """The user approves a command by its text, and `uv run wfctl` runs the
    branch's own copy, which the agent may have edited. A `uv run` entry
    would have the user approve code that no longer does what the command
    says, so every entry runs the installed wfctl."""
    assert [e.text for e in PROMPTED if e.words[0] != "wfctl"] == []
