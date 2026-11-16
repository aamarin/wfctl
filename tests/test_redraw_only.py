"""Tests for `arch.redraw_only`, which tells a redraw from a change to a record (#769).

When the user signs off a layout fix to an accepted record's SVG, `wfctl arch
accept` appends a `redrawn` line to the record's `## Log`. That line isn't a
new decision, so the record gate and the design gate pass over a record whose
only change is such a line (FR-026). Each test below breaks one of the four
conditions in research R-014 and checks the record still counts as changed,
since each condition closes one way to pass a real change off as a redraw.

These run without git. `_paths.record_change` produces the diff, and
`test_paths_redraw.py` covers that side.
"""
from __future__ import annotations

import pytest

from wfctl import arch
from wfctl.arch import _records

_REDRAWN = (
    "- 2026-11-21  redrawn     — layout fix · drawing drawings/a-data-flow.svg "
    "sha256:3f9a0c1b2d4e"
)


def _text(status: str = "accepted", log_tail: str = "", decision_tail: str = "") -> str:
    """A record as the diff leaves it, with the Log ending on line 14."""
    return (
        f"---\nstatus: {status}\ndiagram: data-flow\n---\n\n# a\n\n"  # lines 1-7
        f"## Decision\n\nx\n{decision_tail}"  # lines 8-10 (+ tail)
        "\n## Log\n\n"
        "- 2026-11-20  accepted    — x · drawing drawings/a-data-flow.svg sha256:000000000000\n"
        f"{log_tail}"
    )


def _diff(hunks: str) -> str:
    return (
        "diff --git a/docs/architecture/a.md b/docs/architecture/a.md\n"
        "index 1111111..2222222 100644\n"
        "--- a/docs/architecture/a.md\n"
        "+++ b/docs/architecture/a.md\n"
        f"{hunks}"
    )


_ONE_REDRAW = _diff(f"@@ -14,0 +15 @@\n+{_REDRAWN}\n")


def test_one_redrawn_line_appended_to_an_accepted_records_log_is_a_redraw() -> None:
    """The plain case every other test varies one thing from."""
    assert arch.redraw_only(_ONE_REDRAW, _text(log_tail=f"{_REDRAWN}\n"))


def test_a_proposed_record_is_never_a_redraw() -> None:
    """A `redrawn` line on a proposed record would skip the gates for a
    record nobody has accepted yet (PR-026)."""
    assert not arch.redraw_only(_ONE_REDRAW, _text("proposed", log_tail=f"{_REDRAWN}\n"))


def test_a_form_feed_above_the_log_doesnt_move_the_log_down() -> None:
    """git counts lines by newline alone, and `splitlines` also breaks at a
    form feed. Two form feeds in the Decision put `## Log` two lines later
    than git's numbering, which let a line added under the next heading read
    as inside the Log."""
    text = (
        "---\nstatus: accepted\ndiagram: data-flow\n---\n\n# a\n\n"  # lines 1-7
        "## Decision\n\nx\fy\fz\n\n"  # lines 8-11
        "## Log\n\n"  # lines 12-13
        "- 2026-11-20  accepted    — x · drawing drawings/a-data-flow.svg sha256:000000000000\n"
        f"## Notes\n{_REDRAWN}\n"  # lines 15-16
    )

    assert not arch.redraw_only(_diff(f"@@ -15,0 +16 @@\n+{_REDRAWN}\n"), text)


@pytest.mark.parametrize("separator", ["\r", "\f", " "])
def test_a_redrawn_line_hiding_a_line_break_is_not_a_redraw(separator: str) -> None:
    """git counts a lone carriage return, a form feed, or U+2028 as part of
    one line. The readers that parse the record, and GitHub's renderer, break
    there, so a redrawn line could carry a new `## Boundary` past the gates."""
    smuggled = f"{_REDRAWN}{separator}{separator}## Boundary{separator}{separator}new"
    diff = _diff(f"@@ -14,0 +15 @@\n+{smuggled}\n")

    assert not arch.redraw_only(diff, _text(log_tail=f"{smuggled}\n"))


def test_a_lone_carriage_return_the_read_turned_into_a_newline_is_not_a_redraw() -> None:
    """`record_change` reads git's output in text mode, which turns a lone
    carriage return into a newline. The half after it lands in the hunk with
    no `+` prefix, and skipping it would drop the smuggled heading unseen."""
    diff = _diff(f"@@ -14,0 +15 @@\n+{_REDRAWN}\n\n## Boundary\n\nnew\n")

    assert not arch.redraw_only(diff, _text(log_tail=f"{_REDRAWN}\r\r## Boundary\r\rnew\n"))


def test_an_empty_diff_is_not_a_redraw() -> None:
    """An uncommitted record has an empty committed diff. Reading that as a
    redraw would let the record skip the gates before anyone saw it."""
    assert not arch.redraw_only("", _text())


def test_a_redrawn_shaped_bullet_under_the_decision_is_not_a_redraw() -> None:
    """A bullet shaped like a Log line in `## Decision` changes the decision,
    so only lines inside `## Log` count (PR-026)."""
    diff = _diff(f"@@ -10,0 +11 @@\n+{_REDRAWN}\n")

    assert not arch.redraw_only(diff, _text(decision_tail=f"{_REDRAWN}\n"))


def test_an_added_line_that_isnt_a_redrawn_line_is_not_a_redraw() -> None:
    """A hand-written `accepted` line beside the `redrawn` line claims a
    second agreement, which the gates have to see."""
    accepted = _REDRAWN.replace("redrawn    ", "accepted   ")
    diff = _diff(f"@@ -14,0 +15,2 @@\n+{_REDRAWN}\n+{accepted}\n")

    assert not arch.redraw_only(diff, _text(log_tail=f"{_REDRAWN}\n{accepted}\n"))


def test_a_removed_line_is_not_a_redraw() -> None:
    """A redraw only appends. A removed line is an edit to the record."""
    diff = _diff(f"@@ -10 +9,0 @@\n-x\n@@ -14,0 +14 @@\n+{_REDRAWN}\n")

    assert not arch.redraw_only(diff, _text(log_tail=f"{_REDRAWN}\n").replace("\nx\n", "\n", 1))


def test_a_log_whose_last_line_had_no_newline_still_reads_as_a_redraw() -> None:
    """`_append_log` adds the missing newline before it appends, so git shows
    the old last line removed and re-added. That re-added line doesn't match
    `REDRAWN_LINE`, and refusing it would hold the branch for a write wfctl
    made itself."""
    last = "- 2026-11-20  accepted    — x · drawing drawings/a-data-flow.svg sha256:000000000000"
    diff = _diff(
        f"@@ -14 +14,2 @@\n-{last}\n\\ No newline at end of file\n+{last}\n+{_REDRAWN}\n"
    )

    assert arch.redraw_only(diff, _text(log_tail=f"{_REDRAWN}\n"))


def test_a_line_append_log_writes_matches_redrawn_line() -> None:
    """The writer and the reader live in one module so they spell the format
    once. This test keeps them in step if either changes (PR-027)."""
    lines = _text().splitlines(keepends=True)

    entry = _records._append_log(
        lines, "2026-11-21", "redrawn", "layout fix · drawing x sha256:3f9a0c1b2d4e"
    )

    assert _records.REDRAWN_LINE.fullmatch(entry)
    assert "".join(lines).endswith(entry + "\n")


@pytest.mark.parametrize("eol", ["\n", "\r\n"])
def test_a_redrawn_line_matches_with_either_line_ending(eol: str) -> None:
    """Git keeps a CRLF record's carriage returns in the diff, and a pattern
    anchored before them would read every CRLF redraw as a change."""
    assert _records.REDRAWN_LINE.fullmatch(_REDRAWN + eol.rstrip("\n"))
