"""The design skill proposes to `architecture-decisions` and judges nothing.

Both halves of that fail silently. A handoff naming a skill that moved is a
dead end the agent reads past, and a verdict word grown here would be wfctl's
third answer to the question #96 and #98 already answer differently — #100 owns
gate verdicts, and this skill was written to consume that vocabulary rather than
mint one.
"""
import re
from importlib.resources import files
from pathlib import Path

_AGENTS = Path(str(files("wfctl"))) / "agents"
_SKILL = _AGENTS / "skills" / "architecture-design" / "SKILL.md"

_REFERENCE = re.compile(r"\.agents/skills/([a-z0-9][a-z0-9-]*)")

# The verdict tokens already in force in the bundle: `speckit-implement` and
# `verification-before-completion` report PASS/FAIL, and `code-review` grades a
# finding BLOCKER. Case-sensitive because the skill legitimately uses two of
# these words in lower case — "pass" three times for a design pass, and
# "inconclusive" once while disclaiming the vocabulary it belongs to. Upper case
# is what distinguishes a verdict being minted from prose about one.
_VERDICTS = re.compile(r"\b(PASS|FAIL|BLOCKER)\b")


def test_architecture_design_hands_its_proposal_to_the_record_skill() -> None:
    """The handoff is the only thing that turns a proposed boundary into a
    record.

    Same shape as the level-2 gate: eleven designs carried an instruction to
    write the answer somewhere and none of them did. A skill that ends by
    naming no successor ends by leaving the proposal in the transcript. Presence
    is the invariant, not count — a second pointer to the same skill breaks
    nothing.
    """
    assert "architecture-decisions" in set(_REFERENCE.findall(_SKILL.read_text()))


def test_architecture_design_mints_no_verdict_of_its_own() -> None:
    """A `PASS` here would make three skills answer "did this clear the gate?"

    #100 exists to settle that question once, and the cost of a competing
    vocabulary is not a contradiction anyone reads — it is an agent closing an
    iteration with a word that looks authoritative and binds nothing.
    """
    minted = _VERDICTS.findall(_SKILL.read_text())

    assert minted == []
