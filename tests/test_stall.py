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


def test_three_passes_with_the_evidence_unchanged_is_a_stall(tmp_path: Path) -> None:
    """The defect in #332: the same step, the same inputs, no reason to stop."""
    agent_dir = _log(
        tmp_path,
        _pass("clarify", "aaa", "2026-09-10T10:00:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:01:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:02:00Z"),
    )
    found = find_stall(agent_dir)
    assert found is not None
    assert found.step == "clarify"
    assert found.passes == STALL_AFTER


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
    )
    assert find_stall(agent_dir) is None


def test_two_unchanged_passes_are_not_yet_a_stall(tmp_path: Path) -> None:
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
    )
    found = find_stall(agent_dir)
    assert found is not None
    assert found.passes == STALL_AFTER


def test_the_legacy_double_write_counts_as_one_pass(tmp_path: Path) -> None:
    """Older wfctl wrote two resume lines per pass sharing a timestamp.

    Verified in the `59-deployment-key-metadata` log. Counting them separately
    would fire the bound a pass early on any branch carrying that history.
    """
    agent_dir = _log(
        tmp_path,
        _pass("clarify", "aaa", "2026-09-10T10:00:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:00:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:01:00Z"),
        _pass("clarify", "aaa", "2026-09-10T10:01:00Z"),
    )
    assert find_stall(agent_dir) is None


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


def _seed(agent_dir: Path, step: str, marks: list[str]) -> None:
    """A started session, then one resume line per pass."""
    lines = [json.dumps({"ts": "2026-09-10T09:00:00Z", "event": "start", "step": step})]
    lines += [
        json.dumps(_pass(step, mark, f"2026-09-10T10:0{i}:00Z"))
        for i, mark in enumerate(marks)
    ]
    (agent_dir / "events.jsonl").write_text("\n".join(lines) + "\n")


def test_status_names_the_repeated_step_and_what_did_not_move(storyctl_dir, monkeypatch) -> None:
    """A run that halts silently is a run that looks finished (#332).

    The stopping is the interesting half and the reporting is the half that gets
    dropped, so this asserts on the sentence a person actually reads — not only
    that inference reached the verdict.
    """
    from typer.testing import CliRunner

    from wfctl.cli import app

    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    _seed(storyctl_dir.agent_dir, "implement", ["aaa", "aaa", "aaa"])

    out = CliRunner().invoke(app, ["status"]).output
    assert "implement ran 3 times and changed nothing" in out
    assert "unchanged: spec.md, plan.md, tasks.md" in out
    assert "this needs a person" in out


def test_status_says_nothing_about_a_run_that_is_progressing(storyctl_dir) -> None:
    """The line must not become furniture a reader learns to skip past."""
    from typer.testing import CliRunner

    from wfctl.cli import app

    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    _seed(storyctl_dir.agent_dir, "implement", ["aaa", "bbb", "ccc"])

    out = CliRunner().invoke(app, ["status"]).output
    assert "changed nothing" not in out


def test_the_json_payload_carries_the_verdict_as_null_when_progressing(storyctl_dir) -> None:
    """Present-and-null, never omitted, for `notify`'s reason (FR-004).

    `speckit-orchestrate` branches on this key. A consumer reading its absence as
    "not stalled" cannot tell that from a wfctl too old to count the passes.
    """
    from typer.testing import CliRunner

    from wfctl.cli import app

    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    _seed(storyctl_dir.agent_dir, "implement", ["aaa", "bbb"])

    payload = json.loads(CliRunner().invoke(app, ["status", "--json"]).output)
    assert "stall" in payload
    assert payload["stall"] is None
