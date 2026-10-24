"""`reviewing-security` overrides parts of a vendored prompt it cannot edit.

The skill names those parts by their text: the git section's headings, the line
that forbids bash and writes, the false-positive block, the confidence cut. The
prompt is re-pulled from upstream unedited, so a re-pull that rewords one of
them leaves the skill overriding text that is no longer there, and the reviewer
then follows upstream's new wording with nothing above it. Both halves are
shipped files, so the mismatch is checkable (`a-rule-is-expressed-as-a-check`).
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


@pytest.mark.parametrize("anchor", [
    "GIT STATUS",
    "DIFF CONTENT",
    "origin/HEAD",
    "FALSE POSITIVE FILTERING",
    "Do not use the bash tool or write to any files",
    "allowed-tools",
    "less than 8",
    "Your final reply must contain the markdown report and nothing else.",
])
def test_the_prompt_still_carries_the_text_the_skill_overrides(anchor: str) -> None:
    """Each anchor is text the skill quotes or overrides by name. One that has
    gone from the prompt is an override pointing at nothing."""
    assert anchor in _PROMPT.read_text(encoding="utf-8"), (
        f"{_PROMPT.name} no longer says {anchor!r}; re-read reviewing-security/SKILL.md against it"
    )


def test_every_path_the_skill_sends_a_reviewer_to_ships() -> None:
    """A reviewer reads the two reviews and the checklist by the paths this
    skill gives, relative to its own folder. A read of a path that is not there
    stops nothing, so a renamed reference would cost the review a whole half
    silently. The `../../references/` path is named in order to say it is wrong,
    and is left out."""
    cited = set(re.findall(r"`((?:\.\./)?[a-z0-9-]+/[A-Za-z0-9./-]+\.md)`", _SKILL.read_text(encoding="utf-8")))
    cited = {p for p in cited if not p.startswith("../../")}
    missing = sorted(p for p in cited if not (_SKILL.parent / p).resolve().is_file())

    assert cited, "found no paths in reviewing-security/SKILL.md; the pattern has drifted"
    assert not missing, f"reviewing-security/SKILL.md sends a reviewer to paths that don't ship: {missing}"
