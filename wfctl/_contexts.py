"""The context names a repo's records can govern, and the ones a branch lists.

The domain page holds the name list in header lines beside its `State` line, and
a branch's `design.md` holds the contexts it changes in one header line of its
own. Only the header is read, never the body. A page or a design can quote the
other's lines in a code block, and reading a quoted line would answer for a
branch that never wrote one.

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
from pathlib import Path

from wfctl import _arch
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
    """Each accepted domain page that lists contexts, as (stem, header)."""
    pages = []
    for path in sorted((arch / DOMAIN_DIR).glob("*.md"), key=lambda p: p.stem):
        header = _header(path)
        if header.get("State") == "accepted" and _CONTEXTS in header:
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
