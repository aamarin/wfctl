"""The completion record: what it holds, how it is written, and how it is read.

`checklists/implement-complete.md` says the `implement` step is finished even
with boxes left unticked, because work done outside the implement skill leaves
its boxes unticked. Read by existence alone, it went on saying so after the
story gained a task, and nothing ever removed it (#264). So the record carries
a copy of `tasks.md` as it stood when the step finished, and a task that is
incomplete now and was not incomplete in the copy is new work that reopens the
step (`new-task-reopens-implement`).

The writer and the reader live here together, so the format has one owner
(`264-the-task-copy-lives-in-the-completion-record`). A copy kept in a second
file could go missing apart from the record, and the archive would need a
second row to keep the two together.

This module imports `_md` and the standard library and never `_evidence`,
which imports it. The function that quotes a task list out is passed in by the
caller, since importing `quoted_out` here would close that cycle.
"""
from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable
from datetime import date
from pathlib import Path

from wfctl import _md

RECORD = Path("checklists") / "implement-complete.md"
"""Relative to the feature directory. Named once for the two readers in
`_evidence` and the writer in `cli`. `_archive._SPEC_MAP` keeps its own
string, since that table is plain paths, so a rename has to touch it too."""

_HEADING = "## Tasks at completion"

_BOX = re.compile(r"\[[ xX]\]")
# The inline-span rule `_evidence._blanked` applies. It is spelled again here
# rather than imported, because `_evidence` imports this module. If the two
# drift, a box inside a span is taken as the task's box, its ID stays in the
# description, and a renumber reopens the step, which is the safe direction.
_SPAN = re.compile(r"`[^`\n]+`")
# Only what spec-kit writes straight after the box. A task ID later in the
# text, such as "after T012", stays part of the description, so a new task that
# differs from an old one only in what it depends on cannot hide as old work.
_ID_AND_TAGS = re.compile(r"\s*(?:T\d+\b)?(?:\s*\[(?:P|US\d+)\])*")


def _lines(text: str) -> list[str]:
    """Split on newlines alone.

    `str.splitlines` also splits on form feeds and Unicode line separators,
    so a copy rejoined from its pieces would not equal the `tasks.md` it was
    taken from. The writer and the reader both split this way, so a fence the
    writer counted is a fence the reader sees.
    """
    return text.split("\n")


def render(tasks_text: str, today: date) -> str:
    """The completion record for `tasks_text`, finished on `today`.

    The copy is fenced with tildes one longer than the longest fence marker
    of either character on any line of it, and never shorter than four.
    Every line is counted, not only those a walk reads as fences, because a
    `~~~~~~` line nested inside a backtick block is not a fence to the walk
    but would still close a shorter tilde fence around the copy.
    """
    longest = max(
        (len(marker) for line in _lines(tasks_text) if (marker := _md.opens_fence(line))),
        default=0,
    )
    fence = "~" * max(4, longest + 1)
    body = tasks_text if not tasks_text or tasks_text.endswith("\n") else tasks_text + "\n"
    return (
        f"Implementation complete: {today.isoformat()}\n\n"
        f"{_HEADING}\n\n{fence}markdown\n{body}{fence}\n"
    )


def copy_of(record_text: str) -> str | None:
    """The copy of `tasks.md` this record holds, or None when it holds none.

    None covers a one-line record from before the copy existed, a record whose
    heading has no fenced block after it, and a record cut off before its
    fence closes. The last reads as no copy rather than a short one, since a
    task missing from the copy would read as finished.
    """
    walked = list(_md.walk_lines(_lines(record_text)))
    heading = next(
        (i for i, line in enumerate(walked) if not line.inside and line.text.strip() == _HEADING),
        None,
    )
    if heading is None:
        return None
    opener = next((line for line in walked[heading + 1 :] if line.text.strip()), None)
    if opener is None or not opener.fence:
        return None
    copied: list[str] = []
    # `number` is 1-based, so as an index it is the line after the opener.
    for line in walked[opener.number :]:
        if line.fence:
            return "".join(f"{text}\n" for text in copied)
        copied.append(line.text)
    return None


def description(raw_line: str) -> str:
    """A task's identity for matching: its line without the box, the ID, and
    spec-kit's `[P]` and `[USn]` tags, with whitespace collapsed (FR-006).

    `/speckit.tasks` renumbers and retags on every run, so a description that
    kept either would read an unchanged task as new after any re-run. The box
    is the first one outside an inline code span, since a task may quote the
    checkbox syntax it is about.
    """
    spans = [m.span() for m in _SPAN.finditer(raw_line)]
    box = next(
        (m for m in _BOX.finditer(raw_line) if not any(a <= m.start() < b for a, b in spans)),
        None,
    )
    if box is None:
        return " ".join(raw_line.split())
    rest = raw_line[box.end() :]
    tags = _ID_AND_TAGS.match(rest)
    assert tags is not None  # every group is optional, so it matches empty
    return " ".join(f"{raw_line[: box.start()]} {rest[tags.end() :]}".split())


def _incomplete(raw: str, quote: Callable[[str], str]) -> Counter[str]:
    """The incomplete tasks in a task list, counted by description.

    Which lines are tasks is decided on the quoted-out text, so a task shown in
    a code example is not counted (FR-009), and each description is taken from
    the raw line, so an inline code span keeps its text. The two line up by
    index because quoting out blanks a line rather than dropping it.

    The raw text is split with `splitlines`, not `_lines`, because that is how
    `_blanked` splits it before joining the result on newlines. Splitting the
    two sides differently would pair a form feed's halves with the wrong
    quoted lines.

    A line is incomplete when any box on it is, so `[x] … [ ] …` cannot hide
    the open half behind the ticked one.
    """
    return Counter(
        description(raw_line)
        for raw_line, quoted_line in zip(raw.splitlines(), quote(raw).split("\n"))
        if "[ ]" in quoted_line
    )


def new_incomplete(live: str, copy: str, quote: Callable[[str], str]) -> Counter[str]:
    """The incomplete tasks in the live list that the copy does not account for.

    `quote` is `_evidence.quoted_out`. It is applied here to each text, so the
    raw and quoted forms of one list cannot come from two different texts.

    Matched by count, so two incomplete tasks sharing a description where the
    copy held one leave one new. A task ticked in the copy and incomplete now
    is new too: the copy held it ticked, not incomplete.
    """
    return _incomplete(live, quote) - _incomplete(copy, quote)
