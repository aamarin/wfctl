"""Remove the tool-approval entries an older wfctl merged into Bob Shell's
settings file.

wfctl no longer writes `.bob/settings.json`. Bob Shell gives the project file
precedence over the user's `~/.bob/settings/settings.json`, so a starter
allow-list written into the project replaced whatever the user had approved
globally. What remains here is the removal half, for installs that still carry
those entries:

    {"tools": {"allowed": ["read_file", "execute_command(git)", ...]}}

A flat list of plain strings, so an entry carries no marker saying wfctl added
it. The manifest's `tools` receipts are the only record of that, and an entry
the receipts do not claim is the user's; see
`docs/architecture/the-manifest-owns-what-carries-no-marker.md`.

Same constraint as `_settings.py`: pure functions over already-parsed data, no
`wfctl.*` imports and no I/O. The caller reads, decides, and writes.
"""
from __future__ import annotations


def _allowed(settings: dict) -> list:
    """The consumer's `tools.allowed` list, or empty for any other shape.

    The file is hand-editable, so a `tools` that is not a map, or an `allowed`
    that is not an array, reads as "no entries here" rather than raising.
    """
    tools = settings.get("tools")
    if not isinstance(tools, dict):
        return []
    allowed = tools.get("allowed")
    return allowed if isinstance(allowed, list) else []


def remove_tool_allow(settings: dict, entry: str) -> bool:
    """Drop `entry` from the consumer's `tools.allowed`. True when it changed.

    Prunes upward: an emptied `allowed` goes, and a `tools` map left with
    nothing in it goes with it, so a file that never had the key returns to a
    file that has no key rather than to one carrying an empty scaffold wfctl
    invented.

    Removes every copy, not the first. A duplicate can only come from a
    hand-edit, and leaving the second behind would report the entry gone while
    Bob Shell still approves it.
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
