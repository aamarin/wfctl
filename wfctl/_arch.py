"""Architecture decision records: parse, validate, supersede, project.

One file, one decision, identified by its slug — the filename without
extension. wfctl reads records; it never mediates their content. What it does
own is the projection (`accepted` only) and the link integrity between records,
because those are the two things a reader cannot get right by eye.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from wfctl._io import write_md_atomic


IN_FORCE = "accepted"

# The closed set (data-model.md). Anything outside it — including absent and
# misspelled — parses to "" and is excluded, never to `accepted`.
STATUSES = frozenset({"proposed", IN_FORCE, "superseded", "rejected", "retired"})


@dataclass(frozen=True)
class Record:
    """One record as read off disk. `status` is "" when absent or unrecognised."""

    slug: str
    path: Path
    status: str
    supersedes: str

    @property
    def in_force(self) -> bool:
        return self.status == IN_FORCE


@dataclass(frozen=True)
class Finding:
    """A link-integrity problem. `level` is "error" or "warning"."""

    level: str
    slug: str
    message: str


def _frontmatter_end(lines: list[str]) -> int | None:
    """Index just past the frontmatter's key lines; None when there is no block.

    The single place that knows how far frontmatter extends, so the parser and
    `supersede` cannot disagree about which lines are settings and which are
    body prose.

    An unterminated block ends at the last line rather than counting as absent:
    the keys above a missing final `---` are still the ones the author wrote,
    and dropping them would silently blank a record's status.
    """
    if not lines or lines[0].strip() != "---":
        return None
    return next(
        (i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), len(lines)
    )


def _key_value(line: str) -> tuple[str, str] | None:
    """One frontmatter line as `(key, value)`, or None when it declares no key.

    The single rule for what counts as a key, shared by the parser and by
    `supersede`. Two spellings of it are how a record ends up readable and
    un-editable at the same time: `status : accepted` is a status to anything
    that splits on the colon, and not one to anything matching `"status:"` as a
    prefix.

    An indented key is a nested value, not a top-level setting.
    """
    name, sep, value = line.partition(":")
    if not sep or name.startswith((" ", "\t")):
        return None
    return name.strip(), value.strip().strip("'\"")


def _frontmatter(text: str) -> dict[str, str]:
    """The frontmatter block as key → value, by line scan.

    Mirrors `_skill_deployment` in `wfctl/cli.py`: wfctl's runtime dependencies
    are `typer` and `rich`, and one status field does not justify a third. The
    scan stops at the closing delimiter, so a `status:` line quoted in the body
    is prose and cannot set the record's status.

    A repeated key takes the last value, as a YAML parser would.
    """
    lines = text.splitlines()
    end = _frontmatter_end(lines)
    if end is None:
        return {}
    found: dict[str, str] = {}
    for line in lines[1:end]:
        pair = _key_value(line)
        if pair is not None:
            found[pair[0]] = pair[1]
    return found


def parse_record(path: Path) -> Record:
    """Read one record. Never raises: an unreadable file is an excluded record.

    A record root is a directory anyone can drop a file into, so one undecodable
    file must not take down the read of the whole set. It comes back with an
    empty status, which `validate` and the projection both treat as excluded —
    and which `arch context` names rather than dropping silently.
    """
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return Record(slug=path.stem, path=path, status="", supersedes="")
    front = _frontmatter(text)
    status = front.get("status", "")
    return Record(
        slug=path.stem,
        path=path,
        status=status if status in STATUSES else "",
        supersedes=front.get("supersedes", ""),
    )


def load_records(root: Path) -> list[Record]:
    """Every record under `root`, by slug. A missing root holds no records.

    Sorted by slug, per `data-model.md`, so the projection is stable across runs
    — an unordered listing turns every `arch context` into a diff against
    itself. By slug and not by filename: `-` sorts before `.`, so sorting on the
    name puts `layer-model.md` ahead of `layer.md`.
    """
    if not root.is_dir():
        return []
    return [parse_record(p) for p in sorted(root.glob("*.md"), key=lambda p: p.stem)]


def validate(records: list[Record]) -> list[Finding]:
    """Link integrity across the record set: VR-002, VR-003, VR-004.

    Only the rules checkable from the set alone. The status *transitions* in
    data-model.md are a review convention — records are hand-edited markdown and
    wfctl does not mediate the edits, so a status moved along an illegal path is
    not detectable here. VR-001 needs no check: an illegal value never parses.
    """
    slugs = {r.slug for r in records}
    findings: list[Finding] = []
    claimed: dict[str, list[str]] = {}

    for record in records:
        if not record.supersedes:
            continue
        if record.supersedes == record.slug:
            # Never recorded as claimed: a self-reference would otherwise satisfy
            # VR-003 and mark the record its own successor, silencing the VR-002
            # orphan warning below. One typo would then suppress the finding that
            # exists to catch it.
            findings.append(Finding("error", record.slug, "supersedes itself"))
            continue
        claimed.setdefault(record.supersedes, []).append(record.slug)
        if record.supersedes not in slugs:
            # VR-003: an error, not a warning. The reason the predecessor fell is
            # what the value points at; dangling, the record cannot be read.
            findings.append(Finding(
                "error", record.slug,
                f"supersedes '{record.supersedes}', which is not a record here",
            ))

    for record in records:
        if record.status == "superseded" and record.slug not in claimed:
            # VR-002: a warning, because the usual cause is a successor that
            # exists on an unmerged branch — true of every record mid-review.
            findings.append(Finding(
                "warning", record.slug,
                "is superseded, but no record supersedes it",
            ))

    for target, successors in sorted(claimed.items()):
        if len(successors) > 1:
            # VR-004: split supersession. Two people replaced one decision
            # independently; no rule picks a winner, so a human reconciles it.
            findings.append(Finding(
                "error", target,
                f"is superseded by {len(successors)} records: {', '.join(sorted(successors))}",
            ))

    return findings


def in_force(records: list[Record]) -> list[Record]:
    """The projection: `accepted` records only, in the order given."""
    return [r for r in records if r.in_force]


def excluded_by_status(records: list[Record]) -> Counter[str]:
    """Counts of what the projection left out, keyed by status ("" = unreadable).

    Reported rather than dropped: a record silently missing from the contract
    reads as a decision nobody made.
    """
    return Counter(r.status for r in records if not r.in_force)


def _log_bounds(lines: list[str]) -> tuple[int, int] | None:
    """`(heading index, insertion index)` for the `## Log` section, or None.

    Fenced code blocks are skipped. A record that documents the record format
    contains a fenced `## Log` — `contracts/record-format.md` is exactly such a
    document — and matching it would append the transition inside that example,
    editing an accepted record's body (VR-005) while the real log below never
    records the change.

    The insertion index is the end of the Log section, not end of file: `Log` is
    last by convention only, and appending blind files the transition under
    whatever heading follows. Trailing blank lines stay below the new entry so
    the gap before the next heading survives.
    """
    heading: int | None = None
    fence = ""
    end = len(lines)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if fence:
            if stripped.startswith(fence):
                fence = ""
            continue
        if stripped[:3] in ("```", "~~~"):
            fence = stripped[:3]
            continue
        if heading is None:
            if stripped.lower() == "## log":
                heading = i
        elif stripped.startswith("## "):
            end = i
            break
    if heading is None:
        return None
    while end > heading + 1 and not lines[end - 1].strip():
        end -= 1
    return heading, end


def supersede(record: Record, date: str, reason: str) -> None:
    """Mark `record` superseded: change `status`, append one `Log` line.

    Nothing else in the file is touched (VR-005). An accepted record's body is
    the decision as it was agreed — git holds the edit history, and the file
    holds only what git cannot answer. A changed decision is a new record, so
    rewriting this one would destroy the predecessor the successor points at.

    Raises rather than half-applying, writing nothing in either case: a record
    whose frontmatter declares no `status:`, and one with no `## Log` section to
    append to. The log is where a transition becomes visible, so changing a
    status with nowhere to record it is the silent edit this function exists to
    prevent.
    """
    # newline="": `read_text` translates CRLF to LF, which would rewrite every
    # line in a CRLF record — a whole-body diff from a function contracted to
    # change one field and add one line.
    with record.path.open(newline="") as f:
        lines = f.read().splitlines(keepends=True)

    end = _frontmatter_end(lines)
    if end is None:
        raise ValueError(f"{record.path}: no status line to change")
    # Backwards, because `_frontmatter` takes the last of a repeated key. Editing
    # the first would change a line the parser ignores: the log would record a
    # transition and the record would still read as it did before.
    status = next(
        (
            i for i in reversed(range(1, end))
            if (kv := _key_value(lines[i])) is not None and kv[0] == "status"
        ),
        None,
    )
    if status is None:
        raise ValueError(f"{record.path}: no status line to change")

    bounds = _log_bounds(lines)
    if bounds is None:
        raise ValueError(f"{record.path}: no '## Log' section to append to")
    _, insert_at = bounds

    eol = "\r\n" if lines[0].endswith("\r\n") else "\n"
    lines[status] = f"status: superseded{eol}"
    # A file need not end in a newline, and joining onto one that doesn't would
    # weld the new entry onto the previous line — two transitions on one line,
    # and the predecessor's entry destroyed.
    if insert_at > 0 and not lines[insert_at - 1].endswith(("\n", "\r")):
        lines[insert_at - 1] += eol
    lines.insert(insert_at, f"- {date}  superseded  — {reason}{eol}")

    # Atomic, like every other markdown wfctl rewrites (`_session.py:88`). This
    # one matters more than those: a session summary is re-derivable, while an
    # accepted record is hand-authored and committed, so a torn write loses a
    # decision no later run can reconstruct.
    write_md_atomic(record.path, "".join(lines), newline="")
