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
