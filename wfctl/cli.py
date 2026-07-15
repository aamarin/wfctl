"""wfctl CLI — workflow state manager for agent sessions."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console

from wfctl._paths import get_repo_root, resolve_agent_dir, resolve_branch, resolve_spec_dir

app = typer.Typer(no_args_is_help=True)
console = Console()


def _resolve_context() -> tuple[Path, Path, str, str]:
    """Return (agent_dir, repo_root, branch, issue); exits on error."""
    try:
        repo_root = get_repo_root()
    except SystemExit as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)
    branch = resolve_branch(repo_root)
    issue = branch.split("-")[0] if "-" in branch and branch.split("-")[0].isdigit() else "unknown"
    agent_dir = resolve_agent_dir(repo_root, branch)
    return agent_dir, repo_root, branch, issue


@app.command("start")
def start_cmd(force: bool = typer.Option(False, "--force", help="Overwrite existing state")) -> None:
    """Initialize agent session context."""
    from wfctl import _session

    agent_dir, repo_root, branch, issue = _resolve_context()
    current_json = agent_dir / "current.json"
    current_md = agent_dir / "current.md"

    # Check for corrupted state before idempotency check
    if current_json.exists():
        try:
            json.loads(current_json.read_text())
        except json.JSONDecodeError:
            console.print(f"[red]✗ current.json is corrupted: {current_json}[/red]")
            raise typer.Exit(1)

    if current_json.exists() and current_md.exists() and not force:
        console.print("ℹ Already initialized (use --force to reset)")
        return

    spec_dir = resolve_spec_dir(branch, repo_root)
    _session.start(agent_dir, spec_dir, repo_root, branch, issue, force)

    data = json.loads((agent_dir / "current.json").read_text())
    console.print(
        f"[green]✓[/green] Session started — step: {data['workflow_step']}, "
        f"next: {data['next_command'] or '(none)'}"
    )


@app.command("status")
def status_cmd() -> None:
    """Show pipeline progress."""
    from wfctl._pipeline import steps_display
    from wfctl._paths import resolve_spec_dir
    from wfctl._io import write_json_atomic

    agent_dir, repo_root, branch, issue = _resolve_context()
    spec_dir = resolve_spec_dir(branch, repo_root)

    _SYMBOL_STYLE = {"●": "green", "▶": "yellow", "○": "dim", "–": "dim"}

    console.print(f"[bold]#{issue}  {branch}[/bold]")
    console.print("[dim]" + "─" * 36 + "[/dim]")
    if spec_dir is None:
        console.print("[dim](no spec dir found)[/dim]")

    steps = steps_display(spec_dir, repo_root)
    for step in steps:
        name = step["name"].ljust(12)
        name_fmt = f"[bold]{name}[/bold]" if step["is_current"] else name
        color = _SYMBOL_STYLE.get(step["symbol"], "")
        sym_fmt = f"[{color}]{step['symbol']}[/{color}]" if color else step["symbol"]
        ann = f"  [dim]{step['annotation']}[/dim]" if step["annotation"] else ""
        marker = "  [cyan]← current[/cyan]" if step["is_current"] else ""
        console.print(f"{name_fmt} {sym_fmt}{ann}{marker}")

    current_json = agent_dir / "current.json"
    if current_json.exists():
        current_name = next((s["name"] for s in steps if s["is_current"]), "complete")
        data = json.loads(current_json.read_text())
        data["workflow_step"] = current_name
        write_json_atomic(current_json, data)


@app.command("next")
def next_cmd() -> None:
    """Write next actionable step to next-step.md."""
    from wfctl._pipeline import _infer_steps, _current_step_name, next_step_content
    from wfctl._io import append_event

    agent_dir, repo_root, branch, _ = _resolve_context()
    spec_dir = resolve_spec_dir(branch, repo_root)
    steps = _infer_steps(spec_dir, repo_root)
    step_name = _current_step_name(steps)

    if spec_dir is None:
        command, auto = "/speckit.specify", False
        step_name = "specify"
    else:
        command, auto = next_step_content(step_name)

    next_step_md = agent_dir / "next-step.md"
    if command:
        auto_str = "true" if auto else "false"
        content = f"Next step: {command}\nauto: {auto_str}\nRun this command to continue.\n"
        console.print(f"→ Next step: {command} (auto: {auto_str})")
    else:
        content = "Story complete. Open PR or run /end-session.\n"
        console.print("Story complete — open PR or run `/end-session`.")

    next_step_md.write_text(content)
    append_event(agent_dir, "next", command=command or "complete", auto=auto, step=step_name)


@app.command("resume")
def resume_cmd() -> None:
    """Re-infer pipeline step, write next-step.md, and print current state."""
    from wfctl import _session
    from wfctl._pipeline import next_step_content
    from wfctl._io import append_event

    agent_dir, repo_root, branch, _ = _resolve_context()

    if not (agent_dir / "current.json").exists():
        console.print("[red]✗ No current state. Run `wfctl start` first.[/red]")
        raise typer.Exit(1)

    spec_dir = resolve_spec_dir(branch, repo_root)
    data = _session.resume(agent_dir, spec_dir, repo_root)
    step_name = data.get("workflow_step", "?")

    if spec_dir is None:
        command, auto = "/speckit.specify", False
    else:
        command, auto = next_step_content(step_name)

    next_step_md = agent_dir / "next-step.md"
    if command:
        auto_str = "true" if auto else "false"
        next_step_md.write_text(f"Next step: {command}\nauto: {auto_str}\nRun this command to continue.\n")
        console.print(f"[green]↺[/green] Resumed — step: {step_name}, next: {command} (auto: {auto_str})")
    else:
        next_step_md.write_text("Story complete. Open PR or run /end-session.\n")
        console.print(f"[green]↺[/green] Resumed — step: {step_name} — story complete.")

    append_event(agent_dir, "resume", step=step_name, command=command or "complete", auto=auto)


@app.command("end")
def end_cmd() -> None:
    """End the current session."""
    from wfctl import _session

    agent_dir, repo_root, branch, _ = _resolve_context()

    if not (agent_dir / "current.json").exists():
        console.print("[red]✗ No current state.[/red]")
        raise typer.Exit(1)

    summary_path = _session.end(agent_dir)
    console.print(f"[green]✓[/green] Session ended. Summary written to {summary_path}")


@app.command("checkpoint")
def checkpoint_cmd() -> None:
    """Save a numbered checkpoint artifact."""
    from wfctl import _session

    agent_dir, repo_root, branch, _ = _resolve_context()

    if not (agent_dir / "current.json").exists():
        console.print("[red]✗ Not initialized. Run `wfctl start` first.[/red]")
        raise typer.Exit(1)

    try:
        n = _session.checkpoint(agent_dir, repo_root)
        console.print(f"[green]✓[/green] Checkpoint {n} saved")
    except RuntimeError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)


@app.command("log")
def log_cmd() -> None:
    """Print the event log for the current session."""
    agent_dir, _, _, _ = _resolve_context()
    events_file = agent_dir / "events.jsonl"

    if not events_file.exists():
        console.print("[dim]No events logged yet.[/dim]")
        return

    _STYLES = {
        "start": "green",
        "end": "red",
        "resume": "cyan",
        "next": "yellow",
        "checkpoint": "blue",
        "promote": "magenta",
    }

    import json as _json
    for line in events_file.read_text().splitlines():
        try:
            e = _json.loads(line)
        except _json.JSONDecodeError:
            continue
        ts = e.get("ts", "")[:16].replace("T", " ")
        event = e.get("event", "?")
        color = _STYLES.get(event, "white")
        extras = {k: v for k, v in e.items() if k not in ("ts", "event")}
        detail = "  ".join(f"{k}={v}" for k, v in extras.items())
        console.print(f"[dim]{ts}[/dim]  [{color}]{event:<10}[/{color}]  [dim]{detail}[/dim]")


@app.command("state-dir")
def state_dir_cmd() -> None:
    """Print the active state directory path."""
    agent_dir, _, _, _ = _resolve_context()
    console.print(agent_dir)


@app.command("promote")
def promote_cmd() -> None:
    """Interactively promote memory candidates."""
    import os
    from wfctl import _session

    agent_dir, repo_root, branch, _ = _resolve_context()
    candidates_path = Path(
        os.environ.get("WFCTL_CANDIDATES_FILE", str(agent_dir / "memory-candidates.md"))
    )
    _session.promote(candidates_path, agent_dir)


@app.command("install-skills")
def install_skills_cmd(
    repo: str = typer.Option(
        "https://github.com/MarinVentures/wf-skills",
        "--repo",
        help="wf-skills repo URL",
    ),
    ref: str = typer.Option("main", "--ref", help="Branch or tag to install from"),
) -> None:
    """Install wf-skills (skills + commands) into the current project."""
    import shutil
    import subprocess as sp
    import tempfile

    try:
        repo_root = get_repo_root()
    except SystemExit:
        console.print("[red]✗ Not in a git repo.[/red]")
        raise typer.Exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        result = sp.run(
            ["git", "clone", "--depth=1", "--branch", ref, repo, tmp],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            console.print(f"[red]✗ Clone failed: {result.stderr.strip()}[/red]")
            raise typer.Exit(1)

        count = 0
        for src_rel, dst_rel in [
            (".agents/skills", ".agents/skills"),
            (".claude/commands", ".claude/commands"),
        ]:
            src = Path(tmp) / src_rel
            dst = repo_root / dst_rel
            if not src.exists():
                continue
            dst.mkdir(parents=True, exist_ok=True)
            for item in src.iterdir():
                dest = dst / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
                count += 1

    console.print(f"[green]✓[/green] Installed {count} item(s) from {repo}@{ref}")


if __name__ == "__main__":
    app()
