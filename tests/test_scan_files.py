"""`/speckit.clarify` and `/speckit.analyze` write a scan file into the repository.

Both steps exist to find problems and both wrote everything they found into
`FEATURE_DIR`, which resolves outside the working tree and is gitignored under the
default `<repo>/specs`. A reviewer opening the change saw none of it, so a
thorough scan and one that never ran were the same pull request (#307).

The instruction that fixes that is prose under `wfctl/agents/`, which is the one
thing the suite cannot otherwise see: `install-skills` copies it, no test reads
it, and a wrapper that lost a rule would ship green. So most assertions here are
about the shipped bundle rather than about `wfctl/`.

The exception is `scans_are_not_records`, which holds the one behaviour change the
destination forced. Three panel reviewers independently found that two callers
read the arch root recursively and had begun counting scan files as architecture
records — the record's own `Consequences` had enumerated the readers and missed
these two.
"""

from __future__ import annotations

import subprocess
from importlib.resources import files
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl import _arch
from wfctl._paths import SCANS_DIR, records_on_this_branch, touched_on_this_branch
from wfctl.cli import app

runner = CliRunner()

# Resolved through `files("wfctl")` for `test_skill_cross_references`' reason:
# conftest's autouse `bundle` fixture repoints `_bundle.BUNDLE_ROOT` at a fake
# tree, and reading the real shipped one is this file's whole purpose.
_AGENTS = Path(str(files("wfctl"))) / "agents"

# One per review step. The step name is also the scan file's suffix, so a wrapper
# and the file it writes are named from the same word.
_REVIEW_WRAPPERS = ("clarify", "analyze")

# What the shared discipline lives in, and what each wrapper must still carry
# itself. The split is the design: a rule in the skill is written once, and a rule
# about what *this* step scanned cannot be.
_SHARED = _AGENTS / "skills" / "writing-a-scan-file" / "SKILL.md"


def _wrapper(step: str) -> str:
    return (_AGENTS / "commands" / f"speckit.{step}.md").read_text()


def _section(step: str) -> str:
    return _wrapper(step).split("## Write the scan file")[1]


def _repo(root: Path) -> Path:
    """A git repo with one commit on `main`, so a trunk exists to compare to.

    Deliberately not imported from `test_arch_check`, which ships the same
    helper: a test module importing another test module couples two files whose
    only relation is that both need a repo, and the next edit to that one has to
    know about this one. Six lines is the cheaper side of that trade.
    """
    root.mkdir(parents=True, exist_ok=True)
    for args in (
        ["init", "-q", "-b", "main"],
        ["config", "user.email", "t@example.com"],
        ["config", "user.name", "t"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)
    (root / "README.md").write_text("x\n")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
    return root


# --- the shipped instruction -------------------------------------------------


def test_the_shared_scan_skill_ships() -> None:
    """Both wrappers point at it, and a pointer to a missing skill fails silently.

    That is `test_skill_cross_references`' whole subject one directory over; this
    asserts the specific one the feature cannot work without.
    """
    assert _SHARED.exists()


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_each_review_wrapper_points_at_the_shared_scan_skill(step: str) -> None:
    """Half the instruction lives in one file so it cannot drift between two.

    It drifted before this split existed: the same paste went into both wrappers
    and both lost the `git commit` pathspec together, which a panel found and no
    test could have.
    """
    assert ".agents/skills/writing-a-scan-file/SKILL.md" in _section(step)


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_each_review_wrapper_names_its_own_destination(step: str) -> None:
    """The one thing the shared skill cannot say for either step.

    Hard-coding `docs/architecture` instead of asking `wfctl arch-root` is the
    silent failure this pair guards: a repo that declares the root elsewhere would
    get its scan files written where no reviewer reads them, with no error.
    """
    section = _section(step)

    assert f"scans/<issue>-{step}.md" in section
    assert "arch-root" in section


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_each_review_wrapper_carries_its_own_coverage_rows(step: str) -> None:
    """The coverage table is the file's body, and its rows are step-specific.

    A wrapper that inherited generic rows would produce a table nobody could check
    against what the step actually scans — which is the table's only value.
    """
    section = _section(step)
    first_row = "Functional Scope & Behavior" if step == "clarify" else "A · Duplication"

    assert first_row in section


def test_the_shared_skill_requires_the_empty_run_to_write_a_section() -> None:
    """The case #307 was filed over, and the one an instruction most easily loses.

    Told to auto-choose, an agent stops generating questions at all — so "no
    findings" is what a thorough scan over a clean spec and a scan that never ran
    both produce. An instruction that says to write a scan file *when there is
    something to report* has re-created the defect while looking fixed.
    """
    assert "A run that found nothing still writes the section" in _SHARED.read_text()


def test_the_shared_skill_scopes_the_commit_to_the_scan_file() -> None:
    """A bare `git commit` writes the whole index, mid-pipeline, where staged code is normal.

    The first version of this instruction had the pathspec on `add` and not on
    `commit`, so an author's staged work would land in a commit whose subject says
    it holds a scan file. This repo had already met and written down that exact
    failure in `software-design-decisions/SKILL.md`; the new block was that block
    with the pathspec dropped.
    """
    line = next(
        ln for ln in _SHARED.read_text().splitlines() if ln.strip().startswith("git commit")
    )

    assert " -- " in line, f"commit is unscoped: {line.strip()}"


def test_the_shared_skill_commits_before_it_checks() -> None:
    """`arch check` refuses a file that is only staged, so the order is load-bearing.

    Checking first would fail on every run and teach the reader that the check is
    broken rather than that the file is.
    """
    text = _SHARED.read_text()

    assert text.index("git commit") < text.index("wfctl arch check")


def test_the_shared_skill_extends_a_session_rather_than_replacing_it() -> None:
    """Found by running the step, not by reading it.

    The instruction first said to write the file whole on every run, which reads
    as the simpler rule and is wrong for the only case that matters: this branch
    asked three questions, then re-scanned a spec that no longer had any, and
    replacing would have deleted the three answers FR-013 through FR-015 were
    written from.

    Both halves are asserted because they are separate rules that were settled
    separately — append across sessions, and extend rather than open a second
    section when the date is already present.
    """
    flowed = " ".join(_SHARED.read_text().split())

    assert "never discards an earlier session" in flowed
    assert "extends that section rather than opening a new one" in flowed


def test_the_shared_skill_creates_the_directory_before_writing() -> None:
    """`arch-root` neither checks the root exists nor creates it, and nothing seeds `scans/`.

    So the first scan in any project writes into a parent that is not there, and
    an agent whose `Write` needs an existing directory fails before the commit
    that would have made the file visible. The instruction read correctly and
    could not run — the shape this repo keeps meeting.
    """
    assert "mkdir -p <root>/scans" in _SHARED.read_text()


def test_the_shared_skill_refuses_an_out_of_tree_arch_root() -> None:
    """`wfctl arch-root` exits 0 with a warning when the root is outside the tree.

    Nothing downstream stops on its own, so the step would write a file `git add`
    refuses and no reviewer reaches — the exact state this skill exists to leave
    behind, produced by the skill itself. Falling back to a repository-local path
    is the wrong repair and is named as such: `arch_root` is the single authority
    for where records live.
    """
    flowed = " ".join(_SHARED.read_text().split())

    assert "outside the working tree is the same answer" in flowed
    assert "Do not fall back to a repository-local path" in flowed


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_each_review_wrapper_writes_a_scan_file_on_the_abort_path(step: str) -> None:
    """`inconclusive` was defined and unreachable.

    Both workflows halt early on a missing artifact, and the scan-file section
    sits after the pointer to them — so the one verdict meaning "could not run"
    was never written by any run that could not run. A failed scan and a skipped
    one stayed identical, which is #307 met on the failure path.
    """
    section = _section(step)
    flowed = " ".join(section.split())

    assert "written on every exit path, including an abort" in flowed
    assert "inconclusive" in section


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_no_review_skill_carries_the_instruction(step: str) -> None:
    """`vendor-upstream-skills`: prefer layering to editing.

    Both are `github/spec-kit`-derived. An edit made in the `SKILL.md` is reverted
    by the next upstream pull with no conflict to notice, and the behaviour then
    regresses at a moment whose diff mentions neither step. This fails on the
    repair, not on the original mistake.
    """
    skill = _AGENTS / "skills" / f"speckit-{step}" / "SKILL.md"

    assert "## Write the scan file" not in skill.read_text()


def test_the_analyze_wrapper_names_the_read_only_rule_it_overrides() -> None:
    """`speckit-analyze` says STRICTLY READ-ONLY twice, and now it writes a file.

    `speckit.brainstorm.md` is the precedent and it names every upstream pause it
    overrides. A wrapper that silently contradicts the skill it points at teaches
    the reader to discount both, which costs more than the one rule it bent.
    """
    assert "READ-ONLY" in (_AGENTS / "skills" / "speckit-analyze" / "SKILL.md").read_text()
    assert "read-only rule" in _section("analyze")


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_each_review_wrapper_allows_the_commands_the_scan_file_needs(step: str) -> None:
    """`allowed-tools` is a ceiling on the whole turn, so a rule without its grant
    is a rule that reads correctly and cannot run.

    Silent in the worst way: the agent reports a tool refusal, not a missing
    instruction. `test_skill_cross_references` already holds this for
    `speckit.brainstorm.md`, which is where the shape comes from. `Edit` is in the
    list because appending a session to an existing file through `Write` means
    rewriting it whole, which is the operation most likely to drop what was there.
    """
    front = _wrapper(step).split("---")[1]
    allowed = next(ln for ln in front.splitlines() if ln.startswith("allowed-tools:"))

    for grant in (
        "Write", "Edit", "wfctl arch-root", "wfctl arch check", "mkdir", "git commit",
    ):
        assert grant in allowed, f"speckit.{step}.md cannot run its own instruction: {grant}"


def test_the_clarify_wrapper_keeps_every_rejected_option_rather_than_one() -> None:
    """The grain #307 shipped was per finding; clarify's questions are per option.

    The first version of the findings line read "Decided against <the
    alternative>: <why>" — one alternative, however many the question offered. A
    two-option question and a five-option one rendered identically, so the reader
    could not tell four discarded options from one (#286).
    """
    flowed = " ".join(_section("clarify").split())

    assert "One `Decided against` line per lettered option the question offered" in flowed


def test_the_clarify_wrapper_counts_only_the_lettered_options() -> None:
    """Step 4's rendered table carries a trailing `Short` row, and it is not an option.

    Three panel reviewers found the same thing: "every option the question
    offered" reads onto that row, no true reason exists for rejecting an escape
    hatch, and the anti-straw rule then forces one to be invented — the rule
    breaking the rule beside it.
    """
    flowed = " ".join(_section("clarify").split())

    assert "`Short` row, which is an escape hatch from the options" in flowed


def test_the_clarify_wrapper_refuses_a_straw_option() -> None:
    """A record of options nobody weighed is worse than no record.

    `architecture-decisions` already holds its own `Considered` to this and the
    wrapper borrows the standard rather than restating a weaker one: an instruction
    to name what lost, with no rule about *why*, is answerable by inventing a bad
    option — and a reviewer cannot tell that from a real one.
    """
    flowed = " ".join(_section("clarify").split())

    assert "The reason an option lost is the reason it actually lost" in flowed
    assert "a weakness the option does not have is never one" in flowed


def test_the_clarify_wrapper_keys_the_exemption_on_the_table_not_the_answer() -> None:
    """Step 4 lets an A/B/C question be answered in free-form words.

    The exemption first read "a short-answer question offered no options", which
    is a sentence about the answer as easily as about the question — so the one
    path where options were offered and none was taken would have written "no
    options offered" and discarded all of them. That is the evidence #286 was
    filed over, destroyed by the sentence added to protect it.
    """
    flowed = " ".join(_section("clarify").split())

    assert "Only a question that rendered no option table writes" in flowed
    assert "A multiple-choice question is not that case, however it was answered" in flowed


def test_the_clarify_wrapper_is_not_conditional_on_the_mode() -> None:
    """`speckit.brainstorm.md`'s layer is conditional on `auto_approve`, and copying its
    shape would have inherited a condition this rule does not want.

    A human picking option B destroys A and C as thoroughly as an unattended run
    does. #286 flagged the question rather than answering it; the wrapper answers
    it, so the next reader finds a decision instead of an omission.
    """
    flowed = " ".join(_section("clarify").split())

    assert "This holds however the answer was chosen" in flowed


def test_the_clarify_template_shows_both_findings_shapes() -> None:
    """The rationale is what a reader checks; the template is what an agent copies.

    Every other assertion here matches prose, so reverting the template block to
    one `Decided against` line — and dropping the short-answer line, whose exact
    wording appears nowhere else — ships green while the copyable shape says the
    opposite of the rule above it.
    """
    template = _section("clarify").split("```markdown")[1].split("```")[0]

    assert template.count("Decided against") == 2
    assert "No options offered — short answer." in template


def test_the_shared_skill_defers_the_findings_count_to_the_wrapper() -> None:
    """Two rules in one bundle disagreeing about a count is worse than either alone.

    The skill is read first and its delegation clause lists what it does not own;
    the findings-line shape was not on that list, so it went on stating the
    singular while the clarify wrapper required one line per option. It is also
    where #286's third open question lands: `analyze` reaches a finding with no
    option set to discard, so the count cannot be shared.
    """
    flowed = " ".join(_SHARED.read_text().split())

    assert "How many alternatives that is belongs to the wrapper that sent you here" in flowed


# --- what the destination changed -------------------------------------------


def test_a_scan_file_is_not_a_decision_in_force(tmp_path: Path) -> None:
    """`arch context` must keep meaning "the decisions this repo is built under".

    `load_records` globs `<root>/*.md` one level deep, which is what keeps
    `design/`, `declarations/` and `views/` out of the projection — `wfctl arch
    none`'s own help gives that as the reason declarations live in a
    subdirectory. `scans/` rides on the same property, and a future move of these
    files to the root would file every scan among the accepted records.
    """
    root = tmp_path / "docs" / "architecture"
    (root / SCANS_DIR).mkdir(parents=True)
    (root / SCANS_DIR / "307-clarify.md").write_text("# Clarification scan — #307\n")
    (root / "a-decision.md").write_text(
        "---\nstatus: accepted\n---\n\n# A decision\n\n## Log\n\n- 2026-01-01  accepted  — x\n"
    )

    slugs = [record.slug for record in _arch.load_records(root)]

    assert slugs == ["a-decision"]


def test_a_scan_file_is_not_a_record_this_branch_decided(tmp_path: Path) -> None:
    """The defect three reviewers found, written as the outcome it must not produce.

    `records_on_this_branch` asks git about the arch root, and a git pathspec
    naming a directory is recursive. Before the exclusion, every branch that ran
    clarify reported two `record:` lines for documents that decided nothing —
    under the `auto-approve` notice, whose whole job is telling an unattended run's
    reader what it chose.
    """
    repo = _repo(tmp_path / "r")
    arch = repo / "docs" / "architecture"
    (arch / SCANS_DIR).mkdir(parents=True)
    (arch / SCANS_DIR / "307-clarify.md").write_text("# scan\n")
    (arch / "a-decision.md").write_text("---\nstatus: accepted\n---\n\n# A decision\n")
    subprocess.run(["git", "checkout", "-qb", "307-x"], cwd=repo, check=True)

    slugs = records_on_this_branch(repo, arch, exclude=arch / SCANS_DIR)

    assert slugs == ["a-decision"]


def test_a_scan_file_alone_does_not_answer_the_boundary_question(tmp_path: Path) -> None:
    """`wfctl end`'s handoff says whether the boundary question was answered.

    Clarify and analyze run on nearly every branch, so a scan file counted here
    makes that observation constant-true and it stops carrying anything —
    `_BOUNDARY`'s own comment calls naming a missing answer "answered" the kind of
    claim #70 is about.
    """
    repo = _repo(tmp_path / "r")
    arch = repo / "docs" / "architecture"
    (arch / SCANS_DIR).mkdir(parents=True)
    (arch / SCANS_DIR / "307-clarify.md").write_text("# scan\n")
    subprocess.run(["git", "checkout", "-qb", "307-x"], cwd=repo, check=True)

    assert touched_on_this_branch(repo, arch) is True
    assert touched_on_this_branch(repo, arch, exclude=arch / SCANS_DIR) is False


def test_arch_check_answers_for_a_path_under_scans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The claim the whole destination rests on: the check takes any path.

    `arch check` was built for a level-3 record and never asked whether its
    argument sits under the arch root, so a scan file gets the same answer for
    free and this feature adds no command. Asserted because that is an absence —
    nothing in the command says it is deliberate, and a containment guard added
    later would silently strand every scan file.
    """
    repo = _repo(tmp_path / "r")
    scan = repo / "docs" / "architecture" / SCANS_DIR / "307-clarify.md"
    scan.parent.mkdir(parents=True)
    scan.write_text("# Clarification scan — #307\n")
    subprocess.run(["git", "checkout", "-qb", "307-x"], cwd=repo, check=True)
    subprocess.run(["git", "add", str(scan)], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "scan"], cwd=repo, check=True)
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["arch", "check", str(scan)])

    assert result.exit_code == 0, result.output
    assert "this change adds it" in result.output
