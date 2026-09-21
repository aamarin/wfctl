"""`attention` — the one field answering *does this worktree want a person and
what for* (US2).

Every assertion reads `PipelineReport.attention` directly, off a report built
by calling `build_report`, never through the CLI — proof that the condition and
its rank are derived once, in one place, and not recomputed by a view
(FR-009).
"""
from __future__ import annotations

import json
import types

from typer.testing import CliRunner

from wfctl._pipeline import build_report
from wfctl._session import record_blocked
from wfctl.cli import app

runner = CliRunner()


def _declare(storyctl_dir: types.SimpleNamespace, steps: dict) -> None:
    (storyctl_dir.repo_root / "wfctl.json").write_text(json.dumps({"steps": steps}))


def _report(storyctl_dir: types.SimpleNamespace):
    return build_report(storyctl_dir.spec_dir, storyctl_dir.repo_root, storyctl_dir.agent_dir)


def _stall_on(storyctl_dir: types.SimpleNamespace) -> None:
    """Four `resume`s with nothing touched — a real stall, on whatever step is
    current when this is called, written through the real commands rather than
    a hand-built events.jsonl (`test_stall.py`'s own end-to-end pattern)."""
    assert runner.invoke(app, ["start"]).exit_code == 0
    for _ in range(4):
        assert runner.invoke(app, ["resume"]).exit_code == 0


# --- T010: presence, and the three kinds in isolation -----------------------

def test_attention_is_present_and_none_when_nothing_holds(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    report = _report(storyctl_dir)
    assert report.attention is None


def test_a_refused_action_reports_kind_blocked(storyctl_dir: types.SimpleNamespace) -> None:
    storyctl_dir.stage_upstream_of("tasks")
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "org policy", "decompose",
    )

    report = _report(storyctl_dir)
    assert report.attention is not None
    assert report.attention.kind == "blocked"
    assert report.attention.step == "decompose"


def test_an_outstanding_manual_pass_reports_kind_manual(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Declared on `decompose` rather than `brainstorm`: `brainstorm` carries
    its own built-in `architecture`/`design-doc` passes, both automatic, and
    an unaccepted architecture record on a fresh repo leaves `architecture`
    outstanding first in the cascade — never reaching a custom pass declared
    beside it."""
    storyctl_dir.stage_upstream_of("tasks")
    _declare(storyctl_dir, {
        "decompose": [{"name": "review", "manual": True, "evidence": "ghost.md"}],
    })

    report = _report(storyctl_dir)
    assert report.attention is not None
    assert report.attention.kind == "manual"
    assert report.attention.step == "decompose"
    assert report.attention.detail == "decompose.review"


def test_a_repeated_step_with_unchanged_evidence_reports_kind_stalled(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    _stall_on(storyctl_dir)

    report = _report(storyctl_dir)
    assert report.attention is not None
    assert report.attention.kind == "stalled"
    assert report.attention.step == "implement"


# --- T011: rank, and the unreported condition stays readable ----------------

def test_blocked_outranks_stalled_and_the_stall_stays_readable(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    _stall_on(storyctl_dir)  # stall recorded against "implement"

    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "push", "refused", "decompose",
    )

    report = _report(storyctl_dir)
    assert report.attention.kind == "blocked"
    assert report.attention.step == "decompose"
    # The stall is still there, in the field it has always been in.
    assert report.stall is not None
    assert report.stall.step == "implement"


def test_blocked_outranks_manual_and_the_pass_stays_readable(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    storyctl_dir.stage_upstream_of("tasks")
    _declare(storyctl_dir, {
        "decompose": [{"name": "review", "manual": True, "evidence": "ghost.md"}],
    })
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused", "decompose",
    )

    report = _report(storyctl_dir)
    assert report.attention.kind == "blocked"
    assert report.attention.step == "decompose"

    decompose = next(s for s in report.steps if s["name"] == "decompose")
    review = next(s for s in decompose["sub_steps"] if s["name"] == "review")
    assert review["state"] == "in_progress"
    assert review["manual"] is True


def test_manual_outranks_stalled_and_the_stall_stays_readable(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    storyctl_dir.stage_upstream_of("tasks")
    _declare(storyctl_dir, {
        "decompose": [{"name": "review", "manual": True, "evidence": "ghost.md"}],
    })
    _stall_on(storyctl_dir)  # decompose is current throughout — stall lands on it too

    report = _report(storyctl_dir)
    assert report.attention.kind == "manual"
    assert report.attention.step == "decompose"
    assert report.stall is not None
    assert report.stall.step == "decompose"


# --- T012: block detail is the raw action, never the rendered sentence ------

def test_block_detail_is_the_raw_action_not_the_rendered_annotation(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    storyctl_dir.stage_upstream_of("tasks")
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "org policy", "decompose",
    )

    report = _report(storyctl_dir)
    decompose = next(s for s in report.steps if s["name"] == "decompose")

    assert report.attention.detail == "issue-comment"
    assert decompose["annotation"] == "blocked: host refused issue-comment"
    assert report.attention.detail != decompose["annotation"]

    # Reword the rendered sentence in place. `detail` was captured from
    # `StandingBlock.action` when the report was built, not read back from
    # this string — a reword here must not move it.
    decompose["annotation"] = "a completely different sentence"
    assert report.attention.detail == "issue-comment"


# --- T013: stall detail is pinned, as an observation -------------------------

def test_stall_detail_is_pinned_as_an_observation(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The wording itself is not a property any assertion can hold — only that
    it does not move without someone editing this line, which is what makes a
    later reword visible in review."""
    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    _stall_on(storyctl_dir)

    report = _report(storyctl_dir)
    assert report.attention.detail == "implement repeated 3 times with evidence unchanged"
