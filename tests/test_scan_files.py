"""`/speckit.clarify` and `/speckit.analyze` write a scan file into the repository.

Both steps exist to find problems and both wrote everything they found into
`FEATURE_DIR`, which resolves outside the working tree and is gitignored under the
default `<repo>/specs`. A reviewer opening the change saw none of it, so a
thorough scan and one that never ran were the same pull request (#307).

The instruction that fixes that is prose in two command wrappers, and prose under
`wfctl/agents/` is the one thing the suite cannot otherwise see: `install-skills`
copies it, no test reads it, and a wrapper that lost the section would ship green.
So the assertions here are about the shipped bundle rather than about `wfctl/`.

The other two tests hold the claims the destination rests on — that a file under
`<arch-root>/scans/` is reachable by `wfctl arch check` and invisible to
`wfctl arch context`. Both are true today by properties of code this change does
not touch, which is exactly why they are asserted rather than assumed: nothing
would report it if either moved.
"""

from __future__ import annotations

import subprocess
from importlib.resources import files
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl import _arch
from wfctl.cli import app

runner = CliRunner()

# Resolved through `files("wfctl")` for `test_skill_cross_references`' reason:
# conftest's autouse `bundle` fixture repoints `_bundle.BUNDLE_ROOT` at a fake
# tree, and reading the real shipped one is this file's whole purpose.
_COMMANDS = Path(str(files("wfctl"))) / "agents" / "commands"

# One per review step. The step name is also the scan file's suffix, so a wrapper
# and the file it writes are named from the same word.
_REVIEW_WRAPPERS = ("clarify", "analyze")


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_each_review_wrapper_ships(step: str) -> None:
    """A dropped wrapper takes the instruction with it and nothing else notices.

    The skill it points at is not mirrored, so the wrapper is the only route in:
    `_MIRRORED_SKILLS` names neither `speckit-clarify` nor `speckit-analyze`, and
    a skill absent from both routes is reachable by nobody.
    """
    assert (_COMMANDS / f"speckit.{step}.md").exists()


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_each_review_wrapper_tells_the_step_to_write_a_scan_file(step: str) -> None:
    """The section, its destination, and the reason the destination is asked for.

    Three assertions and not one, because each fails on its own: a wrapper can
    keep the heading and lose the path, or keep both and hard-code
    `docs/architecture`, which is the default and not the truth — a repo that
    declares `arch_root` elsewhere would then have its scan files written where no
    reviewer reads them, silently, which is the defect this feature closes.
    """
    text = (_COMMANDS / f"speckit.{step}.md").read_text()

    assert "## Write the scan file" in text
    assert f"scans/<issue>-{step}.md" in text
    assert "wfctl arch-root" in text


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_each_review_wrapper_makes_the_step_commit_before_checking(step: str) -> None:
    """`arch check` refuses a file that is only staged, so the order is load-bearing.

    A wrapper that told the step to check before committing would fail on every
    run and teach the reader that the check is broken rather than that the file is
    (FR-013).

    Scoped to the section, not the file. `wfctl arch check` also appears in
    `allowed-tools`, which is frontmatter and therefore earlier than everything —
    reading the whole file makes this assertion fail on a correct wrapper.
    """
    section = (_COMMANDS / f"speckit.{step}.md").read_text().split("## Write the scan file")[1]
    commit = section.index("git commit")
    check = section.index("wfctl arch check")

    assert commit < check, "the wrapper checks before it commits"


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_each_review_wrapper_requires_the_empty_run_to_write_a_file(step: str) -> None:
    """The case #307 was filed over, and the one an instruction most easily loses.

    Told to auto-choose, an agent stops generating questions at all — so "no
    findings" is what a thorough scan over a clean spec and a scan that never ran
    both produce. A wrapper that says to write a scan file *when there is
    something to report* has re-created the defect while looking fixed.
    """
    text = (_COMMANDS / f"speckit.{step}.md").read_text()

    assert "A run that found nothing still writes the file" in text


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_each_review_wrapper_appends_a_session_rather_than_replacing(step: str) -> None:
    """Found by running the step, not by reading it.

    The instruction first said to write the file whole on every run, which reads
    as the simpler rule and is wrong for the only case that matters: this branch
    asked three questions, then re-scanned a spec that no longer had any, and
    replacing would have deleted the three answers the requirements were written
    from. A second scan finding nothing is only meaningful given what the first
    one found.

    What is still never merged is two *steps* into one file — that is the
    coordination the destination was chosen to avoid, and the level-2 record's
    `Considered` argues it.
    """
    section = (_COMMANDS / f"speckit.{step}.md").read_text().split("## Write the scan file")[1]
    # Whitespace-normalised: the prose is hard-wrapped, so a phrase that happens
    # to straddle a line break is present and unmatchable as written.
    flowed = " ".join(section.split())

    assert "## Session YYYY-MM-DD" in section
    assert "never discards an earlier session" in flowed


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_no_review_skill_carries_the_instruction(step: str) -> None:
    """`vendor-upstream-skills`: prefer layering to editing.

    Both skills are `github/spec-kit`-derived. An edit made in the `SKILL.md` is
    reverted by the next upstream pull with no conflict to notice, and the
    behaviour then regresses at a moment whose diff mentions neither step. This
    fails on the repair, not on the original mistake.
    """
    skill = Path(str(files("wfctl"))) / "agents" / "skills" / f"speckit-{step}" / "SKILL.md"

    assert "## Write the scan file" not in skill.read_text()


def test_a_scan_file_is_not_a_decision_in_force(tmp_path: Path) -> None:
    """`arch context` must keep meaning "the decisions this repo is built under".

    `load_records` globs `<root>/*.md` one level deep, which is what keeps
    `design/`, `declarations/` and `views/` out of the projection — `wfctl arch
    none`'s own help gives that as the reason declarations live in a
    subdirectory. `scans/` rides on the same property, and a future move of these
    files to the root would file every scan among the accepted records.
    """
    root = tmp_path / "docs" / "architecture"
    (root / "scans").mkdir(parents=True)
    (root / "scans" / "307-clarify.md").write_text("# Clarification scan — #307\n")
    (root / "a-decision.md").write_text(
        "---\nstatus: accepted\n---\n\n# A decision\n\n## Log\n\n- 2026-01-01  accepted  — x\n"
    )

    slugs = [record.slug for record in _arch.load_records(root)]

    assert slugs == ["a-decision"]


def test_arch_check_answers_for_a_path_under_scans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The claim the whole destination rests on: the check takes any path.

    `arch check` was built for a level-3 record and never asked whether its
    argument sits under the arch root (`cli.py`), so a scan file gets the same
    answer for free and this feature adds no wfctl code. Asserted because that is
    an absence — nothing in the command says it is deliberate, and a containment
    guard added later would silently strand every scan file.
    """
    repo = tmp_path / "r"
    repo.mkdir()
    for args in (
        ["init", "-q", "-b", "main"],
        ["config", "user.email", "t@example.com"],
        ["config", "user.name", "t"],
    ):
        subprocess.run(["git", *args], cwd=repo, check=True)
    (repo / "README.md").write_text("x\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)

    scan = repo / "docs" / "architecture" / "scans" / "307-clarify.md"
    scan.parent.mkdir(parents=True)
    scan.write_text("# Clarification scan — #307\n")
    subprocess.run(["git", "checkout", "-qb", "307-x"], cwd=repo, check=True)
    subprocess.run(["git", "add", str(scan)], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "scan"], cwd=repo, check=True)
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["arch", "check", str(scan)])

    assert result.exit_code == 0, result.output
    assert "this change adds it" in result.output
