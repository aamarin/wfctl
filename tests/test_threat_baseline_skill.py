"""`threat-baseline` builds the file the `threat-baseline` pass checks for.

The pass reads only whether `THREAT_MODEL.md` is committed at the repository
root, so everything else the baseline needs is instruction text in the skill:
which upstream mode runs, where the helper is, what wfctl adds to upstream's
file, and that the exception is the user's. These tests pin those lines,
because a skill that drops one still ships and still installs.
"""
from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

_AGENTS = Path(str(files("wfctl"))) / "agents"
_SKILL = _AGENTS / "skills" / "threat-baseline" / "SKILL.md"
_WRAPPER = _AGENTS / "commands" / "threat-baseline.md"
_EXCEPTION = "wfctl step none brainstorm.threat-baseline"


def _body(path: Path) -> str:
    """The file after its frontmatter."""
    return path.read_text().split("\n---\n", 1)[1]


def test_the_opening_says_upstream_does_the_work() -> None:
    """A reader looking for how the threat model is built has to read both
    skills, and the first paragraph is where they learn that (FR-006)."""
    opening = _body(_SKILL).strip().split("\n\n")[1]

    assert "`threat-model`" in opening
    assert "upstream" in opening.lower()


def test_the_mode_follows_auto_approve() -> None:
    """Attended, the user answers upstream's interview. Unattended, nobody is
    there to answer it, so the agent runs the bootstrap and walks the four
    questions itself (FR-005, research R1)."""
    body = _body(_SKILL)

    assert "wfctl status --json" in body
    assert "`auto_approve`" in body
    assert "bootstrap-then-interview ." in body
    assert "bootstrap ." in body
    for question in (
        "What are we working on?",
        "What can go wrong?",
        "What are we going to do about it?",
        "Did we do a good job?",
    ):
        assert question in body, question


def test_upstreams_skill_is_read_as_a_file_not_invoked() -> None:
    """Invoking `/threat-model` by name would need it mirrored, and a mirrored
    copy turns on its `Bash(git:*)` and `Bash(gh api:*)` grants. Reading the
    file grants nothing (#818 security review)."""
    body = _body(_SKILL)

    assert ".agents/skills/threat-model/SKILL.md" in body
    assert "/threat-model " not in body


def test_the_helper_is_found_beside_the_loaded_skill() -> None:
    """Upstream names `.claude/skills/_lib/checkpoint.py`, which exists only on
    Claude's layer. Every other agent finds the helper in the `_lib` folder
    beside the skill it loaded, without an edit to upstream (FR-005a)."""
    body = _body(_SKILL)

    assert ".claude/skills/_lib/checkpoint.py" in body
    assert "/../_lib/checkpoint.py" in body


def test_the_rejected_fixes_section_follows_upstreams_eight() -> None:
    """Upstream tells consumers to find sections by heading and to tolerate
    extras at the end, so wfctl's section goes ninth (FR-007)."""
    body = _body(_SKILL)

    assert "## 8. Recommended mitigations" in body
    assert "## 9. Rejected fixes" in body


def test_the_skill_commits_the_baseline_and_nothing_else() -> None:
    """The pass reads done only on a commit, so a run that writes the file and
    stops is sent back to a bootstrap of several minutes. The pathspec keeps
    anything else staged out of the commit (FR-007a)."""
    body = _body(_SKILL)

    assert "git add THREAT_MODEL.md" in body
    assert re.search(r"git commit -m \"[^\"]+\" -- THREAT_MODEL\.md", body)


def test_an_existing_record_section_is_reread_against_the_baseline() -> None:
    """A `## Threat model` section written before the baseline assumed what the
    rest of the system exposes. Once the map exists, the section is checked
    against it (FR-015a)."""
    body = _body(_SKILL)

    assert "## Threat model" in body
    assert "git grep -l '^## Threat model'" in body


def test_the_skill_and_the_wrapper_leave_the_exception_to_the_user() -> None:
    """`step none` has no check on who runs it, so the instruction and the
    missing grant keep the answer with the user (FR-007b)."""
    for path in (_SKILL, _WRAPPER):
        text = _body(path)
        assert _EXCEPTION in text, path.name
        assert "the user's" in text, path.name


def _grants(path: Path) -> list[str]:
    """Every `Bash` grant in a file's `allowed-tools`, in either form a shipped
    file uses: a space-separated string or upstream's YAML list."""
    text = path.read_text()
    if not text.startswith("---\n"):
        return []
    front = text.split("\n---\n", 1)[0]
    block = re.search(r"^allowed-tools:(.*?)(?=^\S|\Z)", front, re.S | re.M)
    if not block:
        return []
    grants = re.findall(r"Bash\(([^)]*)\)", block.group(1))
    if re.search(r"(^|[\s'\"-])Bash(?=$|[\s'\"])", block.group(1), re.M):
        grants.append("*")
    return grants


def _covers(grant: str, command: str) -> bool:
    """Whether Claude Code's prefix rule `grant` would approve `command`."""
    if grant.endswith(":*"):
        grant = grant[:-2] + "*"
    pattern = ".*".join(re.escape(part) for part in grant.split("*"))
    return re.fullmatch(pattern, command) is not None


def test_no_shipped_grant_covers_the_users_exception() -> None:
    """A grant broad enough to approve `step none` on this pass lets an agent
    declare its own baseline unnecessary without a prompt. The sibling grant
    in `speckit-brainstorm` names `brainstorm.software-design` and stays
    allowed (FR-007b, PR-014)."""
    command = f'{_EXCEPTION} --reason "kept elsewhere"'
    files_ = sorted((_AGENTS / "skills").glob("*/SKILL.md")) + sorted(
        (_AGENTS / "commands").glob("*.md")
    )
    covering = {
        str(path.relative_to(_AGENTS)): grant
        for path in files_
        for grant in _grants(path)
        if _covers(grant, command)
    }

    assert covering == {}


_OUTWARD = (
    "git push origin main",
    "git -c alias.x='!sh -c id' x",
    "gh api -X POST repos/o/r/issues/1/comments -f body=x",
    "gh issue close 1",
    # `-O` opens the matches in the named program, so a bare `git grep*` grant
    # runs any shell command (#818 security review, run 002).
    "git grep -O'sh -c id' x",
)


def test_no_grant_claude_honors_approves_an_outward_command() -> None:
    """Claude Code honors `allowed-tools` on a skill under `.claude/skills/` and on
    a command. Upstream's `threat-model` grants `Bash(git:*)` and
    `Bash(gh api:*)`, which approve a push, a git alias running any shell
    command, and any GitHub write. Mirroring it would have run those with no
    prompt while the skill read commit text anyone can write (#818 security
    review, `THREAT_MODEL.md` T10). A grant in `.agents/skills/` alone is
    inert, so only what reaches Claude is checked."""
    from wfctl.cli import _MIRRORED_SKILLS

    files_ = [
        _AGENTS / "skills" / name / "SKILL.md"
        for name in sorted(_MIRRORED_SKILLS)
        if (_AGENTS / "skills" / name / "SKILL.md").is_file()
    ] + sorted((_AGENTS / "commands").glob("*.md"))
    covering = {
        (str(path.relative_to(_AGENTS)), command): grant
        for path in files_
        for grant in _grants(path)
        for command in _OUTWARD
        if _covers(grant, command)
    }

    assert covering == {}


def test_the_outward_check_recognizes_upstreams_grants() -> None:
    """The check above passes trivially if `_covers` misses upstream's form, so
    this pins it against the two grants that made the mirror unsafe."""
    upstream = _grants(_AGENTS / "skills" / "threat-model" / "SKILL.md")

    assert "git:*" in upstream and "gh api:*" in upstream
    assert _covers("git:*", _OUTWARD[0])
    assert _covers("git:*", _OUTWARD[1])
    assert _covers("gh api:*", _OUTWARD[2])
    assert not _covers("git log*", _OUTWARD[0])
    assert _covers("git grep*", _OUTWARD[4])


def test_the_skill_grants_only_reading_and_searching() -> None:
    """An unprompted `Write`, `Edit`, or checkpoint `append` can put
    `core.fsmonitor` into `.git/config`, and every granted command that runs
    git (`git add`, `wfctl status`, `wfctl arch-root`) then runs the program it
    names with no prompt. The run reads commit text anyone can write, so the
    skill grants nothing that writes or runs (#818 code review, run 002)."""
    front = _SKILL.read_text().split("\n---\n", 1)[0]
    line = re.search(r"^allowed-tools:(.*)$", front, re.M)

    assert line is not None
    assert line.group(1).split() == ["Read", "Glob", "Grep"]


def test_the_grant_check_recognizes_a_broad_grant() -> None:
    """The check above passes trivially if `_covers` never matches, so this
    pins it against the grants FR-007b names."""
    command = f'{_EXCEPTION} --reason "x"'

    assert _covers("wfctl *", command)
    assert _covers("wfctl step none *", command)
    assert _covers("wfctl:*", command)
    assert not _covers("wfctl step none brainstorm.software-design *", command)
    assert not _covers("wfctl status*", command)
