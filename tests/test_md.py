"""Tests for wfctl._md — the one fence walker three modules share.

The closing rule is the whole reason this module exists, and before it existed
each caller had its own. `_shape` implemented CommonMark's, `_body` and `_arch`
matched a prefix; the difference only shows on a document that quotes a fenced
example, which is exactly what all three of them read. So these tests pin the
rule itself rather than any one caller's projection of it — a caller's own tests
cover shapes that reach it, and the shapes that did *not* reach it are the ones
that made three implementations disagree for a year without anyone noticing.
"""
from __future__ import annotations

from wfctl import _md


def _inside(text: str) -> list[str]:
    return [line.text for line in _md.walk(text) if line.inside]


def test_a_fence_closes_on_the_same_character_at_the_same_length() -> None:
    """The base case every other test here is a deviation from."""
    assert _inside("a\n```\nb\n```\nc\n") == ["b"]


def test_a_longer_run_closes_a_shorter_fence() -> None:
    """CommonMark closes on *at least* the opening length, not exactly it."""
    assert _inside("```\nb\n````\nc\n") == ["b"]


def test_a_shorter_run_does_not_close_a_longer_fence() -> None:
    """The asymmetry that lets a ````-fence quote a ```-block.

    Reversed, the inner marker closes the outer fence and everything after it is
    scanned as prose — which is how a reply quoting the response-shape rules
    reported every heading in the quotation as a violation of the rule it was
    quoting.
    """
    assert _inside("````\nb\n```\nc\n") == ["b", "```", "c"]


def test_the_other_fence_character_does_not_close() -> None:
    """`~~~` and ``` are separate fences, so one cannot terminate the other."""
    assert _inside("```\nb\n~~~\nc\n") == ["b", "~~~", "c"]


def test_a_closer_carrying_an_info_string_is_content() -> None:
    """An info string means this is an opening, and inside a block that is text.

    The rule `_body` and `_arch` did not have: both matched a prefix, so a
    document showing two fenced examples back to back had the second one's
    opening read as the first one's close.
    """
    assert _inside("````\nb\n```python\nc\n````\n") == ["b", "```python", "c"]


def test_three_spaces_open_a_fence_and_four_do_not() -> None:
    """Markdown's own limit: at four the line is an indented code block.

    `_arch` matched `stripped[:3]`, so a fence indented inside a list item
    opened one and the rest of the record read as an example.
    """
    assert _inside("   ```\nb\n   ```\n") == ["b"]
    assert _inside("    ```\nb\n    ```\n") == []


def test_an_unclosed_fence_carries_to_the_end() -> None:
    """What a truncated reply leaves, read as what it looks like."""
    assert _inside("a\n```\nb\nc\n") == ["b", "c"]


def test_a_delimiter_is_neither_inside_nor_prose() -> None:
    """Three states, because `_arch` prints a delimiter and the other two skip it."""
    walked = list(_md.walk("a\n```\nb\n```\n"))
    assert [(line.text, line.inside, line.fence) for line in walked] == [
        ("a", False, False),
        ("```", False, True),
        ("b", True, False),
        ("```", False, True),
    ]


def test_opened_names_the_line_the_block_started_on() -> None:
    """`_shape` puts this number in a finding, so it counts from 1 like an editor."""
    assert [(line.number, line.opened) for line in _md.walk("a\n```\nb\nc\n```\n")
            if line.inside] == [(3, 2), (4, 2)]


def test_walk_lines_keeps_the_caller_s_index_when_endings_are_kept() -> None:
    """`splitlines(keepends=True)` is what `_arch.supersede` holds.

    Rejoining that list to re-split it doubles every newline, so `Line.number`
    stops matching the caller's own index — every line past the first fence
    shifts by the number of lines before it, and `supersede` appends the
    transition outside the `## Log` section it was aiming at.
    """
    lines = "## Log\n```\nx\n```\ntail\n".splitlines(keepends=True)
    assert [(line.number, line.inside) for line in _md.walk_lines(lines)] == [
        (1, False), (2, False), (3, True), (4, False), (5, False)
    ]


def test_a_carriage_return_still_closes() -> None:
    """CRLF reaches `walk_lines` intact, because the caller kept its endings."""
    lines = "```\r\nb\r\n```\r\n".splitlines(keepends=True)
    assert [line.text for line in _md.walk_lines(lines) if line.inside] == ["b\r\n"]
