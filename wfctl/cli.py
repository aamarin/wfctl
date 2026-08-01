"""wfctl CLI — workflow state manager for agent sessions."""
from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from pathlib import Path

import typer
from rich.console import Console

from wfctl import _tracker
from wfctl._paths import (
    extract_issue_key,
    get_repo_root,
    resolve_agent_dir,
    resolve_branch,
    resolve_spec_dir,
)

app = typer.Typer(no_args_is_help=True)
# highlight=False: don't let rich auto-color numbers/paths — this output is parsed
# by agents and asserted on in tests. Explicit [green]/[cyan]/… markup still applies.
console = Console(highlight=False)


def _version_callback(value: bool) -> None:
    """Print wfctl's installed version and exit, if --version was passed."""
    if value:
        from importlib.metadata import version as pkg_version

        console.print(f"wfctl {pkg_version('wfctl')}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True,
        help="Show the wfctl version and exit.",
    )
) -> None:
    """wfctl — workflow state manager for agent sessions."""


def _resolve_context() -> tuple[Path, Path, str, str]:
    """Return (agent_dir, repo_root, branch, issue); exits on error."""
    try:
        repo_root = get_repo_root()
    except SystemExit as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)
    branch = resolve_branch(repo_root)
    # Default key shape is \d+ (GitHub); a tracker with non-numeric keys
    # (Jira/Linear/Shortcut) overrides it via key_pattern in its config.
    issue = extract_issue_key(branch, _tracker.load_key_pattern(repo_root))
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
        "issue": "green",
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
    # Plain print: output is consumed by $(wfctl state-dir); rich wraps at
    # terminal width and would inject a newline mid-path.
    print(agent_dir)


@app.command("feature-paths")
def feature_paths_cmd() -> None:
    """Print the active feature's paths as eval-able shell assignments.

    The single source of truth for branch → spec-dir resolution: `resolve_spec_dir`
    honors the active tracker's key_pattern and an exact `specs/<branch>` match.
    The installed speckit runtime (`.specify/scripts/bash/common.sh`) sources this
    instead of re-deriving paths with a numeric-only regex, so non-numeric issue
    keys (e.g. PFHB-123) resolve correctly. Consumed via `eval`, so values are
    single-quoted.
    """
    _, repo_root, branch, _ = _resolve_context()
    spec_dir = resolve_spec_dir(branch, repo_root)
    # No spec folder yet → the conventional path setup-plan.sh will `mkdir -p`.
    feature_dir = spec_dir if spec_dir is not None else repo_root / "specs" / branch
    fields = [
        ("REPO_ROOT", repo_root),
        ("CURRENT_BRANCH", branch),
        ("HAS_GIT", "true"),  # _resolve_context already required a git repo
        ("FEATURE_DIR", feature_dir),
        ("FEATURE_SPEC", feature_dir / "spec.md"),
        ("IMPL_PLAN", feature_dir / "plan.md"),
        ("TASKS", feature_dir / "tasks.md"),
        ("RESEARCH", feature_dir / "research.md"),
        ("DATA_MODEL", feature_dir / "data-model.md"),
        ("QUICKSTART", feature_dir / "quickstart.md"),
        ("CONTRACTS_DIR", feature_dir / "contracts"),
    ]
    # Plain print: output is eval'd by shell; rich would wrap/inject ANSI.
    for name, val in fields:
        print(f"{name}='{val}'")


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


@app.command("issue")
def issue_cmd(
    verb: str = typer.Argument(..., help="list | view | close | comment | create | label"),
    issue_id: str = typer.Argument(None, help="Issue ID (view / close / comment / label)"),
    comment: str = typer.Option(None, "--comment", help="Comment text (close)"),
    body: str = typer.Option(None, "--body", help="Body text (comment / create)"),
    title: str = typer.Option(None, "--title", help="Title (create)"),
    label: str = typer.Option(None, "--label", help="Label name (label)"),
    action: str = typer.Option(None, "--action", help="add | remove (label)"),
) -> None:
    """Run the active issue tracker's command for a standard verb.

    The backend is chosen at install time (`wfctl install-skills --tracker <name>`)
    and defined by `.agents/trackers/<name>.json`. Each verb and its arguments:

    \b
      list                                          list open issues
      view    <id>                                  show one issue
      close   <id> --comment TEXT                   close with a comment
      comment <id> --body TEXT                      add a comment
      create       --title T --body TEXT            open a new issue
      label   <id> --action add|remove --label NAME add/remove a label

    \b
    Examples:
      wfctl issue list
      wfctl issue view 71
      wfctl issue close 71 --comment "Done in abc123"
      wfctl issue label 71 --action add --label in-progress

    Degrades gracefully (exit 0) when no tracker is configured or the active
    backend does not implement the verb.
    """
    from wfctl import _tracker

    agent_dir, repo_root, _, _ = _resolve_context()
    params = {
        "id": issue_id, "comment": comment, "body": body,
        "title": title, "label": label, "action": action,
    }
    params = {k: v for k, v in params.items() if v is not None}
    raise typer.Exit(_tracker.dispatch(agent_dir, repo_root, verb, params))


@app.command("change")
def change_cmd(
    verb: str = typer.Argument(..., help="list | view"),
    change_id: str = typer.Argument(None, help="Change / PR ID (view)"),
) -> None:
    """List or view code changes — GitHub PRs, Gerrit patchsets, etc.

    The changes backend is defined by the `changes` section of the active
    tracker config (`.agents/trackers/<name>.json`), parallel to `issue`'s
    `verbs`. A `{me}` in a command is filled from the config's `identity`, so
    `list` can be scoped to you:

    \b
      list        list your open changes
      view  <id>  show one change

    \b
    Examples:
      wfctl change list
      wfctl change view 128

    Degrades gracefully (exit 0) when no backend is configured or the active
    one does not implement the verb.
    """
    from wfctl import _tracker

    agent_dir, repo_root, _, _ = _resolve_context()
    params = {"id": change_id} if change_id is not None else {}
    raise typer.Exit(
        _tracker.dispatch(agent_dir, repo_root, verb, params, section="changes", event="change")
    )


# The canonical, agent-agnostic layer. Always installed, whatever --agent says:
# wf-skills authors one copy of each skill and command wrapper, and this is where
# that copy lives. Agent layers below are derived views of it.
_BASE_TARGETS = [
    (".agents/skills", ".agents/skills"),
    (".agents/commands", ".agents/commands"),
]

# Added on top of the base layer when --agent names one. Every entry owns a
# unique root, and no entry may claim a destination the base layer already owns.
# That disjointness is the whole mechanism behind backup attribution: a layer can
# only ever encounter its own files or the user's, never another layer's. It is
# enforced by test_layer_destinations_are_disjoint, not by this comment, because
# a new agent added here would otherwise reintroduce the collision silently.
_AGENT_TARGETS = {
    "none": [],
    "codex": [],
    "claude": [(".agents/commands", ".claude/commands")],
    "bob": [
        (".agents/skills", ".bob/skills"),
        (".agents/commands", ".bob/commands"),
    ],
    # `.agents/skills/<name>/SKILL.md` is already the shape Copilot's skills
    # layout expects, so this is a plain copy — no frontmatter transform, no
    # rename. See specs/…/research.md for why the skills layout was chosen over
    # `.github/agents/*.agent.md`, which upstream is deprecating.
    "copilot": [(".agents/skills", ".github/skills")],
}

# Agents that are recognised but have no repo-local path to install into. They
# resolve to an empty layer and print why, rather than erroring: the base layer
# is still what they need, so failing would be misleading.
_AGENT_NOTICES = {
    "codex": (
        "Codex has no repo-local command path — its prompts live in "
        "~/.codex/prompts (never shared through a repo) and its repo entry "
        "point is AGENTS.md.\nInstalling the base layer only; Codex reads "
        ".agents/ and AGENTS.md directly."
    ),
}

# The speckit skills shell out to `.specify/scripts/*.sh` and read
# `.specify/templates/*`. That runtime is repo-level (not per-agent) and
# version-locked to the skills, so it installs alongside them from the same
# wf-skills clone — a managed mirror, same (src, dst) copy machinery as above.
_RUNTIME_TARGETS = [
    (".specify/scripts", ".specify/scripts"),
    (".specify/templates", ".specify/templates"),
]

# Repo-level config files wfctl can seed from wf-skills. Unlike skills (a
# managed mirror), these are seed-once: the copied file becomes the repo's own,
# committed and owned — so install-config keeps no manifest/backup/uninstall
# bookkeeping. Positional config name → source dir in wf-skills whose contents
# copy to the repo root.
_CONFIG_SOURCES = {"workmux": ".agents/configs/workmux"}

_MANIFEST_PATH = ".wf-skills-manifest.json"
_BACKUP_DIR = ".wf-skills-backup"

_BASE_LAYER = "base"
# `tracker` is a bare string, not an installed layer — it holds the repo's
# tracker choice alongside the layer entries and must be skipped by anything
# iterating them. `base` IS a layer (it has items and a pinned commit, so
# `doctor` checks it for drift), it is just not an *agent* — see _agent_keys.
_NON_LAYER_KEYS = frozenset({"tracker"})


def _layer_keys(manifest: dict) -> list[str]:
    """Manifest keys that name an installed layer, base included."""
    return [k for k in manifest if k not in _NON_LAYER_KEYS]


def _agent_keys(manifest: dict) -> list[str]:
    """Manifest keys that name an agent with paths of its own.

    Layers minus the base, minus any agent that installs nothing. `none` and
    `codex` write no entry now, but a manifest from before the layer split can
    still carry a `none` key — and treating that as a chosen agent seeds a
    literal `agent: none` into the committed .workmux.yaml.
    """
    return [
        k
        for k in _layer_keys(manifest)
        if k != _BASE_LAYER and _AGENT_TARGETS.get(k)
    ]


def _restore_hint(layers: Iterable[str]) -> str:
    """The uninstall command(s) that actually restore a set of backups.

    Backups belong to the layer that took them, not to whatever `--agent` was
    asked for: a bare install backs up under `base`, and `--agent none` — the
    obvious guess — matches no entry and silently does nothing.
    """
    names = sorted(set(layers))
    return " and ".join(f"`wfctl uninstall-skills --agent {n}`" for n in names)


def _skill_deployment(skill_dir: Path) -> str:
    """Read the `deployment:` frontmatter key from a skill's SKILL.md. Defaults to 'command'."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return "command"
    lines = skill_md.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return "command"
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("deployment:"):
            return line.split(":", 1)[1].strip().strip("'\"")
    return "command"


def _claude_native_skill_mirror(
    repo_root: Path, item: Path
) -> tuple[str, Path, Path] | None:
    """Claude extra: a skill under .agents/skills marked `deployment: skill` also
    mirrors to .claude/skills/<name> (Claude's native discovery path), on top of
    the .agents/skills reference copy every agent gets. None if it doesn't apply."""
    if not item.is_dir() or _skill_deployment(item) != "skill":
        return None
    dest = repo_root / ".claude" / "skills" / item.name
    return str(dest.relative_to(repo_root)), dest, item


# Per-agent hook for extra mirrors beyond the plain (src, dst) copy in
# _AGENT_TARGETS, keyed the same way — dispatch by agent, not by growing
# `if agent == "..."` branches. Called once per item under .agents/skills;
# returning None means "nothing extra for this item".
_AGENT_SKILL_EXTRAS = {
    "claude": _claude_native_skill_mirror,
}


def _kind_of(src_rel: str) -> str:
    """What an item is, for the install summary — 'skill', 'command', 'runtime'.

    Derived from the source directory, so a new target picks up a sensible label
    without a second lookup table to keep in sync.
    """
    return {"skills": "skill", "commands": "command"}.get(
        src_rel.rsplit("/", 1)[-1], "runtime"
    )


def _format_summary(summary: dict[str, dict[str, int]]) -> list[str]:
    """Render per-layer, per-kind counts — one line per layer that installed
    something.

    A single total would read as a skill count when it is mostly the same skills
    counted once per layer plus runtime files. Layers and kinds with nothing in
    them are omitted rather than shown as `0`.
    """
    # 'runtime' and 'tracker' are mass nouns here — "8 runtimes" reads as eight
    # separate runtimes rather than eight files of one.
    countable = {"skill", "command"}
    width = max((len(layer) for layer in summary), default=0)
    lines = []
    for layer, kinds in summary.items():
        parts = [
            f"{n} {kind}{'s' if n != 1 and kind in countable else ''}"
            for kind, n in kinds.items()
            if n
        ]
        if parts:
            lines.append(f"  {layer.ljust(width)}  {' · '.join(parts)}")
    return lines


def _ensure_gitignored(repo_root: Path, line: str) -> None:
    """Append `line` to .gitignore if absent (create the file if needed). Idempotent."""
    gi = repo_root / ".gitignore"
    text = gi.read_text() if gi.exists() else ""
    if line in text.splitlines():
        return
    if text and not text.endswith("\n"):
        text += "\n"
    gi.write_text(text + f"{line}\n")


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


def _interactive() -> bool:
    """Is there a human to prompt? Seam so tests can exercise both paths."""
    return sys.stdin.isatty()


@app.command("install-skills")
def install_skills_cmd(
    repo: str = typer.Option(
        "https://github.com/aamarin/wf-skills",
        "--repo",
        help="wf-skills repo URL",
    ),
    ref: str = typer.Option("main", "--ref", help="Branch or tag to install from"),
    agent: str = typer.Option(
        "none",
        "--agent",
        help="Also install an agent's native paths on top of the "
        f"agent-agnostic layer: {', '.join(a for a in _AGENT_TARGETS if a != 'none')}. "
        "Omit to install .agents/ only.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip the confirmation prompt when files would be overwritten",
    ),
    tracker: str = typer.Option(
        None,
        "--tracker",
        help="Issue-tracker backend: 'github' (ships), 'none' to clear, or a "
        "custom name whose .agents/trackers/<name>.json you author. Omit to leave unchanged.",
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

    # Said before the install runs, so the reason arrives ahead of a summary
    # that would otherwise look like the agent was simply ignored.
    if agent in _AGENT_NOTICES:
        console.print(f"[cyan]ℹ[/cyan] {_AGENT_NOTICES[agent]}")

    try:
        repo_root = get_repo_root()
    except SystemExit:
        console.print("[red]✗ Not in a git repo.[/red]")
        raise typer.Exit(1)

    manifest = _load_manifest(repo_root)
    # Union across every layer, not just this agent's. A path wfctl installed is
    # wfctl's whichever layer put it there, so it must never be mistaken for a
    # file the user wrote. Two cases need this: the base layer owns .agents/*
    # while an agent install also plans them, and a manifest written before the
    # layer split records those same paths under the agent key. Without the
    # union, the first install after either would prompt to overwrite ~25
    # directories wfctl installed itself, and back them up as if they were the
    # user's.
    prior_items = {
        i["path"]: i
        for key in _layer_keys(manifest)
        for i in manifest[key].get("items", [])
    }

    # First install in a repo that has never chosen a tracker: ask, since the
    # right backend differs per repo. Non-interactive runs (piped, CI, --yes)
    # leave it unset rather than committing a config nobody asked for.
    if tracker is None and "tracker" not in manifest and not yes and _interactive():
        console.print(
            "No issue tracker configured. wf-skills ships a GitHub backend "
            "(.agents/trackers/github.json, via the `gh` CLI)."
        )
        if typer.confirm("Install it?", default=True):
            tracker = "github"
        else:
            # Record the decline, so this is asked once and not on every
            # upgrade. `null` reads as "chose no tracker" — the readers in
            # _tracker.py test the value's truth, so it behaves exactly like
            # an absent key. `--tracker none` clears it and re-opens the
            # question.
            manifest["tracker"] = None
            console.print(
                "[dim]Skipped — `wfctl issue` / `wfctl change` no-op until a tracker "
                "is set, and this won't be asked again. Set one later with:\n"
                "  GitHub   wfctl install-skills --tracker github\n"
                "  Custom   /scaffold-tracker writes .agents/trackers/<name>.json\n"
                "           wfctl tracker-check <name>\n"
                "           wfctl install-skills --tracker <name>\n"
                "Once set, later installs leave that choice — and your edits to its "
                "config — alone.[/dim]"
            )

    with tempfile.TemporaryDirectory() as tmp:
        result = sp.run(
            ["git", "clone", "--depth=1", "--branch", ref, repo, tmp],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            console.print(f"[red]✗ Clone failed: {result.stderr.strip()}[/red]")
            raise typer.Exit(1)

        commit = sp.run(
            ["git", "rev-parse", "HEAD"], cwd=tmp, capture_output=True, text=True
        ).stdout.strip()

        # Plan first: find every item that would overwrite a file we didn't
        # install ourselves, so the user can see the list before anything
        # is touched, rather than finding out from the summary afterward.
        # Each entry carries the layer that owns it, so the manifest can record
        # base and agent items under separate keys — which is what keeps one
        # layer's uninstall from touching another's paths.
        plan: list[tuple[str, str, str, Path, Path]] = []
        # (layer, path) — the layer is what makes the restore hint name a
        # command that works: base-layer backups are not restored by
        # `--agent <the agent asked for>`.
        foreign_overwrites: list[tuple[str, str]] = []
        # Paths install-skills owns going forward — gitignored below so a
        # sync never dirties whatever branch happens to be checked out.
        # Tracker config is deliberately excluded: it's project-owned,
        # user-editable, and meant to be committed.
        gitignore_targets: list[str] = []
        # Base layer first, then the agent's own layer, then the repo-level
        # runtime. An agent install is additive — it never replaces the base.
        # The runtime is agent-independent, so it belongs to base too.
        layered = [
            *((_BASE_LAYER, _kind_of(s), s, d) for s, d in _BASE_TARGETS),
            *((agent, _kind_of(s), s, d) for s, d in targets),
            *((_BASE_LAYER, "runtime", s, d) for s, d in _RUNTIME_TARGETS),
        ]
        for layer, kind, src_rel, dst_rel in layered:
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
                plan.append((layer, kind, rel_dest, dest, item))
                gitignore_targets.append(rel_dest)
                if dest.exists() and rel_dest not in prior_items:
                    foreign_overwrites.append((layer, rel_dest))

                if src_rel == ".agents/skills":
                    extra_fn = _AGENT_SKILL_EXTRAS.get(agent)
                    extra = extra_fn(repo_root, item) if extra_fn else None
                    if extra:
                        # An extra mirror is the agent's own, even though its
                        # source is a base-layer path.
                        extra_rel, extra_dest, extra_item = extra
                        plan.append((agent, "skill", extra_rel, extra_dest, extra_item))
                        gitignore_targets.append(extra_rel)
                        if extra_dest.exists() and extra_rel not in prior_items:
                            foreign_overwrites.append((agent, extra_rel))

        # 'github' is the only tracker wf-skills ships; copy just its config.
        if tracker == "github":
            tsrc = Path(tmp) / ".agents" / "trackers" / "github.json"
            if tsrc.exists():
                tdest = repo_root / ".agents" / "trackers" / "github.json"
                trel = str(tdest.relative_to(repo_root))
                plan.append((_BASE_LAYER, "tracker", trel, tdest, tsrc))
                if tdest.exists() and trel not in prior_items:
                    foreign_overwrites.append((_BASE_LAYER, trel))
            else:
                console.print(
                    "[yellow]⚠[/yellow] --tracker github, but "
                    ".agents/trackers/github.json not found in "
                    f"{repo}@{ref} — nothing installed for it"
                )

        if foreign_overwrites and not yes:
            console.print(
                "[yellow]The following existing file(s) will be overwritten "
                f"(originals will be backed up, restored by "
                f"{_restore_hint(l for l, _ in foreign_overwrites)}):[/yellow]"
            )
            for _, p in foreign_overwrites:
                console.print(f"  {p}")
            typer.confirm("Proceed?", abort=True)

        count = 0
        new_backups = 0
        backup_layers: set[str] = set()
        items: dict[str, list[dict]] = {}
        summary: dict[str, dict[str, int]] = {}
        for layer, kind, rel_dest, dest, item in plan:
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
                backup_layers.add(layer)
            else:
                backup_rel = None

            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
            count += 1
            items.setdefault(layer, []).append({"path": rel_dest, "backup": backup_rel})
            summary.setdefault(layer, {})
            summary[layer][kind] = summary[layer].get(kind, 0) + 1

    installed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # One entry per layer that installed something. An agent with no layer of
    # its own (none, or a notice-only agent) writes no entry, so uninstalling
    # it reports nothing to remove rather than failing on a missing key.
    for layer, layer_items in items.items():
        manifest[layer] = {
            "repo": repo,
            "ref": ref,
            "commit": commit,
            "installed_at": installed_at,
            "items": layer_items,
        }

    # A manifest from before the layer split can carry a `none` entry owning
    # .agents/* — paths the base layer owns now. Agents that install nothing
    # never write an entry, so one can only be a leftover, and leaving it in
    # place double-books those paths: `uninstall-skills --agent none` would
    # delete files `base` still claims. Drop it only once base has recorded
    # every path it held, so nothing is orphaned. Its backup pointers already
    # came across — prior_items carried them into base's items above.
    base_paths = {i["path"] for i in manifest.get(_BASE_LAYER, {}).get("items", [])}
    for stale in [k for k, t in _AGENT_TARGETS.items() if not t and k in manifest]:
        if {i["path"] for i in manifest[stale].get("items", [])} <= base_paths:
            del manifest[stale]

    # Tracker choice is a repo-global sibling of the per-agent entries.
    if tracker == "none":
        manifest.pop("tracker", None)
    elif tracker is not None:
        manifest["tracker"] = tracker
        if tracker != "github":
            cfg = repo_root / ".agents" / "trackers" / f"{tracker}.json"
            if not cfg.exists():
                console.print(
                    f"[yellow]⚠[/yellow] selected tracker '{tracker}' but no "
                    f".agents/trackers/{tracker}.json found — author it with /scaffold-tracker"
                )

    _save_manifest(repo_root, manifest)

    _ensure_gitignored(repo_root, _MANIFEST_PATH)
    _ensure_gitignored(repo_root, f"{_BACKUP_DIR}/")
    for rel in gitignore_targets:
        _ensure_gitignored(repo_root, rel)

    if new_backups:
        console.print(
            f"[yellow]ℹ[/yellow] Backed up {new_backups} pre-existing file(s) to "
            f"{_BACKUP_DIR}/ — restored by {_restore_hint(backup_layers)}"
        )

    console.print(f"[green]✓[/green] Installed from {repo}@{ref}")
    for line in _format_summary(summary):
        console.print(line)

    # Only worth saying when nothing agent-specific was installed: that is the
    # case where a user whose assistant needs native paths sees no sign of them.
    if not any(layer != _BASE_LAYER for layer in summary):
        opt_in = [a for a in _AGENT_TARGETS if _AGENT_TARGETS[a]]
        width = max(len(a) for a in opt_in)
        console.print(
            "\n[dim]Installed to .agents/ — skills and commands in their canonical, "
            "agent-agnostic form.\nIf your agent needs its own native paths:[/dim]"
        )
        for a in opt_in:
            console.print(f"[dim]  {a.ljust(width)}  wfctl install-skills --agent {a}[/dim]")


@app.command("uninstall-skills")
def uninstall_skills_cmd(
    agent: str = typer.Option(
        _BASE_LAYER,
        "--agent",
        help="Layer to remove: "
        f"{', '.join([_BASE_LAYER, *(a for a in _AGENT_TARGETS if _AGENT_TARGETS[a])])}. "
        f"'{_BASE_LAYER}' is the agent-agnostic .agents/ layer a bare install writes.",
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


def _resolve_config_agent(repo_root: Path, explicit: str | None) -> str | None:
    """Agent for a seeded config: explicit flag → sole installed agent → None.

    Mirrors what `install-skills --agent` recorded, so a repo set up for a
    non-default agent gets a matching workmux config without re-specifying it.

    None means "don't assert one". A repo that installed no agent layer made no
    choice to mirror, and naming one anyway would commit a claim its own install
    contradicts — the config is version-controlled, so that lands in everyone's
    checkout. Same for a repo with several: picking one would be arbitrary.
    workmux resolves `<agent>` from ~/.config/workmux/config.yaml when the key
    is absent, which is where a per-developer preference belongs.
    """
    if explicit:
        return explicit
    agents = _agent_keys(_load_manifest(repo_root))
    return agents[0] if len(agents) == 1 else None


@app.command("install-config")
def install_config_cmd(
    name: str = typer.Argument(..., help=f"Config to seed: {', '.join(_CONFIG_SOURCES)}"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
    agent: str = typer.Option(
        None, "--agent",
        help="Agent the config targets (workmux `agent:`). Defaults to the "
        "installed agent from the manifest, else 'claude'.",
    ),
    repo: str = typer.Option(
        "https://github.com/aamarin/wf-skills", "--repo", help="wf-skills repo URL"
    ),
    ref: str = typer.Option("main", "--ref", help="Branch or tag to install from"),
) -> None:
    """Seed a standardized repo config from wf-skills into the current repo.

    Unlike install-skills (a managed mirror), this is seed-once: the copied files
    become the repo's own, committed and owned — no manifest/backup/uninstall.
    Refuses to overwrite an existing file unless --force (git is your undo).
    v1 ships 'workmux'.
    """
    import shutil
    import subprocess as sp
    import tempfile

    src_rel = _CONFIG_SOURCES.get(name)
    if src_rel is None:
        console.print(
            f"[red]✗ Unknown config '{name}'. Available: {', '.join(_CONFIG_SOURCES)}.[/red]"
        )
        raise typer.Exit(1)

    try:
        repo_root = get_repo_root()
    except SystemExit:
        console.print("[red]✗ Not in a git repo.[/red]")
        raise typer.Exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        # ponytail: dup'd clone from install_skills_cmd; extract a helper if a 3rd caller appears
        result = sp.run(
            ["git", "clone", "--depth=1", "--branch", ref, repo, tmp],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            console.print(f"[red]✗ Clone failed: {result.stderr.strip()}[/red]")
            raise typer.Exit(1)

        src = Path(tmp) / src_rel
        if not src.exists():
            console.print(f"[red]✗ Config '{name}' not found in {repo}@{ref} ({src_rel}).[/red]")
            raise typer.Exit(1)

        # Plan the copy (source dir contents → repo root), collecting anything
        # we'd overwrite so we can refuse before touching the tree.
        plan = [(item, repo_root / item.name) for item in src.iterdir()]
        conflicts = [item.name for item, dest in plan if dest.exists() and not force]
        if conflicts:
            console.print(
                f"[red]✗ Would overwrite existing file(s): {', '.join(conflicts)}. "
                f"Pass --force to overwrite (git is your undo).[/red]"
            )
            raise typer.Exit(1)

        for item, dest in plan:
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    if name == "workmux":
        # Worktrees live in ./wt inside the repo — keep git from tracking them.
        _ensure_gitignored(repo_root, "wt/")
        # Point `agent:` at the installed/〈--agent〉 agent (pane runs `<agent>`).
        # With no single agent to mirror, comment the key out rather than
        # guessing — see _resolve_config_agent.
        chosen = _resolve_config_agent(repo_root, agent)
        wf = repo_root / ".workmux.yaml"
        lines = wf.read_text().splitlines(keepends=True)
        for i, ln in enumerate(lines):
            if ln.startswith("agent:"):
                lines[i] = (
                    f"agent: {chosen}\n"
                    if chosen
                    else "# agent: claude   # per-developer; set here or in "
                    "~/.config/workmux/config.yaml\n"
                )
                break
        wf.write_text("".join(lines))

    console.print(
        f"[green]✓[/green] Seeded {name} config ({len(plan)} file(s)) from {repo}@{ref}"
    )


@app.command("tracker-check")
def tracker_check_cmd(
    name: str = typer.Argument(..., help="Tracker name — validates .agents/trackers/<name>.json"),
) -> None:
    """Validate a tracker config; exit non-zero with the specific problems if bad.

    A malformed config doesn't crash `wfctl issue` — it silently disables the
    tracker. This catches the problem instead. Prints `OK: <verbs>` when valid;
    re-run after each fix until it passes.
    """
    repo_root = get_repo_root()
    path = repo_root / ".agents" / "trackers" / f"{name}.json"
    if not path.exists():
        console.print(f"[red]INVALID:[/red] {path} not found")
        raise typer.Exit(1)
    try:
        config = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        console.print(f"[red]INVALID:[/red] {e}")
        raise typer.Exit(1)

    errs = _tracker.validate_config(config)
    if errs:
        console.print("[red]INVALID:[/red]")
        for err in errs:
            console.print(f"  - {err}")
        raise typer.Exit(1)
    console.print(f"[green]OK:[/green] {', '.join(config['verbs'])}")


# wfctl is installed from this repo (uv tool install git+…); doctor compares the
# running version against its latest release tag. Assumes the canonical origin;
# a fork install just shows "couldn't check" / a spurious upgrade, never an error.
_WFCTL_REPO = "https://github.com/aamarin/wfctl.git"


def _parse_semver(v: str) -> tuple | None:
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return None


def _check_wfctl_version() -> int:
    """Report the wfctl tool's freshness. Return 1 if an upgrade is available.

    green ✓ = latest · cyan ⬆ = upgrade available · yellow ⚠ = couldn't check.
    """
    import re
    import subprocess as sp
    from importlib.metadata import version as pkg_version

    installed = pkg_version("wfctl")
    r = sp.run(["git", "ls-remote", "--tags", "--refs", _WFCTL_REPO], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        console.print(f"[yellow]⚠[/yellow] wfctl {installed} — couldn't check latest (offline?)")
        return 0

    tags = [(t, _parse_semver(t)) for t in re.findall(r"refs/tags/v(\d+\.\d+\.\d+)", r.stdout)]
    parsed = [(pv, t) for t, pv in tags if pv]
    cur = _parse_semver(installed)
    if parsed and cur is not None and max(parsed)[0] > cur:
        latest = max(parsed)[1]
        console.print(f"[cyan]⬆[/cyan] wfctl {installed} → {latest} available")
        console.print(f"    upgrade: uv tool install --upgrade {_WFCTL_REPO}")
        return 1

    console.print(f"[green]✓[/green] wfctl {installed} — latest")
    return 0


@app.command("doctor")
def doctor_cmd() -> None:
    """Check the wfctl tool and installed wf-skills content for available updates.

    green ✓ current · cyan ⬆ upgrade available · yellow ⚠ warning · red ✗ error.
    """
    import subprocess as sp
    import tempfile

    exit_code = _check_wfctl_version()

    try:
        repo_root = get_repo_root()
    except SystemExit:
        console.print("[yellow]⚠[/yellow] not in a git repo — skipping skills check.")
        raise typer.Exit(exit_code)

    manifest = _load_manifest(repo_root)
    layers = _layer_keys(manifest)
    if not layers:
        console.print("Nothing installed — run `wfctl install-skills` first.")
        raise typer.Exit(exit_code)

    for agent in layers:
        entry = manifest[agent]
        repo, ref, commit = entry.get("repo"), entry.get("ref"), entry.get("commit")
        if not commit:
            console.print(
                f"[yellow]⚠[/yellow] {agent}: no pinned commit on record (installed "
                "before drift-checking existed) — re-run install-skills to enable this."
            )
            continue

        remote = sp.run(["git", "ls-remote", repo, ref], capture_output=True, text=True)
        if remote.returncode != 0 or not remote.stdout.strip():
            console.print(f"[red]✗[/red] {agent}: couldn't reach {repo}@{ref} — {remote.stderr.strip()}")
            exit_code = 1
            continue

        tip = remote.stdout.split()[0]
        if tip == commit:
            console.print(f"[green]✓[/green] {agent}: skills up to date ({commit[:7]})")
            continue

        exit_code = 1
        console.print(f"[cyan]⬆[/cyan] {agent}: skills behind — {commit[:7]} → {tip[:7]}")
        with tempfile.TemporaryDirectory() as tmp:
            clone = sp.run(["git", "clone", "-q", repo, tmp], capture_output=True, text=True)
            if clone.returncode == 0:
                diff = sp.run(
                    ["git", "diff", "--stat", commit, tip, "--", ".agents/skills", ".agents/commands"],
                    cwd=tmp, capture_output=True, text=True,
                )
                for line in (diff.stdout.strip().splitlines() or ["(no changes under .agents/skills or .agents/commands)"]):
                    console.print(f"    {line}")
            else:
                console.print(f"    (couldn't clone to diff: {clone.stderr.strip()})")
        console.print("    update: wfctl install-skills")

    raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()
