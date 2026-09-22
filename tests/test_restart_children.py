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
