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
"""

import re

_HEADING = re.compile(r"^ {0,3}#{2,6}\s+(.*?)\s*#*\s*$", re.MULTILINE)
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# A cell holding only a bracketed placeholder, "N/A", "None", "TBD" or nothing.
# The bracket form is the template's own convention for an unanswered field —
# `opening-a-change` Step 4 says placeholders in brackets are replaced, not left
# — so a body still carrying them is unfilled in exactly the way a blank one is.
_UNFILLED = re.compile(r"^(?:\[[^\]]*\]|n/?a|none|tbd|-+|)$", re.IGNORECASE)

_SECTION = "review panel"


def _section(body: str) -> str | None:
    """The Review Panel section's text, or None when the body has no such
    heading. Comments are stripped first: the template's own comment block
    explains what the section is for, and an instruction to the author is not
    an answer from one."""
    body = _COMMENT.sub("", body)
    headings = [m for m in _HEADING.finditer(body)]
    for i, m in enumerate(headings):
        if m.group(1).strip().lower() != _SECTION:
            continue
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        return body[m.end() : end]
    return None


def _rows(section: str) -> list[list[str]]:
    """The result rows of the disposition table, cells stripped and the leading
    ordinal dropped.

    The ordinal is not content. Reading it as content is how the first version of
    this check passed the row it shipped with, on the strength of its own row
    number. Header and separator rows are not results and are excluded.
    """
    out = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):  # the |---|---| separator
            continue
        if cells[:1] == ["#"]:  # the header row the template ships
            continue
        if len(cells) > 1 and cells[0].isdigit():
            cells = cells[1:]
        out.append(cells)
    return out


def _roster(section: str) -> str | None:
    """What follows `roster:`, or None where the section has no such line."""
    for line in section.splitlines():
        line = line.strip()
        if line.lower().startswith("roster:"):
            return line.split(":", 1)[1].strip()
    return None


def panel_findings(body: str) -> list[str]:
    """What the body says about the review panel, and whether it says anything.

    Three findings, not one, because the repairs differ. A body with no section
    at all is a template that predates this rule — `install-config` is seed-once,
    so most repositories have one — and the repair is to append the section. A
    row still carrying placeholders, or a missing roster, is a panel that did not
    finish, and the repair is to finish it.

    **Every cell of a result row, not any one of them.** Accepting a row on the
    strength of a single replaced cell passes a table where the reviewer id was
    filled in and the finding and its disposition are still template text — which
    reads on github.com as a reviewed change, and is the failure this whole
    change exists to stop, arriving one layer up from where it was caught.

    Rows may legitimately be absent: a panel that found nothing has none to
    write. The roster may not, because it is the only thing separating a reviewer
    that found nothing from a reviewer that returned nothing, which is the
    distinction `fanning-out-code-review` Step 3 is built around.
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
    for row in _rows(section):
        if any(_UNFILLED.match(cell) for cell in row):
            out.append(
                "opening-a-change Step 1 — a Review Panel row still carries what "
                f"it shipped with: {' | '.join(row)!r}. Every cell of a result "
                "row is filled, or the row is not a result: one replaced cell in "
                "an otherwise untouched row renders as a reviewed finding."
            )

    roster = _roster(section)
    if roster is None or _UNFILLED.match(roster):
        out.append(
            "opening-a-change Step 1 — the '## Review Panel' section carries no "
            "roster. A panel that found nothing is still written down as one — "
            "who reviewed, what each checked — because an empty section and a "
            "panel that never ran read identically."
        )
    return out
