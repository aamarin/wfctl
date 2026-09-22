"""The handoff has a slot for what the session was in the middle of (#397).

A restart fires when the context fills, mid-request, with nobody at the prompt.
The five sections the template asked for were all retrospective, so the turn
that wrote the handoff had nowhere to put the question the user had asked a
hundred seconds earlier — and a handoff that was correct about everything it
covered discarded it anyway. These tests hold the section in the two places it
has to exist at once: the scaffold `end` writes, and the template `end-session`
tells the agent to fill.
"""
from __future__ import annotations

import re
from pathlib import Path

from wfctl import _session

REPO = Path(__file__).resolve().parent.parent
END_SESSION = REPO / "wfctl" / "agents" / "skills" / "end-session" / "SKILL.md"
START_SESSION = REPO / "wfctl" / "agents" / "skills" / "start-session" / "SKILL.md"


def _scaffold() -> str:
    return _session._render_session_summary(
        "397-handoff-records-work-in-flight",
        _session.Observations(step="brainstorm", boundary="unanswered", tree="clean"),
    )


def _template_headings() -> list[str]:
    """The `## ` headings of the fill-in template inside step 4's fenced block.

    Indented three spaces, because the block sits inside a numbered step.
    """
    body = re.search(
        r"^4\. \*\*Fill in.*?```markdown\n(.*?)```", END_SESSION.read_text(), re.S | re.M
    )
    assert body, "end-session/SKILL.md step 4 has no markdown template block"
    return [line.strip() for line in body.group(1).splitlines() if line.strip().startswith("## ")]


def test_the_scaffold_carries_the_in_flight_section() -> None:
    """Prose telling an agent to add a section is a step, and this path's agent is
    one under the context pressure that just fired a restart. A placeholder
    already in the file is a slot instead."""
    assert f"{_session.IN_FLIGHT}\n\n- (fill in)\n" in _scaffold()


def test_the_template_asks_for_the_section_the_scaffold_writes() -> None:
    """Two spellings of the same heading is the drift that leaves an agent filling
    a section nothing reads."""
    assert _session.IN_FLIGHT in _template_headings()


def test_the_scaffold_headings_follow_the_template_order() -> None:
    """The scaffold writes a subset, and a subset in a different order reads as a
    different document — the agent filling it has to match section for section."""
    template = _template_headings()
    scaffold = [
        line.strip() for line in _scaffold().splitlines() if line.strip().startswith("## ")
    ]
    assert scaffold == [h for h in template if h in scaffold]


def test_in_flight_sits_above_the_next_action_section() -> None:
    """`names_no_first_action` reads from `## Next Session TODO` to the next `## `.
    Placed below it, a filled In Flight would answer for a next-action section
    nobody wrote, and the warning at the last moment an operator could fix it
    would never fire."""
    scaffold = _scaffold()
    assert scaffold.index(_session.IN_FLIGHT) < scaffold.index(_session.NEXT_SESSION_TODO)
    assert _session.names_no_first_action(scaffold)


def test_a_filled_in_flight_does_not_answer_for_the_next_action() -> None:
    """The regression the ordering above exists to prevent, exercised rather than
    asserted about."""
    filled = _scaffold().replace(
        f"{_session.IN_FLIGHT}\n\n- (fill in)",
        f"{_session.IN_FLIGHT}\n\n- User asked which record owns the boundary; unanswered.",
    )
    assert _session.names_no_first_action(filled)


def test_the_restart_path_rules_out_the_empty_answer() -> None:
    """"Nothing; between tasks" is the ordinary value everywhere else. On the path
    that stops mid-request with nobody at the prompt it is never true, and a
    template offering it as an option is one an unattended agent will take."""
    section = re.search(
        r"^## When the input is `restart`\n(.*?)(?=^## )", END_SESSION.read_text(), re.S | re.M
    )
    assert section, "end-session/SKILL.md has no `restart` section"
    assert _session.IN_FLIGHT in section.group(1)


def test_step_9_takes_its_quote_from_the_next_action_section_alone() -> None:
    """The routing In Flight could break, held by the sentence that scopes it.

    A request quoted in In Flight keeps the imperative it was asked in, so step
    9 scanning the whole file for a quotable first action can find one there and
    start on work aimed at a session that has already ended. Filling the section
    correctly is what produces that sentence, which is why tense advice in
    `end-session` is not where this can be fixed.
    """
    text = START_SESSION.read_text()
    step_9 = re.search(r"^9\. \*\*Answer the question.*", text, re.S | re.M)
    assert step_9, "start-session/SKILL.md has no step 9"
    # Whitespace-normalised: the sentence is wrapped across lines in the file,
    # and a rewrap would otherwise fail a rule it left intact.
    prose = " ".join(step_9.group(0).split())
    assert "and from nowhere else in the file" in prose
    assert _session.IN_FLIGHT in prose


def test_start_session_reports_what_was_in_flight() -> None:
    """A section written and never read is the same loss one level along: the user
    re-asks their question because the session that could see it said nothing."""
    text = START_SESSION.read_text()
    assert _session.IN_FLIGHT in text
    step_8 = re.search(r"^8\. Report status.*?(?=^9\. )", text, re.S | re.M)
    assert step_8, "start-session/SKILL.md has no step 8"
    assert "In Flight" in step_8.group(0)
