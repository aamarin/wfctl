"""`wfctl end` reports what it saw and concludes nothing (#70).

It used to print "Session ended" and write `**Status**: complete` into the
handoff, on every run — including one that closed a session with most of the
tasks open and a dirty tree. Nothing observed that word. The next session read
it, and a story that was half done was handed over as finished.

What replaces it is three readings taken at the moment `end` runs: where the
pipeline stands, whether the boundary question was answered, whether the tree
has uncommitted work. The reader draws the conclusion; `end` does not.
"""
from __future__ import annotations

import json
import types

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()

# Every spelling of the claim `end` must not make. `complete` is the word that
# was actually written; the rest are the ways it would come back if someone
# reintroduced a verdict without reusing the same string.
COMPLETION_CLAIMS = ("complete", "finished", "done." , "success")


def _end(storyctl_dir: types.SimpleNamespace) -> str:
    runner.invoke(app, ["start"])
    result = runner.invoke(app, ["end"])
    assert result.exit_code == 0, result.output
    return result.output


def _summary(storyctl_dir: types.SimpleNamespace) -> str:
    return (storyctl_dir.agent_dir / "session-summary.md").read_text()


def test_the_printed_line_names_the_position_the_boundary_and_the_tree(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Three clauses, each a reading. The contract in `cli-output.md`."""
    storyctl_dir.stage_upstream_of("tasks", tasks="- [x] T001 done\n- [ ] T002 open\n")

    output = _end(storyctl_dir)

    assert "Session closed — implement 1/2 done, boundary unanswered, tree clean." in output
    assert "Summary: " in output
    # One line, not folded at the console width — it is the only path `end`
    # prints and the next session opens it.
    summary_line = next(ln for ln in output.splitlines() if "Summary:" in ln)
    assert summary_line.strip().endswith("session-summary.md")


def test_the_summary_file_carries_the_same_three_readings(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The file and the line come off one set of observations.

    Two reads of the same facts can disagree if anything moves between them,
    and the file is what the next session actually opens.
    """
    storyctl_dir.stage_upstream_of("tasks", tasks="- [x] T001 done\n- [ ] T002 open\n")

    _end(storyctl_dir)

    summary = _summary(storyctl_dir)
    assert "**Step**: implement 1/2 done" in summary
    assert "**Boundary**: unanswered" in summary
    assert "**Tree**: clean" in summary


@pytest.mark.parametrize(("exception", "expected"), [(True, "answered"), (False, "unknown")])
def test_a_boundary_exception_reads_as_answered_and_git_alone_cannot_say(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
    exception: bool, expected: str,
) -> None:
    """The summary reads the boundary under the same rule as the gate (FR-014),
    so the two never disagree. With the exception moved out of the arch root,
    a summary that asked git alone would report "unanswered" on every branch
    that answered with `arch none`.

    Without an exception the line still maps git's three answers, so a git
    that can't tell still reads `unknown` rather than borrowing an answer.
    """
    from wfctl import cli

    monkeypatch.setattr(cli, "touched_on_this_branch", lambda *a, **k: None)
    if exception:
        runner.invoke(app, ["arch", "none", "--reason", "copy edit"])

    _end(storyctl_dir)

    assert f"**Boundary**: {expected}" in _summary(storyctl_dir)


def test_uncommitted_work_is_reported_as_a_dirty_tree(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The tree clause is read, not assumed — both readings have to be reachable.

    Dirty is the interesting one: it is the state a session most often ends in,
    and the state in which "complete" was most obviously wrong.
    """
    (storyctl_dir.repo_root / "unfinished.py").write_text("# half a change\n")

    output = _end(storyctl_dir)

    assert "tree dirty." in output
    assert "**Tree**: dirty" in _summary(storyctl_dir)


@pytest.mark.parametrize(
    "tasks,expected",
    [
        (None, "brainstorm"),
        ("- [ ] T001 open\n", "implement 0/1 done"),
        ("- [x] T001 done\n", "every step done"),
    ],
    ids=["nothing-started", "mid-implement", "every-step-done"],
)
def test_no_pipeline_state_produces_a_completion_claim(
    storyctl_dir: types.SimpleNamespace, tasks: str | None, expected: str
) -> None:
    """Including the state where the claim would have been true.

    A test that only checked the mid-implement case would pass on an `end` that
    printed "complete" whenever the pipeline was finished — which is where the
    old wording was defensible and where reintroducing it is most tempting.
    The finished story is reported as a position, not as a verdict on the work.
    """
    if tasks is not None:
        storyctl_dir.stage_upstream_of("tasks", tasks=tasks)
        storyctl_dir.make_spec_artifact("decompose")

    output = _end(storyctl_dir)
    summary = _summary(storyctl_dir)

    assert expected in output
    assert "**Step**: " + expected in summary

    assert "**Status**" not in summary
    for claim in COMPLETION_CLAIMS:
        assert claim not in output.lower()
        assert claim not in summary.lower()


def test_the_handoff_prose_reads_as_unfilled(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Honest standing alone (FR-008).

    Nothing above the prose may claim the session finished, and the prose itself
    must not look written when nobody wrote it.
    """
    _end(storyctl_dir)

    summary = _summary(storyctl_dir)
    assert "## What We Accomplished\n\n- (fill in)" in summary
    assert "## Next Session TODO\n\n- [ ] (fill in)" in summary


def test_the_end_event_records_the_position_not_a_status(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`{"event": "end", "status": "complete"}` was the same claim in the log."""
    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")

    _end(storyctl_dir)

    last = json.loads(
        (storyctl_dir.agent_dir / "events.jsonl").read_text().splitlines()[-1]
    )
    assert last["event"] == "end"
    assert "status" not in last
    assert last["step"] == "implement 0/1 done"


# --- #649: the Boundary line reads the same answer `status` does --------------


def _listing(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, listed: str
) -> "Path":
    from pathlib import Path

    from tests.conftest import branch_design, write_domain_page

    root = storyctl_dir.repo_root / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    write_domain_page(root, "session-continuity, attention")
    storyctl_dir.make_spec_artifact("brainstorm", content=branch_design(listed))
    assert isinstance(root, Path)
    return root


def test_a_branch_that_answered_every_context_with_a_no_reads_answered(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Before #649 the line saw only a branch-wide "no" or a changed record, so
    this branch read "unanswered" while `wfctl status` showed the pass done, and
    the next session redid finished work (FR-020)."""
    from wfctl import _design_exceptions

    _listing(storyctl_dir, monkeypatch, "session-continuity, attention")
    for context in ("session-continuity", "attention"):
        _design_exceptions.write(storyctl_dir.spec_dir, "boundary", "Copy only", context=context)

    assert "boundary answered" in _end(storyctl_dir)
    assert "**Boundary**: answered" in _summary(storyctl_dir)


def test_a_branch_whose_only_record_governs_another_context_reads_unanswered(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.conftest import write_record

    root = _listing(storyctl_dir, monkeypatch, "session-continuity")
    write_record(root, "a-decision", diagram="component", governs="attention")

    assert "boundary unanswered" in _end(storyctl_dir)


def test_a_gap_git_cannot_check_reads_unknown(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no trunk, a record committed earlier on the branch is invisible, so
    the line says it can't tell instead of calling the context unanswered."""
    import subprocess

    subprocess.run(
        ["git", "-C", str(storyctl_dir.repo_root), "branch", "-m", "trunk"],
        check=True, capture_output=True,
    )
    _listing(storyctl_dir, monkeypatch, "session-continuity")

    assert "boundary unknown" in _end(storyctl_dir)


def test_without_a_name_list_the_line_reads_as_it_did(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    from wfctl import _design_exceptions

    monkeypatch.setenv("WFCTL_ARCH_DIR", str(storyctl_dir.repo_root / "docs" / "architecture"))
    storyctl_dir.make_spec_artifact("brainstorm")
    _design_exceptions.write(storyctl_dir.spec_dir, "boundary", "Copy only")

    assert "boundary answered" in _end(storyctl_dir)
