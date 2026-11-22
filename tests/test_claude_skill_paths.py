"""Every `.claude/skills/<name>` path a shipped file names is one wfctl mirrors."""
from __future__ import annotations

import re
from pathlib import Path

import wfctl
from wfctl.cli import _MIRRORED_SKILLS

_AGENTS = Path(wfctl.__file__).parent / "agents"
_CLAUDE_SKILL_PATH = re.compile(r"\.claude/skills/([A-Za-z0-9_.-]+)")


def _named_paths() -> dict[str, set[str]]:
    """Each first segment after `.claude/skills/`, with the files that name it."""
    named: dict[str, set[str]] = {}
    for path in sorted(_AGENTS.rglob("*")):
        if not path.is_file() or path.suffix not in {".md", ".py", ".sh"}:
            continue
        for match in _CLAUDE_SKILL_PATH.finditer(path.read_text(errors="replace")):
            named.setdefault(match.group(1), set()).add(str(path.relative_to(_AGENTS)))
    return named


def test_every_claude_skill_path_a_shipped_file_names_is_mirrored() -> None:
    """A skill that runs a file by its `.claude/skills/` path needs that file mirrored.

    Upstream's `threat-model` calls `python3 .claude/skills/_lib/checkpoint.py`.
    `.agents/skills/` gets every skill, but `.claude/skills/` gets only the names
    in `_MIRRORED_SKILLS`. A name missing from the set leaves the call failing
    on a missing file, and the install still reports success. Reads the
    installed package rather than `BUNDLE_ROOT`, since the autouse `bundle`
    fixture points that at a tree holding none of these files.
    """
    named = _named_paths()
    assert named, "no shipped file names a .claude/skills/ path, so this test checks nothing"

    unmirrored = {
        name: sorted(files) for name, files in named.items()
        if name not in _MIRRORED_SKILLS | _READ_FROM_AGENTS
        or not (_AGENTS / "skills" / name).is_dir()
    }

    assert unmirrored == {}


# Upstream's `threat-model` names its own files by `.claude/skills/threat-model/`,
# and wfctl keeps it out of the mirror because its grants are too broad for
# Claude to honor. `threat-baseline` tells the agent to read those files from
# `.agents/skills/threat-model/` instead, and the test below holds it to that.
_READ_FROM_AGENTS = frozenset({"threat-model"})


def test_a_skill_kept_out_of_the_mirror_is_redirected_to_agents() -> None:
    """The exemption above is safe only while some shipped skill sends the agent
    to `.agents/skills/<name>/`. Without that, the paths upstream names lead
    nowhere on Claude and the install still reports success."""
    baseline = (_AGENTS / "skills" / "threat-baseline" / "SKILL.md").read_text()

    for name in _READ_FROM_AGENTS:
        assert name not in _MIRRORED_SKILLS, name
        assert f".agents/skills/{name}/" in baseline, name
