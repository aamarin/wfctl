"""wfctl reads each review step's scan file from the spec folder (#598).

Since `scans-live-in-spec-folder`, a scan isn't committed, so no PR reviewer
sees one go missing. The step readers check it instead: clarify, analyze, and
the plan review pass each stay current until their scan has a `- Verdict:` line
and a coverage row with a status. These tests pin each state the spec's User
Stories 2 and 3 name, and that a held step stays automatic.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from tests.conftest import CLEAN_PLAN, CLEAN_SPEC, write_scan
from wfctl._evidence import (
    SCAN_MISSING, SCAN_NO_ROWS, SCAN_NO_VERDICT, scan_reason,
)
from wfctl._paths import spec_scan
from wfctl._pipeline import _infer_steps, build_report
from wfctl._plan_review import REPORT_NAME, identity

_VALID = (
    "# scan\n\n## Session 2026-11-11\n\n- Verdict: {verdict}\n\n### Coverage\n\n"
    "| Category | Status |\n| --- | --- |\n| Functional Scope | {status} |\n"
)


def _write(feature: Path, step: str, text: str) -> None:
    scan = spec_scan(feature, step)
    scan.parent.mkdir(parents=True, exist_ok=True)
    scan.write_text(text)


def _step(feature: Path, repo_root: Path, name: str):
    return next(s for s in _infer_steps(feature, repo_root) if s.name == name)


def _review_report(feature: Path) -> None:
    (feature / REPORT_NAME).write_text(
        "# Plan review\n\n## Summary\n\nBLOCKER: 0\n\n## Reviewed inputs\n\n"
        "| Input | Identity | Role |\n| --- | --- | --- |\n"
        f"| plan.md | {identity(feature / 'plan.md')} | technical strategy |\n"
    )


def test_the_scan_path_is_under_the_spec_folder(tmp_path: Path) -> None:
    """The readers and the sign-off name the file through one function, so a
    sign-off can't write where the reader doesn't look. The issue key is left
    out because the spec folder already carries it."""
    assert spec_scan(tmp_path, "clarify") == tmp_path / "scans" / "clarify.md"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (None, SCAN_MISSING),
        ("", SCAN_MISSING),
        ("# scan\n\n| Category | Status |\n| --- | --- |\n| A | Clear |\n", SCAN_NO_VERDICT),
        ("# scan\n\n- Verdict: satisfied\n\nNo table.\n", SCAN_NO_ROWS),
        (_VALID.format(verdict="satisfied", status="Clear"), None),
        (_VALID.format(verdict="inconclusive", status="Deferred (no spec.md)"), None),
    ],
    ids=["missing", "empty", "no-verdict", "no-rows", "valid", "inconclusive"],
)
def test_the_scan_reason_names_which_part_is_missing(
    tmp_path: Path, text: str | None, expected: str | None
) -> None:
    """Each held reading says which part to write, so the rerun knows whether
    the file, its verdict, or its coverage table is what it skipped. An
    `inconclusive` scan passes, since the step's own artifact check is what
    holds a step that couldn't run."""
    if text is not None:
        _write(tmp_path, "clarify", text)
    assert scan_reason(tmp_path, "clarify") == expected


def test_an_unsatisfied_verdict_still_passes(tmp_path: Path) -> None:
    """FR-008. The reader asks whether a scan ran, not what it found. Holding
    on `unsatisfied` is a gate on the scan's result, which #100 owns."""
    _write(tmp_path, "clarify", _VALID.format(verdict="unsatisfied", status="Outstanding"))
    assert scan_reason(tmp_path, "clarify") is None


def test_a_file_holding_only_sign_off_sections_has_no_verdict(tmp_path: Path) -> None:
    """A sign-off needs a review report, so a review ran and its wrapper had to
    write a section. A file with only sign-offs means that review skipped its
    scan, and the sign-off mustn't hide it."""
    _write(
        tmp_path, "plan-review",
        "# Plan review scan for #598\n\n## Sign-off 2026-11-11T10:00Z\n\n"
        "- Signed off: plan.md abc\n- Reason: typo\n- Reviewed copy: compared\n",
    )
    assert scan_reason(tmp_path, "plan-review") == SCAN_NO_VERDICT


def test_a_review_section_before_a_sign_off_still_passes(tmp_path: Path) -> None:
    """The whole file is read, not its last section. A plan review scan ends with
    a sign-off section after each sign-off, so a last-section read would hold
    every signed-off plan."""
    _write(
        tmp_path, "plan-review",
        _VALID.format(verdict="satisfied", status="Clear")
        + "\n## Sign-off 2026-11-11T10:00Z\n\n- Signed off: plan.md abc\n",
    )
    assert scan_reason(tmp_path, "plan-review") is None


def test_a_measurement_row_beside_a_status_row_passes(tmp_path: Path) -> None:
    """Analyze's last row carries a percentage. One row with a status is enough,
    so the measurement row needs no exception."""
    _write(
        tmp_path, "analyze",
        "- Verdict: satisfied\n\n| Pass | Status |\n| --- | --- |\n"
        "| A · Duplication | Clear |\n| Requirement-to-task coverage | 100% |\n",
    )
    assert scan_reason(tmp_path, "analyze") is None


def test_a_measurement_row_alone_is_no_coverage(tmp_path: Path) -> None:
    """A percentage isn't one of the four statuses, so a table holding only it
    shows no pass was read."""
    _write(
        tmp_path, "analyze",
        "- Verdict: satisfied\n\n| Pass | Status |\n| --- | --- |\n"
        "| Requirement-to-task coverage | 100% |\n",
    )
    assert scan_reason(tmp_path, "analyze") == SCAN_NO_ROWS


# --- Story 2: a skipped scan holds the step ---------------------------------


def test_a_clarified_spec_with_no_scan_holds_clarify(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The case the replaced record was about: a run told to choose its own
    answers writes `## Clarifications` whether or not it scanned."""
    feature = spec_tree("design.md", content={"spec.md": CLEAN_SPEC}, scans=False)
    clarify = _step(feature, tmp_path, "clarify")
    assert clarify.state == "in_progress"
    assert clarify.annotation == SCAN_MISSING


def test_a_held_clarify_routes_back_to_clarify_automatically(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """PR-002. The text sits in the display, not the reason, because a reason
    on the current step marks it blocked and never automatic. An unattended run
    has to be sent back to write the scan, not stopped."""
    feature = spec_tree("design.md", content={"spec.md": CLEAN_SPEC}, scans=False)
    report = build_report(feature, tmp_path, tmp_path)
    assert (report.current, report.next_command, report.auto) == (
        "clarify", "/speckit.clarify", True,
    )


def test_a_written_scan_lets_clarify_finish(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    feature = spec_tree("design.md", content={"spec.md": CLEAN_SPEC}, scans=False)
    write_scan(feature, "clarify")
    assert _step(feature, tmp_path, "clarify").state == "done"


def test_an_analysis_report_with_no_scan_holds_analyze(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    feature = spec_tree(
        "design.md", "tasks.md", REPORT_NAME,
        content={"spec.md": CLEAN_SPEC, "plan.md": CLEAN_PLAN,
                 "checklists/analysis-report.md": "a report\n"},
    )
    spec_scan(feature, "analyze").unlink()
    _review_report(feature)
    write_scan(feature, "plan-review")
    analyze = _step(feature, tmp_path, "analyze")
    assert analyze.state == "in_progress"
    assert analyze.annotation == SCAN_MISSING


def test_a_clean_plan_review_with_no_scan_holds_the_pass(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    feature = spec_tree("design.md", content={"spec.md": CLEAN_SPEC, "plan.md": CLEAN_PLAN})
    _review_report(feature)
    plan = _step(feature, tmp_path, "plan")
    review = next(p for p in plan.sub_steps if p.name == "plan-review")
    assert review.state == "in_progress"
    assert review.annotation == SCAN_MISSING


# --- Story 3: a feature already past the step isn't sent back ---------------


def test_an_older_feature_with_a_plan_reads_clarify_done_with_a_warning(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """A feature planned before #598 has its clarify scan under the arch root.
    Once `plan.md` exists, the missing scan is a warning with a fix line, the
    trade clarify already makes for a plan written before clarify existed."""
    feature = spec_tree(
        "design.md", content={"spec.md": CLEAN_SPEC, "plan.md": CLEAN_PLAN}, scans=False
    )
    clarify = _step(feature, tmp_path, "clarify")
    assert clarify.state == "done"
    assert clarify.reason == SCAN_MISSING
    assert clarify.remedy == "  run /speckit.clarify"


def test_an_older_feature_with_a_delivery_plan_reads_analyze_done(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    feature = spec_tree(
        "design.md", "tasks.md", "delivery.md",
        content={"spec.md": CLEAN_SPEC, "plan.md": CLEAN_PLAN,
                 "checklists/analysis-report.md": "a report\n"},
        scans=False,
    )
    analyze = _step(feature, tmp_path, "analyze")
    assert analyze.state == "done"
    assert analyze.reason == SCAN_MISSING
    assert analyze.remedy == "  run /speckit.analyze"


def test_an_older_feature_with_every_task_closed_reads_analyze_done(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """Decompose reads skipped, not pending, when every task is closed and no
    `delivery.md` was written. Analyze checked only for `delivery.md`, so a
    feature finished before #598 was sent back to `/speckit.analyze` after
    implement."""
    feature = spec_tree(
        "design.md",
        content={"spec.md": CLEAN_SPEC, "plan.md": CLEAN_PLAN, "tasks.md": "- [x] T001 done\n",
                 "checklists/analysis-report.md": "a report\n"},
        scans=False,
    )
    analyze = _step(feature, tmp_path, "analyze")
    assert analyze.state == "done"
    assert analyze.reason == SCAN_MISSING
    assert analyze.remedy == "  run /speckit.analyze"


def test_an_open_task_with_no_delivery_plan_holds_analyze_on_its_scan(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The closed-tasks arm must not open for a feature still being built. The
    other hold tests stage a `tasks.md` with no checkbox at all, so none of them
    would notice the arm reading one open box as nothing to deliver."""
    feature = spec_tree(
        "design.md",
        content={"spec.md": CLEAN_SPEC, "plan.md": CLEAN_PLAN,
                 "tasks.md": "- [x] T001 done\n- [ ] T002 open\n",
                 "checklists/analysis-report.md": "a report\n"},
        scans=False,
    )
    analyze = _step(feature, tmp_path, "analyze")
    assert analyze.state == "in_progress"
    assert analyze.annotation == SCAN_MISSING


def test_an_older_feature_with_tasks_reads_the_plan_review_done(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    feature = spec_tree(
        "design.md", "tasks.md", content={"spec.md": CLEAN_SPEC, "plan.md": CLEAN_PLAN}
    )
    _review_report(feature)
    plan = _step(feature, tmp_path, "plan")
    review = next(p for p in plan.sub_steps if p.name == "plan-review")
    assert review.state == "done"
