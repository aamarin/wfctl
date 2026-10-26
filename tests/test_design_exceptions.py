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
    _design_exceptions.write(spec, "plan.plan-review", "Signed off in chat")
    assert _design_exceptions.boundary(spec) == "Copy fix only"
    assert _design_exceptions.passes(spec) == {
        "brainstorm.ui-design": "No screen changes",
        "plan.plan-review": "Signed off in chat",
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


def _sub_issue_status(storyctl_dir, monkeypatch, *, own_folder: bool) -> dict:
    """`701-sub`'s pipeline, on a spec root holding epic 700's folder with a
    boundary exception and a pass exception, and a `design.md` so the gate is
    up. With `own_folder`, the sub-issue has a spec folder of its own too."""
    import json

    from typer.testing import CliRunner

    from tests.test_paths import _delivery_map
    from wfctl.cli import app

    specs = storyctl_dir.repo_root / "specs"
    epic = specs / "700-epic"
    epic.mkdir()
    (epic / "delivery.md").write_text(_delivery_map("#701"))
    (epic / "design.md").write_text("# Design\n")
    _design_exceptions.write(epic, BOUNDARY, "The epic reuses the review store")
    _design_exceptions.write(epic, "plan.plan-review", "Skipped for the epic")
    if own_folder:
        (specs / "701-sub").mkdir()
        (specs / "701-sub" / "design.md").write_text("# Design\n")
    monkeypatch.setenv("WFCTL_BRANCH", "701-sub")
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(storyctl_dir.repo_root / "docs" / "architecture"))
    return json.loads(CliRunner().invoke(app, ["status", "--json"]).output)


def _states(payload: dict) -> dict[str, tuple[str, str | None]]:
    return {
        f"{step['name']}.{sub['name']}": (sub["state"], sub["claimed"])
        for step in payload["steps"]
        for sub in step["sub_steps"]
    }


def test_a_sub_issue_with_no_folder_of_its_own_shares_the_epics_exceptions(
    storyctl_dir, monkeypatch
) -> None:
    """Research R11. The epic's brainstorm answered the boundary question for
    every sub-issue, and a pass skipped for the epic was skipped for the plan
    they are all cut from, so a sub-issue that falls back to the epic's folder
    reads both."""
    payload = _sub_issue_status(storyctl_dir, monkeypatch, own_folder=False)

    states = _states(payload)
    assert states["brainstorm.architecture"][0] == "done"
    assert states["plan.plan-review"] == ("skipped", "Skipped for the epic")


def test_a_sub_issue_with_its_own_folder_starts_with_no_exceptions(
    storyctl_dir, monkeypatch
) -> None:
    """A sub-issue whose answers differ from its siblings gets its own folder,
    and wfctl reads that folder first. It starts from nothing, so the epic's
    "no new boundary" doesn't answer a question the sub-issue hasn't."""
    payload = _sub_issue_status(storyctl_dir, monkeypatch, own_folder=True)

    states = _states(payload)
    assert states["brainstorm.architecture"][0] != "done"
    assert states["plan.plan-review"][1] is None
