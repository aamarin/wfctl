"""Tests for `wfctl._settings` — the entry-scoped merge into a consumer's file.

No fixtures, no repo, no settings file on disk. Same payoff `test_workmux`
documents: every case here is a dict literal in and a dict literal out, so
"uninstall restores the consumer's file exactly" is an `==` between two objects
rather than a git repo, an install, and a byte comparison.

The file under test never learns it is JSON. That is deliberate — parsing,
writing and the decision not to write live in `cli`, so the ownership rules can
be exercised without any of it.
"""
from __future__ import annotations

import copy

import pytest

from wfctl import _settings

COMMAND = "wfctl hook user-prompt"
EVENT = "UserPromptSubmit"

# A consumer who already uses hooks, in the shape their own file takes: a hook on
# the event wfctl wants, and one on an event it never touches. Both must survive
# every operation below.
CONSUMER = {
    "permissions": {"allow": ["Bash(git status:*)"]},
    "hooks": {
        EVENT: [{"hooks": [{"type": "command", "command": "./scripts/mine.sh"}]}],
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": "./guard.sh"}]}
        ],
    },
}


def _managed(settings: dict) -> list[dict]:
    return [
        h
        for g in settings["hooks"][EVENT]
        for h in g["hooks"]
        if h["command"].startswith(_settings.MANAGED_PREFIX)
    ]


# --- merge_hook ------------------------------------------------------------

def test_merge_creates_the_hooks_scaffold_in_an_empty_settings_file() -> None:
    """The acceptance criterion for a consumer who has never written a settings
    file: they get a valid one, not a fragment the harness rejects."""
    settings: dict = {}
    assert _settings.merge_hook(settings, EVENT, COMMAND) is True
    assert settings == {
        "hooks": {EVENT: [{"hooks": [{"type": "command", "command": COMMAND}]}]}
    }


def test_merge_leaves_every_entry_the_consumer_already_had() -> None:
    """The whole reason this mode exists. A managed mirror would have replaced
    the file; this may only add a row."""
    settings = copy.deepcopy(CONSUMER)
    assert _settings.merge_hook(settings, EVENT, COMMAND) is True

    assert settings["permissions"] == CONSUMER["permissions"]
    assert settings["hooks"]["PreToolUse"] == CONSUMER["hooks"]["PreToolUse"]
    assert settings["hooks"][EVENT][0] == CONSUMER["hooks"][EVENT][0]
    assert len(settings["hooks"][EVENT]) == 2


def test_merge_is_idempotent_and_reports_no_change() -> None:
    """Re-running the install must replace, never duplicate — and must report
    that nothing moved, because the caller skips the write on False and that is
    what keeps a consumer's indentation and key order intact across upgrades."""
    settings = copy.deepcopy(CONSUMER)
    _settings.merge_hook(settings, EVENT, COMMAND)
    after_first = copy.deepcopy(settings)

    assert _settings.merge_hook(settings, EVENT, COMMAND) is False
    assert settings == after_first
    assert len(_managed(settings)) == 1


def test_merge_replaces_a_stale_command_in_place() -> None:
    """An upgrade that re-anchors a different set of skills changes the command.
    The entry keeps its position: a consumer who ordered their hooks around it
    would otherwise find it moved to the end by an unrelated wfctl upgrade."""
    settings = copy.deepcopy(CONSUMER)
    _settings.merge_hook(settings, EVENT, "wfctl hook old-name")
    settings["hooks"][EVENT].append(
        {"hooks": [{"type": "command", "command": "./after.sh"}]}
    )

    assert _settings.merge_hook(settings, EVENT, COMMAND) is True
    assert [g["hooks"][0]["command"] for g in settings["hooks"][EVENT]] == [
        "./scripts/mine.sh",
        COMMAND,
        "./after.sh",
    ]


def test_merge_collapses_duplicate_managed_entries() -> None:
    """A hand-edited file can hold two. Left alone they inject the same text
    twice on every turn, and the next install would have two rows to reconcile."""
    settings = {
        "hooks": {
            EVENT: [
                {"hooks": [{"type": "command", "command": "wfctl hook one"}]},
                {"hooks": [{"type": "command", "command": "wfctl hook two"}]},
            ]
        }
    }
    assert _settings.merge_hook(settings, EVENT, COMMAND) is True
    assert _managed(settings) == [{"type": "command", "command": COMMAND}]


def test_merge_refuses_a_hooks_key_that_is_not_an_object() -> None:
    """Refusing beats guessing: whatever the consumer meant by it, overwriting
    is the one outcome that loses it. The caller turns this into a warning and
    leaves the file closed."""
    settings = {"hooks": "see ./hooks.json"}
    with pytest.raises(ValueError):
        _settings.merge_hook(settings, EVENT, COMMAND)
    assert settings == {"hooks": "see ./hooks.json"}


def test_merge_ignores_entries_it_cannot_recognise() -> None:
    """The file is hand-editable, so an array can hold a bare string or a typo'd
    key. Raising on the way past would leave a consumer unable to install at all
    until they fixed a line wfctl has no business reading."""
    settings = {"hooks": {EVENT: ["not-a-group", {"hooks": ["not-a-hook"]}]}}
    assert _settings.merge_hook(settings, EVENT, COMMAND) is True
    assert settings["hooks"][EVENT][:2] == ["not-a-group", {"hooks": ["not-a-hook"]}]


def test_a_command_merely_starting_with_wfctl_hook_is_not_managed() -> None:
    """The trailing space in the prefix. Without it a consumer's own
    `wfctl hooks-report` is claimed by wfctl and deleted on uninstall."""
    settings = {
        "hooks": {EVENT: [{"hooks": [{"type": "command", "command": "wfctl hooks-report"}]}]}
    }
    assert _settings.managed_command(settings, EVENT) is None
    _settings.merge_hook(settings, EVENT, COMMAND)
    assert len(settings["hooks"][EVENT]) == 2


# --- remove_hooks ----------------------------------------------------------

def test_remove_restores_the_consumers_file_exactly() -> None:
    """The round trip. Install then uninstall must leave the object the consumer
    started with — not one carrying an empty `UserPromptSubmit` array wfctl
    invented, which is what a prune that stopped at the group level would give."""
    settings = copy.deepcopy(CONSUMER)
    _settings.merge_hook(settings, EVENT, COMMAND)
    assert _settings.remove_hooks(settings, EVENT) is True
    assert settings == CONSUMER


def test_remove_drops_the_hooks_key_it_created() -> None:
    """A file that had no `hooks` at all gets back to no `hooks` at all, so the
    caller can tell an emptied file from one still holding the consumer's
    settings — which is how it decides whether to delete the file."""
    settings: dict = {}
    _settings.merge_hook(settings, EVENT, COMMAND)
    assert _settings.remove_hooks(settings, EVENT) is True
    assert settings == {}


def test_remove_keeps_a_hand_written_hook_in_the_same_array() -> None:
    """Named in the acceptance criteria, and the failure mode with the worst
    blast radius: deleting the array is one line shorter than filtering it."""
    settings = copy.deepcopy(CONSUMER)
    _settings.merge_hook(settings, EVENT, COMMAND)
    _settings.remove_hooks(settings, EVENT)
    assert settings["hooks"][EVENT] == CONSUMER["hooks"][EVENT]
    assert settings["hooks"]["PreToolUse"] == CONSUMER["hooks"]["PreToolUse"]


def test_remove_reports_no_change_when_nothing_is_ours() -> None:
    """The caller writes only on True, so a False here is what keeps uninstall
    from reflowing a settings file it had nothing to remove from."""
    settings = copy.deepcopy(CONSUMER)
    assert _settings.remove_hooks(settings, EVENT) is False
    assert settings == CONSUMER


# --- managed_command -------------------------------------------------------

def test_managed_command_reads_back_what_was_installed() -> None:
    """What `doctor` compares against the command this wfctl would install."""
    settings = copy.deepcopy(CONSUMER)
    _settings.merge_hook(settings, EVENT, COMMAND)
    assert _settings.managed_command(settings, EVENT) == COMMAND


def test_managed_command_is_none_when_the_consumer_deleted_the_entry() -> None:
    """The state the manifest cannot see. Nothing else in `doctor` looks at this
    file, so without this the install reports current while the hook is gone."""
    settings = copy.deepcopy(CONSUMER)
    _settings.merge_hook(settings, EVENT, COMMAND)
    _settings.remove_hooks(settings, EVENT)
    assert _settings.managed_command(settings, EVENT) is None


def test_remove_leaves_a_group_that_arrived_empty_or_unrecognised() -> None:
    """The prune drops a group *it* emptied. A group the consumer wrote empty,
    and one whose shape wfctl does not recognise, are theirs and must survive —
    FR-006.

    Written because `if kept or not hooks` reduces to `if kept:` with the whole
    suite still green: nothing else distinguishes "emptied by us" from "arrived
    empty", so the mutation silently deletes rows out of a consumer's file.
    """
    settings = {
        "hooks": {
            EVENT: [
                {"hooks": []},
                "not-a-group",
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "mine"}]},
                {"hooks": [{"type": "command", "command": COMMAND}]},
            ]
        }
    }

    assert _settings.remove_hooks(settings, EVENT) is True
    assert settings["hooks"][EVENT] == [
        {"hooks": []},
        "not-a-group",
        {"matcher": "Bash", "hooks": [{"type": "command", "command": "mine"}]},
    ]
