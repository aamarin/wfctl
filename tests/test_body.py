"""`check-body` sees a PR body with no panel in it.

The rule — the review panel's reconciled table goes in the description — is the
whole of what makes a skipped panel visible (#187), and a rule with nothing
observing it is what `a-rule-is-expressed-as-a-check` calls the rule's absence
rather than a lighter version of it. So these are the bodies that must not pass.
The shipped-placeholder case is the one worth the code: it renders on github.com
as a well-formed table, which reads as answered-with-nothing rather than as
untouched.
"""
from pathlib import Path

from wfctl._body import panel_findings

_TEMPLATE = (
    Path(__file__).resolve().parent.parent
    / "wfctl/agents/configs/github/.github/pull_request_template.md"
)

_FILLED = """## Review Panel

| # | Reviewer | Finding | Disposition |
|---|---|---|---|
| 1 | r2 | `find` matches directories | applied — reproduced it first |

roster: r1 ✓  r2 ✓  r3 ✓

## Checklist
"""


def test_a_body_with_no_panel_section_is_a_finding() -> None:
    """The case every repository starts in: `install-config` is seed-once, so a
    template seeded before this rule existed never grows the section, and the
    skill tells the agent to append one. A body that did neither is the
    unattended run reaching a PR with nobody having read it."""
    assert panel_findings("# PR\n\n## Summary\n\nDid a thing.\n")


def test_the_template_as_shipped_does_not_pass_its_own_check() -> None:
    """Read from the template rather than retyped, so the two cannot drift into
    a placeholder the check happens to accept. An author who deletes the comment
    block and changes nothing else — which `opening-a-change` Step 4 tells them
    to do — leaves a table that is structurally complete and says nothing."""
    assert panel_findings(_TEMPLATE.read_text())


def test_a_row_numbered_but_otherwise_unfilled_is_not_content() -> None:
    """The shipped row carries its own ordinal, and reading that as an answer is
    how the first version of this check passed the exact body it was written to
    catch."""
    body = "## Review Panel\n\n| # | R | F | D |\n|---|---|---|---|\n| 1 | [r1] | [x] | [y] |\n"

    assert panel_findings(body)


def test_n_a_does_not_satisfy_the_section() -> None:
    """Step 4 says a section you have nothing for gets "N/A", which would be a
    skill-sanctioned way to fill this one without running a panel. The skill now
    exempts the section by name; this is the half of that exemption a body is
    held to rather than told."""
    assert panel_findings("## Review Panel\n\nN/A\n\n## Checklist\n")


def test_a_reconciled_table_passes() -> None:
    """The check has to be quiet on the thing it is asking for, or the author
    learns to ignore it."""
    assert panel_findings(_FILLED) == []


def test_the_sections_own_comment_block_is_not_an_answer() -> None:
    """A template comment explaining what the section is for is an instruction to
    the author. Counting it as content would pass every unedited body."""
    body = _TEMPLATE.read_text().replace(
        "| 1 | [r1] | [what it raised] | [applied / accepted / rejected — with the reason] |",
        "",
    )

    assert panel_findings(body)
