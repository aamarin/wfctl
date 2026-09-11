"""A stop can say it did not finish, and the next session routes on that (#352).

`wfctl end` recorded one mark for a session stopping, and `start-session` read
it as *a human deliberately wrapped up*. A run cut off mid-work came back, found
a handoff and work ready to do, and stopped to ask which of the two it was — a
question answerable only by the person whose absence is why the run was cut off.

The mark the two kinds differ in is one payload key on the `end` event, and the
architecture record `stop-kind-is-a-field-not-an-event` is why it is a key and
not a second event kind: every existing reader matches on the kind, so a second
name there fails by under-counting rather than by raising.

`NO_COLOR` is set once in `conftest.py` and is not re-pinned here — these assert
on console text, so a colour-capable terminal would make them machine-dependent.
"""
from __future__ import annotations

import json
import types

from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def _events(storyctl_dir: types.SimpleNamespace) -> list[dict]:
    lines = (storyctl_dir.agent_dir / "events.jsonl").read_text().splitlines()
    return [json.loads(line) for line in lines]


def _stops(storyctl_dir: types.SimpleNamespace) -> list[dict]:
    return [e for e in _events(storyctl_dir) if e["event"] == "end"]


def _start_then_end(
    storyctl_dir: types.SimpleNamespace, *flags: str
) -> str:
    runner.invoke(app, ["start"])
    result = runner.invoke(app, ["end", *flags])
    assert result.exit_code == 0, result.output
    return result.output


def test_the_flag_records_the_stop_as_continued(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-001. The whole feature is that these two stops are told apart."""
    _start_then_end(storyctl_dir, "--continued")

    assert _stops(storyctl_dir)[-1]["continued"] is True


def test_omitting_the_flag_records_a_finished_stop(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-011, and the half that protects a branch someone wrapped up.

    The key is written either way rather than only when true. A stop that omits
    it is then a line recorded before this feature existed, which is a different
    fact from a stop that declared itself finished — and no reader has to guess
    which of the two an absent key means, because nothing new writes one."""
    _start_then_end(storyctl_dir)

    assert _stops(storyctl_dir)[-1]["continued"] is False


def test_the_closing_line_differs_in_its_first_clause_only(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-002's "everything not stated is unchanged", made checkable.

    Three readings follow the dash — position, boundary, tree — and #70 is why
    they are readings rather than a verdict. A second spelling of them is a
    second thing to keep in step, and the drift would show up as `end` reporting
    a different pipeline position depending on a flag that observes none of it."""
    continued = _start_then_end(storyctl_dir, "--continued").splitlines()[0]

    assert continued.startswith("✓ Session stopped, not finished — ")
    assert "Session closed" not in continued


def test_the_two_closing_lines_agree_on_everything_after_the_dash(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The other direction of the same contract, on one branch's two stops.

    Asserting the prefix alone would pass on a line that renamed `boundary` or
    dropped the tree reading under the flag. Comparing the tails is what pins
    "one clause differs" rather than "the first clause differs"."""
    finished = _start_then_end(storyctl_dir).splitlines()[0]
    continued = _start_then_end(storyctl_dir, "--continued").splitlines()[0]

    assert finished.split(" — ", 1)[1] == continued.split(" — ", 1)[1]


def test_a_handoff_already_on_disk_is_kept_under_either_kind(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-002 and Story 2 scenario 2.

    The write-once rule is what stops a second `end` overwriting prose a human
    filled in between the two, and a continued stop is the case where a second
    `end` is *expected* — an interrupted run stops, restarts, and stops again.
    A flag that reached that rule would delete the handoff on the very branch
    the feature exists to serve."""
    first = _start_then_end(storyctl_dir)
    summary = storyctl_dir.agent_dir / "session-summary.md"
    summary.write_text("# handed over\n\n## Next Session TODO\n\n- [ ] rebase\n")

    second = _start_then_end(storyctl_dir, "--continued")

    assert "⚠ kept — this session wrote nothing" in second
    assert "⚠ kept" not in first
    assert "- [ ] rebase" in summary.read_text()


_WARNING = "⚠ the handoff names no first action"


def _end_over_handoff(
    storyctl_dir: types.SimpleNamespace, handoff: str, *flags: str
) -> str:
    """Put a handoff on disk first, so the write-once rule keeps it verbatim."""
    (storyctl_dir.agent_dir / "session-summary.md").write_text(handoff)
    return _start_then_end(storyctl_dir, *flags)


def test_a_fresh_template_is_warned_about(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-013 on the path it fires on most.

    A continued stop on a branch with no handoff writes the template and then
    warns about what it just wrote. That reads like a bug and is the point: the
    operator is still present, and this is the last moment anyone can supply the
    sentence the next session needs to quote."""
    assert _WARNING in _start_then_end(storyctl_dir, "--continued")


def test_a_missing_section_is_warned_about(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A handoff someone wrote by hand, with no next-action section at all.

    Absent is not empty and not a placeholder, and all three have to reach the
    warning — otherwise the shape most likely to be hand-written is the one
    shape that goes unreported."""
    handoff = "# Handoff\n\n## What We Accomplished\n\n- rewrote the parser\n"

    assert _WARNING in _end_over_handoff(storyctl_dir, handoff, "--continued")


def test_an_empty_section_is_warned_about(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The heading kept and the bullets deleted — what editing down to nothing
    leaves behind."""
    handoff = "# Handoff\n\n## Next Session TODO\n\n"

    assert _WARNING in _end_over_handoff(storyctl_dir, handoff, "--continued")


def test_a_filled_section_is_not_warned_about(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The negative case, and the boundary of what `end` is allowed to judge.

    Filled is not a claim that the sentence names a usable first action — that
    is step 9's gate and `end` cannot reach it. It is the absence of the one
    thing `end` can see, and a warning on filled prose would be the unobservable
    verdict #70 removed, wearing a new word."""
    handoff = "# Handoff\n\n## Next Session TODO\n\n- [ ] rebase onto main\n"

    assert _WARNING not in _end_over_handoff(storyctl_dir, handoff, "--continued")


def test_a_section_filled_below_an_empty_one_does_not_answer_for_it(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The scan stops at the next heading.

    Reading to the end of the file instead would let any prose below the section
    — an Open Questions list, a paste of a stack trace — count as the next
    action, and the warning would go quiet on exactly the handoffs with the most
    written in them."""
    handoff = (
        "# Handoff\n\n## Next Session TODO\n\n\n## Open Questions\n\n- [ ] which db\n"
    )

    assert _WARNING in _end_over_handoff(storyctl_dir, handoff, "--continued")


def test_a_wrapped_up_stop_over_a_template_says_nothing(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The warning is about what the *next* session will do, and after a
    wrapped-up stop that session asks whatever the handoff says. Printing it
    there would be a line with no consequence attached, on the common path."""
    assert _WARNING not in _start_then_end(storyctl_dir)


def test_the_no_session_refusal_is_the_same_under_both(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Story 2 scenario 3. The flag declares what a stop was, not that one may
    happen — so it must not reach the check for whether there is anything to
    stop.

    Byte-identical rather than merely both-refused: an automated resetter reads
    this output, and a refusal worded differently under the flag is a second
    string for a caller to recognise, with nothing keeping the two in step."""
    plain = runner.invoke(app, ["end"])
    flagged = runner.invoke(app, ["end", "--continued"])

    assert plain.exit_code == 1
    assert flagged.exit_code == 1
    assert plain.output == flagged.output
    assert not (storyctl_dir.agent_dir / "events.jsonl").exists()


def test_every_stop_on_a_branch_survives_with_its_kind(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-008 and SC-004, and the reason this feature records the interruption
    instead of erasing the stop.

    The cheap alternative was a hook deleting the `end` line so the next session
    routes past it — same routing today, no wfctl change at all. It leaves a
    branch interrupted four times indistinguishable from one nobody ever worked
    on, which is the fact User Story 3 exists to keep."""
    for _ in range(3):
        _start_then_end(storyctl_dir, "--continued")
    _start_then_end(storyctl_dir)

    assert [stop["continued"] for stop in _stops(storyctl_dir)] == [
        True,
        True,
        True,
        False,
    ]


def test_a_mixed_history_keeps_the_newer_stop_last(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`spec.md`'s first edge case, from both directions.

    This is not FR-007 — that rule is `tail -1` inside `start-session`'s step 4,
    and no function here implements it. What this pins is the property the rule
    stands on: stops land in the order they happened and nothing rewrites an
    earlier one, so the last line is the last stop. Were that false, `tail -1`
    would be reading whichever stop the log happened to end with."""
    _start_then_end(storyctl_dir)
    _start_then_end(storyctl_dir, "--continued")

    assert _stops(storyctl_dir)[-1]["continued"] is True

    _start_then_end(storyctl_dir)

    assert _stops(storyctl_dir)[-1]["continued"] is False
    assert len(_stops(storyctl_dir)) == 3


def test_the_log_gains_no_row_and_no_new_event_kind(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The architecture record's last consequence, checked where it shows.

    A second event kind would have rendered as its own coloured row, and every
    existing reader matching `event == "end"` would have had to learn the second
    name — failing by under-counting rather than by raising. The kind stays one
    string; the payload carries the difference, and `wfctl log` shows it in the
    detail column beside `step=`."""
    _start_then_end(storyctl_dir, "--continued")

    output = runner.invoke(app, ["log"]).output

    assert "continued=True" in output
    assert "end" in output
    # The event column is left-padded to ten characters, so a new kind named
    # `continued` would appear at the start of a line's second field rather than
    # inside the detail string. Asserting on the payload spelling is what tells
    # the two apart.
    assert not any(
        line.split()[2:3] == ["continued"] for line in output.splitlines() if line.split()
    )


def test_the_status_view_is_unchanged_by_a_continued_stop(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-015, and the clarification behind it.

    The issue asked for `wfctl status` to be able to say a run was interrupted N
    times. "Able to" is a capability the record creates; shipping the view is a
    separate decision, and taking it here would add a second reader of a record
    whose shape had not yet been chosen. So the branch history is the only place
    a continued stop is reported, and this is what says so."""
    storyctl_dir.stage_upstream_of("tasks")
    runner.invoke(app, ["start"])
    before = runner.invoke(app, ["status"]).output
    before_json = runner.invoke(app, ["status", "--json"]).output

    runner.invoke(app, ["end", "--continued"])

    assert runner.invoke(app, ["status"]).output == before
    assert runner.invoke(app, ["status", "--json"]).output == before_json


def test_the_payload_is_inert_to_every_existing_reader(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """SC-005, and the architecture record's central claim made checkable.

    Four readers consult the stop mark and all four match on `event == "end"`;
    none reads the payload, because none asks the new question. That is the whole
    argument for putting the kind in the payload rather than in a second event
    kind — so it is worth a test that the three spellings of that payload are
    indistinguishable to all of them, including the absent one already on disk in
    every state dir.

    A `resume` between the two stops rather than a bare start/end pair: without
    one `opens_a_new_sitting` returns `False` by the same path in every variant,
    and three readers agreeing on a value none of them had to compute proves
    nothing."""
    from wfctl._session import session_started
    from wfctl._stall import _passes_this_sitting, opens_a_new_sitting

    events = storyctl_dir.agent_dir / "events.jsonl"
    verdicts = set()
    for payload in ('', ', "continued": false', ', "continued": true'):
        events.write_text(
            '{"ts": "2026-09-01T10:00:00Z", "event": "start", "branch": "418-storyctl"}\n'
            '{"ts": "2026-09-01T11:00:00Z", "event": "end", "step": "plan"'
            + payload
            + "}\n"
            '{"ts": "2026-09-01T12:00:00Z", "event": "resume", "branch": "418-storyctl",'
            ' "step": "plan", "digest": "abc123"}\n'
        )
        verdicts.add(
            (
                session_started(storyctl_dir.agent_dir),
                opens_a_new_sitting(storyctl_dir.agent_dir, "418-storyctl"),
                len(_passes_this_sitting(events, "418-storyctl")),
            )
        )

    assert verdicts == {(True, True, 1)}
