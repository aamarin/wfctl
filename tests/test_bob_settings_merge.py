"""Tests for `wfctl._bob_settings` — the entry-scoped merge into Bob Shell's
settings file. Same payoff as `test_settings_merge.py`: every case here is a
dict literal in and a dict literal out, exercised with no repo and no file on
disk.
"""
from __future__ import annotations

import pytest

from wfctl import _bob_settings

ENTRY = "execute_command(git)"


def test_merge_tool_allow_reports_whether_it_added_the_entry() -> None:
    """The return value is the receipt. After this call the file cannot answer
    whether wfctl added the entry, so this is the only moment it is
    observable."""
    fresh: dict = {}
    assert _bob_settings.merge_tool_allow(fresh, ENTRY) is True
    assert fresh == {"tools": {"allowed": [ENTRY]}}

    theirs = {"tools": {"allowed": [ENTRY]}}
    assert _bob_settings.merge_tool_allow(theirs, ENTRY) is False


def test_merge_tool_allow_keeps_every_entry_the_consumer_had() -> None:
    """`tools.allowed` is where a project puts the commands it trusts Bob Shell
    to run unattended. Losing one of those to an install is the failure this
    whole mode is built to avoid."""
    settings = {"tools": {"allowed": ["read_file"]}}
    assert _bob_settings.merge_tool_allow(settings, ENTRY) is True
    assert settings["tools"]["allowed"] == ["read_file", ENTRY]


def test_remove_tool_allow_prunes_the_keys_it_created() -> None:
    """Uninstall has to return a file that never had a `tools` key to a file
    with no `tools` key, not to one carrying an empty scaffold."""
    settings: dict = {}
    _bob_settings.merge_tool_allow(settings, ENTRY)
    assert _bob_settings.remove_tool_allow(settings, ENTRY) is True
    assert settings == {}


def test_remove_tool_allow_keeps_a_tools_map_still_in_use() -> None:
    """The prune stops at the first key that is not wfctl's doing."""
    settings = {"tools": {"allowed": ["read_file", ENTRY], "other": "kept"}}
    assert _bob_settings.remove_tool_allow(settings, ENTRY) is True
    assert settings == {"tools": {"allowed": ["read_file"], "other": "kept"}}


def test_remove_tool_allow_reports_no_change_when_the_entry_is_absent() -> None:
    """What tells uninstall the consumer edited the entry rather than kept it
    — the caller turns this False into a report rather than a silent skip."""
    settings = {"tools": {"allowed": ["read_file"]}}
    assert _bob_settings.remove_tool_allow(settings, ENTRY) is False
    assert settings == {"tools": {"allowed": ["read_file"]}}


def test_remove_tool_allow_drops_every_copy() -> None:
    """A duplicate can only come from a hand-edit. Leaving the second behind
    would have uninstall report the entry gone while Bob Shell still approves
    it."""
    settings = {"tools": {"allowed": [ENTRY, "read_file", ENTRY]}}
    assert _bob_settings.remove_tool_allow(settings, ENTRY) is True
    assert settings == {"tools": {"allowed": ["read_file"]}}


def test_tool_allow_helpers_ignore_a_shape_they_do_not_recognise() -> None:
    """The file is hand-editable, and a reader asking whether an entry is
    present gets a truthful no rather than a crash."""
    assert _bob_settings.tool_allow_present({"tools": "yes please"}, ENTRY) is False
    assert _bob_settings.tool_allow_present({"tools": {"allowed": "no"}}, ENTRY) is False


def test_merge_tool_allow_refuses_a_tools_key_that_is_not_an_object() -> None:
    """Refusing is the only safe move — overwriting would destroy whatever the
    consumer meant by it — and the caller reports the file as unmergeable."""
    with pytest.raises(ValueError):
        _bob_settings.merge_tool_allow({"tools": ["allowed"]}, ENTRY)
    with pytest.raises(ValueError):
        _bob_settings.merge_tool_allow({"tools": {"allowed": "git"}}, ENTRY)
