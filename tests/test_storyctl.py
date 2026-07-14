"""Tests for wfctl pipeline inference and status/next commands (migrated from pfms test_storyctl.py)."""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl._pipeline import _infer_steps as _infer_pipeline
from wfctl.cli import app

runner = CliRunner()
NS = types.SimpleNamespace


# ─── _infer_pipeline helpers ─────────────────────────────────────────────────

def _symbols(steps) -> list[str]:
    return [s.symbol for s in steps]


def _names(steps) -> list[str]:
    return [s.name for s in steps]


STEP_NAMES = [
    "brainstorm", "specify", "clarify", "plan",
    "tasks", "analyze", "decompose", "implement",
]


class TestInferPipeline:
    def test_step_names_always_present(self, storyctl_dir: NS) -> None:
        steps = _infer_pipeline(None, storyctl_dir.repo_root)
        assert _names(steps) == STEP_NAMES

    # brainstorm
    def test_brainstorm_done_when_agent_spec_exists(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[0].symbol == "●"

    def test_brainstorm_skipped_when_agent_spec_absent(self, storyctl_dir: NS) -> None:
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[0].symbol == "–"

    # specify
    def test_specify_done_when_spec_md_has_no_markers(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="# Spec\n\nNo markers here.\n")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[1].symbol == "●"

    def test_specify_in_progress_when_markers_present(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact(
            "specify", content="# Spec\n\n[NEEDS CLARIFICATION] something\n"
        )
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[1].symbol == "▶"

    # clarify inherits specify
    def test_clarify_inherits_specify_done(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="# Spec\n\nClean.\n")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[2].symbol == "●"

    def test_clarify_inherits_specify_in_progress(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="[NEEDS CLARIFICATION] fix me\n")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[2].symbol == "▶"

    # plan
    def test_plan_done_when_plan_md_exists(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[3].symbol == "●"

    def test_plan_not_started_when_absent(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[3].symbol == "○"

    # tasks
    def test_tasks_done_when_tasks_md_exists_no_open_checkboxes(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="- [x] task 1\n- [x] task 2\n")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[4].symbol == "●"

    def test_tasks_done_when_no_checkboxes(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="# Tasks\n\nno checkboxes here\n")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[4].symbol == "●"

    def test_tasks_done_when_open_checkboxes(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="- [x] done\n- [ ] not done\n")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[4].symbol == "●"

    def test_tasks_not_started_when_absent(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[4].symbol == "○"

    # analyze
    def test_analyze_done_when_requirements_exists(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="- [x] t1\n")
        storyctl_dir.make_spec_artifact("analyze")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[5].symbol == "●"

    def test_analyze_not_started_when_absent(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="- [x] t1\n")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[5].symbol == "○"

    # decompose
    def test_decompose_done_when_delivery_exists(self, storyctl_dir: NS) -> None:
        for step in ["brainstorm", "analyze"]:
            storyctl_dir.make_spec_artifact(step)
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="- [x] t1\n")
        storyctl_dir.make_spec_artifact("decompose")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[6].symbol == "●"

    def test_decompose_skipped_when_absent_and_all_tasks_done(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="- [x] t1\n- [x] t2\n")
        storyctl_dir.make_spec_artifact("analyze")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[6].symbol == "–"

    def test_decompose_not_started_when_absent_and_tasks_incomplete(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="- [ ] t1\n")
        storyctl_dir.make_spec_artifact("analyze")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[6].symbol == "○"

    # implement
    def test_implement_done_when_all_tasks_checked(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="- [x] t1\n- [x] t2\n")
        storyctl_dir.make_spec_artifact("analyze")
        storyctl_dir.make_spec_artifact("decompose")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[7].symbol == "●"

    def test_implement_in_progress_when_open_tasks(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="- [x] t1\n- [ ] t2\n")
        storyctl_dir.make_spec_artifact("analyze")
        storyctl_dir.make_spec_artifact("decompose")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[7].symbol == "▶"

    def test_implement_done_when_sentinel_present(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="- [x] t1\n- [ ] t2\n")
        storyctl_dir.make_spec_artifact("analyze")
        storyctl_dir.make_spec_artifact("decompose")
        sentinel = storyctl_dir.spec_dir / "checklists" / "implement-complete.md"
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text("Implementation complete: 2026-07-08\n")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[7].symbol == "●"

    # cascading ○
    def test_cascade_after_first_non_done_step(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="[NEEDS CLARIFICATION] fix\n")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[1].symbol == "▶"
        assert steps[2].symbol == "▶"
        assert steps[3].symbol == "○"
        assert steps[4].symbol == "○"
        assert steps[5].symbol == "○"
        assert steps[6].symbol == "○"
        assert steps[7].symbol == "○"

    def test_no_spec_dir_all_steps_not_started(self, storyctl_dir: NS) -> None:
        steps = _infer_pipeline(None, storyctl_dir.repo_root)
        assert all(s.symbol == "○" for s in steps)

    def test_zero_byte_file_treated_as_absent(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        (storyctl_dir.spec_dir / "plan.md").write_text("")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[3].symbol == "○"

    def test_specify_done_when_marker_in_inline_code(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact(
            "specify", content="Use `[NEEDS CLARIFICATION]` as the marker pattern.\n"
        )
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[1].symbol == "●"

    def test_specify_done_when_marker_in_fenced_block(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact(
            "specify",
            content="```\nExample: [NEEDS CLARIFICATION] goes here\n```\n",
        )
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[1].symbol == "●"

    def test_no_cascade_from_in_progress_step(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="[NEEDS CLARIFICATION] fix\n")
        storyctl_dir.make_spec_artifact("plan")
        steps = _infer_pipeline(storyctl_dir.spec_dir, storyctl_dir.repo_root)
        assert steps[1].symbol == "▶"
        assert steps[3].symbol == "●"


# ─── wfctl status ────────────────────────────────────────────────────────────

class TestStatus:
    def test_status_output_fully_done(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="- [x] t1\n")
        storyctl_dir.make_spec_artifact("analyze")
        storyctl_dir.make_spec_artifact("decompose")
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        for name in STEP_NAMES:
            assert name in result.output
        assert "●" in result.output

    def test_status_missing_spec_dir_exits_zero(self, storyctl_dir: NS) -> None:
        import shutil
        shutil.rmtree(str(storyctl_dir.spec_dir))
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "○" in result.output
        assert "no spec dir found" in result.output

    def test_status_updates_current_json_workflow_step(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="[NEEDS CLARIFICATION] fix\n")
        current_json = storyctl_dir.agent_dir / "current.json"
        current_json.write_text(json.dumps({"workflow_step": "old", "worktree": "418-storyctl"}))
        runner.invoke(app, ["status"])
        data = json.loads(current_json.read_text())
        assert data["workflow_step"] != "old"
        assert data["workflow_step"] in [
            "specify", "clarify", "brainstorm", "plan", "tasks",
            "analyze", "decompose", "implement", "complete",
        ]


# ─── wfctl next (was storyctl resume) ────────────────────────────────────────

class TestNext:
    def test_next_writes_next_step_for_in_progress(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        runner.invoke(app, ["next"])
        next_step_md = storyctl_dir.agent_dir / "next-step.md"
        assert next_step_md.exists()
        content = next_step_md.read_text()
        assert "/speckit.plan" in content

    def test_next_auto_true_for_plan(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        runner.invoke(app, ["next"])
        content = (storyctl_dir.agent_dir / "next-step.md").read_text()
        assert "auto: true" in content

    def test_next_auto_false_for_clarify(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="[NEEDS CLARIFICATION] something\n")
        runner.invoke(app, ["next"])
        content = (storyctl_dir.agent_dir / "next-step.md").read_text()
        assert "auto: false" in content

    def test_next_auto_false_for_analyze(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="- [x] t1\n")
        runner.invoke(app, ["next"])
        content = (storyctl_dir.agent_dir / "next-step.md").read_text()
        assert "/speckit.analyze" in content
        assert "auto: false" in content

    def test_next_auto_true_for_tasks(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        runner.invoke(app, ["next"])
        content = (storyctl_dir.agent_dir / "next-step.md").read_text()
        assert "/speckit.tasks" in content
        assert "auto: true" in content

    def test_next_writes_completion_when_all_done(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        storyctl_dir.make_spec_artifact("plan")
        storyctl_dir.make_spec_artifact("tasks", content="- [x] t1\n")
        storyctl_dir.make_spec_artifact("analyze")
        storyctl_dir.make_spec_artifact("decompose")
        runner.invoke(app, ["next"])
        content = (storyctl_dir.agent_dir / "next-step.md").read_text()
        assert "complete" in content.lower() or "PR" in content or "end-session" in content

    def test_next_no_spec_dir_suggests_specify(self, storyctl_dir: NS) -> None:
        import shutil
        shutil.rmtree(str(storyctl_dir.spec_dir))
        runner.invoke(app, ["next"])
        content = (storyctl_dir.agent_dir / "next-step.md").read_text()
        assert "/speckit.specify" in content

    def test_next_creates_agent_dir_if_missing(self, storyctl_dir: NS) -> None:
        import shutil
        shutil.rmtree(str(storyctl_dir.agent_dir))
        assert not storyctl_dir.agent_dir.exists()
        runner.invoke(app, ["next"])
        assert (storyctl_dir.agent_dir / "next-step.md").exists()

    def test_next_includes_continuation_line(self, storyctl_dir: NS) -> None:
        storyctl_dir.make_spec_artifact("brainstorm")
        storyctl_dir.make_spec_artifact("specify", content="clean\n")
        runner.invoke(app, ["next"])
        content = (storyctl_dir.agent_dir / "next-step.md").read_text()
        assert "Run this command to continue." in content
