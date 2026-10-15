"""The shipped skill bundle conforms to the Agent Skills frontmatter spec.

Offline on purpose. The upstream reference validator is the authority, but
shelling out to it would put the network inside `uv run pytest`; pinning the
allowed key set here catches the same regression at the same moment. Adopting
the real validator is tracked as #60.
"""

from pathlib import Path

import yaml

import wfctl
from wfctl import _arch

# The Agent Skills spec's top-level frontmatter keys. A key outside this set
# ships clean and only fails when someone runs an external validator by hand —
# which is the silent failure this test exists to convert into a red run.
ALLOWED_KEYS = {
    "allowed-tools", "compatibility", "description", "license", "metadata", "name",
}

# Resolved from the installed package rather than `BUNDLE_ROOT`: the autouse
# `bundle` fixture repoints that at a fixture tree, and this test is about the
# skills wfctl actually ships.
SKILLS_ROOT = Path(wfctl.__file__).parent / "agents" / "skills"
AGENTS_ROOT = SKILLS_ROOT.parent


def test_every_shipped_skill_declares_only_spec_keys() -> None:
    """A non-spec key in any shipped skill fails here rather than in someone
    else's validator run.

    Reuses `_arch._frontmatter` for the scan, which already gets the two rules
    that matter right: keys are column-zero only — seven `speckit-*` skills carry
    `metadata:` with nested children — and the scan stops at the closing `---`
    rather than reading `name:` out of a body paragraph.

    Names the offenders in the assertion rather than counting them: a bare count
    tells you the bundle regressed without telling you where.
    """
    offenders = {}
    for skill_dir in sorted(SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        extra = sorted(set(_arch._frontmatter(skill_md.read_text())) - ALLOWED_KEYS)
        if extra:
            offenders[skill_dir.name] = extra

    assert offenders == {}


def test_every_shipped_frontmatter_parses_as_yaml() -> None:
    """A skill or command whose frontmatter is not valid YAML still installs,
    and Claude Code then loads it without its description. `model-the-domain`
    shipped that way, with an apostrophe inside a single-quoted description,
    and was listed only as "Model the domain", so nothing could select it.

    `_arch._frontmatter` reads keys line by line and never parses a value, so
    the test above passes on a file like that. This one parses each block with
    a real YAML reader. The reader is a dev dependency only, because wfctl
    itself never parses this YAML.

    Every block has to parse, record templates included. Only a skill or a
    command needs a description, since those are the files an agent loads by
    it.
    """
    offenders = {}
    for md in sorted(AGENTS_ROOT.rglob("*.md")):
        text = md.read_text()
        if not text.startswith("---\n"):
            continue
        block = text[len("---\n"):].split("\n---\n", 1)[0]
        rel = md.relative_to(AGENTS_ROOT)
        try:
            parsed = yaml.safe_load(block)
        except yaml.YAMLError as exc:
            offenders[str(rel)] = str(exc).splitlines()[0]
            continue
        loaded_by_description = md.name == "SKILL.md" or rel.parts[0] == "commands"
        if loaded_by_description and not (
            isinstance(parsed, dict) and isinstance(parsed.get("description"), str)
        ):
            offenders[str(rel)] = "no description string"

    assert offenders == {}
