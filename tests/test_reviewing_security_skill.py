"""`reviewing-security` overrides parts of two vendored files it cannot edit.

The skill names those parts by their text: the prompt's git section headings,
the line that forbids bash and writes, the false-positive block, the two
exclusions it scopes, the confidence cut, and the hardening skill's headings and
broken checklist citations. Both files are re-pulled from upstream unedited, so
a re-pull that rewords one of them leaves the skill overriding text that is no
longer there, and the reviewer then follows upstream's new wording with nothing
above it. Both halves are shipped files, so the mismatch is checkable
(`a-rule-is-expressed-as-a-check`).
"""
import re
from importlib.resources import files
from pathlib import Path

import pytest

# Resolved through `files("wfctl")` because conftest's autouse `bundle` fixture
# repoints `_bundle.BUNDLE_ROOT` at a fake tree, and this is about the real one.
_SKILLS = Path(str(files("wfctl"))) / "agents" / "skills"
_SKILL = _SKILLS / "reviewing-security" / "SKILL.md"
_PROMPT = _SKILLS / "reviewing-security" / "references" / "security-review.md"
_HARDENING = _SKILLS / "security-and-hardening" / "SKILL.md"
_PATTERNS = _SKILLS / "security-and-hardening" / "references" / "hardening-patterns.md"


@pytest.mark.parametrize("vendored, anchor", [
    (_PROMPT, "GIT STATUS"),
    (_PROMPT, "DIFF CONTENT"),
    (_PROMPT, "origin/HEAD"),
    (_PROMPT, "FALSE POSITIVE FILTERING"),
    (_PROMPT, "Do not use the bash tool or write to any files"),
    (_PROMPT, "allowed-tools"),
    (_PROMPT, "less than 8"),
    (_PROMPT, "Your final reply must contain the markdown report and nothing else."),
    (_PROMPT, "14. Including user-controlled content in AI system prompts is not a vulnerability."),
    (_PROMPT, "16. Insecure documentation."),
    (_HARDENING, "## Red Flags"),
    (_HARDENING, "## Review Checklist"),
    (_HARDENING, "`../../references/security-checklist.md`"),
    (_PATTERNS, "`../../../references/security-checklist.md"),
], ids=lambda v: v.name if isinstance(v, Path) else v)
def test_the_vendored_files_still_carry_the_text_the_skill_overrides(vendored: Path, anchor: str) -> None:
    """Each anchor is text the skill quotes, overrides, or sends a reviewer to
    by name. One that has gone from its file is an override pointing at
    nothing."""
    assert anchor in vendored.read_text(encoding="utf-8"), (
        f"{vendored.name} no longer says {anchor!r}; re-read reviewing-security/SKILL.md against it"
    )


def test_every_path_the_skill_sends_a_reviewer_to_ships() -> None:
    """A reviewer reads the two reviews and the checklist by the paths this
    skill gives, relative to its own folder. A read of a path that is not there
    stops nothing, so a renamed reference would cost the review a whole half
    silently. The pattern allows one leading `../`, so the broken `../../` and
    `../../../` citations the skill names in order to correct them never match."""
    cited = set(re.findall(r"`((?:\.\./)?[a-z0-9-]+/[A-Za-z0-9./-]+\.md)`", _SKILL.read_text(encoding="utf-8")))
    missing = sorted(p for p in cited if not (_SKILL.parent / p).resolve().is_file())

    assert cited, "found no paths in reviewing-security/SKILL.md; the pattern has drifted"
    assert not missing, f"reviewing-security/SKILL.md sends a reviewer to paths that don't ship: {missing}"
