"""The context names a repo's records can govern, and the ones a branch lists.

The domain page holds the name list in header lines beside its `State` line, and
a branch's `design.md` holds the contexts it changes in one header line of its
own. Only the header, the lines above the first `## ` heading, is read, never
the body. A page or a design can quote the other's lines in a code block below
that heading, and reading a quoted line would answer for a branch that never
wrote one. The scan doesn't track code fences, so a quote above the first
heading is read.

A name is lowercase letters and digits joined by single hyphens. Each name
becomes a folder under the branch's `exceptions/`, so a name like `../x` would
point outside it. `names` leaves anything else off the list, and `malformed`
reports it.

This module imports `_arch`, so `_arch` can't import it back. That's why the
list is passed to `_arch.validate` as an argument and why `split_names` lives
in `_arch`.
"""
from __future__ import annotations

import re
import textwrap
from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple

from wfctl import _arch, _design_exceptions
from wfctl._paths import DOMAIN_DIR

_NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")

# The domain page keeps contexts and outside parties on separate lines because
# they are different kinds of thing. A record can govern either, so they are
# one list here.
_CONTEXTS = "Contexts"
_OUTSIDE = "Outside parties"


def _header(path: Path) -> dict[str, str]:
    """The `key: value` lines above the first `## ` heading, read with the same
    line scan `_arch` uses for frontmatter. Empty when the file can't be read."""
    try:
        lines = path.read_text().splitlines()
    except (OSError, UnicodeDecodeError):
        return {}
    found: dict[str, str] = {}
    for line in lines:
        if line.startswith("## "):
            break
        pair = _arch._key_value(line)
        if pair is not None:
            found[pair[0]] = pair[1]
    return found


def _accepted_pages(arch: Path) -> list[tuple[str, dict[str, str]]]:
    """Each accepted domain page that lists contexts or outside parties, as
    (stem, header)."""
    pages = []
    for path in sorted((arch / DOMAIN_DIR).glob("*.md"), key=lambda p: p.stem):
        header = _header(path)
        if header.get("State") == "accepted" and (_CONTEXTS in header or _OUTSIDE in header):
            pages.append((path.stem, header))
    return pages


def _entries(header: dict[str, str]) -> tuple[str, ...]:
    return _arch.split_names(header.get(_CONTEXTS, "")) + _arch.split_names(
        header.get(_OUTSIDE, "")
    )


def names(arch: Path) -> frozenset[str] | None:
    """The combined name list of every accepted domain page, or None when no
    accepted page has one.

    None and an empty set mean different things. None is a repo that never
    named its contexts, and it keeps the check it had. An empty set would pause
    every branch. A name on two pages counts once.
    """
    pages = _accepted_pages(arch)
    if not pages:
        return None
    return frozenset(
        entry
        for _, header in pages
        for entry in _entries(header)
        if _NAME.fullmatch(entry)
    )


def malformed(arch: Path) -> list[tuple[str, str]]:
    """Each domain-page entry that isn't a valid name, as (page stem, entry)."""
    return [
        (stem, entry)
        for stem, header in _accepted_pages(arch)
        for entry in _entries(header)
        if not _NAME.fullmatch(entry)
    ]


def listed(spec_dir: Path) -> tuple[str, ...] | None:
    """The contexts a branch lists in its `design.md`, in the order written and
    without duplicates. None when there is no `design.md` or no such line. An
    empty line gives `()`, a branch that says it changes no context."""
    header = _header(spec_dir / "design.md")
    if _CONTEXTS not in header:
        return None
    return tuple(dict.fromkeys(_arch.split_names(header[_CONTEXTS])))


class Level(NamedTuple):
    """What differs between the two checks that match contexts: the noun the
    pause uses, the pass whose "no" answers a context, and the command that
    writes it. The architecture check's "no" is the boundary exception, which
    has no pass name."""

    noun: str
    pass_name: str | None
    command: str


ARCHITECTURE = Level("architecture record", None, "wfctl arch none")
SOFTWARE_DESIGN = Level(
    "software design record",
    "brainstorm.software-design",
    "wfctl step none brainstorm.software-design",
)


class Gap(NamedTuple):
    """Why brainstorm pauses and how to fix it. `unanswered` is True only when
    the cause is a listed context with no answer, the one case where git's
    silence about the branch's records can change the result."""

    reason: str
    remedy: str
    unanswered: bool


def _no(spec_dir: Path, context: str, level: Level) -> str | None:
    """The reason a branch gave for needing no record for `context`, if any."""
    if level.pass_name is None:
        return _design_exceptions.boundary(spec_dir, context=context)
    return _design_exceptions.passes(spec_dir, context=context).get(level.pass_name)


def _governed(context: str, records: Iterable[_arch.Record]) -> bool:
    return any(context in record.governs for record in records)


def unanswered(
    listed: Iterable[str], records: Iterable[_arch.Record], spec_dir: Path, level: Level
) -> str | None:
    """The first listed context that no record governs and that has no "no", or
    None when each one has an answer. A "no" for one context never answers
    another."""
    held = list(records)
    for context in listed:
        if not _governed(context, held) and _no(spec_dir, context, level) is None:
            return context
    return None


def pause(
    known: frozenset[str],
    spec_dir: Path,
    records: Iterable[_arch.Record],
    level: Level,
    *,
    location: str,
) -> Gap | None:
    """Why brainstorm pauses, or None when every listed context has an answer.

    A missing or empty `Contexts` line comes first, then a name that isn't on
    the domain page, then a context with no answer. The order matters because a
    misspelled name would otherwise read as a context nobody answered, and the
    remedy would ask for a record about a context that doesn't exist.

    `location` is where a record for this level goes. The caller knows the repo
    root and this module doesn't.
    """
    branch_lists = listed(spec_dir)
    if not branch_lists:
        return Gap(
            "design.md lists no contexts",
            "  Add a line under the title of design.md listing the contexts this branch changes:\n"
            "      Contexts: <names from the domain page>",
            False,
        )
    unknown = next((c for c in branch_lists if c not in known), None)
    if unknown is not None:
        wrapped = textwrap.fill(
            ", ".join(sorted(known)), width=84, initial_indent="      ",
            subsequent_indent="      ",
        )
        return Gap(
            f"{unknown} is not a context on the domain page",
            f"  The domain page lists:\n{wrapped}",
            False,
        )
    context = unanswered(branch_lists, records, spec_dir, level)
    if context is None:
        return None
    return Gap(
        f"no {level.noun} governs {context}",
        f"  Either add a record whose governs field names {context}, under:\n"
        f"      {location}/\n"
        "  or state that it needs none:\n"
        f'      {level.command} --context {context} --reason "<why>"',
        True,
    )


def answers(
    listed: Iterable[str], records: Iterable[_arch.Record], spec_dir: Path, level: Level
) -> list[str]:
    """One `<context>: no — <reason>` line for each listed context answered with
    a "no" and not by a record, for the done row in `wfctl status`."""
    held = list(records)
    lines = []
    for context in listed:
        reason = _no(spec_dir, context, level)
        if reason is not None and not _governed(context, held):
            lines.append(f"{context}: no — {reason}")
    return lines
