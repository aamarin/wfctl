"""The review-panel skill's roster check runs, and its layering stays intact.

The roster check is the only thing standing between a reviewer that silently
returned nothing and a pass recorded as clean — the failure #133 was filed for.
It is a shell command inside a skill, so it ships whether or not it works;
`test_skill_commands` exists because that same shape was wrong twice in
`opening-a-change`. The rest of this file guards the layering: the skill's value
is that it orchestrates three skills it does not own, and both halves of that —
naming them, and not restating their contents — fail silently.
"""
import re
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path

_AGENTS = Path(str(files("wfctl"))) / "agents"
_SKILL = _AGENTS / "skills" / "fanning-out-code-review" / "SKILL.md"

_FENCE = re.compile(r"```bash\n(.*?)```", re.DOTALL)
_REFERENCE = re.compile(r"\.agents/skills/([a-z0-9][a-z0-9-]*)")


def _roster_command() -> str:
    """The one fenced block that checks the roster. Keyed on content rather than
    position: Step 1's `wfctl feature-paths` is also a bash fence, and reordering
    the steps must not silently retarget this test at it."""
    blocks = [b for b in _FENCE.findall(_SKILL.read_text()) if "MISSING" in b]
    assert len(blocks) == 1, f"expected one roster fence, found {len(blocks)}"
    return blocks[0]


def _run(shell: str, feature_dir: Path) -> list[str]:
    """`FEATURE_DIR` is what `wfctl feature-paths` prints and the only variable
    Step 1 puts in the agent's hands. Injecting `REVIEWS` instead would leave the
    fence's own derivation of it untested — which is how the first version of
    this command shipped reading a variable nothing ever set."""
    out = subprocess.run(
        [shell, "-c", _roster_command()],
        env={"FEATURE_DIR": str(feature_dir), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )
    return out.stdout.split()


def _fixture(feature_dir: Path) -> Path:
    """One reviewer that reported, one that wrote an empty file, one that never
    wrote at all. The last two are the cases an agent reads as a clean pass."""
    reviews = feature_dir / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "r1.md").write_text("BLOCKER cli.py:L1 — …\n")
    (reviews / "r2.md").write_text("")
    return feature_dir


def test_the_roster_check_names_the_reviewers_that_did_not_report(
    tmp_path: Path,
) -> None:
    """An absent file and an empty one both have to read as MISSING.

    A reviewer that returns nothing is indistinguishable from one that found
    nothing, and in the run this skill was written from, the agent asserted the
    second. Checking the disk is what makes the two distinguishable at all, so a
    check that passes an empty report gives the assertion back its cover.
    """
    _fixture(tmp_path)

    assert _run("sh", tmp_path) == [
        "reported", "r1", "MISSING", "r2", "MISSING", "r3",
    ]


def test_the_roster_check_survives_zsh(tmp_path: Path) -> None:
    """Same reason as `test_skill_commands`: the shell an agent runs this in on
    macOS is zsh, CI's is not, and the first bug in the sibling command was zsh
    treating a construct differently. Skipped where zsh is absent."""
    if not shutil.which("zsh"):
        return
    _fixture(tmp_path)

    assert _run("zsh", tmp_path) == _run("sh", tmp_path)


def test_the_panel_skill_names_every_skill_it_layers_over() -> None:
    """`vendor-upstream-skills` forbids editing the three skills this one
    orchestrates, so the whole layering is carried by these references. Drop one
    and the panel silently becomes a competing account of it — the reviewer
    hand-off, the rubric, or verify-before-implementing — which is the
    duplication the record exists to prevent."""
    named = set(_REFERENCE.findall(_SKILL.read_text()))
    for skill in ("requesting-code-review", "code-review", "receiving-code-review"):
        assert skill in named, skill


def test_the_panel_skill_does_not_restate_the_rubric() -> None:
    """The reviewers run `code-review`; a copy of its passes here is a second
    home for a fact wfctl ships one copy of (#50), and it would contradict
    `code-review`'s own "one review instead of four overlapping ones" the moment
    either file moved. Derived from `code-review`'s pass headings rather than a
    hardcoded list, so a renamed pass keeps the check honest."""
    rubric = (_AGENTS / "skills" / "code-review" / "SKILL.md").read_text()
    passes = re.findall(r"^\*\*\d\. ([A-Za-z][A-Za-z &-]*)\*\*", rubric, re.MULTILINE)
    assert len(passes) == 6, passes

    skill = _SKILL.read_text()
    restated = sorted(p for p in passes if f"**{p}" in skill)

    assert restated == []


def test_the_panel_skill_is_model_invocable() -> None:
    """The trigger is a change about to be merged, which is a moment nobody
    types a command (#124). Membership in `_MIRRORED_SKILLS` is what puts the
    skill on Claude's native discovery path; without it the command wrapper is
    the only way in, which is the failure being designed out."""
    from wfctl import _arch
    from wfctl.cli import _MIRRORED_SKILLS

    assert "fanning-out-code-review" in _MIRRORED_SKILLS
    # Column-zero keys only, via the same parser the frontmatter test uses:
    # the prose explaining why the key is absent names it, and a substring
    # search would read that explanation as the key it forbids.
    assert "disable-model-invocation" not in _arch._frontmatter(_SKILL.read_text())
