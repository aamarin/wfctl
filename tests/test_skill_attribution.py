"""A skill taken from another project says so in the file, and the record agrees.

Six superpowers-derived skills shipped in the wheel for eleven releases with no
copyright notice (#213), because the only thing recording provenance was a table
in `vendor-upstream-skills` maintained by hand, keyed on a `license:` frontmatter
key six of the seven do not carry. Nothing could report the table was wrong.

The two checks below are a pair on purpose. The notice has to be in the file,
because `MANIFEST.in` grafts `wfctl/agents` into the wheel and that is the
artifact the obligation attaches to; the list has to be in the record, because
that is where a reader looks for which files the project does not own. Either
one alone goes stale the way the table did.
"""
from __future__ import annotations

import re
from pathlib import Path

import wfctl

# Resolved from the installed package for the same reason as
# `test_skill_frontmatter`: conftest's autouse `bundle` fixture repoints
# `_bundle.BUNDLE_ROOT` at a fixture tree, and this is about what wfctl ships.
SKILLS_ROOT = Path(wfctl.__file__).parent / "agents" / "skills"
RECORD = Path(__file__).resolve().parent.parent / "docs" / "architecture" / "vendor-upstream-skills.md"

# The `©` is part of the pattern rather than checked afterwards: a line naming a
# source but no copyright holder is not the notice MIT asks for, and treating it
# as one would let a half-written line satisfy the check.
_LINE = re.compile(r"^Derived from \[([^\]]+)\]\(https://\S+\) \([^)]*©[^)]*\)\.$")
_ROW = re.compile(r"^\| `([a-z0-9-]+)` \| `([^`]+)` \|$", re.M)


def _attributed() -> dict[str, str]:
    """Skill name → the upstream its own last line names."""
    found = {}
    for skill_md in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8").rstrip()
        match = _LINE.match(text.rsplit("\n", 1)[-1])
        if match:
            found[skill_md.parent.name] = match.group(1)
    return found


def _listed() -> dict[str, str]:
    """Skill name → the upstream the record's table names."""
    return dict(_ROW.findall(RECORD.read_text(encoding="utf-8")))


def test_every_skill_the_record_lists_carries_its_attribution_line() -> None:
    """The direction that catches a notice dropped by an edit or an upstream
    re-pull — the file ships without it and only the record still says the
    project does not own that file."""
    missing = sorted(set(_listed()) - set(_attributed()))

    assert not missing, f"listed in vendor-upstream-skills but carry no attribution line: {missing}"


def test_no_skill_claims_an_upstream_the_record_does_not_list() -> None:
    """The direction that failed for eleven releases: a derived skill arrives,
    the table is not touched, and nothing notices. A skill that has genuinely
    become the project's own drops its line and its row together, never one."""
    unlisted = sorted(set(_attributed()) - set(_listed()))

    assert not unlisted, f"carry an attribution line but vendor-upstream-skills does not list them: {unlisted}"


def test_the_file_and_the_record_name_the_same_upstream() -> None:
    """Two homes for one fact only stay honest while they agree. `i-have-adhd`
    is why this is not folded into the checks above: the record named it without
    naming `ayghri/i-have-adhd`, so it was listed, it carried a line, and the
    record was still wrong about where it came from."""
    attributed, listed = _attributed(), _listed()
    disagree = {
        name: (attributed[name], listed[name])
        for name in set(attributed) & set(listed)
        if attributed[name] != listed[name]
    }

    assert not disagree, f"file and record name different upstreams (file, record): {disagree}"
