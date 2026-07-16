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


# Where each agent reads from. Both skills and command-wrapper shims are
# agent-agnostic source content in wf-skills (.agents/skills, .agents/commands)
# — only the install destination differs per agent. wf-skills maintains one
# authored copy of each; there's no per-agent duplication to drift out of sync.
#
# Known limitation: "claude" and "none" share .agents/skills as a destination,
# so installing both in the same repo will cross-attribute backups between
# their manifest entries. Uninstalling one won't corrupt the other's files,
# just its bookkeeping. Not handled — pick one agent per repo.
_AGENT_TARGETS = {
    "claude": [
        (".agents/skills", ".agents/skills"),
        (".agents/commands", ".claude/commands"),
    ],
    "bob": [
        (".agents/skills", ".bob/skills"),
        (".agents/commands", ".bob/commands"),
    ],
    "none": [(".agents/skills", ".agents/skills")],
}

_MANIFEST_PATH = ".wf-skills-manifest.json"
_BACKUP_DIR = ".wf-skills-backup"


def _load_manifest(repo_root: Path) -> dict:
    manifest_file = repo_root / _MANIFEST_PATH
    if manifest_file.exists():
        return json.loads(manifest_file.read_text())
    return {}


def _save_manifest(repo_root: Path, manifest: dict) -> None:
    manifest_file = repo_root / _MANIFEST_PATH
    if manifest:
        manifest_file.write_text(json.dumps(manifest, indent=2) + "\n")
    elif manifest_file.exists():
        manifest_file.unlink()


@app.command("install-skills")
def install_skills_cmd(
    repo: str = typer.Option(
        "https://github.com/aamarin/wf-skills",
        "--repo",
        help="wf-skills repo URL",
    ),
    ref: str = typer.Option("main", "--ref", help="Branch or tag to install from"),
    agent: str = typer.Option(
        "claude",
        "--agent",
        help=f"Target agent: {', '.join(_AGENT_TARGETS)}",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip the confirmation prompt when files would be overwritten",
    ),
) -> None:
    """Install wf-skills (skills + commands) into the current project."""
    import datetime
    import shutil
    import subprocess as sp
    import tempfile

    targets = _AGENT_TARGETS.get(agent)
    if targets is None:
        console.print(
            f"[red]✗ Unknown agent '{agent}'. Choose from: "
            f"{', '.join(_AGENT_TARGETS)}.[/red]"
        )
        raise typer.Exit(1)

    try:
        repo_root = get_repo_root()
    except SystemExit:
        console.print("[red]✗ Not in a git repo.[/red]")
        raise typer.Exit(1)

    manifest = _load_manifest(repo_root)
    prior_items = {i["path"]: i for i in manifest.get(agent, {}).get("items", [])}

    with tempfile.TemporaryDirectory() as tmp:
        result = sp.run(
            ["git", "clone", "--depth=1", "--branch", ref, repo, tmp],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            console.print(f"[red]✗ Clone failed: {result.stderr.strip()}[/red]")
            raise typer.Exit(1)

        # Plan first: find every item that would overwrite a file we didn't
        # install ourselves, so the user can see the list before anything
        # is touched, rather than finding out from the summary afterward.
        plan: list[tuple[str, Path, Path]] = []
        foreign_overwrites: list[str] = []
        for src_rel, dst_rel in targets:
            src = Path(tmp) / src_rel
            dst = repo_root / dst_rel
            if not src.exists():
                console.print(
                    f"[yellow]⚠[/yellow] Expected '{src_rel}' not found in "
                    f"{repo}@{ref} — skipping (nothing installed for this path)"
                )
                continue
            for item in src.iterdir():
                dest = dst / item.name
                rel_dest = str(dest.relative_to(repo_root))
                plan.append((rel_dest, dest, item))
                if dest.exists() and rel_dest not in prior_items:
                    foreign_overwrites.append(rel_dest)

        if foreign_overwrites and not yes:
            console.print(
                "[yellow]The following existing file(s) will be overwritten "
                "(originals will be backed up and can be restored with "
                f"`wfctl uninstall-skills --agent {agent}`):[/yellow]"
            )
            for p in foreign_overwrites:
                console.print(f"  {p}")
            typer.confirm("Proceed?", abort=True)

        count = 0
        new_backups = 0
        items: list[dict] = []
        for rel_dest, dest, item in plan:
            dest.parent.mkdir(parents=True, exist_ok=True)

            # A pre-existing file we didn't put there ourselves gets backed
            # up before being overwritten, so uninstall can restore it. If
            # we already track this path from a prior install, carry its
            # backup forward instead of treating our own output as foreign.
            if rel_dest in prior_items:
                backup_rel = prior_items[rel_dest].get("backup")
            elif dest.exists():
                backup_dest = repo_root / _BACKUP_DIR / rel_dest
                backup_dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.is_dir():
                    shutil.copytree(dest, backup_dest)
                else:
                    shutil.copy2(dest, backup_dest)
                backup_rel = str(Path(_BACKUP_DIR) / rel_dest)
                new_backups += 1
            else:
                backup_rel = None

            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
            count += 1
            items.append({"path": rel_dest, "backup": backup_rel})

    manifest[agent] = {
        "repo": repo,
        "ref": ref,
        "installed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "items": items,
    }
    _save_manifest(repo_root, manifest)

    if new_backups:
        console.print(
            f"[yellow]ℹ[/yellow] Backed up {new_backups} pre-existing file(s) to "
            f"{_BACKUP_DIR}/ — restored by `wfctl uninstall-skills --agent {agent}`"
        )

    console.print(f"[green]✓[/green] Installed {count} item(s) from {repo}@{ref}")


@app.command("uninstall-skills")
def uninstall_skills_cmd(
    agent: str = typer.Option(
        "claude",
        "--agent",
        help=f"Target agent: {', '.join(_AGENT_TARGETS)}",
    ),
) -> None:
    """Remove what install-skills installed for --agent, restoring any file it overwrote."""
    import shutil

    try:
        repo_root = get_repo_root()
    except SystemExit:
        console.print("[red]✗ Not in a git repo.[/red]")
        raise typer.Exit(1)

    manifest = _load_manifest(repo_root)
    entry = manifest.get(agent)
    if not entry:
        console.print(f"Nothing installed for agent '{agent}' — nothing to uninstall.")
        return

    removed = 0
    restored = 0
    for item in entry["items"]:
        path = repo_root / item["path"]
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

        backup_rel = item.get("backup")
        backup_path = repo_root / backup_rel if backup_rel else None
        if backup_path is not None and backup_path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(backup_path), str(path))
            restored += 1
        else:
            removed += 1

    del manifest[agent]
    _save_manifest(repo_root, manifest)

    backup_root = repo_root / _BACKUP_DIR
    if backup_root.exists():
        for d in sorted(backup_root.glob("**/*"), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
        if not any(backup_root.iterdir()):
            backup_root.rmdir()

    console.print(
        f"[green]✓[/green] Removed {removed} item(s), restored {restored} "
        f"pre-existing file(s) for agent '{agent}'"
    )


if __name__ == "__main__":
    app()
