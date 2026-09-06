"""The review panel is reached from `opening-a-change`, and its findings have a
home in the body.

A skill is discovered by matching its description against what a reader said,
which is a mechanism with no input in an unattended run: nothing is typed, so
nothing matches, and the panel never runs while the change reports success
(#187). The reference from `opening-a-change` is the whole of the replacement.
It is one line of prose in a file nothing else reads, so dropping it restores
the defect and breaks no other test here.
"""
import re
from importlib.resources import files
from pathlib import Path

_WFCTL = Path(str(files("wfctl")))
_SKILL = _WFCTL / "agents" / "skills" / "opening-a-change" / "SKILL.md"
_TEMPLATE = (
    _WFCTL / "agents" / "configs" / "github" / ".github" / "pull_request_template.md"
)

_HEADING = re.compile(r"^## Step (\d+): (.*)$", re.MULTILINE)


def _steps() -> list[tuple[int, str]]:
    return [(int(n), title) for n, title in _HEADING.findall(_SKILL.read_text())]


def test_opening_a_change_names_the_panel_skill_by_path() -> None:
    """By path, not by phrase. #187 rejects the other repair — adding trigger
    phrases to the panel's description — because in an unattended run no phrase
    is uttered at all, so no description can match one."""
    assert ".agents/skills/fanning-out-code-review/SKILL.md" in _SKILL.read_text()


def test_the_panel_runs_before_the_body_is_filled() -> None:
    """The panel's disposition table is content for the description, so a panel
    that runs after the body is written has nothing to contribute to it and its
    findings arrive against a change reviewers were already asked to read."""
    titles = [title.lower() for _, title in _steps()]
    panel = next(i for i, t in enumerate(titles) if "review panel" in t)
    body = next(i for i, t in enumerate(titles) if "fill every section" in t)

    # Position in the file, not the number in the heading: an agent reads the
    # steps in the order they are written, and a block moved without renumbering
    # would satisfy a comparison of the numbers while reversing the order.
    assert panel < body, titles


def test_the_steps_are_numbered_in_order_from_one() -> None:
    """Two steps of this skill are referred to by number from inside it, and the
    panel step was inserted ahead of five that already existed. A renumbering
    that misses one leaves the file pointing a reader at the wrong step, which
    reads as correct until it is followed."""
    assert [n for n, _ in _steps()] == list(range(1, len(_steps()) + 1))


def test_the_template_gives_the_panel_a_section() -> None:
    """Step 4 fills every section the template has, so a section is what turns
    "the panel ran" into something a body either answers or visibly does not.
    Without it the table has nowhere to land, and a body with no panel in it is
    indistinguishable from a change three reviewers passed."""
    assert "## Review Panel" in _TEMPLATE.read_text()
