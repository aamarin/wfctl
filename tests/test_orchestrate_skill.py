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


def test_the_session_gate_is_the_first_step_orchestrate_runs() -> None:
    """Below the sub-issue scoping step it is not a gate.

    That step resolves a task range and can report a PR's state — findings,
    produced before anything asked whether they can be recorded. #117 is not
    that the run ended without a session; it is that the run happened.
    """
    first = _first_step()
    assert "session_started" in first, f"step 0 is not the session gate:\n{first}"


def test_the_gate_sends_the_reader_to_start_session_not_wfctl_start() -> None:
    """`wfctl start` clears the check and skips everything else the step does.

    A gate that names it trades one silent omission for another: the skills
    mirror is not refreshed, the architecture contract is not loaded, and the
    handoff is not read — and the user never learns any of that was skipped.
    """
    first = _first_step()
    assert "/start-session" in first


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
