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


def _run(shell: str, bin_dir: Path) -> list[str]:
    """Nothing is injected but a `PATH` carrying the `wfctl` stub.

    `FEATURE_DIR` has to arrive the way the skill says it does — the fence calls
    `wfctl feature-paths` and evals it. Handing the variable in directly would
    test the loop while assuming away the step that binds what the loop reads,
    which is the defect this command shipped with twice: once with the name
    never bound at all, once with it bound only in an earlier shell that no
    longer exists by the time the check runs.
    """
    # `zsh -f` skips the startup files; `sh` has none to skip and reads `-f` as
    # "no globbing", so the flag cannot simply be passed to both. Without it,
    # /etc/zprofile runs `path_helper`, which prepends the login PATH and puts
    # the real `wfctl` ahead of the stub — the fence then reports on whatever
    # repo the test happens to run in.
    argv = [shell, "-f", "-c"] if shell == "zsh" else [shell, "-c"]
    out = subprocess.run(
        [*argv, _roster_command()],
        env={"PATH": f"{bin_dir}:/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )
    return out.stdout.split()


def _fixture(feature_dir: Path) -> Path:
    """One reviewer that reported, one that wrote an empty file, one that never
    wrote at all — the last two are the cases an agent reads as a clean pass —
    plus a `wfctl` stub printing the assignment the real one prints. Returns the
    directory to put on `PATH`."""
    reviews = feature_dir / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "r1.md").write_text("BLOCKER cli.py:L1 — …\n")
    (reviews / "r2.md").write_text("")

    bin_dir = feature_dir / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "wfctl"
    stub.write_text(f"#!/bin/sh\necho \"FEATURE_DIR='{feature_dir}'\"\n")
    stub.chmod(0o755)
    return bin_dir


def test_the_roster_check_names_the_reviewers_that_did_not_report(
    tmp_path: Path,
) -> None:
    """An absent file and an empty one both have to read as MISSING.

    A reviewer that returns nothing is indistinguishable from one that found
    nothing, and in the run this skill was written from, the agent asserted the
    second. Checking the disk is what makes the two distinguishable at all, so a
    check that passes an empty report gives the assertion back its cover.
    """
    bin_dir = _fixture(tmp_path)

    assert _run("sh", bin_dir) == [
        "reported", "r1", "MISSING", "r2", "MISSING", "r3",
    ]


def test_the_roster_check_survives_zsh(tmp_path: Path) -> None:
    """Same reason as `test_skill_commands`: the shell an agent runs this in on
    macOS is zsh, CI's is not, and the first bug in the sibling command was zsh
    treating a construct differently. Skipped where zsh is absent."""
    if not shutil.which("zsh"):
        return
    bin_dir = _fixture(tmp_path)

    assert _run("zsh", bin_dir) == _run("sh", bin_dir)


def test_the_panel_skill_names_every_skill_it_layers_over() -> None:
    """The whole layering is carried by these three references and nothing else.

    Drop one and the panel quietly becomes a second account of what that skill
    owns — the reviewer hand-off, the rubric, or verify-before-implementing —
    which is the duplication `knowledge-placement` and #50 are about. Not
    `vendor-upstream-skills`: it lists two of the three as superpowers-derived
    and not the third, so it explains why two of them are layered over rather
    than edited — not why the panel defers to all three.
    """
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
