"""Where design approval happens, as a per-feature value (#127).

The mode is the first field on `PipelineReport` that no artifact produces — it
is a choice someone made, not a state inference read off disk. That makes two
things worth pinning that inference never needed: that it survives the commands
which run between sessions, and that losing it fails toward stopping for a
human rather than toward running without one.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

from typer.testing import CliRunner

from wfctl import _session
from wfctl.cli import app

runner = CliRunner()


def _payload(args: list[str] | None = None) -> dict:
    result = runner.invoke(app, args or ["status", "--json"])
    return json.loads(result.output)


def _events(agent_dir: Path) -> list[dict]:
    log = agent_dir / "events.jsonl"
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


def test_a_feature_nobody_granted_anything_to_reports_attended(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The default, asserted positively rather than by the absence of a key.

    `test_the_json_view_carries_the_auto_flag` records what happens otherwise:
    deleting `auto` from the payload left 824 tests green, because the one test
    reading that output compared it against itself. A round-trip assertion
    cannot see a field that vanished from both sides.
    """
    assert _payload()["auto_approve"] is False
    assert "auto-approve" not in runner.invoke(app, ["status"]).output


def test_the_flag_grants_the_mode_and_the_payload_carries_it(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Scope item 2: a run whose mode is invisible is a run you cannot trust."""
    runner.invoke(app, ["start", "--auto-approve"])

    assert _payload()["auto_approve"] is True
    assert "auto-approve" in runner.invoke(app, ["status"]).output


def test_granting_the_mode_on_a_running_session_is_not_swallowed(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The write sits above `start`'s early return, and this is why it must.

    `/start-session` runs `wfctl start` on a worktree's first turn, so by the
    time anyone types the flag the session is already recorded. Inside the
    guard, the grant would print "Already initialized" over a flag that did
    nothing — a refusal that reads as success.
    """
    runner.invoke(app, ["start"])
    assert _payload()["auto_approve"] is False

    result = runner.invoke(app, ["start", "--auto-approve"])

    assert "Already initialized" in result.output
    assert _payload()["auto_approve"] is True


def test_a_later_bare_start_does_not_revoke_the_mode(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The reason the option is tri-state rather than a plain `bool`.

    Defaulting to False would revoke the mode on every subsequent `wfctl start`
    — which `/start-session` runs at each handoff — ending an overnight run at
    its first context clear, silently and in the safe-looking direction.
    """
    runner.invoke(app, ["start", "--auto-approve"])
    runner.invoke(app, ["start"])

    assert _payload()["auto_approve"] is True


def test_the_mode_can_be_handed_back_to_a_human(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """#100's escalate-never-waive, in the direction it permits.

    An agent may raise the bar and never lower it, so revoking has to be
    reachable — a mode that could only ever be granted would make the rule
    one-way in the wrong direction.
    """
    runner.invoke(app, ["start", "--auto-approve"])
    runner.invoke(app, ["start", "--no-auto-approve"])

    assert _payload()["auto_approve"] is False


def test_each_grant_leaves_a_line_in_the_event_log(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """What makes a self-grant visible after the fact.

    `wfctl start*` is in `start-session`'s allowlist and the glob admits any
    flag, so an agent can grant itself the mode unprompted. Nothing available
    prevents that; the log is what a reader consults instead, which is why the
    file alone is not the whole store.
    """
    runner.invoke(app, ["start", "--auto-approve"])
    runner.invoke(app, ["start", "--no-auto-approve"])

    grants = [e for e in _events(storyctl_dir.agent_dir) if e["event"] == "mode"]
    assert [e["auto_approve"] for e in grants] == [True, False]
    assert all("ts" in e for e in grants)


def test_a_lost_or_damaged_mode_file_reads_as_attended(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The direction the failure has to fall.

    A truncated write or a hand-edited file must leave the design gates
    stopping for a human. Reading a damaged file as a grant would let a
    corrupted byte hand an agent the authority the flag exists to gate.
    """
    runner.invoke(app, ["start", "--auto-approve"])

    (storyctl_dir.agent_dir / _session.MODE_NAME).write_text("{not json")
    assert _payload()["auto_approve"] is False

    (storyctl_dir.agent_dir / _session.MODE_NAME).unlink()
    assert _payload()["auto_approve"] is False


def test_the_mode_survives_a_finished_story(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Why the field is outside the report's None-together pairing.

    `current`, `next_command` and `auto` are all None once every step is done,
    because there is no step left to run. The mode is still true of that story
    — it ran under one — and a reviewer reading the PR is asking exactly then.
    """
    runner.invoke(app, ["start", "--auto-approve"])
    storyctl_dir.stage_upstream_of("tasks")
    storyctl_dir.make_spec_artifact("decompose")
    (storyctl_dir.spec_dir / "checklists" / "implement-complete.md").write_text("done\n")

    payload = _payload()
    assert (payload["current"], payload["next_command"], payload["auto"]) == (None, None, None)
    assert payload["auto_approve"] is True


def test_resume_says_the_mode_on_its_own_line(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """#127's named mitigation: `auto` and `auto_approve` are different questions.

    `resume` already prints `(auto: …)` for whether this step advances
    unprompted. Folding the mode into that parenthetical is what the issue says
    will make the two read as one axis.
    """
    runner.invoke(app, ["start", "--auto-approve"])
    output = runner.invoke(app, ["resume"]).output

    assert "auto-approve" in output
    assert "(auto: false)" in output
    mode_line = next(line for line in output.splitlines() if "auto-approve" in line)
    assert "(auto:" not in mode_line
