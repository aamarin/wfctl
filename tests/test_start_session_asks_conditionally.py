"""`start-session`'s last step is a branch, not a question.

Step 9 asked "what are we working on today?" unconditionally from the day it was
written. Four worktrees created on 2026-09-06 with a full handoff each named
their own first action, stated it, and then stopped for a human who was not
there (#244).

These assert against rows, not against the step as a whole. The first version of
this file checked for substrings anywhere in step 9, and a review panel showed
all three passing on a scratch copy with the two table cells *swapped* — #244
reintroduced, and every unhandled session starting work unprompted, both green.
A check the violating artifact passes is what `a-rule-is-expressed-as-a-check`
calls the rule's absence, documented.
"""
from importlib.resources import files
from pathlib import Path

import pytest

# `files("wfctl")` rather than a repo-relative path, for the reason
# `test_skill_cross_references` gives: conftest's autouse `bundle` fixture
# repoints the bundle root at a fake tree, and the shipped text is the subject.
_SKILL = Path(str(files("wfctl"))) / "agents" / "skills" / "start-session" / "SKILL.md"

# Anchored on the heading rather than on `"\n9. "`. The step has been renumbered
# once already (8 → 9, `2fdbcdc`), and a renumber should fail as a named missing
# heading rather than as a bare ValueError out of a helper.
_STEP_NINE_HEADING = "**Answer the question, or ask it"
_STEP_EIGHT_HEADING = "Report status to the user:"


def _step_nine() -> str:
    text = _SKILL.read_text()
    if _STEP_NINE_HEADING not in text:
        pytest.fail(f"start-session no longer has a step headed {_STEP_NINE_HEADING!r}")
    return text[text.index(_STEP_NINE_HEADING) :]


def _row(condition: str) -> str:
    """The one table row in step 9 whose condition column starts with `condition`.

    Rows rather than the whole step, because the cell has to be tied to the
    condition that selects it — that binding is the entire content of the fix.
    """
    rows = [
        stripped
        for line in _step_nine().splitlines()
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
    row = _row("a summary naming a first action, and **no** `end` event")
    assert "Do not ask" in row
    assert "Quote the line" in row


def test_a_branch_that_has_ended_a_session_before_is_still_asked() -> None:
    """#244's acceptance criterion (b), and the one the first draft broke.

    `wfctl end` writes a summary with a filled `Next Session TODO` on every
    `/end-session`, so a quotable first action is the steady state of `main`
    rather than a signal. Gating row one on the summary alone had an attended
    `/start-session` in the main checkout begin work against a stale TODO — the
    criterion failing in as many words. The `end` event is the column that
    separates them."""
    row = _row("a summary, and an `end` event")
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


def test_step_eight_reports_which_row_step_nine_took() -> None:
    """Step 9's own argument for being checkable is that step 8 reports the row,
    so the report is the observable artifact and not decoration. It sits above
    step 9 and every other test here slices below it, so without this a later
    edit can delete the evidence and leave the rationale green."""
    text = _SKILL.read_text()
    if _STEP_EIGHT_HEADING not in text:
        pytest.fail(f"start-session no longer has a step headed {_STEP_EIGHT_HEADING!r}")
    step_eight = text[text.index(_STEP_EIGHT_HEADING) : text.index(_STEP_NINE_HEADING)]
    assert "**Next**" in step_eight
    assert "session-summary.md" in step_eight
    # Not just that it says "asking": the report has to separate the two rows
    # that ask, or it cannot show which of the three step 9 took.
    assert "which row of step 9" in step_eight
    assert "rows two and three both ask" in step_eight


def test_worktree_handoff_asks_for_a_line_step_nine_can_quote() -> None:
    """The two skills are one mechanism: step 9 proceeds only on a quotable
    imperative, and `worktree-handoff` is what makes handoff authors write one.
    Its previous wording — "plainly enough to be the default" — is the wording
    three of three panes satisfied while still asking, so a revert to it has to
    fail rather than pass."""
    handoff = (
        Path(str(files("wfctl"))) / "agents" / "skills" / "worktree-handoff" / "SKILL.md"
    ).read_text()
    assert "sentence it can quote" in handoff
    assert "Say that first action plainly enough" not in handoff
