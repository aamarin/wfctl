"""The skills an agent reads name `wfctl auto-approve`, and the rule against an unasked grant (#407).

wfctl can't tell a grant someone asked for from one nobody did, so the only
control on the agent's side is an instruction in `using-wfctl`. Deleting it
would leave the suite green and the agent free to grant itself the mode. These
tests read the shipped skills, not the installed copies, because `.agents/` is
gitignored and a green suite says nothing about it.
"""
from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

_SKILLS = Path(str(files("wfctl"))) / "agents"
_USING = _SKILLS / "skills" / "using-wfctl" / "SKILL.md"
_WALKTHROUGH = _SKILLS / "skills" / "plan-walkthrough" / "SKILL.md"


def _paragraphs(text: str) -> list[str]:
    return [" ".join(p.split()) for p in re.split(r"\n\s*\n", text)]


def test_using_wfctl_turns_the_mode_on_only_when_a_person_asked() -> None:
    """The rule the record accepts as the agent-side control.

    Checked as one paragraph naming both the command and "only when", so moving
    the command out of the rule fails here too.
    """
    assert any(
        "wfctl auto-approve on" in p and "only when" in p
        for p in _paragraphs(_USING.read_text())
    )


def test_using_wfctl_never_names_the_creation_variable_as_a_reason_to_grant() -> None:
    """A security reviewer found the rule said to run `on` when the run started
    with `WFCTL_AUTO_APPROVE=1`. The creation hook already made that grant, so
    the clause only fired after the review cap turned the mode off, and moved
    the re-grant wfctl refuses to make into the agent."""
    rule = next(
        p for p in _paragraphs(_USING.read_text())
        if "wfctl auto-approve on" in p and "only when" in p
    )
    assert "or started the run with" not in rule
    assert "never a reason" in rule


def test_using_wfctl_lists_the_new_command() -> None:
    """An agent looking up how to set the mode finds the command, not `start`'s flag."""
    text = _USING.read_text()
    row = next(line for line in text.splitlines() if line.startswith("| `wfctl auto-approve` |"))
    assert "`wfctl auto-approve on`" in row and "`wfctl auto-approve off`" in row


def test_no_shipped_skill_tells_the_agent_to_set_the_mode_through_start() -> None:
    """SC-005. An agent following old text would keep printing "Already initialized".

    A sentence saying the flag still works is allowed. One telling the agent to
    run it is not.
    """
    offenders = []
    for path in _SKILLS.rglob("*.md"):
        for line in path.read_text().splitlines():
            if re.search(r"[Rr]un `wfctl start --(no-)?auto-approve`", line):
                offenders.append(f"{path.relative_to(_SKILLS)}: {line.strip()}")
    assert offenders == []


def test_the_walkthrough_refusal_names_auto_approve_off() -> None:
    """FR-012. The refusal tells the person the one command that lets the walkthrough run."""
    text = _WALKTHROUGH.read_text()
    refusal = text[text.index("Plan walkthrough needs a person at the prompt"):]
    refusal = refusal[: refusal.index("```")]

    assert "wfctl auto-approve off" in refusal
    assert "start --no-auto-approve" not in refusal


def test_using_wfctl_says_install_config_writes_once() -> None:
    """FR-013. Without it, an agent expects a template change to reach a seeded repo.

    `--force` replacing the repo's edits is the part that costs someone their work.
    """
    paragraphs = [p for p in _paragraphs(_USING.read_text()) if "install-config" in p]

    assert any("once" in p and "--force" in p and "edits" in p for p in paragraphs)
