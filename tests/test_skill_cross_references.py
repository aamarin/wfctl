"""Every skill a shipped file tells the agent to read is a skill that ships.

Skills reference each other by path — a command wrapper points at the skill it
activates, and `start-session` loads the two output-style skills by name. Those
reads fail silently on purpose: `start-session` says to skip an uninstalled
skill rather than stop the session. So a renamed or dropped skill costs the
session a rule and reports nothing, which is #23's shape one directory over.
"""
import re
from importlib.resources import files
from pathlib import Path


# Resolved through `files("wfctl")` for the same reason as
# `test_pipeline_commands`: conftest's autouse `bundle` fixture repoints
# `_bundle.BUNDLE_ROOT` at a fake tree, and reading the real shipped one is this
# file's whole purpose.
_AGENTS = Path(str(files("wfctl"))) / "agents"

# Trailing `/` excluded from the name so a bare `.agents/skills/` — prose about
# the directory, not a reference to one skill — doesn't read as a skill called "".
_REFERENCE = re.compile(r"\.agents/skills/([a-z0-9][a-z0-9-]*)")


def _references() -> dict[str, list[str]]:
    """Skill name → the shipped files naming it."""
    found: dict[str, list[str]] = {}
    for md in sorted(_AGENTS.rglob("*.md")):
        for name in _REFERENCE.findall(md.read_text()):
            found.setdefault(name, []).append(str(md.relative_to(_AGENTS)))
    return found


def test_every_referenced_skill_ships() -> None:
    missing = {
        name: sources
        for name, sources in _references().items()
        if not (_AGENTS / "skills" / name / "SKILL.md").exists()
    }
    assert not missing, f"referenced but not shipped: {missing}"


def test_the_output_style_skills_are_both_loaded_at_session_start() -> None:
    """`i-have-adhd` sets length, `conversation-response-shape` sets order and
    depth. Neither is model-invocable, so nothing else turns them on — dropping
    either from step 1 disables it for every session, quietly."""
    start = (_AGENTS / "skills" / "start-session" / "SKILL.md").read_text()
    loaded = set(_REFERENCE.findall(start))
    assert {"i-have-adhd", "conversation-response-shape"} <= loaded


def test_each_output_style_skill_has_a_command_wrapper() -> None:
    """The wrapper is the only way to turn one back on mid-session, after a
    session that started without `/start-session` or said "stop adhd mode"."""
    for name in ("i-have-adhd", "conversation-response-shape"):
        assert (_AGENTS / "commands" / f"{name}.md").exists(), name


def test_start_session_loads_the_in_force_set() -> None:
    """FR-009's whole delivery path is this one line in one skill.

    A `SessionStart` hook would have been the obvious route and is not one wfctl
    controls: the hook file belongs to the consumer (#85). So nothing else puts
    accepted records in front of an agent, and dropping the call would leave the
    projection shipping, tested, and read by nobody.
    """
    start = (_AGENTS / "skills" / "start-session" / "SKILL.md").read_text()
    assert "wfctl arch context" in start


def test_the_record_template_ships_beside_the_adr_skill() -> None:
    """The skill tells the agent to copy a template that MANIFEST.in has to
    graft. A skill directory whose non-SKILL.md files were never packaged
    installs cleanly and then fails at the moment a record is being written."""
    skill = _AGENTS / "skills" / "architecture-decisions"
    assert (skill / "SKILL.md").exists()
    assert (skill / "record-template.md").exists()


def test_the_level_2_gate_names_the_record_skill() -> None:
    """The gate is the only thing that turns a level-2 answer into a record.
    Eleven designs carried the instruction to write the answer into a
    `design.md` section and none of them did; the reference is what replaces
    that instruction with a skill the agent actually opens."""
    gate = (_AGENTS / "skills" / "design-levels" / "SKILL.md").read_text()
    assert "architecture-decisions" in set(_REFERENCE.findall(gate))


def test_the_record_template_carries_every_section_a_record_needs() -> None:
    """`Owns truth` is the field this feature exists to capture, and the
    template is where the agent gets it from — a template missing it produces
    records missing it, which is the failure being corrected with a new
    filename."""
    template = (
        _AGENTS / "skills" / "architecture-decisions" / "record-template.md"
    ).read_text()
    for section in ("Context", "Decision", "Owns truth", "Considered", "Log"):
        assert f"## {section}" in template, section


def test_the_change_description_skill_defers_to_the_finishing_skill() -> None:
    """`opening-a-change` layers a description step over the integration
    decision rather than owning it.

    `vendor-upstream-skills` forbids editing the vendored skill, so the whole
    layering depends on this one reference. Drop it and the new skill quietly
    becomes a second, competing account of how a branch gets integrated — the
    duplication the record exists to prevent, one skill over.
    """
    skill = (_AGENTS / "skills" / "opening-a-change" / "SKILL.md").read_text()
    assert "finishing-a-development-branch" in set(_REFERENCE.findall(skill))


def test_the_change_description_skill_does_not_restate_the_template() -> None:
    """The skill says to go read the project's template; it must not carry the
    sections itself.

    A section list copied into the skill is a second home for a fact wfctl
    already ships one copy of, and #50 is that exact duplication drifting
    between two repos. The copy that falls behind does not announce itself, so
    the check is here rather than left to whoever notices the contradiction.
    """
    template = (
        _AGENTS / "configs" / "github" / ".github" / "pull_request_template.md"
    ).read_text()
    headings = {line for line in template.splitlines() if line.startswith("## ")}
    skill = (_AGENTS / "skills" / "opening-a-change" / "SKILL.md").read_text().splitlines()
    restated = sorted(h for h in headings if h in skill)

    assert restated == []
