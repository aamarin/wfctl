"""The session restart's decision, as a pure function (#371).

Every rule in `data-model.md`'s table has a case here, because each one guards a
way the personal restart script this replaced went wrong: clearing after a
handoff turn that wrote nothing (the next session quotes an older handoff as
current), logging "already recycled" for a day over a `/clear` that never took,
and saying nothing at all when there was no pane to type into.

No fixtures: an event log is a list of dicts and a pane is a callable.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from wfctl import _restart
from wfctl._restart import (
    CLEAR,
    CLEAR_TEXT,
    DEFAULT_THRESHOLD,
    END,
    END_TEXT,
    HOLD,
    HOLD_CHILDREN,
    NOT_TAKEN,
    NOTHING,
    SKIP,
    START_TEXT,
    Decision,
    decide,
    message,
    threshold,
)

S = "session-1"
OVER = DEFAULT_THRESHOLD + 1


def planned(kind: str, session: str = S, children: tuple[str, ...] = ()) -> dict:
    return {"ts": "2026-09-15T12:00:00Z", "event": "session-restart",
            "session": session, "decision": kind, "children": list(children)}


def sent(text: str, code: int = 0, session: str = S, ts: str = "2026-09-15T12:33:03Z") -> dict:
    return {"ts": ts, "event": "session-restart-send",
            "session": session, "text": text, "exit": code}


def stop(continued: bool = True) -> dict:
    return {"ts": "2026-09-15T12:01:00Z", "event": "end",
            "step": "implement", "continued": continued}


def pane(handle: str | None = "371-x"):
    calls: list[None] = []

    def find() -> str | None:
        calls.append(None)
        return handle

    find.calls = calls  # type: ignore[attr-defined]
    return find


def _no_children() -> list[str]:
    _no_children.calls.append(None)  # type: ignore[attr-defined]
    return []


_no_children.calls = []  # type: ignore[attr-defined]


def run(events: list[dict], tokens: int | None = OVER, limit: int = DEFAULT_THRESHOLD,
        handle: str | None = "371-x", children: tuple[str, ...] = ()) -> Decision:
    return decide(S, tokens, limit, events, pane(handle), lambda: children)


# --- US1: restart, hand off, clear -------------------------------------------

def test_under_the_threshold_decides_nothing_and_never_asks_workmux() -> None:
    """The reply end that happens hundreds of times a day. Asking workmux there
    would put a subprocess on every one of them."""
    find = pane()
    assert decide(
        S, DEFAULT_THRESHOLD - 1, DEFAULT_THRESHOLD, [], find, _no_children
    ).kind == NOTHING
    assert find.calls == []  # type: ignore[attr-defined]
    assert _no_children.calls == []  # type: ignore[attr-defined]


def test_an_unreadable_window_decides_nothing() -> None:
    assert run([], tokens=None).kind == NOTHING


def test_reaching_the_threshold_with_no_restart_under_way_sends_end() -> None:
    """At the threshold, not only past it — "reaches" is the spec's word."""
    d = decide(S, DEFAULT_THRESHOLD, DEFAULT_THRESHOLD, [], pane("371-x"), lambda: [])
    assert d == Decision(END, handle="371-x")
    assert d.texts == [END_TEXT]


def test_a_planned_end_not_yet_sent_decides_nothing() -> None:
    """A person typed in the seconds before the worker ran. Planning `end` again
    would queue a second `/end-session` behind the first."""
    assert run([planned(END)]).kind == NOTHING


def test_a_stop_after_the_end_send_clears() -> None:
    events = [planned(END), sent(END_TEXT), stop()]
    d = run(events)
    assert d == Decision(CLEAR, handle="371-x", end_pos=2)
    assert d.texts == [CLEAR_TEXT, START_TEXT]
    assert events[d.end_pos]["event"] == "end"  # type: ignore[index]


def test_a_stop_before_the_send_is_not_the_handoff() -> None:
    """The handoff has to be newer than the request for it. An `end` from the
    session before — the one whose summary is already on disk — is exactly the
    handoff the restart must not clear on, or the next session quotes it."""
    assert run([stop(), planned(END), sent(END_TEXT)]).kind == HOLD


def test_a_wrapped_up_stop_counts_as_landed() -> None:
    """Clarification Q1. A person ending a held session by hand writes a handoff
    newer than every earlier one, which is the only property the clear needs."""
    assert run([planned(END), sent(END_TEXT), stop(continued=False)]).kind == CLEAR


def test_another_sessions_restart_is_not_this_ones() -> None:
    """After a `/clear` takes, the new session's reply ends read the old
    session's events. They must start fresh rather than inherit its state."""
    events = [planned(END, "old"), sent(END_TEXT, session="old"), stop(),
              planned(CLEAR, "old"), sent(CLEAR_TEXT, session="old")]
    assert run(events).kind == END


def test_end_is_never_planned_twice_for_one_session() -> None:
    """FR-004: still over the threshold after a hold is still one request."""
    events = [planned(END), sent(END_TEXT), planned(HOLD)]
    assert run(events).kind == NOTHING


# --- US2: say so, once, and never retry ---------------------------------------

def test_no_stop_after_the_end_send_holds_once_then_clears_when_it_lands() -> None:
    """State D. The personal script cleared here, and `/start-session` then
    quoted the previous session's handoff as this one's."""
    events = [planned(END), sent(END_TEXT)]
    assert run(events).kind == HOLD
    events.append(planned(HOLD))
    assert run(events).kind == NOTHING
    events.append(stop())
    assert run(events).kind == CLEAR


def test_no_pane_skips_once_per_session() -> None:
    """State E. The personal script logged to a file and the pane showed nothing
    until the harness compacted it anyway."""
    assert run([], handle=None).kind == SKIP
    assert run([planned(SKIP)], handle=None).kind == NOTHING
    assert run([planned(SKIP)], handle="371-x").kind == END


def test_a_landed_handoff_with_no_pane_skips_once() -> None:
    events = [planned(END), sent(END_TEXT), stop()]
    assert run(events, handle=None).kind == SKIP
    events.append(planned(SKIP))
    assert run(events, handle=None).kind == NOTHING


def test_a_planned_clear_not_yet_sent_decides_nothing() -> None:
    """FR-010a, on the clear side."""
    assert run([planned(END), sent(END_TEXT), stop(), planned(CLEAR)]).kind == NOTHING


def test_a_clear_that_exited_zero_and_this_session_is_still_here_is_reported_once() -> None:
    """State F. The pane that grew from 225k to 283k over a day."""
    clear = sent(CLEAR_TEXT)
    events = [planned(END), sent(END_TEXT), stop(), planned(CLEAR), clear]
    d = run(events)
    assert d == Decision(NOT_TAKEN, send=clear)
    events.append(planned(NOT_TAKEN))
    assert run(events).kind == NOTHING


def test_a_clear_that_failed_to_send_is_reported_with_its_exit() -> None:
    clear = sent(CLEAR_TEXT, code=1)
    d = run([planned(END), sent(END_TEXT), stop(), planned(CLEAR), clear])
    assert d == Decision(NOT_TAKEN, send=clear)


def test_an_end_that_failed_to_send_is_reported_and_never_resent() -> None:
    """Clarification Q2. Falling through to hold would blame a model turn that
    never ran; resending types into a pane a person may be using."""
    events = [planned(END), sent(END_TEXT, code=3)]
    assert run(events).kind == NOT_TAKEN
    events.append(planned(NOT_TAKEN))
    assert run(events).kind == NOTHING


def test_turning_the_restart_off_mid_restart_decides_nothing() -> None:
    assert run([planned(END), sent(END_TEXT), stop()], limit=0).kind == NOTHING


# --- #425: children hold the restart before it begins -------------------------

def test_outstanding_children_hold_the_restart_and_never_ask_workmux() -> None:
    """The failure #425 names. Without this the reply end that ends a fan-out
    sends `/end-session restart`, the handoff is written while the panel is still
    out, and the clear two turns later takes its findings with it.

    workmux is not asked because nothing is going to be sent either way."""
    find = pane()
    d = decide(S, OVER, DEFAULT_THRESHOLD, [], find, lambda: ["reviewer r1", "reviewer r2"])
    assert d == Decision(HOLD_CHILDREN, children=("reviewer r1", "reviewer r2"))
    assert d.texts == []
    assert find.calls == []  # type: ignore[attr-defined]


def test_the_children_hold_is_reported_once_and_then_says_nothing() -> None:
    """A panel of six produces a reply end per report. Saying it once is the same
    rule `skip` and `hold` already follow — the pane would otherwise carry six
    copies of a line that has not changed."""
    events: list[dict] = []
    assert run(events, children=("reviewer r1",)).kind == HOLD_CHILDREN
    events.append(planned(HOLD_CHILDREN, children=("reviewer r1",)))
    assert run(events, children=("reviewer r1",)).kind == NOTHING


def test_the_restart_begins_once_the_last_child_has_reported() -> None:
    """The hold's ordinary exit, and the reason it needs no timer: it is
    re-derived on every reply end and ends when the evidence changes."""
    events = [planned(HOLD_CHILDREN, children=("reviewer r1",))]
    assert run(events, children=()).kind == END


def test_a_panel_reporting_one_at_a_time_does_not_repeat_the_hold() -> None:
    """The set shrinks on every reply end a panel of three produces. Each shrink
    is the same hold with less left in it, and a line per shrink would bury the
    first copy — the one carrying the escape hatch."""
    events = [planned(HOLD_CHILDREN, children=("r1", "r2", "r3"))]
    assert run(events, children=("r2", "r3")).kind == NOTHING
    assert run(events, children=("r3",)).kind == NOTHING


def test_a_second_fan_out_is_held_out_loud_rather_than_silently() -> None:
    """The first version said the hold once per session, not once per fan-out. A
    panel sent after an earlier one had already held left the person with a
    session that would not restart and nothing on screen saying why — and the
    pane message is the only place the escape hatch exists."""
    events = [planned(HOLD_CHILDREN, children=("r1",))]
    assert run(events, children=("r9",)).kind == HOLD_CHILDREN


def test_a_second_fan_out_of_identically_named_children_still_speaks() -> None:
    """Descriptions are all the event records, so two panels named alike are
    indistinguishable by name. The count separates them: more children than the
    last hold carried is growth whatever they are called."""
    events = [planned(HOLD_CHILDREN, children=("reviewer",))]
    assert run(events, children=("reviewer", "reviewer")).kind == HOLD_CHILDREN


def test_a_hand_typed_stop_does_not_clear_a_held_pane() -> None:
    """Why the pane message names `/clear` as well. A person taking the escape
    hatch writes a stop, but no *planned* end — so `decide` never reaches the
    branch that sends the clear, falls through to here, and finds the hold
    already recorded. Nothing is sent and nothing further is said, which is why
    half the sequence in that string left them stuck."""
    events = [planned(HOLD_CHILDREN, children=("r1",)), stop()]
    assert run(events, children=("r1",)).kind == NOTHING


def test_a_restart_already_under_way_is_not_held_by_a_later_child() -> None:
    """The boundary this hold does not cross. Once `end` has been sent the
    handoff is written, and `end` is never planned twice — so holding the clear
    would leave no turn able to fold a late child in. The clear is the lesser
    loss, and the case is a session that fans out during its own wrap-up turn."""
    events = [planned(END), sent(END_TEXT), stop()]
    assert run(events, children=("a late reviewer",)).kind == CLEAR


# --- messages -----------------------------------------------------------------

ROOT = Path("/work/371-x")


def test_each_reporting_decision_has_its_contract_text() -> None:
    """The strings in `contracts/hook-session-restart.md`. Pinned because a
    person reads them in the pane with no other context."""
    assert message(Decision(HOLD), ROOT) == (
        "session restart held: /end-session recorded no stop — context not cleared"
    )
    assert message(Decision(SKIP), ROOT) == (
        "session restart skipped: no workmux pane for /work/371-x"
    )
    assert message(Decision(HOLD_CHILDREN, children=("r1", "r2")), ROOT) == (
        "session restart held: 2 subagents still running — context not cleared; "
        "run /end-session restart then /clear yourself if they never report"
    )
    assert message(Decision(NOT_TAKEN, send=sent(CLEAR_TEXT)), ROOT) == (
        "session restart sent /clear at 12:33Z and this session is still here — "
        "run /clear yourself, or /end-session first"
    )
    assert message(Decision(NOT_TAKEN, send=sent(END_TEXT, code=-1)), ROOT) == (
        "session restart never sent /end-session restart (workmux exited -1) — "
        "run it yourself"
    )


def test_a_failed_send_never_claims_it_was_sent() -> None:
    """FR-009. "Sent at 12:33Z" over a `workmux` that exited 1 is the 619 log's
    lie in reverse."""
    text = message(Decision(NOT_TAKEN, send=sent(CLEAR_TEXT, code=1)), ROOT)
    assert text is not None
    assert "never sent /clear" in text
    assert "still here" not in text


def test_one_outstanding_child_is_not_pluralised() -> None:
    """A person reads this line in the pane with nothing else around it, and
    "1 subagents" reads as a bug in the thing that is holding their session."""
    text = message(Decision(HOLD_CHILDREN, children=("r1",)), ROOT)
    assert text is not None
    assert text.startswith("session restart held: 1 subagent still running")


def test_the_children_hold_names_the_escape_hatch_and_no_agent_id() -> None:
    """#425 asks for a decision rather than a timeout, so the line has to say
    what the decision is. The ids are left out deliberately: the harness's own
    launch result calls an agentId internal metadata that must not reach a
    person, and this string is printed in their pane."""
    text = message(Decision(HOLD_CHILDREN, children=("r1", "r2")), ROOT)
    assert text is not None
    assert "run /end-session restart then /clear yourself" in text
    assert "r1" not in text


@pytest.mark.parametrize("kind", [NOTHING, END, CLEAR])
def test_the_deciding_and_sending_kinds_show_nothing(kind: str) -> None:
    assert message(Decision(kind, handle="h"), ROOT) is None


# --- US3: the threshold -------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        (None, DEFAULT_THRESHOLD),
        ("", DEFAULT_THRESHOLD),
        ("abc", DEFAULT_THRESHOLD),
        ("-5", DEFAULT_THRESHOLD),
        ("1e5", DEFAULT_THRESHOLD),
        ("200_000", DEFAULT_THRESHOLD),
        ("150000", 150000),
        (" 150000 ", 150000),
        ("0", 0),
    ],
)
def test_the_threshold_reads_digits_and_nothing_else(raw: str | None, expected: int) -> None:
    """An unreadable value falls back to the default rather than to off: the
    person setting it was tuning the hook, not removing it."""
    environ = {} if raw is None else {_restart.THRESHOLD_ENV: raw}
    assert threshold(environ) == expected


def test_off_decides_nothing_at_any_size() -> None:
    assert run([], tokens=10_000_000, limit=0).kind == NOTHING
