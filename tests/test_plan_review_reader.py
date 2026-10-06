"""The plan review's contract with wfctl: the plan identity, the two report
lines wfctl reads, and the pass reason the step roll-up carries.

The reviewer computes the identity with `git hash-object --no-filters` and wfctl
computes it in Python on every status read. The two sides never talk to each
other, so the only thing holding them to the same value is that they agree on
the same bytes, and the identity tests below compare against git itself rather
than against a hash written into the test.
"""
from __future__ import annotations

import json
import subprocess
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl import _evidence, _pipeline
from wfctl._evidence import DESIGN_BLOCK_REASON, Assessment, Evidence, build_evidence
from wfctl._pipeline import Step, SubStep, _infer_steps, build_report
from wfctl._plan_review import identity, read_report
from wfctl.cli import app
from tests.conftest import CLEAN_PLAN, CLEAN_SPEC, init_git, write_plan_review

runner = CliRunner()


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


# --- the pass state, rows 4 and 5 (T018) ------------------------------------

_STALE = "stale; plan.md changed since the review"


def _edit_plan(feature: Path, extra: str = "\nOne more sentence.\n") -> None:
    plan_md = feature / "plan.md"
    plan_md.write_bytes(plan_md.read_bytes() + extra.encode())


def test_a_report_with_no_plan_row_holds_plan_and_says_the_identity_is_missing(
    spec_tree, repo_root: Path
) -> None:
    """Row 4: a review that never named the plan it read cannot be compared
    with the plan now. Reading it as current would clear any plan at all, and
    reading it as stale would send a person to edit a plan nobody touched, so
    the text names the report as what is wrong."""
    feature = spec_tree("spec.md", "plan.md")
    _report(feature, inputs=f"| spec.md | {_PLAN_ID} | requirements |\n", summary="BLOCKER: 0\n")

    reading = _evidence.plan_review(build_evidence(feature, repo_root))
    assert reading == Assessment("in_progress", None, "the review records no plan.md identity")

    plan = _plan_step(feature, repo_root)
    assert plan.state == "in_progress"
    assert plan.annotation == "the review records no plan.md identity"
    assert plan.reason is None


def test_an_edited_plan_reads_stale_after_a_clean_review(
    spec_tree, repo_root: Path
) -> None:
    """Row 5 (FR-004): the review read a plan that is no longer on disk. Only
    the identity can tell, since the report's count still says clean, and a
    reader that trusted the count would let `tasks` run on unreviewed text."""
    feature = _reviewed_feature(spec_tree, "BLOCKER: 0\n")
    _edit_plan(feature)

    reading = _evidence.plan_review(build_evidence(feature, repo_root))
    assert reading == Assessment("in_progress", None, _STALE)

    plan = _plan_step(feature, repo_root)
    assert plan.state == "in_progress"
    assert plan.annotation == _STALE
    assert plan.reason is None


@pytest.mark.parametrize(
    "summary", ["BLOCKER: 2\n", "MAJOR: 1\n"], ids=["open blocker", "no count"],
)
def test_the_stale_reading_wins_over_whatever_the_report_counted(
    spec_tree, repo_root: Path, summary: str
) -> None:
    """Rows 4 and 5 come before rows 6 and 7. A count is about the plan the
    review read, so once that plan is gone the count describes nothing on
    disk, and "2 BLOCKER findings open" would send the wrapper to revise
    findings that may no longer exist rather than review the new text."""
    feature = _reviewed_feature(spec_tree, summary)
    _edit_plan(feature)

    assert _evidence.plan_review(build_evidence(feature, repo_root)) == Assessment(
        "in_progress", None, _STALE,
    )


def test_an_edit_inside_a_fenced_block_still_reads_stale(
    spec_tree, repo_root: Path
) -> None:
    """The identity is taken from the raw bytes. `ev.plan_text` has fenced
    blocks, comments and inline spans blanked for the section check, so a
    reader that hashed it would miss an edit to a code sample the plan
    carries, which is often the part a reviewer read most closely."""
    feature = spec_tree(
        "spec.md", content={"plan.md": CLEAN_PLAN + "\n```\nold = 1\n```\n"},
    )
    write_plan_review(feature)
    plan_md = feature / "plan.md"
    plan_md.write_text(plan_md.read_text().replace("old = 1", "old = 2"))

    assert _evidence.plan_review(build_evidence(feature, repo_root)) == Assessment(
        "in_progress", None, _STALE,
    )


def test_a_plan_restored_byte_for_byte_reads_done_again(
    spec_tree, repo_root: Path
) -> None:
    """FR-005 and SC-002: an edit and its revert leave the review valid. A
    reader that remembered having seen the plan stale, or that compared
    anything beyond the bytes, would make a person review a plan the review
    already read."""
    feature = _reviewed_feature(spec_tree, "BLOCKER: 0\n")
    plan_md = feature / "plan.md"
    reviewed = plan_md.read_bytes()

    _edit_plan(feature)
    assert _evidence.plan_review(build_evidence(feature, repo_root)).state == "in_progress"

    plan_md.write_bytes(reviewed)
    assert _evidence.plan_review(build_evidence(feature, repo_root)) == Assessment("done")


def test_an_edit_to_spec_alone_leaves_the_review_done(
    spec_tree, repo_root: Path
) -> None:
    """Staleness is about `plan.md` only. The wrapper notices a changed
    `spec.md` through the report's other input rows (FR-026), and a reader
    that hashed every input would hold the pipeline on any spec edit and
    leave a person no way to clear it short of a full review."""
    feature = _reviewed_feature(spec_tree, "BLOCKER: 0\n")
    spec_md = feature / "spec.md"
    spec_md.write_text(spec_md.read_text() + "\nA new requirement.\n")

    assert _evidence.plan_review(build_evidence(feature, repo_root)) == Assessment("done")


# --- the route back from a finished feature (T019) --------------------------


def test_a_stale_review_sends_a_finished_feature_back_to_the_review(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-004 however far the pipeline has gone: every step after `plan` is
    done, and an edit to the reviewed plan still makes `plan` current. The
    payload is contracts/cli.md § `wfctl status`, field for field.

    The step's reason stays null. A reason would route to the step's own
    command, `/speckit.plan`, whose `setup-plan.sh` copies the template over
    `plan.md` and destroys the edit that made the review stale (R3)."""
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    storyctl_dir.make_spec_artifact("plan", content=CLEAN_PLAN)
    write_plan_review(storyctl_dir.spec_dir)
    storyctl_dir.make_spec_artifact("tasks", content="- [x] t1\n- [x] t2\n")
    storyctl_dir.make_spec_artifact("analyze")
    storyctl_dir.make_spec_artifact("decompose")
    _edit_plan(storyctl_dir.spec_dir)

    report = build_report(
        storyctl_dir.spec_dir, storyctl_dir.repo_root, storyctl_dir.agent_dir,
    )

    assert (report.current, report.next_command, report.auto) == ("plan", "/plan-review", False)
    steps = {s["name"]: s for s in report.steps}
    assert all(steps[name]["state"] == "done" for name in ("tasks", "analyze", "implement"))
    plan = steps["plan"]
    assert (plan["state"], plan["annotation"], plan["reason"]) == ("in_progress", _STALE, None)
    assert plan["sub_steps"] == [
        {
            "name": "plan-review", "state": "in_progress", "annotation": _STALE,
            "command": "/plan-review", "manual": False, "claimed": None,
            "needs_person": False, "is_current": True,
        },
    ]


# --- tasks written before any review (#542) ---------------------------------


def _tasked_without_a_review(
    storyctl_dir: types.SimpleNamespace, tasks_md: str, *later: str,
) -> None:
    """A feature whose plan was turned into tasks with no review on record,
    whether the run went out of order or the plan predates this pass."""
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    storyctl_dir.make_spec_artifact("plan", content=CLEAN_PLAN)
    storyctl_dir.make_spec_artifact("tasks", content=tasks_md)
    for step in later:
        storyctl_dir.make_spec_artifact(step)


@pytest.mark.parametrize(
    ("tasks_md", "later"),
    [
        ("# Tasks\n\nno checkbox yet\n", ()),
        ("- [ ] t1\n", ()),
        ("- [x] t1\n- [ ] t2\n", ("analyze", "decompose")),
    ],
    ids=["at tasks", "at analyze", "at implement"],
)
def test_tasks_written_before_any_review_hold_the_plan_for_one(
    storyctl_dir: types.SimpleNamespace, tasks_md: str, later: tuple[str, ...],
) -> None:
    """The pass used to read `skipped` here and only warn, so a run that went
    from the plan straight to `/speckit.tasks` carried on with an unreviewed
    plan under everything it built next. However far the later artifacts got,
    the route goes back to `/plan-review`, and the row says why."""
    _tasked_without_a_review(storyctl_dir, tasks_md, *later)

    report = build_report(
        storyctl_dir.spec_dir, storyctl_dir.repo_root, storyctl_dir.agent_dir,
    )

    assert (report.current, report.next_command) == ("plan", "/plan-review")
    plan = next(s for s in report.steps if s["name"] == "plan")
    [review] = plan["sub_steps"]
    assert (review["state"], review["annotation"]) == ("in_progress", _evidence.PLAN_UNREVIEWED)
    assert report.warnings == ()


def test_a_claim_lets_a_feature_planned_before_the_pass_keep_its_step(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The way out for a feature whose tasks predate this pass. Without one,
    every such feature resumed after the upgrade would have nowhere to go but
    a review of a plan its implementation is half built on."""
    _tasked_without_a_review(storyctl_dir, "- [x] t1\n- [ ] t2\n", "analyze", "decompose")
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(storyctl_dir.repo_root / "docs" / "architecture"))

    claimed = runner.invoke(
        app, ["step", "none", "plan.plan-review", "--reason", "planned before the review existed"],
    )
    assert claimed.exit_code == 0, claimed.output

    payload = json.loads(runner.invoke(app, ["status", "--json"]).output)
    assert payload["current"] == "implement"
    assert payload["warnings"] == []
