"""Merge wfctl's own tool-approval entries into Bob Shell's settings file.

The merge install mode's pure half for Bob, sibling to `_settings.py` (Claude
Code's). Kept as its own module rather than folded into `_settings.py` because
that module's schema — `permissions.deny`, `hooks` — is Claude Code's own, by
its own docstring's declaration; Bob Shell's is unrelated:

    {"tools": {"allowed": ["read_file", "execute_command(git)", ...]}}

A flat list of plain strings, so ownership cannot be marked in the entry the
way a managed hook's command is (it starts `wfctl hook `) — an entry here is
exactly the text Bob Shell matches a tool call against, and decorating it
changes what it approves. Ownership for these lives in wfctl's manifest
instead, same as Claude's deny rules and for the same reason; see
`docs/architecture/the-manifest-owns-what-carries-no-marker.md`.

Same constraint as `_settings.py`: pure functions over already-parsed data, no
`wfctl.*` imports and no I/O. The caller reads, decides, and writes.
"""
from __future__ import annotations


def _allowed(settings: dict) -> list:
    """The consumer's `tools.allowed` list, or empty for any other shape.

    The file is hand-editable, so a `tools` that is not a map, or an `allowed`
    that is not an array, reads as "no entries here" rather than raising. A
    reader asking whether an entry is present gets a truthful no; only a writer
    has to care, and `merge_tool_allow` raises there.
    """
    tools = settings.get("tools")
    if not isinstance(tools, dict):
        return []
    allowed = tools.get("allowed")
    return allowed if isinstance(allowed, list) else []


def tool_allow_present(settings: dict, entry: str) -> bool:
    """Is `entry` in the consumer's `tools.allowed`, exactly as written?

    Exact string equality, because that is how Bob Shell matches the entry
    itself: a near-miss approves something else, so it is not this entry in a
    different spelling.
    """
    return entry in _allowed(settings)


def merge_tool_allow(settings: dict, entry: str) -> bool:
    """Add `entry` to the consumer's `tools.allowed`. True when it was not
    already there.

    The return value is the receipt: the caller records it, because after this
    runs the file can no longer answer whether wfctl was the one that added the
    entry. Nothing here can carry that answer — an allow entry is matched by
    exact text and so cannot hold a marker the way a hook's command does.
    """
    if tool_allow_present(settings, entry):
        return False

    tools = settings.setdefault("tools", {})
    if not isinstance(tools, dict):
        # Whatever the consumer meant by this key, overwriting it is worse
        # than declining to merge.
        raise ValueError("`tools` in the settings file is not an object")
    allowed = tools.setdefault("allowed", [])
    if not isinstance(allowed, list):
        raise ValueError("`tools.allowed` in the settings file is not an array")
    allowed.append(entry)
    return True


def remove_tool_allow(settings: dict, entry: str) -> bool:
    """Drop `entry` from the consumer's `tools.allowed`. True when it changed.

    Prunes upward: an emptied `allowed` goes, and a `tools` map left with
    nothing in it goes with it, so uninstall returns a file that never had the
    key to a file that has no key rather than to one carrying an empty
    scaffold wfctl invented.

    Removes every copy, not the first. A duplicate can only come from a
    hand-edit, and leaving the second behind would have uninstall report the
    entry gone while Bob Shell still approves it.
    """
    allowed = _allowed(settings)
    if entry not in allowed:
        return False

    allowed[:] = [existing for existing in allowed if existing != entry]
    if allowed:
        return True

    tools = settings["tools"]
    del tools["allowed"]
    if not tools:
        del settings["tools"]
    return True
