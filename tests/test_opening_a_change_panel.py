"""The panel step of `opening-a-change` stays where it was put, and stays
readable.

That the step names the panel skill at all is asserted in
`test_skill_cross_references`, beside the other reference this file makes. What
is here is what that file has no opinion on: where the step sits relative to the
one that fills the body, and whether the sentences pointing at steps by number
still resolve.

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

# Through `files("wfctl")`, not `_bundle.BUNDLE_ROOT`: conftest's autouse
# `bundle` fixture repoints that at a fake tree, and what ships is the question
# here. Same reason as `test_skill_cross_references`.
_WFCTL = Path(str(files("wfctl")))
_SKILL = _WFCTL / "agents" / "skills" / "opening-a-change" / "SKILL.md"
_TEMPLATE = (
    _WFCTL / "agents" / "configs" / "github" / ".github" / "pull_request_template.md"
)

_HEADING = re.compile(r"^## Step (\d+): (.*)$", re.MULTILINE)


def _steps() -> list[tuple[int, str]]:
    return [(int(n), title) for n, title in _HEADING.findall(_SKILL.read_text())]


def test_the_panel_runs_before_the_body_is_filled() -> None:
    """The panel's disposition table is content for the description, so a panel
    that runs after the body is written has nothing to contribute to it and its
    findings arrive against a change reviewers were already asked to read."""
    titles = [title.lower() for _, title in _steps()]
    # `next` with a default, so a retitled step fails with the list of titles
    # rather than erroring out of a generator with no diagnostic attached.
    panel = next((i for i, t in enumerate(titles) if "review panel" in t), -1)
    body = next((i for i, t in enumerate(titles) if "fill every section" in t), -1)
    assert panel >= 0 and body >= 0, titles

    # Position in the file, not the number in the heading: an agent reads the
    # steps in the order they are written, and a block moved without renumbering
    # would satisfy a comparison of the numbers while reversing the order.
    assert panel < body, titles


def test_the_steps_are_numbered_in_order_from_one() -> None:
    """A duplicated or skipped heading number leaves two steps answering to one
    reference. Guards the headings only; the references that read them are the
    test below, which is the half this one used to claim and not cover."""
    assert [n for n, _ in _steps()] == list(range(1, len(_steps()) + 1))


def test_the_in_file_step_references_point_at_the_step_they_name() -> None:
    """Three sentences in this file send the reader to a step by number, and
    inserting the panel step renumbered every one of them. A renumbering that
    updates the headings and misses a sentence reads as correct until it is
    followed — and the same insertion did miss two references of this shape in
    `cli.py` and `test_skill_commands.py`, which is how the hazard is known to
    be real rather than imagined.

    Resolved through the headings rather than pinned to a number, so a later
    insertion moves the expectation with the file. Scoped to the three
    references by their own wording: two more sentences near the top say "its
    Step 4" and "Its Step 1" about `finishing-a-development-branch`, and a
    blanket sweep would resolve those against the wrong file.
    """
    text = _SKILL.read_text()
    by_title = {title.lower(): n for n, title in _steps()}
    sidebar, open_it = by_title["fill the sidebar"], by_title["open it"]

    assert f"attribute Step {sidebar} cannot set" in text
    assert f"The sidebar is Step {sidebar}" in text
    assert f"push again before Step {open_it}" in text


def test_the_template_gives_the_panel_a_section() -> None:
    """Step 4 fills every section the template has, so a section is what turns
    "the panel ran" into something a body either answers or visibly does not.
    Without it the table has nowhere to land, and a body with no panel in it is
    indistinguishable from a change three reviewers passed."""
    assert "## Review Panel" in _TEMPLATE.read_text()
