"""Session lifecycle operations — start, end, resume."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from wfctl._io import append_event, write_json_atomic, write_md_atomic
from wfctl._pipeline import _current_step_name, _infer_steps, next_step_content


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _render_current_md(data: dict, next_cmd: str) -> str:
    return (
        f"# Working Context: {data['branch']}\n\n"
        f"**Issue**: #{data['issue']}\n"
        f"**Status**: {data['status']}\n"
        f"**Step**: {data['workflow_step']} — next: {next_cmd or '(none)'}\n"
        f"**Updated**: {data['updated']}\n\n"
        f"## Current Task\n\n"
        f"Working on issue #{data['issue']} ({data['branch']}).\n\n"
        f"## What Has Been Done\n\n"
        f"- Session initialized.\n\n"
        f"## Next Step\n\n"
        f"{next_cmd or 'Run `wfctl status` to check current state.'}\n\n"
        f"## Active Decisions & Constraints\n\n"
        f"- (fill in)\n"
    )


def _render_session_summary(data: dict) -> str:
    now = _now_utc()
    return (
        f"# Session Summary: {now[:10]} — {data.get('branch', 'unknown')}\n\n"
        f"**Start**: {data.get('updated', now)}\n"
        f"**End**: {now}\n"
        f"**Step**: {data.get('workflow_step', 'unknown')}\n"
        f"**Status**: complete\n\n"
        f"## What We Accomplished\n\n"
        f"- (fill in)\n\n"
        f"## Next Session TODO\n\n"
        f"- [ ] (fill in)\n"
    )


def start(
    agent_dir: Path,
    spec_dir: Optional[Path],
    repo_root: Path,
    branch: str,
    issue: str,
    force: bool,
) -> None:
    """Write current.json and current.md atomically with inferred workflow_step."""
    current_json = agent_dir / "current.json"
    current_md = agent_dir / "current.md"

    if current_json.exists() and current_md.exists() and not force:
        return  # idempotent; caller handles output

    # Check for corrupted current.json — exit cleanly with error
    if current_json.exists():
        try:
            json.loads(current_json.read_text())
        except json.JSONDecodeError:
            raise ValueError(f"current.json is corrupted: {current_json}")

    # Infer pipeline step from spec artifacts
    steps = _infer_steps(spec_dir, repo_root)
    step_name = _current_step_name(steps)
    next_cmd, _ = next_step_content(step_name)

    data = {
        "issue": issue,
        "branch": branch,
        "repo": repo_root.name,
        "status": "in_progress",
        "workflow_step": step_name,
        "next_command": next_cmd,
        "updated": _now_utc(),
    }

    write_json_atomic(current_json, data)
    write_md_atomic(current_md, _render_current_md(data, next_cmd))
    append_event(agent_dir, "start", branch=branch, step=step_name)


def end(agent_dir: Path) -> Path:
    """Set status=complete, write session-summary.md; returns summary path."""
    current_json = agent_dir / "current.json"
    data = json.loads(current_json.read_text())

    summary_file = agent_dir / "session-summary.md"
    if not summary_file.exists():
        write_md_atomic(summary_file, _render_session_summary(data))

    data["status"] = "complete"
    data["updated"] = _now_utc()
    write_json_atomic(current_json, data)
    append_event(agent_dir, "end", status="complete")
    return summary_file


def resume(agent_dir: Path, spec_dir: Optional[Path], repo_root: Path) -> dict:
    """Log resume event; re-infer step from filesystem; return updated state."""
    from wfctl._pipeline import _current_step_name, _infer_steps

    current_json = agent_dir / "current.json"
    data = json.loads(current_json.read_text())
    step_name = _current_step_name(_infer_steps(spec_dir, repo_root))
    data["workflow_step"] = step_name
    write_json_atomic(current_json, data)
    append_event(agent_dir, "resume", branch=data.get("branch", ""), step=step_name)
    return data
