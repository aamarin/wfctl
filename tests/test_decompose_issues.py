"""decompose's definition of done includes the issues its plan promises (#8).

`delivery.md` existing used to be the whole check, and the file is written
*before* the issues exist by design — creating them is outward-facing and waits
for a human. So the one state these tests care about is the middle one: a plan
on disk whose Issue Grouping Map still carries placeholders. It read `done`, and
`implement` advances unattended since #148, so a run flowed into implementation
against PRs with no issue to close.

Observed on PFMS `490-budget-actuals-wiring`: three `_(TBD)_` rows, `decompose ●`,
`implement ▶ 0/42 done`. The fixtures below are that file's shape.

Every test configures a tracker first. That is the precondition, not fixture
noise — a repo that declined one has no key to wait for, and the last test here
is the one that pins it.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from tests.conftest import CLEAN_SPEC
from wfctl._pipeline import _infer_steps, build_report

# The two halves of the PFMS file. Two shapes are deliberate. The `PR
# Decomposition` table comes first in every delivery plan and its rows carry
# `#1`, `#2`, `#3` — a scan that finds the Issue Grouping Map by "the first
# table" reads those and sees three keyed rows. And the template puts prose
# between the heading and the table, which is the shape the parser meets most
# often and the one a heading-then-table fixture would never exercise.
_HEADER = """# Delivery Plan: Budget Actuals Wiring (490)

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| #1 | T001-T014 | `budget.py` (modified) | M | tests green |
| #2 | T015-T028 | `actuals.py` (created) | M | #1 merged |
| #3 | T029-T042 | `wiring.py` (created) | S | #2 merged |

## Issue Grouping Map

The **Issue** column must lead with the tracker's native key exactly as returned
— no other format. GitHub: `#251`.

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


def _use_tracker(repo_root: Path, pattern: str | None = None) -> None:
    """Give the repo a tracker, optionally one whose keys are not GitHub's."""
    config: dict[str, object] = {"verbs": {"list": ["gh", "issue", "list"]}}
    if pattern is not None:
        config["key_pattern"] = pattern
    trackers = repo_root / ".agents" / "trackers"
    trackers.mkdir(parents=True, exist_ok=True)
    (trackers / "custom.json").write_text(json.dumps(config))
    (repo_root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "custom"}))


def _feature(spec_tree: Callable[..., Path], delivery: str, tasks: str = "- [ ] T001 open\n") -> Path:
    """A feature staged all the way up to decompose, holding `delivery`.

    Every upstream artifact, not just the one under test: `_infer_steps`
    cascades, so a feature carrying only `delivery.md` reports decompose
    `pending` for a reason that has nothing to do with its issues.
    """
    return spec_tree(
        "design.md", "plan.md", "checklists/analysis-report.md",
        content={"spec.md": CLEAN_SPEC, "tasks.md": tasks, "delivery.md": delivery},
    )


def _states(spec_dir: Path, repo_root: Path) -> dict[str, str]:
    return {s.name: s.state for s in _infer_steps(spec_dir, repo_root)}


def _annotation(spec_dir: Path, repo_root: Path, step: str) -> str | None:
    return next(s.annotation for s in _infer_steps(spec_dir, repo_root) if s.name == step)


def test_a_plan_whose_issues_all_carry_a_key_is_done(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The state the old check got right, pinned so the new one cannot lose it."""
    _use_tracker(tmp_path)
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
    _use_tracker(tmp_path)
    feature = _feature(spec_tree, _delivery("_(TBD)_", "_(TBD)_", "_(TBD)_"))
    assert _states(feature, tmp_path)["decompose"] == "in_progress"


def test_a_placeholder_that_happens_to_contain_a_digit_is_not_a_key(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """`_(TBD)_ (Issue 1)` — the defect surviving inside the fix, found in review.

    No skill defines how a placeholder is spelled, and the template's own row
    label is `(Issue A)`, one keystroke from `(Issue 1)`. Searching the cell, the
    default `\\d+` matched that `1` and the row read as a created issue: the exact
    state this check exists to catch, in a form the first three tests miss.
    The key must therefore *lead* the cell, which is what the template mandates.
    """
    _use_tracker(tmp_path)
    feature = _feature(spec_tree, _delivery("_(TBD)_ (Issue 1)", "TBD #", "{issue-key} (Issue C)"))
    assert _states(feature, tmp_path)["decompose"] == "in_progress"
    assert _annotation(feature, tmp_path, "decompose") == "3 issue rows without a key"


def test_the_step_says_how_many_rows_are_missing_a_key(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """`in_progress` alone does not say what is undone, and the count is the work.

    The wording is what was read rather than what it implies: the rows are the
    whole evidence, and "issues not created" would be a claim about a tracker
    this check never contacts.
    """
    _use_tracker(tmp_path)
    two = _feature(spec_tree, _delivery("#251", "_(TBD)_", "_(TBD)_"))
    assert _annotation(two, tmp_path, "decompose") == "2 issue rows without a key"

    one = _feature(spec_tree, _delivery("#251", "#252", "_(TBD)_"))
    assert _annotation(one, tmp_path, "decompose") == "1 issue row without a key"


def test_a_plan_with_no_issue_grouping_map_is_left_alone(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """A delivery plan predating the table is not evidence that issues are missing.

    The check has one input, the file's own text. Absent a map there is nothing
    to read, and inventing a verdict from that would block every plan written
    before the format existed.
    """
    _use_tracker(tmp_path)
    feature = _feature(spec_tree, "# Delivery Plan\n\nOne PR, one issue.\n")
    assert _states(feature, tmp_path)["decompose"] == "done"


def test_the_key_shape_comes_from_the_tracker_not_from_github(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """A hardcoded `\\d+` is right for GitHub and silently wrong everywhere else.

    Under a Jira-shaped `key_pattern`, `PROJ-4` is a created issue and `#251` is
    not one — the reverse of the default's answer for the same two files.
    `spec_tree` builds one directory, so the second plan replaces the first;
    each assertion reads the state its own line just wrote.
    """
    _use_tracker(tmp_path, r"[A-Z]+-\d+")

    keyed = _feature(spec_tree, _delivery("PROJ-4", "PROJ-5", "PROJ-6"))
    assert _states(keyed, tmp_path)["decompose"] == "done"

    numeric = _feature(spec_tree, _delivery("#251", "#252", "#253"))
    assert _states(numeric, tmp_path)["decompose"] == "in_progress"


def test_a_repo_with_no_tracker_is_never_waiting_for_a_key(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """Declining a tracker is a recorded choice (`"tracker": null`), not an omission.

    Nothing in such a repo creates an issue, so a placeholder there can never
    gain a key. Gating on one strands the pipeline at decompose for the life of
    the repo — `load_key_pattern` hands back GitHub's `\\d+` regardless, which is
    why this reads the choice itself rather than the pattern.
    """
    (tmp_path / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": None}))
    feature = _feature(spec_tree, _delivery("_(TBD)_", "_(TBD)_", "_(TBD)_"))

    assert _states(feature, tmp_path)["decompose"] == "done"
    assert _annotation(feature, tmp_path, "decompose") is None


def test_a_half_decomposed_feature_is_not_routed_to_implement(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The consequence, and the reason the state name alone is not the fix.

    `_current_step_name` returns the first step that still blocks, so decompose
    reading `in_progress` is what keeps `next_command` off `/speckit.implement`
    — which #148 made an unattended run take without a human in between.
    """
    _use_tracker(tmp_path)
    feature = _feature(spec_tree, _delivery("_(TBD)_", "_(TBD)_", "_(TBD)_"))
    report = build_report(feature, tmp_path, tmp_path)
    assert (report.current, report.next_command) == ("decompose", "/speckit.decompose")


def test_a_story_that_already_shipped_is_not_sent_back_to_decompose(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The trap the gate opened, found in review: a finished story that cannot finish.

    With every task ticked, `implement` reads `done` and decompose was still
    blocking — so `current` stayed `decompose`, `next` pointed at a command that
    does not backfill a table, and `/end-session` was unreachable. The likeliest
    way to reach it is an upgrade: a feature shipped long ago whose map nobody
    filled in. The annotation survives, because the rows really are unkeyed; only
    the blocking stops.
    """
    _use_tracker(tmp_path)
    feature = _feature(
        spec_tree,
        _delivery("_(TBD)_", "_(TBD)_", "_(TBD)_"),
        tasks="- [x] T001 done\n",
    )
    report = build_report(feature, tmp_path, tmp_path)

    assert _states(feature, tmp_path)["decompose"] == "done"
    assert _annotation(feature, tmp_path, "decompose") == "3 issue rows without a key"
    assert (report.current, report.next_command) == (None, None)


def test_a_key_pattern_that_opens_with_an_inline_flag_does_not_crash_status(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """`(?i)PROJ-\\d+` — a valid pattern that `wfctl status` used to die on.

    `load_key_pattern` accepts it, because it compiles on its own. Wrapping it as
    `#?(?:...)` to make the `#` optional then raises "global flags not at the
    start of the expression", and nothing catches it: `status` and `resume` exit
    on a traceback for every feature that has a delivery plan, rather than
    reporting a wrong state. So the `#` comes off the cell, never around the
    pattern — which also keeps the flag doing its job, matched here by the
    lowercase `proj-4`.
    """
    _use_tracker(tmp_path, r"(?i)PROJ-\d+")

    keyed = _feature(spec_tree, _delivery("proj-4", "PROJ-5", "PROJ-6"))
    assert _states(keyed, tmp_path)["decompose"] == "done"

    mixed = _feature(spec_tree, _delivery("proj-4", "_(TBD)_", "PROJ-6"))
    assert _states(mixed, tmp_path)["decompose"] == "in_progress"


def test_a_half_decomposed_feature_does_not_advance_unattended(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """#240. The route above is not the halt: `speckit-orchestrate` reads `auto`
    off the payload and never reads `state`.

    Before decompose advanced without a prompt, `auto` was `false` on every
    branch of this step and the command was the only answer worth pinning. It is
    now `true` for a plan that has yet to be written, so the flag is what
    separates "run decompose again" from "stop and ask" — and re-running
    `/speckit.decompose` does not backfill a table anyway.
    """
    _use_tracker(tmp_path)
    feature = _feature(spec_tree, _delivery("_(TBD)_", "_(TBD)_", "_(TBD)_"))
    assert build_report(feature, tmp_path, tmp_path).auto is False


def test_a_feature_with_no_delivery_plan_yet_advances_unattended(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The positive half, and the only branch of decompose that returns `auto: true`.

    Writing the plan is the step's own work, and nothing about it needs a human
    — which is what #8 established and what left the table's `False` encoding a
    reason that had already been removed. Asserting the negative case alone would
    pass against a `decompose` arm hardcoded to `False`, undoing the flip
    entirely; 87d9205 is that mutation surviving the suite one step later.
    """
    _use_tracker(tmp_path)
    feature = spec_tree(
        "design.md", "plan.md", "checklists/analysis-report.md",
        content={"spec.md": CLEAN_SPEC, "tasks.md": "- [ ] T001 open\n"},
    )
    report = build_report(feature, tmp_path, tmp_path)
    assert (report.current, report.next_command, report.auto) == (
        "decompose", "/speckit.decompose", True,
    )
