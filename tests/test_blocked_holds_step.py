"""A standing block holds the step it named, and releases both ways (#364).

The event layer is `test_blocked_events.py`; the command surface is
`test_blocked_cli.py`. This file is the pipeline effect alone: does a block
override a step's own reading, does it avoid cascading past itself, and does
each release path put the step back where its own artifacts leave it.
"""
from __future__ import annotations

import json
import types

from typer.testing import CliRunner

from wfctl._predicates import block_reason
from wfctl._session import record_block_cleared, record_blocked, record_notify_action
from wfctl.cli import app

runner = CliRunner()


def _payload() -> dict:
    return json.loads(runner.invoke(app, ["status", "--json"]).output)


def test_a_block_holds_a_step_whose_own_artifacts_read_done(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The whole claim of the level-2 record — a refused tracker write and a
    successful one leave byte-identical state on disk — stated as the
    assertion that fails if the hold is ever wired as a predicate `implement`
    alone consults. Asserted on the `--json` payload."""
    storyctl_dir.stage_upstream_of("tasks")

    before = next(s for s in _payload()["steps"] if s["name"] == "decompose")
    assert before["state"] == "done"

    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment",
        "host classifier: External System Writes", "decompose",
    )

    held = next(s for s in _payload()["steps"] if s["name"] == "decompose")
    assert held["state"] == "in_progress"
    assert held["reason"] == "host classifier: External System Writes"
    assert held["is_current"] is True


def test_holding_a_done_step_does_not_cascade_the_steps_after_it(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`_infer_steps` sets `cascade = True` on the first `pending` step in its
    own loop; the hold is applied after that loop returns, and must not force
    a legitimately-`done` later step back to `pending` the way a `pending`
    reading inside the loop would."""
    storyctl_dir.stage_upstream_of("tasks")

    record_blocked(storyctl_dir.agent_dir, "418-storyctl", "push", "refused", "plan")

    by_name = {s["name"]: s for s in _payload()["steps"]}
    assert by_name["plan"]["state"] == "in_progress"
    assert by_name["tasks"]["state"] == "done"
    assert by_name["analyze"]["state"] == "done"
    assert by_name["decompose"]["state"] == "done"


def test_a_held_step_adds_no_new_state_name_and_no_new_payload_key(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-018. A held step is `in_progress` with the reason on its annotation
    and reason fields — the shape `verification_block` already uses — and the
    payload gains no new top-level key and no new step field."""
    storyctl_dir.stage_upstream_of("tasks")
    before_keys = set(_payload().keys())

    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused", "decompose",
    )

    payload = _payload()
    assert set(payload.keys()) == before_keys
    held = next(s for s in payload["steps"] if s["name"] == "decompose")
    assert held["state"] in ("done", "in_progress", "pending", "skipped")
    assert set(held.keys()) == {"name", "state", "annotation", "reason", "remedy", "is_current"}


def test_block_reason_answers_for_the_step_the_block_named(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Shaped after `verification_block`: the first matching reason, or `None`
    for a step nothing blocks."""
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused", "decompose",
    )
    assert block_reason(storyctl_dir.agent_dir, "418-storyctl", "decompose") == "refused"
    assert block_reason(storyctl_dir.agent_dir, "418-storyctl", "implement") is None


def test_the_next_action_for_a_held_step_is_the_steps_own_command(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-016. A `next` that named the release would tell an unattended agent
    to clear its own hold — the one thing the asymmetry exists to prevent. The
    release lives in the remedy, addressed to a person."""
    storyctl_dir.stage_upstream_of("tasks")
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused", "decompose",
    )
    payload = _payload()
    assert payload["current"] == "decompose"
    assert "blocked" not in payload["next_command"]
    assert "clear" not in payload["next_command"]
    assert payload["next_command"] == "/speckit.decompose"


def test_the_remedy_names_the_host_and_the_clearing_command(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-015. Says the block came from the agent's host rather than from
    wfctl, that re-running the step will be refused again, and names the
    command a person runs once they have taken the action themselves."""
    storyctl_dir.stage_upstream_of("tasks")
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused", "decompose",
    )
    held = next(s for s in _payload()["steps"] if s["name"] == "decompose")
    assert held["remedy"] is not None
    assert "host" in held["remedy"]
    assert "wfctl" in held["remedy"]
    assert "wfctl blocked issue-comment --clear" in held["remedy"]


def test_a_later_success_for_the_same_action_releases_the_hold(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-020. A run that retried and succeeded already writes `notify-action`
    for itself — that release costs nothing further, with no clearing step of
    its own."""
    storyctl_dir.stage_upstream_of("tasks")
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused", "decompose",
    )
    assert next(s for s in _payload()["steps"] if s["name"] == "decompose")["state"] \
        == "in_progress"

    record_notify_action(storyctl_dir.agent_dir, "issue-comment")

    assert next(s for s in _payload()["steps"] if s["name"] == "decompose")["state"] \
        == "done"


def test_a_block_after_a_success_holds_again(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The reverse order of the test above (FR-012): a success does not
    permanently exempt an action from ever being reported blocked again."""
    storyctl_dir.stage_upstream_of("tasks")
    record_notify_action(storyctl_dir.agent_dir, "issue-comment")
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused later", "decompose",
    )
    held = next(s for s in _payload()["steps"] if s["name"] == "decompose")
    assert held["state"] == "in_progress"
    assert held["reason"] == "refused later"


def test_clearing_works_for_a_run_holding_no_grant(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-013. The path `notify-action` cannot reach — this branch never had
    `wfctl start --allow-notify` run on it — and `--clear` still releases the
    step back to its own reading."""
    storyctl_dir.stage_upstream_of("tasks")
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused", "decompose",
    )
    assert next(s for s in _payload()["steps"] if s["name"] == "decompose")["state"] \
        == "in_progress"

    record_block_cleared(storyctl_dir.agent_dir, "418-storyctl", "issue-comment")

    released = next(s for s in _payload()["steps"] if s["name"] == "decompose")
    assert released["state"] == "done"
    assert released["reason"] is None
