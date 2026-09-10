"""The loop bound: whether three passes changed anything (#332).

Every test here names a way the bound could stop a run that was working, because
that is the failure the feature cannot afford — it happens unattended and looks
like the feature succeeding.
"""

from __future__ import annotations

import json
from pathlib import Path

from wfctl._predicates import Evidence
from wfctl._stall import STALL_AFTER, digest, find_stall


def _evidence(spec: str = "", plan: str = "", tasks: str = "") -> Evidence:
    return Evidence(
        spec_dir=Path("/nonexistent"),
        repo_root=Path("/nonexistent"),
        spec_text=spec,
        has_markers=False,
        plan_text=plan,
        tasks_text=tasks,
        tasks_open=False,
        tasks_done=0,
        tasks_total=0,
        verification=None,
    )


def _log(tmp_path: Path, *passes: object) -> Path:
    """Write an events.jsonl holding the given records, and return its directory."""
    lines = [json.dumps(p) if isinstance(p, dict) else str(p) for p in passes]
    (tmp_path / "events.jsonl").write_text("\n".join(lines) + "\n")
    return tmp_path


def _pass(step: str, mark: str | None, ts: str = "2026-09-10T10:00:00Z") -> dict:
    record: dict = {"ts": ts, "event": "resume", "step": step, "command": f"/{step}"}
    if mark is not None:
        record["digest"] = mark
    return record


def test_identical_evidence_digests_the_same() -> None:
    """The comparison is equality on the digest, so equal inputs must not differ."""
    assert digest(_evidence("a", "b", "c")) == digest(_evidence("a", "b", "c"))


def test_a_change_in_any_one_artifact_moves_the_digest() -> None:
    """Progress in any of the three has to reset the count, not only in the spec."""
    base = digest(_evidence("a", "b", "c"))
    assert digest(_evidence("A", "b", "c")) != base
    assert digest(_evidence("a", "B", "c")) != base
    assert digest(_evidence("a", "b", "C")) != base


def test_text_moving_between_artifacts_moves_the_digest() -> None:
    """Without a separator the three read as one stream and this move is invisible.

    The case the separator exists for: nothing was added or removed, so a
    concatenating digest would call this pass unchanged.
    """
    assert digest(_evidence("ab", "", "")) != digest(_evidence("a", "b", ""))


def test_three_attempts_that_changed_nothing_is_a_stall(tmp_path: Path) -> None:
    """The defect in #332: the same step, the same inputs, no reason to stop.

    Four observations, not three. The line written when the pipeline arrives at a
    step precedes any attempt at it, so an attempt is what sits *between* two
    identical observations — the off-by-one all three reviewers found in the first
    version of this file, which stopped a step after two real runs.
    """
    agent_dir = _log(
        tmp_path,
        _pass("clarify", "aaa", "2026-09-10T10:00:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:01:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:02:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:03:00Z"),
    )
    found = find_stall(agent_dir)
    assert found is not None
    assert found.step == "clarify"
    assert found.passes == STALL_AFTER


def test_arriving_at_a_step_is_not_an_attempt_at_it(tmp_path: Path) -> None:
    """Three identical observations carry two attempts, which is under the bound.

    `resume` records the step that is *about to* run, so counting lines as runs
    stops a step after it has executed twice — the "fires on the first repeat"
    failure `STALL_AFTER` was chosen to avoid.
    """
    agent_dir = _log(
        tmp_path,
        _pass("clarify", "aaa", "2026-09-10T10:00:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:01:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:02:00Z"),
    )
    assert find_stall(agent_dir) is None


def test_a_finished_story_is_never_a_stall(tmp_path: Path) -> None:
    """A completed story stops moving its artifacts by definition.

    `resume` writes `complete` into the same field a real step goes in, so without
    the carve-out every finished branch reports as stalled — inverting the one
    distinction the payload exists to draw.
    """
    agent_dir = _log(
        tmp_path,
        *[_pass("complete", "aaa", f"2026-09-10T10:0{i}:00Z") for i in range(5)],
    )
    assert find_stall(agent_dir) is None


def test_a_branch_parked_overnight_does_not_halt_on_arrival(tmp_path: Path) -> None:
    """Yesterday's unchanged passes plus today's arrival is a parked branch.

    The spec's fourth edge case. `/start-session` writes the sitting boundary into
    this same log, so honouring it costs a comparison — and without it a session
    stops before the step has been entered once.
    """
    agent_dir = _log(
        tmp_path,
        _pass("clarify", "aaa", "2026-09-09T10:00:00Z"),
        _pass("clarify", "aaa", "2026-09-09T10:01:00Z"),
        _pass("clarify", "aaa", "2026-09-09T10:02:00Z"),
        {"ts": "2026-09-10T09:00:00Z", "event": "start", "step": "clarify"},
        _pass("clarify", "aaa", "2026-09-10T10:00:00Z"),
    )
    assert find_stall(agent_dir) is None


def test_reopening_a_session_ends_the_previous_run(storyctl_dir) -> None:
    """The boundary has to be written on the path that carries most sittings.

    `wfctl start` returns at its already-initialized guard on every sitting after
    the first, so before #338's review it recorded nothing — and the parked-branch
    protection was inert for exactly the case it was written for. Driven through
    the real command, because the defect was that the event never existed.
    """
    from typer.testing import CliRunner

    from wfctl.cli import app

    runner = CliRunner()
    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    assert runner.invoke(app, ["start"]).exit_code == 0
    for _ in range(3):
        assert runner.invoke(app, ["resume"]).exit_code == 0

    # A second sitting on a branch that was left parked, nothing having moved.
    assert runner.invoke(app, ["start"]).exit_code == 0
    assert runner.invoke(app, ["resume"]).exit_code == 0
    assert "changed nothing" not in runner.invoke(app, ["status"]).output


def test_another_branch_boundary_does_not_clear_this_one(tmp_path: Path) -> None:
    """A shared state dir means another branch's sitting is not ours.

    Clearing on it would delay or suppress a stall this branch's own run never
    interrupted — the same leak as counting another branch's passes, met on the
    boundary rather than on the observation.
    """
    agent_dir = _log(
        tmp_path,
        *[dict(_pass("clarify", "aaa", f"2026-09-10T10:0{i}:00Z"), branch="a") for i in range(2)],
        {"ts": "2026-09-10T10:05:00Z", "event": "start", "branch": "b", "step": "clarify"},
        *[dict(_pass("clarify", "aaa", f"2026-09-10T10:1{i}:00Z"), branch="a") for i in range(2)],
    )
    found = find_stall(agent_dir, branch="a")
    assert found is not None
    assert found.passes == STALL_AFTER


def test_another_branch_passes_are_not_counted(tmp_path: Path) -> None:
    """`WFCTL_STATE_DIR` can point several branches at one log.

    Sub-issue branches of one epic are the sharp case: a grouping map resolves
    them to a single spec dir, so their digests match and their step names usually
    do too. This is the leak `notify-resolved` already carries a branch for.
    """
    mine = [dict(_pass("clarify", "aaa", f"2026-09-10T10:0{i}:00Z"), branch="a") for i in range(2)]
    theirs = [dict(_pass("clarify", "aaa", f"2026-09-10T10:1{i}:00Z"), branch="b") for i in range(3)]
    agent_dir = _log(tmp_path, *(mine + theirs))
    assert find_stall(agent_dir, branch="a") is None


def test_a_verdict_does_not_outlive_the_artifacts_it_describes(tmp_path: Path) -> None:
    """The screen a person reads straight after fixing what the stall asked for.

    `find_stall` reads the log; the current digest is computed by the same report
    two lines away. Without comparing them, `status` goes on saying the files are
    unchanged after they have been changed.
    """
    agent_dir = _log(
        tmp_path,
        *[_pass("clarify", "aaa", f"2026-09-10T10:0{i}:00Z") for i in range(4)],
    )
    assert find_stall(agent_dir) is not None
    assert find_stall(agent_dir, current="zzz") is None


def test_a_pass_that_advanced_the_work_resets_the_count(tmp_path: Path) -> None:
    """The false positive that would break working automation.

    `clarify` resolving two of six markers per pass renders an identical status
    line every time, which is why the digest and not the rendering is what is
    compared. Three such passes must not stop the run.
    """
    agent_dir = _log(
        tmp_path,
        _pass("clarify", "aaa", "2026-09-10T10:00:00Z"),
        _pass("clarify", "bbb", "2026-09-10T10:01:00Z"),
        _pass("clarify", "ccc", "2026-09-10T10:02:00Z"),
        _pass("clarify", "ddd", "2026-09-10T10:03:00Z"),
    )
    assert find_stall(agent_dir) is None


def test_two_unchanged_observations_are_not_yet_a_stall(tmp_path: Path) -> None:
    """A step legitimately taking a second run is common; stopping there is wrong."""
    agent_dir = _log(
        tmp_path,
        _pass("clarify", "aaa", "2026-09-10T10:00:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:01:00Z"),
    )
    assert find_stall(agent_dir) is None


def test_the_run_is_broken_by_a_different_step(tmp_path: Path) -> None:
    """Passes through one step are not consecutive if another step ran between them.

    Three `clarify` passes sharing a digest, with a `specify` pass in the middle,
    is a pipeline moving — not a step stuck.
    """
    agent_dir = _log(
        tmp_path,
        _pass("clarify", "aaa", "2026-09-10T10:00:00Z"),
        _pass("specify", "aaa", "2026-09-10T10:01:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:02:00Z"),
    )
    assert find_stall(agent_dir) is None


def test_an_unreadable_line_is_skipped_rather_than_ending_the_run(tmp_path: Path) -> None:
    """FR-011, and the reason `session_started` reads the same file the same way.

    A truncated write must not halt a run that is working, and must not hide a
    stall either — the lines on either side are compared as neighbours.
    """
    agent_dir = _log(
        tmp_path,
        _pass("clarify", "aaa", "2026-09-10T10:00:00Z"),
        "{not json at all",
        _pass("clarify", "aaa", "2026-09-10T10:01:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:02:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:03:00Z"),
    )
    found = find_stall(agent_dir)
    assert found is not None
    assert found.passes == STALL_AFTER


def test_a_legacy_double_written_history_never_produces_a_stall(tmp_path: Path) -> None:
    """Older wfctl wrote two resume lines per pass at one timestamp.

    Verified in the `59-deployment-key-metadata` log. They need no special
    handling because they predate the digest field, so the run breaks at them
    regardless — and the collapse rule written for them cost real observations
    the moment a loop turned twice inside a second.
    """
    legacy = [
        {"ts": "2026-09-10T10:00:00Z", "event": "resume", "branch": "a", "step": "clarify"},
        {"ts": "2026-09-10T10:00:00Z", "event": "resume", "step": "clarify",
         "command": "/clarify", "auto": True},
    ] * 3
    assert find_stall(_log(tmp_path, *legacy)) is None


def test_four_observations_inside_one_second_still_count(tmp_path: Path) -> None:
    """A loop fast enough to turn twice in a second must not lose passes.

    The regression the timestamp-collapse rule caused: the end-to-end test drove
    four real resumes inside one second, they counted as two, and the bound never
    fired while every hand-seeded test stayed green.
    """
    agent_dir = _log(
        tmp_path,
        *[_pass("clarify", "aaa", "2026-09-10T10:00:00Z") for _ in range(4)],
    )
    found = find_stall(agent_dir)
    assert found is not None
    assert found.passes == STALL_AFTER


def test_passes_carrying_no_digest_are_never_a_stall(tmp_path: Path) -> None:
    """Every line written before this change lacks one, and cannot be compared.

    Reading their absence as equality would stop a run on the strength of history
    that recorded nothing about what it saw.
    """
    agent_dir = _log(
        tmp_path,
        _pass("clarify", None, "2026-09-10T10:00:00Z"),
        _pass("clarify", None, "2026-09-10T10:01:00Z"),
        _pass("clarify", None, "2026-09-10T10:02:00Z"),
    )
    assert find_stall(agent_dir) is None


def test_a_branch_with_no_event_log_is_not_a_stall(tmp_path: Path) -> None:
    """The first report on a fresh worktree reads a directory with no log in it."""
    assert find_stall(tmp_path) is None


def _events(agent_dir: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in (agent_dir / "events.jsonl").read_text().splitlines()
        if line.strip()
    ]


def _resumes(agent_dir: Path) -> list[dict]:
    return [e for e in _events(agent_dir) if e.get("event") == "resume"]


def test_resume_writes_a_digest_and_it_moves_when_an_artifact_does(storyctl_dir) -> None:
    """The write side, which nothing else in this file reaches.

    Every other test hand-seeds a log with a hardcoded `digest` key, so renaming
    the field in `cli.py` leaves them all green while the bound is inert. This is
    the test that fails if the event stops carrying what `find_stall` reads.
    """
    from typer.testing import CliRunner

    from wfctl.cli import app

    runner = CliRunner()
    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    assert runner.invoke(app, ["start"]).exit_code == 0

    assert runner.invoke(app, ["resume"]).exit_code == 0
    first = _resumes(storyctl_dir.agent_dir)[-1]
    assert "digest" in first, "resume must record what this pass saw"

    (storyctl_dir.spec_dir / "tasks.md").write_text("- [x] T001 done\n- [ ] T002 open\n")
    assert runner.invoke(app, ["resume"]).exit_code == 0
    assert _resumes(storyctl_dir.agent_dir)[-1]["digest"] != first["digest"]


def test_the_bound_fires_end_to_end_through_the_real_commands(storyctl_dir) -> None:
    """`resume` four times with nothing touched, then `status` reports the stall.

    The path a stuck loop actually takes, with no log hand-written by the test —
    the spec's Validation Strategy asks for the bound to be watched firing rather
    than asserted about.
    """
    from typer.testing import CliRunner

    from wfctl.cli import app

    runner = CliRunner()
    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    assert runner.invoke(app, ["start"]).exit_code == 0
    for _ in range(4):
        assert runner.invoke(app, ["resume"]).exit_code == 0

    out = runner.invoke(app, ["status"]).output
    assert "was attempted 3 times and changed nothing" in out
    assert "unchanged (outside quoted blocks)" in out
    assert "this needs a person" in out


def test_the_stall_clears_when_the_work_moves(storyctl_dir) -> None:
    """The screen a person reads straight after doing what the stall asked for."""
    from typer.testing import CliRunner

    from wfctl.cli import app

    runner = CliRunner()
    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    assert runner.invoke(app, ["start"]).exit_code == 0
    for _ in range(4):
        assert runner.invoke(app, ["resume"]).exit_code == 0
    assert "changed nothing" in runner.invoke(app, ["status"]).output

    (storyctl_dir.spec_dir / "tasks.md").write_text("- [x] T001 done\n- [ ] T002 open\n")
    assert "changed nothing" not in runner.invoke(app, ["status"]).output


def test_the_json_payload_carries_the_verdict_as_null_when_progressing(storyctl_dir) -> None:
    """Present-and-null, never omitted, for `notify`'s reason (FR-004).

    `speckit-orchestrate` branches on this key. A consumer reading its absence as
    "not stalled" cannot tell that from a wfctl too old to count the passes.
    """
    from typer.testing import CliRunner

    from wfctl.cli import app

    runner = CliRunner()
    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    assert runner.invoke(app, ["start"]).exit_code == 0
    assert runner.invoke(app, ["resume"]).exit_code == 0

    payload = json.loads(runner.invoke(app, ["status", "--json"]).output)
    assert "stall" in payload
    assert payload["stall"] is None


def test_the_json_payload_carries_the_verdict_body_when_stalled(storyctl_dir) -> None:
    """The populated shape orchestrate reads, which the null case cannot pin."""
    from typer.testing import CliRunner

    from wfctl.cli import app

    runner = CliRunner()
    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    assert runner.invoke(app, ["start"]).exit_code == 0
    for _ in range(4):
        assert runner.invoke(app, ["resume"]).exit_code == 0

    stall = json.loads(runner.invoke(app, ["status", "--json"]).output)["stall"]
    assert stall["step"] == "implement"
    assert stall["passes"] == STALL_AFTER
    assert stall["unchanged"] == ["spec.md", "plan.md", "tasks.md"]
