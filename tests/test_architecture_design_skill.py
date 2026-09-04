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

# The verdict tokens already in force elsewhere in the bundle: `speckit-implement`
# and `verification-before-completion` report PASS/FAIL, `wfctl verify` records
# `inconclusive`. Matched case-sensitively — the skill's prose says a driver must
# be specific enough to fail, and lowercase "fail" is that sentence, not a verdict.
_VERDICTS = re.compile(r"\b(PASS|FAIL|BLOCKED|INCONCLUSIVE)\b")


def test_the_design_skill_hands_its_proposal_to_the_record_skill() -> None:
    """The handoff is the only thing that turns a proposed boundary into a
    record, and it is one reference.

    Same shape as the level-2 gate: eleven designs carried an instruction to
    write the answer somewhere and none of them did. A skill that ends by
    naming no successor ends by leaving the proposal in the transcript.
    """
    assert "architecture-decisions" in set(_REFERENCE.findall(_SKILL.read_text()))


def test_the_design_skill_mints_no_verdict_of_its_own() -> None:
    """A `PASS` here would make three skills answer "did this clear the gate?"

    #100 exists to settle that question once, and the cost of a competing
    vocabulary is not a contradiction anyone reads — it is an agent closing an
    iteration with a word that looks authoritative and binds nothing.
    """
    minted = _VERDICTS.findall(_SKILL.read_text())

    assert minted == []
