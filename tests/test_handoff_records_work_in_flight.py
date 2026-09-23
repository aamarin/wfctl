"""The handoff has a slot for what the session was in the middle of (#397).

A restart fires when the context fills, mid-request, with nobody at the prompt.
The five sections the template asked for were all retrospective, so the turn
that wrote the handoff had nowhere to put the question the user had asked a
hundred seconds earlier — and a handoff that was correct about everything it
covered discarded it anyway.

What the change ships is prose in two skills plus one heading in the scaffold,
so these tests are the whole of what holds it. Each asserts on the clause that
carries the rule rather than on the heading being mentioned nearby: a check the
violating artifact passes is what `a-rule-is-expressed-as-a-check` calls the
rule's absence, documented, and three of these did exactly that on first
writing.
"""
from __future__ import annotations

import re
import types
from pathlib import Path

from typer.testing import CliRunner

from wfctl import _session
from wfctl.cli import app

REPO = Path(__file__).resolve().parent.parent
END_SESSION = REPO / "wfctl" / "agents" / "skills" / "end-session" / "SKILL.md"
START_SESSION = REPO / "wfctl" / "agents" / "skills" / "start-session" / "SKILL.md"

runner = CliRunner()


def _scaffold() -> str:
    return _session._render_session_summary(
        "397-handoff-records-work-in-flight",
        _session.Observations(step="brainstorm", boundary="unanswered", tree="clean"),
    )


def _flat(text: str) -> str:
    """One line, single-spaced. Every rule below is a sentence the file wraps."""
    return " ".join(text.split())


def _step(skill: Path, n: int) -> str:
    """One numbered step of a workflow, bounded by the next one.

    Bounded rather than open-ended: `re.S` with a trailing `.*` runs to EOF, so a
    rule that had moved out of the step into a later one would still be found and
    the test that exists to hold it in place would not notice.
    """
    match = re.search(
        rf"^{n}\. .*?(?=^\d+\. \*\*|^\d+\. [A-Z]|\Z)", skill.read_text(), re.S | re.M
    )
    assert match, f"{skill.name} has no step {n}"
    return _flat(match.group(0))


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


def test_the_restart_path_rules_out_the_empty_answer() -> None:
    """A stop where the context ran out was mid-something by construction.

    "Nothing" is the ordinary answer everywhere else, and an unattended agent
    offered it will take it. The clause ruling it out is what this holds — an
    earlier version asserted only that the heading appeared in the section, and
    stayed green when the clause was deleted.
    """
    restart = re.search(
        r"^## When the input is `restart`\n(.*?)(?=^## )", END_SESSION.read_text(), re.S | re.M
    )
    assert restart, "end-session/SKILL.md has no `restart` section"
    prose = _flat(restart.group(1))
    assert _session.IN_FLIGHT in prose
    assert 'a stop the context forced is never "Nothing"' in prose
    # The condition rules it out, not the input: the same file says a person
    # typing this by hand is indistinguishable from the hook, and one who does
    # so at a clean stop has "Nothing" as the true answer.
    assert "not the word that was typed" in prose


def test_step_9_takes_its_quote_from_the_next_action_section_alone() -> None:
    """The routing In Flight could break, held by the sentence that scopes it.

    A request quoted in In Flight keeps the imperative it was asked in, so step 9
    scanning the whole file for a quotable first action can find one there and
    start on work aimed at a session that has already ended. Filling the section
    correctly is what produces that sentence, which is why tense advice in
    `end-session` is not where this can be fixed.

    Naming the source is the assertion. An earlier version asserted "and from
    nowhere else in the file", which survives swapping the two sections and so
    passed on the exact inversion the sentence exists to prevent.
    """
    step_9 = _step(START_SESSION, 9)
    assert f"The quote comes from `{_session.NEXT_SESSION_TODO}`" in step_9
    assert _session.IN_FLIGHT in step_9


def test_start_session_reports_what_was_in_flight() -> None:
    """A section written and never read is the same loss one level along: the user
    re-asks their question because the session that could see it said nothing."""
    step_8 = _step(START_SESSION, 8)
    assert f"the summary's `{_session.IN_FLIGHT}`, verbatim" in step_8


def test_step_8_routes_the_placeholder_to_the_check_not_to_silence() -> None:
    """Two failures one step apart, and the fix for the first opened the second.

    Reported as content, the scaffold's `- (fill in)` reaches the user as an
    outstanding request nobody made. Suppressed, the session that dropped a real
    request leaves nobody who knows it was asked — which is #397's own loss, one
    turn later. Neither is step 8's to judge: `wfctl start` observes the artifact
    and step 8 carries what it printed.
    """
    step_8 = _step(START_SESSION, 8)
    assert "still `(fill in)`" in step_8
    assert "none of the three is a request" in step_8
    assert "`wfctl start` in step 2 prints a `⚠`" in step_8


def test_an_unfilled_in_flight_is_observed_rather_than_stated() -> None:
    """`a-rule-is-expressed-as-a-check`, over the artifact the work produces.

    "Fill this in" is prose in `end-session`, and a violation of it is visible in
    `session-summary.md`. The record calls a rule delivered with nothing
    observing it the rule's absence documented, so this is the observation.
    """
    assert _session.in_flight_unfilled(_scaffold())


def test_a_filled_in_flight_is_not_reported_as_unfilled() -> None:
    """Including the answer that looks like nothing happened.

    "Nothing; between tasks" is the ordinary value on an attended close, and a
    check that read it as unfilled would warn on every well-written handoff —
    the shape that gets a warning switched off rather than fixed.
    """
    for answer in ("- Nothing; between tasks", "- User asked about the boundary."):
        filled = _scaffold().replace(
            f"{_session.IN_FLIGHT}\n\n{_session.IN_FLIGHT_PLACEHOLDER}",
            f"{_session.IN_FLIGHT}\n\n{answer}",
        )
        assert not _session.in_flight_unfilled(filled), answer


def test_a_handoff_end_did_not_write_is_not_judged() -> None:
    """`worktree-handoff` documents use their own shape and never carry the
    section, and every summary written before it existed lacks it too. Read as
    unfilled, those warn on the one file most likely to be complete — which is
    `names_no_first_action`'s own reason for gating on the template mark."""
    assert not _session.in_flight_unfilled("# Handoff — written before this branch existed\n")
    assert not _session.in_flight_unfilled(
        "# Session Summary: 2026-09-22 — b\n\n## Next Session TODO\n\n- [ ] rebase\n"
    )


def test_a_section_below_does_not_answer_for_the_in_flight_one() -> None:
    """The bound `names_no_first_action` walks, applied to this section: the scan
    stops at the next `## ` so a filled section underneath cannot stand in for an
    empty one above."""
    unfilled = _scaffold().replace(
        f"{_session.NEXT_SESSION_TODO}\n\n{_session.NEXT_ACTION_PLACEHOLDER}",
        f"{_session.NEXT_SESSION_TODO}\n\n- [ ] rebase onto main",
    )
    assert _session.in_flight_unfilled(unfilled)


def test_start_warns_when_the_last_handoff_left_the_section_unfilled(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The check runs where it can see what the agent wrote.

    `end` writes the scaffold at step 3 and the agent fills it at step 4, so no
    reader inside `end` can answer this. `start` is the first wfctl command on
    the far side of the restart's `/clear`, and the session it opens is the one
    that would otherwise carry on knowing nothing was lost.
    """
    runner.invoke(app, ["start"])
    runner.invoke(app, ["end", "--continued"])

    result = runner.invoke(app, ["start"])

    assert result.exit_code == 0, result.output
    assert "left its in-flight section unfilled" in result.output


def test_start_says_nothing_when_the_section_was_filled(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A warning that fires on a well-written handoff is one that gets switched
    off. "Nothing; between tasks" is the ordinary answer and must be silent."""
    runner.invoke(app, ["start"])
    runner.invoke(app, ["end", "--continued"])
    summary = storyctl_dir.agent_dir / "session-summary.md"
    summary.write_text(
        summary.read_text().replace(
            f"{_session.IN_FLIGHT}\n\n{_session.IN_FLIGHT_PLACEHOLDER}",
            f"{_session.IN_FLIGHT}\n\n- Nothing; between tasks",
        )
    )

    result = runner.invoke(app, ["start"])

    assert result.exit_code == 0, result.output
    assert "in-flight" not in result.output


def test_start_warns_on_the_already_initialized_path(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The path a restart actually takes.

    `start` returns early once the branch has a session, and `/start-session`
    runs it on every handoff after the first — so a check placed below that
    guard would be silent on every run that matters and fire only on a branch's
    very first one, where there is no previous handoff to judge.
    """
    runner.invoke(app, ["start"])
    runner.invoke(app, ["end", "--continued"])
    runner.invoke(app, ["start"])

    result = runner.invoke(app, ["start"])

    assert "Already initialized" in result.output
    assert "left its in-flight section unfilled" in result.output
