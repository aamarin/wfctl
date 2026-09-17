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

# A tuple, where `STATUSES` is a frozenset: the accept refusal prints these
# names, and the order they print in is the order the guidance lists them in
# (FR-012, data-model.md "Diagram kind"). Nothing prints `STATUSES`.
DIAGRAM_KINDS = ("data-flow", "component", "state")


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
    # Verbatim, including a value outside `DIAGRAM_KINDS` — unlike `status`,
    # which normalises an unrecognised value to "". Normalising here has no
    # safe direction: folding `dataflow` into "" would report "declares no
    # kind" against a file whose author declared one, and the author cannot
    # see the difference between their typo and an omission. VR-006 is what
    # names the value instead (data-model.md, R-001).
    diagram: str = ""

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
        diagram=front.get("diagram", ""),
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
    """Link integrity across the record set (VR-002, VR-003, VR-004), plus the
    diagram-kind and label-agreement rules this feature added (VR-006, VR-007).

    Only the rules checkable from the set alone. The status *transitions* in
    data-model.md are a review convention — records are hand-edited markdown and
    wfctl does not mediate the edits, so a status moved along an illegal path is
    not detectable here. VR-001 needs no check: an illegal value never parses.
    There is no VR-005 check here by design — it is the frozen-body rule,
    enforced by convention, not code.
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

    for record in records:
        # VR-006: an error, and run on every status, accepted included — it
        # reads the frontmatter, which VR-005 does not freeze, and a
        # misspelled kind is wrong whatever the record's status. "" is
        # excluded: absent means "not declared", which `accept_blockers`
        # covers at the transition that actually needs it, not here.
        if record.diagram and record.diagram not in DIAGRAM_KINDS:
            findings.append(Finding(
                "error", record.slug,
                f"declares diagram '{record.diagram}', which is not a diagram kind",
            ))

    for record in records:
        # VR-007: a warning, and `proposed` only (R-005). `superseded` and
        # `retired` records were accepted once, so their bodies are frozen by
        # the same rule VR-005 already applies to `accepted`; `rejected`
        # records are never accepted, so a finding against one names work
        # nobody will do.
        if record.status != "proposed":
            continue
        drawing = _drawing(record)
        if not drawing:
            continue
        # The rest of the record, with the `## Boundary` section removed
        # entirely — comparing a label against the drawing it came from would
        # let the label satisfy itself: its own words are always "present" in
        # a body that includes the fence they were read out of.
        lines = record.body.splitlines()
        bounds = _section_bounds(lines, "## boundary")
        rest = lines if bounds is None else lines[: bounds[0]] + lines[bounds[1] :]
        record_words = _content_words("\n".join(rest))
        for label in _labels(drawing):
            label_words = _content_words(label)
            # No readable words at all — an ASCII sketch, a fence of prose —
            # compares nothing rather than inventing a finding (research R-004's
            # stated limit).
            if label_words and not (label_words & record_words):
                findings.append(Finding(
                    "warning", record.slug,
                    f"drawing label '{label}' appears nowhere else in the record",
                ))

    return findings


def _drawing(record: Record) -> str:
    """The text inside the first fenced block under `## Boundary`, or "".

    Content is never inspected (clarification Q2) — a fenced block holding
    prose is a drawing to this feature, because the alternative is a rule that
    tells a picture from a code sample, which the corpus does not support. An
    interior that is empty or whitespace-only is not content, though: it is
    the same "nothing drawn" `bounds is None` already returns "" for, so it is
    stripped before the truthiness check a caller makes.

    The first block, not all of them: a second fence under the same heading is
    a second drawing of the same boundary, and nothing here needs to choose
    between them. "First" is tracked by the opening delimiter, not by whether
    anything was collected — an empty first block still ends the search, so a
    scratch fence left blank does not fall through to whatever real drawing
    follows it.

    Reads `_md.walk_lines` directly rather than `_unfenced`, which deliberately
    yields the complement of what this needs — lines *outside* a fence. This is
    the one caller in the module that wants the interior.
    """
    lines = record.body.splitlines()
    bounds = _section_bounds(lines, "## boundary")
    if bounds is None:
        return ""
    heading, end = bounds
    interior: list[str] = []
    opened = False
    for line in _md.walk_lines(lines[heading:end]):
        if line.inside:
            interior.append(line.text)
        elif line.fence:
            if not opened:
                # The block's own opening delimiter — not a stop, the start of
                # what we're reading.
                opened = True
                continue
            # The closing delimiter of the block we opened — stop here,
            # whether or not it had any interior, rather than continue into a
            # second fence this function does not read.
            break
    return "\n".join(interior).strip()


def _kind_list(sep: str, last_sep: str) -> str:
    """`DIAGRAM_KINDS` joined for a sentence, e.g. "a, b or c".

    One place for the two shapes the blockers and the CLI refusal need —
    `" | "` for a value to paste into frontmatter, `", "` plus `"or"` for a
    sentence — so the three names are typed once here and nowhere else.
    """
    if len(DIAGRAM_KINDS) <= 1:
        return sep.join(DIAGRAM_KINDS)
    return sep.join(DIAGRAM_KINDS[:-1]) + last_sep + DIAGRAM_KINDS[-1]


def accept_blockers(record: Record) -> list[str]:
    """Every reason `accept` would refuse `record`, in reading order.

    The single definition `acceptable` and `accept` both read (research R-002)
    — `acceptable`'s own docstring already named the failure a second copy
    produces: a listing built from status alone names a record whose own
    suggested command then fails.

    Status is not among them. `acceptable` tests `status == "proposed"` itself
    and `accept` raises `ValueError(record.status)` as it does today — three
    statuses need three different sentences, chosen by the console from
    `record.status`, and folding them in here would make one list carry two
    vocabularies.

    Order is reading order, and it is load-bearing for FR-005: a record with
    no drawing and no declared kind reports the drawing first, because adding a
    kind to a record with nothing drawn fixes nothing. The kind blockers are
    not conditioned on a drawing being present — `contracts/cli.md`'s own
    refusal example shows both firing together — so an author sees everything
    wrong with the record in one pass rather than discovering the second gap
    only after fixing the first.
    """
    blockers: list[str] = []
    if _log_bounds(record.body.splitlines(keepends=True)) is None:
        blockers.append("no '## Log' section to append to")
    if not _drawing(record):
        blockers.append("no drawing: add a fenced block under '## Boundary'")
    if not record.diagram:
        blockers.append(
            f"no declared kind: add 'diagram: {_kind_list(' | ', ' | ')}' to the frontmatter"
        )
    elif record.diagram not in DIAGRAM_KINDS:
        blockers.append(
            f"'{record.diagram}' is not a diagram kind — use {_kind_list(', ', ' or ')}"
        )
    return blockers


# A node label: quoted, bracketed, braced, or piped — the shapes mermaid
# accepts for display text. `[*]` is excluded at the call site rather than
# here, because the pattern that matches it is the same pattern that matches
# every other bracketed label; the exclusion is content, not syntax.
#
# The bracketed pattern prefers a quoted interior, because `[^\]]*` alone stops
# at the first `]` — and a quoted label is allowed to contain one, so
# `["Use [cache]"]` would otherwise be read as the fragment `"Use [cache`.
_QUOTED_LABEL = re.compile(r'"([^"]*)"')
_BRACKETED_LABEL = re.compile(r"\[(\"[^\"]*\"|[^\]]*)\]")
_BRACED_LABEL = re.compile(r"\{([^}]*)\}")

# An edge label — `-->|text|`, `--x|text|`, `-.->|text|`. The arrow is required,
# and required to be adjacent: a bare `|text|` is how ASCII box art draws a cell
# wall, and matching that would hand the check two labels for every row of a
# table it is supposed to read nothing from (R-004's stated limit).
_EDGE_LABEL = re.compile(r"([-.=]{2,}[>xo]?)\|([^|]*)\|")

# A rounded or circular node — `A(text)`, `A((text))`. The node id must be
# adjacent for the same reason the arrow is above: a bare `(text)` is an aside
# in ordinary prose, and a transition label is allowed to contain one, so
# matching it loose would split `A --> B: refuses (silently)` into two labels.
# Circles are read first; `[^)]*` cannot cross the inner `)` of a double paren.
_CIRCLE_LABEL = re.compile(r"\w+\(\(([^)]*)\)\)")
_ROUNDED_LABEL = re.compile(r"\w+\(([^)]*)\)")

# Alphanumeric tokens. `\w` also matches `_`, which a slug or an identifier
# quoted in a drawing could carry, and treating `arch_root` as one token is
# the reading a content-word comparison wants.
_TOKEN = re.compile(r"[A-Za-z0-9_]+")

# Closed-class English: articles, prepositions, conjunctions, pronouns,
# auxiliaries — words that carry no concept of their own, so a label built
# entirely from them would compare against nothing and a label that merely
# contains one alongside a real word must not count the closed-class word as
# evidence either way. Short (two characters or fewer, per data-model.md) is
# excluded by length rather than by listing every one.
_STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "and", "or", "nor", "but", "not", "with", "for", "from", "into", "onto",
    "off", "out", "over", "under", "than", "then", "when", "what", "which",
    "who", "whom", "whose", "that", "this", "these", "those", "may", "can",
    "could", "will", "would", "shall", "should", "has", "have", "had",
    "does", "did", "its", "his", "her", "their", "our", "your", "you",
    "own", "per", "via", "all", "any", "one", "two", "each", "every",
    "ever", "never", "always", "yet", "so", "too", "also", "only", "just",
    "itself", "themselves", "there", "here", "now",
})


def _content_words(text: str) -> set[str]:
    """Alphanumeric tokens longer than two characters, closed-class English
    excluded, lowercased so a comparison is case-insensitive."""
    return {
        tok for tok in (t.lower() for t in _TOKEN.findall(text))
        if len(tok) > 2 and tok not in _STOPWORDS
    }


def _labels(drawing: str) -> list[str]:
    """Every node label in `drawing`: piped, bracketed, braced, quoted, a bare
    `subgraph` title, or the text after `:` on a transition line.

    `<br/>` and `<br>` become whitespace before any of the shapes are read, so
    a wrapped label reads as the one phrase its author wrote rather than as
    line-broken fragments. `[*]` — mermaid's start/end marker — yields no
    label; it is a syntax element, not a name for anything.

    Each shape removes what it reads before the next one runs, so one label is
    never reported twice. `A["a label"]` is mermaid's own common shape — a
    quoted string inside brackets — and reading the quote separately as well
    would report one label as two.

    Order is what keeps a mixed transition label whole. `A --> B: known "x"` is
    one label, and a bare-quote scan running first would take `"x"` out of it
    and leave `known` behind as a second — so the colon scan runs before it and
    claims the whole tail.

    Three shapes are syntax rather than names and yield nothing: a `%%` comment
    line, which mermaid ignores whatever it contains; `:::`, which attaches a
    CSS class; and a `subgraph` title that is bracketed or quoted, already read
    as a label by the shape it is written in.
    """
    text = drawing.replace("<br/>", " ").replace("<br>", " ")
    found: list[str] = []

    def _unquote(content: str) -> str:
        if content[:1] == '"' and content[-1:] == '"' and len(content) >= 2:
            return content[1:-1]
        return content

    def _take(m: re.Match[str]) -> str:
        content = _unquote(m.group(1).strip())
        if content and content != "*":
            found.append(content)
        return ""

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("%%"):
            continue
        if stripped.startswith("subgraph "):
            title = stripped[len("subgraph ") :].strip()
            if title and "[" not in title and '"' not in title:
                found.append(title)
                continue

        def _take_edge(m: re.Match[str]) -> str:
            content = _unquote(m.group(2).strip())
            if content and content != "*":
                found.append(content)
            return m.group(1)

        remainder = _EDGE_LABEL.sub(_take_edge, line)
        remainder = _BRACED_LABEL.sub(_take, _BRACKETED_LABEL.sub(_take, remainder))
        remainder = _ROUNDED_LABEL.sub(_take, _CIRCLE_LABEL.sub(_take, remainder))
        if "-->" in remainder:
            arrow = remainder.index("-->")
            colon = remainder.find(":", arrow)
            if colon != -1 and remainder[colon : colon + 3] != ":::":
                after = _unquote(remainder[colon + 1 :].strip())
                if after:
                    found.append(after)
                remainder = remainder[:colon]
        _QUOTED_LABEL.sub(_take, remainder)
    return [label.strip() for label in found if label.strip()]


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


def _section_bounds(lines: list[str], heading: str) -> tuple[int, int] | None:
    """`(heading index, end index)` for the first `## <heading>` section, or None.

    Generalised out of `_log_bounds`, once `_drawing` needed the identical rule
    for `## Boundary` (research R-003). Both reasons `_log_bounds`'s docstring
    gave for its own shape hold unchanged here: fenced examples are skipped — a
    record documenting the record format carries a fenced example of the very
    heading being matched, `contracts/record-format.md` for `## Log` and
    `## Boundary` alike — and the section ends at the next `## `, not at end of
    file, so a scan does not run past what it was asked to bound.

    `heading` is matched case-insensitively against a stripped line, so a caller
    passes it lowercase (`"## log"`, `"## boundary"`) and need not think about
    the file's own casing.

    No trailing-blank trim here — that is `_log_bounds`'s own need for an
    insertion point, not a property of "where does this section end".
    """
    heading_idx: int | None = None
    end = len(lines)
    target = heading.lower()
    for i, stripped in _unfenced(lines):
        if heading_idx is None:
            if stripped.lower() == target:
                heading_idx = i
        elif stripped.startswith("## "):
            end = i
            break
    if heading_idx is None:
        return None
    return heading_idx, end


def _log_bounds(lines: list[str]) -> tuple[int, int] | None:
    """`(heading index, insertion index)` for the `## Log` section, or None.

    A call to `_section_bounds`, trimmed to an insertion point: `Log` is last by
    convention only, and appending blind files the transition under whatever
    heading follows. Trailing blank lines stay below the new entry so the gap
    before the next heading survives — the one thing `_section_bounds` does not
    do, because it is this caller's need and not `## Boundary`'s.
    """
    bounds = _section_bounds(lines, "## log")
    if bounds is None:
        return None
    heading, end = bounds
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


def acceptable(record: Record) -> bool:
    """Whether `accept` could act on this record without raising.

    `proposed` is necessary but not sufficient — `accept_blockers` names the
    rest: a `## Log` section to append the transition to, a drawing, and a
    declared kind that `accept` would otherwise refuse. A listing built from
    status alone names a record whose own suggested command then fails, which
    is not a sentence anyone reading a list of "promotable" records was told to
    expect.

    Exported rather than left for `cli` to reimplement: `accept_blockers` is a
    module member (`the-underscore-is-the-module-contract`), and a second copy
    of this rule at the call site is the kind of copy that stops agreeing with
    this one silently.
    """
    return record.status == "proposed" and not accept_blockers(record)


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

    Also raises when `accept_blockers` is non-empty — no drawing, no declared
    kind, or no `## Log` section — following `_set_status`'s own precedent that
    the module owns the invariant and every caller gets it. `wfctl arch accept`
    calls `accept_blockers` itself first and never reaches this branch in the
    normal case; it exists for the caller that is not the CLI, which is every
    reason this guard needs to live here rather than only at the console.
    """
    if record.status != "proposed":
        raise ValueError(record.status)
    blockers = accept_blockers(record)
    if blockers:
        raise ValueError("; ".join(blockers))
    return _set_status(record, IN_FORCE, date, citation)
