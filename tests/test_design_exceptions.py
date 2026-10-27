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


def test_a_hand_written_exception_with_no_blank_line_keeps_its_reason(tmp_path: Path) -> None:
    """The reader split on the header's blank line, so a file written by hand
    as one line, or with no blank line under its header, read back as an empty
    reason. The gate counted it as answered, and `check-body` found the empty
    reason in every body."""
    spec = tmp_path / "700-fix"
    folder = _design_exceptions.folder(spec)
    folder.mkdir(parents=True)
    _design_exceptions.path(spec, BOUNDARY).write_text("Copy fix only\n")
    (folder / "plan.plan-review.md").write_text("# header\nSigned off in chat\n")

    assert _design_exceptions.boundary(spec) == "Copy fix only"
    assert _design_exceptions.passes(spec) == {"plan.plan-review": "Signed off in chat"}


def test_an_exception_with_no_reason_is_no_exception(tmp_path: Path) -> None:
    """`arch none` and `step none` refuse an empty reason, so only a file
    written by hand gets here. Read as an exception, it answered the design
    gate with nothing, and only `check-body` noticed, which neither CI nor the
    guard runs."""
    spec = tmp_path / "700-fix"
    folder = _design_exceptions.folder(spec)
    folder.mkdir(parents=True)
    _design_exceptions.path(spec, BOUNDARY).write_text("# No new boundary\n")
    (folder / "plan.plan-review.md").write_text("# `plan.plan-review` does not apply\n\n")

    assert _design_exceptions.boundary(spec) is None
    assert _design_exceptions.passes(spec) == {}


def test_a_directory_named_like_a_pass_exception_is_not_read(tmp_path: Path) -> None:
    """`passes` globs `*.*.md`, which a directory can match too, and reading
    one raised `IsADirectoryError` on every status read."""
    spec = tmp_path / "700-fix"
    (_design_exceptions.folder(spec) / "x.y.md").mkdir(parents=True)

    assert _design_exceptions.passes(spec) == {}


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


# --- per-context answers (#649) ----------------------------------------------


def test_a_context_gets_its_own_subfolder_of_exceptions(tmp_path: Path) -> None:
    """A "no" for one context must not read as an answer for another, so each
    context writes under `exceptions/<context>/` and `path` names the same file.
    """
    spec = tmp_path / "700-fix"
    boundary = _design_exceptions.write(spec, BOUNDARY, "Copy only", context="install-and-drift")
    ui = _design_exceptions.write(
        spec, "brainstorm.software-design", "No structure change", context="install-and-drift"
    )

    assert boundary == spec / "exceptions" / "install-and-drift" / "boundary.md"
    assert ui == spec / "exceptions" / "install-and-drift" / "brainstorm.software-design.md"
    assert _design_exceptions.path(spec, BOUNDARY, context="install-and-drift") == boundary
    assert _design_exceptions.boundary(spec, context="install-and-drift") == "Copy only"
    assert _design_exceptions.passes(spec, context="install-and-drift") == {
        "brainstorm.software-design": "No structure change"
    }


def test_a_per_context_title_names_the_context(tmp_path: Path) -> None:
    """The file sits in a folder named for the context, but a reader opening it
    alone sees only the title."""
    spec = tmp_path / "700-fix"
    boundary = _design_exceptions.write(spec, BOUNDARY, "Copy only", context="a")
    claim = _design_exceptions.write(spec, "brainstorm.software-design", "None", context="a")

    assert boundary.read_text().splitlines()[0] == "# No new boundary for a"
    assert claim.read_text().splitlines()[0] == "# brainstorm.software-design does not apply to a"


def test_a_per_context_answer_is_not_a_branch_wide_one(tmp_path: Path) -> None:
    """Without a context `boundary` and `passes` read one level and never a
    subfolder, or one context's "no" would clear the whole branch and every
    context's claim would skip the pass (FR-011)."""
    spec = tmp_path / "700-fix"
    _design_exceptions.write(spec, BOUNDARY, "Copy only", context="a")
    _design_exceptions.write(spec, "brainstorm.software-design", "None", context="a")

    assert _design_exceptions.boundary(spec) is None
    assert _design_exceptions.passes(spec) == {}
    assert _design_exceptions.boundary(spec, context="b") is None


def test_reasons_lists_every_label_and_reason_across_both_forms(tmp_path: Path) -> None:
    """`check-body` compares each reason against the PR body, so it needs the
    per-context ones too, labelled so a finding says which answer is missing."""
    spec = tmp_path / "700-fix"
    _design_exceptions.write(spec, BOUNDARY, "Wide")
    _design_exceptions.write(spec, "brainstorm.ui-design", "No screens")
    _design_exceptions.write(spec, BOUNDARY, "Narrow", context="a")

    assert sorted(_design_exceptions.reasons(spec)) == sorted([
        ("boundary", "Wide"),
        ("brainstorm.ui-design", "No screens"),
        ("boundary for a", "Narrow"),
    ])


def test_reasons_of_a_missing_folder_is_empty(tmp_path: Path) -> None:
    assert _design_exceptions.reasons(tmp_path / "none") == []


def test_boundary_contexts_lists_the_contexts_with_a_boundary_exception(tmp_path: Path) -> None:
    """The guard names the branch's own per-context files without the name list,
    so the list going away doesn't hide them (#653). A context holding only a
    pass claim, or an empty file, isn't one."""
    spec = tmp_path / "700-fix"
    _design_exceptions.write(spec, BOUNDARY, "b", context="beta")
    _design_exceptions.write(spec, BOUNDARY, "a", context="alpha")
    _design_exceptions.write(spec, "brainstorm.software-design", "none", context="gamma")
    (spec / "exceptions" / "delta").mkdir()
    (spec / "exceptions" / "delta" / "boundary.md").write_text("# No new boundary for delta\n")

    assert _design_exceptions.boundary_contexts(spec) == ["alpha", "beta"]
    assert _design_exceptions.boundary_contexts(tmp_path / "none") == []


def test_a_context_that_could_leave_the_exceptions_folder_is_refused(tmp_path: Path) -> None:
    """The CLI checks a name against the domain page, but this module builds the
    path, so it refuses one that points outside `exceptions/` itself."""
    import pytest

    for bad in ("../x", "a/b", ".hidden", ""):
        with pytest.raises(ValueError):
            _design_exceptions.path(tmp_path, BOUNDARY, context=bad)
