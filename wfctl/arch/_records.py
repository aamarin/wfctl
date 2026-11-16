"""Architecture decision records: parse, validate, supersede, project.

One file, one decision, identified by its slug — the filename without
extension. wfctl reads records; it never mediates their content. What it does
own is the projection (`accepted` only) and the link integrity between records,
because those are the two things a reader cannot get right by eye.
"""
from __future__ import annotations

import re
import shlex
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import dropwhile, takewhile
from pathlib import Path
from urllib.parse import unquote

from wfctl import _md
from wfctl._io import write_atomic

from ._drawing import NO_DRAWING, Drawing, Problem, fingerprint, read_fence, read_svg


IN_FORCE = "accepted"

# The closed set (data-model.md). Anything outside it — including absent and
# misspelled — parses to "" and is excluded, never to `accepted`.
STATUSES = frozenset({"proposed", IN_FORCE, "superseded", "rejected", "retired"})

# Statuses a person moved a record to. `proposed` is the one that means nobody
# has, and a status outside `STATUSES` parses to "" — so both fall outside this
# set without being named in it.
#
# Not "accepted" alone, which was the first shape and is wrong for a branch that
# supersedes a record: that leaves the old record at `superseded`, which a human
# did decide, and requiring `accepted` would hold such a branch forever.
#
# Here rather than in `_evidence`, because the "architecture accepted" fact and
# the worktree guard both read it, and the guard can't import `_evidence`.
RULED_ON = frozenset({IN_FORCE, "superseded", "rejected", "retired"})

# A tuple, where `STATUSES` is a frozenset: the accept refusal prints these
# names, and the order they print in is the order the guidance lists them in
# (FR-012, data-model.md "Diagram kind"). Nothing prints `STATUSES`.
DIAGRAM_KINDS = ("data-flow", "component", "state", "sequence")

# The heading each tier's template requires and the other's does not, which is
# what makes a record's level readable from the file rather than only from the
# directory holding it. `Owns truth` is asked first and `Diagram` only in its
# absence: the first is what makes a record bind, and a diagram drawn beside one
# is decoration on a decision that still owns something.
#
# Named here and held against the templates by a test, for the reason
# `required-sections-are-wfctls` already gives about `spec.md` and `plan.md`: a
# check that opened a template at read time would need an answer for the repo
# that installed none, and both answers are wrong.
LEVEL_2_SECTION = "Owns truth"
LEVEL_3_SECTION = "Diagram"

# The heading `model-the-domain`'s template carries and neither record template
# does. A domain model binds nothing, so at the root it is the placement check's
# weighed-nothing row — but that row's remedy is `implementation/`, and a
# level-2 description filed as a level-4 note is a second misfiling (#464).
# This is what lets the row name `domain/` instead.
DOMAIN_MODEL_SECTION = "Ubiquitous Language"


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
    # The contexts or outside parties the record is about, as the domain page
    # names them. Verbatim like `diagram`: whether a name is on the page is
    # `validate`'s question, since the page is not this module's to read.
    governs: tuple[str, ...] = ()

    @property
    def in_force(self) -> bool:
        return self.status == IN_FORCE

    @property
    def kinds(self) -> tuple[str, ...]:
        """The declared kinds, in the order written and with repeats kept.

        Read from `diagram` on every access rather than stored beside it, so the
        verbatim value and the list can't disagree. Repeats are kept because a
        kind listed twice is a refusal, and a reader that dropped them would have
        nothing left to refuse.
        """
        return split_list(self.diagram)


@dataclass(frozen=True)
class Refusal:
    """A reason `accept` refuses a record, printed as its own line with a fix.

    Kept apart from the strings `accept_blockers` returns, which print together
    under one `cannot be accepted yet` line. Folding these into that list would
    change the output every existing record already gets (R-013).
    """

    problem: str
    fix: str


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


def split_names(value: str) -> tuple[str, ...]:
    """A comma-separated list of names: trimmed, with empty entries dropped.

    Lives here and not beside the code that reads the domain page because
    `parse_record` needs it for `governs`, and that module imports this one.
    One rule serves every such list, so a trailing comma means the same thing
    in a record, on the domain page and in a branch's design.md.
    """
    return tuple(name for name in (part.strip() for part in value.split(",")) if name)


def split_list(value: str) -> tuple[str, ...]:
    """A frontmatter value that may be a YAML inline list, such as `[a, b]`.

    One pair of surrounding brackets is stripped, then the rest is read with
    `split_names`, so `a`, `[a]`, and `[a, b]` all read as lists. wfctl reads
    frontmatter with a line scan and has no YAML parser, and the inline form is
    the only list syntax a record or a view needs.
    """
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return split_names(value)


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


def parse_status(text: str) -> str:
    """A record's status from its text, or "" when absent or unrecognised.

    For a reader that holds the text rather than a file, such as the worktree
    guard reading a record at a commit through `git show`. Normalised the way
    `parse_record` normalises it, so the two never disagree about one record.
    """
    status = _frontmatter(text).get("status", "")
    return status if status in STATUSES else ""


def parse_governs(text: str) -> tuple[str, ...]:
    """A record's `governs` names from its text, for a reader that holds the text
    rather than a file, as `parse_status` is. Empty when the field is absent."""
    return split_names(_frontmatter(text).get("governs", ""))


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
        governs=split_names(front.get("governs", "")),
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


def validate(
    records: list[Record], names: frozenset[str] | None = None
) -> list[Finding]:
    """Link integrity across the record set (VR-002, VR-003, VR-004), plus the
    diagram-kind and label-agreement rules this feature added (VR-006, VR-007),
    and the failure-row warning a `sequence` record gets (#495).

    Only the rules checkable from the set alone. The status *transitions* in
    data-model.md are a review convention — records are hand-edited markdown and
    wfctl does not mediate the edits, so a status moved along an illegal path is
    not detectable here. VR-001 needs no check: an illegal value never parses.
    There is no VR-005 check here by design — it is the frozen-body rule,
    enforced by convention, not code.

    `names` is the domain page's list, passed in because reading it is
    `_contexts`' job and that module imports this one. `None` means the repo
    has no list, and then no `governs` value is wrong.
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
        # covers at the transition that actually needs it, not here. Named per
        # kind, so a list with one typo says which entry it is.
        for kind in _distinct_kinds(record):
            if kind not in DIAGRAM_KINDS:
                findings.append(Finding(
                    "error", record.slug,
                    f"declares diagram '{kind}', which is not a diagram kind",
                ))

    for record in records:
        # The kind rules `accept` refuses (FR-015), as warnings on `proposed`
        # only, for VR-007's reasons below. A doctor error would exit 1 on every
        # run while a record is still being drafted. The unknown-kind refusal
        # isn't repeated here, since VR-006 above already reports it as an error.
        if record.status != "proposed":
            continue
        for refusal in _repeat_refusals(record) + _drawing_refusals(record):
            findings.append(Finding("warning", record.slug, refusal.problem))
        # A one-kind record's drawing problem, which `_drawing_refusals` leaves
        # to `accept_blockers`. Without it the author would first hear of a
        # broken link from `accept`.
        if len(_distinct_kinds(record)) <= 1 and (problem := _drawing(record).problem):
            findings.append(Finding("warning", record.slug, problem.problem))

    for record in records:
        # VR-007: a warning, and `proposed` only (R-005). `superseded` and
        # `retired` records were accepted once, so their bodies are frozen by
        # the same rule VR-005 already applies to `accepted`; `rejected`
        # records are never accepted, so a finding against one names work
        # nobody will do.
        if record.status != "proposed":
            continue
        # Every kind's drawing in a list, as `_sequence_drawing` does for the
        # failure-step rule, so a label is checked whichever kind it sits under.
        if len(_distinct_kinds(record)) > 1:
            drawings = [d for d in _drawings(record).values() if d]
        else:
            drawings = [d for d in [_drawing(record)] if d]
        if not drawings:
            continue
        # The rest of the record, with the `## Boundary` section removed
        # entirely — comparing a label against the drawing it came from would
        # let the label satisfy itself: its own words are always "present" in
        # a body that includes the fence they were read out of.
        lines = record.body.splitlines()
        bounds = _section_bounds(lines, "## boundary")
        rest = lines if bounds is None else lines[: bounds[0]] + lines[bounds[1] :]
        record_words = _content_words("\n".join(rest))
        # Not deduplicated, so a one-kind record warns once per repeat of a
        # label, as it did before lists (SC-004).
        for label in (label for d in drawings for label in d.labels):
            label_words = _content_words(label)
            # No readable words at all — an ASCII sketch, a fence of prose —
            # compares nothing rather than inventing a finding (research R-004's
            # stated limit).
            if label_words and not (label_words & record_words):
                findings.append(Finding(
                    "warning", record.slug,
                    f"drawing label '{label}' appears nowhere else in the record",
                ))
        # Nothing lays out a hand-drawn SVG, so a label can run off the edge
        # with no error. The estimate is rough on purpose, and `proposed` only
        # for VR-007's reasons: the user reads an accepted record's drawing
        # before accepting it.
        for label in (label for d in drawings for label in d.past_edge):
            findings.append(Finding(
                "warning", record.slug, f"drawing label '{label}' runs past the drawing's edge"
            ))

    for record in records:
        # The failure-row rule (#495), as a warning, `proposed` only, for
        # VR-007's reasons. `accept_blockers` refuses the same drawing at
        # acceptance; this is the notice that arrives while the record is still
        # being written, so the refusal is not the first anyone hears of it.
        if record.status != "proposed":
            continue
        drawing = _sequence_drawing(record)
        if drawing and not drawing.shows_failure:
            findings.append(Finding(
                "warning", record.slug,
                "declares a sequence diagram with no step that fails — "
                f"{drawing.failure_fix}",
            ))

    for record in records:
        # An accepted record's drawing binds, so doctor warns when it breaks or
        # changes after the user signed it off (FR-021). Superseded and retired
        # records are left out, since their drawings no longer bind anything.
        if record.status != IN_FORCE:
            continue
        distinct = _distinct_kinds(record)
        if len(distinct) > 1:
            for kind, drawn in _drawings(record).items():
                if kind in distinct and drawn.problem:
                    findings.append(Finding(
                        "warning", record.slug, f"### {kind}: {drawn.problem.problem}"
                    ))
        elif problem := _drawing(record).problem:
            findings.append(Finding("warning", record.slug, problem.problem))
        # A link no Log line names gets no warning. That covers a record
        # accepted before fingerprints existed, and an SVG link added to an
        # accepted record, which the frozen-body rule and the design gate
        # already cover, since the link is in the record's body.
        for drawing, signed, current in _sign_offs(record):
            if signed is not None and signed != current:
                findings.append(Finding(
                    "warning", record.slug,
                    f"drawing {drawing.link} changed since it was accepted — look at it, "
                    # Quoted and after `--`, since a person pastes this line and
                    # a slug is a file name, which can hold a space or start with `-`.
                    f'then run wfctl arch accept --agreed "<where>" -- '
                    f"{shlex.quote(record.slug)}",
                ))

    if names is not None:
        for record in records:
            # An error, run on every status like VR-006: a misspelled name
            # answers nothing, and the first sign would be a branch pausing on
            # the context the record was meant to cover.
            for name in record.governs:
                if name not in names:
                    findings.append(Finding(
                        "error", record.slug,
                        f"governs {name}, which isn't on the domain page's name list",
                    ))

    return findings


# A markdown image, `![alt](target)`, with the target optionally in `<…>` and
# an optional title in any of the three forms GitHub accepts. Only this form
# links a drawing: it is what GitHub renders inline and what the skills teach,
# and accepting an HTML `<img>` as well would mean parsing HTML inside
# markdown.
_IMAGE = re.compile(
    r"!\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)


def _image_targets(text: str) -> list[str]:
    """Each image target in `text`, as the file GitHub would fetch.

    GitHub drops a query or fragment and decodes the path, so a link it shows
    as the picture names the same file here. Reading it literally told the
    author "no drawing" beside a drawing they could see.
    """
    targets = []
    for match in _IMAGE.finditer(text):
        target = match.group(1) or match.group(2)
        if "://" not in target and not target.lower().startswith("data:"):
            target = unquote(re.split(r"[?#]", target, maxsplit=1)[0])
        targets.append(target)
    return targets


# What GitHub shows as text rather than rendering: an HTML comment, which can
# span lines, an inline code span, and an image whose `!` is escaped.
_UNRENDERED = re.compile(r"<!--.*?-->|`[^`\n]*`|\\!", re.DOTALL)


def _rendered(text: str) -> str:
    """`text` with the parts GitHub doesn't render as markup removed.

    An image inside any of them shows no picture, so counting it let a record
    pass with nothing drawn, and beside a real fence it made a false "both an
    SVG and a fenced block" refusal.
    """
    return _UNRENDERED.sub(" ", text)


def _is_svg_link(target: str) -> bool:
    """A link wfctl can read as a drawing: a local file ending in `.svg`.

    A URL or a `data:` URI points at nothing in the repository, and any other
    image has no labels to check, so neither is a drawing.
    """
    lowered = target.lower()
    return lowered.endswith(".svg") and "://" not in lowered and not lowered.startswith("data:")


def _read_heading(walked: list[_md.Line], heading: str, record_dir: Path) -> Drawing:
    """The drawing under one heading: its SVG link or its first fence.

    The first fence, not all of them: a second fence under the same heading is
    a second drawing of the same boundary, and nothing here needs to choose
    between them. "First" is tracked by the opening delimiter, not by whether
    anything was collected, so a scratch fence left blank does not fall
    through to whatever real drawing follows it.

    An SVG link counts only outside a fence, since a fence shows an image line
    as text. Two SVG links, or an SVG beside a non-empty fence, are problems
    rather than a choice: a record carrying two drawings would pass with one
    of them unchecked. Two fences keep the first-wins rule above, because
    refusing them would change the result for records that pass today.
    """
    interior: list[str] = []
    prose: list[str] = []
    state = "closed"  # closed → open → done
    for line in walked:
        if line.inside:
            if state == "open":
                interior.append(line.text)
        elif line.fence:
            state = "open" if state == "closed" else "done"
        else:
            prose.append(line.text)
    links = [t for t in _image_targets(_rendered("\n".join(prose))) if _is_svg_link(t)]
    fence = read_fence("\n".join(interior))
    if len(links) > 1:
        return Drawing(format="svg", problem=Problem(
            f"'{heading}' links two SVG drawings",
            "keep one, or give each its own '### <kind>' heading.",
        ))
    if links and fence:
        return Drawing(format="svg", problem=Problem(
            f"'{heading}' has both an SVG and a fenced block", "keep one."
        ))
    if links:
        return read_svg(links[0], record_dir)
    return fence


def _drawing(record: Record) -> Drawing:
    """The summary of the drawing under `## Boundary`, read by `_read_heading`.

    Content is never inspected (clarification Q2): a fenced block holding
    prose is a drawing to this feature, because the alternative is a rule that
    tells a picture from a code sample, which the corpus does not support. An
    interior that is empty or whitespace-only is not content, though, so the
    summary is falsy for a caller's truthiness check, as it is for a record
    with no `## Boundary` at all.

    Reads `_md.walk_lines` directly rather than `_unfenced`, which yields only
    the lines outside a fence, since a fence's interior is half of what this
    reads.
    """
    lines = record.body.splitlines()
    bounds = _section_bounds(lines, "## boundary")
    if bounds is None:
        return NO_DRAWING
    heading, end = bounds
    walked = list(_md.walk_lines(lines[heading + 1 : end]))
    written = lines[heading].strip()
    # An SVG drawing is read with the fences under any non-kind `###` heading
    # left out, so a legend fenced under `### Key`, which the record template
    # allows, isn't counted as a second drawing beside it. Every other line
    # stays, so a second SVG below `### Key` is still two drawings. Without an
    # SVG the whole section is read as before, so no fence-only record changes
    # result.
    without_legends = _without_legend_fences(walked)
    svg = _read_heading(without_legends, written, record.path.parent)
    if svg.format == "svg":
        return svg
    return _read_heading(walked, written, record.path.parent)


def _without_legend_fences(walked: list[_md.Line]) -> list[_md.Line]:
    """`walked` minus every fenced block that sits under a non-kind `###`."""
    kept = []
    under_legend = False
    for line in walked:
        text = line.text.strip()
        if not line.inside and not line.fence and text.startswith("### "):
            under_legend = text[4:].strip().lower() not in DIAGRAM_KINDS
        elif under_legend and (line.inside or line.fence):
            continue
        kept.append(line)
    return kept


def _drawings(record: Record) -> dict[str, Drawing]:
    """Each `### <kind>` heading under `## Boundary`, mapped to its drawing.

    A heading counts when its text is one of `DIAGRAM_KINDS`, ignoring case, so
    `### Sequence` is the `sequence` drawing. The kind's subsection ends at the
    next `###` or `##` heading of any text. A `### Key` heading isn't a kind and
    is never refused, but it still ends the subsection above it. Ending only at
    the next kind heading would let a `### data-flow` with nothing under it
    reach past `### Key` and take the next kind's drawing as its own, which is
    the swap the headings exist to catch.

    Each subsection is read the way `_drawing` reads the whole section. A
    heading with nothing drawn maps to `NO_DRAWING`, so a caller can tell a
    kind drawn nowhere from a heading drawn empty. A repeated heading keeps the
    first.

    A drawing above the first `###` heading belongs to no kind. In a record
    that declares one kind, `_drawing` still finds it, which is how a one-kind
    record keeps passing with its drawing directly under `## Boundary`.

    The section is walked once and split afterwards, so a `###` line inside a
    fence is never taken for a heading.
    """
    lines = record.body.splitlines()
    bounds = _section_bounds(lines, "## boundary")
    if bounds is None:
        return {}
    heading, end = bounds
    subsections: list[tuple[str, str, list[_md.Line]]] = []
    for line in _md.walk_lines(lines[heading + 1 : end]):
        if not line.inside and not line.fence and line.text.strip().startswith("### "):
            written = line.text.strip()
            subsections.append((written[4:].strip().lower(), written, []))
        elif subsections:
            subsections[-1][2].append(line)
    found: dict[str, Drawing] = {}
    for kind, written, walked in subsections:
        if kind in DIAGRAM_KINDS and kind not in found:
            found[kind] = _read_heading(walked, written, record.path.parent)
    return found


def _svg_drawings(record: Record) -> list[Drawing]:
    """The record's SVG drawings with no problem, in heading order.

    The same heading rules acceptance reads: `_drawing` for a record with up to
    one kind, and each `### <kind>` subsection for a record with several.
    """
    return [d for d in _all_drawings(record) if d.format == "svg" and d and d.path is not None]


def _all_drawings(record: Record) -> list[Drawing]:
    """Every drawing the record links, problems included, in heading order."""
    if len(_distinct_kinds(record)) > 1:
        return list(_drawings(record).values())
    return [_drawing(record)]


# One SVG's sign-off at the end of an `accepted` or `redrawn` Log line. The
# lookahead stops a link at the next sign-off or the end of the line, so a link
# holding a space still reads whole.
_SIGN_OFF = re.compile(r" · drawing (.+?) sha256:([0-9a-f]{12})(?= · drawing |\s*$)")


def _sign_offs(record: Record) -> list[tuple[Drawing, str | None, str]]:
    """Each SVG drawing, the fingerprint the Log last signed off for its link,
    and the file's fingerprint now.

    The signed fingerprint comes from the last `accepted` or `redrawn` line in
    `## Log` naming the link, and is None when no line names it. Scoped to the
    Log section for the reason `accepted_on` gives.
    """
    lines = record.body.splitlines(keepends=True)
    bounds = _log_bounds(lines)
    signed: dict[str, str] = {}
    if bounds is not None:
        heading, end = bounds
        for _, stripped in _unfenced(lines[heading:end]):
            if re.match(r"-\s+\d{4}-\d{2}-\d{2}\s+(?:accepted|redrawn)\b", stripped):
                for m in _SIGN_OFF.finditer(stripped):
                    # A citation holding " · drawing " starts the match early,
                    # and the link is what follows the last one.
                    link = m.group(1).rsplit(" · drawing ", 1)[-1]
                    signed[link] = m.group(2)
    return [
        (d, signed.get(d.link), fingerprint(d.path))
        for d in _svg_drawings(record)
        # Always true after `_svg_drawings`, and here so mypy narrows `path`.
        if d.path is not None
    ]


def _sign_off_note(record: Record) -> str:
    """` · drawing <link> sha256:<hex>` for each SVG, in heading order, or ""."""
    return "".join(
        f" · drawing {drawing.link} sha256:{current}"
        for drawing, _, current in _sign_offs(record)
    )


def needs_redraw(record: Record) -> bool:
    """Whether accepting this accepted record again would sign off its drawing.

    True when an SVG no longer matches the fingerprint the Log last signed off,
    the Log names none for it, or the SVG has a problem (FR-022). A record with no SVG, or every SVG
    matching, has nothing to sign off, and accepting it again refuses as before.
    """
    if record.status != IN_FORCE:
        return False
    # A broken SVG takes the same path, so accepting again names the problem
    # the way acceptance would, rather than saying there is nothing to do.
    if any(d.format == "svg" and d.problem for d in _all_drawings(record)):
        return True
    return any(signed != current for _, signed, current in _sign_offs(record))


def _distinct_kinds(record: Record) -> tuple[str, ...]:
    """The declared kinds, each once, in the order first written.

    Every rule except the repeat refusal reads this rather than `kinds`, so
    `[state, state]` declares one kind, listed twice, and is refused once for
    the repeat and nothing else.
    """
    return tuple(dict.fromkeys(record.kinds))


def _sequence_drawing(record: Record) -> Drawing:
    """The drawing the failure-step rule reads, or `NO_DRAWING` when there is none.

    A record declaring only `sequence` uses `_drawing`, as before lists. A
    record declaring more than one kind uses its `### sequence` subsection, so
    adding a second kind isn't a way around the rule (FR-014).
    """
    distinct = _distinct_kinds(record)
    if distinct == ("sequence",):
        return _drawing(record)
    if len(distinct) > 1 and "sequence" in distinct:
        return _drawings(record).get("sequence", NO_DRAWING)
    return NO_DRAWING


# How to draw each kind, for the fix line of a missing-drawing refusal. Keyed
# by kind for the reason `_DIAGRAM_KIND_BLURBS` in `cli.py` is: a kind added to
# `DIAGRAM_KINDS` without an entry here raises `KeyError` instead of printing a
# fix for the wrong kind.
_DRAWING_FIX: dict[str, str] = {
    "data-flow": "an SVG in drawings/, or a mermaid flowchart",
    "component": "an SVG in drawings/, or a mermaid flowchart",
    "state": "an SVG in drawings/, or a mermaid stateDiagram-v2",
    "sequence": (
        'an SVG in drawings/ with class="failing-step" on the step that fails, '
        "or a mermaid sequenceDiagram with an alt block or a -x message"
    ),
}


def _repeat_refusals(record: Record) -> list[Refusal]:
    """One refusal for each kind the list names more than once."""
    counts = Counter(record.kinds)
    refusals = []
    for kind, count in counts.items():
        if count > 1:
            times = "twice" if count == 2 else f"{count} times"
            refusals.append(
                Refusal(f"declares {kind} {times}", "list each kind once in 'diagram:'.")
            )
    return refusals


def _drawing_refusals(record: Record) -> list[Refusal]:
    """A declared kind with no drawing, and a drawn kind with no declaration.

    A record declaring one kind is never refused for a missing drawing here.
    Its drawing may sit directly under `## Boundary`, and the existing `no
    drawing` blocker already covers it, so its output doesn't change. A record
    declaring no kind gets the `no declared kind` blocker instead, and a
    heading it carries isn't refused on top of that.
    """
    distinct = _distinct_kinds(record)
    if not distinct:
        return []
    drawings = _drawings(record)
    refusals = []
    if len(distinct) > 1:
        for kind in distinct:
            drawn = drawings.get(kind, NO_DRAWING)
            if kind in DIAGRAM_KINDS and drawn.problem:
                # In place of the missing-drawing refusal, never beside it:
                # telling the author to draw a kind that is already linked
                # would send them looking for the wrong fix.
                refusals.append(Refusal(f"### {kind}: {drawn.problem.problem}", drawn.problem.fix))
            elif kind in DIAGRAM_KINDS and not drawn:
                refusals.append(Refusal(
                    f"declares a {kind} diagram but doesn't draw one",
                    f"under '## Boundary', add a '### {kind}' heading with "
                    f"{_DRAWING_FIX[kind]}.",
                ))
    for kind in drawings:
        if kind not in distinct:
            refusals.append(Refusal(
                f"draws a '### {kind}' heading, but 'diagram:' doesn't declare {kind}",
                f"add {kind} to the list, or remove the heading.",
            ))
    return refusals


def kind_refusals(record: Record) -> list[Refusal]:
    """The refusals a record's list of kinds adds to `accept_blockers` (FR-012).

    Empty for every record that declares one kind and draws no `### <kind>`
    heading for another, which is every record written before lists existed.
    An unknown kind in a one-kind record keeps its existing blocker, so this
    names one only in a list.
    """
    distinct = _distinct_kinds(record)
    refusals = _repeat_refusals(record)
    if len(distinct) > 1:
        refusals += [
            Refusal(
                f"declares '{kind}', which is not a diagram kind",
                f"use {_kind_list(', ', ', or ')}.",
            )
            for kind in distinct
            if kind not in DIAGRAM_KINDS
        ]
    return refusals + _drawing_refusals(record)


def _kind_list(sep: str, last_sep: str) -> str:
    """`DIAGRAM_KINDS` joined for a sentence, e.g. "a, b or c".

    One place for the two shapes the blockers and the CLI refusal need —
    `" | "` for a value to paste into frontmatter, `", "` plus `"or"` for a
    sentence — so the kind names are typed once here and nowhere else.
    """
    if len(DIAGRAM_KINDS) <= 1:
        return sep.join(DIAGRAM_KINDS)
    return sep.join(DIAGRAM_KINDS[:-1]) + last_sep + DIAGRAM_KINDS[-1]


def accept_blockers(record: Record) -> list[str]:
    """Every reason `accept` would refuse `record`, in reading order.

    One half of the rule `accept_problems` returns, with `kind_refusals` the
    other (research R-002). `acceptable`'s own docstring names the failure a
    second copy produces: a listing built from status alone names a record
    whose own suggested command then fails.

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
    distinct = _distinct_kinds(record)
    if _log_bounds(record.body.splitlines(keepends=True)) is None:
        blockers.append("no '## Log' section to append to")
    # Only up to one kind. A record declaring more gets one `kind_refusals`
    # line per missing drawing, and this line would say the same thing again.
    if len(distinct) <= 1:
        drawing = _drawing(record)
        if drawing.problem:
            # Where `no drawing` would sit, and in its place, for the reason
            # `_drawing_refusals` gives for a multi-kind record.
            blockers.append(f"{drawing.problem.problem}: {drawing.problem.fix}")
        elif not drawing:
            blockers.append("no drawing: add an SVG image or a fenced block under '## Boundary'")
    if not distinct:
        blockers.append(
            f"no declared kind: add 'diagram: {_kind_list(' | ', ' | ')}' to the frontmatter"
        )
    elif len(distinct) == 1 and distinct[0] not in DIAGRAM_KINDS:
        # The verbatim value, as before lists, so a one-kind record's refusal
        # reads the same. An unknown kind inside a list is `kind_refusals`'.
        blockers.append(
            f"'{record.diagram}' is not a diagram kind — use {_kind_list(', ', ' or ')}"
        )
    elif (sequence := _sequence_drawing(record)) and not sequence.shows_failure:
        # Conditioned on a drawing, unlike the kind blockers above: with nothing
        # drawn, "no drawing" already says the whole of it, and a second line
        # about a failure row in a drawing that does not exist fixes nothing.
        blockers.append(f"a sequence drawing with no step that fails: {sequence.failure_fix}")
    return blockers


def accept_problems(record: Record) -> list[str]:
    """Every reason `accept` refuses `record`, as one list of problem lines.

    `accept_blockers` and `kind_refusals` together, in that order. `acceptable`,
    `accept`, and the design gate all read this, so none of them can miss half
    of the rule. Before this function, the design gate read `accept_blockers`
    alone and passed a two-kind record with no drawings that `accept` refused.
    `wfctl arch accept` still calls the two separately, since it prints them in
    two shapes.
    """
    return accept_blockers(record) + [r.problem for r in kind_refusals(record)]


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

REDRAWN = "redrawn"

# A `redrawn` line as `_append_log` writes it, for `redraw_only` to read in a
# diff. Beside the width it pads to, so the writer and the reader spell the
# format in one module. A trailing `\r` is allowed, since git keeps a CRLF
# record's carriage returns in the diff.
REDRAWN_LINE = re.compile(
    rf"- \d{{4}}-\d{{2}}-\d{{2}}  {REDRAWN:<{_LOG_STATUS_WIDTH}}— .* · drawing .+ "
    r"sha256:[0-9a-f]{12}\r?"
)


def _read_lines(record: Record) -> list[str]:
    # newline="": `read_text` translates CRLF to LF, which would rewrite every
    # line in a CRLF record — a whole-body diff from a function contracted to
    # change one field and add one line.
    with record.path.open(newline="") as f:
        return f.read().splitlines(keepends=True)


def _append_log(lines: list[str], date: str, word: str, note: str) -> str:
    """Append one `Log` line to `lines` in place, and return the line.

    The one place a Log line is formatted, so a status change and a redraw
    can't write it two ways. Raises, leaving `lines` unchanged, when the file
    has no `## Log` section or `note` carries a line break.

    A line break in `note` is the sharpest of the two, because it does not look
    like a failure. One `Log` entry is one line, so a note carrying a break writes
    a *second* entry — well-formed, indistinguishable from a real one, and dated
    by whoever supplied the note. `accepted_on` then reports that date, which is
    the one thing about a transition nobody can re-derive from the file. Refused
    here rather than at each caller so every writer is covered by the same rule:
    a citation pasted from a review thread is multi-line without anyone intending
    anything.
    """
    # Every break `splitlines` honors, not only `\n` and `\r`, since
    # `redraw_only` and the Log readers split there too: a U+2028 in a pasted
    # citation would otherwise write a sign-off nothing reads.
    if note.splitlines() not in ([note], []):
        raise ValueError(
            "a log entry is one line, and this note carries a line break — it "
            "would write a second entry nothing distinguishes from a real one"
        )
    bounds = _log_bounds(lines)
    if bounds is None:
        raise ValueError("no '## Log' section to append to")
    _, insert_at = bounds
    eol = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    # A file need not end in a newline, and joining onto one that doesn't would
    # weld the new entry onto the previous line — two transitions on one line,
    # and the predecessor's entry destroyed.
    if insert_at > 0 and not lines[insert_at - 1].endswith(("\n", "\r")):
        lines[insert_at - 1] += eol
    entry = f"- {date}  {word:<{_LOG_STATUS_WIDTH}}— {note}"
    lines.insert(insert_at, entry + eol)
    return entry


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

    `_append_log` formats the line and says why a line break is refused.

    Returns the entry it wrote, so a caller reporting the transition quotes the
    line rather than re-composing it from the same parts — two spellings of one
    line are two spellings that can drift.
    """
    lines = _read_lines(record)

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

    try:
        entry = _append_log(lines, date, status, note)
    except ValueError as e:
        raise ValueError(f"{record.path}: {e}") from None
    # After the append, which raises before changing anything. The Log sits
    # below the frontmatter, so the insert never moves `status_line`.
    eol = "\r\n" if lines[0].endswith("\r\n") else "\n"
    lines[status_line] = f"status: {status}{eol}"

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

    `proposed` is necessary but not sufficient — `accept_problems` names the
    rest: a `## Log` section to append the transition to, a drawing, a
    declared kind, for a `sequence` a step that fails, and for a list of kinds
    a drawing under each kind's heading, each of which `accept` would otherwise
    refuse. A listing built from
    status alone names a record whose own suggested command then fails, which
    is not a sentence anyone reading a list of "promotable" records was told to
    expect.

    Exported rather than left for `cli` to reimplement: `accept_problems` is a
    module member (`the-underscore-is-the-module-contract`), and a second copy
    of this rule at the call site is the kind of copy that stops agreeing with
    this one silently.
    """
    return record.status == "proposed" and not accept_problems(record)


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

    Also raises when `accept_problems` is non-empty — no drawing, no declared
    kind, no `## Log` section, or a list of kinds that `kind_refusals`
    refuses — following `_set_status`'s own precedent that
    the module owns the invariant and every caller gets it. `wfctl arch accept`
    calls `accept_blockers` and `kind_refusals` itself first and never reaches
    this branch in the normal case; it exists for the caller that is not the
    CLI, which is every reason this guard needs to live here rather than only
    at the console.
    """
    if record.status != "proposed":
        raise ValueError(record.status)
    blockers = accept_problems(record)
    if blockers:
        raise ValueError("; ".join(blockers))
    # The fingerprint goes on the line the agreement is recorded on, since it
    # says which version of the drawing that agreement covers (FR-020).
    return _set_status(record, IN_FORCE, date, citation + _sign_off_note(record))


def redraw(record: Record, date: str, citation: str) -> str:
    """Sign off an accepted record's changed drawing with one `redrawn` Log line.

    The status stays `accepted`, and `accepted_on` keeps the original date,
    since the line writes no `accepted` word. A `redrawn` line claims that the
    user looked at the new drawing, not a second agreement to the decision, so
    it doesn't weaken the refusal `accept` gives an accepted record (FR-022).

    Raises, writing nothing, when the record isn't accepted, when any
    acceptance check fails, or when every SVG already matches its fingerprint.
    Every check reruns because a layout fix could drop what acceptance required,
    such as a sequence drawing's failing step.
    """
    if record.status != IN_FORCE:
        raise ValueError(record.status)
    blockers = accept_problems(record)
    if blockers:
        raise ValueError("; ".join(blockers))
    if not needs_redraw(record):
        raise ValueError(f"{record.path}: every drawing matches its fingerprint")
    lines = _read_lines(record)
    try:
        entry = _append_log(lines, date, REDRAWN, citation + _sign_off_note(record))
    except ValueError as e:
        raise ValueError(f"{record.path}: {e}") from None
    write_atomic(record.path, "".join(lines), newline="")
    return entry


_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def redraw_only(diff: str, text: str) -> bool:
    """Whether `diff` changes the record only by appending `redrawn` lines.

    `diff` is a `git diff -U0` of one record from the branch point, and `text`
    is the record as the diff leaves it. A redraw is the user's sign-off on a
    layout fix, not a new decision, so the record and design gates pass over a
    record this returns true for (FR-026, research R-014). True only when all
    four of these hold, and each closes one way to pass a real change off as a
    redraw:

    1. The record is accepted. A `redrawn` line on a proposed record would
       skip the gates for a record nobody has accepted.
    2. The diff adds a line. An uncommitted record has an empty committed
       diff, which says nothing about what changed.
    3. Every added line matches `REDRAWN_LINE` and sits inside `## Log`, so a
       bullet shaped like one under `## Decision` still counts.
    4. The diff removes no line. The one exception is the old last line when
       it had no newline: `_append_log` adds the newline before it appends,
       so git shows that line removed and re-added unchanged.
    """
    if parse_status(text) != IN_FORCE:
        return False
    # Split on "\n" alone, as git counts lines. `splitlines` also breaks at a
    # form feed or U+2028, which would put `## Log` at the wrong line number.
    lines = text.split("\n")
    bounds = _section_bounds(lines, "## log")
    if bounds is None:
        return False
    log_start, log_end = bounds
    added: list[tuple[int, str]] = []
    removed: list[str] = []
    new_line = 0
    in_hunk = False
    previous = ""
    for raw in diff.split("\n"):
        raw = raw.removesuffix("\r")
        if m := _HUNK.match(raw):
            new_line = int(m.group(1))
            in_hunk = True
        elif not in_hunk:
            continue
        elif raw.startswith("+"):
            added.append((new_line, raw[1:]))
            new_line += 1
        elif raw.startswith("-"):
            removed.append(raw[1:])
        elif raw.startswith("\\") and previous.startswith("-"):
            # The marker follows the old side's last line. A marker after an
            # added line says the new side ends without a newline, which
            # `_append_log` never leaves.
            removed[-1] = "\0" + removed[-1]
        elif raw:
            # `-U0` leaves no context lines, so an unprefixed line in a hunk
            # is a lone carriage return the text-mode read turned into a
            # newline. Git counts it as part of one line, and every other
            # reader of the record sees a line break there.
            return False
        previous = raw
    if not added:
        return False
    readded: str | None = None
    if removed:
        if len(removed) != 1 or not removed[0].startswith("\0"):
            return False
        readded = removed[0][1:]
    for number, line in added:
        # 1-based on the new side, so line `number` is `lines[number - 1]`.
        if not log_start < number - 1 < log_end:
            return False
        if readded is not None and line == readded:
            readded = None
            continue
        # A line that `splitlines` would break, at a carriage return, form
        # feed, or U+2028, is one line to git and several to the readers that
        # parse the record, which could find a new `## Boundary` inside it.
        if line.splitlines() != [line] or not REDRAWN_LINE.fullmatch(line):
            return False
    return readded is None
