"""The shipped skill bundle conforms to the Agent Skills frontmatter spec.

Offline on purpose. The upstream reference validator is the authority, but
shelling out to it would put the network inside `uv run pytest`; pinning the
allowed key set here catches the same regression at the same moment. Adopting
the real validator is tracked as #60.
"""

from pathlib import Path

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


def test_every_shipped_skill_declares_only_spec_keys() -> None:
    """A non-spec key in any shipped skill fails here rather than in someone
    else's validator run.

    `i-have-adhd` is exempt: it is vendored, it carries upstream's
    `disable-model-invocation`, and `vendor-upstream-skills` forbids editing it.
    Exempt by name rather than by a pattern, so a second non-conforming skill
    cannot arrive under cover of the same exemption.

    Reuses `_arch._frontmatter` for the scan, which already gets the two rules
    that matter right: keys are column-zero only — seven `speckit-*` skills carry
    `metadata:` with nested children — and the scan stops at the closing `---`
    rather than reading `name:` out of a body paragraph.

    Names the offenders in the assertion rather than counting them: a bare count
    tells you the bundle regressed without telling you where.
    """
    offenders = {}
    for skill_dir in sorted(SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name == "i-have-adhd":
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        extra = sorted(set(_arch._frontmatter(skill_md.read_text())) - ALLOWED_KEYS)
        if extra:
            offenders[skill_dir.name] = extra

    assert offenders == {}
