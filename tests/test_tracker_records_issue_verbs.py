"""Tracker writes reach the tracker, and each one says what it did (#384).

The grant #280 put in front of `comment`, `create` and `label` refused the one
person it deferred to — on #371 an attended session was refused after the
maintainer said "file it" — and the host's permission layer was already refusing
the same commands on its own. So nothing in wfctl stands between a tracker verb
and the tracker now, and the tests here pin that from the only side that proves
it: the backend ran.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from wfctl import _tracker

WRITES = ["comment", "create", "label"]


def _backend(root: Path, marker: Path) -> None:
    """A backend whose every verb records that it ran.

    An exit code of 0 would also come back from a repo with no such verb, so the
    marker file is what separates "reached the tracker" from "skipped quietly".
    """
    (root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "fake"}))
    trackers = root / ".agents" / "trackers"
    trackers.mkdir(parents=True, exist_ok=True)
    argv = ["sh", "-c", f"echo ran >> {marker}"]
    (trackers / "fake.json").write_text(json.dumps({"verbs": {
        "comment": argv, "create": argv, "label": argv, "close": argv,
        "view": argv, "list": argv, "start": argv, "stop": argv,
    }}))


def _ran(marker: Path) -> int:
    return len(marker.read_text().splitlines()) if marker.exists() else 0


@pytest.mark.parametrize("branch", ["418-storyctl", "main"])
def test_a_run_nobody_granted_anything_reaches_the_tracker(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], branch: str,
) -> None:
    """The default state of every branch, trunk included.

    The trunk is parametrized because it was the one branch the grant could never
    be lifted on — a refusal there had no remedy at all — so it is where a
    leftover trunk check would survive unnoticed by a feature-branch test.
    """
    monkeypatch.setenv("WFCTL_BRANCH", branch)
    marker = tmp_path / "ran.log"
    _backend(storyctl_dir.repo_root, marker)
    for verb in WRITES:
        assert _tracker.dispatch(
            storyctl_dir.agent_dir, storyctl_dir.repo_root, branch, verb, {"id": "418"},
        ) == 0, verb
    assert _ran(marker) == len(WRITES)
    out = capsys.readouterr().out
    assert "nobody allowed it" not in out
    assert "--allow-notify" not in out


def _actions(agent_dir: Path) -> list[str]:
    log = agent_dir / "events.jsonl"
    if not log.exists():
        return []
    return [
        e["action"] for e in map(json.loads, log.read_text().splitlines())
        if e.get("event") == "notify-action"
    ]


def test_each_write_is_recorded_under_the_name_a_block_is_filed_against(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path,
) -> None:
    """`384-an-action-is-named-by-the-verb-that-takes-it`. The skills file
    `report-block issue-create`; this used to record bare `create`, and `close`
    recorded nothing — so a retry that worked never lifted its own hold."""
    _backend(storyctl_dir.repo_root, tmp_path / "ran.log")
    for verb in [*WRITES, "close"]:
        _tracker.dispatch(
            storyctl_dir.agent_dir, storyctl_dir.repo_root, "418-storyctl", verb, {"id": "418"},
        )
    assert _actions(storyctl_dir.agent_dir) == [
        "issue-comment", "issue-create", "issue-label", "issue-close",
    ]


def test_board_moves_and_reads_record_no_action(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path,
) -> None:
    """`start` and `stop` run from worktree hooks, and nothing files a block
    against them; recording them would put a board move into every restarted
    session's handoff. Reads were never actions."""
    _backend(storyctl_dir.repo_root, tmp_path / "ran.log")
    for verb in ("start", "stop", "view", "list"):
        _tracker.dispatch(
            storyctl_dir.agent_dir, storyctl_dir.repo_root, "418-storyctl", verb, {"id": "418"},
        )
    assert _actions(storyctl_dir.agent_dir) == []


def test_a_failed_write_records_nothing(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A write that exited non-zero told nobody anything, and recording it would
    lift a hold on an action that is still not done."""
    root = storyctl_dir.repo_root
    (root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "fake"}))
    trackers = root / ".agents" / "trackers"
    trackers.mkdir(parents=True, exist_ok=True)
    (trackers / "fake.json").write_text(json.dumps({"verbs": {"create": ["false"]}}))
    assert _tracker.dispatch(storyctl_dir.agent_dir, root, "418-storyctl", "create", {}) != 0
    assert _actions(storyctl_dir.agent_dir) == []


@pytest.mark.parametrize("verb", ["create", "close"])
def test_a_successful_retry_lifts_the_hold_its_refusal_filed(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path, verb: str,
) -> None:
    """The end-to-end form of the naming decision: file the block the way the
    skills do, let the retry succeed, and the step is no longer held — with
    nobody typing a release."""
    from typer.testing import CliRunner

    from wfctl.cli import app

    runner = CliRunner()
    storyctl_dir.stage_upstream_of("tasks")
    runner.invoke(app, ["report-block", f"issue-{verb}", "--reason", "host refused"])
    held = json.loads(runner.invoke(app, ["status", "--json"]).output)
    assert any(s["reason"] == "host refused" for s in held["steps"])

    _backend(storyctl_dir.repo_root, tmp_path / "ran.log")
    assert _tracker.dispatch(
        storyctl_dir.agent_dir, storyctl_dir.repo_root, "418-storyctl", verb, {"id": "418"},
    ) == 0

    after = json.loads(runner.invoke(app, ["status", "--json"]).output)
    assert not any(s["reason"] == "host refused" for s in after["steps"])


def test_a_leftover_grant_file_changes_nothing(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path,
) -> None:
    """A worktree that once ran `wfctl start --deny-notify` still has its
    `notify.json`. Nothing reads it now, and nothing deletes it either — a file
    in someone's state dir is theirs — so the check is that a `denied` one
    neither stops a write nor shows up in `status`."""
    from typer.testing import CliRunner

    from wfctl.cli import app

    runner = CliRunner()
    marker = tmp_path / "ran.log"
    _backend(storyctl_dir.repo_root, marker)
    before = runner.invoke(app, ["status"]).output

    (storyctl_dir.agent_dir / "notify.json").write_text(
        json.dumps({"state": "denied", "source": "local", "branch": "418-storyctl"})
    )
    assert _tracker.dispatch(
        storyctl_dir.agent_dir, storyctl_dir.repo_root, "418-storyctl", "create", {"id": "418"},
    ) == 0
    assert _ran(marker) == 1
    assert runner.invoke(app, ["status"]).output == before
