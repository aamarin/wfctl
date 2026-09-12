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
#
# 483 adds lines, and is taken as a disclosed exception rather than under the
# sentence above. The arithmetic, because a paragraph arguing for its own
# exception has to survive being checked: `SKILL.md` was 478 and is now 483 —
# five lines, four of prose and the separator — so the ceiling spends the two
# it had spare and takes three more.
#
# What those five buy is not a seventh rule. They are the Persistence section's
# pointer at `digest.md`, which is the countermeasure to the decay this ceiling
# is a proxy for: the file is capped because its rules get lost mid-session,
# and those lines are what say they are now re-sent every turn. Paying them
# once to stop measuring the wrong surface is the trade, and the rule above
# still stands for the seventh rule when it comes.
#
# The ceiling now equals the file exactly. That is deliberate — the next line
# added to `SKILL.md` has to argue for itself here rather than land in slack.
#
# 490 is that argument, and the second disclosed exception. Seven lines: one
# table row under rule 3, and a six-line paragraph lifting rule 2's
# two-sentence cap when the reader asked for plain words.
#
# Not a seventh rule, which is why it ships without an example of its own —
# the table row carries the form and rule 2's paragraph carries only where its
# cap stops applying. The sentence above still governs the seventh rule.
#
# What the seven buy is a contradiction, not an addition. Rule 3 granted a
# request for a simple explanation full depth; rule 2 forbade plain language
# past two sentences. A reply that satisfied such a reader had to break rule 2
# to do it, so the file taught the wrong thing at the moment it was most likely
# to be reached for.
#
# 491 is the third disclosed exception, and one line: a sixth row in the
# form-selection table, for a chain of calls whose destinations fan out again.
#
# Not a seventh rule, so it ships without an example of its own — the row
# carries its form in the same two columns as the five above it, and the
# sentence about cutting rather than adding still governs the seventh rule.
#
# What the line buys is a shape that was being drawn by hand instead of picked.
# The two nearest rows each carry one layer of a nested chain and stop: `one
# source, several destinations` draws the fan and drops that a destination fans
# again; `a sequence with exits` draws the exits and drops that the sequence is
# reached through three other nodes. A reader who found neither invented a
# drawing, which is the failure the table exists to prevent.
_LINE_CEILING = 491


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
