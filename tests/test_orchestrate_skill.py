"""The session gate is orchestrate's first step, and nothing cites its steps by number.

#117 was a run that reached conclusions on a branch wfctl had no record of, so
the findings existed only in scrollback. The fix is an instruction, which the
suite cannot exercise — what it can hold is the one property the fix depends on:
the gate runs before the steps that produce findings. A gate that drifts below
them is the bug again, and it drifts silently, because moving a numbered step
breaks nothing a test asserts on.

The last test guards the way this change nearly shipped a defect of its own:
renumbering the steps retargeted `delivery-plan-template.md`'s "step 0" at the
new gate, in package data that lands in consumer repos. Naming a step is stable
under renumbering; a number is not.
"""
import re
from importlib.resources import files
from pathlib import Path

_AGENTS = Path(str(files("wfctl"))) / "agents"
_SKILL = _AGENTS / "skills" / "speckit-orchestrate" / "SKILL.md"

_STEP = re.compile(r"^(\d+)\. ", re.MULTILINE)


def _first_step() -> str:
    """The text of step 0, from its heading to the next numbered step."""
    text = _SKILL.read_text()
    starts = [m.start() for m in _STEP.finditer(text)]
    assert len(starts) >= 2, "orchestrate should have several numbered steps"
    return text[starts[0]:starts[1]]


def _displayed_strings() -> list[str]:
    """Every string step 0 tells the agent to display, however it is laid out.

    The quoted cell of each table row, plus any `- Display: "…"` bullet still
    there. Both forms rather than the current one, so the shape of the gate is
    the skill author's to choose and this stays a check on what it *says*.
    """
    step = _first_step()
    return [
        *re.findall(r"^\s*- Display: \"(.*)\"$", step, re.MULTILINE),
        *re.findall(r"^\s*\|[^|]*\|\s*\"(.*?)\"\s*\|", step, re.MULTILINE),
    ]


def test_the_session_gate_is_the_first_step_orchestrate_runs() -> None:
    """Below the sub-issue scoping step it is not a gate.

    That step resolves a task range and can report a PR's state — findings,
    produced before anything asked whether they can be recorded. #117 is not
    that the run ended without a session; it is that the run happened.
    """
    first = _first_step()
    assert "session_open" in first, f"step 0 is not the session gate:\n{first}"


def test_the_gate_sends_the_reader_to_start_session_not_wfctl_start() -> None:
    """`wfctl start` clears the check and skips everything else the step does.

    A gate that names it trades one silent omission for another: the skills
    mirror is not refreshed, the architecture contract is not loaded, and the
    handoff is not read — and the user never learns any of that was skipped.

    The displayed strings, not the step. Four paragraphs below them argue for
    `/start-session` over `wfctl start` by name, so a search over the whole step
    passes on the argument while the remedy itself says the other thing — which
    is what a mutation of the line demonstrated under #204.

    Read from the gate's table rather than from `- Display:` bullets, which is
    the form it had while there was one refusal to display. There are two since
    #200 — a branch that never had a session, and one another conversation
    holds — and **both** rows are asserted, because a table makes it easy to add
    a state whose remedy nobody wrote.
    """
    displayed = _displayed_strings()
    assert len(displayed) >= 2, f"the gate should display a string per state: {displayed}"
    assert all("/start-session" in d for d in displayed), displayed


def test_no_shipped_skill_cites_an_orchestrate_step_by_number() -> None:
    """A cross-reference that survives renumbering has to name the step.

    `delivery-plan-template.md` said "`speckit-orchestrate` step 0" and meant
    the epic-spec check; inserting the gate above it silently pointed consumer
    repos at the gate instead. Nothing failed — which is why this is a test and
    not a comment.
    """
    offenders = [
        f"{path.relative_to(_AGENTS)}:{n}: {line.strip()}"
        for path in _AGENTS.rglob("*.md")
        if path != _SKILL
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if "orchestrate" in line and re.search(r"\bstep \d", line, re.IGNORECASE)
    ]
    assert not offenders, "cite the step by name, not by number:\n" + "\n".join(offenders)
