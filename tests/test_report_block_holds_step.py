"""A standing block holds the step it named, and releases both ways (#364).

The event layer is `test_report_events.py`; the command surface is
`test_report_verbs.py`. This file is the pipeline effect alone: does a block
override a step's own reading, does it avoid cascading past itself, and does
each release path put the step back where its own artifacts leave it.
"""
from __future__ import annotations

import json
import types

from typer.testing import CliRunner

from wfctl._session import record_blocked, record_outward_action
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
    payload gains no new top-level key and no new step field.

    `sub_steps` is the one exception, added by #339 for every step alike —
    always present and empty for the seven with nothing to split — so it is
    named here rather than making this test read as broken by that feature.
    """
    storyctl_dir.stage_upstream_of("tasks")
    before_keys = set(_payload().keys())

    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused", "decompose",
    )

    payload = _payload()
    assert set(payload.keys()) == before_keys
    held = next(s for s in payload["steps"] if s["name"] == "decompose")
    assert held["state"] in ("done", "in_progress", "pending", "skipped")
    assert set(held.keys()) == {
        "name", "state", "annotation", "reason", "remedy", "is_current", "sub_steps",
    }


def test_two_actions_blocked_against_the_same_step_report_the_latest(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Two different actions can each be refused while the same step is
    current. The report must show whichever was filed most recently, not
    whichever `standing_blocks` happens to have seen first — a dict keyed
    only on step name silently drops the other one either way, but dropping
    the *newer* block would leave a cleared, months-old reason on screen
    after a person had already dealt with it."""
    storyctl_dir.stage_upstream_of("tasks")
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "push", "refused push", "decompose",
    )
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused comment",
        "decompose",
    )

    held = next(s for s in _payload()["steps"] if s["name"] == "decompose")
    assert held["reason"] == "refused comment"

    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "push", "refused push again", "decompose",
    )

    held = next(s for s in _payload()["steps"] if s["name"] == "decompose")
    assert held["reason"] == "refused push again"


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
    assert "report-action" not in payload["next_command"]
    assert payload["next_command"] == "/speckit.decompose"


def test_a_block_on_implement_with_tasks_still_open_routes_back_to_implement(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A host block filed mid-implementation holds `implement` the same way a
    failed verification does, but re-running implement is exactly what a
    mid-task block needs — `next_step_content`'s "every task is already
    ticked" reasoning for routing a blocked `implement` to `wfctl verify`
    does not hold with a task still open, and the routing used to ignore
    that and send the agent to verify an unfinished tree regardless."""
    storyctl_dir.stage_upstream_of("tasks", tasks="- [x] T001 done\n- [ ] T002 open\n")
    assert next(s for s in _payload()["steps"] if s["name"] == "implement")["state"] \
        == "in_progress"

    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused", "implement",
    )

    payload = _payload()
    held = next(s for s in payload["steps"] if s["name"] == "implement")
    assert held["state"] == "in_progress"
    assert held["reason"] == "refused"
    assert payload["next_command"] == "/speckit.implement"


def test_the_remedy_names_the_host_and_the_releasing_command(
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
    assert "wfctl report-action issue-comment" in held["remedy"]


def test_the_remedy_shell_quotes_a_multi_word_action(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`action` is accepted as free text (`wfctl report-block "issue comment"
    --reason refused` is a legal call), so the printed remedy must be too —
    an unquoted copy-paste either fails Typer's parsing or, for a value
    carrying shell metacharacters, runs something other than the release it
    was meant to."""
    storyctl_dir.stage_upstream_of("tasks")
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue comment", "refused", "decompose",
    )
    held = next(s for s in _payload()["steps"] if s["name"] == "decompose")
    assert "wfctl report-action 'issue comment'" in held["remedy"]


def test_a_later_success_for_the_same_action_releases_the_hold(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A retry that succeeded through `wfctl issue` writes `notify-action` for
    itself, so the release costs nothing further and needs no clearing step."""
    storyctl_dir.stage_upstream_of("tasks")
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused", "decompose",
    )
    assert next(s for s in _payload()["steps"] if s["name"] == "decompose")["state"] \
        == "in_progress"

    record_outward_action(storyctl_dir.agent_dir, "418-storyctl", "issue-comment")

    assert next(s for s in _payload()["steps"] if s["name"] == "decompose")["state"] \
        == "done"


def test_a_block_after_a_success_holds_again(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The reverse order of the test above (FR-012): a success does not
    permanently exempt an action from ever being reported blocked again."""
    storyctl_dir.stage_upstream_of("tasks")
    record_outward_action(storyctl_dir.agent_dir, "418-storyctl", "issue-comment")
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused later", "decompose",
    )
    held = next(s for s in _payload()["steps"] if s["name"] == "decompose")
    assert held["state"] == "in_progress"
    assert held["reason"] == "refused later"


def test_next_step_md_carries_the_hold_the_same_as_status(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`next` used to infer steps without applying the block hold, so
    `next-step.md` — the file an agent actually reads — sent it straight back
    to the refused step with no `why:`/`how:`, while `status` (which does
    apply the hold) showed the block. The two views must agree."""
    storyctl_dir.stage_upstream_of("tasks")
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused", "decompose",
    )

    held = next(s for s in _payload()["steps"] if s["name"] == "decompose")
    assert held["state"] == "in_progress"

    runner.invoke(app, ["next"])
    content = (storyctl_dir.agent_dir / "next-step.md").read_text()
    assert "why: refused" in content
    assert "wfctl report-action issue-comment" in content
