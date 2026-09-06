"""Architecture decision records: parse, validate, supersede, project.

One file, one decision, identified by its slug — the filename without
extension. wfctl reads records; it never mediates their content. What it does
own is the projection (`accepted` only) and the link integrity between records,
because those are the two things a reader cannot get right by eye.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import dropwhile, takewhile
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
    # The file as read, so the one "unreadable file is an excluded record" rule
    # lives in `parse_record` alone. Every reader of a record's prose would
    # otherwise re-open the file and carry its own copy of that policy.
    body: str = ""

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

    An indented key is a nested value, not a top-level setting, and a commented
    line declares nothing at all — `# status: accepted` is a note about the key,
    not the key.
    """
    name, sep, value = line.partition(":")
    if not sep or name.startswith((" ", "\t", "#")):
        return None
    return name.strip(), value.strip().strip("'\"")


def _frontmatter(text: str) -> dict[str, str]:
    """The frontmatter block as key → value, by line scan.

    Scanned rather than parsed: wfctl's runtime dependencies are `typer` and
    `rich`, and one status field does not justify a third. The scan stops at the
    closing delimiter, so a `status:` line quoted in the body is prose and cannot
    set the record's status.

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
        body=text,
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


def decision_text(record: Record) -> str:
    """A record's `## Decision` as the projection prints it, or "".

    The first paragraph, plus — when that paragraph ends in a colon — the
    verbatim block it points at. A colon is a promise the paragraph does not
    keep alone: `knowledge-placement` announces a scope mapping and
    `no-hardcoded-agent` an expansion, and each puts the thing announced in a
    drawing below rather than in the sentence (#226). Not the whole section:
    projecting that takes `arch context` from 52 lines to 245 and buries the
    records around each one.

    The colon is the signal and the following block is not. `layer-model` opens
    with a constraint that stands on its own and follows it with a four-row
    table, so "paragraph followed by a block" is a heuristic with a false
    positive in the corpus it ships against.

    A record whose lead paragraph is grammatical but incomplete is out of reach
    here, and stays that way. `install-modes` names three modes without saying
    which three; `vendor-upstream-skills` leads with a terminology note and puts
    the attribution rule below it. Nothing in the artifact separates those from
    a record whose lead sentence genuinely is the decision, and
    `a-rule-is-expressed-as-a-check` decides that case: a rule whose violation is
    invisible in what the work already produces stays prose.

    The paragraph stops at a blank line, a heading, or a fence delimiter, the
    last so that a Decision opening on a code example does not project the
    example as the decision. That stop reads the raw line and does not go
    through `_unfenced`, which answers a different question — whether a line
    sits inside a fence, not whether the paragraph ended at one. The heading
    scan above is what needs `_unfenced`: a record documenting the record format
    carries a fenced `## Decision` example, and matching it would project
    template text as the contract.

    A carried block is separated from the paragraph by a blank line, which the
    caller splits on to decide what to re-wrap. That is safe to split on because
    the paragraph is joined with `" "` and can never contain one itself.

    Reads `record.body` — `parse_record` already read the file, and a second
    read here would be a second copy of its unreadable-file policy.

    Empty for a record with no `Decision` section, which is a record the
    template did not produce. `arch context` prints the slug alone rather than
    suppressing it: a record accepted without saying what it decided is a
    problem to see, not to hide.
    """
    lines = record.body.splitlines()
    for i, stripped in _unfenced(lines):
        if stripped.lower() != "## decision":
            continue
        after = list(dropwhile(lambda ln: not ln.strip(), lines[i + 1 :]))
        para = list(takewhile(
            lambda ln: ln.strip()
            and not ln.startswith("#")
            and ln.strip()[:3] not in ("```", "~~~"),
            after,
        ))
        text = " ".join(ln.strip() for ln in para)
        if not text.endswith(":"):
            return text
        block = _pointed_at(after[len(para) :])
        if not block:
            return text
        return text + "\n\n" + "\n".join(block)
    return ""


def excluded_by_status(records: list[Record]) -> Counter[str]:
    """Counts of what the projection left out, keyed by status ("" = unreadable).

    Reported rather than dropped: a record silently missing from the contract
    reads as a decision nobody made.
    """
    return Counter(r.status for r in records if not r.in_force)


def _pointed_at(lines: list[str]) -> list[str]:
    """The block a dangling colon points at, given the lines below a paragraph.

    Verbatim and unjoined, fence delimiters kept whole. `knowledge-placement`'s
    mapping is aligned columns, so reflowing it into the sentence is the same
    loss as dropping it, and the fence is what tells the printer not to.

    A fence, a table or a list — the three shapes a colon conventionally points
    at — and nothing else. Prose after a colon is ordinary English: "decided by
    scope, then by what is constrained: the exception is ownership" reads as one
    sentence continued, and carrying it would both project a paragraph the colon
    never promised and leave the colon check with almost no way to fail.

    The list branch is here for the check's sake more than the projection's.
    Nothing in the corpus uses that shape today, but records lean on lists
    heavily, and without the branch a well-formed record turns the corpus test
    red and its author has to reword prose to satisfy the tool — which is the
    objection #226 raised against repairing the records instead of the code.

    Empty otherwise, and that is the finding: the paragraph still ends in a
    colon, so the corpus check fires rather than inventing a block. A list
    broken by a blank line stops at the blank, and an indented code block or a
    blockquote carries nothing at all; both would be reported against the record
    rather than silently half-projected.
    """
    rest = list(dropwhile(lambda ln: not ln.strip(), lines))
    if not rest:
        return []
    opener = rest[0].strip()
    marker = opener[:1]
    run = len(opener) - len(opener.lstrip(marker)) if marker in ("`", "~") else 0
    if run >= 3:
        # The whole delimiter run, not its first three characters. `_unfenced`
        # can truncate because it only ever asks "am I inside a fence"; here the
        # delimiter is re-emitted as output, so a ```` opener closed with ```
        # would project a malformed pair — and a nested ``` would end the block
        # early, losing everything under it.
        fence = marker * run
        body = list(takewhile(lambda ln: not ln.strip().startswith(fence), rest[1:]))
        if len(body) == len(rest) - 1:
            # No closer anywhere below. Carrying to end of file would project
            # `## Considered` and `## Log` as the decision — the 245-line
            # outcome this function rejects — off one missing backtick. Nothing
            # else would catch it, since the projected text then ends in a
            # fence rather than a colon.
            return []
        return [rest[0], *body, fence]
    marker = rest[0].lstrip()
    ordered = marker.split(" ", 1)[0]
    if (
        marker[:1] == "|"
        or marker[:2] in ("- ", "* ")
        or (ordered[:-1].isdigit() and ordered[-1:] in (".", ")"))
    ):
        return list(takewhile(lambda ln: ln.strip(), rest))
    return []


def _unfenced(lines: list[str]) -> Iterator[tuple[int, str]]:
    """`(index, stripped line)` for every line outside a fenced code block.

    Shared by the two heading scans so they cannot disagree about what a fence
    is. A record that documents the record format carries fenced `## Log` and
    `## Decision` examples — `contracts/record-format.md` is exactly such a
    document — and matching one would append a transition inside the example, or
    project the example as the decision the record reached.
    """
    fence = ""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if fence:
            if stripped.startswith(fence):
                fence = ""
            continue
        if stripped[:3] in ("```", "~~~"):
            fence = stripped[:3]
            continue
        yield i, stripped


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
    end = len(lines)
    for i, stripped in _unfenced(lines):
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
