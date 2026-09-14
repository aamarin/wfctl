"""The event layer `wfctl blocked` reads and writes (#364).

Nothing here touches the CLI or the pipeline — that is `test_blocked_cli.py`
and `test_blocked_holds_step.py`. This file is the three functions in
`_session.py` alone: writing a block, writing a clearing, and reading the
standing set back.
"""
from __future__ import annotations

import types

from wfctl._session import (
    record_block_cleared,
    record_blocked,
    record_notify_action,
    standing_blocks,
)


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


def test_a_clearing_event_carries_no_reason_and_no_step(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-013. A clearing asserts one fact — a person took the action — and
    carries nothing else: no reason to restate, no step of its own to name."""
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "host refused it", "decompose"
    )
    record_block_cleared(storyctl_dir.agent_dir, "418-storyctl", "issue-comment")
    log = (storyctl_dir.agent_dir / "events.jsonl").read_text()
    assert '"event": "block-cleared"' in log
    assert '"reason"' not in log.split('"event": "block-cleared"')[1].split("\n")[0]
    assert standing_blocks(storyctl_dir.agent_dir, "418-storyctl") == []


def test_the_most_recent_event_for_an_action_is_the_one_that_stands(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-012. Three kinds share one action-keyed timeline — blocked,
    block-cleared, notify-action — and whichever is most recent for an action
    decides its state, whatever came before it."""
    branch = "418-storyctl"
    agent_dir = storyctl_dir.agent_dir

    # blocked, then cleared: released.
    record_blocked(agent_dir, branch, "issue-comment", "first refusal", "decompose")
    record_block_cleared(agent_dir, branch, "issue-comment")
    assert standing_blocks(agent_dir, branch) == []

    # blocked again after the clearing: standing once more, later reason wins.
    record_blocked(agent_dir, branch, "issue-comment", "second refusal", "decompose")
    blocks = standing_blocks(agent_dir, branch)
    assert len(blocks) == 1
    assert blocks[0].reason == "second refusal"

    # a later notify-action for the same action releases it for free (FR-020).
    record_notify_action(agent_dir, "issue-comment")
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
