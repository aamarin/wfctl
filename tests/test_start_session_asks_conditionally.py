"""`start-session`'s last step is a branch, not a question.

Step 9 asked "what are we working on today?" unconditionally from the day it was
written. Four worktrees created on 2026-09-06 with a full handoff each named
their own first action, stated it, and then stopped for a human who was not
there (#244). The fix is a branch on what step 4 found; these tests fail if it
reverts to a single unconditional ask, which is what the prose looked like for
nine months without anyone noticing it was a defect.
"""
from importlib.resources import files
from pathlib import Path

# `files("wfctl")` rather than a repo-relative path, for the reason
# `test_skill_cross_references` gives: conftest's autouse `bundle` fixture
# repoints the bundle root at a fake tree, and the shipped text is the subject.
_SKILL = Path(str(files("wfctl"))) / "agents" / "skills" / "start-session" / "SKILL.md"


def _step_nine() -> str:
    text = _SKILL.read_text()
    start = text.index("\n9. ")
    return text[start:]


def test_step_nine_proceeds_when_the_answer_is_already_on_disk() -> None:
    """The arm that closes #244. An unattended worktree carrying a handoff has
    been told what to do, and a step that asks anyway never reaches a pipeline
    step at all."""
    step = _step_nine()
    assert "Do not ask" in step
    assert "session-summary.md" in step


def test_step_nine_still_asks_when_nothing_answers_the_question() -> None:
    """The acceptance criterion that keeps attended sessions safe. A fix making
    every session start work unprompted trades one defect for a worse one."""
    step = _step_nine()
    assert "What are we working on today?" in step
    assert "no summary" in step


def test_step_nine_gates_on_a_quotable_line_rather_than_on_tone() -> None:
    """`worktree-handoff` already asked handoff authors to "say that first action
    plainly enough to be the default", and three of three panes did exactly that
    and asked anyway. `a-rule-is-expressed-as-a-check` names the shape: the
    branch has to turn on something observable, and the quote is it."""
    assert "Quote the line" in _step_nine()
