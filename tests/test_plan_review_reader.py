"""The plan review's contract with wfctl: the plan identity, the two report
lines wfctl reads, and the pass reason the step roll-up carries.

The reviewer computes the identity with `git hash-object --no-filters` and wfctl
computes it in Python on every status read. The two sides never talk to each
other, so the only thing holding them to the same value is that they agree on
the same bytes, and the identity tests below compare against git itself rather
than against a hash written into the test.
"""
from __future__ import annotations

import subprocess
import types
from pathlib import Path

import pytest

from wfctl import _evidence, _pipeline
from wfctl._evidence import DESIGN_BLOCK_REASON, Assessment, Evidence, build_evidence
from wfctl._pipeline import Step, SubStep, _infer_steps
from wfctl._plan_review import identity, read_report
from tests.conftest import init_git


def _git_hash(path: Path, *flags: str) -> str:
    """What the reviewer's shell computes for `path`, run from the file's own
    directory so a repository's attributes apply when there is one."""
    result = subprocess.run(
        ["git", "hash-object", *flags, str(path)],
        cwd=path.parent, check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


# --- identity (T003) -------------------------------------------------------


def test_the_identity_of_an_lf_file_is_the_hash_git_computes_without_filters(
    tmp_path: Path,
) -> None:
    """The plain case, outside any repository, where the feature directory
    resolves in this repo. A header built with the wrong length or separator
    fails here first, since git is the reference and not a constant."""
    plan = tmp_path / "plan.md"
    plan.write_bytes(b"# Plan\n\nOne line.\n")

    assert identity(plan) == _git_hash(plan, "--no-filters")


def test_the_identity_of_a_crlf_file_ignores_the_repositorys_line_ending_rule(
    tmp_path: Path,
) -> None:
    """A repository with `*.md text eol=lf` makes plain `git hash-object`
    normalise CRLF before hashing, so a reviewer that dropped `--no-filters`
    would record a value wfctl never computes, and the review would read stale
    the moment it was written.

    The second assertion proves the fixture exercises normalisation at all.
    Without it, a repository that happened not to apply the rule would make
    this test the same as the LF one.
    """
    repo = init_git(tmp_path / "repo")
    (repo / ".gitattributes").write_text("*.md text eol=lf\n")
    plan = repo / "plan.md"
    plan.write_bytes(b"# Plan\r\n\r\nOne line.\r\n")

    assert identity(plan) == _git_hash(plan, "--no-filters")
    assert identity(plan) != _git_hash(plan)


def test_the_identity_of_a_file_under_a_clean_filter_is_taken_from_its_raw_bytes(
    tmp_path: Path,
) -> None:
    """A clean filter rewrites the bytes plain `git hash-object` hashes, and
    wfctl reads the working-tree bytes. Only `--no-filters` makes the two sides
    agree, and this is the case research R1 measured them diverging on."""
    repo = init_git(tmp_path / "repo")
    (repo / ".gitattributes").write_text("*.md filter=shout\n")
    subprocess.run(
        ["git", "-C", str(repo), "config", "filter.shout.clean", "tr a-z A-Z"],
        check=True, capture_output=True,
    )
    plan = repo / "plan.md"
    plan.write_bytes(b"# Plan\n\nOne line.\n")

    assert identity(plan) == _git_hash(plan, "--no-filters")
    assert identity(plan) != _git_hash(plan)


def test_a_plan_restored_to_its_reviewed_bytes_has_its_reviewed_identity_again(
    tmp_path: Path,
) -> None:
    """FR-005: an edit and its revert leave the review valid. An identity that
    folded in anything beyond the bytes, such as a modification time, would
    leave the restored plan reading stale."""
    plan = tmp_path / "plan.md"
    plan.write_bytes(b"# Plan\n\nOne line.\n")
    reviewed = identity(plan)

    plan.write_bytes(b"# Plan\n\nAn edited line.\n")
    assert identity(plan) != reviewed

    plan.write_bytes(b"# Plan\n\nOne line.\n")
    assert identity(plan) == reviewed


# --- read_report (T004) ----------------------------------------------------

_PLAN_ID = "9f2c1e0d4b6a8c2e1f3a5b7d9e0c2a4f6b8d0e1c"


def _report(
    tmp_path: Path,
    *,
    inputs: str = f"| plan.md | {_PLAN_ID} | technical strategy |\n",
    summary: str = "BLOCKER: 2\nMAJOR: 1\nMINOR: 0\n",
    findings: str = "none\n",
) -> Path:
    """A report shaped like contracts/report-format.md, with each section's
    body replaceable so a test changes only the line it is about."""
    path = tmp_path / "plan-review.md"
    path.write_text(
        "# Plan review\n\n"
        "## Summary\n\n" + summary + "\n"
        "## Reviewed inputs\n\n"
        "| Input | Identity | Role |\n"
        "| --- | --- | --- |\n" + inputs + "\n"
        "## Findings\n\n" + findings
    )
    return path


def test_the_report_gives_the_plan_identity_and_the_open_blocker_count(tmp_path: Path) -> None:
    """The two lines wfctl reads, in the shape the contract gives them. Every
    reader state in the later phases builds on these two values."""
    report = read_report(_report(tmp_path))

    assert report.plan_identity == _PLAN_ID
    assert report.open_blockers == 2


def test_a_report_with_no_plan_row_records_no_identity(tmp_path: Path) -> None:
    """Row 4 of the pass state: a review that never named the plan it read
    cannot be compared against the plan now, so the value is absent rather
    than a guess."""
    path = _report(tmp_path, inputs=f"| spec.md | {_PLAN_ID} | requirements |\n")

    assert read_report(path).plan_identity is None


def test_a_report_with_no_blocker_line_records_no_count(tmp_path: Path) -> None:
    """Row 6: a missing count is promised evidence gone silent. Reading it as
    zero would let a report with open BLOCKER findings pass as clean."""
    path = _report(tmp_path, summary="MAJOR: 1\nMINOR: 0\n")

    assert read_report(path).open_blockers is None


@pytest.mark.parametrize(
    "cell",
    [
        _PLAN_ID.upper(),
        _PLAN_ID[:-1],
        _PLAN_ID + "0",
        "absent",
        "",
    ],
    ids=["uppercase", "39 characters", "41 characters", "absent", "empty"],
)
def test_a_plan_identity_that_is_not_40_lowercase_hex_characters_is_absent(
    tmp_path: Path, cell: str
) -> None:
    """`git hash-object` prints 40 lowercase hex characters and `identity`
    returns the same, so any other value can never match the plan. Reading it
    as absent names the real problem, where reading it as a mismatch would
    call the plan edited when it was not."""
    path = _report(tmp_path, inputs=f"| plan.md | {cell} | technical strategy |\n")

    assert read_report(path).plan_identity is None


def test_a_plan_row_outside_reviewed_inputs_is_not_read(tmp_path: Path) -> None:
    """A finding can quote a table row naming `plan.md`, and its identity cell
    could be any hash the reviewer saw. Only the inputs table says which plan
    this review read."""
    path = _report(
        tmp_path,
        inputs=f"| spec.md | {_PLAN_ID} | requirements |\n",
        findings=f"| plan.md | {_PLAN_ID} | quoted from an earlier review |\n",
    )

    assert read_report(path).plan_identity is None


def test_a_blocker_line_outside_the_summary_is_not_read(tmp_path: Path) -> None:
    """A finding can quote an earlier report's `BLOCKER: 3`, and that count is
    not this report's. Read from anywhere, it would hold a clean report open or
    clear one that lost its summary line."""
    path = _report(tmp_path, summary="MAJOR: 1\n", findings="BLOCKER: 0\n")

    assert read_report(path).open_blockers is None


# --- the pass reason in the step roll-up (T006) ----------------------------


def test_brainstorms_design_block_still_sets_the_step_reason_and_its_remedy(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The roll-up now copies a pass's reason onto its step instead of the
    pass's rendered text. The architecture pass sets its reason itself, so
    the step must still carry `DESIGN_BLOCK_REASON`, and `_design_remedy`,
    which keys on exactly that string, must still produce the two ways out."""
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(storyctl_dir.repo_root / "docs" / "architecture"))
    storyctl_dir.make_spec_artifact("brainstorm")

    brainstorm = _infer_steps(storyctl_dir.spec_dir, storyctl_dir.repo_root)[0]

    assert brainstorm.name == "brainstorm"
    assert brainstorm.state == "in_progress"
    assert brainstorm.reason == DESIGN_BLOCK_REASON
    assert brainstorm.sub_steps[0].reason == DESIGN_BLOCK_REASON
    assert brainstorm.remedy is not None
    assert 'wfctl arch none --reason "<why>"' in brainstorm.remedy


def test_a_pass_that_only_displays_text_leaves_its_step_without_a_reason(
    spec_tree, repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A step with a reason reads as held, and a held step routes to its own
    command. Copying the pass's display text onto the step's reason would send
    a stale plan review to `/speckit.plan`, which overwrites `plan.md` (R3).
    The text still reaches the step's annotation, where a person reads it."""
    def displays_only(ev: Evidence) -> Assessment:
        return Assessment("in_progress", None, "stale; plan.md changed since the review")

    monkeypatch.setitem(
        _pipeline._STEPS, "brainstorm",
        Step(
            "/speckit.brainstorm", "automatic", _pipeline._STEPS["brainstorm"].reads,
            sub_steps=(SubStep("probe", "/probe", "automatic", displays_only),),
        ),
    )
    feature = spec_tree("design.md")

    brainstorm = _infer_steps(feature, repo_root)[0]

    assert brainstorm.state == "in_progress"
    assert brainstorm.annotation == "stale; plan.md changed since the review"
    assert brainstorm.reason is None
    assert brainstorm.sub_steps[0].reason is None


# --- the pass state, rows 2, 6, 7 and 8 (T008) ------------------------------


def _reviewed_feature(spec_tree, summary: str | None) -> Path:
    """A feature whose plan is complete, with a report of that exact plan.

    `summary=None` writes no report at all. Otherwise the report's `plan.md` row
    carries the plan's real identity, so every test here is about the count and
    never about staleness, which rows 4 and 5 own.
    """
    feature = spec_tree("spec.md", "plan.md")
    if summary is not None:
        _report(
            feature,
            inputs=f"| plan.md | {identity(feature / 'plan.md')} | technical strategy |\n",
            summary=summary,
        )
    return feature


def _plan_step(feature: Path, repo_root: Path) -> _pipeline._PipelineStep:
    return next(s for s in _infer_steps(feature, repo_root) if s.name == "plan")


def _plan_review_pass(step: _pipeline._PipelineStep) -> _pipeline._PipelineSubStep:
    return next(s for s in step.sub_steps if s.name == "plan-review")


def test_a_complete_plan_with_no_report_holds_plan_with_nothing_to_say(
    spec_tree, repo_root: Path
) -> None:
    """Row 2 (R2): the review has not run, so the pass is current. It reads
    `in_progress` rather than `pending`, because the roll-up holds a step only
    on an `in_progress` pass, and a `pending` one would let `tasks` become
    current before the plan was ever reviewed. No text, because nothing has
    gone wrong yet, and no reason, because a reason would route to
    `/speckit.plan`."""
    feature = _reviewed_feature(spec_tree, None)

    reading = _evidence.plan_review(build_evidence(feature, repo_root))
    assert reading == Assessment("in_progress")

    plan = _plan_step(feature, repo_root)
    assert plan.state == "in_progress"
    assert plan.annotation is None
    assert plan.reason is None
    assert _plan_review_pass(plan).state == "in_progress"


def test_a_report_with_no_blocker_count_holds_plan_and_says_the_line_is_missing(
    spec_tree, repo_root: Path
) -> None:
    """Row 6: the skill promised the count and wrote none. Reading silence as
    zero would pass a review whose findings nobody counted, and the text names
    the missing line so a person knows the report is what to fix."""
    feature = _reviewed_feature(spec_tree, "MAJOR: 1\nMINOR: 0\n")

    reading = _evidence.plan_review(build_evidence(feature, repo_root))
    assert reading == Assessment("in_progress", None, "the review records no BLOCKER count")

    plan = _plan_step(feature, repo_root)
    assert plan.state == "in_progress"
    assert plan.annotation == "the review records no BLOCKER count"
    assert plan.reason is None


def test_an_open_blocker_holds_plan_and_counts_what_is_open(
    spec_tree, repo_root: Path
) -> None:
    """Row 7 (FR-026): a review of the current plan with a BLOCKER open holds
    the pipeline before `tasks`. The text is display only, so the pass routes
    to `/plan-review`; carried as the step's reason, it would route to
    `/speckit.plan`, which copies the template over `plan.md` (R3)."""
    feature = _reviewed_feature(spec_tree, "BLOCKER: 2\nMAJOR: 0\nMINOR: 0\n")

    reading = _evidence.plan_review(build_evidence(feature, repo_root))
    assert reading == Assessment("in_progress", None, "2 BLOCKER findings open")

    plan = _plan_step(feature, repo_root)
    assert plan.state == "in_progress"
    assert plan.annotation == "2 BLOCKER findings open"
    assert plan.reason is None


def test_a_clean_review_of_the_current_plan_reads_done(
    spec_tree, repo_root: Path
) -> None:
    """Row 8: the one reading that lets `tasks` become current. A reader that
    fell through to `in_progress` here would hold every reviewed plan forever."""
    feature = _reviewed_feature(spec_tree, "BLOCKER: 0\nMAJOR: 3\nMINOR: 1\n")

    reading = _evidence.plan_review(build_evidence(feature, repo_root))
    assert reading == Assessment("done")

    plan = _plan_step(feature, repo_root)
    assert plan.state == "done"
    assert plan.annotation is None
    assert plan.reason is None
    assert _plan_review_pass(plan).state == "done"
