"""The shipped skill bundle conforms to the Agent Skills frontmatter spec.

Offline on purpose. The upstream reference validator is the authority, but
shelling out to it would put the network inside `uv run pytest`; pinning the
allowed key set here catches the same regression at the same moment. Adopting
the real validator is tracked as #60.
"""

from pathlib import Path

import wfctl

# The Agent Skills spec's top-level frontmatter keys. A key outside this set
# ships clean and only fails when someone runs an external validator by hand —
# which is the silent failure this test exists to convert into a red run.
ALLOWED_KEYS = frozenset(
    {"allowed-tools", "compatibility", "description", "license", "metadata", "name"}
)

# `vendor-upstream-skills` forbids editing a vendored file, and this one carries
# `disable-model-invocation`. Exempted by name rather than by a pattern, so a
# second non-conforming skill cannot arrive under cover of the same exemption.
VENDORED_EXEMPTIONS = frozenset({"i-have-adhd"})

# Resolved from the installed package rather than `BUNDLE_ROOT`: the autouse
# `bundle` fixture repoints that at a fixture tree, and this test is about the
# skills wfctl actually ships.
SKILLS_ROOT = Path(wfctl.__file__).parent / "agents" / "skills"


def _top_level_keys(skill_md: Path) -> list[str]:
    """Frontmatter keys at column zero, up to the closing delimiter.

    Both halves are load-bearing. Seven `speckit-*` skills carry `metadata:` with
    nested `author:` and `source:` children, so a scan that counted indented
    lines would report `author` as a top-level key and red out a quarter of the
    bundle. And a scan that ran past the closing `---` would read prose — every
    `name:` written in a body paragraph — as frontmatter.
    """
    lines = skill_md.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    keys = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line.strip() or line[:1].isspace() or line.lstrip().startswith("#"):
            continue
        name, sep, _ = line.partition(":")
        if sep:
            keys.append(name.strip())
    return keys


def test_every_shipped_skill_declares_only_spec_keys() -> None:
    """A non-spec key in any shipped skill fails here rather than in someone
    else's validator run.

    Named the offenders in the assertion rather than counting them: a bare count
    tells you the bundle regressed without telling you where.
    """
    offenders = {}
    for skill_dir in sorted(SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name in VENDORED_EXEMPTIONS:
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        extra = sorted(set(_top_level_keys(skill_md)) - ALLOWED_KEYS)
        if extra:
            offenders[skill_dir.name] = extra

    assert offenders == {}


def test_the_bundle_is_actually_being_scanned() -> None:
    """Guards the two ways this file could pass while checking nothing: a
    `SKILLS_ROOT` that resolves somewhere empty, and a parser that returns no
    keys at all."""
    skill_dirs = [d for d in SKILLS_ROOT.iterdir() if d.is_dir()]

    assert len(skill_dirs) > 20
    assert "name" in _top_level_keys(SKILLS_ROOT / "design-levels" / "SKILL.md")
