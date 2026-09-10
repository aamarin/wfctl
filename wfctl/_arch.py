"""Architecture decision records: parse, validate, supersede, project.

One file, one decision, identified by its slug — the filename without
extension. wfctl reads records; it never mediates their content. What it does
own is the projection (`accepted` only) and the link integrity between records,
because those are the two things a reader cannot get right by eye.
"""
from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import dropwhile, takewhile
from pathlib import Path

from wfctl import _md
from wfctl._io import write_atomic


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

    Index is 0-based, because both callers use it to slice `lines`. `_md.walk`
    numbers from 1 for findings that name a line to a reader, so the conversion
    happens here rather than at both call sites.

    The fence delimiters are excluded too. The walk reports them as outside —
    `_pointed_at` prints one, and reads it from `lines` directly — but a heading
    scan that saw a bare ``` would be scanning the boundary of the example it is
    trying to skip.

    Two rules tightened when this moved to `_md`, and both narrow what opens or
    closes a fence rather than widening it. A fence indented four spaces or more
    no longer opens one — at four the line is an indented code block, which is
    markdown's rule and not this module's — so a record whose fence is nested
    inside a list item now has its headings seen rather than skipped. And a
    closing run must match the opening character, be at least as long, and carry
    no info string, where the old prefix match let any three of the character
    close any fence. A record using ```` to quote a ```-block is the shape that
    was read wrong before; a record closing a ````-fence with a bare ``` is the
    shape that changes meaning now, and `supersede` refuses it rather than
    editing the wrong section.
    """
    for line in _md.walk_lines(lines):
        if not line.inside and not line.fence:
            yield line.number - 1, line.text.strip()


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


# The width every `Log` line in this repository's records already pads its status
# word to — `accepted` and four spaces, `superseded` and two. It was two literal
# spaces inside `supersede`'s f-string while there was one transition and nothing
# to align against; a second transition is what makes it a column, and a column
# nobody names is one the third caller gets wrong.
_LOG_STATUS_WIDTH = 12


def _set_status(record: Record, status: str, date: str, note: str) -> str:
    """Change `record`'s status to `status` and append one `Log` line saying so.

    The whole of a status transition, shared by the two that exist. Not because
    the two are the same decision — `supersede` and `accept` differ in who may
    call them and on what — but because the *file* is the same file, and four of
    the things that go wrong here are properties of the format rather than of the
    transition. `_frontmatter_end` and `_key_value` each say in their own
    docstring that they exist so the parser and `supersede` cannot disagree; a
    second hand-written copy of this body is where that agreement would be lost,
    silently, one hazard at a time.

    Nothing else in the file is touched (VR-005). An accepted record's body is
    the decision as it was agreed — git holds the edit history, and the file
    holds only what git cannot answer.

    Raises rather than half-applying, writing nothing in any case: a record whose
    frontmatter declares no `status:`, one with no `## Log` section to append to,
    and a `note` carrying a line break. The log is where a transition becomes
    visible, so changing a status with nowhere to record it is the silent edit
    this function exists to prevent.

    A line break in `note` is the sharpest of the three, because it does not look
    like a failure. One `Log` entry is one line, so a note carrying a break writes
    a *second* entry — well-formed, indistinguishable from a real one, and dated
    by whoever supplied the note. `accepted_on` then reports that date, which is
    the one thing about a transition nobody can re-derive from the file. Refused
    here rather than at each caller so `supersede`'s reason is covered by the same
    rule: neither caller's field is more trusted than the other's, and a citation
    pasted from a review thread is multi-line without anyone intending anything.

    Returns the entry it wrote, so a caller reporting the transition quotes the
    line rather than re-composing it from the same parts — two spellings of one
    line are two spellings that can drift.
    """
    if "\n" in note or "\r" in note:
        raise ValueError(
            f"{record.path}: a log entry is one line, and this note carries a "
            "line break — it would write a second entry nothing distinguishes "
            "from a real one"
        )
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
    status_line = next(
        (
            i for i in reversed(range(1, end))
            if (kv := _key_value(lines[i])) is not None and kv[0] == "status"
        ),
        None,
    )
    if status_line is None:
        raise ValueError(f"{record.path}: no status line to change")

    bounds = _log_bounds(lines)
    if bounds is None:
        raise ValueError(f"{record.path}: no '## Log' section to append to")
    _, insert_at = bounds

    eol = "\r\n" if lines[0].endswith("\r\n") else "\n"
    lines[status_line] = f"status: {status}{eol}"
    # A file need not end in a newline, and joining onto one that doesn't would
    # weld the new entry onto the previous line — two transitions on one line,
    # and the predecessor's entry destroyed.
    if insert_at > 0 and not lines[insert_at - 1].endswith(("\n", "\r")):
        lines[insert_at - 1] += eol
    entry = f"- {date}  {status:<{_LOG_STATUS_WIDTH}}— {note}"
    lines.insert(insert_at, entry + eol)

    # Atomic, like every other markdown wfctl rewrites (`_session.py:88`). This
    # one matters more than those: a session summary is re-derivable, while an
    # accepted record is hand-authored and committed, so a torn write loses a
    # decision no later run can reconstruct.
    write_atomic(record.path, "".join(lines), newline="")
    return entry


def supersede(record: Record, date: str, reason: str) -> str:
    """Mark `record` superseded: change `status`, append one `Log` line.

    No guard on the current status, unlike `accept`. What a `Log` line here names
    is the successor that replaced this record, so a second one is a second
    successor — a claim that may be wrong but is not self-contradictory. Which
    statuses may be superseded is a question nothing has yet had to answer.
    """
    return _set_status(record, "superseded", date, reason)


def accepted_on(record: Record) -> str:
    """The date this record's `Log` says it was accepted, or "" when it says none.

    Read out of the log rather than out of git, because the log is the answer the
    file itself gives and git's is a different question — when the *file* changed,
    which for a record moved between repositories or committed late is not when
    anyone agreed to it.

    Empty for every record accepted before there was a command to log it, which is
    most of the ones already in force. That is a real answer and the caller renders
    it as one; the alternative is a date inferred from somewhere the record does
    not point at, which is the substitution this whole transition exists to refuse.

    The last such line wins, matching `_frontmatter`'s rule for a repeated key: a
    log is appended to, so the last entry is the current one.

    Scoped to the `## Log` section rather than run over the body, for the reason
    `_log_bounds` exists at all: a record is free to *show* a log entry above its
    own log — a format being documented, a predecessor being quoted — and outside
    a fence that line is indistinguishable from the real thing. `_unfenced` covers
    the fenced case and only that one.
    """
    lines = record.body.splitlines(keepends=True)
    bounds = _log_bounds(lines)
    if bounds is None:
        return ""
    heading, end = bounds
    found = ""
    for _, stripped in _unfenced(lines[heading:end]):
        # The rendered shape `_set_status` writes, matched loosely enough to also
        # catch the hand-written entries that predate it — those pad to the same
        # column but were typed, so a stricter match would silently read them as
        # absent and report every pre-existing record as unlogged.
        m = re.match(r"-\s+(\d{4}-\d{2}-\d{2})\s+accepted\b", stripped)
        if m:
            found = m.group(1)
    return found


def accept(record: Record, date: str, citation: str) -> str:
    """Mark `record` accepted: change `status`, append one `Log` line.

    The transition `a-human-accepts-a-decision` gives a human. wfctl performs it
    and records where the agreement happened; it never decides that one did.
    `citation` is written into the log and never read back — whether it is true
    has no objective test, and the record says so rather than implying a check.

    Only `proposed` promotes. Refusing an already-accepted record is the guard
    `supersede` does not carry, and it is not symmetry for its own sake: a second
    `accepted` line asserts a second agreement that never happened, in the one
    field this whole transition exists to make trustworthy.

    The exception carries the refused status and no message. `wfctl arch accept`
    does not read it — it holds the record already and picks its wording from
    `record.status` before calling, because three statuses need three different
    sentences and only the console knows what they are. What the payload is for is
    the caller that is not that one: a status is the only thing about this refusal
    that cannot be recovered from the record afterwards, since by then it is
    whatever the caller decided to do next.
    """
    if record.status != "proposed":
        raise ValueError(record.status)
    return _set_status(record, IN_FORCE, date, citation)
