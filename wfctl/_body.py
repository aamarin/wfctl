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

# A cell holding only a bracketed placeholder, "N/A", "None", "TBD" or nothing.
# The bracket form is the template's own convention for an unanswered field —
# `opening-a-change` Step 4 says placeholders in brackets are replaced, not left
# — so a body still carrying them is unfilled in exactly the way a blank one is.
_UNFILLED = re.compile(r"^(?:\[[^\]]*\]|n/?a|none|tbd|-+|)$", re.IGNORECASE)

# A bracketed span that is not a markdown link. `[target]` is an unfilled field;
# `[the record](url)` is prose, and treating the second as the first would reject
# a finished summary for citing something.
_PLACEHOLDER = re.compile(r"\[[^\]]*\](?!\()")

_SECTION = "review panel"
_SUMMARY = "**panel:**"

# Reviewer, finding, disposition. The floor for a table with no header to
# measure against — three is what a result row means, not a column count this
# module prefers.
_RESULT_CELLS = 3


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

    The width comes from the header where there is one, so a repository whose
    table carries a fifth column has its own shape enforced rather than this
    module's. The leading ordinal is dropped from both: it is an index, and
    reading it as content is how the first version of this check passed the row
    it shipped with, on the strength of its own row number.
    """
    width, rows = _RESULT_CELLS, []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):  # the |---|---| separator
            continue
        if cells[:1] == ["#"]:  # the header row the template ships
            width = max(len(cells) - 1, 1)
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

    Presence, never content — no check can tell a true account of six passes
    from a fabricated one. What it removes is the one-line fake.
    """
    for line in section.splitlines():
        line = line.strip()
        if not line or line.startswith("|"):
            continue
        if line.lower().startswith("roster:") or line.lower().startswith(_SUMMARY):
            continue
        return True
    return False


def panel_findings(body: str) -> list[str]:
    """What the body says about the review panel, and whether it says anything.

    One finding per way of looking reviewed without being reviewed, because the
    repairs differ. A body with no section at all is a template that predates
    this rule — `install-config` is seed-once, so most repositories have one —
    and the repair is to append the section. Everything after that is a panel
    that did not finish, and the repair is to finish it.
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
        if line.strip().lower().startswith(_SUMMARY) and _PLACEHOLDER.search(line):
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
        elif any(_UNFILLED.match(cell) for cell in row):
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
    if roster is None or _UNFILLED.match(roster):
        out.append(
            "opening-a-change Step 1 — the '## Review Panel' section carries no "
            "roster. It is the only thing telling a reviewer that found nothing "
            "from a reviewer that returned nothing, which is the distinction "
            "fanning-out-code-review Step 3 is built around."
        )
    return out
