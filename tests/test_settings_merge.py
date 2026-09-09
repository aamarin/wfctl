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


# --- merge_hook, matcher ---------------------------------------------------

PRETOOL = "PreToolUse"
GUARD = "wfctl hook worktree-guard"


def test_a_matcherless_event_leaves_every_group_matcher_alone() -> None:
    """The regression the matcher parameter could most easily cause. Two of the
    three managed events have nothing to match on, and passing None must leave
    them behaving exactly as they did before the parameter existed."""
    settings = copy.deepcopy(CONSUMER)
    assert _settings.merge_hook(settings, EVENT, COMMAND) is True
    assert all("matcher" not in g for g in settings["hooks"][EVENT])
    # The consumer's own PreToolUse group, on an event this call never named.
    assert settings["hooks"][PRETOOL][0]["matcher"] == "Bash"


def test_a_fresh_group_carries_the_matcher_it_was_given() -> None:
    """A tool event's hook is inert without a matcher — it either never fires or
    fires on everything, depending on the harness."""
    settings: dict = {}
    assert _settings.merge_hook(settings, PRETOOL, GUARD, "Bash") is True
    assert settings["hooks"][PRETOOL] == [
        {"matcher": "Bash", "hooks": [{"type": "command", "command": GUARD}]}
    ]


def test_adopting_a_hand_wired_entry_corrects_its_matcher_in_place() -> None:
    """Someone who followed the README but scoped it to every tool. The command
    is one wfctl recognises, so the install adopts the entry — and before this,
    adopted it without looking at the matcher, printing a ✓ over a hook that
    still fired on every tool call."""
    settings = {
        "hooks": {
            PRETOOL: [
                {"matcher": "*", "hooks": [{"type": "command", "command": GUARD}]},
                {"matcher": "Edit", "hooks": [{"type": "command", "command": "./mine.sh"}]},
            ]
        }
    }
    assert _settings.merge_hook(settings, PRETOOL, GUARD, "Bash") is True
    assert settings["hooks"][PRETOOL][0]["matcher"] == "Bash"
    # Position kept: a consumer who ordered their hooks deliberately does not
    # find wfctl's moved to the end, and theirs is untouched either way.
    assert settings["hooks"][PRETOOL][1]["matcher"] == "Edit"


def test_a_correct_entry_with_a_correct_matcher_reports_no_change() -> None:
    """What keeps a re-install from reflowing the file. The matcher comparison
    had to join the command comparison rather than replace it."""
    settings = {
        "hooks": {
            PRETOOL: [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": GUARD}]}
            ]
        }
    }
    assert _settings.merge_hook(settings, PRETOOL, GUARD, "Bash") is False


# --- permissions -----------------------------------------------------------

RULE = "Bash(cd:*)"


def test_merge_permission_reports_whether_it_added_the_rule() -> None:
    """The return value is the receipt. After this call the file cannot answer
    whether wfctl added the rule, so this is the only moment it is observable."""
    fresh: dict = {}
    assert _settings.merge_permission(fresh, RULE) is True
    assert fresh == {"permissions": {"deny": [RULE]}}

    theirs = {"permissions": {"deny": [RULE]}}
    assert _settings.merge_permission(theirs, RULE) is False


def test_merge_permission_keeps_every_rule_the_consumer_had() -> None:
    """A deny list is where a project puts the commands it has decided are
    dangerous. Losing one of those to an install is the failure this whole mode
    is built to avoid."""
    settings = {"permissions": {"allow": ["Bash(npm test)"], "deny": ["Bash(rm:*)"]}}
    assert _settings.merge_permission(settings, RULE) is True
    assert settings["permissions"]["deny"] == ["Bash(rm:*)", RULE]
    assert settings["permissions"]["allow"] == ["Bash(npm test)"]


def test_remove_permission_prunes_the_keys_it_created() -> None:
    """Uninstall has to return a file that never had a `permissions` key to a
    file with no `permissions` key, not to one carrying an empty scaffold."""
    settings: dict = {}
    _settings.merge_permission(settings, RULE)
    assert _settings.remove_permission(settings, RULE) is True
    assert settings == {}


def test_remove_permission_keeps_a_permissions_map_still_in_use() -> None:
    """The prune stops at the first key that is not wfctl's doing."""
    settings = {"permissions": {"allow": ["Bash(npm test)"], "deny": [RULE]}}
    assert _settings.remove_permission(settings, RULE) is True
    assert settings == {"permissions": {"allow": ["Bash(npm test)"]}}


def test_remove_permission_reports_no_change_when_the_rule_is_absent() -> None:
    """What tells uninstall the consumer edited the rule rather than kept it —
    the caller turns this False into a report rather than a silent skip."""
    settings = {"permissions": {"deny": ["Bash(cd:/tmp/*)"]}}
    assert _settings.remove_permission(settings, RULE) is False
    assert settings == {"permissions": {"deny": ["Bash(cd:/tmp/*)"]}}


def test_remove_permission_drops_every_copy() -> None:
    """A duplicate can only come from a hand-edit. Leaving the second behind
    would have uninstall report the rule gone while the agent still denies it."""
    settings = {"permissions": {"deny": [RULE, "Bash(rm:*)", RULE]}}
    assert _settings.remove_permission(settings, RULE) is True
    assert settings == {"permissions": {"deny": ["Bash(rm:*)"]}}


def test_permission_helpers_ignore_a_shape_they_do_not_recognise() -> None:
    """Same posture as `_groups`: the file is hand-editable, and a reader asking
    whether a rule is present gets a truthful no rather than a crash."""
    assert _settings.permission_present({"permissions": "yes please"}, RULE) is False
    assert _settings.permission_present({"permissions": {"deny": "no"}}, RULE) is False
    assert _settings.related_rules({"permissions": None}, RULE) == []


def test_merge_permission_refuses_a_permissions_key_that_is_not_an_object() -> None:
    """Refusing is the only safe move — overwriting would destroy whatever the
    consumer meant by it — and the caller reports the file as unmergeable."""
    with pytest.raises(ValueError):
        _settings.merge_permission({"permissions": ["deny"]}, RULE)
    with pytest.raises(ValueError):
        _settings.merge_permission({"permissions": {"deny": "Bash(cd:*)"}}, RULE)


def test_related_rules_finds_the_edited_form_and_nothing_else() -> None:
    """What a reader is shown after being told a managed rule is missing. Which
    entry is the edit is not recoverable, so the verb is the honest guess — and
    finding nothing is an answer, not a gap."""
    settings = {"permissions": {"deny": ["Bash(cd:/tmp/*)", "Bash(rm:*)"]}}
    assert _settings.related_rules(settings, RULE) == ["Bash(cd:/tmp/*)"]
    assert _settings.related_rules({"permissions": {"deny": ["Bash(rm:*)"]}}, RULE) == []
    # The rule itself is not "related to" itself: a caller showing this list is
    # explaining an absence, and echoing the missing rule back reads as present.
    assert _settings.related_rules({"permissions": {"deny": [RULE]}}, RULE) == []


def test_a_shared_group_keeps_its_matcher_and_wfctls_hook_moves_out() -> None:
    """Correcting a matcher in place re-scopes every hook in the group, and a
    group is what a matcher applies to. The README this change retires told
    people to wire the guard by hand, so a hand-wired entry sharing a group with
    their own hook is exactly the population the correction targets — and
    narrowing their hook from `*` to `Bash` is silent, reported as ✓, and not
    undone by uninstall, which owns entries rather than matchers."""
    settings = {
        "hooks": {
            PRETOOL: [
                {
                    "matcher": "*",
                    "hooks": [
                        {"type": "command", "command": "./my-audit.sh"},
                        {"type": "command", "command": GUARD},
                    ],
                }
            ]
        }
    }
    assert _settings.merge_hook(settings, PRETOOL, GUARD, "Bash") is True
    theirs, ours = settings["hooks"][PRETOOL]
    assert theirs == {
        "matcher": "*",
        "hooks": [{"type": "command", "command": "./my-audit.sh"}],
    }
    assert ours == {"matcher": "Bash", "hooks": [{"type": "command", "command": GUARD}]}
    # And uninstall leaves their group exactly as they wrote it.
    _settings.remove_hooks(settings, PRETOOL)
    assert settings["hooks"][PRETOOL] == [theirs]
