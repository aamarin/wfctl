"""Read the `review` key in `wfctl.json`: the review groups, in run order.

One reader for every caller, so `wfctl check config`, `wfctl review start` and
the worktree guard can't disagree about which reviewers a repository declared.
The guard imports this module on a matched command, so it imports nothing that
loads `typer` or `rich`.

`security` and `code` always run first, in that order, whether or not the list
names them, and every other group follows in list order. The code group reviews
the security group's fixes, and a custom group reviews the result of both
(`622-review-groups-list.md`).
"""
from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path

CONFIG_PATH = "wfctl.json"

# The one model that runs inside the current agent, so it needs no command.
CLAUDE = "claude"

_BUILT_IN = ("security", "code")
_DEFAULT_SKILL = {"security": "reviewing-security"}
_FALLBACK_SKILL = "code-review"
_DEFAULT_REVIEWERS: list[object] = [{"name": CLAUDE, "count": 3}]

# Every key each level may hold. A misspelled key, such as `reviewer` for
# `reviewers`, would otherwise fall back to the default and pass as valid.
_REVIEW_KEYS = ("commands", "groups")
_GROUP_KEYS = ("group", "skill", "reviewers")
_REVIEWER_KEYS = ("name", "count")

# A group name becomes a directory under `reviews/`, so it can't hold a slash
# or start with a dot. Matched with `fullmatch`, since `$` also matches before
# a trailing newline. A model name follows the same rule, since `review start`
# prints it in lines the panel skill reads one at a time.
PLAIN_NAME = re.compile(r"[a-z][a-z0-9-]*")
# A command is printed on that same line, so it can't hold a control character
# either. A newline in one would print a roster line nobody declared.
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
# A skill is named the way an agent loads one, optionally after a plugin name,
# such as `agent-skills:review`. A path is never a skill name.
_SKILL_NAME = re.compile(r"[a-z0-9][a-z0-9-]*(?::[a-z0-9][a-z0-9-]*)?")

# Each reviewer is a full review of the range, and more than this in one group
# is a typo rather than a panel. Unbounded, a count of 2,000,000 took two
# seconds to load on every guarded command. The bound is on the group's total,
# since repeating an entry under the bound reached the same count.
MAX_COUNT = 20


@dataclass(frozen=True)
class Reviewer:
    """One expected report: its id, such as `s3`, and the model that writes it.

    `command` is how a model other than Claude is started, and None for Claude.
    """

    id: str
    model: str
    command: str | None


@dataclass(frozen=True)
class Group:
    name: str
    skill: str
    reviewers: tuple[Reviewer, ...]


def load(repo_root: Path) -> tuple[list[Group], list[str]]:
    """Return (the groups in run order, problems).

    Any problem returns no groups at all. A run started from half a declaration
    would expect a different roster from the one the repository wrote, so every
    caller stops on a problem instead.
    """
    path = repo_root / CONFIG_PATH
    if not path.exists():
        return _resolve({}, {}), []
    try:
        data = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return [], [f"{CONFIG_PATH}: not valid JSON ({e})"]
    if not isinstance(data, dict):
        return [], [f"{CONFIG_PATH}: top level must be an object"]

    review = data.get("review", {})
    if not isinstance(review, dict):
        return [], ["review must be an object"]

    problems = [f"review: unknown key '{k}'" for k in review if k not in _REVIEW_KEYS]
    commands = _commands(review.get("commands", {}), problems)

    entries = review.get("groups", [])
    if not isinstance(entries, list):
        return [], [*problems, "review.groups must be a list"]

    declared: dict[str, dict[str, object]] = {}
    for i, entry in enumerate(entries):
        name = entry.get("group") if isinstance(entry, dict) else None
        if not isinstance(name, str):
            problems.append(f"review.groups[{i}] has no group name")
            continue
        if not PLAIN_NAME.fullmatch(name):
            problems.append(
                f"review group '{name}': a name is lowercase letters, digits and "
                "hyphens, starting with a letter"
            )
            continue
        if name in declared:
            problems.append(f"review group '{name}' is listed twice")
            continue
        problems += [
            f"review group '{name}': unknown key '{k}'" for k in entry if k not in _GROUP_KEYS
        ]
        declared[name] = entry

    groups = _resolve(declared, commands, problems)
    return ([], problems) if problems else (groups, [])


def _commands(found: object, problems: list[str]) -> dict[str, str] | None:
    """`review.commands`, or None when it isn't an object of strings.

    A command wfctl can't split into words is a finding here rather than a
    model `review start` reports as missing, since the quoting is a fact about
    the repository and not about the machine.
    """
    if not isinstance(found, dict) or not all(
        isinstance(v, str) and v.strip() for v in found.values()
    ):
        problems.append("review.commands must map each model to a command string")
        return None
    if CLAUDE in found:
        problems.append(f"review.commands: {CLAUDE} runs inside the agent and takes no command")
    for model, command in found.items():
        if _CONTROL.search(command):
            problems.append(
                f"review.commands: the command for '{model}' holds a control character"
            )
            continue
        try:
            shlex.split(command)
        except ValueError as e:
            problems.append(f"review.commands: can't split the command for '{model}': {e}")
    return found


def _resolve(
    declared: dict[str, dict[str, object]],
    commands: dict[str, str] | None,
    problems: list[str] | None = None,
) -> list[Group]:
    """Every group in run order, with its reviewers numbered, appending what's
    wrong with each declaration to `problems`.

    `commands` is None when `review.commands` couldn't be read. That's already
    a finding, and a second one per model saying it has no command would point
    at the wrong fix.
    """
    problems = problems if problems is not None else []
    order = [*_BUILT_IN, *(n for n in declared if n not in _BUILT_IN)]

    first_letter: dict[str, str] = {}
    for name in order:
        earlier = first_letter.setdefault(name[0], name)
        if earlier != name:
            problems.append(
                f"review groups '{earlier}' and '{name}' both start with "
                f"'{name[0]}'; reviewer ids would clash"
            )

    groups: list[Group] = []
    for name in order:
        entry = declared.get(name, {})
        skill = entry.get("skill", _DEFAULT_SKILL.get(name, _FALLBACK_SKILL))
        if not isinstance(skill, str) or not _SKILL_NAME.fullmatch(skill):
            problems.append(f"review group '{name}': skill must be a skill name")
            continue
        if "reviewers" in entry:
            listed = entry["reviewers"]
        elif name in _BUILT_IN:
            listed = _DEFAULT_REVIEWERS
        else:
            listed = []
        if not isinstance(listed, list):
            problems.append(f"review group '{name}': reviewers must be a list")
            continue
        if not listed:
            problems.append(f"review group '{name}' has no reviewers")
            continue
        reviewers = _reviewers(name, listed, commands, problems)
        if reviewers is not None:
            groups.append(Group(name, skill, reviewers))
    return groups


def _reviewers(
    group: str, listed: list[object], commands: dict[str, str] | None, problems: list[str],
) -> tuple[Reviewer, ...] | None:
    """The group's reviewers, numbered across its whole list, so the first
    Codex reviewer after two Claude ones is `s3` rather than a second `s1`."""
    found: list[Reviewer] = []
    ok = True
    for spec in listed:
        model = spec.get("name") if isinstance(spec, dict) else None
        if not isinstance(model, str) or not model:
            problems.append(f"review group '{group}': each reviewer needs a name and a count")
            ok = False
            continue
        assert isinstance(spec, dict)
        if not PLAIN_NAME.fullmatch(model):
            problems.append(
                f"review group '{group}': model {model!r} isn't lowercase letters, "
                "digits and hyphens, starting with a letter"
            )
            ok = False
            continue
        unknown = [k for k in spec if k not in _REVIEWER_KEYS]
        if unknown:
            problems.append(f"review group '{group}': unknown key '{unknown[0]}' in a reviewer")
            ok = False
            continue
        count = spec.get("count")
        # `bool` is a subclass of `int`, and `"count": true` is a typo rather
        # than a count of one.
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            problems.append(f"review group '{group}': count for '{model}' must be 1 or more")
            ok = False
            continue
        if len(found) + count > MAX_COUNT:
            problems.append(f"review group '{group}' has more than {MAX_COUNT} reviewers")
            return None
        command = None if model == CLAUDE or commands is None else commands.get(model)
        if model != CLAUDE and command is None:
            if commands is not None:
                problems.append(
                    f"review group '{group}': model '{model}' has no entry in review.commands"
                )
            ok = False
            continue
        for _ in range(count):
            found.append(Reviewer(f"{group[0]}{len(found) + 1}", model, command))
    return tuple(found) if ok else None
