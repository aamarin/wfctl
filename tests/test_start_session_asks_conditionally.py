"""`start-session`'s last step is a branch, not a question.

Step 8 asked "what are we working on today?" unconditionally from the day it was
written. Four worktrees created on 2026-09-06 with a full handoff each named
their own first action, stated it, and then stopped for a human who was not
there (#244).

These assert against rows, not against the step as a whole. The first version of
this file checked for substrings anywhere in step 8, and a review panel showed
all three passing on a scratch copy with the two table cells *swapped* — #244
reintroduced, and every unhandled session starting work unprompted, both green.
A check the violating artifact passes is what `a-rule-is-expressed-as-a-check`
calls the rule's absence, documented.

Since #352 the branch reads the last stop's *kind* rather than the presence of a
stop, so these also slice step 3 — the read step 8 is a branch on. Every helper
here used to start at step 8's heading, which left the one step that decides what
step 8 sees unreachable by any assertion in the file.
"""
from importlib.resources import files
from pathlib import Path

import pytest

# `files("wfctl")` rather than a repo-relative path, for the reason
# `test_skill_cross_references` gives: conftest's autouse `bundle` fixture
# repoints the bundle root at a fake tree, and the shipped text is the subject.
_SKILL = Path(str(files("wfctl"))) / "agents" / "skills" / "start-session" / "SKILL.md"

# Anchored on the heading rather than on `"\n8. "`. The step has been renumbered
# twice already (8 → 9, `2fdbcdc`; 9 → 8, #485), and a renumber should fail as
# a named missing heading rather than as a bare ValueError out of a helper.
_STEP_EIGHT_HEADING = "**Answer the question, or ask it"
_STEP_SEVEN_HEADING = "Report status to the user:"
_STEP_THREE_HEADING = "**Read the position, then the handoff:**"
_STEP_FOUR_HEADING = "**Surface work done on this branch**"


def _step_eight() -> str:
    text = _SKILL.read_text()
    if _STEP_EIGHT_HEADING not in text:
        pytest.fail(f"start-session no longer has a step headed {_STEP_EIGHT_HEADING!r}")
    return text[text.index(_STEP_EIGHT_HEADING) :]


def _step_three() -> str:
    """Step 3 alone, bounded at both ends.

    Step 8 is last, so `_step_eight` can run to the end of the file. Step 3 is in
    the middle, and an unbounded slice would carry step 8's table into it — where
    a prefix match finds a row that belongs to the other table and asserts
    nothing about this one.
    """
    text = _SKILL.read_text()
    for heading in (_STEP_THREE_HEADING, _STEP_FOUR_HEADING):
        if heading not in text:
            pytest.fail(f"start-session no longer has a step headed {heading!r}")
    return text[text.index(_STEP_THREE_HEADING) : text.index(_STEP_FOUR_HEADING)]


def _row(condition: str, section: str | None = None) -> str:
    """The one table row in step 8 whose condition column starts with `condition`.

    Rows rather than the whole step, because the cell has to be tied to the
    condition that selects it — that binding is the entire content of the fix.
    """
    rows = [
        stripped
        for line in (section if section is not None else _step_eight()).splitlines()
        # The table is indented inside the numbered step, so the row's own text
        # starts after the leading whitespace and the opening pipe.
        for stripped in [line.strip()]
        if stripped.startswith("| ") and stripped[2:].startswith(condition)
    ]
    if len(rows) != 1:
        pytest.fail(f"expected one row starting {condition!r}, found {len(rows)}")
    return rows[0]


def test_a_handoff_on_a_branch_nobody_has_worked_on_starts_without_a_reply() -> None:
    """#244's acceptance criterion (a). An unattended worktree carrying a handoff
    has been told what to do, and a step that asks anyway never reaches a
    pipeline step at all."""
    row = _row("an issue branch, or a stop marked continued")
    assert "Do not ask" in row
    assert "Quote the line" in row


def test_a_branch_that_has_ended_a_session_before_is_still_asked() -> None:
    """#244's acceptance criterion (b), and the one the first draft broke.

    `wfctl end` writes a summary with a filled `Next Session TODO` on every
    `/end-session`, so a quotable first action is the steady state of `main`
    rather than a signal. Gating row one on the summary alone had an attended
    `/start-session` in the main checkout begin work against a stale TODO — the
    criterion failing in as many words. What separates them is whether the
    branch names an issue: `main` accumulates a handoff from every session that
    ever ended on it, and its top TODO is as likely to be last month's as
    today's."""
    row = _row("a trunk branch with no stop at all, or whose last stop was not continued")
    assert "Ask:" in row
    assert "Do not ask" not in row


def test_a_state_dir_with_no_answer_in_it_is_still_asked() -> None:
    """The other half of criterion (b), including the near-miss that is most
    likely to arrive: `wfctl end` writes `- [ ] (fill in)` when a session closes
    without the prose filled in, which is a summary carrying a TODO bullet that
    names nothing."""
    row = _row("no summary, one whose next action is still `(fill in)`")
    assert "Ask:" in row
    assert "Do not ask" not in row


def test_step_seven_reports_which_row_step_eight_took() -> None:
    """Step 8's own argument for being checkable is that step 7 reports the row,
    so the report is the observable artifact and not decoration. It sits above
    step 8 and every other test here slices below it, so without this a later
    edit can delete the evidence and leave the rationale green."""
    text = _SKILL.read_text()
    if _STEP_SEVEN_HEADING not in text:
        pytest.fail(f"start-session no longer has a step headed {_STEP_SEVEN_HEADING!r}")
    step_seven = text[text.index(_STEP_SEVEN_HEADING) : text.index(_STEP_EIGHT_HEADING)]
    assert "**Next**" in step_seven
    assert "session-summary.md" in step_seven
    # Not just that it says "asking": the report has to separate the two rows
    # that ask, or it cannot show which of the three step 8 took.
    assert "which row of step 8" in step_seven
    assert "rows two and three both ask" in step_seven


def test_worktree_handoff_asks_for_a_line_step_eight_can_quote() -> None:
    """The two skills are one mechanism: step 8 proceeds only on a quotable
    imperative, and `worktree-handoff` is what makes handoff authors write one.
    Its previous wording — "plainly enough to be the default" — is the wording
    three of three panes satisfied while still asking, so a revert to it has to
    fail rather than pass."""
    handoff = (
        Path(str(files("wfctl"))) / "agents" / "skills" / "worktree-handoff" / "SKILL.md"
    ).read_text()
    assert "sentence it can quote" in handoff
    assert "Say that first action plainly enough" not in handoff


def test_a_stop_marked_continued_shares_the_do_not_ask_row() -> None:
    """#352's stall. A run cut off mid-work writes a handoff and a continued
    stop, and the session that follows has everything it needs; asking anyway
    puts the question to the one person the interruption established is absent.

    Same row as a branch with no stop, and that is the claim worth pinning: the
    existing behaviour there was already *do not ask*, so this is one row with
    two conditions rather than a fourth row nobody has to keep consistent."""
    row = _row("an issue branch, or a stop marked continued")
    assert "Do not ask" in row
    assert "Quote the line" in row


def test_a_continued_stop_does_not_relax_the_quote_gate() -> None:
    """FR-006 and SC-003. The gate is quoting a literal sentence, and no stop
    record reaches it.

    The failure this forbids is a row one that reads "a stop marked continued"
    and nothing else — which would start work on whatever the agent inferred the
    branch was probably for, on precisely the branches nobody is watching."""
    carry_on = _row("an issue branch, or a stop marked continued")
    assert "naming a first action" in carry_on

    unquotable = _row("no summary, one whose next action is still `(fill in)`")
    assert "Ask:" in unquotable
    assert "Do not ask" not in unquotable


def test_step_three_reads_the_last_stop_and_not_any_stop() -> None:
    """FR-007, which lives entirely in this step's `tail -1`.

    Step 3's old phrasing — *whether any line carries `"event": "end"`* — cannot
    express it. On a branch wrapped up once and interrupted since, "any" finds
    the older stop and asks a question the newer one already answered. The
    command is stated literally in the step because an agent improvising a grep
    gets it wrong in the direction that starts work unbidden."""
    step_three = _step_three()
    assert "tail -1" in step_three
    assert "whether any line carries" not in step_three


def test_step_three_rejects_a_torn_line_rather_than_reading_it() -> None:
    """A partial append is a fragment of a stop, and it still says `end`.

    Without the `}$` the plain grep matches it, `tail -1` prefers it to the real
    stop underneath, and — lacking `"continued": true` — it reads as a wrap-up.
    A run that was cut off then asks, which is the defect this whole change
    removes, arriving through the log's most likely corruption."""
    assert "}$" in _step_three()


def test_step_three_names_all_three_outcomes_of_that_read() -> None:
    """A two-outcome read is the same defect wearing the new command.

    `grep | tail -1` returns nothing, a continued line, or any other line, and
    the third covers both `"continued": false` and a stop recorded before this
    feature existed. Collapsing it to "continued or not" leaves the reader to
    decide what an absent key means, which is the one thing the migration
    turns on."""
    step_three = _step_three()
    for outcome in ("nothing", '`"continued": true`', "any other line"):
        assert outcome in step_three, f"step 3 states no outcome for {outcome}"


def test_an_issue_branch_is_never_asked_what_to_work_on() -> None:
    """The question has one answer on an issue branch and the branch is already
    carrying it.

    `352-session-stopped-not-finished` says what the session is for in its own
    name, so asking spends a turn to be told what `wfctl status` prints on its
    first line. The stop's kind is the wrong column there: a session that wrapped
    up deliberately on an issue branch left the *same* issue open, and the next
    one is not at liberty to work on something else."""
    row = _row("an issue branch, or a stop marked continued")
    assert "Do not ask" in row
    assert _row("a trunk branch with no stop at all, or whose last stop was not continued") != row


def test_a_trunk_branch_with_no_stop_at_all_is_asked_too() -> None:
    """The state that matched no row when the branch axis first landed.

    Step 3's table names the outcome — `nothing` comes back from the grep — and
    step 8's rows consumed it nowhere: row one wanted an issue branch or a
    continued stop, row two wanted a *last stop*, row three wanted an unquotable
    handoff. A trunk branch someone handed a filled handoff to fell through all
    three, and an agent resolving the gap by the pre-#352 table would have begun
    work against `main`'s accumulated TODO — SC-002 in as many words."""
    row = _row("a trunk branch with no stop at all, or whose last stop was not continued")
    assert "no stop at all" in row
    assert "Ask:" in row


def test_step_three_says_where_the_branch_kind_comes_from() -> None:
    """The issue key decides two of the three rows, so step 3 has to hand step 8
    a fact and not an impression.

    `wfctl status --json` is already run at the top of this step and `issue` is
    the first key in its payload, so this costs no command. `unknown` is the
    literal it prints for a branch whose name carries no key — naming the literal
    is what stops an agent inferring "trunk" from a branch called `develop`, or
    missing it on one called `main-rewrite`."""
    step_three = _step_three()
    assert "issue" in step_three
    assert "unknown" in step_three
