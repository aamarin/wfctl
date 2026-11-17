"""The four skills that teach drawing all link the one drawing style file.

The style is written once, in `design-levels/references/drawing-style.md`, and
the other skills link to it rather than keep a copy
(`740-drawing-style-one-file`). A relative link that points nowhere fails
silently: the agent follows it, finds nothing, and draws without the style,
which is the drift the one file exists to prevent.
"""
import re
from importlib.resources import files
from pathlib import Path

import pytest


# Through `files("wfctl")` rather than `install.BUNDLE_ROOT`, since conftest's
# autouse `bundle` fixture repoints that at a fake tree.
_SKILLS = Path(str(files("wfctl"))) / "agents" / "skills"

_STYLE = _SKILLS / "design-levels" / "references" / "drawing-style.md"

_LINKING = [
    _SKILLS / "design-levels" / "SKILL.md",
    _SKILLS / "architecture-decisions" / "SKILL.md",
    _SKILLS / "software-design-decisions" / "SKILL.md",
    _SKILLS / "model-the-domain" / "references" / "visual-language.md",
]

_LINK = re.compile(r"\]\(([^)\s]*drawing-style\.md)(?:#[^)]*)?\)")


def test_the_style_file_ships() -> None:
    assert _STYLE.is_file()


@pytest.mark.parametrize("source", _LINKING, ids=lambda p: p.parent.name if p.name == "SKILL.md" else p.name)
def test_each_drawing_skill_links_the_style_file_at_a_path_that_exists(source: Path) -> None:
    """A file with no link at all fails too, since a link deleted in an edit
    leaves the skill teaching drawing with no style, the same as a broken one."""
    targets = _LINK.findall(source.read_text())
    assert targets, f"{source.relative_to(_SKILLS)} has no link to drawing-style.md"
    for target in targets:
        resolved = (source.parent / target).resolve()
        assert resolved == _STYLE.resolve(), (
            f"{source.relative_to(_SKILLS)} links {target}, which resolves to {resolved}"
        )
