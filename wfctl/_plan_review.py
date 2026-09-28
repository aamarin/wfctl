"""The plan review's contract with wfctl, held in one place.

A review is written by an agent running the `plan-review` skill, and wfctl reads
it back on every status read. The two never share code, so the format between
them is defined here, once, and a test holds these constants against the example
the same wheel ships in the skill's `references/report-format.md`
(`required-sections-are-wfctls`, research R6).

wfctl reads two lines of the report and nothing else:

1. The `plan.md` row of the `## Reviewed inputs` table, which says which plan
   this review read.
2. The `BLOCKER: <n>` line under `## Summary`, which counts the findings of
   priority BLOCKER still open in this report.

Everything else in the report belongs to the skill.

The plan identity is a git blob hash taken with no filters (research R1). The
reviewer computes it with `git hash-object --no-filters`, and `identity` below
computes the same value from the same bytes. Plain `git hash-object` applies a
repository's line-ending rules and clean filters first, and then the two sides
disagree on a plan nobody edited.

A module of its own rather than a part of `_evidence`, because the reader, the
sign-off command, and the review cap all use this one format, and spreading it
across `_evidence`, `_session`, and `cli` would put one contract in three files.
It depends on nothing in wfctl beyond `_io`, so every one of those callers can
import it without a cycle.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

# Both files sit in the feature directory beside `plan.md` (research R7).
REPORT_NAME = "plan-review.md"
COPY_NAME = "plan-review.plan.md"

# The `plan.md` row of `## Reviewed inputs`, matched against one line. The first
# cell is exactly `plan.md`, the second is the identity, and later cells are the
# skill's. The identity has to be 40 lowercase hex characters and fill its cell,
# so an uppercase, truncated, or `absent` value does not match and reads as no
# identity. Treating it as a mismatch instead would call the plan edited when the
# report is what is wrong.
PLAN_IDENTITY_ROW = re.compile(r"^\s*\|\s*plan\.md\s*\|\s*([0-9a-f]{40})\s*\|")

# The open BLOCKER count under `## Summary`, matched against one line. The whole
# line is the count, so a line that says more than the number does not match and
# reads as no count, which holds the pipeline rather than guessing at zero.
BLOCKER_COUNT_LINE = re.compile(r"^BLOCKER:\s*(\d+)\s*$")

# The section each line is read from. Matching either line anywhere in the report
# would pick up a finding that quotes an earlier review's table row or count.
_INPUTS_HEADING = "## Reviewed inputs"
_SUMMARY_HEADING = "## Summary"


class Report(NamedTuple):
    """The two values wfctl reads from a review report.

    Each is `None` when its line is missing or malformed. The reader treats
    both the same way, as promised evidence gone silent
    (`promised-evidence-blocks-on-silence`), and says which one is missing.
    """

    plan_identity: str | None
    open_blockers: int | None


def identity(path: Path) -> str:
    """The git blob hash of the file at `path`, taken from its bytes as they
    are on disk.

    The same value `git hash-object --no-filters <path>` prints, computed here
    so a status read never starts a subprocess and works with no repository at
    all, since the feature directory resolves outside the working tree in this
    repo. A file restored byte for byte gets its old identity back (FR-005).
    """
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def read_report(path: Path) -> Report:
    """The plan identity and the open BLOCKER count from the report at `path`.

    A missing report raises `FileNotFoundError` rather than reading as two
    `None` values. No report and a report with no identity are different pass
    states (data-model.md § Pass state, rows 1 - 2 and 4), and the caller
    tells them apart by checking the file first.

    A section starts at its `##` heading and ends at the next heading of level
    1 or 2, so a `###` subsection stays inside it. The first matching line in
    a section is the one read. Undecodable bytes are replaced rather than
    raised, since both lines are ASCII and a stray byte elsewhere in the report
    should not stop a status read.
    """
    plan_identity: str | None = None
    open_blockers: int | None = None
    section: str | None = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("# ") or line.startswith("## "):
            section = line.rstrip()
            continue
        if section == _INPUTS_HEADING and plan_identity is None:
            row = PLAN_IDENTITY_ROW.match(line)
            if row:
                plan_identity = row.group(1)
        elif section == _SUMMARY_HEADING and open_blockers is None:
            count = BLOCKER_COUNT_LINE.match(line)
            if count:
                open_blockers = int(count.group(1))
    return Report(plan_identity, open_blockers)


# The line of a sign-off section that names the plan it accepted, in the shape
# contracts/report-format.md § The sign-off line gives. wfctl writes it and never
# reads it back: the reader takes a sign-off from the `sign-off` event, so a line
# of this shape typed into the scan file by hand signs nothing off (research R8).
SIGN_OFF_LINE = "- Signed off: plan.md {identity}"


def append_sign_off(scan_path: Path, identity: str, reason: str, compared: bool) -> None:
    """Append one `## Sign-off <UTC timestamp>` section to the scan file.

    One section per sign-off, appended after whatever the file already holds,
    for the reason research R10 gives about reviews: each one binds a different
    plan identity, and a section per run keeps each identity under its own
    heading. A new file starts with the heading the `/plan-review` wrapper
    writes, so a sign-off made before any review section reached this clone
    still produces a file the reviewer recognises.

    `compared` says whether the reviewed plan copy was there to diff against.
    It is written for the pull request reviewer, who otherwise cannot tell a
    sign-off made after reading the change from one made blind.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    section = (
        f"## Sign-off {stamp}\n\n"
        f"{SIGN_OFF_LINE.format(identity=identity)}\n"
        f"- Reason: {reason}\n"
        f"- Reviewed copy: {'compared' if compared else 'missing'}\n"
    )
    existing = scan_path.read_text() if scan_path.exists() else ""
    if not existing:
        issue = scan_path.name.removesuffix("-plan-review.md")
        existing = f"# Plan review scan for #{issue}\n"
    separator = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
    scan_path.parent.mkdir(parents=True, exist_ok=True)
    scan_path.write_text(existing + separator + section)


def _events(agent_dir: Path, branch: str) -> Iterator[dict]:
    """This branch's lines of `events.jsonl`, oldest first.

    Read line by line with a malformed line skipped, as `_stall` reads the same
    file. Every command appends here, and a truncated final write must not make
    a sign-off vanish or a review count twice. A line naming no branch matches
    every branch, which is the convention every other reader of the log keeps;
    `grant_auto_approve` writes its `mode` event with no branch.
    """
    events = agent_dir / "events.jsonl"
    if not events.exists():
        return
    for line in events.read_text().splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        if data.get("branch") not in (None, branch):
            continue
        yield data


def sign_offs(agent_dir: Path, branch: str) -> list[str]:
    """The plan identities this branch's `sign-off` events accepted, oldest first.

    The only source of a sign-off. The scan file carries the same identity, and
    it is never read, since the agent writes that file on every review and a
    line it typed there would be indistinguishable from one wfctl wrote. Only
    `wfctl step sign-off` appends this event, so every sign-off the reader
    honours is also one the review cap counted.
    """
    return [
        data["plan"]
        for data in _events(agent_dir, branch)
        if data.get("event") == "sign-off" and isinstance(data.get("plan"), str)
    ]


def review_count(agent_dir: Path, branch: str, pending: str | None = None) -> int:
    """How many plan reviews and sign-offs this branch made since auto-approve
    was last granted, following data-model.md § Approval mode and the cap.

    1. The count starts at the last `mode` event granting auto-approve. With no
       grant it is 0, since there is nothing to revoke.
    2. The baseline is the `review` value on the last `resume` before that
       grant, so a report that was already there when the grant landed is not
       counted as a review made under it.
    3. Each later `resume` whose `review` differs from the last one seen counts
       once, and each later `sign-off` event counts once.

    A report's hash changing is wfctl's own observation that a review ran,
    which is why the count reads `resume` lines rather than asking the agent.
    A `resume` with no `review` field saw no report, and leaves the last value
    seen in place; a report deleted and restored byte for byte is the same
    review and is not counted again.

    `pending` is the value the calling `resume` is about to record. That call
    has to decide on the cap before it writes its own line, since the line
    carries the `auto` the cap may change, so it passes its value here instead.

    `start` events change nothing. A restart runs `wfctl start` with no flag,
    and a count that reset there would hand an unattended run three new laps
    every time its context filled (FR-022).
    """
    granted = False
    count = 0
    # The last report hash a `resume` recorded. At a grant it is the baseline,
    # and after it each new value is one more review.
    previous: str | None = None
    for data in _events(agent_dir, branch):
        kind = data.get("event")
        if kind == "mode" and data.get("auto_approve") is True:
            granted = True
            count = 0
        elif kind == "resume":
            value = data.get("review")
            if not isinstance(value, str):
                continue
            if granted and value != previous:
                count += 1
            previous = value
        elif kind == "sign-off" and granted:
            count += 1
    if not granted:
        return 0
    return count + (1 if pending is not None and pending != previous else 0)


# Reviews and sign-offs under one grant before auto-approve turns off while the
# pass is outstanding (FR-022). The same number as `_stall.STALL_AFTER`, for its
# reason: a plan legitimately taking a second review is common, and a cap that
# fired on it would stop working automation.
REVIEW_CAP = 3
