"""Whether the loop has stopped making progress, read from the event log.

`speckit-orchestrate` executes whatever `next_command` names for as long as
`auto` reads true, and nothing counted the passes (#332). A step whose evidence
comes from an agent's judgment rather than from a file appearing can complete,
change nothing, and leave itself exactly as current as it found it — and the loop
re-enters it with the same inputs until something external stops it.

The count lives here rather than in the agent because it has to outlive the
agent's memory of it: a run unattended enough to need a bound is one whose
conversation gets cleared or compacted partway, and a session resuming the branch
tomorrow has none of today's passes (`wfctl-counts-the-passes`).

Nothing here is written to remember an attempt. `resume` already appends one line
per pass; what it gained is a digest of the evidence that pass saw, which is
history rather than cached state — a past pass's artifacts cannot be re-derived,
because they have moved since. That is what `session-state-is-re-derived` reserves
for a session file.

**A `resume` line is an observation, not an execution.** It records the step that
is *about to* run, so the line written when the pipeline arrives at a step
predates any attempt at it. Three reviewers each found the same off-by-one in the
first version of this file, which counted lines and called them attempts. What
sits between two identical observations is one attempt that changed nothing, so
`n` identical lines carry `n - 1` attempts — and that difference is the whole of
what `find_stall` returns.

What follows from an observation not being an execution: nothing here can tell a
`resume` that followed a step from one a person ran by hand. Four bare
`wfctl resume` calls in a sitting therefore read as three attempts that changed
nothing, and the next real loop refuses a step that never ran. The remedy is the
same one the report names — move an artifact, or start a new session, since a
`start` event ends the run — and it is written down rather than designed away
because the alternative is the agent reporting its own executions, which is the
tally `wfctl-counts-the-passes` rejects.

A branch with no resolved spec directory records no digest and is therefore
outside the bound entirely: there is nothing to compare. That is correct rather
than a gap — a loop wedged before any feature directory exists is wedged on
something this fingerprint cannot see — but it is wider than the `decompose`
carve-out the design record names, so it is written down here too.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wfctl._predicates import Evidence

# Attempts that changed nothing, not observations of them. Three rather than two
# because a step legitimately taking a second run is common, and a bound that
# fires on the first repeat would stop working automation — the failure this
# feature is least able to afford, since it happens at the hour nobody is
# watching and looks like the feature working.
STALL_AFTER = 3

# What the digest covers, in the order it covers them.
COVERED = ("spec.md", "plan.md", "tasks.md")

# Between the artifacts, so that a byte moving from the end of one file to the
# start of the next changes the result. Without it the digest reads the three as
# one stream and a move between them is invisible.
_SEP = b"\x00"

# The pipeline's name for "no step left". `resume` writes it into the same field
# a real step goes in, and the artifacts of a finished story stop moving by
# definition — so without this the bound reports every completed branch as
# stalled, which inverts the one distinction the payload exists to draw.
_COMPLETE = "complete"


@dataclass(frozen=True)
class Stall:
    """A step that was attempted `passes` times with the evidence unchanged."""

    step: str
    passes: int
    unchanged: tuple[str, ...]


def digest(ev: "Evidence") -> str:
    """A short digest of the artifact text this inference already read.

    From `Evidence` rather than from the rendered step line, which is the level-3
    decision (`332-progress-is-measured-in-artifacts`): `clarify` and `specify`
    both return `Reading("in_progress")` with no reason and no annotation while
    markers stand, so a pass resolving two of six markers renders identically to
    one resolving none. The bytes distinguish them; the rendering cannot.

    `Evidence` holds the *blanked* text — fenced blocks and inline spans are
    replaced before it is built, so an edit confined to a fenced block reads as no
    progress here. That is the same read every predicate makes, which is why it is
    the right one to compare; what it costs is that "unchanged" means unchanged
    outside quoted blocks, and the render sites say so.

    Truncated, because the only question asked of it is whether two passes match.
    A collision costs one missed stop, which a person still catches; carrying the
    full digest costs a longer line in every event forever.
    """
    h = hashlib.sha256()
    for text in (ev.spec_text, ev.plan_text, ev.tasks_text):
        h.update(text.encode("utf-8"))
        h.update(_SEP)
    return h.hexdigest()[:12]


def _passes_this_sitting(events: Path, branch: str | None) -> list[dict]:
    """This sitting's `resume` lines, oldest first, for this branch.

    A malformed line is skipped rather than raising, for the reason
    `session_started` gives about the same file: it is appended to by every
    command, and a truncated final write must not change what the log means. Here
    that is FR-011 — skipping the line compares its neighbours as neighbours,
    which slows the bound by nothing and stops a damaged log from halting a run
    that is working.

    **A sitting boundary ends the previous run.** Two unchanged passes yesterday
    plus today's arrival at the same step is a run of three identical lines, and
    reading straight back through it halts a session before the step has been
    entered once. That is the spec's fourth edge case, and the branch is parked
    rather than stuck. `/start-session` writes the boundary into this same log, so
    it costs a comparison to honour — and `wfctl start` writes one on the path
    that carries almost every sitting after the first, where it used to return at
    its already-initialized guard having recorded nothing. `end` counts too, for
    the sitting that closed properly rather than being abandoned.

    **Filtered by branch**, because `WFCTL_STATE_DIR` can point several branches
    at one log — which is exactly how a notify grant made on a feature branch once
    answered for the trunk, and why `notify-resolved` has carried a branch since.
    Sub-issue branches of one epic are the sharp case here: a grouping map
    resolves them to a single spec dir, so their digests are identical and their
    step names usually are too. A line written before this field existed carries
    no branch and is kept, since dropping it would silently shorten every run on
    an established branch.

    Older wfctl wrote two lines per `resume` at one timestamp, so a single
    observation reads as two on any branch carrying that history — and nothing
    here special-cases it, deliberately. Those lines predate the digest field
    entirely, so the trailing run breaks at the first of them whatever the count
    says. The first version of this file collapsed same-timestamp neighbours to
    handle them, which cost real observations the moment a loop turned twice
    inside one second: four passes counted as two and the bound never fired.
    """
    if not events.exists():
        return []
    out: list[dict] = []
    for line in events.read_text().splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        if branch is not None and record.get("branch") not in (None, branch):
            # Ahead of both reads below, so a *boundary* is branch-scoped too.
            # Under a shared state dir another branch opening a sitting would
            # otherwise clear this branch's history, which delays or suppresses a
            # stall its own run never interrupted.
            continue
        if record.get("event") in ("start", "end"):
            out.clear()
            continue
        if record.get("event") != "resume":
            continue
        out.append(record)
    return out


def opens_a_new_sitting(agent_dir: Path, branch: str | None = None) -> bool:
    """Whether a boundary is worth recording, for `start`'s already-initialized path.

    `wfctl start` is deliberately idempotent in the log — `/start-session` runs it
    on every handoff, so an unconditional append would grow the file with lines
    repeating the previous one, and two tests hold that contract. But the bound
    needs a boundary somewhere: without one, yesterday's unchanged passes stay
    contiguous with today's first, and a branch parked overnight halts before its
    step has been attempted at all in this sitting.

    Both hold if the boundary is written only when the previous sitting actually
    ran something. A second `start` moments after the first has no `resume`
    between them and appends nothing, which is the case those tests pin; a
    session opened over yesterday's work does, and records that it is new.
    """
    events = agent_dir / "events.jsonl"
    if not events.exists():
        return False
    worked = False
    for line in events.read_text().splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        if branch is not None and record.get("branch") not in (None, branch):
            continue
        event = record.get("event")
        if event in ("start", "end"):
            worked = False
        elif event == "resume":
            worked = True
    return worked


def find_stall(
    agent_dir: Path,
    branch: str | None = None,
    current: str | None = None,
    covered: tuple[str, ...] = COVERED,
) -> Stall | None:
    """The attempts behind the trailing run of identical observations.

    `current` is this report's own digest, which `build_report` has already
    computed. Where it differs from the trailing recorded one the artifacts have
    moved since the last pass, so the run is over — without this, `status` goes on
    telling a person the files are unchanged on the screen they look at straight
    after changing them.
    """
    passes = _passes_this_sitting(agent_dir / "events.jsonl", branch)
    if not passes:
        return None

    last = passes[-1]
    step, mark = last.get("step"), last.get("digest")
    if not isinstance(step, str) or not isinstance(mark, str) or step == _COMPLETE:
        return None
    if current is not None and current != mark:
        return None

    observations = 0
    for record in reversed(passes):
        if record.get("step") != step or record.get("digest") != mark:
            break
        observations += 1

    # One attempt sits between each pair of identical observations. The arrival
    # observation is not an attempt, which is why this is a subtraction and not a
    # rename.
    attempts = observations - 1
    return Stall(step=step, passes=attempts, unchanged=covered) if attempts >= STALL_AFTER else None
