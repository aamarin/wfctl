"""Merge wfctl's own hook entries into a settings file the consumer owns.

The merge install mode's pure half — see `docs/architecture/install-modes.md`
for why the mode exists.

Ownership is per-entry, and the marker is the command itself: every managed
hook's command starts `wfctl hook `, so the installer finds its own rows by
prefix instead of by a sidecar list that can go stale against the file. A
consumer who deletes the entry by hand leaves nothing behind to resurrect.

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

`PreToolUse` is the event that made the matcher load-bearing. Before it every
managed event was matcher-less, so `merge_hook` could treat a group as a wrapper
and reach past it to the hook inside. It cannot now: a consumer who wired the
guard by hand and scoped it wrongly has a correct command in a group that fires
on everything, and correcting that means reaching the container.

Permissions are the other half, and they are a different kind of entry. A rule in
`permissions.deny` is matched by exact string, so it cannot carry `MANAGED_PREFIX`
or any other marker — decorating it changes what it denies. Ownership for those
lives in wfctl's manifest instead of in the file, which is
`docs/architecture/the-manifest-owns-what-carries-no-marker.md`; nothing here
knows about it, because nothing here does I/O.
"""
from __future__ import annotations

from collections.abc import Callable, Collection
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


def subcommand_of(command: str) -> str | None:
    """The `wfctl hook` subcommand `command` runs, or None when it is not wfctl's.

    A managed row's identity (`a-managed-hook-is-owned-by-its-subcommand`). The
    event cannot be it once two wfctl features share one — `Stop` carries both the
    reply check and the session restart — and the whole command cannot either,
    because the redirect and `|| true` after the name change between versions
    without the feature changing. The first word after the prefix is already
    written in every row wfctl installs, so no marker is added to find it.
    """
    if not command.startswith(MANAGED_PREFIX):
        return None
    words = command[len(MANAGED_PREFIX):].split()
    return words[0] if words else ""


def managed_command(
    settings: dict, event: str, subcommand: str | None = None
) -> str | None:
    """The command of the managed hook for `event` running `subcommand`, or None.

    What `doctor` compares against the command the running wfctl would install:
    equal means current, different means behind, None means the consumer removed
    it after wfctl recorded it. `subcommand=None` is any managed row on the event,
    first in file order — what a caller asking about an event with one wfctl
    feature on it means.
    """
    found = _managed_pairs(settings, event, subcommand)
    return found[0][1]["command"] if found else None


def managed_subcommands(settings: dict, event: str) -> list[str]:
    """The subcommands of every managed row on `event`, in file order."""
    return [
        subcommand_of(hook["command"]) or ""
        for _, hook in _managed_pairs(settings, event)
    ]


def _managed_pairs(
    settings: dict, event: str, subcommand: str | None = None
) -> list[tuple[dict, dict]]:
    """Every managed hook for `event` with the group holding it, in file order.

    Paired rather than flattened because a tool event's `matcher` lives on the
    group, not on the hook: a caller correcting one has to reach the container,
    and the flattened form has already thrown it away.

    Narrowed to one subcommand when given, which is every writer's view: a merge
    of the reply check must not see the session restart beside it as a duplicate
    of itself.
    """
    return [
        (group, hook)
        for group in _groups(settings, event)
        for hook in _hooks_of(group)
        if _is_managed(hook)
        and (subcommand is None or subcommand_of(hook["command"]) == subcommand)
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


def merge_hook(
    settings: dict, event: str, command: str, matcher: str | None = None
) -> bool:
    """Install `command` as the managed hook for `event`. True when it changed.

    Mutates `settings` in place and reports whether anything actually moved, so
    the caller can skip the write entirely on a re-install. That is the whole
    answer to reflowing a consumer's file: reading and rewriting JSON normalises
    their indentation and key order, so the one run in ten that changes something
    normalises it and the nine that do not never open the file for writing.

    Replaces rather than appends when a managed entry running the same subcommand
    is already present, which is what makes a repeated install idempotent.
    Replacement is in place — the entry keeps its position in the array, so a
    consumer who deliberately ordered their hooks around it does not find it moved
    to the end on the next upgrade.

    A managed row running a *different* subcommand is another wfctl feature and is
    left where it is. That costs a rename its position: a subcommand wfctl renamed
    no longer matches its successor, so the new row is appended and the old one is
    left for `prune_unshipped`, which the caller runs with the set it ships.

    `matcher` is the group's, not the hook's, and `None` means the event has
    nothing to match on — which leaves every group's matcher exactly as found,
    the behaviour the two matcher-less events have always had. Given one, an
    entry adopted from a hand-edit has its group corrected as well as its
    command: a consumer who followed the README but wrote `"matcher": "*"` had a
    command wfctl recognises inside a group that fires on every tool, and
    replacing only the command would report success over an entry still scoped
    wrong.

    Corrected in place only where the group holds nothing else. A group is the
    unit a matcher applies to, so one shared with the consumer's own hook has
    wfctl's moved out to a group of its own rather than rewritten underneath
    them — which is the one case where the position guarantee above does not
    hold, and the reason it does not is that keeping the position would mean
    keeping their matcher wrong.
    """
    subcommand = subcommand_of(command)
    managed = _managed_pairs(settings, event, subcommand)

    if len(managed) == 1:
        group, hook = managed[0]
        changed = False
        if hook.get("command") != command or hook.get("type") != "command":
            hook["command"] = command
            hook["type"] = "command"
            changed = True
        if matcher is not None and group.get("matcher") != matcher:
            if len(_hooks_of(group)) == 1:
                group["matcher"] = matcher
            else:
                # The group is shared, and a matcher is the whole group's. The
                # consumer put their own hook in here — correcting the matcher in
                # place would silently re-scope theirs, which is the one thing
                # this mode promises never to do, and `remove_hooks` would leave
                # it narrowed after an uninstall because a matcher is not an entry
                # it owns. So wfctl's hook leaves instead: theirs keeps the
                # matcher it was written with, and the guard gets the scope it
                # needs.
                group["hooks"] = [h for h in _hooks_of(group) if h is not hook]
                _groups(settings, event).append(
                    {"matcher": matcher, "hooks": [hook]}
                )
            changed = True
        return changed

    if managed:
        # More than one can only come from a hand-edit. Two copies inject the same
        # text twice every turn, so they collapse to a single fresh entry rather
        # than leaving a second row for the next install to fight over.
        _remove_where(
            settings, event, lambda h: subcommand_of(h["command"]) == subcommand
        )

    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        # The consumer's `hooks` is not a map. Refusing is the only safe move —
        # overwriting it would destroy whatever they meant by it — and the caller
        # reports the file as unmergeable.
        raise ValueError("`hooks` in the settings file is not an object")
    groups = hooks.setdefault(event, [])
    if not isinstance(groups, list):
        raise ValueError(f"`hooks.{event}` in the settings file is not an array")
    fresh: dict = {"hooks": [{"type": "command", "command": command}]}
    if matcher is not None:
        # Ahead of `hooks` rather than appended after it: this is the order
        # Claude Code's own documentation writes a tool-event group in, and the
        # file is one a person reads.
        fresh = {"matcher": matcher, **fresh}
    groups.append(fresh)
    return True


def remove_hooks(settings: dict, event: str) -> bool:
    """Drop every managed hook for `event`. True when it changed.

    Prunes upward as it goes: a group left with no hooks is removed, an event
    left with no groups is removed, and a `hooks` map left empty is removed. That
    upward prune is what lets uninstall restore a file that never had a `hooks`
    key to a file that has no `hooks` key, rather than to one carrying an empty
    scaffold wfctl invented.

    Every subcommand, not one. Uninstall removes whatever wfctl put on the event,
    including a row an older wfctl installed under a name this one never ships.
    """
    return _remove_where(settings, event, lambda _: True)


def prune_unshipped(settings: dict, event: str, shipped: Collection[str]) -> bool:
    """Drop managed rows on `event` whose subcommand is not in `shipped`.

    What keeps a rename from leaving its predecessor running beside it, now that
    `merge_hook` no longer treats any wfctl row on the event as the one to
    replace. Only wfctl's rows are candidates, so a consumer's hook is untouched
    whatever it runs.
    """
    return _remove_where(
        settings, event, lambda h: subcommand_of(h["command"]) not in shipped
    )


def _remove_where(
    settings: dict, event: str, doomed: Callable[[dict], bool]
) -> bool:
    """Drop managed hooks on `event` for which `doomed` holds. True when it changed.

    `doomed` sees managed entries only — `_is_managed` has already checked the
    shape it reads — so a predicate can index `command` without guarding.
    """
    changed = False
    surviving_groups = []
    for group in _groups(settings, event):
        hooks = _hooks_of(group)
        kept = [h for h in hooks if not (_is_managed(h) and doomed(h))]
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


def _deny(settings: dict) -> list:
    """The consumer's `permissions.deny` list, or empty for any other shape.

    Same posture as `_groups`: the file is hand-editable, so a `permissions` that
    is not a map, or a `deny` that is not an array, reads as "no rules here"
    rather than raising. A reader asking whether a rule is present gets a truthful
    no; only a writer has to care, and `merge_permission` raises there.
    """
    permissions = settings.get("permissions")
    if not isinstance(permissions, dict):
        return []
    deny = permissions.get("deny")
    return deny if isinstance(deny, list) else []


def permission_present(settings: dict, rule: str) -> bool:
    """Is `rule` in the consumer's deny list, exactly as written?

    Exact string equality, because that is how the agent matches the rule itself:
    a near-miss denies something else, so it is not this rule in a different
    spelling. What `doctor` asks, and half of what the uninstall gate asks.
    """
    return rule in _deny(settings)


def merge_permission(settings: dict, rule: str) -> bool:
    """Add `rule` to the consumer's deny list. True when it was not already there.

    The return value is the receipt: the caller records it, because after this
    runs the file can no longer answer whether wfctl was the one that added the
    rule. Nothing here can carry that answer — a deny rule is matched by exact
    text and so cannot hold a marker the way a hook's command does.
    """
    if permission_present(settings, rule):
        return False

    permissions = settings.setdefault("permissions", {})
    if not isinstance(permissions, dict):
        # Same arm as `hooks` above and for the same reason: whatever the consumer
        # meant by this key, overwriting it is worse than declining to merge.
        raise ValueError("`permissions` in the settings file is not an object")
    deny = permissions.setdefault("deny", [])
    if not isinstance(deny, list):
        raise ValueError("`permissions.deny` in the settings file is not an array")
    deny.append(rule)
    return True


def remove_permission(settings: dict, rule: str) -> bool:
    """Drop `rule` from the consumer's deny list. True when it changed.

    Prunes upward like `remove_hooks`: an emptied `deny` goes, and a `permissions`
    map left with nothing in it goes with it, so uninstall returns a file that
    never had the key to a file that has no key rather than to one carrying an
    empty scaffold wfctl invented. A `permissions` still holding `allow` stays.

    Removes every copy, not the first. A duplicate can only come from a hand-edit,
    and leaving the second behind would have uninstall report the rule gone while
    the agent still denies on it.
    """
    deny = _deny(settings)
    if rule not in deny:
        return False

    deny[:] = [existing for existing in deny if existing != rule]
    if deny:
        return True

    permissions = settings["permissions"]
    del permissions["deny"]
    if not permissions:
        del settings["permissions"]
    return True


def related_rules(settings: dict, rule: str) -> list[str]:
    """Deny rules that block the same verb as `rule`, `rule` itself aside.

    What a caller shows a reader who was told a managed rule is missing. Which of
    their rules is the edited form of it is not recoverable — a deny list is a
    list of strings and nothing links an entry to what it used to be — so the verb
    is the closest honest guess: `Bash(cd:*)` narrowed to `Bash(cd:/tmp/*)` still
    starts `Bash(cd`, and a rule about anything else does not.

    Returning nothing is an answer rather than a gap: the rule may simply have
    been deleted, and inventing a candidate would be worse than saying nothing.
    """
    # The colon is kept on the prefix. Without it `Bash(cd:*)` also claims
    # `Bash(cdk:*)`, and naming an unrelated rule as "the edited form" is worse
    # than naming none: it sends a reader to change something they never touched.
    verb = rule.split(":", 1)[0] + ":"
    return [
        existing
        for existing in _deny(settings)
        if isinstance(existing, str) and existing != rule and existing.startswith(verb)
    ]


def managed_matcher(settings: dict, event: str) -> str | None:
    """The matcher on the group holding the managed hook for `event`, or None.

    None means either no managed hook or a group carrying no matcher, and a
    caller comparing against an expected matcher wants the same answer for both:
    a tool event whose group says nothing fires on everything, which is not what
    was installed.

    Separate from `managed_command` because drift has two shapes here and they
    are repaired by the same command but described differently — an entry that
    is behind is running old code, one that is scoped wrong is running correct
    code where nothing will ever call it.
    """
    found = [group for group, _ in _managed_pairs(settings, event)]
    if not found:
        return None
    matcher = found[0].get("matcher")
    return matcher if isinstance(matcher, str) else None
