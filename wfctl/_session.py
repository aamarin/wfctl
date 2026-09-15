"""Session lifecycle operations — start, end, resume.

What a session file holds is what re-derivation cannot reach. Everything else —
the issue, the branch, the pipeline step, the next command, when it last moved —
is computed from artifacts on every read, so nothing here caches a conclusion
about it (`session-state-is-re-derived`).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from wfctl._io import append_event, write_atomic

# The one per-feature setting, and the only file in the state dir that holds a
# choice rather than a reading. `verify.json` is the shape it copies: named,
# JSON, one writer, one reader, and its name spelled in the module that means
# something by it rather than in `_io`.
MODE_NAME = "mode.json"


class Observations(NamedTuple):
    """What `end` could see at the moment it ran. No conclusion among them.

    Each field is a reading, not a verdict: where the pipeline stands, whether
    the boundary question was answered, whether the tree has uncommitted work.
    "Complete" is not here because it is not observable — that is #70.
    """

    step: str
    boundary: str
    tree: str


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    the shipped skill passes the value through
    `${WFCTL_SESSION_ID:+--session-id "$WFCTL_SESSION_ID"}`, which already
    collapses unset and empty into "the flag is not there". A reader that treated
    `""` as an identity would answer differently depending on which of the two
    the shell happened to produce, for a caller that did the same thing both
    times.

    The one transformation wfctl performs on the value. Equality is the only
    other operation — never a parse, a split or a pattern
    (`session-identity-comes-from-the-caller`).
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


def auto_approve(agent_dir: Path) -> bool:
    """Whether this feature's design gates may be answered without a human.

    The one value here that is not re-derived, and the module docstring's
    carve-out is why: no artifact implies it, so there is nothing to recompute it
    from and nothing for it to go stale against. `current.json` rotted because
    every field on it had a live answer elsewhere; this has none.

    Absent, malformed or unreadable reads as `False`, never as granted. The
    conservative direction is the whole point — a state dir that lost this file
    must fall back to stopping for a human, not to running without one.

    Three ways to be unreadable, and the shape is the one that bites. `ValueError`
    rather than `JSONDecodeError` because an invalid UTF-8 byte raises
    `UnicodeDecodeError`, which is a `ValueError` and not an `OSError`; and
    `isinstance` because `null`, `3` and `[]` all parse successfully and have no
    `.get`. Every caller reaches this through `build_report`, so an uncaught
    raise here is not a bad read of one field — it is `status`, `start`, `resume`
    and `end` all failing for that branch until someone deletes the file by hand.
    `_verify.load_record` guards the same way for the same reason.
    """
    path = agent_dir / MODE_NAME
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and data.get("auto_approve") is True


def grant_auto_approve(agent_dir: Path, granted: bool) -> None:
    """Record the mode, and record that it was granted.

    Two writes for two questions. The file answers "what mode is this feature in
    now", which is what every later report reads. The event answers "when was
    autonomy granted", which the file cannot: it holds one value and is
    overwritten, so a grant leaves no trace in it.

    That second question exists because the setter is not necessarily a person.
    `/start-session` runs `wfctl start` on every worktree spin-up and handoff and
    its allowlist admits any flag, so an agent can grant itself the mode. Nothing
    available here prevents that — the event is what makes it visible afterwards,
    beside the `start` and `resume` lines that say what the session did next.
    """
    write_atomic(agent_dir / MODE_NAME, json.dumps({"auto_approve": granted}, indent=2))
    append_event(agent_dir, "mode", auto_approve=granted)


def record_outward_action(agent_dir: Path, branch: str, action: str) -> None:
    """Record one outward action this run took, after it succeeded.

    Written by `wfctl report-action` for what no wfctl verb performs — a push —
    and by `_tracker.dispatch` for its own writes. The event keeps the name
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


# The two halves of the handoff's next-action section, named once. `end`
# recognises an unfilled section by them and the template writes it from them,
# so the two cannot drift apart into a warning that never fires.
NEXT_SESSION_TODO = "## Next Session TODO"
NEXT_ACTION_PLACEHOLDER = "- [ ] (fill in)"

# The line that says `end` wrote this file: the title `_render_session_summary`
# opens with, which `end-session`'s own fill-in template repeats verbatim.
#
# Not `**Step**:`, which this was first and is too weak to carry it. That is an
# ordinary label, so a handoff reporting its own pipeline position under the same
# word reads as a summary `end` wrote — and since `worktree-handoff` forbids a
# `## Next Session TODO`, the false warning this mark exists to prevent comes
# straight back. A document has to title itself a session summary to collide
# with this one.
_TEMPLATE_MARK = "# Session Summary:"


def _render_session_summary(branch: str, observed: Observations) -> str:
    """The handoff, headed by what `end` could see rather than what it hoped.

    `**Status**: complete` used to sit here. Nothing observed it — `end` wrote
    the word on every run, including one that closed a session with half the
    tasks open and a dirty tree (#70). What replaces it is three facts and no
    conclusion drawn from them; the reader draws their own, which is the whole
    difference.

    Prose below stays as it is. A handoff whose sections were never filled in
    must read as unfilled, and nothing above them may claim otherwise.
    """
    now = _now_utc()
    return (
        f"# Session Summary: {now[:10]} — {branch}\n\n"
        f"**End**: {now}\n"
        f"**Step**: {observed.step}\n"
        f"**Boundary**: {observed.boundary}\n"
        f"**Tree**: {observed.tree}\n\n"
        f"## What We Accomplished\n\n"
        f"- (fill in)\n\n"
        f"{NEXT_SESSION_TODO}\n\n"
        f"{NEXT_ACTION_PLACEHOLDER}\n"
    )


def names_no_first_action(summary: str) -> bool:
    """Is this handoff's next-action section still the template's?

    Beside the renderer above and reading the same constants, because the only
    thing that can recognise the placeholder is whatever writes it. A copy of the
    literal in the command that prints the warning would go on matching the old
    text after the template moved on, and the warning would die with nothing
    going red.

    The question is narrow on purpose: whether the section was *ever filled in*,
    not whether what fills it names a usable first action. The second is step 9's
    judgment — its gate is quoting a literal sentence — and `end` has no way to
    reach it. Answering the narrow one is what lets `end` speak at the last
    moment the operator is still there to fix it (FR-013).

    **A file `end` did not write is not judged at all**, and a missing section is
    the case that turns on it. `worktree-handoff` tells handoff authors in as
    many words not to add a `Next Session TODO` — the sentence it can quote goes
    in that document's own shape — so reading "no section" as "no first action"
    warns on every fresh worktree, which is #352's own scenario and the one place
    the handoff is most likely to be complete. `_TEMPLATE_MARK` is the title
    `end` writes and `end-session` repeats, which no handoff carries by accident.
    """
    if _TEMPLATE_MARK not in summary:
        return False
    if NEXT_SESSION_TODO not in summary:
        return True
    body = summary[summary.index(NEXT_SESSION_TODO) + len(NEXT_SESSION_TODO) :]
    # To the next heading, so a section someone filled in *below* this one does
    # not answer for it.
    for line in body.splitlines():
        if line.startswith("## "):
            break
        stripped = line.strip()
        if stripped and stripped != NEXT_ACTION_PLACEHOLDER:
            return False
    return True


def end(
    agent_dir: Path, branch: str, observed: Observations, *, continued: bool
) -> tuple[Path, bool]:
    """Write session-summary.md if absent; return its path and whether it wrote.

    The observations are passed in rather than taken here: the caller has
    already built the report, and a second inference is a second chance to
    disagree with the line it is about to print.

    `continued` says whether the work carries on, and it is the caller's to
    declare — keyword-only and with no default, so a call site that has not
    thought about it does not compile rather than quietly recording a wrap-up.
    `end` cannot conclude it: `**Status**: complete` was written on every run
    including one that closed with half the tasks open, and #70 removed it
    because nothing observed the word. What `end` can observe is that it was
    told, and that is the whole of what goes in the log.

    Written once. A second `end` must not overwrite prose a human or agent
    filled in between the two.

    The flag is returned because only this function knows which of the two
    happened, and the caller reports it. Whether the file was written is not
    re-derivable afterwards: the kept file and a freshly written one are both
    just a `session-summary.md` sitting there, and the mtime cannot separate
    them either — `worktree-handoff` copies a handoff in after the branch's
    first `start` event, so "older than the session" classifies a handoff as
    stale (#239).
    """
    summary_file = agent_dir / "session-summary.md"
    written = not summary_file.exists()
    if written:
        write_atomic(summary_file, _render_session_summary(branch, observed))

    append_event(
        agent_dir, "end", branch=branch, step=observed.step, continued=continued
    )
    return summary_file, written
