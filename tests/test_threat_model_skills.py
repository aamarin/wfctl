"""The skill that writes a threat model and the skill that reads one agree.

`architecture-decisions/references/threat-model.md` defines the section and
its four parts, and `reviewing-security` searches for them by heading. If the
two drift, the reviewer finds no threat model on a record that has one and
reports the change as missing it, or worse, judges against a part it can't see.
The design side has to send the author there, too, or the section is never
written (`design/799-threat-model-in-the-record.md`).
"""
import re
from importlib.resources import files
from pathlib import Path

_SKILLS = Path(str(files("wfctl"))) / "agents" / "skills"
_REFERENCE = _SKILLS / "architecture-decisions" / "references" / "threat-model.md"
_REVIEWER = _SKILLS / "reviewing-security" / "SKILL.md"
_LINK_SUFFIX = "references/threat-model.md"
_TRIGGER = "adds, removes, loosens, or tightens"


def _part_headings() -> list[str]:
    """The `###` headings inside the reference's section skeleton."""
    skeleton = re.search(r"```markdown\n(## Threat model\n.*?)```", _REFERENCE.read_text(), re.S)
    assert skeleton, "the reference shows no `## Threat model` skeleton"
    return re.findall(r"^### (.+)$", skeleton.group(1), flags=re.M)


def test_the_reference_defines_the_four_parts_in_order() -> None:
    """The reviewer reads the parts by name, so their names and number are the
    contract. A fifth part, or a renamed one, has to change the reviewer too."""
    assert _part_headings() == [
        "Defends against", "Must keep catching", "Accepts", "Must let through",
    ]


def test_the_reviewer_names_the_section_and_every_part_the_reference_defines() -> None:
    """A part the reviewer doesn't name is a part it doesn't judge against."""
    reviewer = _REVIEWER.read_text()

    assert "## Threat model" in reviewer
    for part in _part_headings():
        assert f"`{part}`" in reviewer, part


def test_the_author_and_the_reviewer_both_link_the_one_reference() -> None:
    """The shape lives in one file so a change to it reaches both sides.
    `architecture-decisions` links it from inside its own folder, so the
    suffix is what all three share."""
    for skill in ("design-levels", "reviewing-security", "architecture-decisions"):
        assert _LINK_SUFFIX in (_SKILLS / skill / "SKILL.md").read_text(), skill


def test_every_design_skill_states_the_same_trigger() -> None:
    """Clarify settled that a tightened control counts as well as a loosened
    one. A skill still saying "narrows" sends a tightening past the threat
    model, which is how #769's change reached #792."""
    for skill in ("design-passes", "design-levels", "architecture-decisions", "reviewing-security"):
        assert _TRIGGER in (_SKILLS / skill / "SKILL.md").read_text(), skill


def test_the_reviewer_searches_the_trunk_for_threat_models_as_well_as_the_head() -> None:
    """A search at the head alone misses an accepted threat model the branch
    deleted, moved, or stripped of its heading, and the reviewer then judges
    against whatever the branch left. Two security reviewers found this on
    #799's own panel. The code panel then found that comparing against the
    trunk's tip reports every record accepted after the branch left as a
    deletion, so the branch is measured from its merge base, and the trunk is
    named on `origin` because a bare name can resolve to a tag."""
    reviewer = " ".join(_REVIEWER.read_text().split())

    assert "git grep -l '^## Threat model' <ref>" in reviewer
    assert "at the base, the trunk, and the head" in reviewer
    assert "Don't narrow the search to `wfctl arch-root`" in reviewer
    assert "git merge-base <trunk> <head>" in reviewer
    assert "--find-renames --name-status <base> <head>" in reviewer
    assert "`origin/<name>`" in reviewer


def test_the_reviewer_judges_an_edit_to_an_accepted_threat_model_with_no_code_change() -> None:
    """The reviewer once kept only records naming a control the commits
    changed, so a branch that moved a form between lists, or narrowed who the
    control defends against, without touching code went unjudged. PR review
    on #799 found both."""
    reviewer = " ".join(_REVIEWER.read_text().split())

    assert "whether or not the commits change a control" in reviewer
    assert "That covers the `Defends against` part as well as the lists" in reviewer


def test_a_listed_form_with_no_test_is_a_finding_and_may_precede_its_test() -> None:
    """The threat model comes before code, so the reference can't require a
    form's test to exist when the form is written down. The reviewer reports
    the missing test instead, once the change claims to be done."""
    reference = " ".join(_REFERENCE.read_text().split())
    reviewer = " ".join(_REVIEWER.read_text().split())

    assert "a form can go in the list before its test exists" in reference
    assert "A `Must keep catching` form with no test at the head is a finding" in reviewer


def test_a_successor_record_is_a_note_not_a_finding_every_round() -> None:
    """A successor the user accepted on the branch would otherwise draw the
    same findings each round and spend the round cap on a bar the user
    already agreed to, which is the #792 loop this change exists to stop."""
    reviewer = " ".join(_REVIEWER.read_text().split())

    assert "These notes don't by themselves make your verdict `Request changes`" in reviewer
