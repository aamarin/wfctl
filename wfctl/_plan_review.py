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
import re
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
