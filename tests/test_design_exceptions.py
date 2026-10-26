"""`_design_exceptions` owns the exceptions folder inside a spec folder.

Every writer and reader of a design exception goes through this module, so the
header a command writes and the header a reader strips are defined in one file
(`design-exceptions-module.md`). These tests pin the format and the
missing-folder behaviour the gate, the pipeline and the guard all rely on.
"""
from __future__ import annotations

from pathlib import Path

from wfctl import _design_exceptions
from wfctl._design_exceptions import BOUNDARY


def test_folder_and_path_name_the_exceptions_folder_without_creating_it(tmp_path: Path) -> None:
    """The guard prints `path` in a refusal, so naming a file must not create it."""
    spec = tmp_path / "700-fix"
    assert _design_exceptions.folder(spec) == spec / "exceptions"
    assert _design_exceptions.path(spec, BOUNDARY) == spec / "exceptions" / "boundary.md"
    assert not spec.exists()


def test_write_creates_the_spec_folder_when_it_does_not_exist(tmp_path: Path) -> None:
    """`arch none` is often the first thing a branch writes, before `design.md`
    exists, so the module creates the spec folder rather than refusing (FR-003).
    """
    spec = tmp_path / "700-fix"
    written = _design_exceptions.write(spec, BOUNDARY, "Copy fix only")
    assert written == spec / "exceptions" / "boundary.md"
    assert written.is_file()


def test_write_titles_each_exception_by_its_kind(tmp_path: Path) -> None:
    """The branch name the old headers carried is gone, since the spec folder is
    already named for the branch (research R2).
    """
    spec = tmp_path / "700-fix"
    boundary = _design_exceptions.write(spec, BOUNDARY, "Copy fix only")
    ui = _design_exceptions.write(spec, "brainstorm.ui-design", "No screen changes")
    assert boundary.read_text() == "# No new boundary\n\nCopy fix only\n"
    assert ui.read_text() == "# `brainstorm.ui-design` does not apply\n\nNo screen changes\n"


def test_a_second_write_replaces_the_reason(tmp_path: Path) -> None:
    """One change makes one answer per question, so a second write overwrites."""
    spec = tmp_path / "700-fix"
    _design_exceptions.write(spec, BOUNDARY, "first")
    _design_exceptions.write(spec, BOUNDARY, "second")
    assert _design_exceptions.boundary(spec) == "second"


def test_readers_return_each_reason_and_never_list_the_boundary_as_a_pass(tmp_path: Path) -> None:
    """`passes` reads `*.*.md`, so `boundary.md` never shows up as a pass named
    `boundary`, which would read as a skipped pass that doesn't exist.
    """
    spec = tmp_path / "700-fix"
    _design_exceptions.write(spec, BOUNDARY, "Copy fix only")
    _design_exceptions.write(spec, "brainstorm.ui-design", "No screen changes")
    _design_exceptions.write(spec, "plan.plan-walkthrough", "Signed off in chat")
    assert _design_exceptions.boundary(spec) == "Copy fix only"
    assert _design_exceptions.passes(spec) == {
        "brainstorm.ui-design": "No screen changes",
        "plan.plan-walkthrough": "Signed off in chat",
    }


def test_a_multi_line_reason_reads_back_whole(tmp_path: Path) -> None:
    """The reader keeps everything after the first blank line, so a reason with
    its own blank line survives the round trip.
    """
    spec = tmp_path / "700-fix"
    _design_exceptions.write(spec, BOUNDARY, "line one\n\nline two")
    assert _design_exceptions.boundary(spec) == "line one\n\nline two"


def test_readers_return_nothing_for_a_missing_folder(tmp_path: Path) -> None:
    """The gate calls `boundary` on every status read, including on a branch
    with no spec folder, so a missing folder is an answer and not an error.
    """
    spec = tmp_path / "700-fix"
    assert _design_exceptions.boundary(spec) is None
    assert _design_exceptions.passes(spec) == {}
    spec.mkdir()
    assert _design_exceptions.boundary(spec) is None
    assert _design_exceptions.passes(spec) == {}
