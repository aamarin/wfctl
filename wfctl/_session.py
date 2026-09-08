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


def session_started(agent_dir: Path) -> bool:
    """Whether `wfctl start` has run for this branch.

    Read from the event log rather than from a file's existence. `current.json`
    used to answer this by being there, which made one fact the reason a whole
    cache of derivable fields had to be kept alive. The `start` event records the
    same thing as it happens, and is append-only, so nothing has to be rewritten
    to keep it true.

    A malformed line is skipped rather than raising: the log is appended to by
    every command, and a truncated final write must not make the session look
    unstarted — that would send the reader to `wfctl start` on a session that is
    running.
    """
    events = agent_dir / "events.jsonl"
    if not events.exists():
        return False
    for line in events.read_text().splitlines():
        try:
            if json.loads(line).get("event") == "start":
                return True
        except json.JSONDecodeError:
            continue
    return False


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


# The second per-feature choice, and its own file rather than a second key on
# `mode.json`. What `mode.json` says about itself is one writer, one reader; a
# second key would make every write a read-merge-write and give a partly-corrupt
# file a meaning nobody has decided. The ~12 lines saved would have been spent on
# merge logic and a new failure mode.
NOTIFY_NAME = "notify.json"

# The label that grants from the tracker side. Spelled here rather than in
# `_tracker`: which label means *may notify* is this module's business, and
# reading labels off an issue is that one's.
NOTIFY_LABEL = "authority:notify"


class NotifyGrant(NamedTuple):
    """Whether this run may take an action that tells someone outside the repo.

    `granted` is what every caller gates on, and it is False for every source
    below except `label` and `local`. `source` is what keeps the refusals apart,
    and they are not one event: nobody granted it, someone turned it off, the
    stored value could not be read, the tracker could not be reached, or this is
    the trunk and no grant reaches it. FR-015 exists because the middle two
    decide a whole run and must not be filed as a person withholding authority.

    `detail` is for the event log and never for the console. `status` is glanced
    at and has to stay one line; an unbounded stderr wraps and stops being
    scannable, while a log carrying a fixed string cannot answer the only
    question it is opened for.
    """

    granted: bool
    source: str
    detail: str | None = None


def _read_notify_file(agent_dir: Path) -> tuple[dict | None, str | None]:
    """The stored grant, or why it could not be read. Absent is not a failure.

    Guards the three shapes `auto_approve` guards, and for the reason its
    docstring gives: `ValueError` because an invalid UTF-8 byte raises
    `UnicodeDecodeError`, which is a `ValueError` and not an `OSError`; and
    `isinstance` because `null`, `3` and `[]` all parse and have no `.get`.

    Where it parts company with `auto_approve` is the missing file. That reader
    folds absent into malformed because both mean False to it. Here they are
    different answers — absent means nobody has said anything, which a label may
    still answer, and malformed means the answer is lost, which nothing may
    overrule.
    """
    path = agent_dir / NOTIFY_NAME
    if not path.exists():
        return None, None
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        return None, f"{path.name}: {e}"
    if not isinstance(data, dict):
        return None, f"{path.name}: expected an object, found {type(data).__name__}"
    return data, None


def notify_grant(
    agent_dir: Path, repo_root: Path, branch: str, issue: str | None
) -> NotifyGrant:
    """Resolve the grant once, for the whole run (FR-014).

    Never raises. Every failure shape resolves to refused, matching
    `auto_approve`'s posture and for its stated reason: a raise here breaks
    `status`, `start`, `resume` and `end` for that branch at once.

    The order is the grid in `data-model.md`, and it is also what keeps the
    tracker round-trip off the common path: an explicit local *denied* beats a
    label and a local *granted* needs no second opinion, so only an unset local
    file asks the tracker anything.

    Takes `repo_root` and `branch`, which the contract's two-argument sketch did
    not: the trunk question below cannot be asked without them, and the label
    read reaches the backend through the repo's own config rather than through a
    name this module would have to hardcode.

    Called by `wfctl start` and nothing else. Every other command reads the
    answer back through `resolved_notify`, which is what keeps the tracker
    round-trip to one per run.
    """
    from wfctl._paths import on_trunk

    # FR-008, asked first so nothing later can reach past it. Authority is
    # bounded by the feature branch, and the state dir being per-branch already
    # makes this true by construction — which is exactly why it is asserted
    # here, where it survives the state dir changing shape.
    trunk = on_trunk(repo_root, branch)
    if trunk is None:
        # Its own source rather than `unreadable`, which blames the issue
        # tracker. A repo whose trunk cannot be named may have no tracker at all,
        # and telling that reader the tracker was unreachable names a cause that
        # is not the cause — the mistake the `corrupt`/`unreadable` split already
        # corrected once, not applied to this third case until a panel found it.
        return NotifyGrant(False, "unknown-trunk")
    if trunk:
        return NotifyGrant(False, "trunk")

    data, corrupt = _read_notify_file(agent_dir)
    if corrupt is not None:
        return NotifyGrant(False, "corrupt", corrupt)
    if data is not None:
        state = data.get("state")
        if state == "denied":
            return NotifyGrant(False, "deny")
        if state == "granted":
            return NotifyGrant(True, "local")
        # A file holding neither is a file whose answer is lost, not one that
        # says nothing: something wrote it, and reading it as unset would let a
        # typo resolve the way an absent file does.
        return NotifyGrant(False, "corrupt", f"{NOTIFY_NAME}: unknown state {state!r}")

    # `"unknown"` as well as None. `extract_issue_key` returns that sentinel for
    # a branch carrying no key and never returns None, so a `is None` guard alone
    # is dead code — every keyless branch reached the label read, asked the
    # tracker about an issue called "unknown", and had the failure filed as a
    # tracker that could not be reached. An absent key is not a failed read, and
    # conflating them is what FR-015 forbids.
    if issue is None or issue == "unknown":
        return NotifyGrant(False, "unset")

    from wfctl._tracker import read_issue_labels

    labels, detail = read_issue_labels(repo_root, issue)
    if detail is not None:
        return NotifyGrant(False, "unreadable", detail)
    if labels is not None and NOTIFY_LABEL in labels:
        return NotifyGrant(True, "label")
    # No labels and no failure covers two states that resolve alike: the tracker
    # answered and the label was absent, or there is no tracker to ask (FR-012).
    # A missing label says nothing, not no — which is why this is `unset` and not
    # `deny`.
    return NotifyGrant(False, "unset")


def action_grant(agent_dir: Path, repo_root: Path) -> NotifyGrant:
    """The verdict at the moment an action is about to be taken.

    `resolved_notify` alone is not enough here, and the gap was real: the state
    dir is per-branch only when `WFCTL_STATE_DIR` is unset, so under a shared one
    a grant made on a feature branch fired a notifying action on the trunk. The
    comment that used to sit beside the resolve-time check claimed it "survives
    the state dir changing shape" — it did not, because a gate reading the log
    reads whatever branch wrote it.

    So the branch is re-asked here rather than trusted from the record. Two local
    git calls, on a path that is about to talk to a network service anyway; the
    round-trip argument that keeps this out of `status` does not apply.
    """
    from wfctl._paths import on_trunk, resolve_branch

    trunk = on_trunk(repo_root, resolve_branch(repo_root))
    if trunk is None:
        return NotifyGrant(False, "unknown-trunk")
    if trunk:
        return NotifyGrant(False, "trunk")
    return resolved_notify(agent_dir)


def grant_notify(agent_dir: Path, state: str) -> None:
    """Record the grant, and record that it was made.

    Two writes for two questions, copied from `grant_auto_approve` and for its
    reason. The file answers *what is the state now*, which every later report
    reads. The event answers *when was this given*, which the file cannot: it
    holds one value and is overwritten, so a grant leaves no trace in it.

    That second question carries more here than it does for the mode. The
    decision record says a human grants this and an agent may only narrow it,
    and nothing available here can tell the two apart — `/start-session` runs
    `wfctl start` under a glob that admits any flag. The event is what makes a
    self-grant legible afterwards, which is the whole of what enforces the rule.

    There is no call that writes *unset*: returning to unset is deleting the
    file, and no code path does that today.
    """
    write_atomic(
        agent_dir / NOTIFY_NAME,
        json.dumps({"state": state, "source": "local", "at": _now_utc()}, indent=2),
    )
    append_event(agent_dir, "notify-grant", state=state, source="local")


def record_notify_resolved(agent_dir: Path, grant: NotifyGrant) -> None:
    """Record the answer the run will hold to, at the moment the run begins.

    FR-014 says the grant is read once and that answer holds for every notifying
    action in the run, and this is where "once" happens: `wfctl start` resolves,
    every later command reads the line back. The alternative was resolving on
    each command, which spends a 1.4s tracker round-trip on every `wfctl status`
    — dozens per session, all returning the same answer, against a budget
    `plan.md` states as one round-trip per run.

    Not a cache. `session-state-is-re-derived` forbids carrying a conclusion
    forward from an earlier write, and what this writes is an event: the log is
    an artifact, and reading the last answer out of it is re-derivation from
    disk, the same way `session_started` reads the `start` line rather than
    trusting a file's existence.

    What it costs is a label added mid-run, which is seen at the next `wfctl
    start` rather than the next command. FR-014 already spent that.
    """
    if _last_resolved(agent_dir) == grant:
        # `start` is idempotent about the event log, and a second run that
        # resolved the same answer must leave it byte-identical — `/start-session`
        # runs `wfctl start` on every handoff, so an unconditional append would
        # make the log grow with lines that say what the previous one said.
        # What is worth recording is the answer changing, which is what a flag
        # or a newly-added label does.
        return
    append_event(
        agent_dir, "notify-resolved",
        granted=grant.granted, source=grant.source, detail=grant.detail,
    )


def _last_resolved(agent_dir: Path) -> NotifyGrant | None:
    """The last recorded resolution, or None when nothing has resolved one.

    None and a recorded refusal are the same verdict and not the same fact, and
    only this reader can tell them apart: one says nobody has opened a session on
    this branch, the other says a session asked and was told no. The public
    reader below collapses them on purpose — a caller gating on the answer wants
    the verdict — but the writer must not, or the first resolution of a run that
    found nothing would look like a resolution that had already been recorded and
    never be written down.
    """
    events = agent_dir / "events.jsonl"
    if not events.exists():
        return None
    found = None
    for line in events.read_text().splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("event") == "notify-resolved":
            found = NotifyGrant(
                bool(data.get("granted")),
                str(data.get("source", "unset")),
                data.get("detail"),
            )
    return found


def resolved_notify(agent_dir: Path) -> NotifyGrant:
    """The answer this run is holding to, or refused when nothing resolved one.

    Refused is the honest reading of an absent line, not a fallback: no `wfctl
    start` has run on this branch, so nobody has granted anything to it. The
    conservative direction is the same one `auto_approve` takes and for the same
    reason — a state dir that lost this must stop, not proceed.

    A malformed line is skipped rather than raising, matching `session_started`:
    every command appends here, so a truncated final write must not decide the
    authority question by crashing the reader.
    """
    last = _last_resolved(agent_dir)
    return NotifyGrant(False, "unset") if last is None else last


def record_notify_action(agent_dir: Path, action: str) -> None:
    """Record one notifying action that was taken (FR-010).

    Called after the action succeeded, by whatever took it. The log is the
    required destination rather than one of several: it is written whether or
    not a change is open and whether or not the session ends cleanly, and the
    session summary and PR body are renderings of it.
    """
    append_event(agent_dir, "notify-action", action=action)


def record_notify_declined(agent_dir: Path, action: str, reason: str) -> None:
    """Record that the run held the authority and chose not to use it (FR-011).

    Distinct from a refusal, and the distinction is the requirement rather than
    bookkeeping: *the agent decided this was not its call* and *nobody allowed
    this* look identical in a report that files them together, and only one of
    them is a signal that the grant should be widened.

    No count. An earlier draft of the console wording read "declined 6 issue
    writes", and the number contradicts the reason — an agent that declined
    because it could not read the plan confidently cannot also claim it knew
    there were exactly six.
    """
    append_event(agent_dir, "notify-declined", action=action, reason=reason)


def record_notify_refused(agent_dir: Path, action: str, source: str) -> None:
    """Record that the run wanted to notify someone and was not allowed to.

    The other half of FR-011, written where the refusal happens rather than left
    to the actor to remember. `source` travels with it because the five refused
    states are not one event — a tracker that could not be reached is not a
    person withholding authority.
    """
    append_event(agent_dir, "notify-refused", action=action, source=source)


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
        f"## Next Session TODO\n\n"
        f"- [ ] (fill in)\n"
    )


def end(agent_dir: Path, branch: str, observed: Observations) -> tuple[Path, bool]:
    """Write session-summary.md if absent; return its path and whether it wrote.

    The observations are passed in rather than taken here: the caller has
    already built the report, and a second inference is a second chance to
    disagree with the line it is about to print.

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

    append_event(agent_dir, "end", step=observed.step)
    return summary_file, written
