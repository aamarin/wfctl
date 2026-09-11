"""Which of an open change's fields are unset, and whether that matters.

`opening-a-change` Step 6 ends with "an open PR is not done: sidebar, reviewers,
the closing keyword your tracker parses." That sentence is skipped, repeatedly,
because nothing disagrees when it is: a run that did it and a run that did not
produce the same observable state. `a-rule-is-expressed-as-a-check` decides what
to do about that — an open change is an artifact the work already produces, so
the rule ships as a check over it.

## Why this is not simply "report every blank field"

Because labels and milestones are GitHub's vocabulary and Gerrit has neither, and
because a repository whose triage someone else controls does not want to be told
its changes have no owner. A check that reported every blank field would be right
here and wrong nearly everywhere, and a noisy check is learned around and then
ignored — which loses the prose *and* the check.

So a blank field is reported only when something already said it should be
filled, and there are exactly two things that can say so: the branch's issue,
whose attributes the change is meant to carry across, and `change_check` in the
repository's own `wfctl.json`. wfctl supplies neither. It holds no field name at
all, which is what lets the same code be correct against a tracker it has never
heard of. `docs/architecture/the-repo-names-the-fields-a-change-must-carry.md`
records that split.

## What is pure here and what is not

`compare` is, and stays that way: two payloads and a list in, rows out, no
repository and no subprocess. That is `_shape.py`'s shape, and it is why every
state in `data-model.md` is reachable from a unit test.

`load_required` is not, and is here rather than in `_verify.py` because that
module's subject is the definition of done. It borrows only `CONFIG_PATH`, so the
file's *location* has one definition while each key's schema lives with the
feature that reads it.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from wfctl._verify import CONFIG_PATH

CONFIG_KEY = "change_check"


@dataclass(frozen=True)
class Field:
    """One key something expected, and whether the change carries it.

    A key nobody expected never becomes a `Field`. The distinction matters more
    than it looks: absent means the check had no opinion, while `satisfied` means
    it had one and the change met it. Collapsing them would make a repository
    that requires nothing indistinguishable from one that requires everything and
    got it.
    """

    key: str
    # `required`, `inherited`, or `unreported` — the last being `wfctl.json`
    # naming a key the backend never emits. Easy to leave out and expensive to:
    # treating an absent key as "nothing required" makes a typo mean the
    # requirement was never written, which is a check that quietly stops
    # checking.
    source: str
    satisfied: bool
    missing: list = field(default_factory=list)
    value: list = field(default_factory=list)
    reported: list = field(default_factory=list)


def _as_list(value: object) -> list:
    """Every payload value as a list, so one comparison serves both shapes.

    A scalar is a one-element set and an unset scalar is an empty one, which
    makes "does the change cover the issue" the only question asked — of a list
    of labels and of a lone milestone alike. The alternative is two branches
    that must agree, and `data-model.md` names the shape rather than the field
    as what chooses between them.
    """
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [v for v in value if v is not None and v != ""]
    return [value]


def compare(
    required: list[str],
    issue_fields: dict | None,
    change_fields: dict,
) -> list[Field]:
    """One row per key something expected, in a stable order.

    `issue_fields` is None when there was no issue to read — a branch carrying no
    key, or a read that did not return. Required keys are still checked in that
    case: what the repository asked for is knowable without the issue, and
    dropping it would report less than the run actually saw.
    """
    rows: list[Field] = []
    inherited = issue_fields or {}

    for key in sorted(set(required) | set(inherited)):
        if key not in change_fields:
            if key in required:
                # Only a *required* key earns this. An issue carrying a key the
                # change's backend does not report is the ordinary state of two
                # trackers with different vocabularies, and nothing the author
                # of this change can act on.
                rows.append(
                    Field(key, "unreported", False, reported=sorted(change_fields))
                )
            continue

        have = _as_list(change_fields[key])
        want = _as_list(inherited.get(key))
        missing = [v for v in want if v not in have]

        if key in required:
            rows.append(Field(key, "required", bool(have) and not missing,
                              missing=missing, value=have))
        elif want:
            rows.append(Field(key, "inherited", not missing,
                              missing=missing, value=have))
        # else: the issue does not carry it and the repository did not ask for
        # it. Nothing true to say, so nothing said.

    return rows


def load_required(repo_root: Path) -> tuple[list[str], list[str]]:
    """Return (required keys, problems). Both empty means nothing is required.

    Problems come back rather than raise, the way `_verify.load_config` returns
    them, so a caller that only wants to know "is anything required" needs no
    guard. A half-valid declaration yields no keys at all: a check that reported
    findings it could not justify from a file it could not read would be worse
    than one that reported none.
    """
    path = repo_root / CONFIG_PATH
    if not path.exists():
        return [], []
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        # `doctor` already reports a malformed `wfctl.json`, and says it better
        # than this reader could. Saying it twice would put the same finding in
        # front of someone opening a change, where it is not what they asked.
        return [], []
    if not isinstance(data, dict):
        return [], []

    declared = data.get(CONFIG_KEY)
    if declared is None:
        return [], []
    if not isinstance(declared, list):
        return [], [f"{CONFIG_PATH}: '{CONFIG_KEY}' must be a list of field names"]

    keys: list[str] = []
    errs: list[str] = []
    for i, entry in enumerate(declared, 1):
        if not isinstance(entry, str):
            errs.append(
                f"{CONFIG_PATH}: '{CONFIG_KEY}' entry {i} must be a field name, "
                f"got {type(entry).__name__}"
            )
        elif not entry.strip():
            errs.append(f"{CONFIG_PATH}: '{CONFIG_KEY}' entry {i} is empty")
        elif entry not in keys:
            keys.append(entry)

    return ([], errs) if errs else (keys, [])


def describe(row: Field) -> str:
    """The line one row renders as, without its marker.

    Here rather than in the command for the reason `_shape.py` gives about its
    own findings: the wording is what a reader acts on, and a string built
    inside a print call is a string no test ever reads. The marker stays with
    the command, because it also has to say things no row produced.
    """
    if row.source == "unreported":
        reports = ", ".join(row.reported) or "nothing"
        return (
            f"required by {CONFIG_PATH}, which the tracker never reports — "
            f"it reports {reports}"
        )

    missing = ", ".join(str(v) for v in row.missing)
    if row.satisfied:
        return ", ".join(str(v) for v in row.value)
    if not row.missing:
        # Required, and blank. There is no issue value to name, so the reason is
        # the whole message.
        return f"empty; required by {CONFIG_PATH}"
    if not row.value:
        return f"empty; issue has {missing}"
    return f"missing {missing}"
