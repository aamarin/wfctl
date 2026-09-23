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
    no report at all, so the pane held past its threshold with no way out. Of 496
    launches across this repo's 325 session transcripts, 207 read as outstanding
    under the first reader and 148 of those had in fact reported."""
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


def test_a_typed_prompt_quoting_a_notification_does_not_release_the_hold(
    tmp_path: Path,
) -> None:
    """The near miss beside the shape above, in the shape that actually occurs.

    `queued_command` is the only attachment type in 1512 transcripts that carries
    a `prompt` string, and a person can type one that quotes a report — asking
    about the notification they just saw. The quote lands mid-sentence, which is
    what separates it from a delivery: a delivery opens a line.

    This test replaces one built on a `prompt_snapshot` carrying a `prompt`. No
    such record exists — 0 of 1898 snapshots have that key, so the test passed
    over a shape the harness never writes and the branch it named was never the
    one keeping the two apart.
    """
    typed = json.dumps({
        "type": "attachment",
        "attachment": {"type": "queued_command", "prompt": (
            "what does it mean when I get a <task-notification>\n"
            "<task-id>a1</task-id>\n</task-notification>"
        )},
    })
    t = transcript(tmp_path, launch("a1"), typed)
    assert outstanding_children(t) == ["Review panel r1"]


def test_a_delivery_behind_the_harness_caution_paragraph_releases_the_hold(
    tmp_path: Path,
) -> None:
    """The second way a real report was thrown away, and the reason the reader is
    anchored to a line rather than to the start of the string.

    The harness prefixes some deliveries with a caution telling the model not to
    read the notification as something the user said. The tag then begins 494
    characters in, and a reader requiring it to open the whole string discarded
    the record together with the `<task-id>` that was the only reason to read it.
    35 such deliveries sit in the corpus, against 4 prose mentions — and the two
    separate cleanly on whether the tag opens its line.
    """
    prefixed = json.dumps({
        "type": "user",
        "message": {"content": (
            "[SYSTEM NOTIFICATION - NOT USER INPUT]\n"
            "This is an automated background-task event, NOT a message from the "
            "user.\n\n"
            "<task-notification>\n<task-id>a1</task-id>\n</task-notification>"
        )},
    })
    t = transcript(tmp_path, launch("a1"), prefixed)
    assert outstanding_children(t) == []


def resume(agent_id: str) -> str:
    """The harness's record of a reported child being sent back to work.

    Not a second launch. It carries `resumedAgentId` and neither an `agentId` nor
    a description, which is why a reader watching launches alone never sees it.
    """
    return json.dumps({
        "type": "user",
        "toolUseResult": {
            "success": True, "resumedAgentId": agent_id,
            "message": f"Message queued for delivery to {agent_id}.",
        },
        "message": {"content": [{"type": "tool_result", "text": "Message queued"}]},
    })


def test_a_resumed_child_is_outstanding_again(tmp_path: Path) -> None:
    """The hold's own purpose, lost on the second round trip.

    A panel reviewer reports, is asked to go deeper on one finding, and goes back
    out under the same id — the notification that just arrived says so itself:
    "The user can send it another message and resume it, so the same task-id may
    notify more than once." The first reader answered from a launched set minus a
    reported set, so the id stayed reported forever and the resumed child read as
    finished. A restart firing there clears the pane mid-flight, which is the loss
    this whole hold exists to prevent.
    """
    t = transcript(
        tmp_path, launch("a1"), notification("a1"), resume("a1"),
    )
    assert outstanding_children(t) == ["Review panel r1"]


def test_a_resumed_child_that_reports_again_is_finished(tmp_path: Path) -> None:
    """The other half of the same order, and what stops the fix holding forever."""
    t = transcript(
        tmp_path, launch("a1"), notification("a1"), resume("a1"), notification("a1"),
    )
    assert outstanding_children(t) == []


def test_a_resume_naming_a_child_launched_before_the_clear_still_holds(
    tmp_path: Path,
) -> None:
    """Resumes cross transcripts, so the description does not always survive.

    Two sessions in the corpus resume a child whose launch is in the transcript a
    previous restart cleared. The child is out now either way, so it holds — under
    the unnamed row, because the resume record carries no description of its own.
    """
    t = transcript(tmp_path, resume("a-from-before-the-clear"))
    assert outstanding_children(t) == [UNNAMED_CHILD]


def test_a_child_quoting_a_siblings_id_does_not_release_the_sibling(
    tmp_path: Path,
) -> None:
    """A report's `<result>` carries the child's own prose verbatim, inside the
    same string the ids are read from. A reviewer of this very module writes task
    ids in its findings, so collecting every id in the notification let one child
    mark a still-running sibling as reported. The header id is emitted before any
    element holding text somebody else wrote, so taking the first is enough.
    """
    quoting = json.dumps({
        "type": "user",
        "message": {"content": (
            "<task-notification>\n<task-id>a1</task-id>\n"
            "<status>completed</status>\n"
            "<result>r1 here. The reader marks <task-id>a2</task-id> reported "
            "even though a2 is still out.</result>\n</task-notification>"
        )},
    })
    t = transcript(
        tmp_path,
        launch("a1", "reviewer r1"),
        launch("a2", "reviewer r2"),
        quoting,
    )
    assert outstanding_children(t) == ["reviewer r2"]


def test_a_notification_naming_no_child_releases_nothing(tmp_path: Path) -> None:
    """Not every `<task-notification>` is a child reporting back. A goal check-in
    and an artifact-watch notice both arrive in this shape carrying no
    `<task-id>` — 18 of the corpus's 1127 deliveries — and neither says anything
    about whether the panel is still out."""
    check_in = json.dumps({
        "type": "user",
        "message": {"content": (
            "<task-notification>\n"
            "<summary>Goal check-in: background work still running</summary>\n"
            "</task-notification>"
        )},
    })
    t = transcript(tmp_path, launch("a1"), check_in)
    assert outstanding_children(t) == ["Review panel r1"]
