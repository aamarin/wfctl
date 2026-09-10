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
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wfctl._predicates import Evidence

# Three rather than two. A step legitimately taking a second run is common, and a
# bound that fires on the first repeat would stop working automation — the
# failure this feature is least able to afford, because it happens at the hour
# nobody is watching and looks like the feature working.
STALL_AFTER = 3

# What the digest covers, in the order it covers them. Named here rather than at
# the call site so the report can say which artifacts did not move without
# re-deriving the list from the hash it cannot read.
COVERED = ("spec.md", "plan.md", "tasks.md")

# Between the artifacts, so that a byte moving from the end of one file to the
# start of the next changes the result. Without it the digest reads the three as
# one stream and a move between them is invisible.
_SEP = b"\x00"


@dataclass(frozen=True)
class Stall:
    """A step that ran `passes` times with the evidence unchanged between them."""

    step: str
    passes: int
    unchanged: tuple[str, ...] = COVERED


def digest(ev: "Evidence") -> str:
    """A short digest of the artifact text this inference already read.

    From `Evidence` rather than from the rendered step line, which is the level-3
    decision (`332-progress-is-measured-in-artifacts`): `clarify` and `specify`
    both return `Reading("in_progress")` with no reason and no annotation while
    markers stand, so a pass resolving two of six markers renders identically to
    one resolving none. The bytes distinguish them; the rendering cannot.

    Truncated, because the only question asked of it is whether two passes match.
    A collision costs one missed stop, which a person still catches; carrying the
    full digest costs a longer line in every event forever.
    """
    h = hashlib.sha256()
    for text in (ev.spec_text, ev.plan_text, ev.tasks_text):
        h.update(text.encode("utf-8"))
        h.update(_SEP)
    return h.hexdigest()[:12]


def _resume_events(events: Path) -> list[dict]:
    """Every `resume` line, oldest first, with the legacy double-write collapsed.

    A malformed line is skipped rather than raising, for the reason
    `session_started` gives about the same file: it is appended to by every
    command, and a truncated final write must not change what the log means. Here
    that is FR-011 — skipping the line compares its neighbours as neighbours,
    which slows the bound by nothing and stops a damaged log from halting a run
    that is working.

    Older wfctl wrote two lines per `resume` carrying the same timestamp, so a
    single pass reads as two and the bound would fire a pass early. Adjacent
    lines sharing a timestamp are therefore one pass. Two genuine passes inside
    one second would also collapse, which undercounts — the bound fires late
    rather than early, and late is the direction this feature already chose.
    """
    if not events.exists():
        return []
    out: list[dict] = []
    for line in events.read_text().splitlines():
        try:
            record = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(record, dict) or record.get("event") != "resume":
            continue
        if out and out[-1].get("ts") == record.get("ts"):
            # The later line of a legacy pair carries the richer fields.
            out[-1] = record
            continue
        out.append(record)
    return out


def find_stall(agent_dir: Path) -> Stall | None:
    """The trailing run of passes sharing a step and a digest, when it is long enough.

    Read from the end, because only consecutive passes count: a branch resumed
    days later, or a step returned to after the pipeline moved on, is not the same
    situation as a step that cannot get out of its own way. The run stops at the
    first pass that differs in either field — which is what resets the count when
    a pass makes progress — and at the first that carries no digest, since a pass
    whose evidence was never recorded cannot be compared to one whose was.
    """
    passes = _resume_events(agent_dir / "events.jsonl")
    if not passes:
        return None

    last = passes[-1]
    step, mark = last.get("step"), last.get("digest")
    if not isinstance(step, str) or not isinstance(mark, str):
        return None

    run = 0
    for record in reversed(passes):
        if record.get("step") != step or record.get("digest") != mark:
            break
        run += 1

    return Stall(step=step, passes=run) if run >= STALL_AFTER else None
