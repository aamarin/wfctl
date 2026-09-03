"""Merge wfctl's own hook entries into a settings file the consumer owns.

The merge install mode's pure half — see `docs/architecture/install-modes.md`
for why the mode exists.

Ownership is per-entry, and the marker is the command itself: every managed hook
runs `wfctl hook user-prompt`, so the installer finds its own rows by prefix
instead of by a sidecar list that can go stale against the file. A consumer who
deletes the entry by hand leaves nothing behind to resurrect.

Same constraint as `_workmux`: pure functions over already-parsed data, no
`wfctl.*` imports and no I/O. The caller reads, decides, and writes. That is what
lets a round-trip — foreign hooks in, install, uninstall, byte-compare — be three
dict literals instead of a git repo and a settings file on disk.

The schema mirrored here is Claude Code's:

    {"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command",
                                                "command": "..."}]}]}}

Two nested levels named `hooks`: an outer map of event name → *groups*, and
inside each group a list of the hooks that run for it. Groups exist to carry a
`matcher` for tool events; `UserPromptSubmit` has nothing to match on, so a
managed entry is a group of one.
"""
from __future__ import annotations

from typing import Any

# Every hook wfctl installs runs this, and nothing else does. Matching on the
# command rather than on a name field is what keeps ownership readable from the
# settings file alone — a consumer looking at their own JSON can see which rows
# are not theirs without consulting wfctl's manifest.
#
# The trailing space is load-bearing: without it this also claims a consumer's
# own `wfctl hooks-report` or `wfctl hookup`, and uninstall would delete it.
MANAGED_PREFIX = "wfctl hook "


def _is_managed(hook: Any) -> bool:
    """Is this one hook entry wfctl's?

    Defensive about shape because the file is hand-editable: a consumer may have
    written a bare string, a list, or a typo'd key into the array, and a merge
    that raises on the way past leaves them with an install that cannot run at
    all. Anything unrecognisable is simply not ours.
    """
    return (
        isinstance(hook, dict)
        and isinstance(hook.get("command"), str)
        and hook["command"].startswith(MANAGED_PREFIX)
    )


def managed_command(settings: dict, event: str) -> str | None:
    """The command of the managed hook installed for `event`, or None.

    What `doctor` compares against the command the running wfctl would install:
    equal means current, different means behind, None means the consumer removed
    it after wfctl recorded it.
    """
    found = _managed(settings, event)
    return found[0]["command"] if found else None


def _managed(settings: dict, event: str) -> list[dict]:
    """Every managed hook entry installed for `event`, in file order."""
    return [
        hook
        for group in _groups(settings, event)
        for hook in _hooks_of(group)
        if _is_managed(hook)
    ]


def _groups(settings: dict, event: str) -> list:
    """The group list for `event`, or empty when the file has no such shape."""
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return []
    groups = hooks.get(event)
    return groups if isinstance(groups, list) else []


def _hooks_of(group: Any) -> list:
    """The hook entries inside one group, or empty for an unrecognised group."""
    if not isinstance(group, dict):
        return []
    hooks = group.get("hooks")
    return hooks if isinstance(hooks, list) else []


def merge_hook(settings: dict, event: str, command: str) -> bool:
    """Install `command` as the managed hook for `event`. True when it changed.

    Mutates `settings` in place and reports whether anything actually moved, so
    the caller can skip the write entirely on a re-install. That is the whole
    answer to reflowing a consumer's file: reading and rewriting JSON normalises
    their indentation and key order, so the one run in ten that changes something
    normalises it and the nine that do not never open the file for writing.

    Replaces rather than appends when a managed entry is already present, which
    is what makes a repeated install idempotent. Replacement is in place — the
    entry keeps its position in the array, so a consumer who deliberately ordered
    their hooks around it does not find it moved to the end on the next upgrade.
    """
    managed = [
        hook
        for group in _groups(settings, event)
        for hook in _hooks_of(group)
        if _is_managed(hook)
    ]

    if len(managed) == 1:
        hook = managed[0]
        if hook.get("command") == command and hook.get("type") == "command":
            return False
        hook["command"] = command
        hook["type"] = "command"
        return True

    if managed:
        # More than one can only come from a hand-edit. Two copies inject the same
        # text twice every turn, so they collapse to a single fresh entry rather
        # than leaving a second row for the next install to fight over.
        remove_hooks(settings, event)

    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        # The consumer's `hooks` is not a map. Refusing is the only safe move —
        # overwriting it would destroy whatever they meant by it — and the caller
        # reports the file as unmergeable.
        raise ValueError("`hooks` in the settings file is not an object")
    groups = hooks.setdefault(event, [])
    if not isinstance(groups, list):
        raise ValueError(f"`hooks.{event}` in the settings file is not an array")
    groups.append({"hooks": [{"type": "command", "command": command}]})
    return True


def remove_hooks(settings: dict, event: str) -> bool:
    """Drop every managed hook for `event`. True when it changed.

    Prunes upward as it goes: a group left with no hooks is removed, an event
    left with no groups is removed, and a `hooks` map left empty is removed. That
    upward prune is what lets uninstall restore a file that never had a `hooks`
    key to a file that has no `hooks` key, rather than to one carrying an empty
    scaffold wfctl invented.
    """
    changed = False
    surviving_groups = []
    for group in _groups(settings, event):
        hooks = _hooks_of(group)
        kept = [h for h in hooks if not _is_managed(h)]
        if len(kept) != len(hooks):
            changed = True
            group["hooks"] = kept
        # A group emptied by this prune goes with it; a group that arrived empty,
        # or whose shape we did not recognise, is the consumer's and stays.
        if kept or not hooks:
            surviving_groups.append(group)

    if not changed:
        return False

    hooks_map = settings["hooks"]
    if surviving_groups:
        hooks_map[event] = surviving_groups
    else:
        del hooks_map[event]
        if not hooks_map:
            del settings["hooks"]
    return True
