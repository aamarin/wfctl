"""wfctl CLI — workflow state manager for agent sessions."""
from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from pathlib import Path

import typer
from rich.console import Console

from wfctl import _bundle, _tracker
# Module scope, unlike the rest of `_archive`, which `archive-specs` imports
# lazily inside its `try` so an import error cannot strand a worktree. An
# `except` clause resolves its class before the handler runs, so this name has to
# exist by then. Safe to hoist: `_archive` imports only datetime, shutil and
# pathlib, so there is no import here that can fail on its own.
from wfctl._archive import ArchiveIncomplete as _ArchiveIncomplete
from wfctl._manifest import MANIFEST_PATH as _MANIFEST_PATH
from wfctl._manifest import load_manifest as _load_manifest
from wfctl._manifest import save_manifest as _save_manifest
from wfctl._paths import (
    _SPEC_DIR_OVERRIDE,
    extract_issue_key,
    get_repo_root,
    main_checkout,
    project_name,
    resolve_agent_dir,
    resolve_branch,
    resolve_spec_dir,
    spec_root,
    spec_root_declaration,
)

app = typer.Typer(no_args_is_help=True)
# highlight=False: don't let rich auto-color numbers/paths — this output is parsed
# by agents and asserted on in tests. Explicit [green]/[cyan]/… markup still applies.
console = Console(highlight=False)


def _wfctl_version() -> str:
    """The running wfctl's version — the provenance half the manifest records.

    One function rather than four `pkg_version("wfctl")` calls because it is what
    `install-skills` writes, what `doctor` compares against, and what two
    messages print. Tests patch this instead of the metadata machinery, so a
    fixture can install "1.0.0" and read it back without a real distribution.
    """
    from importlib.metadata import version as pkg_version

    return pkg_version("wfctl")


def _version_callback(value: bool) -> None:
    """Print wfctl's installed version and exit, if --version was passed."""
    if value:
        console.print(f"wfctl {_wfctl_version()}")
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


# Two names, one function. `archive-story` is a compatibility shim, hidden so it
# is not advertised as a second supported spelling: `.workmux.yaml` is repo-local,
# so copies predating the rename persist indefinitely, and a failing `pre_remove`
# hook now aborts the removal. Without the alias those repos would hit an unknown
# command, exit non-zero, and find their worktrees unremovable — a worse failure
# than the silent loss this command exists to prevent.
# ponytail: transition-only. Delete once the notice below has stopped appearing
# during teardowns on every machine — that silence is the end condition, and it
# is why the notice exists at all. #36 removed the doctor check that used to
# report this, because it only fired where someone happened to run doctor; this
# fires where the hook actually runs. Delete the alias and the notice together.
_FORMER_ARCHIVE_COMMAND = "archive-story"


@app.command("archive-specs")
@app.command(_FORMER_ARCHIVE_COMMAND, hidden=True)
def archive_specs_cmd(
    ctx: typer.Context,
    worktree: str = typer.Argument(
        None, help="Worktree to archive. Defaults to $WM_WORKTREE_PATH, then the current repo."
    ),
    handle: str = typer.Argument(
        None, help="Story handle. Defaults to $WM_HANDLE, then the branch."
    ),
) -> None:
    """Rescue a story's speckit artifacts before its worktree is deleted.

    Wired into workmux's `pre_remove`. `specs/` is gitignored, so a worktree
    holding only design artifacts reads *clean* to git and is removed without
    complaint — while work git can see already stops the removal on its own.
    This covers exactly the set nothing else can. Artifacts outside the worktree
    are not at risk and are not copied; the message names the resolved path so
    the absence of an archive does not read as a failed lookup.

    Two exit rules, and the split matters:

    * **Non-zero only when at-risk artifacts existed and copying them failed**
      (`ArchiveIncomplete`). A failing `pre_remove` hook aborts the removal, so
      this refuses the teardown rather than reporting the loss afterwards.
      `workmux remove --force` does *not* bypass the hook, which is why the
      refusal prints the manual route out — completely, since `git worktree
      remove` itself refuses when untracked files are present.
    * **Zero for everything else**, still via a bare `except`. An unrelated
      internal failure must not strand a worktree, and nothing was provably lost.
      It catches SystemExit too: `get_repo_root` raises that rather than an
      Exception, so `except Exception` alone would let a non-git checkout exit 1.

    This replaces an earlier "never exits non-zero" contract. That guarantee, in
    combination with `|| true` in the hook, meant a failed archive was silent and
    the worktree was destroyed anyway — the exact failure this command exists to
    prevent, delivered by its own error handling.

    Named `archive-specs` since #27, because it archives the spec dir and one
    superseded path and nothing else. `archive-story` survives as a hidden alias:
    `.workmux.yaml` is repo-local, and with the hook now able to abort a removal,
    an unknown command name would make those repos' worktrees unremovable.
    """
    try:
        # Inside the `try` on purpose: an import that raises here would exit
        # non-zero and strand the worktree, which is exactly what this command
        # promises not to do. Do not hoist these to module scope or above it.
        import os
        import subprocess as sp

        from wfctl import _archive

        # First, before any work that can return early: a repo whose hook still
        # names the alias should hear about it even on the teardowns that archive
        # nothing, since re-seeding the hook is the fix either way.
        #
        # Third line as in the rescue notice below — the end condition belongs in
        # the output, not only in the ponytail comment above.
        if ctx.info_name == _FORMER_ARCHIVE_COMMAND:
            console.print(
                "[yellow]⚠[/yellow] invoked as `archive-story`; renamed to "
                "`archive-specs`.\n"
                "  Re-seed the hook: wfctl install-config\n"
                "  The alias is retired once this line stops appearing."
            )

        root = worktree or os.environ.get("WM_WORKTREE_PATH")
        repo_root = Path(root).resolve() if root else get_repo_root()
        if not repo_root.is_dir():
            console.print(f"[yellow]⚠[/yellow] no worktree at '{repo_root}' — nothing archived")
            return

        branch = resolve_branch(repo_root)
        story = handle or os.environ.get("WM_HANDLE") or branch
        # `story` keys the spec lookup: an explicit handle wins, because the
        # caller knows which story is being torn down better than HEAD does.
        # Only fall back to `branch` when it differs — a miss walks every
        # ancestor branch, which is ~270ms of git, and repeating it is free of
        # any new answer.
        spec_dir = resolve_spec_dir(story, repo_root)
        if spec_dir is None and story != branch:
            spec_dir = resolve_spec_dir(branch, repo_root)
        state_dir = resolve_agent_dir(repo_root, branch)

        rev = sp.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root, capture_output=True, text=True,
        )
        commit = rev.stdout.strip() if rev.returncode == 0 else "unknown"

        archive_dir, mapped, rescued = _archive.archive(
            repo_root,
            handle=story,
            branch=branch,
            commit=commit,
            spec_dir=spec_dir,
            state_dir=state_dir,
        )
        # Reported whether or not anything else was archived. Gating this on an
        # empty plan hid it in the mixed case — an external spec root *plus* a
        # legacy `.agent/spec.md` — where the legacy file produces an archive and
        # the durable directory is skipped silently, which is exactly when the
        # explanation is most needed.
        if spec_dir is not None and not _archive.is_inside(repo_root, spec_dir):
            # escape(): the line carries rich markup for the tick, so a path
            # containing `[…]` — legal on every platform — would be parsed as a
            # style tag and silently dropped. This message exists to name a
            # location; printing a path that is not the real one is worse than
            # printing none.
            from rich.markup import escape

            console.print(
                f"[green]✓[/green] spec dir is durable ({escape(str(spec_dir))}) — "
                "nothing there was at risk, nothing copied",
                soft_wrap=True,
            )
        if archive_dir is None:
            if spec_dir is None or _archive.is_inside(repo_root, spec_dir):
                console.print(f"ℹ no speckit artifacts for '{story}' — nothing to archive")
            return
        console.print(f"[green]✓[/green] archived {len(mapped)} artifact(s) → {archive_dir}")

        # Additional to the count above, not a replacement: that line says what
        # was archived, this one says where it came from. Both matter in the
        # mixed case, where a durable spec dir is skipped and the only reason an
        # archive exists at all is the superseded directory.
        #
        # The closing sentence is the shim's end condition, in the output rather
        # than only in the ponytail comment below — otherwise the reader learns
        # the path is going away but not that the silence is the signal.
        if rescued:
            console.print(
                f"[yellow]⚠[/yellow] rescued {rescued} file(s) from legacy `.agent/` — "
                "a superseded path\n"
                "  kept only to rescue them. Nothing else reads it.\n"
                "  The read is retired once this line stops appearing."
            )
    except _ArchiveIncomplete as e:
        # The one path that exits non-zero. `pre_remove` failing aborts the
        # removal, so this refuses the teardown rather than reporting the loss
        # after it happened. `workmux remove --force` does NOT bypass the hook,
        # which is why the manual route is spelled out rather than implied — and
        # spelled out completely: `git worktree remove` refuses when untracked
        # files are present, and bypassing workmux skips its tmux cleanup.
        console.print(
            f"[red]✗[/red] {e.at_risk} spec file(s) could not be archived — "
            "removal aborted, nothing lost."
        )
        # These lines are meant to be pasted into a shell, so every interpolated
        # value is quoted: a worktree path containing a space otherwise produces a
        # command that fails, and a branch or path carrying shell metacharacters
        # produces one that does something else entirely.
        #
        # markup=False with them: a path may legitimately contain `[`, which rich
        # would read as a style tag and swallow. soft_wrap for the same reason as
        # above — rich wraps at the terminal width and would break mid-path, and a
        # route that cannot be pasted is no better than one not printed.
        import shlex

        console.print(f"  Cause: {e}", soft_wrap=True, markup=False)
        console.print("")
        console.print(
            f"  Retry:         workmux remove {shlex.quote(story)}",
            soft_wrap=True, markup=False,
        )
        console.print(
            f"  Remove anyway: git worktree remove {shlex.quote(str(repo_root))}"
            f" && git branch -D {shlex.quote(branch)}",
            soft_wrap=True, markup=False,
        )
        console.print(
            "                 (add --force to the first if the worktree has untracked\n"
            "                  files; leaves the tmux window workmux would have closed)"
        )
        raise typer.Exit(1) from e
    except (Exception, SystemExit) as e:  # noqa: BLE001 — see the docstring
        console.print(f"[yellow]⚠[/yellow] archive failed ({e}) — continuing so teardown is not blocked")


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
    # No spec folder yet → the path setup-plan.sh will `mkdir -p`. Resolved
    # through `spec_root` like the lookup above, not hardcoded: this line names
    # where every new spec is written, so hardcoding it here made the configured
    # root honored on read and silently ignored on create.
    feature_dir = spec_dir if spec_dir is not None else spec_root(repo_root) / branch
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


@app.command("spec-root")
def spec_root_cmd(
    path: str | None = typer.Argument(
        None, help="Directory to write spec dirs under. Omit to show the current root."
    ),
    unset: bool = typer.Option(False, "--unset", help="Remove the recorded root."),
) -> None:
    """Show, set, or clear where this repo's spec dirs live.

    Stored as `spec_root` in `.wf-skills-manifest.json`. The path is kept exactly
    as typed — `~` is expanded when read, not when written, so the manifest stays
    portable — and is neither created nor checked for existence.

    Writes the main checkout's manifest when there is one, and says so: the
    manifest is gitignored and a worktree's copy dies with the worktree, so
    recording it there would set a value that silently evaporates.
    """
    import os

    if path is not None and unset:
        console.print("[red]✗[/red] give a path or --unset, not both")
        raise typer.Exit(2)

    repo_root = get_repo_root()

    if path is None and not unset:
        if os.environ.get(_SPEC_DIR_OVERRIDE):
            source = _SPEC_DIR_OVERRIDE
        else:
            found = spec_root_declaration(repo_root)
            source = (
                str(found[1] / _MANIFEST_PATH)
                if found is not None
                else "default (no spec_root recorded)"
            )
        console.print(f"spec root: {spec_root(repo_root)}", soft_wrap=True)
        console.print(f"source:    {source}", soft_wrap=True)
        return

    target = main_checkout(repo_root) or repo_root
    manifest = _load_manifest(target)
    if unset:
        manifest.pop("spec_root", None)
    else:
        manifest["spec_root"] = path
    _save_manifest(target, manifest)

    # `_save_manifest` deletes a manifest that has become empty, so `--unset` on a
    # repo that recorded nothing writes no file — claiming otherwise sends the
    # user looking for a path that isn't there.
    manifest_file = target / _MANIFEST_PATH
    if not manifest_file.exists():
        console.print("nothing to unset — no spec_root was recorded")
        return

    # soft_wrap: these paths are the point of the lines; rich would wrap mid-path.
    console.print(f"[green]✓[/green] wrote {manifest_file}", soft_wrap=True)
    if _ensure_gitignored(target, _MANIFEST_PATH):
        # Tracked in most repos, and `target` may not be where the user is
        # standing — an unannounced edit here lands in someone's next commit.
        console.print(f"[green]✓[/green] gitignored it in {target / '.gitignore'}", soft_wrap=True)


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
#
# Every pair here and below is (source, destination). Sources are relative to
# `_bundle.BUNDLE_ROOT` and carry no leading dot — inside the installed package
# these are ordinary data directories, not a project's hidden config. The dot
# belongs to the destination alone, which is a real `.agents/` in the user's
# repo. The two halves are no longer the same string even where they name the
# same subtree, so neither is derivable from the other.
_BASE_TARGETS = [
    ("agents/skills", ".agents/skills"),
    ("agents/commands", ".agents/commands"),
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
    "claude": [("agents/commands", ".claude/commands")],
    "bob": [
        ("agents/skills", ".bob/skills"),
        ("agents/commands", ".bob/commands"),
    ],
    # `agents/skills/<name>/SKILL.md` is already the shape Copilot's skills
    # layout expects, so this is a plain copy — no frontmatter transform, no
    # rename. See specs/…/research.md for why the skills layout was chosen over
    # `.github/agents/*.agent.md`, which upstream is deprecating.
    "copilot": [("agents/skills", ".github/skills")],
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
# bundle — a managed mirror, same (src, dst) copy machinery as above.
_RUNTIME_TARGETS = [
    ("specify/scripts", ".specify/scripts"),
    ("specify/templates", ".specify/templates"),
]

# Repo-level config files wfctl can seed from wf-skills. Unlike skills (a
# managed mirror), these are seed-once: the copied file becomes the repo's own,
# committed and owned — so install-config keeps no manifest/backup/uninstall
# bookkeeping. Positional config name → source dir in the bundle whose contents
# copy to the repo root.
#
# A source may nest: `github/` holds `.github/pull_request_template.md`, so the
# directory structure under the source is the structure that lands in the repo.
_CONFIG_SOURCES = {
    "workmux": "agents/configs/workmux",
    "github": "agents/configs/github",
}

_BACKUP_DIR = ".wf-skills-backup"

_BASE_LAYER = "base"
# `tracker` and `spec_root` are bare strings, not installed layers — they hold
# the repo's tracker choice and its spec root alongside the layer entries, and
# must be skipped by anything iterating them: `_layer_keys` feeds callers that
# do `manifest[key].get("items", [])`, which raises AttributeError on a string.
# `base` IS a layer (it has items and a content hash, so `doctor` checks it for
# drift), it is just not an *agent* — see _agent_keys.
_NON_LAYER_KEYS = frozenset({"tracker", "spec_root", "spec_root_asked"})


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


def _ensure_gitignored(repo_root: Path, line: str) -> bool:
    """Ignore `line` via .gitignore unless git already ignores it.

    Coverage is git's own verdict, so a broader pattern already matching the path
    suppresses the write — a literal comparison cannot see that, and enumerating
    every path under an existing `.agents/` is what #11 was.

    Returns whether it wrote. `spec-root` announces the edit, since `.gitignore`
    is tracked and `repo_root` may not be where the user is standing;
    `install-skills` counts the Falses to report how many it skipped.
    """
    import subprocess as sp

    # ponytail: one process per path, ~7ms each (~600ms per install) against a
    # ~15s clone. Batch via `check-ignore --stdin` over gitignore_targets if #1
    # lands and the clone stops dominating.
    #
    # Every argument below is load-bearing; each has a test that fails without it.
    #   --no-index  a tracked path reports "not ignored" even when a pattern
    #               matches, so we would write a line that cannot affect it
    #   --          a leading dash otherwise parses as an option (`-Z` exits 129)
    #   capture_output  git writes `fatal:` to stderr outside a repo
    #
    # Non-zero means "not covered", which is also the safe fallback: when the
    # check cannot run at all, write the line.
    if sp.run(
        ["git", "check-ignore", "-q", "--no-index", "--", line],
        cwd=repo_root,
        capture_output=True,
    ).returncode == 0:
        return False

    gi = repo_root / ".gitignore"
    text = gi.read_text() if gi.exists() else ""
    if text and not text.endswith("\n"):
        text += "\n"
    gi.write_text(text + f"{line}\n")
    return True


def _interactive() -> bool:
    """Is there a human to prompt? Seam so tests can exercise both paths."""
    return sys.stdin.isatty()


_SPEC_ROOT_ASKED = "spec_root_asked"


def _spec_root_question_answered(repo_root: Path) -> bool:
    """Has this project already answered the spec-location question?

    Two ways to have answered, and both count:

    * the marker this prompt writes, or
    * a `spec_root` already recorded — by `wfctl spec-root`, or by a repo that
      configured one before this prompt existed. Asking those projects would be
      asking a question they have already answered more explicitly than the
      prompt can, and a wrong answer would silently relocate their specs.

    Walks this checkout then the main one for both, mirroring
    `spec_root_declaration`. `post_create` reinstalls in every fresh worktree,
    where the manifest is regenerated from scratch, so a local-only read would
    re-ask in each of them.
    """
    if spec_root_declaration(repo_root) is not None:
        return True
    if _load_manifest(repo_root).get(_SPEC_ROOT_ASKED):
        return True
    main = main_checkout(repo_root)
    return bool(main and _load_manifest(main).get(_SPEC_ROOT_ASKED))


def _spec_root_panels(name: str) -> list[object]:
    """The three options, rendered.

    Stacked rather than side by side: three boxes across truncate their titles
    below ~110 columns.
    """
    from rich.markup import escape
    from rich.panel import Panel

    # A directory name is not markup. `[` is legal in one, and unescaped it is
    # parsed as a style tag and dropped, so the panel would show a project name
    # the user does not recognise.
    name = escape(name)

    return [
        Panel(
            f"  [bold]{name}/[/bold]\n"
            "  ├── specs/42-feature/      ← spec.md, plan.md, tasks.md\n"
            "  └── wt/42-feature/         worktree\n\n"
            "  Committed with your code, or gitignored — your .gitignore decides.\n"
            "  If gitignored, removing the worktree deletes them.",
            title="[bold]1[/bold]  Keep them in the repo",
            subtitle="default · nothing to configure",
            title_align="left", subtitle_align="right", width=78,
        ),
        Panel(
            f"  [bold]{name}/[/bold]\n"
            f"  ├── {name}-specs/       its own repo, gitignored here\n"
            "  │   └── specs/42-feature/\n"
            "  └── wt/42-feature/         worktree\n\n"
            "  Survives worktree removal, versioned on its own remote, and\n"
            "  greppable from any worktree without a checkout.",
            title="[bold]2[/bold]  In a specs repo cloned here",
            subtitle="durable · in git · greppable",
            title_align="left", subtitle_align="right", width=78,
        ),
        Panel(
            "  [bold]~/Development/[/bold]\n"
            f"  ├── {name}-specs/\n"
            "  │   └── 42-feature/\n"
            f"  └── {name}/wt/42-feature/\n\n"
            "  Survives worktree removal. Whether it is version-controlled is\n"
            "  up to you.",
            title="[bold]3[/bold]  Somewhere else on disk",
            subtitle="durable",
            title_align="left", subtitle_align="right", width=78,
        ),
    ]


def _ask_where_specs_live(repo_root: Path) -> tuple[str, str | None]:
    """Ask once, on first interactive install.

    Returns `(choice, path)` — the option the user picked and the path they gave,
    or None for the default. The choice is returned rather than re-derived from
    the path's shape: both prompts accept absolute *and* relative input, so
    inferring "this was option 2" from `not is_absolute()` mislabels an absolute
    answer to option 2 and a relative answer to option 3, and the clone guidance
    and gitignore entry hang off that distinction.

    Option 1 records no `spec_root` at all: the default *is* the absence of the
    key, so a repo that answers "keep them here" must resolve byte-identically to
    one that was never asked. Recording `null` instead would be bookkeeping under
    a name that implies behaviour.

    Never creates, clones, or checks the target. A not-yet-existing root is
    exactly the case the setting exists to support, and network I/O mid-install
    is a blast radius this does not need.
    """
    name = project_name(repo_root)
    console.print()
    console.print("[bold]Where should this project's specs live?[/bold]")
    console.print(
        "Each feature gets a spec, plan, and tasks. Worktrees get removed when\n"
        "the work ends — if the specs live inside one, they go with it."
    )
    for panel in _spec_root_panels(name):
        console.print(panel)
    console.print(
        "Change any time with `wfctl spec-root`. Skipping keeps option 1."
    )

    choice = typer.prompt("Choose [1/2/3]", default="1", show_default=True).strip()
    if choice == "2":
        directory = typer.prompt("Directory", default=f"{name}-specs").strip()
        return "2", (directory or f"{name}-specs")
    if choice == "3":
        return "3", (typer.prompt("Path").strip() or None)
    return "1", None


@app.command("install-skills")
def install_skills_cmd(
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

    # Same shape as the tracker question above, and asked in the same breath:
    # first interactive install only, never under --yes or a pipe, never twice.
    # `spec_root` exists since #25 but nothing pointed a project at it, so repos
    # took the default and found out it was wrong when `workmux remove` deleted a
    # spec — the failure the setting exists to prevent.
    if not yes and _interactive() and not _spec_root_question_answered(repo_root):
        choice, chosen = _ask_where_specs_live(repo_root)
        # The main checkout, not this one: the manifest is gitignored and a
        # worktree's copy dies with the worktree, so recording it here would set
        # a value that silently evaporates. Same target `wfctl spec-root` uses.
        target = main_checkout(repo_root) or repo_root
        target_manifest = _load_manifest(target)
        target_manifest[_SPEC_ROOT_ASKED] = True
        if chosen:
            target_manifest["spec_root"] = chosen
        _save_manifest(target, target_manifest)
        if target == repo_root:
            # Keep the in-memory copy in step, or the save at the end of this
            # command writes the pre-answer manifest back over it.
            manifest[_SPEC_ROOT_ASKED] = True
            if chosen:
                manifest["spec_root"] = chosen

        console.print(
            f"[green]✓[/green] wrote {target / _MANIFEST_PATH}", soft_wrap=True
        )
        if chosen and _ensure_gitignored(target, _MANIFEST_PATH):
            console.print(
                f"[green]✓[/green] gitignored it in {target / '.gitignore'}", soft_wrap=True
            )
        if choice == "2" and chosen:
            # Keyed on the option the user picked, not on the path's shape. Both
            # prompts accept absolute and relative input, so an absolute answer to
            # option 2 would have lost this guidance and a relative answer to
            # option 3 would have received it wrongly — along with a `../…`
            # gitignore entry that means nothing.
            import shlex

            # Only a path inside the checkout can be gitignored by it. An absolute
            # answer to option 2 lands elsewhere on disk and simply has no entry
            # to write; `_ensure_gitignored` would otherwise be handed a path its
            # `check-ignore` call cannot evaluate against this repo.
            from rich.markup import escape

            rel = Path(chosen).expanduser()
            if not rel.is_absolute() and _ensure_gitignored(target, f"{chosen}/"):
                console.print(
                    f"[green]✓[/green] gitignored {escape(chosen)}/ in "
                    f"{escape(str(target / '.gitignore'))}",
                    soft_wrap=True,
                )
            # Anchored to `target`, not left relative. `chosen` is stored relative
            # to the main checkout, but these lines get pasted into whatever shell
            # the user is standing in — from a linked worktree that would create
            # the specs repo inside the worktree, which is the one place it must
            # not go. Quoted for the same reason as the teardown escape route.
            where = shlex.quote(str(target / chosen)) if not rel.is_absolute() \
                else shlex.quote(str(rel))
            # escape() as well as quote(): shell quoting protects the shell, rich
            # markup is a separate layer, and `[` is legal in a path. Without it
            # these lines — which exist to be pasted — lose part of the path and
            # create the specs repo somewhere else, or nowhere.
            where = escape(where)
            console.print(
                f"\n[dim]Not created yet — when you have a specs repo:\n"
                f"  git clone <url> {where}\n\n"
                f"Or start one:\n"
                f"  mkdir -p {where}/specs && git -C {where} init[/dim]",
                soft_wrap=True,
            )

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
        src = _bundle.BUNDLE_ROOT / src_rel
        dst = repo_root / dst_rel
        if not src.exists():
            # Reachable only from a broken install — the bundle ships with the
            # package, so a missing source means the wheel lost files rather
            # than that the user asked for something that does not exist. Named
            # as such, since "not found in wf-skills@main" used to send people
            # to look upstream for a problem on their own disk.
            console.print(
                f"[yellow]⚠[/yellow] Expected '{src_rel}' missing from this "
                f"wfctl install ({_bundle.BUNDLE_ROOT}) — skipping "
                "(nothing installed for this path)"
            )
            continue
        for item in src.iterdir():
            dest = dst / item.name
            rel_dest = str(dest.relative_to(repo_root))
            plan.append((layer, kind, rel_dest, dest, item))
            gitignore_targets.append(rel_dest)
            if dest.exists() and rel_dest not in prior_items:
                foreign_overwrites.append((layer, rel_dest))

            if src_rel == "agents/skills":
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

    # 'github' is the only tracker the bundle ships; copy just its config.
    if tracker == "github":
        tsrc = _bundle.BUNDLE_ROOT / "agents" / "trackers" / "github.json"
        if tsrc.exists():
            tdest = repo_root / ".agents" / "trackers" / "github.json"
            trel = str(tdest.relative_to(repo_root))
            plan.append((_BASE_LAYER, "tracker", trel, tdest, tsrc))
            if tdest.exists() and trel not in prior_items:
                foreign_overwrites.append((_BASE_LAYER, trel))
        else:
            console.print(
                "[yellow]⚠[/yellow] --tracker github, but "
                "agents/trackers/github.json is missing from this wfctl "
                f"install ({_wfctl_version()}) — nothing installed for it"
            )

    if foreign_overwrites and not yes:
        console.print(
            "[yellow]The following existing file(s) will be overwritten "
            "(originals will be backed up, restored by "
            f"{_restore_hint(layer for layer, _ in foreign_overwrites)}):[/yellow]"
        )
        for _, p in foreign_overwrites:
            console.print(f"  {p}")
        typer.confirm("Proceed?", abort=True)

    # Hashed once, before the copy, and shared by every layer. The digest covers
    # the whole bundle rather than one layer's subtree, so there is nothing
    # per-layer to compute — see `_bundle.content_hash` for why it is whole-tree.
    # Computed first so a bundle-less install fails with the repo untouched: the
    # alternative is a copied tree and no manifest, which uninstall can't undo.
    try:
        content_hash = _bundle.content_hash(_bundle.BUNDLE_ROOT)
    except FileNotFoundError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1) from e

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
    wfctl_version = _wfctl_version()
    # One entry per layer that installed something. An agent with no layer of
    # its own (none, or a notice-only agent) writes no entry, so uninstalling
    # it reports nothing to remove rather than failing on a missing key.
    #
    # Replaced, not updated: this is also the migration off `repo`/`ref`/`commit`,
    # and those name a fetch that no longer happens. `layer_items` already carries
    # every prior `backup` pointer forward, so the one field that cannot be
    # recomputed survives — an `.update()` here would keep the dead keys instead.
    for layer, layer_items in items.items():
        manifest[layer] = {
            "wfctl_version": wfctl_version,
            "content_hash": content_hash,
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

    # A count, not a list: `git check-ignore -v <path>` already attributes each
    # skip to a file, line, and pattern, and a second listing here would drift.
    skipped = sum(
        not _ensure_gitignored(repo_root, rel)
        for rel in (_MANIFEST_PATH, f"{_BACKUP_DIR}/", *gitignore_targets)
    )
    if skipped:
        console.print(
            f"[dim]ℹ {skipped} ignore entr{'y' if skipped == 1 else 'ies'} "
            f"already covered by .gitignore — skipped[/dim]"
        )

    if new_backups:
        console.print(
            f"[yellow]ℹ[/yellow] Backed up {new_backups} pre-existing file(s) to "
            f"{_BACKUP_DIR}/ — restored by {_restore_hint(backup_layers)}"
        )

    console.print(f"[green]✓[/green] Installed from wfctl {wfctl_version}")
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
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip the confirmation when removing a layer others still read.",
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
        console.print(f"Nothing installed for layer '{agent}' — nothing to uninstall.")
        return

    # Agent layers are views of the base, not copies of it: their command
    # wrappers point into .agents/skills. Removing the base underneath one
    # leaves it installed and broken, so this asks first — the only ordering
    # that isn't destructive is agents first, base last.
    dependents = _agent_keys(manifest) if agent == _BASE_LAYER else []
    if dependents and not yes:
        console.print(
            f"[yellow]⚠[/yellow] {', '.join(dependents)} still installed, and "
            f"read the '{_BASE_LAYER}' layer's skills — removing it leaves them "
            "in place pointing at files that no longer exist.\n"
            f"[dim]Remove them first: "
            + " ".join(f"wfctl uninstall-skills --agent {d}" for d in dependents)
            + "[/dim]"
        )
        typer.confirm(f"Remove '{_BASE_LAYER}' anyway?", abort=True)

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
        f"pre-existing file(s) for layer '{agent}'"
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
        "sole agent layer in the manifest; with none or several, the key is "
        "left commented out rather than guessed.",
    ),
) -> None:
    """Seed a standardized repo config from wf-skills into the current repo.

    Unlike install-skills (a managed mirror), this is seed-once: the copied files
    become the repo's own, committed and owned — no manifest/backup/uninstall.
    Refuses to overwrite an existing file unless --force (git is your undo).

    \b
    workmux  .workmux.yaml, with `agent:` and `window_prefix:` filled in
    github   .github/pull_request_template.md
    """
    import shutil

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

    src = _bundle.BUNDLE_ROOT / src_rel
    if not src.exists():
        # `name` is already known to _CONFIG_SOURCES, so the config is one wfctl
        # ships and the files are missing from this install — not something the
        # user asked for that never existed.
        console.print(
            f"[red]✗ Config '{name}' is missing from this wfctl install "
            f"({_bundle.BUNDLE_ROOT}) — expected '{src_rel}'.[/red]"
        )
        raise typer.Exit(1)

    # Plan the copy (source dir contents → repo root), collecting anything
    # we'd overwrite so we can refuse before touching the tree.
    #
    # File by file, not entry by entry: a nested source lands inside a directory
    # the repo almost certainly already has. Comparing directory names would
    # refuse `github` in every repo with a `.github/`, while the copy underneath
    # it silently overwrote whatever shared a name with a seeded file.
    plan = [
        (item, repo_root / item.relative_to(src))
        for item in sorted(src.rglob("*"))
        if item.is_file()
    ]
    conflicts = [
        str(dest.relative_to(repo_root)) for _, dest in plan if dest.exists() and not force
    ]
    if conflicts:
        console.print(
            f"[red]✗ Would overwrite existing file(s): {', '.join(conflicts)}. "
            f"Pass --force to overwrite (git is your undo).[/red]"
        )
        raise typer.Exit(1)

    for item, dest in plan:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest)

    if name == "workmux":
        from wfctl import _workmux

        # Worktrees live in ./wt inside the repo — keep git from tracking them.
        _ensure_gitignored(repo_root, "wt/")

        # Resolve here, substitute in _workmux. The module takes plain values and
        # never touches git or the manifest, which is what keeps its tests
        # fixture-free — see wfctl/_workmux.py.
        #
        # `agent:` gets the installed/〈--agent〉 agent, or stays commented when
        # there is no single one to mirror (see _resolve_config_agent).
        chosen = _resolve_config_agent(repo_root, agent)

        # The project's name, not this checkout's. `get_repo_root` is
        # `--show-toplevel`, which inside a worktree returns the branch handle —
        # seeding from a worktree would commit `window_prefix: '9-some-branch__'`.
        raw_project = project_name(repo_root)
        proj = _workmux.tmux_safe(raw_project)
        if proj != raw_project:
            console.print(
                f"[dim]ℹ window_prefix: '{raw_project}' → '{proj}' — tmux rewrites "
                ". and : in session names[/dim]",
                soft_wrap=True,
            )

        wf = repo_root / ".workmux.yaml"
        patched = _workmux.patch_seed(wf.read_text(), agent=chosen, project=proj)
        wf.write_text(patched)

        # Watch for the surviving placeholder, not for a missing key: if the
        # template renames `window_prefix` upstream, a key check passes at exactly
        # the moment the placeholder does ship. tmux accepts `<` and `>`, so an
        # unsubstituted prefix becomes a real session named `<project>__<branch>`
        # — committed, for everyone on the repo.
        if _workmux.unsubstituted_placeholder(patched):
            console.print(
                f"[yellow]⚠[/yellow] .workmux.yaml still contains "
                f"'{_workmux.PROJECT_PLACEHOLDER}' — the prefix was not substituted.\n"
                "  The template's window_prefix key may have been renamed or "
                "reformatted upstream.\n"
                f"  Fix: set window_prefix: '{proj}__'",
                soft_wrap=True,
            )

    console.print(
        f"[green]✓[/green] Seeded {name} config ({len(plan)} file(s)) "
        f"from wfctl {_wfctl_version()}"
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


def _archive_destination(repo_root: Path) -> str:
    """Where `archive-specs` would write, for display only — creates nothing.

    `resolve_agent_dir` would answer this but also mkdirs, and a health check that
    creates directories while reporting on them is a check with side effects.
    """
    import os

    override = os.environ.get("WFCTL_STATE_DIR")
    if override:
        return f"{override}/archive/"
    xdg = Path(os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state"))
    path = xdg / "wfctl" / project_name(repo_root) / "<branch>" / "archive"
    try:
        return f"~/{path.relative_to(Path.home())}/"
    except ValueError:
        return f"{path}/"


def _check_workmux_hook(repo_root: Path) -> None:
    """Report a `.workmux.yaml` that won't archive on teardown; offer to fix it.

    `install-config` is seed-once and refuses to overwrite, so fixing the upstream
    template only ever reaches repos seeded afterwards. This is the one path by
    which an already-seeded repo becomes protected.

    Deliberately reports `pre_remove` only — never an unsubstituted session
    prefix. A cosmetic warning beside a data-loss warning trains the reader to
    skim past both, and this is the one whose job is to be noticed.

    Never touches doctor's exit code: this is drift, reported the way a missing
    pinned commit is, not a failure.
    """
    from wfctl import _workmux

    wf = repo_root / ".workmux.yaml"
    if not wf.exists():
        return  # not every repo uses workmux
    try:
        text = wf.read_text()
    except OSError as exc:
        console.print(f"[yellow]⚠[/yellow] couldn't read .workmux.yaml: {exc}")
        return
    if _workmux.pre_remove_wired(text):
        return

    console.print(
        "[yellow]⚠[/yellow] .workmux.yaml: pre_remove does not call "
        "`wfctl archive-specs` — removing a\n"
        "  worktree will discard its specs, plan, and tasks."
    )
    # soft_wrap: rich would otherwise wrap this at the terminal width and could
    # split the path itself, which both reads badly and breaks assertions on it.
    console.print(
        f"  Archives would be written to: {_archive_destination(repo_root)}",
        soft_wrap=True,
    )

    patched = _workmux.wire_pre_remove(text)
    if patched is None:
        # Custom steps, or no key at all. Both leave the insertion point and
        # ordering unknowable, so hand it back rather than guess.
        # soft_wrap: this line is meant to be copy-pasted into a YAML list, and a
        # wrapped line pastes broken.
        console.print(
            "  pre_remove holds custom steps — add this entry to it yourself:\n"
            f"{_workmux.ARCHIVE_HOOK}",
            soft_wrap=True,
        )
        return
    if not _interactive():
        # /start-session runs doctor through a non-TTY shell. Without this line
        # the automated path reports a problem with no route to the fix.
        console.print("  Run `wfctl doctor` from a terminal to wire it.")
        return
    if not typer.confirm("Wire it now?", default=True):
        # Declining is not recorded. Unlike choosing no tracker — a genuine
        # one-time decision — an unwired teardown hook is ongoing drift, and
        # re-reporting drift is what a doctor is for.
        return
    try:
        wf.write_text(patched)
    except OSError as exc:
        console.print(f"[yellow]⚠[/yellow] couldn't write .workmux.yaml: {exc}")
        return
    console.print("[green]✓[/green] pre_remove wired — .workmux.yaml")


def _check_spec_root_migration(repo_root: Path) -> None:
    """Report in-repo spec dirs stranded by a recorded `spec_root`.

    Recording a root migrates nothing, and the recorded root is the only one
    consulted — no fallback, so one feature's artifacts can never split across
    two locations. The cost is that pre-existing `specs/*` become invisible, and
    a silently invisible spec is the failure class this whole feature removes.

    Recurring drift, not a transition — which is why #36 swept the checks beside
    this one and left this one standing. The condition needs a repo that
    accumulated `specs/*` and then adopted a root elsewhere, and both halves are
    still produced today: `install-skills` asks every new project where its specs
    live, and `wfctl spec-root` re-answers it for an existing one. A project that
    adopts a root next year strands whatever it had, exactly as one that adopted
    a root last year did. There is no end condition to observe here.

    Reports only: never moves or deletes, and never touches doctor's exit code —
    same contract as `_check_workmux_hook`, which treats drift as reportable
    rather than as failure.
    """
    in_repo = repo_root / "specs"
    if not in_repo.is_dir():
        return
    # Keyed on what a manifest *records*, not on what `spec_root` resolves. The
    # latter honors WFCTL_SPEC_DIR, so a one-off `WFCTL_SPEC_DIR=… wfctl doctor`
    # — or the env var exported in a shell profile, which this design warns
    # against but people do — would announce "spec_root is set" in a repo that
    # records nothing, and nag about moving specs to a transient directory.
    declared = spec_root_declaration(repo_root)
    if declared is None:
        return
    root = declared[0]
    # Resolve both sides: a recorded relative value comes back resolved, while
    # repo_root does not have to be (WFCTL_REPO_ROOT is taken verbatim). Compared
    # raw, a root pointing at this very directory reads as a mismatch and the
    # warning tells the user to move specs from a directory to itself.
    if root.resolve() == in_repo.resolve():
        return
    stranded = sorted(p for p in in_repo.iterdir() if p.is_dir())
    if not stranded:
        return

    one = len(stranded) == 1
    console.print(
        f"[yellow]⚠[/yellow] spec_root is set, but {in_repo} still holds "
        f"{len(stranded)} spec {'directory' if one else 'directories'} that will not be found.",
        soft_wrap=True,
    )
    # soft_wrap: this names a path the reader is expected to act on; a wrapped
    # path reads as two paths and pastes broken.
    it = "it" if one else "them"
    console.print(f"  Move {it} to {root}, or remove {it}.", soft_wrap=True)


@app.command("doctor")
def doctor_cmd() -> None:
    """Check the wfctl tool and installed wf-skills content for available updates.

    green ✓ current · cyan ⬆ upgrade available · yellow ⚠ warning · red ✗ error.
    """
    exit_code = _check_wfctl_version()

    try:
        repo_root = get_repo_root()
    except SystemExit:
        console.print("[yellow]⚠[/yellow] not in a git repo — skipping skills check.")
        raise typer.Exit(exit_code)

    # Before the manifest gate below: a repo can have a .workmux.yaml or a
    # recorded spec_root without having installed skills. Both are drift a repo
    # can carry with nothing pinned, so both are reported either way.
    _check_workmux_hook(repo_root)
    _check_spec_root_migration(repo_root)

    manifest = _load_manifest(repo_root)
    layers = _layer_keys(manifest)
    if not layers:
        console.print("Nothing installed — run `wfctl install-skills` first.")
        raise typer.Exit(exit_code)

    # One hash for the whole bundle, so it is computed once no matter how many
    # layers are on record — every entry in one manifest carries the same value.
    running_version = _wfctl_version()
    try:
        bundle_hash = _bundle.content_hash(_bundle.BUNDLE_ROOT)
    except FileNotFoundError as e:
        # Every remaining check compares against this digest, so there is no
        # partial report to salvage — the other checks above have already run.
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1) from e

    for agent in layers:
        entry = manifest[agent]
        recorded = entry.get("content_hash")
        if not recorded:
            # Unmeasurable, not stale: the layer may well be current, and there
            # is nothing the user could have done to avoid this record. Warn and
            # leave the exit code alone — re-installing writes a hash.
            console.print(
                f"[yellow]⚠[/yellow] {agent}: installed before content hashing — "
                "re-run install-skills to enable drift checking."
            )
            continue

        if recorded == bundle_hash:
            console.print(f"[green]✓[/green] {agent}: skills current (wfctl {running_version})")
            continue

        exit_code = 1
        installed_by = entry.get("wfctl_version")
        if installed_by and installed_by != running_version:
            console.print(
                f"[cyan]⬆[/cyan] {agent}: skills stale — installed by wfctl "
                f"{installed_by}, running {running_version}"
            )
        else:
            # Same version, different content: an editable install whose skills
            # were edited in place. Naming the version twice would read as a bug.
            console.print(f"[cyan]⬆[/cyan] {agent}: bundled skills changed since install")
        console.print("    update: wfctl install-skills")

    raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()
