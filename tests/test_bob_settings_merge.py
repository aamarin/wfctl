"""Tests for `wfctl._bob_settings`, the removal of tool-approval entries an
older wfctl merged into Bob Shell's settings file. Same payoff as
`test_settings_merge.py`: every case here is a dict literal in and a dict
literal out, exercised with no repo and no file on disk.
"""
from __future__ import annotations

from wfctl import _bob_settings

ENTRY = "execute_command(git)"


def test_remove_tool_allow_prunes_the_keys_it_created() -> None:
    """A file that never had a `tools` key has to come back with no `tools`
    key, not with an empty scaffold wfctl invented."""
    settings: dict = {"tools": {"allowed": [ENTRY]}}
    assert _bob_settings.remove_tool_allow(settings, ENTRY) is True
    assert settings == {}


def test_remove_tool_allow_keeps_a_tools_map_still_in_use() -> None:
    """The prune stops at the first key that is not wfctl's doing."""
    settings = {"tools": {"allowed": ["read_file", ENTRY], "other": "kept"}}
    assert _bob_settings.remove_tool_allow(settings, ENTRY) is True
    assert settings == {"tools": {"allowed": ["read_file"], "other": "kept"}}


def test_remove_tool_allow_reports_no_change_when_the_entry_is_absent() -> None:
    """The caller writes the file only on a change, so a False here is what
    keeps an untouched file byte-identical."""
    settings = {"tools": {"allowed": ["read_file"]}}
    assert _bob_settings.remove_tool_allow(settings, ENTRY) is False
    assert settings == {"tools": {"allowed": ["read_file"]}}


def test_remove_tool_allow_drops_every_copy() -> None:
    """A duplicate can only come from a hand-edit. Leaving the second behind
    would report the entry gone while Bob Shell still approves it."""
    settings = {"tools": {"allowed": [ENTRY, "read_file", ENTRY]}}
    assert _bob_settings.remove_tool_allow(settings, ENTRY) is True
    assert settings == {"tools": {"allowed": ["read_file"]}}


def test_remove_tool_allow_ignores_a_shape_it_does_not_recognise() -> None:
    """The file is hand-editable, and a shape wfctl never wrote cannot hold an
    entry wfctl added. A crash here would block the install that runs it."""
    odd_tools: dict = {"tools": "yes please"}
    odd_allowed: dict = {"tools": {"allowed": "no"}}
    assert _bob_settings.remove_tool_allow(odd_tools, ENTRY) is False
    assert _bob_settings.remove_tool_allow(odd_allowed, ENTRY) is False
    assert odd_tools == {"tools": "yes please"}
    assert odd_allowed == {"tools": {"allowed": "no"}}
