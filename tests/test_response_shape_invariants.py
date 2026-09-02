"""`conversation-response-shape` carries rules other files defer to.

Its content is prose, so the suite cannot check that it reads well. What it can
check is the structure other files depend on: that the rule numbers three
in-file references point at have not moved, that the form-selection table has
exactly one home, and that no example teaches a rule using vocabulary a
downstream repo has never heard of.

Each assertion here exists because the failure it catches is silent — the file
still installs, the suite still passes, and the cost lands on a reader.
"""

import re
from importlib.resources import files
from pathlib import Path

# Resolved through `files("wfctl")` for the same reason as
# `test_skill_cross_references`: conftest's autouse `bundle` fixture repoints
# `_bundle.BUNDLE_ROOT` at a fake tree, and reading the real shipped one is
# this file's whole purpose.
_AGENTS = Path(str(files("wfctl"))) / "agents"
_SKILL = _AGENTS / "skills" / "conversation-response-shape" / "SKILL.md"

# Not a correctness property — a decay one. This skill's documented failure is
# that its rules get lost partway through a long session, so every line is more
# surface for that to happen to, and the number exists to force a deliberate
# choice rather than to be correct.
#
# 480. The number has moved twice, both times because the file gained a rule
# rather than because the budget was wrong: 450 was estimated before any of the
# six rules were written, 460 held five, and rule 6 arrived from an experiment
# run after the plan was written. Two cuts were taken along the way — the
# "render the literal output" rule, which a control run found fires at the same
# rate when absent, and the worked example under "the drawing leads", which the
# form-selection table duplicates.
#
# Moving it again should mean cutting a rule, not adding a line. Six rules each
# carrying one example is the shape; a rule without an example does not fire.
_LINE_CEILING = 480


def test_the_first_three_rules_keep_their_numbers() -> None:
    """Three sentences in this file cite "rule 1" and "rule 3" by number, and
    nothing else checks them. Renumbering to slot a new rule in earlier would
    leave prose pointing at the wrong rule, reading correctly the whole time.
    """
    headings = re.findall(r"^## (\d)\. (.+)$", _SKILL.read_text(), re.MULTILINE)
    assert headings[:3] == [
        ("1", "Answer first"),
        ("2", "Frame in plain language before mechanics"),
        ("3", "Scale depth to what was asked for, never to the topic"),
    ]


def test_the_skill_stays_under_its_line_budget() -> None:
    """Rules decay across a long session, so length is a real cost here rather
    than a style preference. Overrunning is a signal to cut, and the feature
    plan names which passage goes first.
    """
    lines = len(_SKILL.read_text().splitlines())
    assert lines <= _LINE_CEILING, f"{lines} lines, ceiling {_LINE_CEILING}"


def test_the_form_selection_table_has_exactly_one_home() -> None:
    """The pull request template points at this table rather than restating it,
    and two more skills point at it once #556 lands. A copy goes stale the first
    time the table changes and then contradicts its owner silently —
    `knowledge-placement` calls that the condition with no owner.
    """
    homes = [md for md in _AGENTS.rglob("*.md") if "| The material is |" in md.read_text()]
    assert len(homes) == 1, f"expected one home, found {[str(m) for m in homes]}"


def _fenced_blocks(text: str) -> list[str]:
    """The fenced example blocks, without their fences."""
    return [b.rstrip("\n") for b in re.findall(r"```[^\n]*\n(.*?)```", text, re.DOTALL)]


def test_no_example_teaches_a_rule_in_wfctl_vocabulary() -> None:
    """This skill installs into every repo that runs `install-skills`, so an
    example built on wfctl's own commands is undecodable everywhere else (#80).
    Prose *about* wfctl is fine — the constraint is on examples, which are what
    a reader must follow to learn the rule. Red with two such blocks before
    #102; the second was a whole wfctl scenario, not a swappable identifier.
    """
    guilty = [b for b in _fenced_blocks(_SKILL.read_text()) if "wfctl" in b]
    assert not guilty, f"{len(guilty)} example block(s) still use wfctl vocabulary"
