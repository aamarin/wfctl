"""What a PR description breaks against `opening-a-change`, as a machine sees it.

Pure functions over strings, and a sibling to `_shape.body_findings` rather than
part of it: that one is *"the part of `conversation-response-shape` a machine can
see"* and says so in its first line, while the rule here comes from
`opening-a-change`. One command reads a PR body; two skills have rules about
what is in it. Splitting by owning skill keeps each module's docstring true when
the other skill's rules move.

## Why this exists at all

`a-rule-is-expressed-as-a-check` decides it: a violation visible in an artifact
the work already produces is expressed as a check over that artifact, and the
record names the PR body in its list. The rule checked here — the review panel's
reconciled table goes in the description — is the whole of what makes a skipped
panel visible (#187). Shipped as prose alone it would be a rule nothing observes,
placed on the artifact the record was written about, which is the failure it
names rather than a lighter version of it.

## What every rule here is one instance of

A panel that never ran must not be able to look like a panel that found nothing.
Each rule below closes one way of producing the second while having done the
first, and each was found by a reviewer producing exactly that body rather than
by reasoning about it — a half-filled row, a row missing its disposition, a
roster with no evidence behind it, a placeholder summary. The check is a floor,
not a proof: it can see that evidence was written, never that it is true.
"""

import re

_HEADING = re.compile(r"^ {0,3}(#{2,6})\s+(.*?)\s*#*\s*$", re.MULTILINE)
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_MD_HEADING = re.compile(r"^ {0,3}#{1,6}\s")

# Equal-length delimiter runs, which is CommonMark's rule. A single-backtick
# pattern reads ``[0]`` as two empty spans and leaves the brackets exposed.
_CODE = re.compile(r"(`+)[\s\S]*?\1")

# A cell boundary is an *unescaped* pipe. A row quoting another row — which a
# disposition explaining a table defect does — writes `\|` inside a code span,
# and splitting on every pipe tears that span into cells, inventing a
# cardinality the row never had.
_CELL = re.compile(r"(?<!\\)\|")
# A delimiter row: what makes the line above it a header, in CommonMark and
# therefore on the page. The `#` column is optional and naming it was this
# module's own guess at the same question.
_DELIMITER = re.compile(r"^[\s:|-]+$")

# What the template ships in a field nobody answered: "N/A", "None", "TBD", a
# dash run, or nothing.
_SHIPPED = re.compile(r"\[[^\]]*\]|n/?a|none|tbd|-+", re.IGNORECASE)

_BRACKETED = re.compile(r"\[[^\]]*\]")
# A bracketed span carrying link syntax — `](` inline, `][` reference. Not a
# judgement about whether the link resolves: the placeholders below decide that,
# and this only keeps a citation from reading as an unanswered field.
_LINKISH = re.compile(r"\]\(|\]\[")

# The exact spans `wfctl/agents/configs/github/.github/pull_request_template.md`
# ships in its Review Panel section, held here rather than read from disk so this
# module stays pure. `tests/test_body.py` pins the two together, and would fail
# if the template grew a placeholder this set does not carry.
#
# **These are why this module is not a markdown parser.** Recognising an
# unanswered field by bracket syntax meant learning inline links, reference
# links, shortcut links and their definitions — four constructs, four findings,
# each an approximation that disagreed with the renderer somewhere. Matching what
# the template actually ships needs none of them.
PLACEHOLDERS = frozenset(
    {
        "[target]",
        "[n]",
        "[r1]",
        "[what it raised]",
        "[applied / accepted / rejected — with the reason]",
        "[r1 ✓  r2 ✓  r3 ✓ — and which, if any, were re-asked]",
    }
)

_SECTION = "review panel"
_SUMMARY = "**panel:**"

# Reviewer, finding, disposition. The floor for a table with no header to
# measure against — three is what a result row means, not a column count this
# module prefers.
_RESULT_CELLS = 3


def _unanswered(text: str) -> bool:
    """Whether the field still holds something the template put there.

    Quoted code is removed first — a disposition naming ``[0]`` or quoting a
    shipped row is an author writing accurately, and rejecting the description
    for describing is the failure direction that teaches a reader to ignore the
    check.

    Two questions, and neither parses a link. A shipped placeholder anywhere in
    the field is one, wherever it sits and whatever surrounds it: an author who
    wrapped `[what it raised]` in reference-link syntax has still not written a
    finding, and the page still shows the template's words. A field that is
    *entirely* one bracketed span with no link syntax is the other, which is what
    reaches a repository whose template is not this one.
    """
    bare = _CODE.sub("", text)
    if any(placeholder in bare for placeholder in PLACEHOLDERS):
        return True
    stripped = bare.strip()
    return bool(_BRACKETED.fullmatch(stripped) and not _LINKISH.search(stripped))


def _written(text: str) -> bool:
    """Whether a field holds something an author put there, in **all** of it.

    **The one predicate this module has**, asked of every field it reads — a
    table cell, the roster, a line of evidence. Five findings on PR #234 were one
    defect: each field had grown its own answer to this question, and every field
    with a weaker answer was another way to look reviewed without being reviewed.
    Fields differ in what they hold; none of them differs in what it means to be
    filled.

    **No early return, and that is the point.** A later finding was this function
    stopping at the first valid link it saw and never reading the rest, so
    `[what it raised] see [#234](url)` passed on the strength of its citation.
    That was the third instance of one rule — *any match satisfies* — after a row
    accepted on any filled cell and a row accepted on the cells that happened to
    exist. Every question is asked of the whole field, and nothing here may
    return on the first thing that looks right.
    """
    stripped = text.strip()
    if not stripped:
        return False
    if _unanswered(stripped):
        return False
    return not _SHIPPED.fullmatch(_CODE.sub("", stripped).strip())


def _blank_fences(text: str) -> str:
    """The text with fenced blocks emptied, line count preserved.

    A body explaining this very section quotes it, and a quoted `## Review Panel`
    is an example rather than a section. Left in, a fenced example carrying a
    roster passes a body with no panel at all, and one carrying no roster hides
    the real section further down — both reported on PR #234.
    """
    out, fence = [], ""
    for line in text.splitlines():
        marker = _FENCE.match(line)
        if fence:
            out.append("")
            if marker and line.strip().startswith(fence):
                fence = ""
            continue
        if marker:
            fence = marker.group(1)
            out.append("")
            continue
        out.append(line)
    return "\n".join(out)


def _section(body: str) -> str | None:
    """The Review Panel section's text, or None where the body has no such
    heading.

    Ends at the next heading of the same level or higher, not at the next
    heading of any level: a template organising the section with `### Findings`
    and `### Roster` under it would otherwise have its table and roster fall
    outside the section and be reported missing.
    """
    body = _blank_fences(_COMMENT.sub("", body))
    headings = list(_HEADING.finditer(body))
    for i, m in enumerate(headings):
        if m.group(2).strip().lower() != _SECTION:
            continue
        depth = len(m.group(1))
        end = len(body)
        for later in headings[i + 1 :]:
            if len(later.group(1)) <= depth:
                end = later.start()
                break
        return body[m.end() : end]
    return None


def _table(section: str) -> tuple[int, list[list[str]]]:
    """The result rows of the disposition table, and how many cells one needs.

    A header is the row a delimiter row follows, which is CommonMark's rule and
    therefore the renderer's. Recognising it by a `#` first cell instead was this
    module's own guess at the same question, and a table written with the common
    `| Reviewer | Finding | Disposition |` header had that header counted as a
    result — a section holding nothing but a header then read as a panel with
    one finding.

    The width comes from the header where there is one, so a repository whose
    table carries a fifth column has its own shape enforced rather than this
    module's. The leading ordinal is dropped from both: it is an index, and
    reading it as content is how the first version of this check passed the row
    it shipped with, on the strength of its own row number.
    """
    lines = [
        line.strip() for line in section.splitlines() if line.strip().startswith("|")
    ]
    width, rows = _RESULT_CELLS, []
    for i, line in enumerate(lines):
        if _DELIMITER.fullmatch(line):
            continue
        cells = [c.strip().replace("\\|", "|") for c in _CELL.split(line.strip("|"))]
        following = lines[i + 1] if i + 1 < len(lines) else ""
        if _DELIMITER.fullmatch(following):  # the row above a delimiter is a header
            width = max(len(cells) - 1, 1) if cells[:1] == ["#"] else len(cells)
            continue
        if len(cells) > 1 and cells[0].isdigit():
            cells = cells[1:]
        rows.append(cells)
    return width, rows


def _roster(section: str) -> str | None:
    """What follows `roster:`, or None where the section has no such line."""
    for line in section.splitlines():
        line = line.strip()
        if line.lower().startswith("roster:"):
            return line.split(":", 1)[1].strip()
    return None


def _evidence(section: str) -> bool:
    """Whether the section says anything beyond its roster and its summary.

    Only reachable when the panel reported no findings, where there is no table
    to read. `fanning-out-code-review` Step 3: *"'No findings' is a valid result
    only when it says which passes ran and what was checked in each. A bare
    'looks good' is a missing report wearing a verdict."* A roster alone is that
    bare verdict, and it is the cheapest body a skipped panel can produce.

    A heading is structure rather than evidence, and `N/A` is the answer Step 4
    forbids here by name — both were accepted while this asked only whether a
    line existed, which is the question `_written` exists so that nothing asks.

    Presence, never content — no check can tell a true account of six passes
    from a fabricated one. What it removes is the one-line fake.
    """
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("|") or _MD_HEADING.match(line):
            continue
        low = stripped.lower()
        if low.startswith("roster:") or low.startswith(_SUMMARY):
            continue
        if _written(stripped):
            return True
    return False


def panel_findings(body: str) -> list[str]:
    """What the body says about the review panel, and whether it says anything.

    One finding per way of looking reviewed without being reviewed, because the
    repairs differ. A body with no section at all is a template that predates
    this rule — `install-config` is seed-once, so most repositories have one —
    and the repair is to append the section. Everything after that is a panel
    that did not finish, and the repair is to finish it.

    Every field is read through `_written`, and the summary through the same
    link handling, so a new field added here inherits both rather than growing a
    fourth answer to what "filled" means. That is what the reviewers on #234
    were finding, once per field, until the fields stopped disagreeing.
    """
    section = _section(body)
    if section is None:
        return [
            "opening-a-change Step 1 — no '## Review Panel' section. The panel's "
            "disposition table is what makes a skipped panel visible; a body "
            "without it reads exactly like a change three reviewers passed. "
            "Append the section, whether or not the template carries one."
        ]

    out = []
    for line in section.splitlines():
        if not line.strip().lower().startswith(_SUMMARY):
            continue
        if _unanswered(line):
            out.append(
                "opening-a-change Step 1 — the Review Panel summary still carries "
                f"placeholders: {line.strip()!r}. The count of reviewers and "
                "findings is the line a reader checks the table against."
            )

    width, rows = _table(section)
    for row in rows:
        if len(row) < width:
            out.append(
                "opening-a-change Step 1 — a Review Panel row is missing cells: "
                f"{' | '.join(row)!r} has {len(row)} where the table takes "
                f"{width}. A row without its disposition records a finding "
                "nobody said what they did about."
            )
        elif not all(_written(cell) for cell in row):
            out.append(
                "opening-a-change Step 1 — a Review Panel row still carries what "
                f"it shipped with: {' | '.join(row)!r}. Every cell of a result "
                "row is filled, or the row is not a result: one replaced cell in "
                "an otherwise untouched row renders as a reviewed finding."
            )

    if not rows and not _evidence(section):
        out.append(
            "opening-a-change Step 1 — the Review Panel reports no findings and "
            "shows no evidence. 'No findings' is a result only when it says which "
            "passes ran and what each reviewer checked; a roster on its own is "
            "the bare verdict fanning-out-code-review Step 3 rejects."
        )

    roster = _roster(section)
    if roster is None or not _written(roster):
        out.append(
            "opening-a-change Step 1 — the '## Review Panel' section carries no "
            "roster. It is the only thing telling a reviewer that found nothing "
            "from a reviewer that returned nothing, which is the distinction "
            "fanning-out-code-review Step 3 is built around."
        )
    return out
