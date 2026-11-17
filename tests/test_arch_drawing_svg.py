"""Tests for a record whose drawing is an SVG file in `drawings/` (#740).

A record links the SVG with a markdown image under `## Boundary`, or under
`### <kind>` when it declares several kinds (`record-drawing-can-be-svg`). The
SVG reader turns the file into the same summary a fence produces, so these
tests cover two things: what the reader takes from the link and the file, and
how a broken link or file reaches the author as one line naming the problem.

Problem wording is typed here rather than read from `_drawing`, because the
wording is the contract (`contracts/cli.md`). The author searches the record
for the link the line quotes, and a rewording that dropped it would leave them
with nothing to search for.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import write_record
from wfctl.arch import _records as _arch
from wfctl.arch._drawing import read_svg

_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100">'
    '<text x="10" y="20">writes the file</text></svg>\n'
)
_FENCE = "```mermaid\nflowchart LR\n  A --> B\n```\n"


def _svg(root: Path, name: str = "a-data-flow.svg", text: str = _SVG) -> Path:
    path = root / "drawings" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _record(root: Path, boundary: str, diagram: str = "data-flow", **kw: object) -> _arch.Record:
    path = write_record(root, "a", diagram=diagram, boundary=f"## Boundary\n\n{boundary}\n", **kw)  # type: ignore[arg-type]
    return _arch.parse_record(path)


# --- finding the link (T009) -------------------------------------------------


def test_a_valid_svg_in_drawings_reads_as_an_svg_drawing(tmp_path: Path) -> None:
    """The plain case every other test varies one thing from."""
    svg = _svg(tmp_path)

    drawing = read_svg("drawings/a-data-flow.svg", tmp_path)

    assert drawing.format == "svg"
    assert drawing.problem is None
    assert drawing.path == svg.resolve()
    assert drawing


def test_an_svg_link_under_the_boundary_is_the_records_drawing(tmp_path: Path) -> None:
    """The record links the SVG with a markdown image, which GitHub renders
    inline, and wfctl counts that link the same way it counts a fence."""
    _svg(tmp_path)
    record = _record(tmp_path, "![the flow](drawings/a-data-flow.svg)")

    assert _arch._drawing(record).format == "svg"
    assert "no drawing" not in " ".join(_arch.accept_problems(record))


def test_an_image_line_inside_a_fence_is_not_a_link(tmp_path: Path) -> None:
    """A fence shows text as written, so an image line inside one is an
    example of the syntax and never renders as a picture."""
    _svg(tmp_path)
    record = _record(tmp_path, "```text\n![x](drawings/a-data-flow.svg)\n```\n")

    assert _arch._drawing(record).format == "fence"


@pytest.mark.parametrize(
    "image",
    [
        "![x](drawings/a-data-flow.svg 'the flow')",
        "![x](drawings/a-data-flow.svg (the flow))",
        '![x](drawings/a-data-flow.svg "the flow")',
        "![x](drawings/a-data-flow.svg?raw=true)",
        "![x](drawings/a-data-flow.svg#top)",
        "![x](drawings/a%2Ddata-flow.svg)",
        "![x](<drawings/a-data-flow.svg>)",
        # The first backslash escapes the second, so the `!` is not escaped.
        r"\\![x](drawings/a-data-flow.svg)",
    ],
)
def test_an_image_link_github_renders_is_read_as_the_drawing(tmp_path: Path, image: str) -> None:
    """A link GitHub shows as the picture but wfctl couldn't read told the
    author "no drawing" beside a drawing they could see, the message this
    reader exists to replace. GitHub drops the query and fragment and decodes
    the path, and accepts all three title forms."""
    _svg(tmp_path)
    record = _record(tmp_path, image)

    drawing = _arch._drawing(record)

    assert drawing.format == "svg"
    assert drawing.problem is None


@pytest.mark.parametrize(
    "image",
    ["![x][flow]", "![x][Flow]", "![flow][]", "![flow]"],
)
def test_a_reference_style_image_resolves_to_its_definition(tmp_path: Path, image: str) -> None:
    """GitHub renders a reference-style image from a definition anywhere in
    the file. wfctl found no link and told the author "no drawing" beside a
    drawing they could see (#777). A label matches its definition ignoring
    case, as in CommonMark."""
    _svg(tmp_path)
    record = _record(
        tmp_path, f"{image}\n\n## Notes\n\n[flow]: drawings/a-data-flow.svg 'the flow'\n"
    )

    drawing = _arch._drawing(record)

    assert drawing.format == "svg"
    assert drawing.problem is None
    assert drawing.link == "drawings/a-data-flow.svg"


@pytest.mark.parametrize("image", ["![x][flow]", "![flow][]"])
def test_a_reference_with_no_definition_names_the_missing_label(
    tmp_path: Path, image: str
) -> None:
    """The author wrote a link, so "no drawing" would tell them to draw
    something they already linked. The problem names the label to define."""
    record = _record(tmp_path, image)

    problem = _arch._drawing(record).problem

    assert problem is not None
    assert problem.problem == "'## Boundary' links an image by reference [flow], which the record never defines"
    assert problem.fix == "add [flow]: drawings/<file>.svg to the record, or write the link inline."


@pytest.mark.parametrize("other", ["![x](drawings/a-data-flow.svg)", _FENCE])
def test_an_undefined_reference_beside_a_drawing_leaves_the_drawing_alone(
    tmp_path: Path, other: str
) -> None:
    """A broken badge or screenshot reference next to a working drawing
    refused the record, and the fix line asked for an SVG the record already
    had. The missing label matters only when nothing else is drawn."""
    _svg(tmp_path)
    record = _record(tmp_path, f"![ci][badge]\n\n{other}")

    drawing = _arch._drawing(record)

    assert drawing
    assert drawing.problem is None


def test_a_definition_that_continues_a_paragraph_defines_nothing(tmp_path: Path) -> None:
    """In CommonMark a definition can't interrupt a paragraph, so GitHub shows
    the line as text and no picture. Counted, it let a record pass with
    nothing drawn."""
    _svg(tmp_path)
    record = _record(tmp_path, "Some prose line\n[d]: drawings/a-data-flow.svg\n\n![x][d]")

    assert not _arch._drawing(record)


@pytest.mark.parametrize(
    "before",
    [
        "Some prose\n\n---",
        "Title\n-----",
        "Title\n=====",
        "## Notes",
        "<!-- a note -->",
        # An indented code block isn't a paragraph, so nothing continues.
        "Some prose\n\n    indented code",
    ],
)
def test_a_definition_after_a_block_that_ends_a_paragraph_resolves(
    tmp_path: Path, before: str
) -> None:
    """A thematic break, a setext underline, an ATX heading, and an HTML
    comment block each end a paragraph, so GitHub reads the next line as a
    definition. Read as paragraph text, they told the author to define a
    label the file already defines."""
    _svg(tmp_path)
    record = _record(tmp_path, f"![x][d]\n\n{before}\n[d]: drawings/a-data-flow.svg\n")

    assert _arch._drawing(record)


@pytest.mark.parametrize(
    "before", ["#tag", "`code`", r"\!", "The flow is below. <!-- TODO: redraw\nafter the split -->"]
)
def test_a_definition_after_paragraph_text_defines_nothing(tmp_path: Path, before: str) -> None:
    """`#tag` isn't a heading without a space after the `#`, and a line
    holding only a code span or an escape is paragraph text. A comment that
    opens partway through a line is inline, so the paragraph goes on past
    its last line. In each case GitHub shows the next line as text. Counted
    as a definition, it let a record pass with nothing drawn."""
    _svg(tmp_path)
    record = _record(tmp_path, f"![x][d]\n\n{before}\n[d]: drawings/a-data-flow.svg\n")

    assert not _arch._drawing(record)


@pytest.mark.parametrize(
    "definition",
    ["[d]:\n  drawings/a-data-flow.svg", '[d]: drawings/a-data-flow.svg\n  "the flow"'],
)
def test_a_definition_continued_on_the_next_line_resolves(
    tmp_path: Path, definition: str
) -> None:
    """CommonMark lets a definition's target, or its title, start on the
    line after the one before it, and GitHub renders the image."""
    _svg(tmp_path)
    record = _record(tmp_path, f"![x][d]\n\n## Notes\n\n{definition}\n")

    assert _arch._drawing(record)


def test_a_definition_spread_over_three_lines_leaves_the_next_one_readable(
    tmp_path: Path,
) -> None:
    """A label, a target on the next line, and a title on the line after
    that make one definition. Reading only two lines left the title as
    paragraph text, which hid the definition below it."""
    _svg(tmp_path)
    record = _record(
        tmp_path,
        "![x][e]\n\n## Notes\n\n[d]:\n  drawings/other.svg\n  'title'\n[e]: drawings/a-data-flow.svg\n",
    )

    assert _arch._drawing(record)


@pytest.mark.parametrize("under", ["---", "#", "<drawings/a-data-\nflow.svg>"])
def test_a_label_with_no_valid_target_under_it_defines_nothing(
    tmp_path: Path, under: str
) -> None:
    """`[d]:` above `---` is a setext heading and above `#` is followed by an
    empty heading, and an angle-bracket target can't span lines. Read as a
    definition, the reference resolved to something GitHub never shows and
    the author heard nothing about the missing definition."""
    record = _record(tmp_path, f"![x][d]\n\n## Notes\n\n[d]:\n{under}\n")

    problem = _arch._drawing(record).problem

    assert problem is not None
    assert "[d]" in problem.problem


def test_a_definition_after_a_comment_on_its_line_defines_nothing(tmp_path: Path) -> None:
    """A line that starts with a comment is an HTML block to its end, so
    GitHub shows the definition after the comment as raw text."""
    _svg(tmp_path)
    record = _record(
        tmp_path, "![x][d]\n\n## Notes\n\n<!-- note --> [d]: drawings/a-data-flow.svg\n"
    )

    assert not _arch._drawing(record)


def test_an_undefined_reference_beside_a_fenced_drawing_under_a_note_heading_keeps_the_fence(
    tmp_path: Path,
) -> None:
    """The SVG pass leaves out fences under a non-kind `###`, so it saw no
    fence and returned the missing label, and the full pass that finds the
    fence never ran. A broken badge refused a record that reads as drawn
    without it."""
    record = _record(tmp_path, f"![ci][badge]\n\nIntro.\n\n### Overview\n\n{_FENCE}")

    drawing = _arch._drawing(record)

    assert drawing.format == "fence"
    assert drawing.problem is None


def test_a_definition_target_can_hold_parentheses(tmp_path: Path) -> None:
    """A definition's target ends at whitespace, not at `)`, so a file name
    with parentheses resolves instead of reading as undefined."""
    _svg(tmp_path, "a(1).svg")
    record = _record(tmp_path, "![x][d]\n\n## Notes\n\n[d]: drawings/a(1).svg\n")

    drawing = _arch._drawing(record)

    assert drawing
    assert drawing.link == "drawings/a(1).svg"


def test_an_image_with_an_empty_label_is_not_a_reference(tmp_path: Path) -> None:
    """CommonMark gives `![][]` no label to look up, so GitHub shows it as
    text. A problem line asking the author to define `[]` would have no fix."""
    record = _record(tmp_path, "![][]")

    assert _arch._drawing(record).format == "none"


@pytest.mark.parametrize(
    "hidden",
    ["`[flow]: drawings/a-data-flow.svg`", "```text\n[flow]: drawings/a-data-flow.svg\n```"],
)
def test_a_definition_github_does_not_render_resolves_nothing(tmp_path: Path, hidden: str) -> None:
    """A definition inside a code span or a fence is text on GitHub, so the
    image it would resolve shows nothing."""
    _svg(tmp_path)
    record = _record(tmp_path, f"![flow]\n\n## Notes\n\n{hidden}\n")

    assert _arch._drawing(record).format == "none"


def test_a_fenced_legend_under_key_does_not_refuse_an_svg_drawing(tmp_path: Path) -> None:
    """The record template allows a `### Key` with a fenced legend under
    `## Boundary`. Read as part of the drawing, that legend made an SVG record
    "both an SVG and a fenced block", which the spec refuses only for a second
    drawing of the boundary."""
    _svg(tmp_path)
    record = _record(
        tmp_path,
        "![the flow](drawings/a-data-flow.svg)\n\n### Key\n\n```text\n──► writes\n```\n",
    )

    assert _arch._drawing(record).format == "svg"
    assert _arch._drawing(record).problem is None


def test_a_second_svg_below_key_is_still_two_drawings(tmp_path: Path) -> None:
    """Skipping the legend's fence must not skip the rest of the section: a
    second SVG under `### Key` would otherwise ship with its labels unchecked."""
    _svg(tmp_path)
    _svg(tmp_path, "b.svg")
    record = _record(
        tmp_path,
        "![a](drawings/a-data-flow.svg)\n\n### Key\n\n![b](drawings/b.svg)\n",
    )

    problem = _arch._drawing(record).problem

    assert problem is not None
    assert problem.problem == "'## Boundary' links two SVG drawings"


@pytest.mark.parametrize(
    "hidden",
    [
        "<!-- ![x](drawings/a-data-flow.svg) -->",
        "<!--\n![x](drawings/a-data-flow.svg)\n-->",
        # A line that starts with a comment is raw HTML to its end.
        "<!-- note --> ![x](drawings/a-data-flow.svg)",
        r"\![x](drawings/a-data-flow.svg)",
        r"\\\![x](drawings/a-data-flow.svg)",
        "`![x](drawings/a-data-flow.svg)`",
    ],
)
def test_an_image_github_does_not_render_is_not_a_drawing(tmp_path: Path, hidden: str) -> None:
    """A commented-out, escaped, or code-span image shows no picture on
    GitHub. Counted as the drawing, it let a record pass with nothing drawn,
    and beside a real fence it made a false "both" refusal."""
    _svg(tmp_path)

    alone = _arch._drawing(_record(tmp_path, hidden))
    with_fence = _arch._drawing(_record(tmp_path, f"{hidden}\n\n{_FENCE}"))

    assert alone.format == "none"
    assert with_fence.format == "fence"


def test_an_svg_beside_a_fence_above_any_key_is_still_refused(tmp_path: Path) -> None:
    """Two drawings of the same boundary would pass with one unchecked."""
    _svg(tmp_path)
    record = _record(tmp_path, f"![the flow](drawings/a-data-flow.svg)\n\n{_FENCE}")

    problem = _arch._drawing(record).problem

    assert problem is not None
    assert problem.problem == "'## Boundary' has both an SVG and a fenced block"


@pytest.mark.parametrize(
    "target",
    [
        "https://example.com/a.svg",
        # Protocol-relative, so another host, the same as `https://` (#777).
        "//example.com/a.svg",
        "data:image/svg+xml,<svg/>",
        "drawings/a.png",
    ],
)
def test_an_image_that_is_not_a_local_svg_is_not_a_drawing(tmp_path: Path, target: str) -> None:
    """wfctl can read only a file in the repository, and only an SVG has
    labels it can check, so any other image leaves the heading undrawn."""
    record = _record(tmp_path, f"![x]({target})")

    assert not _arch._drawing(record)
    assert _arch._drawing(record).format == "none"


# --- what goes wrong with a link or a file (T010) ----------------------------


def _problem(drawing: object) -> tuple[str, str]:
    problem = drawing.problem  # type: ignore[attr-defined]
    assert problem is not None
    return problem.problem, problem.fix


def test_a_missing_file_names_the_link_as_written(tmp_path: Path) -> None:
    drawing = read_svg("drawings/x.svg", tmp_path)

    assert _problem(drawing) == (
        "drawing links drawings/x.svg, which doesn't exist",
        "create it, or correct the link.",
    )
    assert not drawing


@pytest.mark.parametrize("link", ["../x.svg", "x.svg"])
def test_a_file_outside_drawings_is_refused_even_though_it_exists(
    tmp_path: Path, link: str
) -> None:
    """An SVG anywhere else under the arch root would count as a changed
    record, so wfctl refuses it rather than reading it. Ignoring it instead
    would tell the author to draw something that is already there."""
    arch = tmp_path / "arch"
    arch.mkdir()
    (tmp_path / "x.svg").write_text(_SVG)
    (arch / "x.svg").write_text(_SVG)

    assert _problem(read_svg(link, arch)) == (
        f"drawing links {link}, which is outside drawings/",
        "move it into the drawings/ folder beside the records, and update the link.",
    )


def test_a_leading_slash_gets_its_own_problem(tmp_path: Path) -> None:
    """GitHub reads `/drawings/x.svg` from the repo root, while a join to the
    record's folder reads it from the filesystem root. Telling that author to
    move a file already in `drawings/` would send them to the wrong place."""
    _svg(tmp_path, "x.svg")

    assert _problem(read_svg("/drawings/x.svg", tmp_path)) == (
        "drawing links /drawings/x.svg, which isn't relative to the record",
        "write it relative to the record, as drawings/<file>.svg.",
    )


def test_a_link_the_filesystem_cannot_resolve_is_a_problem_not_a_crash(
    tmp_path: Path,
) -> None:
    """Resolving a path with a NUL byte raises `ValueError`. Uncaught, one
    record carrying such a link took down `doctor`, `arch check`, and the
    guard's record check with a traceback, where every other bad link is a
    problem line on that record alone."""
    (tmp_path / "drawings").mkdir()

    problem, fix = _problem(read_svg("drawings/a\x00.svg", tmp_path))

    # The reason after the colon is Python's own, and its wording changes by version.
    assert problem.startswith("drawing links drawings/a\x00.svg, which can't be resolved: ")
    assert fix == "correct the link."


def test_a_symlink_loop_in_drawings_is_a_problem_not_a_crash(tmp_path: Path) -> None:
    """3.11 raises `RuntimeError` resolving a loop and 3.13 doesn't, so the
    problem line differs by version. What both must do is report the record
    rather than raise."""
    drawings = tmp_path / "drawings"
    drawings.mkdir()
    (drawings / "a.svg").symlink_to(drawings / "b.svg")
    (drawings / "b.svg").symlink_to(drawings / "a.svg")

    problem, _ = _problem(read_svg("drawings/a.svg", tmp_path))

    assert "drawings/a.svg" in problem


def test_a_drawings_folder_that_is_itself_a_symlink_is_refused(tmp_path: Path) -> None:
    """Resolving both sides of the containment check follows a symlinked
    `drawings/` to wherever it points, so files outside the arch root read as
    inside it. The folder is refused instead, whatever it points at."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "x.svg").write_text(_SVG)
    arch = tmp_path / "arch"
    arch.mkdir()
    (arch / "drawings").symlink_to(elsewhere)

    assert _problem(read_svg("drawings/x.svg", arch)) == (
        "drawing links drawings/x.svg, but drawings/ is a symlink",
        "make drawings/ a folder beside the records, not a link to one.",
    )


def test_a_file_the_reader_cannot_reach_is_a_problem_not_a_crash(tmp_path: Path) -> None:
    """On 3.11, `Path.exists` raises `PermissionError` under a folder with no
    permissions, where 3.12 returns False, so a locked folder in `drawings/`
    crashed every reader of the record set."""
    locked = tmp_path / "drawings" / "locked"
    locked.mkdir(parents=True)
    (locked / "x.svg").write_text(_SVG)
    locked.chmod(0)
    try:
        problem, _ = _problem(read_svg("drawings/locked/x.svg", tmp_path))
    finally:
        locked.chmod(0o755)

    assert problem == "drawing drawings/locked/x.svg can't be read: Permission denied"


@pytest.mark.parametrize("root", ["<not-svg><text>approved</text></not-svg>", "<html/>"])
def test_well_formed_xml_that_is_not_an_svg_is_refused(tmp_path: Path, root: str) -> None:
    """Parsing only proves the file is XML. Without a check on the root, any
    XML file named `.svg` counted as the drawing and had its text checked as
    labels."""
    _svg(tmp_path, "x.svg", root)

    assert _problem(read_svg("drawings/x.svg", tmp_path)) == (
        "drawing drawings/x.svg isn't an SVG: its root element is not <svg>",
        "fix the file so it opens as XML.",
    )


def test_a_symlink_in_drawings_pointing_elsewhere_is_outside(tmp_path: Path) -> None:
    """The check runs after resolving, so a link that only looks like it is
    in `drawings/` doesn't get its target past the design gate."""
    (tmp_path / "elsewhere.svg").write_text(_SVG)
    (tmp_path / "drawings").mkdir()
    (tmp_path / "drawings" / "x.svg").symlink_to(tmp_path / "elsewhere.svg")

    problem, _ = _problem(read_svg("drawings/x.svg", tmp_path))

    assert problem == "drawing links drawings/x.svg, which is outside drawings/"


def test_a_doctype_is_refused(tmp_path: Path) -> None:
    """Entity expansion needs a DOCTYPE, and a hand-drawn SVG needs none, so
    refusing it removes the question whatever expat the machine links."""
    _svg(tmp_path, "x.svg", '<!DOCTYPE svg [<!ENTITY a "b">]>\n' + _SVG)

    assert _problem(read_svg("drawings/x.svg", tmp_path)) == (
        "drawing drawings/x.svg declares a DOCTYPE",
        "remove it, since a drawing needs none.",
    )


def test_a_utf16_file_carrying_a_doctype_is_refused(tmp_path: Path) -> None:
    """A check on the raw bytes would miss `<!DOCTYPE` spread over two bytes
    per character, and expat would still parse it."""
    path = tmp_path / "drawings" / "x.svg"
    path.parent.mkdir()
    path.write_bytes(('<!DOCTYPE svg [<!ENTITY a "b">]>\n' + _SVG).encode("utf-16"))

    problem, fix = _problem(read_svg("drawings/x.svg", tmp_path))

    assert problem.startswith("drawing drawings/x.svg can't be read: ")
    assert fix == "fix the file so it opens as XML."


def test_a_utf8_file_declaring_utf16_is_checked_as_the_text_it_holds(tmp_path: Path) -> None:
    """The parser reads the same decoded text the DOCTYPE check read, so the
    encoding an XML declaration names can't make the two see different
    characters."""
    _svg(
        tmp_path,
        "x.svg",
        '<?xml version="1.0" encoding="UTF-16"?>\n<!DOCTYPE svg [<!ENTITY a "b">]>\n' + _SVG,
    )

    problem, _ = _problem(read_svg("drawings/x.svg", tmp_path))

    assert problem == "drawing drawings/x.svg declares a DOCTYPE"


def test_invalid_xml_carries_the_parsers_reason(tmp_path: Path) -> None:
    _svg(tmp_path, "x.svg", "<svg><text>a</svg>")

    assert _problem(read_svg("drawings/x.svg", tmp_path)) == (
        "drawing drawings/x.svg can't be read: mismatched tag: line 1, column 14",
        "fix the file so it opens as XML.",
    )


def test_a_directory_named_like_an_svg_cannot_be_read(tmp_path: Path) -> None:
    """`wfctl doctor` runs over repositories the user didn't write, so a read
    failure comes back as a problem line and never as a traceback."""
    (tmp_path / "drawings" / "x.svg").mkdir(parents=True)

    problem, _ = _problem(read_svg("drawings/x.svg", tmp_path))

    assert problem.startswith("drawing drawings/x.svg can't be read: ")


def test_a_heading_with_both_an_svg_and_a_fence_is_a_problem(tmp_path: Path) -> None:
    """A record carrying two drawings would pass with one of them unchecked."""
    _svg(tmp_path)
    record = _record(tmp_path, f"![x](drawings/a-data-flow.svg)\n\n{_FENCE}")

    drawing = _arch._drawing(record)

    assert drawing.format == "svg"
    assert _problem(drawing) == (
        "'## Boundary' has both an SVG and a fenced block",
        "keep one.",
    )


def test_a_heading_with_two_svg_links_is_a_problem(tmp_path: Path) -> None:
    _svg(tmp_path)
    _svg(tmp_path, "b.svg")
    record = _record(tmp_path, "![x](drawings/a-data-flow.svg)\n\n![y](drawings/b.svg)")

    assert _problem(_arch._drawing(record)) == (
        "'## Boundary' links two SVG drawings",
        "keep one, or give each its own '### <kind>' heading.",
    )


def test_a_kind_heading_names_itself_as_written_in_its_problem(tmp_path: Path) -> None:
    _svg(tmp_path)
    record = _record(
        tmp_path,
        f"### Data-flow\n\n![x](drawings/a-data-flow.svg)\n\n{_FENCE}\n### state\n\n{_FENCE}",
        diagram="[data-flow, state]",
    )

    problem, _ = _problem(_arch._drawings(record)["data-flow"])

    assert problem == "'### Data-flow' has both an SVG and a fenced block"


# --- what `accept` prints (T011) ----------------------------------------------


def test_a_one_kind_problem_replaces_the_no_drawing_line(tmp_path: Path) -> None:
    """The record never gets both lines: `no drawing` would tell the author to
    draw something that is already linked."""
    record = _record(tmp_path, "![x](drawings/a-data-flow.svg)")

    assert _arch.accept_problems(record) == [
        "drawing links drawings/a-data-flow.svg, which doesn't exist: "
        "create it, or correct the link.",
    ]


def test_a_one_kind_problem_sits_where_no_drawing_would_in_reading_order(
    tmp_path: Path,
) -> None:
    record = _record(tmp_path, "![x](drawings/a-data-flow.svg)", diagram="", log=False)

    problems = _arch.accept_problems(record)

    assert problems[0] == "no '## Log' section to append to"
    assert problems[1].startswith("drawing links drawings/a-data-flow.svg, which doesn't exist: ")
    assert problems[2].startswith("no declared kind: ")
    assert len(problems) == 3


def test_a_multi_kind_problem_replaces_the_missing_kind_refusal(tmp_path: Path) -> None:
    record = _record(
        tmp_path,
        f"### data-flow\n\n![x](drawings/a-data-flow.svg)\n\n### state\n\n{_FENCE}",
        diagram="[data-flow, state]",
    )

    assert _arch.accept_problems(record) == [
        "### data-flow: drawing links drawings/a-data-flow.svg, which doesn't exist",
    ]
    assert _arch.kind_refusals(record) == [
        _arch.Refusal(
            "### data-flow: drawing links drawings/a-data-flow.svg, which doesn't exist",
            "create it, or correct the link.",
        )
    ]


def test_a_broken_sequence_svg_gets_one_line_and_not_three(tmp_path: Path) -> None:
    """A drawing with a problem doesn't count as drawn, so the failing-step
    check doesn't add a line about a drawing wfctl couldn't read."""
    record = _record(tmp_path, "![x](drawings/a-sequence.svg)", diagram="sequence")

    assert len(_arch.accept_problems(record)) == 1


# --- what `doctor` warns while the record is proposed (T012) ------------------


@pytest.mark.parametrize(
    ("boundary", "files", "expected"),
    [
        ("![x](drawings/a-data-flow.svg)", {}, "drawing links drawings/a-data-flow.svg, which doesn't exist"),
        ("![x](../a.svg)", {"../a.svg": _SVG}, "drawing links ../a.svg, which is outside drawings/"),
        ("![x](/drawings/a.svg)", {}, "drawing links /drawings/a.svg, which isn't relative to the record"),
        (
            "![x](drawings/a-data-flow.svg)",
            {"drawings/a-data-flow.svg": "<!DOCTYPE svg>\n" + _SVG},
            "drawing drawings/a-data-flow.svg declares a DOCTYPE",
        ),
        (
            "![x](drawings/a-data-flow.svg)",
            {"drawings/a-data-flow.svg": "<svg>"},
            "drawing drawings/a-data-flow.svg can't be read: no element found: line 1, column 5",
        ),
        (
            f"![x](drawings/a-data-flow.svg)\n\n{_FENCE}",
            {"drawings/a-data-flow.svg": _SVG},
            "'## Boundary' has both an SVG and a fenced block",
        ),
        (
            "![x](drawings/a-data-flow.svg)\n\n![y](drawings/a-data-flow.svg)",
            {"drawings/a-data-flow.svg": _SVG},
            "'## Boundary' links two SVG drawings",
        ),
    ],
)
def test_doctor_warns_with_the_problem_for_a_one_kind_proposed_record(
    tmp_path: Path, boundary: str, files: dict[str, str], expected: str
) -> None:
    """Before SVG, a one-kind record had no drawing problem doctor could name,
    so the author would first hear of a broken link from `accept`."""
    arch = tmp_path / "arch"
    for name, text in files.items():
        path = arch / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    record = _record(arch, boundary)

    warnings = [f.message for f in _arch.validate([record]) if f.level == "warning"]

    assert warnings == [expected]


# --- what wfctl reads out of an SVG (T020, T021) ------------------------------


def _summary(tmp_path: Path, body: str, attrs: str = 'viewBox="0 0 400 100"') -> object:
    _svg(tmp_path, "x.svg", f'<svg xmlns="http://www.w3.org/2000/svg" {attrs}>{body}</svg>')
    return read_svg("drawings/x.svg", tmp_path)


def test_a_label_is_each_text_with_its_tspans_joined_by_spaces(tmp_path: Path) -> None:
    """A long label is wrapped with `<tspan>` lines, and the label check has
    to read it as the one phrase its author wrote."""
    drawing = _summary(
        tmp_path,
        '<text x="10" y="20">first</text>'
        '<text x="10" y="40"><tspan x="10">wraps over</tspan><tspan x="10" dy="14">two lines</tspan></text>',
    )

    assert drawing.labels == ("first", "wraps over two lines")  # type: ignore[attr-defined]


def test_a_drawing_without_the_svg_namespace_reads_the_same(tmp_path: Path) -> None:
    """GitHub needs `xmlns` to render, but a draft may leave it out, and what
    the drawing shows doesn't depend on it."""
    _svg(tmp_path, "x.svg", '<svg viewBox="0 0 400 100"><text x="10" y="20">a label</text></svg>')

    assert read_svg("drawings/x.svg", tmp_path).labels == ("a label",)


def test_the_failing_step_is_any_element_carrying_the_class(tmp_path: Path) -> None:
    """The author marks the step, so wfctl never guesses it from a stroke
    color, and the class can sit beside others on the same element."""
    marked = _summary(tmp_path, '<line class="arrow failing-step"/><text x="1" y="1">a</text>')
    plain = _summary(tmp_path, '<line class="arrow refused-edge"/><text x="1" y="1">a</text>')

    assert marked.shows_failure  # type: ignore[attr-defined]
    assert not plain.shows_failure  # type: ignore[attr-defined]
    assert plain.failure_fix == 'add class="failing-step" to the element that fails'  # type: ignore[attr-defined]


_SEQUENCE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100">'
    '<text x="10" y="20">agent asks</text><line class="arrow"/></svg>\n'
)
_SEQUENCE_FENCE = "```mermaid\nsequenceDiagram\n  A->>B: agent asks\n```\n"


@pytest.mark.parametrize("form", ["svg", "fence"])
def test_the_failing_step_check_reads_either_format_through_the_summary(
    tmp_path: Path, form: str
) -> None:
    """One check, two formats, and the line names the fix in the format the
    author drew, so a fence author is never told to add a CSS class."""
    _svg(tmp_path, "a-sequence.svg", _SEQUENCE_SVG)
    boundary = "![x](drawings/a-sequence.svg)" if form == "svg" else _SEQUENCE_FENCE
    record = _record(tmp_path, f"{boundary}\n\n## Decision\n\nThe agent asks.", diagram="sequence")
    fix = (
        'add class="failing-step" to the element that fails'
        if form == "svg"
        else "add an alt, opt, break or critical block, or a lost message (-x)"
    )

    assert _arch.accept_problems(record) == [f"a sequence drawing with no step that fails: {fix}"]
    assert [f.message for f in _arch.validate([record])] == [
        f"declares a sequence diagram with no step that fails — {fix}"
    ]


@pytest.mark.parametrize("form", ["svg", "fence"])
def test_the_label_check_reads_either_format_through_the_summary(
    tmp_path: Path, form: str
) -> None:
    _svg(tmp_path, "a-data-flow.svg", _SVG.replace("writes the file", "invented shibboleth"))
    boundary = (
        "![x](drawings/a-data-flow.svg)"
        if form == "svg"
        else '```mermaid\nflowchart LR\n  A["invented shibboleth"]\n```\n'
    )
    record = _record(tmp_path, boundary)

    assert [f.message for f in _arch.validate([record])] == [
        "drawing label 'invented shibboleth' appears nowhere else in the record"
    ]


def test_failing_step_on_another_kind_changes_nothing(tmp_path: Path) -> None:
    _svg(tmp_path, "a-data-flow.svg", _SVG.replace("<text", '<line class="failing-step"/><text'))
    record = _record(tmp_path, "![x](drawings/a-data-flow.svg)\n\n## Decision\n\nIt writes the file.")

    assert _arch.accept_problems(record) == []
    assert _arch.validate([record]) == []


# --- a label running past the edge (T025, T026) -------------------------------
#
# Every case below uses a 13px label, whose 12 characters estimate to 93.6
# units wide, so a reader can check each boundary by hand.

_TWELVE = "file missing"


@pytest.mark.parametrize(
    ("anchor", "x", "past"),
    [
        ("start", 300, False),
        ("start", 310, True),
        ("middle", 350, False),
        ("middle", 360, True),
        ("middle", 40, True),
        ("end", 400, False),
        ("end", 90, True),
    ],
)
def test_the_estimated_extent_follows_the_text_anchor(
    tmp_path: Path, anchor: str, x: int, past: bool
) -> None:
    drawing = _summary(
        tmp_path, f'<text x="{x}" y="20" font-size="13" text-anchor="{anchor}">{_TWELVE}</text>'
    )

    assert drawing.past_edge == ((_TWELVE,) if past else ())  # type: ignore[attr-defined]


def test_a_text_anchor_set_by_a_class_is_read_like_one_set_by_attribute(tmp_path: Path) -> None:
    """Font size was read from a class and the anchor wasn't, so a label
    centered by its class was measured from its left edge and warned, and the
    author couldn't clear it without moving the anchor into an attribute."""
    style = "<style>.c { text-anchor: middle; font-size: 13px }</style>"
    centered = _summary(tmp_path, f'{style}<text x="350" class="c" y="20">{_TWELVE}</text>')
    too_far = _summary(tmp_path, f'{style}<text x="360" class="c" y="20">{_TWELVE}</text>')

    assert centered.past_edge == ()  # type: ignore[attr-defined]
    assert too_far.past_edge == (_TWELVE,)  # type: ignore[attr-defined]


def test_a_label_wrapped_onto_tspan_lines_is_measured_line_by_line(tmp_path: Path) -> None:
    """Wrapping is how an author fixes a label past the edge. Measured as one
    joined line, a wrapped label that fits was still flagged, and nothing the
    author could do short of unwrapping it cleared the warning. The label
    check still reads the joined text."""
    wrapped = (
        f'<text x="300" y="20" font-size="13"><tspan x="300">{_TWELVE}</tspan>'
        f'<tspan x="300" dy="16">{_TWELVE}</tspan></text>'
    )
    one_line_too_long = (
        f'<text x="300" y="20" font-size="13"><tspan x="300">{_TWELVE}</tspan>'
        f'<tspan x="310" dy="16">{_TWELVE}</tspan></text>'
    )

    assert _summary(tmp_path, wrapped).past_edge == ()  # type: ignore[attr-defined]
    assert _summary(tmp_path, wrapped).labels == (f"{_TWELVE} {_TWELVE}",)  # type: ignore[attr-defined]
    assert _summary(tmp_path, one_line_too_long).past_edge == (  # type: ignore[attr-defined]
        f"{_TWELVE} {_TWELVE}",
    )


def test_the_recreated_file_missi_label_is_past_the_edge(tmp_path: Path) -> None:
    """The label from commit `0d7e56d`, which rendered as "file missi" with no
    error from anything. Its root sets 13px, and its class sets nothing."""
    drawing = _summary(
        tmp_path,
        '<style>.label { fill: #1f2328; }</style>'
        f'<text x="708" y="180" class="label">{_TWELVE}</text>',
        'viewBox="0 0 760 330" font-size="13"',
    )
    corrected = _summary(
        tmp_path,
        f'<text x="692" y="210" text-anchor="end" class="label">{_TWELVE}</text>',
        'viewBox="0 0 760 330" font-size="13"',
    )

    assert drawing.past_edge == (_TWELVE,)  # type: ignore[attr-defined]
    assert corrected.past_edge == ()  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("attrs", "past"),
    [
        ('viewBox="350 0 300 100"', True),
        ('viewBox="0 0 400 100" width="200"', False),
        ('width="350px"', True),
        ('width="400"', False),
        ('width="50%"', False),
        ("", False),
    ],
)
def test_the_edge_comes_from_the_viewbox_then_the_width(
    tmp_path: Path, attrs: str, past: bool
) -> None:
    """`viewBox` is the coordinate system the `x` values are written in. A
    percentage width, or neither attribute, has no edge to measure against,
    so it gets no warning rather than a guess."""
    drawing = _summary(tmp_path, f'<text x="300" y="20" font-size="13">{_TWELVE}</text>', attrs)

    assert drawing.past_edge == ((_TWELVE,) if past else ())  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("style", "text_attrs", "root_attrs", "past"),
    [
        # A class rule wins over the same element's attribute, as in CSS.
        (".big { font-size: 40px; }", 'class="big" font-size="13"', "", True),
        # An inline style wins over a class rule on the same element.
        (".big { font-size: 40px; }", 'class="big" style="font-size: 13px"', "", False),
        # A class rule wins over the root's attribute.
        (".big { font-size: 40px; }", 'class="big"', 'font-size="13"', True),
        # One rule naming two classes counts for each of them.
        (".name, .big { font-size: 40px; }", 'class="big"', 'font-size="13"', True),
        # A rule inside `@media` sets one theme only and is skipped.
        ("@media (prefers-color-scheme: dark) { .big { font-size: 40px; } }", 'class="big"', 'font-size="13"', False),
        # A selector that isn't one class isn't read.
        ("text.big { font-size: 40px; }", 'class="big"', 'font-size="13"', False),
        # With nothing set, the SVG default of 16 applies: 12 × 0.6 × 16 = 115.2.
        ("", "", "", True),
    ],
)
def test_the_font_size_lookup_order(
    tmp_path: Path, style: str, text_attrs: str, root_attrs: str, past: bool
) -> None:
    """The order matches the browser's. On each element, an inline style wins,
    then a class rule, then the attribute. Research R-005 for #740 put the
    attribute before the class, so wfctl measured some labels at a size the
    browser never renders them at (#776)."""
    drawing = _summary(
        tmp_path,
        f'<style>{style}</style><text x="300" y="20" {text_attrs}>{_TWELVE}</text>',
        f'viewBox="0 0 400 100" {root_attrs}',
    )

    assert drawing.past_edge == ((_TWELVE,) if past else ())  # type: ignore[attr-defined]


def test_an_ancestor_class_sets_the_size_when_nothing_closer_does(tmp_path: Path) -> None:
    drawing = _summary(
        tmp_path,
        f'<style>.big {{ font-size: 40px; }}</style><g class="big"><text x="300" y="20">{_TWELVE}</text></g>',
        'viewBox="0 0 400 100"',
    )

    assert drawing.past_edge == (_TWELVE,)  # type: ignore[attr-defined]


def test_the_nearest_element_that_sets_the_size_wins_over_the_root(tmp_path: Path) -> None:
    """wfctl read the root's attribute before any ancestor's class. A label in
    a group whose class sets 40px was measured at the root's 13px, so it ran
    past the edge in the browser and wfctl reported nothing (#776)."""
    drawing = _summary(
        tmp_path,
        f'<style>.big {{ font-size: 40px; }}</style><g class="big"><text x="300" y="20">{_TWELVE}</text></g>',
        'viewBox="0 0 400 100" font-size="13"',
    )

    assert drawing.past_edge == (_TWELVE,)  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "body",
    [
        f'<text x="390" y="20" style="text-anchor:end">{_TWELVE}</text>',
        f'<text x="300" y="20" style="font-size:8px">{_TWELVE}</text>',
        f'<g style="fill: red; font-size: 8px"><text x="300" y="20">{_TWELVE}</text></g>',
    ],
)
def test_an_inline_style_sets_the_size_and_anchor_it_renders_with(
    tmp_path: Path, body: str
) -> None:
    """wfctl ignored inline styles. A label that fits at the size or anchor
    its style sets was measured at the default and flagged, and the author
    couldn't clear the warning without restyling the drawing (#776)."""
    assert _summary(tmp_path, body).past_edge == ()  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("style", "classes", "past"),
    [
        (".small { font-size: 8px; } .big { font-size: 40px; }", "small big", True),
        (".small { font-size: 8px; } .big { font-size: 40px; }", "big small", True),
        (".big { font-size: 40px; } .small { font-size: 8px; }", "small big", False),
    ],
)
def test_two_class_rules_resolve_by_stylesheet_order(
    tmp_path: Path, style: str, classes: str, past: bool
) -> None:
    """When two class rules set the size, the browser uses the one later in
    the stylesheet, whatever order the `class` attribute lists them in. wfctl
    took the first class listed and missed a 40px label."""
    drawing = _summary(
        tmp_path, f'<style>{style}</style><text x="300" y="20" class="{classes}">{_TWELVE}</text>'
    )

    assert drawing.past_edge == ((_TWELVE,) if past else ())  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("body", "past"),
    [
        # An important class rule beats a normal inline style on the same element.
        (f'<style>.big {{ font-size: 40px !important; }}</style><text x="300" y="20" class="big" style="font-size: 8px">{_TWELVE}</text>', True),
        # An important inline style beats an important class rule.
        (f'<style>.big {{ font-size: 40px !important; }}</style><text x="300" y="20" class="big" style="font-size: 8px !important">{_TWELVE}</text>', False),
        # Importance doesn't cross elements: the label's own value still wins.
        (f'<g style="font-size: 8px !important"><text x="300" y="20" style="font-size: 40px">{_TWELVE}</text></g>', True),
        # Of two rules for one class, an earlier important one beats a later normal one.
        (f'<style>.big {{ font-size: 40px !important; }} .big {{ font-size: 8px; }}</style><text x="300" y="20" class="big">{_TWELVE}</text>', True),
        (f'<style>.end {{ text-anchor: end !important; }} .end {{ text-anchor: start; }}</style><text x="390" y="20" font-size="8" class="end">{_TWELVE}</text>', False),
        # `inherit` takes the parent's value, not the same element's attribute.
        (f'<g font-size="8"><text x="300" y="20" font-size="40" style="font-size: inherit">{_TWELVE}</text></g>', False),
        # In one block, an important declaration beats a later normal one.
        (f'<text x="300" y="20" style="font-size: 8px !important; font-size: 40px">{_TWELVE}</text>', False),
    ],
)
def test_an_important_declaration_wins_on_its_own_element(
    tmp_path: Path, body: str, past: bool
) -> None:
    """`!important` made the value unreadable, so wfctl fell through to the
    next source and measured a label at a size the browser never uses."""
    assert _summary(tmp_path, body).past_edge == ((_TWELVE,) if past else ())  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("body", "past"),
    [
        # 2em of a 10px group is 20px: 12 × 0.6 × 20 = 144, past the edge.
        (f'<g font-size="10"><text x="300" y="20" font-size="2em">{_TWELVE}</text></g>', True),
        (f'<g font-size="40"><text x="300" y="20" style="font-size: 0.2em">{_TWELVE}</text></g>', False),
        (f'<g font-size="40"><text x="300" y="20" font-size="20%">{_TWELVE}</text></g>', False),
        # Relative sizes compound: 0.5em of 2em of 8px is 8px.
        (f'<g font-size="8"><g font-size="2em"><text x="300" y="20" font-size="0.5em">{_TWELVE}</text></g></g>', False),
        # On the root, a relative size is relative to the default of 16.
        (f'<text x="300" y="20" font-size="0.5em">{_TWELVE}</text>', False),
    ],
)
def test_a_relative_font_size_is_measured_against_the_parent(
    tmp_path: Path, body: str, past: bool
) -> None:
    """An `em` or `%` size counted as unset, so wfctl measured the label at
    the parent's size. It missed a label that grows past the edge and
    flagged one that shrinks to fit."""
    assert _summary(tmp_path, body).past_edge == ((_TWELVE,) if past else ())  # type: ignore[attr-defined]


def test_deeply_nested_relative_sizes_are_measured_without_a_crash(tmp_path: Path) -> None:
    """Resolving each relative size by recursion raised `RecursionError`
    past about a thousand levels, and that stopped every reader of the
    record set, not only the edge warning."""
    depth = 2000
    body = '<g font-size="1em">' * depth + f'<text x="300" y="20" font-size="8">{_TWELVE}</text>' + "</g>" * depth
    relative = '<g font-size="1em">' * depth + f'<text x="300" y="20" font-size="0.5em">{_TWELVE}</text>' + "</g>" * depth

    assert _summary(tmp_path, body).past_edge == ()  # type: ignore[attr-defined]
    assert _summary(tmp_path, relative).past_edge == ()  # type: ignore[attr-defined]


def test_a_property_name_is_read_whatever_its_case(tmp_path: Path) -> None:
    """CSS property names ignore case, so `FONT-SIZE` sets the size."""
    drawing = _summary(tmp_path, f'<text x="300" y="20" style="FONT-SIZE: 8px">{_TWELVE}</text>')

    assert drawing.past_edge == ()  # type: ignore[attr-defined]


def test_a_custom_property_is_not_the_font_size(tmp_path: Path) -> None:
    """`--font-size` is a custom property and sets no size, so the label is
    measured at the default of 16 and runs past the edge."""
    drawing = _summary(tmp_path, f'<text x="300" y="20" style="--font-size: 8px">{_TWELVE}</text>')

    assert drawing.past_edge == (_TWELVE,)  # type: ignore[attr-defined]


def test_a_label_in_a_transformed_group_is_measured_as_written(tmp_path: Path) -> None:
    """The drawing style teaches absolute coordinates, so wfctl doesn't
    compose transforms. A label moved left by its group still reads as past
    the edge at its written `x`."""
    drawing = _summary(
        tmp_path,
        f'<g transform="translate(-200 0)"><text x="310" y="20" font-size="13">{_TWELVE}</text></g>',
    )

    assert drawing.past_edge == (_TWELVE,)  # type: ignore[attr-defined]


_WIDE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100">'
    f'<text x="380" y="20" font-size="13">{_TWELVE}</text></svg>\n'
)


def test_doctor_warns_about_a_label_past_the_edge_on_a_proposed_record(tmp_path: Path) -> None:
    _svg(tmp_path, "a-data-flow.svg", _WIDE)
    record = _record(tmp_path, "![x](drawings/a-data-flow.svg)\n\n## Decision\n\nThe file goes missing.")

    assert [f.message for f in _arch.validate([record])] == [
        "drawing label 'file missing' runs past the drawing's edge"
    ]


def test_an_accepted_record_gets_no_edge_warning(tmp_path: Path) -> None:
    """The user looked at the drawing when they accepted it, so a warning
    about how it renders would name a decision already made."""
    _svg(tmp_path, "a-data-flow.svg", _WIDE)
    record = _record(tmp_path, "![x](drawings/a-data-flow.svg)\n\n## Decision\n\nThe file goes missing.")
    accepted = _arch.parse_record(
        record.path.write_text(record.body.replace("status: proposed", "status: accepted"))
        and record.path
    )

    assert _arch.validate([accepted]) == []


def test_a_multi_kind_record_gets_the_edge_check_on_each_kinds_svg(tmp_path: Path) -> None:
    _svg(tmp_path, "a-data-flow.svg", _WIDE)
    _svg(tmp_path, "a-state.svg", _WIDE.replace(_TWELVE, "state missing"))
    record = _record(
        tmp_path,
        "### data-flow\n\n![x](drawings/a-data-flow.svg)\n\n"
        "### state\n\n![y](drawings/a-state.svg)\n\n## Decision\n\nThe file and the state go missing.",
        diagram="[data-flow, state]",
    )

    assert [f.message for f in _arch.validate([record])] == [
        "drawing label 'file missing' runs past the drawing's edge",
        "drawing label 'state missing' runs past the drawing's edge",
    ]
