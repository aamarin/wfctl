"""The event log: what happened on a branch, one JSON line per event.

Every command appends here through `_io.append_event`, and this module holds
the readers that answer from those lines, and the writers for the events that
mean something to them. Whether a session started, who holds the branch, how the
last session stopped, and which outward actions an agent's host refused are
all read here, on every read, rather than kept in a file that could go stale
(`session-state-is-re-derived`).

The domain page puts the event log in evidence and derivation, since it records
what happened. Session continuity reads it from here and keeps only the
handoff.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

from wfctl._io import append_event


def read_events(state_dir: Path) -> list[dict]:
    """Every well-formed record in the branch's event log, in line order.

    A malformed or non-object line is skipped rather than raising, as every other
    reader of this log does: a torn final append must not stop the restart hook,
    which reads every record to decide what a reply end does.
    """
    try:
        text = (state_dir / "events.jsonl").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    events = []
    for line in text.splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            events.append(record)
    return events


def session_started(agent_dir: Path, branch: str | None = None) -> bool:
    """Whether `wfctl start` has run for this branch.

    Read from the event log rather than from a file's existence. `current.json`
    used to answer this by being there, which made one fact the reason a whole
    cache of derivable fields had to be kept alive. The `start` event records the
    same thing as it happens, and is append-only, so nothing has to be rewritten
    to keep it true.

    A malformed line is skipped rather than raising: the log is appended to by
    every command, and a truncated final write must not make the session look
    unstarted — that would send the reader to `wfctl start` on a session that is
    running. `isinstance` guards the same way `last_session_id` does: `null`,
    `3` and `[]` all parse successfully and have no `.get`.

    `branch` filters the same way `_holder_since_last_boundary` does: a line
    naming a different branch is skipped, and one naming none — every line
    predating branch-scoping — matches every branch. Without it, a shared
    `WFCTL_STATE_DIR` let a branch that never ran `start` inherit another
    branch's line here, while the holder scan two calls later was already
    scoped — so `session_open_for` fell through to `"unknown"` instead of
    `"none"`, and `"unknown"` passes the gates `"none"` is meant to stop.
    """
    events = agent_dir / "events.jsonl"
    if not events.exists():
        return False
    for line in events.read_text().splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict) or data.get("event") != "start":
            continue
        if branch is not None and data.get("branch") not in (None, branch):
            continue
        return True
    return False


def identity(presented: str | None) -> str | None:
    """The caller's identity, or None when it presented none.

    Empty and whitespace-only read as absent rather than as an identity, because
    the value comes from an environment variable, and a variable exported as
    `""` is the same caller as one never exported. A reader that treated `""`
    as an identity would answer differently depending on which of the two the
    shell happened to produce, for a caller that did the same thing both times.

    The one transformation wfctl performs on the value. Equality is the only
    other operation — never a parse, a split or a pattern
    (`session-identity-from-named-agent`).
    """
    if presented is None:
        return None
    return presented if presented.strip() else None


def _holder_since_last_boundary(
    agent_dir: Path, branch: str | None
) -> tuple[str | None, bool]:
    """The identity on the most recent `start` for `branch`, and whether an
    `end` followed it.

    One scan serves both `last_session_id` and `session_open_for`, filtered
    the way `opens_a_new_sitting` filters (`_stall.py:174`): a line naming a
    different branch is skipped, and one naming none — every line predating
    branch-scoping — matches every branch, so it still counts. Without that
    filter a shared `WFCTL_STATE_DIR` (`_paths.py:672-676`) would let one
    branch's `start` answer for another's, which
    `session-identity-comes-from-the-caller` names as the exact risk.

    `ended` resets on every `start` for the same reason `opens_a_new_sitting`
    resets `worked` there: whichever boundary is most recent governs, and an
    `end` an identity never has reason to precede a `start` other than its own
    — `wfctl end` is gated to the holder, so an `end` line always closes the
    `start` immediately above it.
    """
    events = agent_dir / "events.jsonl"
    if not events.exists():
        return None, False
    holder: str | None = None
    ended = False
    for line in events.read_text().splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        if branch is not None and data.get("branch") not in (None, branch):
            continue
        event = data.get("event")
        if event == "start":
            value = data.get("session_id")
            holder = identity(value) if isinstance(value, str) else None
            ended = False
        elif event == "end":
            ended = True
    return holder, ended


def last_stop(agent_dir: Path, branch: str) -> str:
    """The kind of the branch's most recent stop: `none`, `continued`, or `wrapped`.

    Only `wfctl end` writes a stop, and `--continued` marks one that didn't
    finish. A stop with no `continued` key predates the flag and was a wrap-up.
    The most recent stop decides, because a branch wrapped up once and cut off
    since has both. A line that doesn't parse is skipped like every other reader
    of this log skips one, since a torn final append still contains `"end"`.
    Lines naming another branch are skipped too, and lines naming none still
    count, as `_holder_since_last_boundary` treats them.
    """
    events = agent_dir / "events.jsonl"
    try:
        text = events.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "none"
    kind = "none"
    for line in text.splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict) or data.get("event") != "end":
            continue
        if data.get("branch") not in (None, branch):
            continue
        kind = "continued" if data.get("continued") is True else "wrapped"
    return kind


def last_session_id(agent_dir: Path, branch: str | None = None) -> str | None:
    """Who holds the branch: the identity on the most recent `start`, or None.

    The *last* start line, where `session_started` reads the first. The two ask
    different questions of the same lines — has a session ever run here, versus
    who is in it now — and the append-only log answers both without either
    rewriting anything. A takeover is a new `start` line, so the holder moves by
    the same mechanism that records the session opening.

    None covers two cases that are one fact: no `start` line at all, and a line
    that carries no `session_id`. Both mean nobody identified is holding the
    branch, which is what FR-012 lets the first identified caller take over.

    `branch` defaults to `None` — every branch — for callers that already scope
    `agent_dir` to one branch themselves; a caller reading a shared state dir
    passes its own branch, matching `opens_a_new_sitting`.
    """
    holder, _ended = _holder_since_last_boundary(agent_dir, branch)
    return holder


def session_open_for(
    agent_dir: Path, presented: str | None, branch: str | None = None
) -> str:
    """Who holds this branch, relative to the caller: the holder relation.

    One of `"none"`, `"self"`, `"other"`, `"unknown"` — the four states
    `data-model.md` draws, named as a fact about *whether it is you* rather than
    as the identity itself, which `status` never prints.

    `"none"` is asked first and beats `"unknown"`. A branch that never had a
    session and a caller that presented nothing both leave `session_open` false,
    so the two agree on the answer and differ on what they can tell the reader —
    and "no session here" is the one that names a remedy.

    **A holder that is absent is `"unknown"`, not `"other"`.** Every branch
    recorded before this feature has `start` lines carrying no identity, so
    reading that as a holder the caller is not would refuse every one of them at
    once. `data-model.md` puts holder-absent and identity-absent in the same
    state D for exactly this reason: the released behaviour, plus the right for
    the first identified caller to take over.

    **A holder matching the caller, with an `end` since, still reads `"other"`.**
    `data-model.md` § State transitions calls this "not a state": a branch whose
    session was wrapped up is state C to the next reader "the same string, the
    same remedy" whether that reader is a different conversation or the one that
    ended it — `docs/architecture/design/200-session-id-rides-on-the-start-event.md`
    states the criterion as "no `end` event follows it".
    """
    if not session_started(agent_dir, branch):
        return "none"
    caller = identity(presented)
    if caller is None:
        return "unknown"
    holder, ended = _holder_since_last_boundary(agent_dir, branch)
    if holder is None:
        return "unknown"
    return "self" if holder == caller and not ended else "other"


def record_outward_action(agent_dir: Path, branch: str, action: str) -> None:
    """Record one outward action this run took, after it succeeded.

    Written by `wfctl report-action` for what no wfctl verb performs — a push —
    and by `wfctl issue` for each tracker write that landed. The event keeps the name
    `notify-action` though nothing here notifies anyone any more: the event name
    is storage and the verb is interface, and renaming storage would break every
    log already written and `_restart`'s reader of them. The function is
    interface, so it carries the name the change left behind.

    `branch` is stored for the reason `record_blocked` stores it, and the two
    have to agree: this event releases the hold that one files, and
    `standing_blocks` reads an event with no branch as matching every branch. A
    release that named no branch would therefore lift a hold filed on a
    different one — unreachable until the action names agreed, which is exactly
    what recording `issue-<verb>` arranged.

    The log is the destination rather than one of several: it is written whether
    or not a change is open and whether or not the session ends cleanly, and it
    is the only trace of a push that survives a restart's `/clear`.
    """
    append_event(agent_dir, "notify-action", branch=branch, action=action)


class StandingBlock(NamedTuple):
    """One action whose most recent event, for this branch, is a block that has
    not since cleared (#364).

    Not a raw event: `reason` and `step` are lifted out of it for
    `_pipeline`'s hold to read without re-parsing `events.jsonl`.
    """

    action: str
    reason: str
    step: str | None


def record_blocked(
    agent_dir: Path, branch: str, action: str, reason: str, step: str | None,
) -> None:
    """Record that the agent's own host refused an outward action wfctl never
    ran (#364 FR-005, FR-006 — #384 numbers two different requirements the
    same, so the issue is named rather than left to the reader to guess).

    `step` is the step `build_report` found current at call time; the agent
    supplies only the two facts it alone witnessed (`action`, `reason`).

    `branch` is stored because a state dir shared across worktrees holds every
    branch's events, so the write has to say which branch it is about, not just
    which directory it landed in.
    """
    append_event(
        agent_dir, "blocked", branch=branch, action=action, reason=reason, step=step
    )


def standing_blocks(agent_dir: Path, branch: str) -> list[StandingBlock]:
    """Every action whose latest event, for this branch, is a standing block
    (#364 FR-012, FR-020, FR-021).

    Three event kinds share one action-keyed timeline: `blocked`,
    `block-cleared`, and `notify-action`. A `notify-action` is the release —
    `wfctl report-action`, or a `wfctl issue` write that succeeded on retry —
    so taking the action lifts its own hold with no clearing step. Whichever of
    the three is most recent for a given action decides that action's state;
    only `blocked` leaves it standing.

    `block-cleared` is no longer written: `wfctl blocked --clear` was removed
    with the grant (#384), because it said what recording the action already
    says. It is still read, so a block cleared in a log written before then stays
    cleared rather than coming back to hold a step nobody is working on.

    Scoped to `branch`: a shared state dir holds every branch's events, and
    reading one branch's answer off another's block is how one feature's hold
    would land on a different one. All three kinds carry a branch now that
    `record_outward_action` writes one, and an event without the field matches
    every branch — the only events missing it are `notify-action` lines written
    before #384, which nothing filed a matching hold against anyway.

    Malformed lines are skipped rather than raised: every command appends here,
    so a truncated final write must not crash the reader that answers whether
    the pipeline may advance.

    **Ordered by recency, oldest block first.** Two different actions can hold
    the same step, and a caller that needs the truly latest one — `_apply_block_hold`
    picks it with a last-write-wins dict comprehension — depends on this order
    rather than on the order actions first appeared in the log.
    """
    events = agent_dir / "events.jsonl"
    if not events.exists():
        return []
    # action -> (kind, reason, step) of its most recent qualifying event.
    latest: dict[str, tuple[str, str | None, str | None]] = {}
    for line in events.read_text().splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        kind = data.get("event")
        if kind not in ("blocked", "block-cleared", "notify-action"):
            continue
        if data.get("branch") not in (None, branch):
            continue
        action = data.get("action")
        if not isinstance(action, str):
            continue
        reason = data.get("reason") if kind == "blocked" else None
        step = data.get("step") if kind == "blocked" else None
        # `_apply_block_hold` keys a dict on `.step` — a malformed line whose
        # `step` survived `json.loads` as a list or number would crash the
        # reader that must not crash on a malformed line, same as `action`
        # above.
        if not isinstance(step, str):
            step = None
        # Re-inserted rather than updated in place: a dict preserves a key's
        # original position across reassignment, so without the pop, iteration
        # order would reflect which action was *first* seen rather than which
        # was *most recently* blocked. Two actions holding the same step is
        # exactly the case `_apply_block_hold`'s last-write-wins dict comprehension
        # needs this order for — it must see the truly latest block last.
        latest.pop(action, None)
        latest[action] = (kind, reason, step)
    return [
        StandingBlock(action, reason, step)
        for action, (kind, reason, step) in latest.items()
        if kind == "blocked" and isinstance(reason, str)
    ]
