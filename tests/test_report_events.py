"""The event layer `wfctl report-block` and `report-action` write (#364, #384).

Nothing here touches the CLI or the pipeline — that is `test_report_verbs.py`
and `test_report_block_holds_step.py`. This file is the two writers in
`_session.py` and the reader of the standing set, including the `block-cleared`
lines logs from before #384 still carry.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

from wfctl._session import record_blocked, record_outward_action, standing_blocks


def _old_clear(agent_dir: Path, branch: str, action: str) -> None:
    """A `block-cleared` line as `wfctl blocked --clear` wrote it before #384.

    Written by hand because nothing writes one any more — which is exactly the
    case worth pinning: a log that carries one has to keep reading as released.
    """
    with open(agent_dir / "events.jsonl", "a") as f:
        f.write(json.dumps({
            "ts": "2026-09-01T00:00:00Z", "event": "block-cleared",
            "branch": branch, "action": action,
        }) + "\n")


def test_a_block_event_carries_the_step_it_was_reported_on(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-010. The step travels with the block, because a hold applied later
    from whatever is current at read time would move onto a step the pipeline
    has since advanced past — a different claim, and a wrong one."""
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "host refused it", "decompose"
    )
    blocks = standing_blocks(storyctl_dir.agent_dir, "418-storyctl")
    assert len(blocks) == 1
    assert blocks[0].action == "issue-comment"
    assert blocks[0].reason == "host refused it"
    assert blocks[0].step == "decompose"


def test_a_clearing_written_before_the_verb_was_removed_still_releases(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`--clear` went with #384 and its event did not go with it. Dropped from
    the reader, every block cleared in an existing log would come back to hold a
    step nobody is working on — with no verb left that writes the clearing."""
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "host refused it", "decompose"
    )
    _old_clear(storyctl_dir.agent_dir, "418-storyctl", "issue-comment")
    assert standing_blocks(storyctl_dir.agent_dir, "418-storyctl") == []


def test_the_most_recent_event_for_an_action_is_the_one_that_stands(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Three kinds share one action-keyed timeline — blocked, block-cleared (old
    logs), notify-action — and whichever is most recent for an action decides its
    state, whatever came before it."""
    branch = "418-storyctl"
    agent_dir = storyctl_dir.agent_dir

    # blocked, then cleared: released.
    record_blocked(agent_dir, branch, "issue-comment", "first refusal", "decompose")
    _old_clear(agent_dir, branch, "issue-comment")
    assert standing_blocks(agent_dir, branch) == []

    # blocked again after the clearing: standing once more, later reason wins.
    record_blocked(agent_dir, branch, "issue-comment", "second refusal", "decompose")
    blocks = standing_blocks(agent_dir, branch)
    assert len(blocks) == 1
    assert blocks[0].reason == "second refusal"

    # a later notify-action for the same action releases it — `report-action`,
    # or a `wfctl issue` write that succeeded on retry.
    record_outward_action(agent_dir, branch, "issue-comment")
    assert standing_blocks(agent_dir, branch) == []

    # blocked a third time, after the success: standing again.
    record_blocked(agent_dir, branch, "issue-comment", "third refusal", "decompose")
    blocks = standing_blocks(agent_dir, branch)
    assert len(blocks) == 1
    assert blocks[0].reason == "third refusal"


def test_a_block_on_one_branch_does_not_hold_a_step_on_another(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-021. A state dir shared across worktrees holds every branch's
    events, and `standing_blocks` must not read another branch's block as its
    own."""
    agent_dir = storyctl_dir.agent_dir
    record_blocked(agent_dir, "418-storyctl", "issue-comment", "refused here", "decompose")
    assert standing_blocks(agent_dir, "999-other-branch") == []
    assert len(standing_blocks(agent_dir, "418-storyctl")) == 1


def test_a_success_on_one_branch_does_not_lift_a_hold_on_another(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The release half of the test above, and the half that was missing.

    Recording a tracker write as `issue-<verb>` made the two sides share a
    vocabulary for the first time, so a branchless release started matching
    holds the skills had filed — a successful `wfctl issue create` in one
    worktree silently cleared another branch's hold, and its step read done with
    the refused write never made.
    """
    agent_dir = storyctl_dir.agent_dir
    record_blocked(agent_dir, "418-storyctl", "issue-create", "host refused", "decompose")
    record_outward_action(agent_dir, "999-other-branch", "issue-create")

    blocks = standing_blocks(agent_dir, "418-storyctl")
    assert len(blocks) == 1
    assert blocks[0].reason == "host refused"


def test_a_release_written_before_branches_were_recorded_still_lifts_its_hold(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A `notify-action` line in a log written before #384 carries no branch,
    and `standing_blocks` reads a missing field as matching every branch. That
    stays true so an old log's release is not resurrected as a hold nobody is
    working on — the narrow cost of which is the test above's scenario, which
    could only arise from a log old enough to predate the names agreeing."""
    agent_dir = storyctl_dir.agent_dir
    record_blocked(agent_dir, "418-storyctl", "push", "host refused", "implement")
    with open(agent_dir / "events.jsonl", "a") as f:
        f.write(
            '{"ts": "2026-01-01T00:00:00Z", "event": "notify-action", "action": "push"}\n'
        )

    assert standing_blocks(agent_dir, "418-storyctl") == []


def test_a_non_string_step_field_is_dropped_rather_than_crashing_the_reader(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`_apply_block_hold` keys a dict on `.step`, so a `step` that survived
    `json.loads` as a list — a hand-edited or externally corrupted line, valid
    JSON but not the shape this file ever writes — must not reach it as an
    unhashable value. Same contract `action` above is already held to."""
    agent_dir = storyctl_dir.agent_dir
    with open(agent_dir / "events.jsonl", "a") as f:
        f.write(
            '{"ts": "2026-01-01T00:00:00Z", "event": "blocked", "branch": '
            '"418-storyctl", "action": "push", "reason": "x", "step": ["bad"]}\n'
        )

    blocks = standing_blocks(agent_dir, "418-storyctl")
    assert len(blocks) == 1
    assert blocks[0].step is None


def test_a_truncated_final_line_is_skipped_rather_than_crashing_the_reader(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Every command appends here, so a write cut off mid-line must not decide
    whether a step is held by raising instead of answering."""
    agent_dir = storyctl_dir.agent_dir
    record_blocked(agent_dir, "418-storyctl", "issue-comment", "refused", "decompose")
    events = agent_dir / "events.jsonl"
    with open(events, "a") as f:
        f.write('{"ts": "2026-01-01T00:00:00Z", "event": "blocked", "branch": "418-sto')

    blocks = standing_blocks(agent_dir, "418-storyctl")
    assert len(blocks) == 1
    assert blocks[0].action == "issue-comment"
