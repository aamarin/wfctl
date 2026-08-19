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
