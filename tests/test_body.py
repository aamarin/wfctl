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


def test_a_row_with_one_cell_replaced_is_still_unfilled() -> None:
    """Reported by the Codex reviewer on PR #234 and reproduced before it was
    believed: with `any`, replacing `[r1]` alone made the row read as filled
    while the finding and its disposition were still template text, and
    `check-body` exited 0 on it. A half-filled table renders on github.com as a
    reviewed change, which is #187's own failure arriving one layer up from
    where this check was written to catch it."""
    body = (
        "## Review Panel\n\n"
        "| # | Reviewer | Finding | Disposition |\n|---|---|---|---|\n"
        "| 1 | r1 | [what it raised] | [applied — with the reason] |\n\n"
        "roster: r1 ✓  r2 ✓  r3 ✓\n"
    )

    assert panel_findings(body)


def test_a_panel_that_found_nothing_needs_no_rows_but_needs_a_roster() -> None:
    """Zero findings is a valid result, so requiring a result row would force a
    fake one. The roster is what cannot be dropped: it is the only thing telling
    a reviewer that found nothing from a reviewer that returned nothing, which
    is the distinction `fanning-out-code-review` Step 3 exists for. What such a
    body must also carry is the account of what was checked — see below."""
    checked = "## Review Panel\n\nWhole rubric each, no findings.\n\n"

    assert panel_findings(checked + "roster: r1 ✓  r2 ✓  r3 ✓\n") == []
    assert panel_findings(checked)


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


def test_a_row_missing_its_last_cell_is_not_a_result() -> None:
    """Reported on PR #234 and reproduced: `| 1 | r1 | found bug |` renders as a
    finding nobody said what they did about, and the cell-by-cell check saw only
    the cells that were there and called them all filled. Cardinality is read
    before content, and from the header where there is one, so a table with a
    fifth column has its own shape enforced rather than this module's."""
    body = (
        "## Review Panel\n\n"
        "| # | Reviewer | Finding | Disposition |\n|---|---|---|---|\n"
        "| 1 | r1 | found bug |\n\n"
        "roster: r1 ✓  r2 ✓  r3 ✓\n"
    )

    assert panel_findings(body)


def test_a_fenced_example_is_not_the_section() -> None:
    """Reported on PR #234 and reproduced both ways: a body quoting the section
    in a fence — this PR's own body does — passed with no panel anywhere in it,
    and a quoted example above a real panel would have hidden the real one,
    because `_section` returns the first heading it finds."""
    quoted = (
        "## Summary\n\nLike this:\n\n```\n## Review Panel\n\n"
        "roster: r1 ✓  r2 ✓  r3 ✓\n```\n"
    )

    assert panel_findings(quoted)


def test_the_section_survives_headings_nested_under_it() -> None:
    """A template organising the section with `### Findings` and `### Roster`
    had its table and roster fall outside the section and be reported missing —
    a valid body rejected, which is the failure direction that teaches an author
    to ignore the check. The section ends at a heading of its own level or
    higher, never at one nested under it."""
    body = (
        "## Review Panel\n\n### Findings\n\n"
        "| # | Reviewer | Finding | Disposition |\n|---|---|---|---|\n"
        "| 1 | r1 | found a bug | applied |\n\n"
        "### Roster\n\nroster: r1 ✓  r2 ✓  r3 ✓\n\n## Checklist\n"
    )

    assert panel_findings(body) == []


def test_a_placeholder_summary_line_is_a_finding() -> None:
    """The shipped `**Panel:** [target] — [n] reviewers, [n] findings` is the
    line a reader checks the table's length against, and it was the one part of
    the section nothing looked at. Bracketed spans that are markdown links are
    not placeholders — rejecting a finished summary for citing something is the
    same false rejection as the nested-heading case."""
    filled_row = (
        "| # | Reviewer | Finding | Disposition |\n|---|---|---|---|\n"
        "| 1 | r1 | found a bug | applied |\n\nroster: r1 ✓  r2 ✓  r3 ✓\n"
    )

    assert panel_findings(f"## Review Panel\n\n**Panel:** [target] — [n] findings\n\n{filled_row}")
    assert (
        panel_findings(
            f"## Review Panel\n\n**Panel:** [#234](http://x) — 3 reviewers, 1 finding\n\n{filled_row}"
        )
        == []
    )


def test_a_roster_with_no_evidence_behind_it_is_not_a_no_findings_panel() -> None:
    """The cheapest body a skipped panel can produce, reported on PR #234 after
    the previous round explicitly allowed zero rows. `fanning-out-code-review`
    Step 3: "No findings" is a valid result only when it says which passes ran
    and what was checked in each. Presence of that account is checkable;
    truthfulness is not, and this check claims only the first."""
    bare = "## Review Panel\n\n**Panel:** wfctl — 3 reviewers, 0 findings\n\nroster: r1 ✓  r2 ✓\n"
    with_evidence = (
        "## Review Panel\n\nAll six passes each, over the renumbered steps and "
        "both template copies. No findings.\n\nroster: r1 ✓  r2 ✓\n"
    )

    assert panel_findings(bare)
    assert panel_findings(with_evidence) == []


def test_every_field_answers_to_one_notion_of_filled() -> None:
    """The shape behind four separate findings on PR #234, pinned as one test.

    Each field had grown its own answer to "did the author write this" — cells
    rejected `N/A`, the evidence line accepted it, the summary read links
    differently from both — so every field with the weaker answer was another
    way to look reviewed without being reviewed, reported once per field. The
    same value now means the same thing wherever it lands, and a field added
    later inherits that rather than deciding again.
    """
    filled_table = (
        "| # | Reviewer | Finding | Disposition |\n|---|---|---|---|\n"
        "| 1 | r1 | found a bug | applied |\n\n"
    )

    # `N/A` is unfilled in a cell, in the roster, and as evidence alike.
    assert panel_findings(f"## Review Panel\n\n{filled_table}roster: N/A\n")
    assert panel_findings("## Review Panel\n\nN/A\n\nroster: r1 ✓  r2 ✓\n")
    assert panel_findings(
        "## Review Panel\n\n"
        "| # | Reviewer | Finding | Disposition |\n|---|---|---|---|\n"
        "| 1 | r1 | found a bug | N/A |\n\nroster: r1 ✓  r2 ✓\n"
    )


def test_a_heading_is_structure_rather_than_evidence() -> None:
    """`### Findings` under an otherwise empty section satisfied the evidence
    check while saying nothing about which passes ran — reported on PR #234
    after the previous round added the check but asked only whether a line
    existed."""
    body = "## Review Panel\n\n### Findings\n\nroster: r1 ✓  r2 ✓  r3 ✓\n"

    assert panel_findings(body)


def test_reference_style_links_are_prose_not_placeholders() -> None:
    """`[review record][panel]` is a link, and the exemption written for inline
    `[x](url)` did not reach it — so a finished summary citing its own record
    was rejected. A bare `[label]` is a link only where the body defines that
    label, which is the one thing separating a shortcut link from a field nobody
    filled in."""
    table = (
        "| # | Reviewer | Finding | Disposition |\n|---|---|---|---|\n"
        "| 1 | r1 | found a bug | applied |\n\nroster: r1 ✓  r2 ✓\n"
    )
    ref = f"## Review Panel\n\n**Panel:** [review record][panel] — 3 reviewers\n\n{table}"

    assert panel_findings(ref + "\n[panel]: https://example.com\n") == []
    assert panel_findings(f"## Review Panel\n\n**Panel:** [target] — [n]\n\n{table}")


def test_a_field_is_read_whole_rather_than_until_it_looks_right() -> None:
    """The third instance of one rule — *any match satisfies* — after a row
    accepted on any filled cell and a row accepted on the cells that happened to
    exist. `_written` stopped at the first valid link it saw, so a cell holding
    `[what it raised]` beside a real citation passed on the strength of the
    citation. Every question is now asked of the whole field.
    """
    cited = (
        "## Review Panel\n\n"
        "| # | Reviewer | Finding | Disposition |\n|---|---|---|---|\n"
        "| 1 | r1 | [what it raised] see [#234](https://x) | applied |\n\n"
        "roster: r1 ✓  r2 ✓  r3 ✓\n"
    )

    assert panel_findings(cited)
    assert panel_findings(
        "## Review Panel\n\nAll six passes each. No findings.\n\n"
        "roster: [r1 ✓ r2 ✓] per [record](https://x)\n"
    )


def test_quoted_brackets_are_not_unanswered_fields() -> None:
    """The false-rejection half of the same change, and the direction that costs
    more: a finding naming `[0]`, or quoting the shipped row it is about, is an
    author writing accurately. Rejecting the description for describing is how a
    check teaches its reader to stop looking at it."""
    body = (
        "## Review Panel\n\n"
        "| # | Reviewer | Finding | Disposition |\n|---|---|---|---|\n"
        "| 1 | r1 | the `[0]` index is read twice | applied — see [#234](https://x) |\n\n"
        "roster: r1 ✓  r2 ✓  r3 ✓\n"
    )

    assert panel_findings(body) == []


def test_a_cell_boundary_is_an_unescaped_pipe() -> None:
    """A disposition explaining a table defect quotes a table row, and writes
    `\\|` inside a code span to do it. Splitting on every pipe tore that span
    into cells — inventing a cardinality the row never had, and exposing
    brackets that were quoted rather than unfilled.

    Found by running the check over this PR's own body, which is also how the
    reverse was found: a row with *unescaped* pipes inside a code span really is
    broken, because GitHub splits the cell before it reads the span. The check
    agreeing with the renderer is the point.
    """
    quoted = (
        "## Review Panel\n\n"
        "| # | Reviewer | Finding | Disposition |\n|---|---|---|---|\n"
        "| 1 | codex | a row read as filled | applied — `\\| 1 \\| r1 \\|` exited 0 |\n\n"
        "roster: r1 ✓  r2 ✓  r3 ✓\n"
    )

    assert panel_findings(quoted) == []
