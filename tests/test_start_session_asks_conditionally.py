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
stop, so these also slice step 3, the read step 8 is a branch on. Since #432
that read is `wfctl status --session`, which reports the stop's kind itself, and
the last row splits by branch kind: trunk still asks, and an issue branch starts
from the branch's progress unless the evidence disagrees.
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
_STEP_THREE_HEADING = "**Read the session report:**"
_STEP_FOUR_HEADING = "**Read the branch's commits"


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


_TRUNK_NO_ANSWER = "a trunk branch with no summary"
_ISSUE_NO_ANSWER = "an issue branch with no summary"


def test_a_trunk_branch_with_no_answer_in_the_state_dir_is_still_asked() -> None:
    """The other half of criterion (b), including the near-miss that is most
    likely to arrive: `wfctl end` writes `- [ ] (fill in)` when a session closes
    without the prose filled in, which is a summary carrying a TODO bullet that
    names nothing. On trunk nothing else says what the session is for, so the
    row still asks."""
    row = _row(_TRUNK_NO_ANSWER)
    assert "(fill in)" in row
    assert "Ask:" in row
    assert "Do not ask" not in row


def test_an_issue_branch_with_no_answer_starts_from_its_progress() -> None:
    """FR-022 and `session-start-reads-branch-progress`. Asking here had the user
    repeat what the branch name and the issue already say, every time a new
    worktree started.

    The order is the claim. The commit count says whether implementation has
    started, the pipeline position says how far the design got, and the issue
    says what the work is for. Read the other way round, the issue's prose
    decides before the repository has said where the work stands."""
    row = _row(_ISSUE_NO_ANSWER)
    assert "(fill in)" in row
    assert "Do not ask" in row
    evidence = ("the commit count", "the pipeline position", "the issue")
    positions = [row.find(item) for item in evidence]
    assert -1 not in positions, f"the row names no {evidence[positions.index(-1)]}"
    assert positions == sorted(positions), "the row reads its evidence out of order"
    assert "next command the pipeline position names" in row


def test_the_issue_row_asks_when_the_evidence_disagrees() -> None:
    """The record weighed going ahead and reporting the mismatch, and rejected
    it. A mismatch usually means the issue or the spec is out of date, and work
    done against the wrong one is wasted, while asking costs one turn."""
    row = _row(_ISSUE_NO_ANSWER)
    assert "naming the mismatch" in row
    assert "evidence disagrees" in row


def test_the_issue_row_asks_when_the_issue_line_has_no_answer() -> None:
    """When the issue line carries a reason code, the agent has the commit count
    and the pipeline position and nothing that says what the work is for. Two
    pieces of evidence can't disagree with a third that never arrived, so
    without this clause a `timeout` reads as agreement."""
    row = _row(_ISSUE_NO_ANSWER)
    assert "reason code" in row


def test_the_issue_row_asks_when_the_issue_body_is_empty() -> None:
    """PR-035. An issue with a title and no body has answered the tracker call
    and still says nothing about what is left to do. It is the reason-code case
    with a successful read, and treating it as evidence that agrees starts work
    on a guess."""
    row = _row(_ISSUE_NO_ANSWER)
    assert "issue body is empty" in row


def test_the_issue_row_reads_the_issue_when_the_report_left_the_body_out() -> None:
    """#699. A summary can exist and still name no first action, and the
    report leaves the body out whenever it prints a handoff. This row picks
    the next command from the issue and asks when the body is empty, so
    without the command it would read a missing body as an empty one."""
    row = _row(_ISSUE_NO_ANSWER)
    assert "left the issue body out" in row
    assert "`wfctl issue view <id>`" in row


def test_the_two_no_answer_rows_route_differently() -> None:
    """The swap this file's docstring records, applied to the split. A table
    whose two halves were given the same cell, or each other's, would pass any
    check that reads the step as a whole."""
    trunk = _row(_TRUNK_NO_ANSWER)
    issue = _row(_ISSUE_NO_ANSWER)
    assert trunk != issue
    assert "Ask:" in trunk and "Do not ask" not in trunk
    assert "Do not ask" in issue


def test_every_row_names_the_branch_kind() -> None:
    """Four rows since #432, and each one has to be selectable from the report
    alone. A row whose condition names no branch kind leaves the agent to judge
    which kind of branch it is on, which is the inference the report's issue
    line exists to replace."""
    rows = [
        line.strip()
        for line in _step_eight().splitlines()
        if line.strip().startswith("| ") and not line.strip().startswith("|---")
    ][1:]
    assert len(rows) == 4, rows
    for row in rows:
        condition = row.split("|")[1]
        assert "issue branch" in condition or "trunk branch" in condition, condition


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
    assert "which row of step 8" in step_seven
    # Three kinds of evidence, one per way a row is chosen: a quote, the
    # branch's progress, or the reason for asking. FR-022 asks for the second
    # by name, since without it a session that started from the pipeline
    # position reports the same as one that quoted a handoff.
    flat = " ".join(step_seven.split())
    assert "the commit count, the pipeline position, and the issue" in flat
    assert "that you are asking and why" in flat


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


def test_a_continued_stop_on_trunk_does_not_relax_the_quote_gate() -> None:
    """FR-006 and SC-003, on trunk. The gate is quoting a literal sentence, and
    no stop record reaches it.

    The failure this forbids is a row one that reads "a stop marked continued"
    and nothing else, which would start work on `main` from whatever the agent
    inferred, on the branches nobody is watching. An issue branch has its own
    no-quote row since #432, so the claim is limited to trunk."""
    carry_on = _row("an issue branch, or a stop marked continued")
    assert "naming a first action" in carry_on

    unquotable = _row(_TRUNK_NO_ANSWER)
    assert "Ask:" in unquotable
    assert "Do not ask" not in unquotable


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

    Step 3 names the outcome, a last stop of `none`, and step 8's rows once
    consumed it nowhere: row one wanted an issue branch or a
    continued stop, row two wanted a *last stop*, row three wanted an unquotable
    handoff. A trunk branch someone handed a filled handoff to fell through all
    three, and an agent resolving the gap by the pre-#352 table would have begun
    work against `main`'s accumulated TODO — SC-002 in as many words."""
    row = _row("a trunk branch with no stop at all, or whose last stop was not continued")
    assert "no stop at all" in row
    assert "Ask:" in row


def test_step_three_says_where_the_branch_kind_comes_from() -> None:
    """The branch kind decides every row, so step 3 has to hand step 8 a fact
    and not an impression.

    On a branch whose issue is `unknown`, the report makes no tracker call and
    its issue line reads `not-applicable`. Naming that line is what stops an
    agent inferring "trunk" from a branch called `develop-2`, or missing it on
    one called `main-rewrite`. The stop's kind used to come from a grep step 3
    stated; `last_stop()` reads it now, and `test_session_stopped_not_finished`
    holds the three cases the grep tests held."""
    step_three = _step_three()
    assert "Issue (tracker text): not-applicable" in step_three
    assert "unknown" in step_three
    assert "last stop" in step_three
