"""Children this session launched and nothing has heard back from (#425).

The restart's second hold condition, and the one whose absence is silent. A pane
cleared while a review panel is still out loses every finding it was about to
report, and the next session cannot tell that from a panel that never ran.

Every shape here is one a real transcript in this repo produced: an async
subagent, a fork with no description of its own, a notification that arrives for
a child launched before a `/clear`, and an agent reply that quotes the
notification tags while writing about them.
"""
from __future__ import annotations

import json
from pathlib import Path

from wfctl._restart import UNNAMED_CHILD, outstanding_children


def launch(agent_id: str, description: str | None = "Review panel r1") -> str:
    """The harness's record of a child starting: a tool result carrying its id."""
    result: dict[str, object] = {
        "isAsync": True, "status": "async_launched", "agentId": agent_id,
    }
    if description is not None:
        result["description"] = description
    return json.dumps({
        "type": "user",
        "toolUseResult": result,
        "message": {"content": [{"type": "tool_result", "text": "Async agent launched"}]},
    })


def notification(agent_id: str) -> str:
    """The harness's record of that child reporting back."""
    return json.dumps({
        "type": "user",
        "message": {"content": (
            f"<task-notification>\n<task-id>{agent_id}</task-id>\n"
            "<tool-use-id>toolu_1</tool-use-id>\n</task-notification>"
        )},
    })


def absorbed(agent_id: str) -> str:
    """The same report, delivered while the session was mid-turn.

    The harness folds a notification that arrives during a running turn into that
    turn as an `attachment` instead of writing a `user` record for it. It is the
    shape a fanned-out session produces most, because a parent waiting on a panel
    is usually working while the panel reports.
    """
    return json.dumps({
        "type": "attachment",
        "attachment": {"prompt": (
            f"<task-notification>\n<task-id>{agent_id}</task-id>\n"
            "<tool-use-id>toolu_1</tool-use-id>\n</task-notification>"
        )},
    })


def transcript(tmp_path: Path, *lines: str) -> Path:
    path = tmp_path / "t.jsonl"
    path.write_text("\n".join(lines) + "\n")
    return path


def test_a_session_that_never_fanned_out_has_no_children(tmp_path: Path) -> None:
    """The overwhelming majority of sessions. A scan that found children here
    would hold every restart wfctl performs."""
    t = transcript(tmp_path, json.dumps({"type": "assistant", "message": {"usage": {}}}))
    assert outstanding_children(t) == []


def test_a_launched_child_with_no_notification_is_outstanding(tmp_path: Path) -> None:
    """The failure #425 is about, in its smallest form."""
    t = transcript(tmp_path, launch("a1"))
    assert outstanding_children(t) == ["Review panel r1"]


def test_a_child_that_reported_back_is_not_outstanding(tmp_path: Path) -> None:
    t = transcript(tmp_path, launch("a1"), notification("a1"))
    assert outstanding_children(t) == []


def test_only_the_children_still_out_are_reported(tmp_path: Path) -> None:
    """A panel reports one at a time, and the hold has to shrink with it rather
    than hold on the whole panel until the last one lands."""
    t = transcript(
        tmp_path,
        launch("a1", "reviewer r1"),
        launch("a2", "reviewer r2"),
        launch("a3", "reviewer r3"),
        notification("a2"),
    )
    assert outstanding_children(t) == ["reviewer r1", "reviewer r3"]


def test_a_child_with_no_description_still_occupies_a_row(tmp_path: Path) -> None:
    """A fork records no description. Dropping it would report zero children over
    a session that has one out, which is the hold failing open."""
    t = transcript(tmp_path, json.dumps({
        "type": "user", "toolUseResult": {"status": "forked", "agentId": "a9"},
    }))
    assert outstanding_children(t) == [UNNAMED_CHILD]


def test_a_notification_for_a_child_this_transcript_never_launched_is_ignored(
    tmp_path: Path,
) -> None:
    """A `/clear` starts a new transcript, and a child launched before it reports
    into the new one. There is nothing to hold — the launch is already gone."""
    t = transcript(tmp_path, notification("a-from-before-the-clear"))
    assert outstanding_children(t) == []


def test_an_agent_writing_about_notifications_does_not_release_the_hold(
    tmp_path: Path,
) -> None:
    """The reason the tags are matched structurally rather than in the raw line.
    This branch's own session put `<task-id>` into an assistant reply while
    building the scanner; a substring read would have cleared its own hold."""
    quoted = json.dumps({
        "type": "assistant",
        "message": {"content": [{
            "type": "text",
            "text": "the completion arrives as <task-notification><task-id>a1</task-id>",
        }]},
    })
    t = transcript(tmp_path, launch("a1"), quoted)
    assert outstanding_children(t) == ["Review panel r1"]


def test_a_torn_final_line_does_not_lose_the_launches_before_it(tmp_path: Path) -> None:
    """The harness appends while the hook reads. A half-written last line must
    leave the children already on record outstanding, not raise."""
    path = tmp_path / "t.jsonl"
    path.write_text(launch("a1") + "\n" + '{"type": "user", "toolUseRes')
    assert outstanding_children(path) == ["Review panel r1"]


def test_an_unreadable_transcript_reports_no_children(tmp_path: Path) -> None:
    """Holding on a file that cannot be opened would hold the branch's every
    restart with nothing able to release it. `occupancy` already decides
    *nothing* on the same file, so the hook never reaches this reading."""
    assert outstanding_children(tmp_path / "missing.jsonl") == []


def test_a_child_that_reported_mid_turn_is_not_outstanding(tmp_path: Path) -> None:
    """The shape the first reader missed, and the one that made this hold
    permanent: every notification arriving while the parent was working read as
    no report at all, so the pane held past its threshold with no way out. Two
    independent reviewers measured 200 of 489 launches in this repo's own
    transcripts reading as outstanding, 141 of which had reported."""
    t = transcript(tmp_path, launch("a1"), absorbed("a1"))
    assert outstanding_children(t) == []


def test_a_queued_notification_alone_does_not_release_the_hold(tmp_path: Path) -> None:
    """A queued item can be removed unsent — `resume_failed` in the corpus — so a
    queue record is not evidence the session ever saw the report. Releasing on one
    would clear a pane with a child still out, which is #425's own failure."""
    queued = json.dumps({
        "type": "queue-operation",
        "operation": "enqueue",
        "content": (
            "<task-notification>\n<task-id>a1</task-id>\n"
            "<tool-use-id>toolu_1</tool-use-id>\n</task-notification>"
        ),
    })
    t = transcript(tmp_path, launch("a1"), queued)
    assert outstanding_children(t) == ["Review panel r1"]


def test_a_prompt_snapshot_quoting_a_notification_does_not_release_the_hold(
    tmp_path: Path,
) -> None:
    """The near miss beside the shape above. A `prompt_snapshot` attachment
    carries whatever the turn's prompt held, which for this branch includes
    sessions discussing notifications — two such records sit in the transcript
    this fix was measured on. It is an attachment with a `prompt`, and only the
    requirement that the tag be the *whole* of it keeps the two apart."""
    snapshot = json.dumps({
        "type": "attachment",
        "attachment": {"type": "prompt_snapshot", "prompt": (
            "Here is what a report looks like: <task-notification>\n"
            "<task-id>a1</task-id>\n</task-notification>"
        )},
    })
    t = transcript(tmp_path, launch("a1"), snapshot)
    assert outstanding_children(t) == ["Review panel r1"]
