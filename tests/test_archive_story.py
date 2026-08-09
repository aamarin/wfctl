"""Tests for `wfctl archive-story` — preserve speckit artifacts before teardown."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def _write(path: Path, text: str = "x\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _make_story(repo_root: Path, handle: str, *rels: str) -> Path:
    """Create a spec dir with the given spec-dir-relative files."""
    spec_dir = repo_root / "specs" / handle
    for rel in rels:
        _write(spec_dir / rel)
    return spec_dir


def _archive_dir(agent_dir: Path) -> Path:
    return agent_dir / "archive"


def test_archives_artifacts_in_pipeline_order(agent_dir: Path) -> None:
    """The numbering is the pipeline order, and it must survive past 9 entries.

    Sorting the results would be lexicographic, putting 10-delivery.md and
    11-analysis-report.md ahead of 2-spec.md — the bug caught reviewing #9.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(
        repo_root, handle,
        "design.md", "spec.md", "checklists/requirements.md", "plan.md", "research.md",
        "data-model.md", "contracts/cli.md", "quickstart.md", "tasks.md",
        "delivery.md", "checklists/analysis-report.md",
    )

    result = runner.invoke(app, ["archive-story"])
    assert result.exit_code == 0, result.output

    arch = _archive_dir(agent_dir)
    assert (arch / "1-design.md").is_file()
    assert (arch / "10-delivery.md").is_file()
    assert (arch / "11-analysis-report.md").is_file()

    rows = [
        ln.split("|")[1].strip()
        for ln in (arch / "README.md").read_text().splitlines()
        if ln.startswith("| [")
    ]
    numbers = [int(r.split("-")[0].lstrip("[")) for r in rows]
    assert numbers == sorted(numbers), f"index is out of pipeline order: {rows}"
    assert numbers == list(range(1, 12))

    # Nothing the map should have named may fall through to the catch-all. This
    # is the assertion that fails if the design doc stops being mapped: it would
    # still be archived, as `extra/design.md`, so a missing-file check alone
    # would not notice. A silent renaming is the failure mode worth guarding.
    extra = arch / "extra"
    assert not extra.exists(), f"unmapped artifacts fell through: {list(extra.iterdir())}"


def test_a_design_doc_at_the_superseded_path_is_still_archived(agent_dir: Path) -> None:
    """A branch predating the layout move must not lose its design doc.

    This runs from `pre_remove`, so declining to archive `.agent/spec.md` is
    deleting it. It lands under `extra/` rather than as `1-design.md`: the
    numbered sequence describes what the current pipeline produces, and nothing
    infers from the archive, so preserving the file reads nothing twice.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md", "plan.md")
    _write(repo_root / ".agent" / "spec.md", "legacy design\n")

    assert runner.invoke(app, ["archive-story"]).exit_code == 0

    arch = _archive_dir(agent_dir)
    legacy = arch / "extra" / "legacy-agent-spec.md"
    assert legacy.is_file(), "the superseded design doc was silently dropped"
    assert legacy.read_text() == "legacy design\n"
    assert not (arch / "1-design.md").exists(), "the old path must not claim the mapped slot"


def test_a_design_doc_at_the_superseded_path_is_archived_without_a_spec_dir(
    agent_dir: Path,
) -> None:
    """The whole story may be one file at the old path — that is still a story.

    `_plan` returning empty means `archive` reports nothing to archive and
    copies nothing, so this is the case where the guard has to run before the
    `spec_dir is None` bail-out rather than after it.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _write(repo_root / ".agent" / "spec.md", "legacy design\n")

    assert runner.invoke(app, ["archive-story"]).exit_code == 0

    assert (_archive_dir(agent_dir) / "extra" / "legacy-agent-spec.md").is_file()


def test_unmapped_artifacts_land_under_extra(agent_dir: Path) -> None:
    """A speckit artifact the map has never heard of is archived, not dropped."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md", "REVIEW.md", "notes/scratch.md")

    assert runner.invoke(app, ["archive-story"]).exit_code == 0

    arch = _archive_dir(agent_dir)
    assert (arch / "2-spec.md").is_file(), "mapped file still uses its numbered name"
    assert (arch / "extra" / "REVIEW.md").is_file()
    assert (arch / "extra" / "notes" / "scratch.md").is_file(), "nesting is preserved"
    assert not (arch / "extra" / "spec.md").exists(), "a mapped file must not be duplicated"


def test_implementation_sentinel_is_numbered_last(agent_dir: Path) -> None:
    """The story ends at the implement sentinel, not one step short at analysis.

    It was previously unmapped and landed under `extra/`, so reading the index top
    to bottom stopped at `11-analysis-report.md` — omitting the artifact that says
    the story finished.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(
        repo_root,
        handle,
        "checklists/analysis-report.md",
        "checklists/implement-complete.md",
    )

    assert runner.invoke(app, ["archive-story"]).exit_code == 0

    arch = _archive_dir(agent_dir)
    assert (arch / "12-implement-complete.md").is_file()
    assert not (arch / "extra" / "checklists" / "implement-complete.md").exists()

    index = (arch / "README.md").read_text()
    assert index.index("11-analysis-report.md") < index.index("12-implement-complete.md"), (
        "the sentinel must come last, and 12 must not sort ahead of 11"
    )


def test_a_symlink_does_not_drag_in_content_from_outside_the_spec_dir(
    agent_dir: Path, tmp_path: Path
) -> None:
    """`is_file()` follows symlinks; `find -type f` never matched one.

    Only the unmapped scan skips them. A mapped artifact is archived whether or
    not it is a link, matching the shell version's `[ -e ]` test.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    spec_dir = _make_story(repo_root, handle, "plan.md")

    outside = _write(tmp_path / "outside" / "secret.md", "not part of this story\n")
    (spec_dir / "leaked.md").symlink_to(outside)
    (spec_dir / "spec.md").symlink_to(_write(tmp_path / "outside" / "real-spec.md"))

    assert runner.invoke(app, ["archive-story"]).exit_code == 0

    arch = _archive_dir(agent_dir)
    assert not (arch / "extra" / "leaked.md").exists()
    assert (arch / "2-spec.md").is_file(), "a mapped artifact is archived even as a link"


def test_rerun_moves_the_previous_archive_aside(agent_dir: Path) -> None:
    """A rerun refreshes rather than accumulating, and never destroys the old one."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md")

    assert runner.invoke(app, ["archive-story"]).exit_code == 0
    (_archive_dir(agent_dir) / "2-spec.md").write_text("first run\n")

    assert runner.invoke(app, ["archive-story"]).exit_code == 0

    aside = [p for p in agent_dir.glob("archive-*") if p.is_dir()]
    assert len(aside) == 1, f"expected one archive moved aside, got {aside}"
    assert (aside[0] / "2-spec.md").read_text() == "first run\n"
    assert (_archive_dir(agent_dir) / "2-spec.md").read_text() == "x\n"


def test_an_emptied_spec_dir_does_not_displace_a_good_archive(agent_dir: Path) -> None:
    """A story with nothing left in it must not overwrite the story that was there.

    The spec dir still exists — it has just been emptied — so the run has a
    resolvable story but no artifacts. Archiving that would move the real
    archive aside and leave a bare index in its place.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    spec_dir = _make_story(repo_root, handle, "spec.md")

    assert runner.invoke(app, ["archive-story"]).exit_code == 0
    (spec_dir / "spec.md").unlink()

    result = runner.invoke(app, ["archive-story"])
    assert result.exit_code == 0
    assert "nothing to archive" in result.output
    assert (_archive_dir(agent_dir) / "2-spec.md").is_file(), "the real archive survived"
    assert not list(agent_dir.glob("archive-*")), "nothing was moved aside"


def test_two_runs_in_the_same_second_both_archive(agent_dir: Path) -> None:
    """Back-to-back reruns must not collide on the moved-aside name.

    A second-resolution stamp made the second rename land on a non-empty
    directory, which raises — swallowed into 'archive failed', losing exactly
    the archive this command exists to take.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _make_story(repo_root, os.environ["WFCTL_BRANCH"], "spec.md")

    for _ in range(3):
        result = runner.invoke(app, ["archive-story"])
        assert result.exit_code == 0
        assert "archive failed" not in result.output, result.output

    assert (_archive_dir(agent_dir) / "2-spec.md").is_file()
    assert len(list(agent_dir.glob("archive-*"))) == 2


def test_a_non_git_checkout_still_exits_zero(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`get_repo_root` raises SystemExit, which `except Exception` does not catch."""
    monkeypatch.delenv("WFCTL_REPO_ROOT")

    def not_a_repo() -> Path:
        raise SystemExit("wfctl: not a git repository")

    monkeypatch.setattr("wfctl.cli.get_repo_root", not_a_repo)
    result = runner.invoke(app, ["archive-story"])
    assert result.exit_code == 0
    assert "archive failed" in result.output


def test_nothing_to_archive_is_a_success(agent_dir: Path) -> None:
    """A repo that never opted into speckit still tears down cleanly."""
    result = runner.invoke(app, ["archive-story"])
    assert result.exit_code == 0
    assert "nothing to archive" in result.output
    assert not _archive_dir(agent_dir).exists()


def test_missing_worktree_does_not_fail(agent_dir: Path, tmp_path: Path) -> None:
    """A path that isn't there is reported, not raised — teardown continues."""
    result = runner.invoke(app, ["archive-story", str(tmp_path / "gone")])
    assert result.exit_code == 0
    assert "no worktree" in result.output


def test_failure_never_blocks_teardown(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The contract that matters: whatever breaks, the hook exits 0.

    A non-zero exit here strands a worktree, which is a worse outcome than the
    missed archive it would be reporting.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _make_story(repo_root, os.environ["WFCTL_BRANCH"], "spec.md")

    def boom(*a: object, **k: object) -> None:
        raise OSError("disk on fire")

    monkeypatch.setattr("wfctl._archive.archive", boom)
    result = runner.invoke(app, ["archive-story"])
    assert result.exit_code == 0
    assert "archive failed" in result.output
    assert "disk on fire" in result.output


def test_handle_that_differs_from_the_spec_dir_still_resolves(agent_dir: Path) -> None:
    """The deliberate improvement over scripts/archive-story.sh.

    The script joined `specs/<handle>` literally, so a worktree whose handle
    did not exactly name its spec directory archived nothing. Going through
    `resolve_spec_dir` matches on the issue key instead.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    # WFCTL_BRANCH is '342-state-workflow'; the spec dir is named differently
    # but carries the same issue key.
    _make_story(repo_root, "342-a-different-slug", "spec.md", "plan.md")

    assert runner.invoke(app, ["archive-story"]).exit_code == 0
    arch = _archive_dir(agent_dir)
    assert (arch / "2-spec.md").is_file()
    assert (arch / "4-plan.md").is_file()


def test_index_records_branch_commit_and_source(agent_dir: Path) -> None:
    """The index is the archive's only context once the worktree is gone."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md")

    assert runner.invoke(app, ["archive-story"]).exit_code == 0
    readme = (_archive_dir(agent_dir) / "README.md").read_text()

    assert f"# Story archive: {handle}" in readme
    assert "| Branch |" in readme and "| Last commit |" in readme
    assert str(repo_root) in readme
    assert "| [2-spec.md](2-spec.md) | `specs/" in readme, "source path stays worktree-relative"


def test_explicit_arguments_win_over_the_environment(agent_dir: Path) -> None:
    """workmux passes both positionally; they must beat WM_* and HEAD."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _make_story(repo_root, "342-explicit-story", "spec.md")

    result = runner.invoke(app, ["archive-story", str(repo_root), "342-explicit-story"])
    assert result.exit_code == 0
    assert (_archive_dir(agent_dir) / "2-spec.md").is_file()
