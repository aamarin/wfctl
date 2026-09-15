"""The two halves of the restart turn cannot drift apart (#371).

The hook sends one word and the skill says what that word does
(`design/371-the-session-restart-instruction-lives-in-end-session`). That split is
only safe while both halves agree, and nothing at runtime checks it: a renamed
section, or a send text with a trailing space, runs a normal end-session that
stops to ask a question nobody is there to answer, and the `/clear` behind it
never comes. These tests are what does check it.
"""
from __future__ import annotations

import re
from pathlib import Path

from wfctl import _restart

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "wfctl" / "agents" / "skills" / "end-session" / "SKILL.md"
WRAPPER = REPO / "wfctl" / "agents" / "commands" / "end-session.md"


def _restart_section() -> str:
    text = SKILL.read_text()
    match = re.search(r"^## When the input is `restart`\n(.*?)(?=^## )", text, re.S | re.M)
    assert match, "end-session/SKILL.md has no `restart` section for the hook to select"
    return match.group(1)


def test_the_hook_sends_exactly_the_word_the_skill_keys_on() -> None:
    assert _restart.END_TEXT == "/end-session restart"
    assert _restart.Decision(_restart.END).texts == ["/end-session restart"]


def test_the_restart_section_records_a_continued_stop() -> None:
    """`/start-session` takes its first row on a continued stop. A bare `wfctl
    end` records a wrapped-up one, and the session after the clear would read it
    as work somebody finished."""
    assert "wfctl end --continued" in _restart_section()


def test_the_restart_section_skips_both_questions() -> None:
    """Steps 6 and 7 ask before committing and before touching the tracker. Asked
    here, the question sits unanswered until the clear discards it."""
    section = _restart_section()
    assert re.search(r"Steps 6 and 7 are skipped", section)


def test_the_restart_section_names_the_step_numbers_that_still_exist() -> None:
    """The section overrides steps by number. A renumbered workflow would leave it
    describing steps that are now something else."""
    text = SKILL.read_text()
    for n, title in ((3, "Close the session"), (4, "Fill in"), (6, "Ask before committing"),
                     (7, "Ask before touching the tracker")):
        assert re.search(rf"^{n}\. \*\*{re.escape(title)}", text, re.M), (n, title)


def test_the_wrapper_passes_its_input_to_the_skill() -> None:
    """No wrapper read `$ARGUMENTS` before this; without it the word the hook sends
    never reaches the skill at all."""
    assert "$ARGUMENTS" in WRAPPER.read_text()


def test_the_default_threshold_is_written_once() -> None:
    """A second 200000 is a second default, and the two drift the first time one
    of them is tuned."""
    hits = [
        str(p.relative_to(REPO))
        for p in (REPO / "wfctl").rglob("*.py")
        if re.search(r"\b200_?000\b", p.read_text())
    ]
    assert hits == ["wfctl/_restart.py"], hits
    assert len(re.findall(r"\b200_?000\b", (REPO / "wfctl" / "_restart.py").read_text())) == 1
