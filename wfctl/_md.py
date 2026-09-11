"""One fence walker, for the modules that were each carrying their own.

Knowing which lines of a markdown document sit inside a fenced code block was
answered three times and three ways before this existed: `_shape` implemented
CommonMark's closing rule, and the other two matched a prefix. A prefix match
closes a fence on ```` ```python ```` appearing *inside* one, so a document
quoting a fenced example — which every caller here reads, because each is
checking text that quotes the rules it enforces — has the rest of the example
scanned as prose.

So the strict rule is the shared one, and it is the one whose failure `_shape`
already documented: a reply quoting a ```-block inside a ````-fence reported
every heading in the quotation as a violation of the rule it was quoting.

This yields per-line state and projects nothing. Each caller wants a different
shape from the same walk — lines outside, blocks with their opening line number,
or the text with fenced lines blanked — and a walker that returned any one of
them would have the other two building it back from a lossy view.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from typing import NamedTuple

# Up to three leading spaces, which is markdown's own limit: at four the line is
# an indented code block and opens nothing. The info string is captured because
# it is what separates an opening fence from a closing one.
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


class Line(NamedTuple):
    """One line of the document, and where it sits relative to the fences."""

    number: int
    """1-based, so a caller can name it in a finding without adjusting."""

    text: str
    """Verbatim. Callers that want it stripped do their own stripping."""

    inside: bool
    """Inside a fenced block. The fence delimiters themselves are not inside —
    they are the boundary, and `_arch` prints one as output."""

    opened: int | None
    """For a line inside a block, the line number of its opening fence.
    None elsewhere. This is what lets a caller group a walk back into blocks
    without re-deriving the boundaries."""

    fence: bool
    """This line is a fence delimiter. Neither inside nor prose, and all three
    callers need to tell it from both: two skip it, and `_arch` prints it. It is
    reported rather than left to a caller's own regex because a caller matching
    its own would be deciding again what this walk already decided."""


def walk_lines(lines: Iterable[str]) -> Iterator[Line]:
    """`walk`, over lines that are already split.

    The primitive, because a caller holding `splitlines(keepends=True)` has line
    endings inside each string and rejoining them to re-split loses the mapping
    between a `Line.number` and that caller's own list index. Every index past
    the first fence comes back short by the number of lines before it, which
    `test_supersession_appends_inside_the_log_section` is what catches.

    Trailing newlines are harmless to the fence match: `.` does not cross one and
    `$` sits before it, so ``` and ```` compare the same either way.
    """
    marker: str | None = None
    opened = 0
    for number, line in enumerate(lines, 1):
        fence = _FENCE.match(line)
        if marker is None:
            yield Line(number, line, False, None, bool(fence))
            if fence:
                marker, opened = fence.group(1), number
            continue
        if (
            fence
            and fence.group(1)[0] == marker[0]
            and len(fence.group(1)) >= len(marker)
            and not fence.group(2).strip()
        ):
            marker = None
            yield Line(number, line, False, None, True)
            continue
        yield Line(number, line, True, opened, False)


def walk(text: str) -> Iterator[Line]:
    """Every line of `text`, tagged with whether it sits inside a fence.

    A fence closes only on the same character, at least as long as the opener,
    and carrying no info string — CommonMark's rule. An unclosed fence takes the
    rest of the document with it, which is what a truncated reply looks like and
    the correct reading of it.
    """
    return walk_lines(text.splitlines())
