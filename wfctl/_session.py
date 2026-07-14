"""Session lifecycle operations — start, end, resume, checkpoint, promote."""
from __future__ import annotations

import json
import re
import subprocess
from datetime import date as _date
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from wfctl._io import append_event, write_json_atomic, write_md_atomic
from wfctl._pipeline import _current_step_name, _infer_steps, next_step_content


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_issue(branch: str) -> str:
    parts = branch.split("-")
    if parts and parts[0].isdigit():
        return parts[0]
    return "unknown"


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


def resume(agent_dir: Path) -> dict:
    """Log resume event; return current state dict."""
    current_json = agent_dir / "current.json"
    data = json.loads(current_json.read_text())
    append_event(agent_dir, "resume", branch=data.get("branch", ""), step=data.get("workflow_step", ""))
    return data


def checkpoint(agent_dir: Path, repo_root: Path) -> int:
    """Save numbered checkpoint; returns checkpoint number."""
    current_json = agent_dir / "current.json"
    data = json.loads(current_json.read_text())

    diff_result = subprocess.run(
        ["git", "diff", "HEAD"], capture_output=True, text=True, cwd=repo_root
    )
    if diff_result.returncode != 0:
        raise RuntimeError(f"Cannot capture diff: {diff_result.stderr.strip()}")

    # Find next checkpoint number by scanning existing patch files
    nums = [
        int(p.stem.split("-")[1])
        for p in agent_dir.glob("checkpoint-*.patch")
        if p.stem.split("-")[1].isdigit()
    ]
    n = max(nums, default=0) + 1

    patch_path = agent_dir / f"checkpoint-{n}.patch"
    md_path = agent_dir / f"checkpoint-{n}.md"
    patch_path.write_text(diff_result.stdout)
    write_md_atomic(md_path, f"# Checkpoint {n}\n\n**Step**: {data.get('workflow_step', '?')}\n")
    append_event(agent_dir, "checkpoint", n=n)
    return n


def promote(candidates_path: Path, agent_dir: Path) -> None:
    """Interactively promote memory candidates via Rich Prompt."""
    from datetime import date
    from rich.prompt import Prompt
    from rich.console import Console
    from wfctl._io import write_md_atomic

    console = Console()

    if not candidates_path.exists() or not candidates_path.read_text().strip():
        console.print("No candidates found.")
        return

    # Parse ###-delimited blocks
    text = candidates_path.read_text()
    candidates: list[dict] = []
    for block in text.split("\n### "):
        block = block.strip()
        if not block:
            continue
        if not block.startswith("###"):
            block = "### " + block
        lines = block.splitlines()
        title = lines[0].lstrip("#").strip()
        fields: dict = {"title": title, "raw": block}
        for line in lines[1:]:
            for field in ("Type", "Rationale", "Status"):
                prefix = f"**{field}:**"
                if line.startswith(prefix):
                    fields[field.lower()] = line[len(prefix):].strip()
        candidates.append(fields)

    if not candidates:
        console.print("No candidates found.")
        return

    needs_edit = [c for c in candidates if c.get("status") == "NEEDS_EDIT"]
    normal = [c for c in candidates if c.get("status") != "NEEDS_EDIT"]
    ordered = needs_edit + normal

    today = date.today().strftime("%Y-%m-%d")
    promoted_file = agent_dir / "promoted" / f"{today}.md"
    promoted_file.parent.mkdir(parents=True, exist_ok=True)

    approved = 0
    skipped = 0
    remaining = list(candidates)

    for i, candidate in enumerate(ordered, 1):
        console.rule(f"Candidate {i}/{len(ordered)}")
        console.print(candidate.get("raw", ""))
        choice = Prompt.ask("[A]pprove / [S]kip / [E]dit").strip().lower()

        if choice == "a":
            entry = (
                f"### {candidate['title']}\n"
                f"**Type:** {candidate.get('type', '')}\n"
                f"**Rationale:** {candidate.get('rationale', '')}\n"
            )
            with open(promoted_file, "a") as f:
                f.write(entry + "\n")
            remaining = [c for c in remaining if c is not candidate]
            approved += 1
        elif choice == "e":
            for c in remaining:
                if c["title"] == candidate["title"]:
                    c["status"] = "NEEDS_EDIT"
        else:
            skipped += 1

    # Rewrite candidates file
    blocks = []
    for c in remaining:
        lines = [f"### {c['title']}", f"**Type:** {c.get('type', '')}",
                 f"**Rationale:** {c.get('rationale', '')}"]
        if c.get("status") == "NEEDS_EDIT":
            lines.append("**Status:** NEEDS_EDIT")
        blocks.append("\n".join(lines))
    candidates_path.write_text("\n\n".join(blocks) + ("\n" if blocks else ""))

    append_event(agent_dir, "promote", approved=approved, skipped=skipped)
    console.print(f"✓ Promotion complete — {approved} approved, {skipped} skipped")
