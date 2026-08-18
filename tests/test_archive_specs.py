"""Tests for `wfctl archive-specs` — preserve speckit artifacts before teardown."""
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

    result = runner.invoke(app, ["archive-specs"])
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

    assert runner.invoke(app, ["archive-specs"]).exit_code == 0

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

    assert runner.invoke(app, ["archive-specs"]).exit_code == 0

    assert (_archive_dir(agent_dir) / "extra" / "legacy-agent-spec.md").is_file()


def test_the_whole_superseded_directory_is_archived_not_just_spec_md(
    agent_dir: Path,
) -> None:
    """`.agent/` is read as a directory, so a neighbour of spec.md is not deleted.

    Reading one filename rescued `spec.md` and destroyed everything beside it.
    Three `brief.md` files survived the 2026-08-11 worktree cleanup only because
    they were copied out by hand first — this is the regression that made that
    necessary.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _write(repo_root / ".agent" / "spec.md", "legacy design\n")
    _write(repo_root / ".agent" / "brief.md", "the brief\n")
    _write(repo_root / ".agent" / "notes" / "scratch.md", "nested\n")

    assert runner.invoke(app, ["archive-specs"]).exit_code == 0

    arch = _archive_dir(agent_dir)
    # spec.md keeps the flat name every archive written so far already uses.
    assert (arch / "extra" / "legacy-agent-spec.md").read_text() == "legacy design\n"
    assert (arch / "extra" / "legacy-agent" / "brief.md").read_text() == "the brief\n"
    assert (arch / "extra" / "legacy-agent" / "notes" / "scratch.md").read_text() == "nested\n"


def test_unmapped_artifacts_land_under_extra(agent_dir: Path) -> None:
    """A speckit artifact the map has never heard of is archived, not dropped."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md", "REVIEW.md", "notes/scratch.md")

    assert runner.invoke(app, ["archive-specs"]).exit_code == 0

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

    assert runner.invoke(app, ["archive-specs"]).exit_code == 0

    arch = _archive_dir(agent_dir)
    assert (arch / "12-implement-complete.md").is_file()
    assert not (arch / "extra" / "checklists" / "implement-complete.md").exists()

    index = (arch / "README.md").read_text()
    # Presence first: `.index` raises ValueError on a miss, which reads as a broken
    # test rather than the regression it actually is.
    assert "11-analysis-report.md" in index
    assert "12-implement-complete.md" in index
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

    assert runner.invoke(app, ["archive-specs"]).exit_code == 0

    arch = _archive_dir(agent_dir)
    assert not (arch / "extra" / "leaked.md").exists()
    assert (arch / "2-spec.md").is_file(), "a mapped artifact is archived even as a link"


def test_rerun_moves_the_previous_archive_aside(agent_dir: Path) -> None:
    """A rerun refreshes rather than accumulating, and never destroys the old one."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md")

    assert runner.invoke(app, ["archive-specs"]).exit_code == 0
    (_archive_dir(agent_dir) / "2-spec.md").write_text("first run\n")

    assert runner.invoke(app, ["archive-specs"]).exit_code == 0

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

    assert runner.invoke(app, ["archive-specs"]).exit_code == 0
    (spec_dir / "spec.md").unlink()

    result = runner.invoke(app, ["archive-specs"])
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
        result = runner.invoke(app, ["archive-specs"])
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
    result = runner.invoke(app, ["archive-specs"])
    assert result.exit_code == 0
    assert "archive failed" in result.output


def test_nothing_to_archive_is_a_success(agent_dir: Path) -> None:
    """A repo that never opted into speckit still tears down cleanly."""
    result = runner.invoke(app, ["archive-specs"])
    assert result.exit_code == 0
    assert "nothing to archive" in result.output
    assert not _archive_dir(agent_dir).exists()


def test_missing_worktree_does_not_fail(agent_dir: Path, tmp_path: Path) -> None:
    """A path that isn't there is reported, not raised — teardown continues."""
    result = runner.invoke(app, ["archive-specs", str(tmp_path / "gone")])
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
    result = runner.invoke(app, ["archive-specs"])
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

    assert runner.invoke(app, ["archive-specs"]).exit_code == 0
    arch = _archive_dir(agent_dir)
    assert (arch / "2-spec.md").is_file()
    assert (arch / "4-plan.md").is_file()


def test_index_records_branch_commit_and_source(agent_dir: Path) -> None:
    """The index is the archive's only context once the worktree is gone."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md")

    assert runner.invoke(app, ["archive-specs"]).exit_code == 0
    readme = (_archive_dir(agent_dir) / "README.md").read_text()

    assert f"# Story archive: {handle}" in readme
    assert "| Branch |" in readme and "| Last commit |" in readme
    assert str(repo_root) in readme
    assert "| [2-spec.md](2-spec.md) | `specs/" in readme, "source path stays worktree-relative"


def test_explicit_arguments_win_over_the_environment(agent_dir: Path) -> None:
    """workmux passes both positionally; they must beat WM_* and HEAD."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    _make_story(repo_root, "342-explicit-story", "spec.md")

    result = runner.invoke(app, ["archive-specs", str(repo_root), "342-explicit-story"])
    assert result.exit_code == 0
    assert (_archive_dir(agent_dir) / "2-spec.md").is_file()


def test_former_name_still_dispatches(agent_dir: Path) -> None:
    """`archive-story` must keep working — .workmux.yaml is repo-local and older
    copies persist. A failing pre_remove hook now aborts the removal, so an
    unknown command name would make those repos' worktrees unremovable, which is
    worse than the loss this feature exists to prevent."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md", "plan.md")

    result = runner.invoke(app, ["archive-story"])

    assert result.exit_code == 0, result.output
    arch = _archive_dir(agent_dir)
    assert (arch / "2-spec.md").is_file()
    assert (arch / "4-plan.md").is_file()


def test_former_name_is_not_advertised() -> None:
    """The alias is a compatibility shim, not a second supported spelling."""
    out = runner.invoke(app, ["--help"]).output

    assert "archive-specs" in out
    assert "archive-story" not in out


# --- Containment: archive what teardown destroys, skip what it cannot reach ----
#
# The predicate is path containment, never "is spec_root set". The third test
# below is the one an on/off flag would get wrong.


def _durable_story(root: Path, handle: str, *rels: str) -> Path:
    """A spec dir under an external root, reached via WFCTL_SPEC_DIR."""
    spec_dir = root / handle
    for rel in rels:
        _write(spec_dir / rel)
    return spec_dir


def test_default_layout_archives_exactly_what_it_archives_today(agent_dir: Path) -> None:
    """Regression guard — must pass before the predicate exists and after.

    Most repos are here. Asserts the full mapped list rather than a count, so a
    predicate that silently drops one entry cannot pass.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "design.md", "spec.md", "plan.md", "tasks.md")

    assert runner.invoke(app, ["archive-specs"]).exit_code == 0

    arch = _archive_dir(agent_dir)
    assert sorted(p.name for p in arch.iterdir()) == [
        "1-design.md", "2-spec.md", "4-plan.md", "9-tasks.md", "README.md",
    ]


def test_durable_spec_root_is_not_copied(agent_dir: Path, tmp_path: Path,
                                          monkeypatch: pytest.MonkeyPatch) -> None:
    """Specs outside the worktree are not at risk, so teardown does not copy them.

    The legacy design doc *is* inside the worktree and is still rescued — the
    predicate is about location, not about which file it is.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    durable = tmp_path.parent / "durable-specs"
    spec_dir = _durable_story(durable, handle, "design.md", "spec.md", "plan.md")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(durable))
    _write(repo_root / ".agent" / "spec.md", "legacy design\n")

    result = runner.invoke(app, ["archive-specs"])
    assert result.exit_code == 0, result.output

    arch = _archive_dir(agent_dir)
    assert (arch / "extra" / "legacy-agent-spec.md").is_file(), "at-risk file dropped"
    assert not (arch / "1-design.md").exists(), "durable spec was copied anyway"
    assert not (arch / "2-spec.md").exists()
    assert (spec_dir / "spec.md").is_file(), "the live spec must be untouched"

    # The mixed case is where both messages earn their place, and where either
    # alone would mislead: the durable notice explains why almost nothing was
    # copied, the rescue notice explains why an archive exists at all. Neither
    # may suppress the other (#36).
    assert "spec dir is durable" in result.output
    assert "rescued 1 file(s)" in result.output


def test_spec_root_resolving_inside_the_worktree_is_still_archived(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Containment, not configuration.

    A spec_root that points back inside the worktree describes files teardown
    still destroys. Also a regression guard: this passes today, and a predicate
    keyed on "is spec_root set" rather than on the path would break it.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    inside = repo_root / "nested-specs"
    _durable_story(inside, handle, "spec.md", "plan.md")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(inside))

    assert runner.invoke(app, ["archive-specs"]).exit_code == 0

    arch = _archive_dir(agent_dir)
    assert (arch / "2-spec.md").is_file()
    assert (arch / "4-plan.md").is_file()


def test_durable_root_with_nothing_at_risk_writes_no_archive(
    agent_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Under the rescue framing, the absence of an archive is the right output."""
    handle = os.environ["WFCTL_BRANCH"]
    durable = tmp_path.parent / "durable-none"
    _durable_story(durable, handle, "spec.md", "plan.md")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(durable))

    result = runner.invoke(app, ["archive-specs"])

    assert result.exit_code == 0, result.output
    assert not _archive_dir(agent_dir).exists(), "copied files that were never at risk"


def test_durable_skip_message_names_the_resolved_path(
    agent_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without the path the message cannot be told apart from a failed lookup."""
    handle = os.environ["WFCTL_BRANCH"]
    durable = tmp_path.parent / "durable-msg"
    spec_dir = _durable_story(durable, handle, "spec.md")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(durable))

    out = runner.invoke(app, ["archive-specs"]).output

    assert "durable" in out.lower()
    assert str(spec_dir) in out


# --- Failure semantics: refuse the removal only when something was lost --------


def _fail_copy_on(monkeypatch: pytest.MonkeyPatch, nth: int) -> None:
    """Make the Nth copy raise, mid-loop.

    Deliberately not an unwritable state dir: that fails at mkdir before any copy
    runs, so it exercises setup rather than the copy path and cannot leave the
    partial state these tests exist to detect.
    """
    import shutil
    real = shutil.copy2
    calls = {"n": 0}

    def flaky(src: object, dst: object) -> object:
        calls["n"] += 1
        if calls["n"] == nth:
            raise OSError(28, "No space left on device")
        return real(src, dst)

    monkeypatch.setattr(shutil, "copy2", flaky)


def test_failed_copy_of_at_risk_files_refuses_the_removal(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-zero is what makes workmux abort — silence here destroys the specs."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "design.md", "spec.md", "plan.md")
    _fail_copy_on(monkeypatch, 2)

    result = runner.invoke(app, ["archive-specs"])

    assert result.exit_code != 0, "teardown would have proceeded and lost the specs"


def test_nothing_at_risk_still_exits_zero(agent_dir: Path, tmp_path: Path) -> None:
    """Regression guard — must pass before and after.

    Guards against the new non-zero path widening past its rule. A missing
    worktree and a non-git directory cannot have lost anything.
    """
    assert runner.invoke(app, ["archive-specs", str(tmp_path / "gone")]).exit_code == 0
    assert runner.invoke(app, ["archive-specs"]).exit_code == 0


def test_refusal_message_names_both_routes_out(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`workmux remove --force` does not bypass the hook, so the manual route is
    the only escape and must be stated completely — including the caveat that
    `git worktree remove` refuses when untracked files are present."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "design.md", "spec.md")
    _fail_copy_on(monkeypatch, 1)

    out = runner.invoke(app, ["archive-specs"]).output

    assert "No space left on device" in out, "the cause must be visible"
    assert "workmux remove" in out
    assert "git worktree remove" in out
    assert "git branch -D" in out
    assert "--force" in out, "the untracked-files caveat is missing"
    assert "tmux" in out, "the skipped-cleanup note is missing"

    # The escape route has to survive being pasted. rich wraps at the terminal
    # width and will break a long path across lines unless soft_wrap is set —
    # every assertion above still passes when that happens, because the
    # substrings are short. Caught by running the real teardown, not by the
    # tests, which is why this line exists.
    escape = next(ln for ln in out.splitlines() if "git worktree remove" in ln)
    assert str(repo_root) in escape, "the path was wrapped out of the command"
    assert "git branch -D" in escape, "the command was split across lines"


def test_failed_run_leaves_the_previous_archive_untouched(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refusing a removal invites a retry. A retry that displaced a complete
    archive with a partial one would make the safety mechanism the damage."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "design.md", "spec.md", "plan.md")
    assert runner.invoke(app, ["archive-specs"]).exit_code == 0
    arch = _archive_dir(agent_dir)
    before = sorted(p.name for p in arch.iterdir())
    assert "README.md" in before

    _fail_copy_on(monkeypatch, 2)
    assert runner.invoke(app, ["archive-specs"]).exit_code != 0

    assert sorted(p.name for p in arch.iterdir()) == before, "archive/ was degraded"
    assert (arch / "README.md").is_file(), "the index went missing"


def test_failure_then_retry_leaves_no_junk_directory(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The timestamped pool is real history — every successful re-run adds one.
    A failed attempt must never land in it, or nothing distinguishes junk from
    a previous story."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "design.md", "spec.md", "plan.md")
    assert runner.invoke(app, ["archive-specs"]).exit_code == 0

    # Fires once, on the 2nd copy, then lets everything through — so the retry
    # below runs clean. Deliberately not `monkeypatch.undo()`: pytest hands the
    # test and the `agent_dir` fixture the same monkeypatch instance, so undoing
    # would also unset WFCTL_STATE_DIR and send the retry to a different state
    # dir, where it would find nothing to displace and pass vacuously.
    _fail_copy_on(monkeypatch, 2)
    assert runner.invoke(app, ["archive-specs"]).exit_code != 0
    assert runner.invoke(app, ["archive-specs"]).exit_code == 0

    dirs = sorted(p.name for p in agent_dir.iterdir() if p.is_dir())
    assert len(dirs) == 2, f"expected archive/ + one timestamped run, got {dirs}"
    assert "archive" in dirs
    for d in dirs:
        assert (agent_dir / d / "README.md").is_file(), f"{d} is an incomplete result"


def test_failed_promotion_also_refuses_the_removal(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every failure with a non-empty plan must reach ArchiveIncomplete.

    The promotion renames used to sit outside the try, so a failure there raised a
    bare OSError, the CLI's generic handler turned it into exit 0, and teardown
    deleted the worktree with nothing promoted.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "design.md", "spec.md")

    real_rename = Path.rename

    def refuse_promotion(self: Path, target: object) -> object:
        if self.name.endswith(".staging"):
            raise OSError(13, "Permission denied")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", refuse_promotion)

    result = runner.invoke(app, ["archive-specs"])

    assert result.exit_code != 0, "teardown would have proceeded with nothing promoted"


def test_unclearable_staging_refuses_rather_than_merging_stale_files(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`_copy` mkdirs with exist_ok, so a staging dir left by a killed run would
    have its stale files promoted as if this run had copied them. If it cannot be
    cleared, block instead."""
    import shutil
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "design.md")
    stale = agent_dir / "archive.staging"
    _write(stale / "9-tasks.md", "left by a killed run\n")

    # Honours `ignore_errors` the way the real one does, so this exercises the
    # un-ignored clear at the top of the run rather than the best-effort cleanup
    # in the handler.
    def refuse(path: object, *a: object, ignore_errors: bool = False, **k: object) -> None:
        if not ignore_errors:
            raise OSError(13, "Permission denied")

    monkeypatch.setattr(shutil, "rmtree", refuse)

    result = runner.invoke(app, ["archive-specs"])

    assert result.exit_code != 0
    assert not (_archive_dir(agent_dir) / "9-tasks.md").exists(), "stale file promoted"


def test_durable_skip_is_reported_even_when_something_else_is_archived(
    agent_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The mixed case: an external spec root plus a legacy design doc. The legacy
    file produces an archive, so gating the notice on an empty plan hid the
    explanation exactly where it is most needed."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    durable = tmp_path.parent / "durable-mixed"
    spec_dir = _durable_story(durable, handle, "spec.md")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(durable))
    _write(repo_root / ".agent" / "spec.md", "legacy design\n")

    out = runner.invoke(app, ["archive-specs"]).output

    assert "durable" in out.lower()
    assert str(spec_dir) in out
    assert "archived" in out, "the at-risk legacy file should still be archived"


def test_escape_route_survives_a_path_with_spaces(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The refusal message is meant to be pasted. An unquoted path containing a
    space produces a command that fails; metacharacters produce one that does
    something else."""
    import shlex
    spaced = tmp_path / "a dir with spaces"
    spaced.mkdir()
    _make_story(spaced, "42-spaced", "design.md", "spec.md")
    _fail_copy_on(monkeypatch, 1)

    out = runner.invoke(app, ["archive-specs", str(spaced), "42-spaced"]).output

    line = next(ln for ln in out.splitlines() if "git worktree remove" in ln)
    assert shlex.quote(str(spaced)) in line, "the path was interpolated unquoted"
    # Pasting it must parse as one argument, not three.
    parsed = shlex.split(line.split("git worktree remove", 1)[1].split("&&")[0])
    assert parsed == [str(spaced)]


def test_durable_message_survives_a_path_containing_markup(
    agent_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`[` is legal in a directory name; rich reads it as a style tag.

    The message exists to name a location, so a silently truncated path is worse
    than no message at all.
    """
    handle = os.environ["WFCTL_BRANCH"]
    durable = tmp_path.parent / "durable[bold]root"
    spec_dir = _durable_story(durable, handle, "spec.md")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(durable))

    out = runner.invoke(app, ["archive-specs"]).output

    assert str(spec_dir) in out, "the path was mangled by markup parsing"


# --- the two end-condition notices (#36) ------------------------------------
#
# Two compatibility paths survived the sweep because deleting them destroys
# data: the read that rescues a superseded `.agent/`, and the `archive-story`
# alias. Each now announces itself when it fires, so "has this machine been
# migrated" is answerable from teardown output instead of from a comment nobody
# observes. The silence cases matter as much as the firing ones — a notice that
# never goes quiet can never end the transition it exists to close.


def test_the_former_name_reports_its_own_rename(agent_dir: Path) -> None:
    """Invoking the alias names the current command and the fix."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md")

    result = runner.invoke(app, ["archive-story"])

    assert result.exit_code == 0, result.output
    assert "archive-story" in result.output
    assert "archive-specs" in result.output
    assert "install-config" in result.output
    assert "retired once this line stops appearing" in result.output


def test_the_current_name_says_nothing_about_the_rename(agent_dir: Path) -> None:
    """The silence half. A notice on every invocation could never end."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md")

    result = runner.invoke(app, ["archive-specs"])

    assert result.exit_code == 0, result.output
    assert "renamed to" not in result.output
    assert "install-config" not in result.output


def test_the_former_name_still_reports_when_there_is_nothing_to_archive(
    agent_dir: Path,
) -> None:
    """The hook needs re-seeding whether or not this teardown archived anything.

    Gating the notice on a non-empty archive would hide it on exactly the
    worktrees that are cheapest to tear down, which are the ones a machine
    accumulates most of.
    """
    result = runner.invoke(app, ["archive-story"])

    assert result.exit_code == 0, result.output
    assert "archive-specs" in result.output


def test_a_legacy_rescue_reports_how_many_files_it_saved(agent_dir: Path) -> None:
    """The count must match the files actually rescued, not the archive total."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md")
    _write(repo_root / ".agent" / "spec.md", "legacy design\n")
    _write(repo_root / ".agent" / "brief.md", "the brief\n")
    _write(repo_root / ".agent" / "notes" / "scratch.md", "nested\n")

    result = runner.invoke(app, ["archive-specs"])

    assert result.exit_code == 0, result.output
    assert "rescued 3 file(s)" in result.output, result.output
    # The end condition, stated in the output rather than only in a comment:
    # without it a reader learns the path is going away but not that the
    # silence afterwards is the signal to delete it (SC-005).
    assert "retired once this line stops appearing" in result.output


def test_no_legacy_dir_means_no_rescue_notice(agent_dir: Path) -> None:
    """The silence half — this is the signal the path is removable."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md")

    result = runner.invoke(app, ["archive-specs"])

    assert result.exit_code == 0, result.output
    assert "rescued" not in result.output


def test_an_empty_legacy_dir_is_not_reported_as_a_rescue(agent_dir: Path) -> None:
    """Present but empty rescues nothing, so it must read as migrated.

    An existence-keyed notice would report a directory someone had already
    emptied, and the machine would look unmigrated forever.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md")
    (repo_root / ".agent").mkdir()

    result = runner.invoke(app, ["archive-specs"])

    assert result.exit_code == 0, result.output
    assert "rescued" not in result.output


def test_both_notices_appear_together_without_suppressing_each_other(
    agent_dir: Path,
) -> None:
    """The two conditions are independent, and a machine can carry both.

    Reporting only one would understate what that machine still needs, and the
    exit code must not move — a teardown is never aborted by a message about a
    shim.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md")
    _write(repo_root / ".agent" / "spec.md", "legacy design\n")

    result = runner.invoke(app, ["archive-story"])

    assert result.exit_code == 0, result.output
    assert "rescued 1 file(s)" in result.output
    assert "archive-specs" in result.output


def test_an_unmapped_spec_file_is_not_miscounted_as_a_rescue(agent_dir: Path) -> None:
    """The rescue count must come from the rescue, not from a name that resembles it.

    Unmapped spec-dir files land under `extra/` too, so counting by destination
    prefix let `extra/legacy-agent-notes.md` — an ordinary spec artifact — read
    as a rescued `.agent/` file. The machine then reports a superseded path it
    does not have, and the notice can never go silent, which is precisely the
    signal the notice exists to give.
    """
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    handle = os.environ["WFCTL_BRANCH"]
    _make_story(repo_root, handle, "spec.md", "legacy-agent-notes.md")
    assert not (repo_root / ".agent").exists(), "the fixture must have no legacy dir"

    result = runner.invoke(app, ["archive-specs"])

    assert result.exit_code == 0, result.output
    assert "rescued" not in result.output, result.output
