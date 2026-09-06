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


def _is_filled(section: str) -> bool:
    """Whether anything in the section was written rather than shipped.

    Table rows only, and the roster line. Prose around them is not the test: the
    section is a table by construction, and a sentence saying the panel ran is
    the claim this check exists to stop standing in for the table.
    """
    for line in section.splitlines():
        line = line.strip()
        if line.lower().startswith("roster:"):
            if not _UNFILLED.match(line.split(":", 1)[1].strip()):
                return True
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):  # the |---|---| separator
            continue
        if cells[:1] == ["#"]:  # the header row the template ships
            continue
        # The leading ordinal is not content. Without this the shipped row
        # `| 1 | [r1] | … |` reads as filled on the strength of its own row
        # number, and the check passes the exact body it exists to catch.
        if len(cells) > 1 and cells[0].isdigit():
            cells = cells[1:]
        if any(not _UNFILLED.match(c) for c in cells):
            return True
    return False


def panel_findings(body: str) -> list[str]:
    """What the body says about the review panel, and whether it says anything.

    Two findings, not one, because the fixes differ: a body with no section at
    all is a template that predates this rule — `install-config` is seed-once, so
    most repositories have one — and the repair is to append the section. A
    section left as shipped is a panel that did not run, and the repair is to run
    it.

    An unfilled section is the case worth the code. It renders on github.com as a
    well-formed table with a placeholder row, which reads as *answered, and the
    answer was nothing* rather than as untouched — the indistinguishability the
    section was added to remove, arriving through the section itself.
    """
    section = _section(body)
    if section is None:
        return [
            "opening-a-change Step 1 — no '## Review Panel' section. The panel's "
            "disposition table is what makes a skipped panel visible; a body "
            "without it reads exactly like a change three reviewers passed. "
            "Append the section, whether or not the template carries one."
        ]
    if not _is_filled(section):
        return [
            "opening-a-change Step 1 — the '## Review Panel' section is still as "
            "shipped: no finding rows and no roster. A panel that found nothing "
            "is written down as one — who reviewed, what each checked — because "
            "an empty section and a panel that never ran read identically."
        ]
    return []
