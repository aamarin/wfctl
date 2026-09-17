"""Tests for `_arch._section_bounds`, the scanner `_log_bounds` and `_drawing`
share (research R-003).

`_log_bounds` already had its own coverage through `test_arch_records.py`'s
supersession and acceptance tests; what is new here is the generalised form
itself, and the second heading it now has to serve without the two callers
disagreeing about what a fence is.
"""
from __future__ import annotations

import re

from wfctl import _arch


def test_finds_the_boundary_section() -> None:
    lines = "# X\n\n## Boundary\n\nsome text\n\n## Log\n\nmore\n".splitlines()

    bounds = _arch._section_bounds(lines, "## boundary")

    assert bounds is not None
    heading, end = bounds
    assert lines[heading].strip() == "## Boundary"
    assert lines[end].strip() == "## Log"


def test_stops_at_the_next_level_two_heading() -> None:
    lines = "## Boundary\n\na\n\n## Considered\n\nb\n".splitlines()

    heading, end = _arch._section_bounds(lines, "## boundary")

    assert lines[end].strip() == "## Considered"


def test_runs_to_end_of_file_when_no_heading_follows() -> None:
    lines = "## Boundary\n\na\nb\nc\n".splitlines()

    heading, end = _arch._section_bounds(lines, "## boundary")

    assert end == len(lines)


def test_no_such_heading_is_none() -> None:
    lines = "# X\n\n## Decision\n\ntext\n".splitlines()

    assert _arch._section_bounds(lines, "## boundary") is None


def test_a_heading_quoted_inside_a_fence_is_skipped() -> None:
    """The case `contracts/record-format.md` is itself an instance of: a record
    documenting the record format carries a fenced `## Boundary` example, and
    matching it would scan the example's interior as the real section."""
    lines = (
        "# Contract\n\n"
        "````markdown\n"
        "## Boundary\n\nexample content\n"
        "````\n\n"
        "## Log\n\nreal\n"
    ).splitlines()

    assert _arch._section_bounds(lines, "## boundary") is None


def test_a_fence_indented_inside_a_list_item_still_opens_and_headings_are_seen() -> None:
    """`_unfenced`'s own rule: four spaces or more is an indented code block,
    which opens nothing, so the heading scan here is unaffected by it either."""
    lines = (
        "- an item\n\n"
        "    ```\n"
        "    ## Boundary\n"
        "    ```\n\n"
        "## Boundary\n\nreal\n"
    ).splitlines()

    bounds = _arch._section_bounds(lines, "## boundary")

    assert bounds is not None
    heading, _ = bounds
    assert lines[heading].strip() == "## Boundary"


def test_log_bounds_is_now_a_call_to_section_bounds_and_keeps_its_own_trim() -> None:
    """`_log_bounds`'s insertion-index trim is its own need, not a property of
    `_section_bounds` — this is what proves the generalisation kept it."""
    lines = "## Log\n\n- an entry\n\n\n".splitlines()

    heading, insert_at = _arch._log_bounds(lines)

    assert lines[heading].strip() == "## Log"
    assert insert_at == 3  # trimmed past the two trailing blank lines


def test_kinds_match_the_shipped_template() -> None:
    """FR-010, following `tests/test_pipeline_sections.py`'s own pattern: loads
    the packaged template through `importlib.resources`, not the working
    tree's copy, so a divergence between the constant and what actually ships
    is what fails — not what the repo happens to hold locally. `Path` rather
    than a dotted import past `files("wfctl")`, because `architecture-decisions`
    is not a legal module segment."""
    from importlib.resources import files
    from pathlib import Path

    template_path = (
        Path(str(files("wfctl")))
        / "agents"
        / "skills"
        / "architecture-decisions"
        / "record-template.md"
    )
    template = template_path.read_text()

    declared = re.search(r"^diagram: <([^>]+)>", template, re.MULTILINE)
    assert declared is not None, "the template no longer offers a diagram kind"
    offered = {alt.strip() for alt in declared.group(1).split("|")}

    assert offered == set(_arch.DIAGRAM_KINDS), (
        f"template offers {sorted(offered)}, code permits "
        f"{sorted(_arch.DIAGRAM_KINDS)}"
    )
