"""decompose's definition of done includes the issues its plan promises (#8).

`delivery.md` existing used to be the whole check, and the file is written
*before* the issues exist by design — creating them is outward-facing and waits
for a human. So the one state these tests care about is the middle one: a plan
on disk whose Issue Grouping Map still carries placeholders. It read `done`, and
`implement` advances unattended since #148, so a run flowed into implementation
against PRs with no issue to close.

Observed on PFMS `490-budget-actuals-wiring`: three `_(TBD)_` rows, `decompose ●`,
`implement ▶ 0/42 done`. The fixtures below are that file's shape.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from tests.conftest import CLEAN_SPEC
from wfctl._pipeline import _infer_steps, build_report

# The two halves of the PFMS file. The `PR Decomposition` table comes first in
# every delivery plan and its rows carry `#1`, `#2`, `#3` — a scan that finds the
# Issue Grouping Map by "the first table" reads those and sees three keyed rows.
_HEADER = """# Delivery Plan: Budget Actuals Wiring (490)

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| #1 | T001-T014 | `budget.py` (modified) | M | tests green |
| #2 | T015-T028 | `actuals.py` (created) | M | #1 merged |
| #3 | T029-T042 | `wiring.py` (created) | S | #2 merged |

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
"""

_TRAILER = """
**Grouping pattern**: Phase-grouped
**Rationale**: Infrastructure work with no clear user stories.
"""


def _delivery(*issue_cells: str) -> str:
    rows = "".join(
        f"| {cell} | T{n:03d}-T{n + 13:03d} | `[490] group {i}` | 3h | PR #{i} |\n"
        for i, (cell, n) in enumerate(zip(issue_cells, range(1, 100, 14)), start=1)
    )
    return _HEADER + rows + _TRAILER


def _feature(spec_tree: Callable[..., Path], delivery: str) -> Path:
    """A feature staged all the way up to decompose, holding `delivery`.

    Every upstream artifact, not just the one under test: `_infer_steps`
    cascades, so a feature carrying only `delivery.md` reports decompose
    `pending` for a reason that has nothing to do with its issues.
    """
    return spec_tree(
        "design.md", "plan.md", "checklists/analysis-report.md",
        content={
            "spec.md": CLEAN_SPEC,
            "tasks.md": "- [ ] T001 open\n",
            "delivery.md": delivery,
        },
    )


def _states(spec_dir: Path, repo_root: Path) -> dict[str, str]:
    return {s.name: s.state for s in _infer_steps(spec_dir, repo_root)}


def _annotation(spec_dir: Path, repo_root: Path, step: str) -> str | None:
    return next(s.annotation for s in _infer_steps(spec_dir, repo_root) if s.name == step)


def _use_tracker_pattern(repo_root: Path, pattern: str) -> None:
    trackers = repo_root / ".agents" / "trackers"
    trackers.mkdir(parents=True, exist_ok=True)
    (trackers / "custom.json").write_text(json.dumps({"key_pattern": pattern, "verbs": {}}))
    (repo_root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "custom"}))


def test_a_plan_whose_issues_all_carry_a_key_is_done(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The state the old check got right, pinned so the new one cannot lose it."""
    feature = _feature(spec_tree, _delivery("#251", "#252", "#253"))
    assert _states(feature, tmp_path)["decompose"] == "done"


def test_a_plan_whose_issues_were_never_created_is_still_in_progress(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The defect itself: three `_(TBD)_` rows that used to report a finished step.

    Every row here also carries `PR #1`, `PR #2`, `PR #3` in `Closes With`, which
    is why the check reads the `Issue` cell and not the row — searching the whole
    row finds those and calls the file complete.
    """
    feature = _feature(spec_tree, _delivery("_(TBD)_", "_(TBD)_", "_(TBD)_"))
    assert _states(feature, tmp_path)["decompose"] == "in_progress"


def test_the_step_says_how_many_issues_are_missing(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """`in_progress` alone does not say what is undone, and the count is the work.

    Without it the reader is told decompose is unfinished by a step whose file is
    on disk — the annotation is the only place that distinguishes "half done"
    from "not started".
    """
    feature = _feature(spec_tree, _delivery("#251", "_(TBD)_", "_(TBD)_"))
    assert _annotation(feature, tmp_path, "decompose") == "plan written, 2 issues not created"


def test_a_plan_with_no_issue_grouping_map_is_left_alone(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """A delivery plan predating the table is not evidence that issues are missing.

    The check has one input, the file's own text. Absent a map there is nothing
    to read, and inventing a verdict from that would block every plan written
    before the format existed.
    """
    feature = _feature(spec_tree, "# Delivery Plan\n\nOne PR, one issue.\n")
    assert _states(feature, tmp_path)["decompose"] == "done"


def test_the_key_shape_comes_from_the_tracker_not_from_github(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """A hardcoded `\\d+` is right for GitHub and silently wrong everywhere else.

    Under a Jira-shaped `key_pattern`, `PROJ-4` is a created issue and `#251` is
    not one — the reverse of the default's answer for the same two files.
    """
    _use_tracker_pattern(tmp_path, r"[A-Z]+-\d+")

    keyed = _feature(spec_tree, _delivery("PROJ-4", "PROJ-5", "PROJ-6"))
    assert _states(keyed, tmp_path)["decompose"] == "done"

    numeric = _feature(spec_tree, _delivery("#251", "#252", "#253"))
    assert _states(numeric, tmp_path)["decompose"] == "in_progress"


def test_a_half_decomposed_feature_is_not_routed_to_implement(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The consequence, and the reason the state name alone is not the fix.

    `_current_step_name` returns the first step that still blocks, so decompose
    reading `in_progress` is what keeps `next_command` off `/speckit.implement`
    — which #148 made an unattended run take without a human in between.
    """
    feature = _feature(spec_tree, _delivery("_(TBD)_", "_(TBD)_", "_(TBD)_"))
    report = build_report(feature, tmp_path, tmp_path)
    assert (report.current, report.next_command) == ("decompose", "/speckit.decompose")
