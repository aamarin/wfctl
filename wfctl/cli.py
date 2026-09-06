"""wfctl CLI — workflow state manager for agent sessions."""
from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import typer
from rich.console import Console

from wfctl import _bundle, _settings, _tracker
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
    arch_root,
    is_in_tree,
    extract_issue_key,
    get_repo_root,
    main_checkout,
    project_name,
    resolve_agent_dir,
    resolve_branch,
    resolve_spec_dir,
    spec_root,
    spec_root_declaration,
    touched_on_this_branch,
)

if TYPE_CHECKING:
    from wfctl import _session
    from wfctl._pipeline import PipelineReport

app = typer.Typer(no_args_is_help=True)
# highlight=False: don't let rich auto-color numbers/paths — this output is parsed
# by agents and asserted on in tests. Explicit [green]/[cyan]/… markup still applies.
console = Console(highlight=False)

# Pipeline state name → (glyph, rich style). The only place a state is drawn.
# Inference carries names, so the drawing exists for exactly as long as one
# console line: a symbol cannot travel back up into `_pipeline` without being
# spelled here first, and a caller reading the report never sees one.
#
# `pending` and `skipped` share a style deliberately — the states differ, the
# emphasis does not, and colouring "passed by" differently from "not yet" would
# assert a judgement about which is worse.
_NO_SESSION = "[red]✗ No session found for this branch. Run `wfctl start` first.[/red]"

_STATE_GLYPH: dict[str, tuple[str, str]] = {
    "done":        ("●", "green"),
    "in_progress": ("▶", "yellow"),
    "pending":     ("○", "dim"),
    "skipped":     ("–", "dim"),
}


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


def _remove_session_fossils(agent_dir: Path) -> None:
    """Delete `current.md` and `current.json` if this state dir still has them.

    Inert to this code, which reads neither. Not inert to an older `start-session`
    elsewhere on the machine: it reads `current.md`, whose resume point was
    written once at `wfctl start` and never again — the stale answer this feature
    exists to remove. A developer has tens of state directories and upgrades the
    tool once, so the fossils outlive the code that wrote them.

    Silent. The files are tool-written and never hand-edited, and a notice about
    a file the reader did not know existed is noise.
    """
    for name in ("current.md", "current.json"):
        (agent_dir / name).unlink(missing_ok=True)


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
    _remove_session_fossils(agent_dir)
    return agent_dir, repo_root, branch, issue


@app.command("start")
def start_cmd(
    force: bool = typer.Option(False, "--force", help="Open a session even if one is recorded")
) -> None:
    """Initialize agent session context."""
    from wfctl._io import append_event
    from wfctl._pipeline import build_report

    agent_dir, repo_root, branch, _ = _resolve_context()
    spec_dir = resolve_spec_dir(branch, repo_root)
    report = build_report(spec_dir, repo_root, agent_dir)

    if report.session_started and not force:
        console.print("ℹ Already initialized (use --force to reset)")
        return

    step = report.current or "complete"
    append_event(agent_dir, "start", branch=branch, step=step)
    console.print(
        f"[green]✓[/green] Session started — step: {step}, "
        f"next: {report.next_command or '(none)'}"
    )


@app.command("status")
def status_cmd(
    as_json: bool = typer.Option(False, "--json", help="Print the report as JSON")
) -> None:
    """Show pipeline progress."""
    from wfctl._pipeline import STORY_COMPLETE_CONSOLE, build_report
    from wfctl._paths import resolve_spec_dir

    agent_dir, repo_root, branch, issue = _resolve_context()
    spec_dir = resolve_spec_dir(branch, repo_root)
    report = build_report(spec_dir, repo_root, agent_dir)

    if as_json:
        # The same object the console branch renders, in the other format. The
        # flag selects a rendering and never a second inference — two inference
        # paths is what `pipeline-state-is-one-payload` rejects, not two formats.
        # Without this an agent's only source of per-step state is the block
        # below, whose glyphs are lossy by construction.
        console.print_json(data={
            "issue": issue,
            "branch": branch,
            # Which feature the steps below were counted from, null when none
            # resolved. Without it an unresolved branch and a finished story are
            # the same payload — every step `pending`/`done` with no way to ask
            # *whose* tasks.md said so, which is how #120 stayed quiet.
            "spec_dir": str(spec_dir) if spec_dir is not None else None,
            "session_started": report.session_started,
            "current": report.current,
            "next_command": report.next_command,
            "auto": report.auto,
            "steps": report.steps,
        })
        return

    console.print(f"[bold]#{issue}  {branch}[/bold]")
    console.print("[dim]" + "─" * 36 + "[/dim]")
    if spec_dir is None:
        console.print("[dim](no spec dir found)[/dim]")

    steps = report.steps
    for step in steps:
        name = step["name"].ljust(12)
        name_fmt = f"[bold]{name}[/bold]" if step["is_current"] else name
        glyph, color = _STATE_GLYPH[step["state"]]
        sym_fmt = f"[{color}]{glyph}[/{color}]"
        ann = f"  [dim]{step['annotation']}[/dim]" if step["annotation"] else ""
        marker = "  [cyan]← current[/cyan]" if step["is_current"] else ""
        console.print(f"{name_fmt} {sym_fmt}{ann}{marker}")

    # The completion sentence rather than a second spelling of it: `_pipeline`
    # owns both forms so the file an agent reads and the line a human reads
    # cannot drift apart.
    console.print(f"[dim]next:[/dim] {report.next_command or STORY_COMPLETE_CONSOLE}")


@app.command("verify")
def verify_cmd() -> None:
    """Run this repository's definition of done and record the outcome."""
    from wfctl import _verify

    agent_dir, repo_root, _, _ = _resolve_context()
    raise typer.Exit(_verify.perform(agent_dir, repo_root))


def _refuse_unless_boundary_answered(
    spec_dir: Path | None, step_name: str, repo_root: Path
) -> None:
    """Exit 1 when the design step is being left with the boundary unanswered.

    Called by every command that writes `next-step.md`, not just `next`:
    `speckit-orchestrate` advances the pipeline with `wfctl resume`, so gating
    only `next` would leave the orchestrated path — the one that actually runs —
    walking straight past the check. `start` is deliberately not gated: it opens
    the session that has to run `arch none` to answer.

    Before the file is written, never after. `next-step.md` is what the agent
    reads next, so a refusal that still wrote it would be a message nothing acts
    on.
    """
    from wfctl._pipeline import DESIGN_GATE_REFUSAL, design_gate

    arch = arch_root(repo_root)
    # `is False` — never a falsy check. `touched_on_this_branch` returns None
    # when git cannot answer (no trunk, or a root outside the tree), and that
    # case proceeds along with a real True: the gate refuses only on evidence.
    # `design/` is excluded, not counted. It holds level-3 records, which govern
    # one feature and say nothing about ownership — the question this gate asks.
    # Counting them would let a change that genuinely moves a boundary satisfy
    # the gate with a record whose own format forbids it from drawing one, and
    # #121 item 3 guarantees every such record lands in the branch diff.
    if design_gate(
        spec_dir,
        step_name,
        lambda: touched_on_this_branch(repo_root, arch, exclude=arch / "design") is False,
    ):
        console.print(DESIGN_GATE_REFUSAL.format(location=_arch_location(arch, repo_root)))
        raise typer.Exit(1)


@app.command("next")
def next_cmd() -> None:
    """Write next actionable step to next-step.md."""
    from wfctl._pipeline import (
        STORY_COMPLETE_CONSOLE,
        STORY_COMPLETE_FILE,
        _current_step_name,
        _infer_steps,
        next_step_content,
    )
    from wfctl._io import append_event

    agent_dir, repo_root, branch, _ = _resolve_context()
    spec_dir = resolve_spec_dir(branch, repo_root)
    steps = _infer_steps(spec_dir, repo_root)
    step_name = _current_step_name(steps)

    # With no spec dir there is no design.md either, so the gate cannot fire.
    _refuse_unless_boundary_answered(spec_dir, step_name, repo_root)

    # No special case for a missing spec dir. It used to force `/speckit.specify`,
    # from when an absent design read as "skipped" and specify was the honest
    # first step. Inference now says `brainstorm` for a feature nothing has
    # happened to, whether or not the directory exists, and `status` prints that
    # — a `next-step.md` naming a different step would be the drift this file is
    # the single writer of.
    command, auto = next_step_content(step_name, repo_root, spec_dir)

    next_step_md = agent_dir / "next-step.md"
    if command:
        auto_str = "true" if auto else "false"
        content = f"Next step: {command}\nauto: {auto_str}\nRun this command to continue.\n"
        console.print(f"→ Next step: {command} (auto: {auto_str})")
    else:
        content = STORY_COMPLETE_FILE
        console.print(STORY_COMPLETE_CONSOLE)

    next_step_md.write_text(content)
    append_event(agent_dir, "next", command=command or "complete", auto=auto, step=step_name)


@app.command("resume")
def resume_cmd() -> None:
    """Re-infer pipeline step, write next-step.md, and print current state."""
    from wfctl._pipeline import STORY_COMPLETE_FILE, build_report
    from wfctl._session import session_started
    from wfctl._io import append_event

    agent_dir, repo_root, branch, _ = _resolve_context()

    if not session_started(agent_dir):
        console.print(_NO_SESSION)
        raise typer.Exit(1)

    spec_dir = resolve_spec_dir(branch, repo_root)
    report = build_report(spec_dir, repo_root, agent_dir)
    step_name = report.current or "complete"

    # Gated before anything is written. Refusing afterwards left `next-step.md`
    # deliberately stale while the event log said the session had advanced, so
    # the two disagreed about where it was — after a command that reported
    # failure.
    _refuse_unless_boundary_answered(spec_dir, step_name, repo_root)

    command, auto = report.next_command, report.auto

    next_step_md = agent_dir / "next-step.md"
    if command:
        auto_str = "true" if auto else "false"
        next_step_md.write_text(f"Next step: {command}\nauto: {auto_str}\nRun this command to continue.\n")
        console.print(f"[green]↺[/green] Resumed — step: {step_name}, next: {command} (auto: {auto_str})")
    else:
        next_step_md.write_text(STORY_COMPLETE_FILE)
        console.print(f"[green]↺[/green] Resumed — step: {step_name} — story complete.")

    # `bool` because the log has carried a Boolean here since `next` wrote the
    # first one, and `auto` is None at story complete. Two shapes for one
    # situation is drift in a record nothing can migrate afterwards.
    append_event(
        agent_dir, "resume", step=step_name, command=command or "complete", auto=bool(auto)
    )


# Whether the boundary question was answered, as a word. Three readings rather
# than two: git cannot always tell, and `end` reports what it saw — calling a
# missing answer "answered" is the kind of claim #70 is about.
_BOUNDARY = {True: "answered", False: "unanswered", None: "unknown"}


def _observe(repo_root: Path, report: "PipelineReport") -> "_session.Observations":
    """Read the three facts `end` reports, at the moment it is asked.

    Position comes off the report the caller already built, so the summary file
    and the printed line cannot name different steps.
    """
    from wfctl import _session
    from wfctl import _verify

    current = next((s for s in report.steps if s["is_current"]), None)
    if current is None:
        # Not "complete". `_current_step_name` calls the terminal position that,
        # and it is accurate about the pipeline — but on a handoff line it reads
        # as a verdict on the session, which is the word #70 removed. This names
        # the artifacts instead, and leaves the judgement to whoever reads it.
        step = "every step done"
    else:
        step = f"{current['name']} {current['annotation']}" if current["annotation"] \
            else current["name"]

    _, dirty = _verify.code_identity(repo_root)
    return _session.Observations(
        step=step,
        boundary=_BOUNDARY[touched_on_this_branch(repo_root, arch_root(repo_root))],
        tree="dirty" if dirty else "clean",
    )


@app.command("end")
def end_cmd() -> None:
    """End the current session."""
    from wfctl import _session
    from wfctl._pipeline import build_report

    agent_dir, repo_root, branch, _ = _resolve_context()

    if not _session.session_started(agent_dir):
        console.print(_NO_SESSION)
        raise typer.Exit(1)

    spec_dir = resolve_spec_dir(branch, repo_root)
    observed = _observe(repo_root, build_report(spec_dir, repo_root, agent_dir))
    summary_path = _session.end(agent_dir, branch, observed)

    # "closed", not "ended and complete". Every clause names something read a
    # moment ago; none of them concludes the work is done, because `end` has no
    # way to observe that (#70).
    console.print(
        f"[green]✓[/green] Session closed — {observed.step}, "
        f"boundary {observed.boundary}, tree {observed.tree}."
    )
    # soft_wrap: the path is read by an agent, and rich folds a long one at the
    # console width — which turns the only machine-readable thing `end` prints
    # into two lines that no longer name a file.
    console.print(f"  Summary: {summary_path}", soft_wrap=True)


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
def state_dir_cmd(
    branch: str = typer.Option(
        None, "--branch", help="Another branch's state dir, instead of the active one."
    ),
) -> None:
    """Print a state directory path — the active branch's, or --branch's."""
    import os
    import subprocess as sp

    from wfctl._paths import _STATE_DIR_OVERRIDE

    # This command's whole contract is that stdout is a path — `cd "$(wfctl
    # state-dir)"`, and the handoff writer's `cp … "$(wfctl state-dir --branch
    # X)/session-summary.md"`. The module console is stdout-bound, so a refusal
    # printed through it becomes the destination the caller substitutes in.
    err = Console(stderr=True, highlight=False)

    agent_dir, repo_root, active_branch, _ = _resolve_context()

    # `--branch` exists so a session can write into a branch it is not on — a
    # worktree handoff, written before the child branch has ever been checked
    # out. The layout stays here rather than being reconstructed by the caller:
    # `resolve_agent_dir` has always taken a branch, only the CLI surface didn't.
    if branch and branch != active_branch:
        # A branch name reaching this flag came from an argument, not from git,
        # and it is about to become a path component. git's own parser is the
        # authority on what a ref may contain — it rejects `..` and the rest
        # without a second rule set here to keep in step.
        #
        # The one thing it does not reject is a leading `-`: `check-ref-format
        # refs/heads/-x` exits 0. That name is a legal ref and an illegal
        # argument — the caller's next line is `wm add <branch>`, where `-x`
        # parses as flags. Refused here rather than left for workmux to
        # misread, which is the only rule this needs beyond git's.
        ref_ok = sp.run(
            ["git", "check-ref-format", f"refs/heads/{branch}"], capture_output=True
        )
        if ref_ok.returncode != 0 or branch.startswith("-"):
            err.print(f"[red]✗ not a valid branch name: {branch}[/red]")
            raise typer.Exit(1)
        # The override names one directory outright and has no branch component
        # to substitute, so it can only ever answer for the active branch.
        # Answering with it anyway hands the caller the *active* branch's dir
        # under another branch's name — and the caller is about to write a
        # handoff there, over its own.
        if os.environ.get(_STATE_DIR_OVERRIDE):
            err.print(
                f"[red]✗ {_STATE_DIR_OVERRIDE} pins one directory; "
                f"it cannot resolve --branch {branch}[/red]"
            )
            raise typer.Exit(1)
        agent_dir = resolve_agent_dir(repo_root, branch)

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
                f"[yellow]⚠[/yellow] invoked as `{_FORMER_ARCHIVE_COMMAND}`; renamed "
                "to `archive-specs`.\n"
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


arch_app = typer.Typer(no_args_is_help=True, help="Architecture decision records.")
# A group, not `arch-context`/`arch-none`: `arch-root` is named for `spec-root`,
# which it mirrors, and renaming it into the group would break the one command
# here that already ships.
app.add_typer(arch_app, name="arch")


def _arch_location(root: Path, repo_root: Path) -> str:
    """How a path under the arch root is named in output.

    Repo-relative in-tree, absolute outside, and never with a trailing
    separator — it renders files as well as directories, so a caller that means
    a directory writes the slash itself.

    A record set lives beside the code by default, and printing the absolute
    path for it is noise that differs per machine. Out-of-tree has no relative
    form worth showing, so it stays absolute.

    Escaped here rather than at each print, because one caller forgetting is
    silent: a path containing `[wip]` is legal on every platform and rich reads
    it as a style tag, so the message names a directory that does not exist —
    and `[/y]` raises `MarkupError` instead, killing the message entirely. The
    same hazard `arch-root` documents, in the one place every caller shares.
    """
    from rich.markup import escape

    if not is_in_tree(root, repo_root):
        return escape(str(root))
    rel = root.resolve().relative_to(repo_root.resolve())
    # `Path(".")` when the root *is* the repo root: "./" reads as a stray typo
    # next to a slug, so the absolute path is the clearer name for that case.
    return escape(str(root) if rel == Path(".") else str(rel))


@arch_app.command("context")
def arch_context_cmd() -> None:
    """Print the architectural decisions currently in force.

    Accepted records only. What is proposed, superseded, rejected or retired
    stays on disk for people and is counted here, never listed — a superseded
    record read as live is the confusion `status` exists to prevent.

    This command reports what is in force; it does not judge whether the set is
    correct, and an empty or unreadable set is not an error.

    Falsification test (`plan.md`): this exists instead of a seeded
    `grep -l "^status: accepted"` because `install-config` is seed-once, so a
    fix to a seeded hook reaches only repos seeded afterwards. If in a year this
    command is still equivalent to that grep — no ordering, no exclusion
    counts, no unreadable-record reporting that the grep lacks — it did not need
    to exist, and retiring it is the right call rather than inheriting it.
    """
    import textwrap

    from rich.markup import escape

    from wfctl import _arch

    _, repo_root, _, _ = _resolve_context()
    root = arch_root(repo_root)
    location = _arch_location(root, repo_root)

    records = _arch.load_records(root)
    accepted = _arch.in_force(records)

    if accepted:
        plural = "" if len(accepted) == 1 else "s"
        console.print(
            f"# Architectural contract — {len(accepted)} accepted decision{plural}\n"
        )
        for record in accepted:
            console.print(escape(record.slug))
            decision = _arch.decision_text(record)
            if decision:
                # Wrapped here rather than left to rich, which re-wraps at the
                # terminal edge and drops the indent on continuation lines — the
                # second line of one decision then lines up with the next slug.
                # break_on_hyphens=False keeps "re-derivation" in one piece.
                console.print(escape(textwrap.fill(
                    decision, 74, initial_indent="  ", subsequent_indent="  ",
                    break_on_hyphens=False,
                )))
            console.print()
    else:
        console.print("# Architectural contract — no accepted decisions\n")
        if not records:
            console.print(f"{location}/ holds no records yet.")

    # `excluded` counts the unreadable under "" as well; they get their own
    # sentence below, so both readers filter rather than one popping the key out
    # of a Counter the other still needs.
    excluded = _arch.excluded_by_status(records)
    unreadable = [r.path.name for r in records if not r.status]

    hidden = sum(n for status, n in excluded.items() if status)
    if hidden:
        breakdown = ", ".join(
            f"{n} {status}" for status, n in sorted(excluded.items()) if status
        )
        plural = "" if hidden == 1 else "s"
        console.print(
            f"{hidden} record{plural} not shown ({breakdown}) — {location}/",
            soft_wrap=True,
        )

    if unreadable:
        one = len(unreadable) == 1
        console.print(
            f"[yellow]⚠[/yellow] {len(unreadable)} record{'' if one else 's'} "
            f"{'has' if one else 'have'} no readable status and "
            f"{'was' if one else 'were'} excluded: {escape(', '.join(unreadable))}",
            soft_wrap=True,
        )


@arch_app.command("none")
def arch_none_cmd(
    reason: str = typer.Option(..., "--reason", help="Why this change draws no boundary."),
) -> None:
    """Declare that this change draws no new architectural boundary.

    Written to a file in the change under review rather than to the state dir,
    because the claim's only check is a reviewer reading it and disagreeing.
    wfctl does not verify it: whether a change draws a boundary is a judgment
    with no objective test, unlike completion, which either exits zero or does
    not (FR-010a).

    Kept out of the record set — `docs/architecture/*.md` is decisions, and a
    declaration is the absence of one. The subdirectory is what keeps it out:
    `load_records` globs one level, so a declaration filed beside the records
    would be read as a record with an unreadable status.
    """
    from rich.markup import escape

    from wfctl._io import write_md_atomic

    _, repo_root, branch, _ = _resolve_context()
    root = arch_root(repo_root)

    if not reason.strip():
        # The declaration exists to be a claim a reviewer can disagree with.
        # An empty one is the silent omission the check was built to stop,
        # with an extra command in front of it.
        console.print("[red]✗[/red] --reason cannot be empty: say why no boundary changed.")
        raise typer.Exit(1)

    # `.name`: the branch reaches this as a path segment, and unlike the state
    # dir this write lands in a working tree. Git rejects `..` in a refname, so
    # only `WFCTL_BRANCH` can carry one — but the file is committed, and a write
    # that escapes the arch root is not a mistake to discover after review.
    path = root / "declarations" / f"{Path(branch).name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Overwritten, not appended: one change makes one claim, and a branch that
    # declares twice has changed its mind rather than declared again.
    #
    # Atomic, for the reason `_arch.supersede` gives about the records beside it:
    # this is hand-authored and committed, so a torn write loses a claim no later
    # run can reconstruct.
    # No frontmatter: nothing reads a declaration, and the two fields it carried
    # — branch and date — are the two things git answers about a committed file.
    # `record-format.md` draws the same line for records: the file holds what git
    # cannot.
    write_md_atomic(path, f"# No new boundary — {Path(branch).name}\n\n{reason}\n")
    # The declaration's only check is a reviewer reading it, so "did it land in
    # the change under review?" is the whole question — and both ways it can
    # fail are silent. An out-of-tree root writes outside the repo; a gitignored
    # root writes a file git never reports. Either way the design gate keeps
    # refusing and the escape hatch it names has no effect, so a green ✓ here
    # would send the author back to a command that already did nothing.
    if touched_on_this_branch(repo_root, path) is not True:
        console.print(
            f"[yellow]⚠[/yellow] Wrote {_arch_location(path, repo_root)}, but it is not "
            "part of the change under\n  review — the root is outside the working tree, "
            "or git is ignoring it. No\n  reviewer will see this claim, and the design "
            "step will keep refusing.",
            soft_wrap=True,
        )
        raise typer.Exit(1)

    console.print(f'[green]✓[/green] Recorded: no boundary changed — "{escape(reason)}"')


@app.command("arch-root")
def arch_root_cmd() -> None:
    """Show where this repo's architecture records live.

    Read-only, unlike `spec-root`. The root is declared as `arch_root` in
    `.wf-skills-manifest.json`, and the default needs no command to reach it —
    a repo that wants the records beside its code already has them there.

    Neither creates the root nor requires it to exist: a repo has no records
    until it writes its first one, and reporting "not found" for that state
    would describe a normal repo as broken.
    """
    from rich.markup import escape

    repo_root = get_repo_root()
    root = arch_root(repo_root)
    # escape(): this command's whole job is to name a location, and a path
    # containing `[…]` — legal on every platform — would otherwise be parsed as
    # a style tag and dropped, naming a directory that does not exist.
    console.print(escape(str(root)), soft_wrap=True)

    if not is_in_tree(root, repo_root):
        # A warning, not a finding: this is a configured choice, so the exit code
        # stays 0. What it costs is not obvious from the path alone, which is why
        # the consequence is spelled out rather than labelled "out of tree".
        # soft_wrap: the break is placed here, so rich must not re-place it. Left
        # to wrap, a narrow terminal splits the second line mid-sentence and the
        # hanging indent stops lining up.
        console.print(
            "[yellow]⚠[/yellow] Root is outside the working tree. Records will not "
            "share a commit with the\n  code implementing them, and will not reach "
            "anyone who clones this repo.",
            soft_wrap=True,
        )


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
_BASE_SKILL_ROOT = ".agents/skills"
_BASE_TARGETS = [
    ("agents/skills", _BASE_SKILL_ROOT),
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

# The merge install mode's one target — see `docs/architecture/install-modes.md`
# for why merge exists and why it is claude-only.
#
# Repo-local `.claude/settings.json`, not the user-global one: the hook reads the
# skills *this repo* installed, so a global entry would fire in every checkout on
# the machine, including ones that never ran `install-skills`.
#
# The command is a fixed string, not derived from which skills are installed —
# per `research.md`'s command-name decision, a new digest-bearing skill reaches
# a consumer's next session with no re-install, and `doctor`'s "behind" check
# narrows to real drift (wfctl renamed the subcommand) rather than firing every
# time any skill gains a digest.
SETTINGS_PATH = ".claude/settings.json"
SETTINGS_EVENT = "UserPromptSubmit"
STOP_EVENT = "Stop"

# The hooks `wfctl hook` can run. These names are an interface: they are what a
# consumer's settings.json invokes, so renaming one breaks every settings file
# already pointing at it. Beside `HOOK_COMMAND` rather than beside the sub-app
# that answers them, because the installed command and the name it dispatches
# on are the same fact, and 1200 lines apart they drift.
_USER_PROMPT = "user-prompt"
_WORKTREE_GUARD = "worktree-guard"
_RESPONSE_SHAPE = "response-shape"

HOOK_COMMAND = f"{_settings.MANAGED_PREFIX}{_USER_PROMPT}"
# `|| true`, unlike the `UserPromptSubmit` entry, because the events differ in
# what a non-zero exit means. On `Stop` it *blocks the stop*: the agent is told
# to keep going and stops again, so a wfctl that cannot run this — one older than
# the settings file, or uninstalled from PATH without `uninstall-skills` — turns
# a usage banner into a loop at the end of every turn.
#
# Nothing is lost by swallowing it. This hook warns and never blocks, so it has
# no non-zero exit of its own to report; every one it could produce is a version
# mismatch or a bug, and neither is worth a per-turn error on work that was fine.
STOP_HOOK_COMMAND = f"{_settings.MANAGED_PREFIX}{_RESPONSE_SHAPE} 2>/dev/null || true"

# Event → the command this wfctl installs for it. One map rather than a pair of
# constants because three separate places have to agree on it: the merge, the
# uninstall record it writes, and `doctor`'s freshness check. The two entries are
# opposite halves of the same skill — `UserPromptSubmit` re-anchors the rules
# before a reply is written, `Stop` looks at what was actually written (#212).
MANAGED_HOOKS = {SETTINGS_EVENT: HOOK_COMMAND, STOP_EVENT: STOP_HOOK_COMMAND}

# What `doctor` says a missing entry costs. Per event, because the two lose
# different things and "the managed hook is gone" tells the reader neither.
_HOOK_GONE = {
    SETTINGS_EVENT: "is gone — the skills it re-anchors decay again mid-session",
    STOP_EVENT: "is gone — nothing looks at a reply once it is written",
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


def _agent_flag(layer: str) -> str:
    """The `--agent` a repair command needs to reach this layer, or nothing.

    The base layer is what `install-skills` writes with no flag, so naming it
    would print an agent that `_AGENT_TARGETS` does not have. Every other layer
    is only rewritten when it is asked for by name.
    """
    return "" if layer == _BASE_LAYER else f" --agent {layer}"


def _recorded_path(repo_root: Path, rel: str) -> Path | None:
    """Join a manifest-recorded path onto the repo, refusing one that escapes it.

    Every path wfctl writes is recorded as `dest.relative_to(repo_root)`, so a
    rejection here means a hand-edited or corrupted manifest rather than anything
    wfctl produced. It is checked because it guards a delete: `Path` joining
    silently discards the left operand when the right is absolute, so a single
    bad row would have `remove` reach outside the project entirely.

    Lexical rather than resolved. Resolving would follow a symlinked install path
    through to its target, which is the one thing removal must not do — see
    `_remove_recorded`.
    """
    path = Path(rel)
    if path.is_absolute() or ".." in path.parts:
        return None
    return repo_root / rel


def _remove_recorded(path: Path) -> None:
    """Remove a path wfctl recorded, whatever kind it turns out to be.

    `is_dir()` follows a symlink and `shutil.rmtree` refuses one, so the obvious
    directory-or-file branch does not merely mis-handle a linked path — it raises
    partway through and takes the whole command down with it. Linking installed
    paths in from a main checkout is a real layout: #38's evidence found twelve
    worktrees doing exactly that.

    The link is what the record names, so the link is what goes; whatever it
    points at belongs to whoever made it and is never wfctl's to delete. Tested
    before `is_file`/`is_dir` because both follow the link, and before any
    `exists()` check because a dangling link is invisible to it and still ours to
    clear.
    """
    import shutil

    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _recorded_items(manifest: dict) -> list[dict]:
    """Every `items` entry across every layer, flattened.

    Both callers want the same traversal and neither wants the layer it came
    from: `install-skills` keys them by path for backup bookkeeping, `doctor`
    keeps only the paths. Written out twice, the two drift the moment an entry
    grows a field or a layer needs filtering.
    """
    return [i for key in _layer_keys(manifest) for i in manifest[key].get("items", [])]


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


# The skills Claude discovers natively, declared here rather than marked in each
# SKILL.md. A file-level mark cannot cover a vendored skill — the next upstream
# pull drops whatever we added — and it put authority over a layer's contents in
# the files instead of the installer that owns them (`layer-model`).
#
# A name here also suppresses `<name>.md` from the *mirroring layer's* command
# directory — see `_mirror_supersedes_wrapper`. The wrapper still ships, and
# every other layer still gets it.
_MIRRORED_SKILLS = frozenset({
    "architecture-decisions",
    "conversation-response-shape",
    "design-levels",
    "fanning-out-code-review",
    "i-have-adhd",
    # Removing this entry restores #124 rather than trimming a list: the skill
    # still ships and still installs, its wrapper un-suppresses on the same run,
    # and the only remaining way to reach it is a human typing that wrapper —
    # which is the failure it was written for. Nothing else in the tree says the
    # skill has to be discoverable.
    "opening-a-change",
    "receiving-code-review",
    # The one gate `speckit-orchestrate` opens with names `/start-session` as
    # its remedy, and the flag on that wrapper governs the Skill tool rather
    # than the filesystem: an agent reaching for `Skill(start-session)` is
    # refused, an agent that reads the wrapper's body follows its pointer and
    # runs the workflow whole. Both happened on 2026-09-06 (#204). Mirroring
    # does not make a refused route work — it removes the fork, so the outcome
    # stops depending on which way the agent reached.
    #
    # Its `allowed-tools:` sits on the SKILL.md rather than the wrapper, because
    # suppression drops a wrapper whole and `.claude/commands/` was the only
    # place that key was ever read unstripped. On a skill the same grant reaches
    # a model-initiated invocation, `Bash(wfctl install-skills*)` included —
    # sanctioned by the Safety section of this repo's AGENTS.md, which already
    # has `/start-session` refreshing a stale mirror unattended.
    "start-session",
    "using-superpowers",
    "verification-before-completion",
    "worktree-handoff",
})


# The destination the mirror below owns — shared with Claude Code itself, with
# its plugins, and with whatever the user keeps there. Named here, beside the
# mirror, because the abandoned-entry scan has to look in this directory and a
# root produced inline is a root nothing else can ask about. The alternative was
# widening the extras hook to return its root alongside the path; that grows a
# contract to serve its single implementation.
_CLAUDE_NATIVE_SKILL_ROOT = ".claude/skills"


# Frontmatter keys that are Claude-specific and have no meaning in Bob Shell.
# `disable-model-invocation: true` causes Bob Shell to skip model invocation
# entirely — the skill body never executes. That is the bug where /end-session
# and other commands do nothing when invoked in Bob Shell.
_CLAUDE_ONLY_FRONTMATTER_KEYS = frozenset({
    "allowed-tools",
    "disable-model-invocation",
})


def _strip_claude_frontmatter(text: str) -> str:
    """Remove Claude-only frontmatter keys from a command file's content.

    Drops lines whose key matches _CLAUDE_ONLY_FRONTMATTER_KEYS from the
    leading YAML block. Drops the block entirely if no keys remain after
    stripping. Returns text unchanged when there is no front matter or the
    block has no closing fence.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    close = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            close = i
            break
    if close is None:
        return text
    kept = ["---\n"]
    for line in lines[1:close]:
        key = line.split(":", 1)[0].strip()
        if key not in _CLAUDE_ONLY_FRONTMATTER_KEYS:
            kept.append(line)
    # Drop the block entirely if nothing remains between the fences.
    if all(ln.strip() == "---" for ln in kept):
        return "".join(lines[close + 1:])
    kept.append(lines[close])
    kept.extend(lines[close + 1:])
    return "".join(kept)


def _copy_command_for_bob(src: "Path", dest: "Path") -> None:
    """Copy a command file to a Bob destination, stripping Claude-only frontmatter."""
    dest.write_text(_strip_claude_frontmatter(src.read_text(encoding="utf-8")), encoding="utf-8")


def _claude_native_skill_mirror(
    repo_root: Path, item: Path
) -> tuple[str, Path, Path] | None:
    """Claude extra: a skill under .agents/skills named in `_MIRRORED_SKILLS` also
    mirrors to .claude/skills/<name> (Claude's native discovery path), on top of
    the .agents/skills reference copy every agent gets. None if it doesn't apply."""
    if not item.is_dir() or item.name not in _MIRRORED_SKILLS:
        return None
    dest = repo_root / _CLAUDE_NATIVE_SKILL_ROOT / item.name
    return str(dest.relative_to(repo_root)), dest, item


# Per-agent hook for extra mirrors beyond the plain (src, dst) copy in
# _AGENT_TARGETS, keyed the same way — dispatch by agent, not by growing
# `if agent == "..."` branches. Called once per item under .agents/skills;
# returning None means "nothing extra for this item".
_AGENT_SKILL_EXTRAS = {
    "claude": _claude_native_skill_mirror,
}


def _mirror_supersedes_wrapper(layer: str, agent: str, src_rel: str, item: Path) -> bool:
    """Whether this agent's own command layer should skip `item`, because the
    mirror already put the same name on its native discovery path.

    `layer` is a parameter rather than a caller-side guard because the per-layer
    scope below is the entire correctness argument, and a contract stated in a
    docstring while enforced at one call site is a contract the next call site
    does not get.

    Both files claim one `/name`. Claude Code documents the skill as winning that
    tie; a session on 2026-09-04 got the wrapper instead, and its
    `disable-model-invocation` refused the Skill tool for the very skill the
    wrapper points at — while another session the same day, same machine, got the
    skill and ran it (#170). Which one wins is not wfctl's to set, so the fix is
    to stop shipping the tie into the layer that has both.

    Suppressed per layer, never from the bundle, and that distinction is the
    whole correctness of this function. The wrapper is one file whose body is
    "read the sibling skill", and it is still the only typed route for a layer
    that gets no mirror — `_AGENT_TARGETS` gives bob `.bob/commands/`, where
    `_copy_command_for_bob` strips the key Bob Shell reads as "never execute the
    body". Deleting the wrapper from the bundle instead would hand bob the
    vendored `i-have-adhd` skill with that key intact and no stripped copy left
    to reach it: a Claude-shaped argument taking out a layer it never described.

    Keyed on `_AGENT_SKILL_EXTRAS` rather than on `agent == "claude"`, because
    what makes a wrapper redundant is that this agent got the mirror, not its
    name. An agent added to that table later inherits the suppression with it.
    """
    return (
        layer == agent
        and src_rel == "agents/commands"
        and agent in _AGENT_SKILL_EXTRAS
        and item.stem in _MIRRORED_SKILLS
    )


def _read_settings(path: Path) -> tuple[dict | None, str | None]:
    """Parse a consumer-owned settings file. `(settings, problem)`.

    `settings` and `problem` are mutually exclusive.

    A missing file is `({}, None)` — not an error, and the case the acceptance
    criterion calls out: a consumer who has never written one gets a valid file
    created underneath their install.

    A file that exists and cannot be parsed is a refusal, never a fresh `{}`.
    Defaulting there would let one stray comma cost the consumer every permission
    and hook they had, which is the exact damage this whole mode exists to avoid.

    Decoded as `utf-8-sig` so a leading BOM is consumed rather than reported: an
    editor that writes one is not a broken file, but it made the merge refuse
    every time and named no way out of it.
    """
    if not path.exists():
        return {}, None
    try:
        settings = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, str(exc)
    if not isinstance(settings, dict):
        return None, "top level is not an object"
    return settings, None


def _write_settings(path: Path, settings: dict) -> None:
    """Write a consumer-owned settings file back, disturbing it as little as
    a JSON round-trip allows.

    Rewriting parsed JSON reflows the file — key order and array layout are gone
    the moment it round-trips, and no amount of care here brings them back short
    of a format-preserving parser, which is a runtime dependency for one file.
    Indent is Claude Code's own two spaces; sniffing the consumer's width bought
    half a guarantee at the cost of threading the source text through every
    caller, while key order went anyway.

    `ensure_ascii=False` because this file is committed and read by a person:
    escaping every accented character in a path they typed is churn in the diff,
    not safety. `write_md_atomic` rather than `write_json_atomic`, only for the
    trailing newline every other text file in their repo ends with.

    Resolved first, and the mode carried over, because `os.replace` installs a
    fresh inode: onto a symlink it swaps the consumer's link for a regular file
    and leaves the file they actually read untouched, and it would hand back
    whatever mode `mkstemp` chose rather than the one they set.
    """
    from wfctl._io import write_md_atomic

    target = path.resolve()
    mode = target.stat().st_mode & 0o777 if target.exists() else None
    write_md_atomic(
        target, json.dumps(settings, indent=2, ensure_ascii=False) + "\n"
    )
    if mode is not None:
        target.chmod(mode)


def _merge_hooks(
    repo_root: Path, agent: str, prior: dict[tuple[str, str], dict]
) -> tuple[list[dict], list[str], list[str]]:
    """Install `agent`'s managed hooks. `(records, written, problems)`.

    `records` is what the manifest stores so uninstall can find these entries
    again; it is recorded even when nothing was written, because an entry already
    correct is still one wfctl owns and must remove on the way out.

    Writes only when `merge_hook` reports a change. That is half the answer to the
    one real cost of this mode — a rewrite reflows the consumer's file, so a
    re-install that changes nothing must not open it at all. `_write_settings` is
    the other half. Between them the file is reflowed once, on the install that
    first adds the entry, and never again.
    """
    records: list[dict] = []
    written: list[str] = []
    problems: list[str] = []
    targets = (
        [(SETTINGS_PATH, e, c) for e, c in MANAGED_HOOKS.items()]
        if agent == "claude"
        else []
    )
    # `or is_symlink`, because `exists()` follows the link: a symlink whose
    # target does not exist yet read as "nothing here", and wfctl recorded a
    # file it had created. Uninstall deletes what it created — which would be
    # the consumer's symlink, not the settings inside it.
    #
    # Per file, not per target, and taken from any prior record for that file
    # before the disk is consulted. `created` answers "did wfctl bring this file
    # into existence", which is a fact about the file; two events share one, and
    # uninstall unlinks only when the record that empties the file says `created`.
    # Sampling it per target gets that record wrong twice — within one pass, where
    # the second event sees the file the first just made, and across an upgrade,
    # where a repo installed when wfctl managed one event records `created: False`
    # on the second. Either way uninstall leaves an empty `{}` behind.
    created = {
        rel: next(
            # `.get`, not `[...]`: the manifest is on disk, gitignored and
            # hand-editable, and an install that raises on a record missing a key
            # is a crash where the honest answer is "then wfctl did not create
            # this file". False is also the safe side of the guess — it costs an
            # empty `{}` left behind, where True costs a consumer's file.
            (p.get("created", False) for (path_, _), p in prior.items() if path_ == rel),
            not ((repo_root / rel).exists() or (repo_root / rel).is_symlink()),
        )
        for rel, _, _ in targets
    }
    for rel, event, command in targets:
        path = repo_root / rel
        # A pass that cannot finish must still hand back the record it was given.
        # The manifest layer is rewritten whole on every install, so a record not
        # re-emitted here is not stale — it is gone, and with it wfctl's claim on
        # an entry still sitting in the consumer's file for uninstall to remove.
        keep = prior.get((rel, event))
        settings, problem = _read_settings(path)
        if settings is None:
            problems.append(f"{rel}: {problem}")
            records.extend([keep] if keep else [])
            continue
        try:
            changed = _settings.merge_hook(settings, event, command)
        except ValueError as exc:
            problems.append(f"{rel}: {exc}")
            records.extend([keep] if keep else [])
            continue
        if changed:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                _write_settings(path, settings)
            except OSError as exc:
                # Same arm as the two above rather than an escape: this runs after
                # the skill copies and before the manifest is saved, so raising
                # here left the copies on disk with nothing recording them.
                problems.append(f"{rel}: {exc}")
                records.extend([keep] if keep else [])
                continue
            # By file, not by entry: two events share `.claude/settings.json`, and
            # the block this feeds is about the file staying the consumer's.
            if rel not in written:
                written.append(rel)
        # `created` is what lets uninstall leave no trace: a file wfctl brought
        # into existence and then emptied is deleted, while one the consumer
        # already had keeps whatever else is in it. Derived above, per file.
        records.append(
            {"path": rel, "event": event, "command": command,
             "created": created[rel]}
        )
    return records, written, problems


def _unmerge_hooks(
    repo_root: Path, records: Iterable[dict]
) -> tuple[int, list[str]]:
    """Remove the managed hooks `records` describes. `(files changed, problems)`.

    A file that has gone needs no action — uninstall's job is to leave nothing of
    wfctl's behind, and there is nothing there. A file that has stopped *parsing*
    is different: one stray comma still leaves wfctl's entry sitting in it, and
    the record naming it is deleted moments later. Reported rather than raised,
    so a broken settings file cannot block the rest of the uninstall.
    """
    changed: set[str] = set()
    problems: list[str] = []
    for record in records:
        path = repo_root / record["path"]
        if not path.exists():
            continue
        settings, problem = _read_settings(path)
        if settings is None:
            problems.append(f"{record['path']}: {problem}")
            continue
        if not _settings.remove_hooks(settings, record["event"]):
            continue
        if not settings and record.get("created"):
            path.unlink()
        else:
            _write_settings(path, settings)
        # By file, not by record — `_merge_hooks` counts `written` the same way
        # and for the same reason: two managed events share one settings file,
        # and the summary this feeds says "settings file(s)".
        changed.add(record["path"])
    return len(changed), problems


def _kind_of(src_rel: str, item: Path | None = None) -> str:
    """What an item is, for the install summary — 'skill', 'command', 'runtime'.

    Derived from the source directory, so a new target picks up a sensible label
    without a second lookup table to keep in sync.

    A skill is a directory. `agents/skills` also holds `NOTICES.md`, which has to
    sit beside the skills it covers to reach an installed project at all — and
    counting it as one made a bare install report 34 skills over 33 directories
    (#216). It counts as a `notice` rather than falling through to `runtime`,
    which is the specify tree's label and would have moved the miscount rather
    than fixed it. What is installed does not change; only the line that counts it.
    """
    label = {"skills": "skill", "commands": "command"}.get(src_rel.rsplit("/", 1)[-1], "runtime")
    if label == "skill" and item is not None and not item.is_dir():
        return "notice"
    return label


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
    prune: bool = typer.Option(
        False,
        "--prune",
        help="Delete paths a previous install recorded that this one no longer "
        "ships. Without it they are named and left alone.",
    ),
    tracker: str = typer.Option(
        None,
        "--tracker",
        help="Issue-tracker backend: 'github' (ships), 'none' to clear, or a "
        "custom name whose .agents/trackers/<name>.json you author. Omit to leave unchanged.",
    ),
    # `from` is a keyword, so the parameter cannot carry the flag's name. The
    # option string is what the user types and what `doctor`'s remedy prints.
    source: str = typer.Option(
        None,
        "--from",
        help="Install from this bundle root instead of the running wfctl. "
        "Accepts a checkout root or the package directory inside it.",
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

    from rich.markup import escape

    # Said before the install runs, so the reason arrives ahead of a summary
    # that would otherwise look like the agent was simply ignored.
    if agent in _AGENT_NOTICES:
        console.print(f"[cyan]ℹ[/cyan] {_AGENT_NOTICES[agent]}")

    # Before anything is read from the repo and long before anything is written
    # to it, so a path that resolves to nothing leaves the project exactly as it
    # was. Never falls back to the running bundle: a run that reported success
    # over a tree the caller did not name is the confusion #146 opens with.
    bundle_root = _bundle.BUNDLE_ROOT
    if source is not None:
        try:
            bundle_root = _bundle.resolve_root(Path(source))
        except FileNotFoundError as e:
            console.print(f"[red]✗ {e}[/red]", soft_wrap=True)
            raise typer.Exit(1) from e

    # Who to blame when a tree the install expects is not there. The wheel ships
    # complete, so its absence is a broken install; a root the caller named is
    # theirs to fix, and `resolve_root` admits a partial one on purpose.
    origin_label = (
        f"the source you named ({escape(str(bundle_root))})"
        if source is not None
        else f"this wfctl install ({escape(str(bundle_root))})"
    )

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
    prior_items = {i["path"]: i for i in _recorded_items(manifest)}
    # The same records kept per layer, because the orphan diff below is only
    # sound within a layer. A path also leaves the record when the user installs
    # a narrower set of layers, so a whole-manifest diff would call every path of
    # a layer they deselected abandoned. Read here rather than later: the loop
    # that writes the new record replaces these entries wholesale.
    prior_layer_items = {k: manifest[k].get("items", []) for k in _layer_keys(manifest)}

    # `--from` is one-shot, so a bare install silently discards it. Said before
    # the copy, and deliberately not gated on `--yes`: `/start-session` refreshes
    # a stale mirror unattended with `--yes`, which makes that the one place the
    # discard happens without anyone choosing it. Scoped to the layers this run
    # rewrites, which always include base — `layered` below appends
    # `_BASE_TARGETS` on every run, so even `--agent claude` rewrites base's
    # record and drops its source. What the scoping excludes is the *other* agent
    # layers, whose records this run does not touch.
    if source is None:
        rewritten = {_BASE_LAYER, agent} & set(_layer_keys(manifest))
        for prior_source in sorted(
            {s for k in rewritten if (s := manifest[k].get("source"))}
        ):
            # Future tense: the foreign-overwrite prompt below can still abort
            # the run, and "Replacing" would have described something that never
            # happened.
            console.print(
                f"[yellow]⚠[/yellow] Will replace an install from "
                f"{escape(prior_source)} with wfctl {_wfctl_version()} "
                "— no source named",
                soft_wrap=True,
            )

    # A worktree inherits the project's choice rather than being asked again,
    # from the main checkout's manifest — the same fallback `spec_root` resolves
    # through, and for the same reason: the manifest is gitignored, so a
    # worktree's copy starts empty and dies with the worktree, which leaves the
    # main checkout the only durable place a project-level decision can live.
    # Without this the question below is never posed in a worktree at all, since
    # every install in its lifecycle is non-interactive (post_create is a hook,
    # /start-session passes --yes). An absent key is not "declined" — it is
    # permanently unasked, and `wfctl issue` no-ops in silence for the life of
    # the worktree.
    #
    # The parallel with `spec_root` stops at the lookup: that resolves on every
    # read and stays authoritative, while this copies once into a manifest that
    # later installs then leave alone. A worktree outliving a change of tracker
    # keeps the old one. Copying is what `--tracker` already means here, and the
    # alternative — resolving the backend at dispatch time — would have
    # `_tracker.py` execute argv out of a config file belonging to a different
    # checkout. `spec_root` inherits a path; this would inherit a command.
    if tracker is None and "tracker" not in manifest:
        main = main_checkout(repo_root)
        inherited = _load_manifest(main) if main is not None else {}
        if "tracker" in inherited:
            name = inherited["tracker"]
            # Recorded even when it is None: a decline is a decision, and
            # recording it is what closes the question here too.
            manifest["tracker"] = name
            # `tracker` is not the choice — it is "the caller selected one on
            # this run", and it is what plans a copy of the backend's config
            # below. Set it only when this checkout has no config to copy over:
            # `.agents/trackers/` is deliberately not gitignored, so a project
            # that commits its backend has the file already, and planning a write
            # over it classifies a tracked file as a foreign overwrite — which
            # aborts the whole install on the TTY-less hook this exists to fix,
            # and silently replaces the project's config under --yes.
            if name:
                if not (repo_root / ".agents" / "trackers" / f"{name}.json").exists():
                    tracker = name
                # Announced for the same reason the spec-root write below is: a
                # decision that arrives from another checkout, and that a later
                # `--tracker none` here cannot durably undo, is not one to make
                # in silence.
                console.print(
                    f"[dim]Tracker '{escape(name)}' inherited from "
                    f"{escape(str(main))}[/dim]",
                    soft_wrap=True,
                )

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
        src = bundle_root / src_rel
        dst = repo_root / dst_rel
        if not src.exists():
            # Two ways to arrive here, and they blame opposite parties. Without
            # `--from` the bundle ships with the package, so a missing tree means
            # the wheel lost files — named as such, since "not found in
            # wf-skills@main" used to send people to look upstream for a problem
            # on their own disk. With `--from` the tree is one the caller chose,
            # and `resolve_root` accepts a root holding only one of them because a
            # partial bundle is a real state during a re-sync; saying "this wfctl
            # install" there sends them to reinstall the wheel over a typo.
            # soft_wrap, like every other line here that carries a path: rich
            # breaks a long one across two lines, and a wrapped path is one the
            # reader cannot copy or grep for.
            console.print(
                f"[yellow]⚠[/yellow] Expected '{src_rel}' missing from "
                f"{origin_label} — skipping (nothing installed for this path)",
                soft_wrap=True,
            )
            continue
        for item in src.iterdir():
            if _mirror_supersedes_wrapper(layer, agent, src_rel, item):
                continue
            dest = dst / item.name
            rel_dest = str(dest.relative_to(repo_root))
            plan.append((layer, _kind_of(src_rel, item), rel_dest, dest, item))
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
        tsrc = bundle_root / "agents" / "trackers" / "github.json"
        if tsrc.exists():
            tdest = repo_root / ".agents" / "trackers" / "github.json"
            trel = str(tdest.relative_to(repo_root))
            plan.append((_BASE_LAYER, "tracker", trel, tdest, tsrc))
            if tdest.exists() and trel not in prior_items:
                foreign_overwrites.append((_BASE_LAYER, trel))
        else:
            console.print(
                "[yellow]⚠[/yellow] --tracker github, but "
                "agents/trackers/github.json is missing from "
                f"{origin_label} — nothing installed for it"
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
        content_hash = _bundle.content_hash(bundle_root)
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
        elif agent == "bob" and rel_dest.startswith(".bob/commands/"):
            _copy_command_for_bob(item, dest)
        else:
            shutil.copy2(item, dest)
        count += 1
        items.setdefault(layer, []).append({"path": rel_dest, "backup": backup_rel})
        summary.setdefault(layer, {})
        summary[layer][kind] = summary[layer].get(kind, 0) + 1

    # After the copies, before the manifest write: the hook the merge installs
    # runs `wfctl hook user-prompt`, which reads the skills the loop above just
    # placed, and the manifest below has to record what the merge decided.
    #
    # No confirmation prompt, unlike a foreign overwrite. The prompt exists
    # because a mirror destroys whatever it lands on; a merge cannot — it adds
    # one entry and leaves every other byte of meaning in the file alone. The
    # edit is still named in the summary, because a consumer-owned file is one
    # nobody should find changed without being told.
    prior_merged = {
        (m["path"], m["event"]): m
        for key in _layer_keys(manifest)
        for m in manifest[key].get("merged", [])
    }
    merged, merge_written, merge_problems = _merge_hooks(repo_root, agent, prior_merged)

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
    #
    # `source` is written only when one was named. Absence means the default,
    # and it is a complete answer rather than a gap: before `--from` the running
    # tool was the only source there was, so every manifest predating it reads
    # correctly with no migration. That is what separates it from `content_hash`,
    # whose absence is genuinely unmeasurable and warns.
    for layer, layer_items in items.items():
        manifest[layer] = {
            "wfctl_version": wfctl_version,
            "content_hash": content_hash,
            "installed_at": installed_at,
            "items": layer_items,
            **({"source": str(bundle_root)} if source is not None else {}),
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

    # A sibling of `items`, never a member of it. `uninstall-skills` deletes
    # every path in `items` outright, so recording `.claude/settings.json` there
    # would have wfctl remove a file it only ever edited one entry of — the
    # consumer's permissions and their own hooks with it.
    if merged:
        manifest.setdefault(agent, {})["merged"] = merged

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

    # Paths a previous install recorded under a layer this install rewrote, and
    # that this install did not write. What makes removal defensible here and
    # nowhere else is that the evidence is wfctl's own record: the manifest says
    # wfctl put the file there, so this is not a guess about who owns it.
    #
    # `doctor` reports the same files by scanning disk against the current
    # record, and that is the half it keeps. It has to guess — a path missing
    # from the record looks identical whether it was renamed upstream or fell
    # out because a layer was deselected — which is why it may only report.
    # Here the two cases are already separated: a deselected layer is not in
    # `items`, so it is never diffed. Report stays with `doctor`, removal stays
    # here, and neither grows the other's half.
    #
    # Diffed against every layer's new paths rather than the layer's own, so a
    # path that moved between layers — the pre-layer-split `none` entry is the
    # live case — is seen as still installed instead of dropped.
    installed_paths = {i["path"] for entries in items.values() for i in entries}
    orphans = sorted(
        (
            (layer, i)
            for layer in items
            for i in prior_layer_items.get(layer, ())
            if i["path"] not in installed_paths
        ),
        key=lambda pair: pair[1]["path"],
    )

    restored_originals = 0
    if prune:
        for _, item in orphans:
            path = _recorded_path(repo_root, item["path"])
            if path is None:
                console.print(
                    f"[yellow]⚠[/yellow] {item['path']} is recorded as a path "
                    "outside this repo — left alone",
                    soft_wrap=True,
                )
                continue
            _remove_recorded(path)

            # The same undo `uninstall-skills` performs on a recorded item, for
            # the same reason: the backup is the user's own file from before
            # wfctl overwrote the path. Dropping the path without putting it back
            # strands it under `.wf-skills-backup/` with its record gone and
            # nothing left that would ever restore it — the defect this flag
            # exists to fix, one directory over.
            backup_rel = item.get("backup")
            backup = _recorded_path(repo_root, backup_rel) if backup_rel else None
            if backup is not None and backup.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(backup), str(path))
                restored_originals += 1
    else:
        # Kept in the record rather than dropped with the install that stopped
        # shipping them. Replacing the layer wholesale is what put the original
        # orphan out of reach: the file stays on disk and the only note that
        # wfctl wrote it disappears, so neither `--prune` nor `uninstall-skills`
        # can ever name it again. Reporting a path and erasing its record in the
        # same breath would make the line above advice nobody can act on — the
        # re-run it points at would diff against a record that no longer holds
        # the path.
        #
        # `uninstall-skills` reaching them too is the point, not a side effect:
        # they are wfctl's output, and a teardown that leaves them behind is the
        # same defect wearing the other command's name.
        for layer, item in orphans:
            items[layer].append({**item, "orphaned": True})
            manifest[layer]["items"] = items[layer]

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

    if orphans and not prune:
        one = len(orphans) == 1
        console.print(
            f"[yellow]⚠[/yellow] {len(orphans)} path{'' if one else 's'} a previous "
            f"install recorded {'is' if one else 'are'} no longer shipped, and "
            f"{'it is' if one else 'they are'} still on disk:"
        )
        for _, item in orphans:
            console.print(f"    {item['path']}", soft_wrap=True)
        # Named as a re-run of this command, not as a cleanup command of its own:
        # the diff only exists during an install, so there is nothing else to run.
        console.print(
            "    Re-run with --prune to delete "
            f"{'it' if one else 'them'}, once you've checked nothing needs "
            f"{'it' if one else 'them'}."
        )

    elif orphans:
        line = f"[yellow]ℹ[/yellow] Pruned {len(orphans)} path(s) this wfctl no longer ships"
        if restored_originals:
            # Worth its own clause: those paths are not gone, they hold the
            # user's own file again, and a bare "pruned" would read as deleted.
            line += (
                f" — {restored_originals} of them held a pre-existing file wfctl "
                "had overwritten, and it was put back"
            )
        console.print(line)

    for problem in merge_problems:
        # A warning, not a failure. Everything else in this install landed, and
        # the repo is usable without the hook — refusing here would trade a
        # working install for an unparseable settings file the user has to fix
        # before they can have either.
        console.print(
            f"[yellow]⚠[/yellow] {problem} — left untouched; the managed hook "
            "was not added or updated",
            soft_wrap=True,
        )

    # The path as typed, not the resolved one the manifest holds: this line is
    # read next to the command that produced it, and `../116-pr` is what the
    # reader can match against what they wrote.
    installed_from = escape(source) if source is not None else f"wfctl {wfctl_version}"
    console.print(
        f"[green]✓[/green] Installed from {installed_from}",
        soft_wrap=True,
    )
    for line in _format_summary(summary):
        console.print(line)
    for merged_rel in merge_written:
        # Its own block, below a blank line rather than indented under the ✓.
        # The lines above it are counts of files wfctl owns outright; this is the
        # one file in the install that stays the consumer's, and reading as a
        # third count would bury exactly the thing worth noticing.
        console.print(
            f"\n[green]✓[/green] Merged wfctl's managed hooks into {merged_rel}\n"
            "  Your own hooks, permissions and settings are still there — "
            "`wfctl uninstall-skills`\n  removes just wfctl's own entries. The rewrite "
            "reflows the file once; later installs\n  leave it closed.",
            soft_wrap=True,
        )

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
    for item in entry.get("items", []):
        path = _recorded_path(repo_root, item["path"])
        if path is None:
            console.print(
                f"[yellow]⚠[/yellow] {item['path']} is recorded as a path outside "
                "this repo — left alone",
                soft_wrap=True,
            )
            continue
        _remove_recorded(path)

        backup_rel = item.get("backup")
        backup_path = _recorded_path(repo_root, backup_rel) if backup_rel else None
        if backup_path is not None and backup_path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(backup_path), str(path))
            restored += 1
        else:
            removed += 1

    # Before the manifest is dropped, because the record is the only thing that
    # says which file and which event wfctl edited. Recomputing it from
    # `SETTINGS_PATH`/`SETTINGS_EVENT` would miss an entry installed by an older
    # wfctl that merged somewhere this one no longer does — and leave it
    # running forever.
    unmerged, unmerge_problems = _unmerge_hooks(repo_root, entry.get("merged", []))
    for problem in unmerge_problems:
        console.print(
            f"[yellow]⚠[/yellow] {problem} — wfctl's hook entry may still be in "
            "this file; the record naming it is being removed either way",
            soft_wrap=True,
        )

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
    if unmerged:
        # soft_wrap, break placed by hand: rich re-wraps at the terminal edge and
        # splits "in place" across two lines under an indent that then stops
        # lining up with the ✓ above it.
        console.print(
            f"  Removed the managed hook from {unmerged} settings file(s).\n"
            "  Your own entries in them were left alone.",
            soft_wrap=True,
        )


# What one skill may spend of a turn's context. The digest is a reminder, not the
# skill — anything past this is a file that has stopped being one, and the cost
# lands on every turn of every session in the repo rather than once.
_DIGEST_MAX_CHARS = 500


# What a skill directory may be called, for the purpose of printing its name into
# an agent's context. Deliberately narrower than the filesystem allows: the name
# is interpolated beside the digest, so anything that can carry a newline can
# forge a second bullet the same way a digest's own text could. Reaching this
# needs local write access to the gitignored manifest rather than a clone — but
# once it is attacker-supplied, the name is as much so as the text.
_SKILL_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*$")


def _installed_skill_names(manifest: dict) -> list[str]:
    """Skills the manifest records under `.agents/skills/`, sorted by name.

    Sorted rather than kept in manifest order: the manifest's order is install
    order, which is an implementation detail of whichever run wrote it, and the
    hook's output is read by a person often enough to be worth a stable one.

    The manifest, not the directory listing, is what makes a skill installed.
    `.gitignore` gets one line per installed skill, so a directory wfctl never
    installed is not covered by it and rides along in a clone — and the hook is
    wired by a *committed* `.claude/settings.json`. Reading the filesystem let a
    repository put text of its choosing into the reader's context on every turn,
    under a header saying that text governs the response. Reading the manifest
    means a clone re-anchors what its owner installed and nothing else.
    """
    prefix = ".agents/skills/"
    names = {
        item["path"][len(prefix):]
        for item in _recorded_items(manifest)
        if isinstance(item, dict)
        and isinstance(item.get("path"), str)
        and item["path"].startswith(prefix)
        and _SKILL_NAME.fullmatch(item["path"][len(prefix):])
    }
    return sorted(names)


def _digest_text(skill_dir: Path, root: Path) -> str:
    """One skill's digest, flattened to a single line, or `""` if it has none.

    Three things are enforced here rather than left to the digest's author,
    because in a clone the author is whoever wrote the repo:

    Resolved inside `repo_root` — a `digest.md` symlinked at `~/.aws/credentials`
    otherwise read that file into the model's context every turn.

    Whitespace collapsed — one bullet per skill is the format's only structure,
    and a digest carrying newlines forged both a second header and a bullet
    attributed to a skill that does not exist.

    Truncated — see `_DIGEST_MAX_CHARS`.

    `UnicodeDecodeError` is caught beside `OSError` because it is a `ValueError`
    and does not descend from it: a binary digest.md crashed the hook.
    """
    digest = skill_dir / "digest.md"
    try:
        if not digest.resolve().is_relative_to(root):
            return ""
        text = digest.read_text()
    except (OSError, UnicodeDecodeError, ValueError, RuntimeError):
        # `RuntimeError` is the one that does not look like the others: it is what
        # `resolve()` raises on a symlink loop, and it descends from neither
        # OSError nor ValueError, so a looped digest.md crashed the hook.
        return ""
    flat = " ".join(text.split())
    return flat[:_DIGEST_MAX_CHARS].rstrip() + "…" if len(flat) > _DIGEST_MAX_CHARS else flat


def _hook_user_prompt() -> None:
    """Print what's active, for a hook re-injecting it on every turn.

    What the managed `UserPromptSubmit` entry runs (`HOOK_COMMAND`). A skill
    loaded once at session start decays as the context fills; this is the text
    that re-anchors it — sourced fresh from each installed skill's own
    `digest.md` rather than pasted in at install time, so the hook's coverage
    tracks the installed tree without the settings file recording which skills
    it currently covers.

    No arguments beyond the event name: the entry's file location already scopes
    it to one repo and one agent, and the skill list is discovered here, not
    received as input (`research.md`'s command-name decision).

    Reads the repo's installed `.agents/skills/`, not the bundle — a worktree
    with an older install re-anchors what it has, not what wfctl now ships.

    Exits 0 whatever it finds, printing nothing it cannot source. This runs on
    every user turn: a hook that fails is a per-turn error in a session that was
    otherwise fine, and the failure it would be reporting — a skill or a repo
    that isn't there — is one `wfctl doctor` already covers, once, on request.
    """
    # `OSError` alongside `SystemExit` because `get_repo_root` shells out to git
    # and raises `FileNotFoundError` when there is no git on PATH — a case the
    # sibling `worktree-guard` already handles and this one reached as a crash.
    try:
        repo_root = get_repo_root()
        manifest = _load_manifest(repo_root)
    except (SystemExit, OSError, json.JSONDecodeError):
        return

    # Resolved once, not per skill: it is the same answer every time, and the
    # loop below asks it for every installed skill on every turn.
    try:
        root = repo_root.resolve()
    except (OSError, RuntimeError):
        return

    lines = []
    for name in _installed_skill_names(manifest):
        text = _digest_text(repo_root / ".agents" / "skills" / name, root)
        if text:
            lines.append(f"- {name}: {text}")

    if lines:
        # `typer.echo`, not `console.print`: this is stdout consumed by an agent
        # harness, not a terminal. rich would wrap it at the terminal width and
        # read a `[...]` in a digest's own text as markup to strip.
        typer.echo("These skills are active and govern this response:")
        for line in lines:
            typer.echo(line)


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


@app.command("check-body")
def check_body_cmd(
    path: Path = typer.Argument(..., help="The change description to check, as a file"),
) -> None:
    """Check a PR description's drawings against `conversation-response-shape`.

    The cheaper half of the same problem the `Stop` hook covers: a PR body is a
    file on disk before `gh pr create` reads it, so checking it is a script over
    a file rather than a hook over a response. `opening-a-change` Step 4 already
    writes the body to a file and passes the file; this reads that file.

    **Why not a flag on `doctor`.** That was the first shape considered, and
    `doctor`'s own contract rules it out twice. It says what stays out of it is
    "anything whose answer depends on where the user is in their work" — a PR
    body exists only while a change is being opened, which is the definition of
    that. And it runs unprompted at every session start with no argument and one
    exit code for the whole repo; a check that needs a file named on the command
    line has nowhere to be handed one, and folding a per-file verdict into that
    exit code costs the signal `doctor` exists to carry. The same reasoning keeps
    it out of `verify`, which records that a *branch* is done rather than judging
    a file it is handed.

    Only the drawing rules, because the skill scopes the two surfaces apart
    (SKILL.md:429): headers are a violation in a reply and *required* in a PR
    body, while the template names this skill's form-selection table as the
    single owner of which drawing to use. `wfctl/_shape.py` carries the split.

    Exits 1 when it finds something, so the finding is hard to walk past. It
    gates nothing — nothing runs this but the author.
    """
    try:
        # Explicit, not the platform default: wfctl's own descriptions are
        # written UTF-8 and a locale that is not would decide this differently on
        # two machines reading the same file.
        body = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        console.print(f"[red]Can't read {path}:[/red] {exc}")
        raise typer.Exit(1)

    from wfctl import _shape
    from rich.markup import escape

    found = _shape.body_findings(body)
    if not found:
        console.print(f"[green]✓[/green] {path}: drawings look right", soft_wrap=True)
        return
    for line in found:
        console.print(f"[yellow]⚠[/yellow] {escape(line)}", soft_wrap=True)
    raise typer.Exit(1)


def _worktree_roots(cwd: str) -> tuple[str, list[str]]:
    """The worktree `cwd` is in, and every worktree root git knows about.

    ('', []) when git cannot answer — no repo, no git on PATH. The guard then
    has nothing to compare against and allows the command, which is the right
    failure direction for something that runs before every Bash call.
    """
    import subprocess

    def git(*args: str) -> str | None:
        try:
            out = subprocess.run(
                ["git", "-C", cwd, *args], capture_output=True, text=True, check=True
            )
        except (OSError, subprocess.CalledProcessError):
            return None
        return out.stdout

    here = git("rev-parse", "--show-toplevel")
    listing = git("worktree", "list", "--porcelain")
    if here is None or listing is None:
        return "", []
    roots = [
        line.split(" ", 1)[1]
        for line in listing.splitlines()
        if line.startswith("worktree ")
    ]
    return here.strip(), roots


hook_app = typer.Typer(
    no_args_is_help=True,
    help="Run an agent hook. Not for interactive use — this is what a "
    "`settings.json` hook entry invokes, so the rule stays versioned with wfctl "
    "instead of pasted into one developer's config.",
)
app.add_typer(hook_app, name="hook")


@hook_app.command(_USER_PROMPT)
def hook_user_prompt_cmd() -> None:
    """UserPromptSubmit. Re-anchor the skills installed in this repo.

    Prints each installed skill's `digest.md`. A skill loaded once at session
    start decays as the context fills; this is the text that re-anchors it,
    sourced fresh from the skills themselves rather than pasted in at install
    time, so the hook's coverage tracks the installed tree without the settings
    file recording which skills it currently covers.

    No arguments: the entry's file location already scopes it to one repo and
    one agent, and the skill list is discovered, not received as input
    (`research.md`'s command-name decision).
    """
    _hook_user_prompt()


# What the `Stop` hook sends back. The finding leads and the instruction follows,
# and that order is the whole design.
#
# An instruction on its own is the fourth reminder in a stack of three that
# already lost, which is #212. What makes this one different is that it arrives
# knowing what was broken — so it is a correction rather than a re-statement, and
# it is the half that changes every turn rather than scrolling past unread.
#
# The instruction is there because re-reading the skill in full demonstrably
# works and demonstrably decays: in the session this was built in, invoking it
# took the reply from a finding on four turns out of four to none on the two that
# followed, and the drift returned two turns after that. A pointer alone would
# have to be believed; a pointer under a finding has just been shown to be right.
_SHAPE_REPORT = """Your last reply broke conversation-response-shape:

{findings}

Re-read the skill in full before the next reply — the every-turn digest is 500
characters and this is what it does not carry. Run `/conversation-response-shape`
if you can; otherwise read `.agents/skills/conversation-response-shape/SKILL.md`,
including the seven-question pre-send check at the end."""


def _last_exchange(transcript: Path) -> tuple[str, str]:
    """`(prompt, terminal reply)` — the last user turn and what it drew.

    Reconstructed from the agent's JSONL transcript, which is the only place the
    finished reply exists: `Stop` hands over a path, not the text.

    A turn is a user message that is not a tool result, then everything up to the
    next one. The reply is reset on every message carrying a `tool_use`, so what
    survives is the text written *after* the last tool call — the terminal reply,
    which is the one the reader actually receives. Narration between two tool
    calls is not it and would otherwise dominate the word count.

    ponytail: reads the whole file. A session's transcript is a few megabytes and
    this runs once per turn; seek to the tail if that stops being true.
    """
    prompt = ""
    reply: list[str] = []
    with transcript.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            # Every field defensively, for `hook_worktree_guard_cmd`'s reason: a
            # transcript written by a newer agent than this wfctl knows about must
            # degrade to "no finding", never to a traceback at the end of a turn
            # that was otherwise fine.
            if not isinstance(record, dict):
                continue
            message = record.get("message")
            if not isinstance(message, dict):
                continue
            blocks = message.get("content")
            kinds = (
                {b.get("type") for b in blocks if isinstance(b, dict)}
                if isinstance(blocks, list)
                else set()
            )
            # A `tool_result` is not the only `user` record the reader did not
            # type. `isMeta` marks an injected skill body, a slash-command
            # expansion or an `[Image: …]` stub; `promptSource: "system"` marks a
            # subagent completion or a usage-limit notice. Roughly a quarter of
            # turn boundaries are one of those, and taking one as the prompt
            # judges the reply against text nobody wrote — in both directions,
            # since an injected `SKILL.md` asks for everything and an image stub
            # asks for nothing. Skipped rather than reset: they arrive after a
            # tool call, which has already cleared the reply, and leaving `prompt`
            # alone is what keeps the reader's own words in scope.
            if record.get("isMeta") or record.get("promptSource") == "system":
                continue
            if record.get("type") == "user" and "tool_result" not in kinds:
                prompt, reply = _message_text(message), []
            elif record.get("type") == "assistant":
                text = _message_text(message)
                if text.strip():
                    reply.append(text)
                if "tool_use" in kinds:
                    reply = []
    return prompt, "\n".join(reply).strip()


def _message_text(message: dict) -> str:
    """The human-readable text of one transcript message.

    Two shapes, because a user prompt is stored as a bare string and an
    assistant reply as a list of blocks. Blocks that are not text — tool calls,
    thinking, images — contribute nothing, which is what makes the word count a
    count of what the reader read.
    """
    blocks = message.get("content")
    if isinstance(blocks, str):
        return blocks
    if not isinstance(blocks, list):
        return ""
    return "\n".join(
        b["text"]
        for b in blocks
        if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)
    )


@hook_app.command(_RESPONSE_SHAPE)
def hook_response_shape_cmd() -> None:
    """Stop. Report what the finished reply broke in `conversation-response-shape`.

    The half of that skill nothing had: every other layer — this repo's
    `UserPromptSubmit` hook, the rule in `SKILL.md`, the pre-send check — fires
    before the reply exists, so drift was visible only to the reader noticing.
    See `wfctl/_shape.py` for what is and is not checkable, and #212 for the
    session where all three layers fired and all three lost.

    **Warns, never blocks.** Exit 0, never exit 2 — blocking a stop tells the
    agent to keep going and stop again. Over the twenty terminal replies this was
    tuned on, half carry a finding; a gate at that rate stops being read, and one
    of the ten is an options list the reader's own instructions ask for. The
    check cannot tell that one from the rest, so it says what it saw.

    **It reports to the model, not to the terminal.** `systemMessage` is the
    obvious channel and it is not wired for this event — measured, not assumed:
    across seven `Stop` runs in one session the hook produced a finding twice and
    neither reached the reader, while the runs that printed nothing were correctly
    silent. `hookSpecificOutput.additionalContext` is the channel that works, and
    it is the better one anyway: it reaches the agent that wrote the reply, in
    time to shape the next one. `systemMessage` is emitted beside it so a version
    that wires it up costs no change here.

    Silent when it finds nothing, which is most turns and the only behaviour
    that keeps the loud ones worth reading.
    """
    from wfctl import _shape

    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return
    if not isinstance(payload, dict):
        return

    # `last_assistant_message` is the finished reply, handed over so a hook does
    # not have to parse the transcript for it. Preferred when present and fallen
    # back on when it is not, because the prompt still has to come from the
    # transcript — the depth gate needs the words that were asked, and no field
    # carries those.
    reply = payload.get("last_assistant_message")
    path = payload.get("transcript_path")
    if not isinstance(path, str) or not path:
        return
    try:
        prompt, walked = _last_exchange(Path(path).expanduser())
    except OSError:
        # Same posture as `_hook_user_prompt`: this runs at the end of every turn,
        # and a transcript that has moved or cannot be read is not a thing to
        # report on work that was otherwise fine.
        return
    if not isinstance(reply, str) or not reply.strip():
        reply = walked
    if not reply:
        return

    found = _shape.findings(reply, prompt)
    if found:
        message = _SHAPE_REPORT.format(
            findings="\n".join(f"  - {line}" for line in found)
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": STOP_EVENT,
                "additionalContext": message,
            },
            "systemMessage": message,
        }))


@hook_app.command(_WORKTREE_GUARD)
def hook_worktree_guard_cmd() -> None:
    """PreToolUse/Bash. Refuse a command aimed at another worktree.

    Reads the agent's JSON payload on stdin. Refuses a command that mutates or
    executes in a git worktree other than the session's own; reads and `workmux`
    are allowed. Exits 2 to block, which is what puts the reason in front of the
    agent — exit 1 is *non-blocking* and lets the command through.

    See `wfctl/_guard.py` for the decision and its known gaps.
    """
    from wfctl import _guard

    # Every field defensively, because this runs before *every* Bash call and a
    # traceback from it reaches the agent as a hook error on work that had
    # nothing wrong with it. A payload this code cannot read describes no
    # command, and no command crosses no boundary.
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return
    # Types too, not just presence. `{"tool_input": "…"}` raises on `.get` and a
    # list `command` raises inside `re.findall` — both the traceback-on-every-
    # Bash-call this block exists to prevent, which the first version of it
    # still allowed through.
    if not isinstance(payload, dict):
        return
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str):
        return
    # The payload's `cwd` is the session's, which is the one the guard is about.
    # This process's own cwd is the agent's project directory and can differ.
    here, roots = _worktree_roots(payload.get("cwd") or ".")
    if not here:
        return

    message = _guard.refusal(command, here, roots)
    if message:
        # Straight to stderr, not through `console`: exit 2 hands stderr to the
        # model verbatim, and rich would wrap it to this process's terminal
        # width — which, running under a hook, is whatever the agent inherited.
        print(message, file=sys.stderr)
        raise typer.Exit(2)


# Where releases come from. Tags are always read from here, even for a fork
# install: a fork's tag list freezes at fork time, so comparing against it would
# report "latest" straight through an upstream release. Where the *branch* comes
# from, and where every remedy points, is the recorded origin instead — see
# _installed_build.
_WFCTL_REPO = "https://github.com/aamarin/wfctl.git"


def _parse_semver(v: str) -> tuple | None:
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return None


class _Build(NamedTuple):
    """What the running wfctl records about where it came from."""

    url: str
    """The repository installed from. Every remedy names this, pinned or not."""

    commit: str
    """The commit installed, for comparing against a branch tip."""

    pinned: bool
    """The user asked for a fixed revision, so drift against a branch is not news."""


def _installed_build() -> _Build | None:
    """Where this wfctl came from, or None if it did not come from a repository.

    Read from PEP 610 `direct_url.json`, which pip and uv both write for a
    source-control install. That the commit is already on disk is what keeps this
    check free: no build-time stamping, no packaging change, no network.

    `pinned` and `None` answer two different questions, and collapsing them loses
    the url. A pinned build still has an origin, and every remedy has to name it —
    telling someone who pinned a fork to install from upstream would swap their
    lineage, which is the one instruction this command must never give. So a pin
    suppresses only the branch comparison.

    None is for the shapes with no origin to name at all:

      no direct_url.json    installed from an index or a source archive
      no vcs_info           an editable or plain-directory install — a checkout
                            is not drift, it is someone's working copy
      unreadable            a health check must not raise on a metadata file
                            some other tool wrote

    Deliberately keyed on `vcs_info` rather than the URL scheme: `git+file://`
    is a real git install of a local clone, with a real branch worth comparing.
    """
    from importlib.metadata import PackageNotFoundError, distribution

    try:
        raw = distribution("wfctl").read_text("direct_url.json")
    except (PackageNotFoundError, OSError):
        return None
    if not raw:
        return None
    try:
        payload = json.loads(raw)
        vcs = payload["vcs_info"]
        return _Build(
            url=str(payload["url"]),
            commit=str(vcs["commit_id"]),
            pinned="requested_revision" in vcs,
        )
    except (ValueError, KeyError, TypeError):
        return None


def _remote_state(url: str) -> tuple[str, str, list[str]] | None:
    """(default_branch, tip, tags) from one ls-remote, or None if unreachable.

    `--symref HEAD` answers both halves in a single round trip and reports the
    default branch by name, so nothing here hardcodes "master" and a rename to
    "main" needs no change.

    None means the query failed, which is deliberately distinct from a repo that
    simply has no tags — the caller has to tell "couldn't look" from "looked, and
    there is nothing", or a failed check reads as a passing one.
    """
    import re
    import subprocess as sp

    # No `--refs` here, deliberately: it filters out anything not under refs/,
    # which includes HEAD — so `--refs` and `--symref HEAD` cancel out and the
    # branch half silently goes missing. The cost is that annotated tags also
    # emit a `^{}` dereference row, which the tag pattern below matches twice;
    # harmless, since the comparison only takes a maximum.
    # `--` before the url, because the url comes from direct_url.json — a file on
    # disk that this process does not own. git reads leading-dash arguments as
    # options wherever they appear, so a recorded url of
    # `--upload-pack=<command>` would run that command on every doctor, i.e. on
    # every session start, forever. The terminator makes it a pathname again.
    r = sp.run(
        ["git", "ls-remote", "--symref", "--", url, "HEAD", "refs/tags/v*"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0 or not r.stdout.strip():
        return None

    branch = re.search(r"^ref: refs/heads/(\S+)\tHEAD$", r.stdout, re.M)
    tip = re.search(r"^([0-9a-f]{40})\tHEAD$", r.stdout, re.M)
    if not branch or not tip:
        return None
    tags = re.findall(r"refs/tags/(v\d+\.\d+\.\d+)", r.stdout)
    return branch.group(1), tip.group(1), tags


def _check_wfctl_version() -> bool:
    """Report the wfctl tool's freshness. True if there is something to act on.

    Two independent verdicts. The release check asks whether a newer version has
    been published; the branch check asks whether this build is the branch it was
    installed from. They are not the same question, and for anyone following the
    README — which installs from the default branch — only the second one can
    answer "am I running the current code?".

    green ✓ = current · cyan ⬆ = action available · yellow ⚠ = couldn't check.
    """
    installed = _wfctl_version()
    cur = _parse_semver(installed)
    build = _installed_build()

    # Every remedy names the repo the user actually installed from — including a
    # pinned build, which still has an origin even though it is not branch-
    # comparable. Telling a fork user to install from upstream would replace
    # their build with a different lineage: the one instruction doctor must
    # never give.
    remedy = build.url if build else _WFCTL_REPO

    # A pin is a deliberate choice of revision, so only the *branch* half is
    # suppressed; the release half and the remedy still apply.
    comparable = build if build is not None and not build.pinned else None

    # Releases always come from upstream, whoever you installed from: a fork's
    # tag list freezes at fork time.
    upstream = _remote_state(_WFCTL_REPO)

    # A newer release outranks the branch check, so it is answered first — the
    # upgrade it prescribes re-resolves the branch too, and two remedies is one
    # more than anyone acts on. Answering it here also means a fork never pays
    # for the second query below only to have its answer discarded.
    if upstream is not None and cur is not None:
        newer = [(pv, t) for t in upstream[2] if (pv := _parse_semver(t.lstrip("v")))]
        if newer and max(newer)[0] > cur:
            console.print(f"[cyan]⬆[/cyan] wfctl {installed} → {max(newer)[1].lstrip('v')} available")
            console.print(f"    upgrade: uv tool install --upgrade {remedy}")
            return True

    # The branch comes from wherever this build did. For the ordinary install
    # that is the same repo already queried above — one round trip, as before.
    # String equality is the test: uv and pip record the url verbatim, so the
    # worst a cosmetic difference (a trailing slash, a missing .git) costs is one
    # extra query, never a wrong verdict.
    if comparable is None:
        branch_state = None
    elif comparable.url == _WFCTL_REPO:
        branch_state = upstream
    else:
        branch_state = _remote_state(comparable.url)

    drift = comparable is not None and branch_state is not None and comparable.commit != branch_state[1]
    tags_lost = upstream is None
    branch_lost = comparable is not None and branch_state is None

    if not drift and (tags_lost or branch_lost):
        # One warning line, always, naming what could not run — and what could,
        # so a check that failed is never mistaken for a check that passed.
        if tags_lost and branch_lost:
            note = "couldn't check releases or branch (offline?)"
        elif branch_lost:
            note = "latest release; couldn't check branch drift"
        elif comparable is not None:
            note = "couldn't check releases; build matches branch tip"
        else:
            note = "couldn't check releases (offline?)"
        console.print(f"[yellow]⚠[/yellow] wfctl {installed} — {note}")
        return False

    if drift:
        assert comparable is not None and branch_state is not None  # implied by `drift`
        # One condition, one pair: a green ✓ next to "couldn't check" would be a
        # contradiction, and two ternaries are two chances to introduce it.
        mark, head = (
            ("[yellow]⚠[/yellow]", "couldn't check releases")
            if tags_lost
            else ("[green]✓[/green]", "latest release")
        )
        console.print(f"{mark} wfctl {installed} — {head}")
        console.print(
            f"[cyan]⬆[/cyan] build behind {branch_state[0]} — "
            f"{comparable.commit[:7]} → {branch_state[1][:7]}"
        )
        console.print("    bundled skills are from this build too")
        console.print(f"    reinstall: uv tool install --force {remedy}")
        return True

    console.print(f"[green]✓[/green] wfctl {installed} — latest")
    return False


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


# The contract every `_check_*` below implements — the return value, not the
# arguments, which vary with what a check needs (`_check_abandoned_entries` takes
# the loaded manifest so it does not re-read one `doctor` already has).
#
#   True  — drift found, and still standing as the check returns.
#   False — no drift; or the check could not tell (offline, unreadable, nothing
#           recorded to compare against); or it found drift and repaired it.
#
# `doctor_cmd` ORs the results, so the exit code describes the repo's state when
# the run ends rather than what was seen along the way. Could-not-tell returning
# False is deliberate: a build must not fail because GitHub was briefly
# unreachable. Say so in the output — a silent False is indistinguishable from a
# pass, and the return value carries no message.
def _warn_missing_bootstrap(repo_root: Path) -> None:
    """Warn that a seeded `.workmux.yaml` won't install skills into new worktrees.

    Warns and returns; never a finding. `install-config` is seed-once, so the
    template fix reaches only repos seeded afterwards, and this is the one path
    by which an already-seeded repo hears about it. But a worktree without skills
    is recoverable by hand, and a repo may bootstrap its own way — so this must
    not hold the exit code hostage to a preference. `⚠` with the command, and the
    reader opts in.

    Runs after `_check_workmux_hook` so the teardown warning, which is data loss,
    is never the second thing on screen.
    """
    from wfctl import _workmux

    wf = repo_root / ".workmux.yaml"
    if not wf.exists():
        return
    try:
        text = wf.read_text()
    except OSError:
        return  # _check_workmux_hook already reported the unreadable file
    if _workmux.post_create_wired(text):
        return

    console.print(
        "[yellow]⚠[/yellow] .workmux.yaml: post_create does not call "
        "`wfctl install-skills` — a new\n"
        "  worktree will start with no skills, commands, or .specify/ runtime."
    )
    # soft_wrap: meant to be pasted into a YAML list, and a wrapped line pastes
    # broken.
    console.print(
        "  Add this entry to post_create yourself:\n"
        '    - cd "$WM_WORKTREE_PATH" && wfctl install-skills '
        '${WFCTL_AGENT:+--agent "$WFCTL_AGENT"} || true',
        soft_wrap=True,
    )


def _check_workmux_hook(repo_root: Path) -> bool:
    """Report a `.workmux.yaml` that won't archive on teardown; offer to fix it.

    `install-config` is seed-once and refuses to overwrite, so fixing the upstream
    template only ever reaches repos seeded afterwards. This is the one path by
    which an already-seeded repo becomes protected.

    Deliberately reports `pre_remove` only — never an unsubstituted session
    prefix. A cosmetic warning beside a data-loss warning trains the reader to
    skim past both, and this is the one whose job is to be noticed.

    True when the hook is still unwired as this returns. The one check that can
    *resolve* what it found: accepting the offer leaves the repo protected, so it
    returns False having written the fix. An unreadable file is could-not-tell —
    reported, but no finding to fail on.
    """
    from wfctl import _workmux

    wf = repo_root / ".workmux.yaml"
    if not wf.exists():
        return False  # not every repo uses workmux
    try:
        text = wf.read_text()
    except OSError as exc:
        console.print(f"[yellow]⚠[/yellow] couldn't read .workmux.yaml: {exc}")
        return False
    if _workmux.pre_remove_wired(text):
        return False

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
        return True
    if not _interactive():
        # /start-session runs doctor through a non-TTY shell. Without this line
        # the automated path reports a problem with no route to the fix.
        console.print("  Run `wfctl doctor` from a terminal to wire it.")
        return True
    if not typer.confirm("Wire it now?", default=True):
        # Declining is not recorded. Unlike choosing no tracker — a genuine
        # one-time decision — an unwired teardown hook is ongoing drift, and
        # re-reporting drift is what a doctor is for.
        return True
    try:
        wf.write_text(patched)
    except OSError as exc:
        console.print(f"[yellow]⚠[/yellow] couldn't write .workmux.yaml: {exc}")
        return True  # the hook is still unwired, whatever the cause
    console.print("[green]✓[/green] pre_remove wired — .workmux.yaml")
    return False


def _check_spec_root_migration(repo_root: Path) -> bool:
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

    Reports only: never moves or deletes. True while spec directories are
    stranded — the repo stays misconfigured until they are moved or removed, and
    unlike the teardown hook beside it this one has no self-clearing path.
    """
    in_repo = repo_root / "specs"
    if not in_repo.is_dir():
        return False
    # Keyed on what a manifest *records*, not on what `spec_root` resolves. The
    # latter honors WFCTL_SPEC_DIR, so a one-off `WFCTL_SPEC_DIR=… wfctl doctor`
    # — or the env var exported in a shell profile, which this design warns
    # against but people do — would announce "spec_root is set" in a repo that
    # records nothing, and nag about moving specs to a transient directory.
    declared = spec_root_declaration(repo_root)
    if declared is None:
        return False
    root = declared[0]
    # Resolve both sides: a recorded relative value comes back resolved, while
    # repo_root does not have to be (WFCTL_REPO_ROOT is taken verbatim). Compared
    # raw, a root pointing at this very directory reads as a mismatch and the
    # warning tells the user to move specs from a directory to itself.
    if root.resolve() == in_repo.resolve():
        return False
    stranded = sorted(p for p in in_repo.iterdir() if p.is_dir())
    if not stranded:
        return False

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
    return True


def _scanned_dirs(manifest: dict) -> tuple[str, ...]:
    """Where the abandoned-entry scan looks: wfctl's own destinations, taken from
    the target tables rather than restated, so adding a target cannot leave the
    scan behind.

    Fixed destinations, not every directory the manifest records into, and the
    agent roots — `.claude/`, `.bob/`, `.github/` — stay out with one exception.
    They are the user's own directories; a slash command someone authored there
    is not wfctl's abandoned output. Keeping them out costs nothing for a plain
    `_AGENT_TARGETS` entry, because the base source is copied whole *somewhere*:
    the rename that orphans `.claude/commands/old.md` orphans
    `.agents/commands/old.md` alongside it, and the base layer's copy is scanned.
    The real case is caught without reaching into shared ground.

    `_mirror_supersedes_wrapper` skips names inside one of those copies and does
    not weaken that: what it skips still ships to the base layer, so the scanned
    twin is exactly where the argument above already looks for it. A name it
    suppresses leaves `.claude/commands/<name>.md` behind on the install that
    adds it, and that one is caught as a recorded path this wfctl no longer
    ships — the other half of doctor, not this scan.

    `.claude/skills` is the exception because it is a *selective* mirror — only
    the skills `_MIRRORED_SKILLS` names — so its orphans have no twin under
    `.agents/`. Dropping a name from that set leaves `.agents/skills/<name>`
    installed and recorded and the `.claude/skills/<name>` copy on disk with
    nothing pointing at it (#110). Nowhere else reports it, so this is the one
    agent destination worth reaching into. The mirror root is not in
    `_AGENT_TARGETS` — no (src, dst) pair produces it, the mirror does, one item
    at a time — so it comes from the constant that mirror declares.

    Gated on the claude layer being recorded, so a `--agent bob` repo's
    `.claude/` is not read at all. That gate alone is not enough: in a repo that
    *did* install for claude, `.claude/skills/` is still shared ground, and
    `_scan_owns` is what keeps the user's own skills out of the report.

    `.agents/trackers/` stays out: `install-skills --tracker github` records
    `github.json` there, but `/scaffold-tracker` documents the same directory as
    the place to hand-author `<name>.json` for any other tracker. Scanning it
    would report a repo's own Jira config as abandoned and, under this contract,
    fail its build over a file wfctl never wrote. It is shared ground wearing an
    owned tree's prefix, and it stays out by not being a target — no special case
    to keep in sync. Splitting installed from hand-authored configs would be
    tidier and buys nothing: every other access is by exact filename, so this
    scan was the only thing that ever enumerated the directory.
    """
    return (
        *(dest for _, dest in (*_BASE_TARGETS, *_RUNTIME_TARGETS)),
        *((_CLAUDE_NATIVE_SKILL_ROOT,) if "claude" in _agent_keys(manifest) else ()),
    )


def _scan_owns(repo_root: Path, scanned: str, child: Path) -> bool:
    """Whether an unrecorded `child` of `scanned` is wfctl's to report at all.

    True everywhere except the Claude skill mirror, whose root is the one scanned
    directory the user writes to as well — Claude Code and its plugins keep
    project-local skills there, and `.claude/` is commonly gitignored whole (this
    repo does it), so `_tracked_paths` cannot tell a hand-authored skill from an
    orphan the way it can under `.agents/`.

    A mirror is a copy of a base-layer skill, so the copy is wfctl's only when the
    thing it copies is on disk. That is exactly the shape of the case this scan
    exists for — un-mirroring drops the name from `_MIRRORED_SKILLS` and leaves
    `.agents/skills/<name>` right where it was — and never the shape of a skill
    someone wrote themselves, which has no base-layer counterpart.

    On disk, not in the record: a skill dropped upstream entirely leaves both
    copies unrecorded, and both should report.
    """
    if scanned != _CLAUDE_NATIVE_SKILL_ROOT:
        return True
    return (repo_root / _BASE_SKILL_ROOT / child.name).exists()


def _tracked_paths(repo_root: Path, candidates: list[str]) -> set[str]:
    """Which of `candidates` git tracks — a directory counts when it holds a
    tracked file.

    `ls-files`, not `check-ignore`: ignore rules never untrack, so a path can be
    matched by a pattern and still be committed. Asking about coverage would
    answer a different question and clear the exception lines — `!pfms-*` beside
    `.agents/skills/*` — that are exactly the case worth keeping.

    One process for the whole set rather than one per path: this runs at every
    session start, and the scan is a handful of directory entries.

    Empty on failure, which reports every candidate. The alternative fallback
    treats everything as tracked and silences the check outright — better to warn
    about a committed file than to go quiet about an orphaned one.
    """
    import subprocess as sp

    if not candidates:
        return set()
    result = sp.run(
        ["git", "ls-files", "-z", "--", *candidates],
        cwd=repo_root, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return set()

    # A tracked path arrives as itself (a file) or as its contents (a directory),
    # so a candidate is tracked when it is listed or prefixes something listed.
    listed = [p for p in result.stdout.split("\0") if p]
    return {
        rel
        for rel in candidates
        if any(p == rel or p.startswith(f"{rel}/") for p in listed)
    }


def _check_verify_config(repo_root: Path) -> bool:
    """Report a malformed `wfctl.json`. Returns whether drift still stands.

    A broken definition of done is worse than an absent one: absent degrades to
    the old behaviour honestly, while broken means the gate silently does not
    run — the failure this whole check exists to remove, one level up. `verify`
    already refuses it, but only someone who runs `verify` finds out, and the
    people who most need to know are the ones whose CI calls `doctor`.
    """
    from wfctl import _verify

    _, errs = _verify.load_config(repo_root)
    if not errs:
        return False
    for e in errs:
        console.print(f"[yellow]⚠[/yellow] {e}")
    console.print("    fix it, or `wfctl verify` and the implement gate stay blocked")
    return True


def _check_arch_records(repo_root: Path) -> bool:
    """Report link-integrity findings across the architecture record set.

    A dangling or split supersession reads exactly like a healthy set otherwise:
    `arch context` prints the accepted records and judges nothing, so two records
    replacing the same decision are both delivered as the contract (#113).

    Only `error` holds the exit code, matching the severity `Finding` carries. A
    record marked `superseded` whose successor is still on a branch is the normal
    state mid-review, and failing CI on it would make this a check to route
    around rather than read.

    The one check here that reads a directory wfctl never wrote — `arch_root`
    defaults to `docs/architecture`, which a repo may have been keeping ADRs in
    long before it installed anything. That set can only reach `warning`: an
    `error` needs a `supersedes:` frontmatter key, which is this tool's own
    convention and not MADR's or adr-tools', while `status: superseded` alone is
    the VR-002 warning. A repo that never adopted the feature can be nagged; it
    cannot be failed.

    Validates the top-level tier only, because `load_records` globs one level.
    That is the tier boundary `design-levels` draws and `arch none` already
    relies on — `<arch-root>/design/` and `declarations/` are Level 3 and stay
    out. Design records carry their own `supersedes:` and their own status
    vocabulary, so their link integrity is unchecked by anything (#166).
    """
    from rich.markup import escape

    from wfctl import _arch

    root = arch_root(repo_root)
    findings = _arch.validate(_arch.load_records(root))
    for finding in findings:
        marker = "[red]✗[/red]" if finding.level == "error" else "[yellow]⚠[/yellow]"
        console.print(f"{marker} {escape(finding.slug)}: {escape(finding.message)}")
    if findings:
        # The one repair is editing the records, so the reader needs the path
        # rather than a command — and the root is configurable, so it cannot be
        # guessed from the slug.
        #
        # soft_wrap: an out-of-tree root prints absolute, and a path rich folded
        # at the terminal width reads as two paths and pastes broken.
        console.print(f"    records: {_arch_location(root, repo_root)}/", soft_wrap=True)
    return any(f.level == "error" for f in findings)


def _check_managed_hooks(repo_root: Path, manifest: dict) -> bool:
    """Report a managed hook that is missing, or behind what this wfctl installs.

    The merge mode's freshness check, and it needs its own because the bundle
    content hash cannot see it: the hook lives in a file wfctl does not own and
    does not hash, so a settings file edited back to the consumer's original
    leaves every other check reporting the install as current.

    Silent when the hook is current, unlike the checks below. This check has no
    healthy state worth a line: the file is the consumer's, and a report that
    names it on every clean run trains them to skim the run that doesn't.

    The events come from `MANAGED_HOOKS` and the *files* come from the manifest.
    Driving both off the record would mean a repo installed when wfctl managed
    one event never hears about the second: its record names no `Stop` entry, so
    nothing looks for one, and the bundle hash cannot see it either because the
    hook adds nothing under `wfctl/agents/`. The feature would ship to nobody who
    already had wfctl. The record still says which file and which layer, which is
    what the repair command needs.
    """
    from rich.markup import escape

    drift = False
    for layer in _layer_keys(manifest):
        paths = dict.fromkeys(
            record["path"] for record in manifest[layer].get("merged", [])
        )
        for rel in paths:
            # Read once per file, not once per event: an unparseable settings
            # file is one problem however many entries wfctl keeps in it.
            settings, problem = _read_settings(repo_root / rel)
            if settings is None:
                console.print(
                    f"[yellow]⚠[/yellow] {escape(rel)}: {escape(problem or '')} — "
                    "can't tell whether the managed hooks are current"
                )
                continue

            for event in MANAGED_HOOKS:
                drift = _report_hook_drift(settings, layer, rel, event) or drift
    return drift


def _report_hook_drift(settings: dict, layer: str, rel: str, event: str) -> bool:
    """Print what one managed entry got wrong, if anything. True when it drifted."""
    from rich.markup import escape

    actual = _settings.managed_command(settings, event)
    if actual == MANAGED_HOOKS[event]:
        return False

    state = _HOOK_GONE[event] if actual is None else "is behind this wfctl"
    # soft_wrap and the break placed by hand: rich would otherwise
    # re-wrap at the terminal edge and split the settings path across
    # two lines, which both reads badly and makes assertions on these
    # strings depend on the terminal running them.
    console.print(
        f"[cyan]⬆[/cyan] {layer}: managed {event} hook in "
        f"{escape(rel)}\n  {state}",
        soft_wrap=True,
    )
    console.print(f"    fix: wfctl install-skills --agent {layer}")
    return True


def _check_abandoned_entries(repo_root: Path, manifest: dict) -> bool:
    """Report entries wfctl installed and no longer records, and name — without
    reporting — the paths in its destinations that it cannot account for.

    A rename upstream writes the new path and leaves the old file; the manifest is
    then replaced per layer, so the old path falls out of the record entirely.
    `uninstall-skills` removes only what the manifest lists, so neither command can
    reach it afterwards — the file is wfctl's output but no longer its
    responsibility. It is not inert: a stale command file is still invocable and
    still instructs an agent to write to a handoff path nothing reads.

    Found by comparing disk against the current record rather than against
    history, because a dropped path leaves no trace to compare against.

    Scans fixed destinations rather than the parents of recorded paths. Deriving
    them from the record looks tidier and has a hole in it: the last recorded
    entry in a directory falling out takes the whole directory out of the scan
    with it, so the orphan goes unreported in exactly the case worth reporting.

    One level deep, not recursive. Every recorded path sits directly inside one of
    these destinations, so a one-level listing sees exactly the units the record
    describes; recursing would descend into recorded directories and report their
    contents — files that are installed and accounted for. That also gives the
    granularity rule for free: a skill is installed and recorded as one directory,
    so an abandoned one is one finding rather than one per file inside it.

    Reports only, and cannot do otherwise for what it finds by scanning: a path
    missing from the record looks identical whether it was renamed upstream, was
    edited locally, or fell out because a layer was deselected, so removing on
    that evidence would eventually delete someone's work. `install-skills
    --prune` removes instead of reporting because it has evidence this check
    cannot get — the record naming the path, under a layer it just rewrote.
    Paths that install flagged on the way past are reported here too, so a
    finding keeps standing after the one run that noticed it.

    Tracked paths are excluded. These destinations are shared ground: a project
    may commit its own skills and commands beside the installed ones, naming them
    as exceptions to a `.gitignore` that ignores the rest. Being in the record is
    what makes a path wfctl's, and being tracked is what makes it the repo's —
    absent from the record *and* tracked is the second, not an orphan. Reporting
    it invites the reader to delete committed work on wfctl's say-so.

    A finding needs evidence that wfctl wrote the path, and the check has three
    sources of it, not two (#183):

    - **The flag.** Since #38 an install that stops shipping a path keeps it on
      record marked `orphaned`, so the record itself says wfctl wrote it. Exact.
    - **A base-layer twin.** A mirror under `.claude/skills/` is a copy of a
      skill under `.agents/skills/`; the twin being on disk is why `_scan_owns`
      lets it through, and that is positive proof, not an absence of doubt.
    - **Nothing.** Under `.agents/`, `_scan_owns` returns `True` because no fact
      contradicts it. A hand-placed skill and an orphan left by a pre-0.16
      install are the same thing there — an untracked directory holding a
      `SKILL.md`, absent from the record — and no filter can separate them,
      because there is no fact on disk for one to read.

    So the third group is named and nothing more. The bug was never a missing
    filter beside `_scan_owns`; it was a verdict stronger than its evidence,
    which claimed wfctl had installed a file, that it was dropped upstream, and
    that the reader should delete it — three false statements about a skill they
    had written that morning, with exit 1 behind them.

    `.agents/skills/` being shared ground does not contradict the `layer-model`
    record. That record governs *this* repo's source-versus-generated split —
    editing `.agents/` here reaches nothing, because `wfctl/agents/` is the
    source. It says nothing about a consuming repo, where #87 already found a
    project keeping its own skills in that tree.

    The trade is a line that stays in a repo keeping its own skills, and silence
    about a pre-0.16 orphan under `.agents/`. Both beat what #87 priced: a check
    that fails a consumer's build over their file and tells them to delete it.
    """
    recorded_items = _recorded_items(manifest)
    recorded = {i["path"] for i in recorded_items}
    # The same finding reached from the other side. `install-skills` knows a path
    # was dropped at the moment it stops writing it, and keeps the record with a
    # flag rather than erasing it — erasing was what put the orphan beyond every
    # command's reach. Without reading the flag here, that install's one line is
    # the only time the path is ever named, and this check would go quiet on
    # exactly the case it was written for.
    #
    # A path is either on record carrying this flag or absent from the record and
    # found by the scan below, never both, so the two halves cannot report one
    # file twice. Existence is checked because a reader may already have deleted
    # it by hand, and the record outlives the file.
    # Keyed by layer, unlike `_recorded_items`, because the repair below is
    # per-layer: `install-skills` diffs only the layers the run installs, so a
    # bare `--prune` cannot reach a path under `.claude/`.
    flagged = {
        i["path"]: layer
        for layer in _layer_keys(manifest)
        for i in manifest[layer].get("items", ())
        if i.get("orphaned") and (repo_root / i["path"]).exists()
    }

    # Kept as (destination, path) pairs, because which destination a candidate
    # came from is what says whether `_scan_owns` proved anything about it.
    found = sorted(
        (scanned, rel)
        for scanned in _scanned_dirs(manifest)
        if (d := repo_root / scanned).is_dir()
        for child in d.iterdir()
        if (rel := str(child.relative_to(repo_root))) not in recorded
        if _scan_owns(repo_root, scanned, child)
    )
    tracked = _tracked_paths(repo_root, [rel for _, rel in found])
    untracked = [(scanned, rel) for scanned, rel in found if rel not in tracked]

    # `_scan_owns` is not a filter in one place and a verdict in the other; it
    # answers the same question, and only at the mirror root does it have a fact
    # to answer from. A mirror surviving it has a base-layer twin on disk, which
    # is positive proof wfctl put it there — so it is a finding, exactly as it
    # was before this split. Everywhere else the predicate returned `True`
    # because nothing contradicted it, which is not the same as knowing.
    proven = {rel for scanned, rel in untracked if scanned == _CLAUDE_NATIVE_SKILL_ROOT}
    unknown = {rel for scanned, rel in untracked if rel not in proven}
    # escape(): these lines carry rich markup, and this block's paths are by
    # definition ones wfctl did not write — the name is entirely the user's. An
    # unescaped `[draft]-skill` prints as `-skill`, and `[/x]-skill` raises
    # MarkupError out of a command that runs at every session start.
    from rich.markup import escape

    # Printed first and separately because it is not a finding, and saying so is
    # the whole of #183. Named under the same heading as the flagged half, these
    # paths borrowed a certainty the scan does not have and told a reader to
    # delete a skill they had written that morning.
    if unknown:
        one = len(unknown) == 1
        console.print(
            f"[dim]ℹ {len(unknown)} "
            f"{'path is' if one else 'paths are'} not on record under a "
            f"directory wfctl installs into:[/dim]"
        )
        for path in sorted(unknown):
            console.print(f"    [dim]{escape(path)}[/dim]", soft_wrap=True)
        # One line, short enough not to wrap at 80: it is the only place the
        # reader is told this is not a finding, and a sentence broken across two
        # lines beside a path list reads as the next path.
        console.print(
            "    [dim]Left alone — wfctl cannot tell yours from an old "
            "leftover.[/dim]"
        )

    # Only paths wfctl can show are its own return a finding. Exiting 1 on the
    # rest meant a repo keeping one skill of its own could never have a green
    # `doctor`, and the remedy offered for that was to delete the skill.
    abandoned = sorted({*flagged, *proven})
    if not abandoned:
        return False

    one = len(abandoned) == 1
    console.print(
        f"[yellow]⚠[/yellow] {len(abandoned)} installed "
        f"{'path is' if one else 'paths are'} no longer shipped — "
        f"renamed or dropped upstream:"
    )
    for path in abandoned:
        console.print(f"    {escape(path)}", soft_wrap=True)
    # One repair per layer, and the whole invocation rather than the verb: the
    # printed line is what the reader runs, and `/start-session` runs it
    # unattended. `install-skills` diffs only the layers the run installs, so a
    # bare `--prune` against a flagged `.claude/` path is a no-op that doctor
    # then reports again forever; and `--from` is one-shot, so omitting a
    # recorded source repairs the drift by reinstalling the release over the
    # branch that produced it. The stale-skills repair below already carries
    # both for these reasons — this line is the same command and had neither.
    #
    # quote() before escape(), as there: the line is copied into a shell, and a
    # source path holding a space printed as two arguments.
    import shlex

    for layer in sorted(set(flagged.values())):
        source = manifest[layer].get("source")
        frm = f" --from {escape(shlex.quote(source))}" if source else ""
        # soft_wrap for the same reason the path lines have it: this is a line
        # the reader pastes, and a wrapped one pastes as two broken commands.
        console.print(
            f"    Remove the recorded one(s) with "
            f"`wfctl install-skills{_agent_flag(layer)}{frm} --prune`.",
            soft_wrap=True,
        )
    if proven:
        console.print(
            "    Delete the rest by hand once you've checked nothing needs them."
            if flagged
            else f"    Delete {'it' if one else 'them'} by hand once you've "
            f"checked nothing needs {'it' if one else 'them'}."
        )
    return True


@app.command("doctor")
def doctor_cmd() -> None:
    """Report state wfctl put in this repo that has since drifted.

    green ✓ current · cyan ⬆ upgrade available · yellow ⚠ warning · red ✗ error
    · dim ℹ named, not a finding — it does not reach the exit code.

    A check belongs here when it names state this command can decide is wrong on
    its own, and can point the reader at the repair — the command that performs
    it, or the file to edit when there is no command, as the record-set check
    has. Originally that read "something wfctl installed or seeded"; the
    record-set check is the one that widened it, because integrity over content
    wfctl only *reads* is still a question with one right answer.

    What stays out is anything whose answer depends on where the user is in
    their work. This command runs unprompted at every session start, which makes
    it a magnet for anything you want noticed, and each arrival costs the exit
    code some of its meaning. Uncommitted spec artifacts are the worked example:
    mid-feature they are the normal state, so reporting them here turns the one
    green signal red for a condition that is not wrong.

    Two of the checks below are freshness (the tool version, the content hash);
    the rest are integrity (the teardown hook, the spec-root move, the definition
    of done, the record set, abandoned entries and managed hooks) — `npm
    outdated` and `npm doctor` under one name. `_warn_missing_bootstrap` is in
    neither, because it never becomes a finding. Named rather than counted: a
    numeral here has gone stale three times, and one that has to agree with the
    list beside it is a second place to be wrong.

    An earlier count made the sixth check the sign to split the two halves. It
    arrived unremarked and so did the seventh, which is the evidence that the
    trigger was the wrong one: the cost is report length, and a healthy repo
    still prints two lines because every integrity check is silent when it
    passes. Split them when a green run stops fitting on a screen.

    Exits 1 when a check found drift that still stands as the run ends, 0
    otherwise — including when a check could not reach an answer, which is a
    warning rather than a finding. Every applicable check runs before exiting, so
    one run reports everything wrong at once. `⚠` is the one marker that maps to
    either code: both cases warn a person, only one is a repo problem.
    """
    # Each check reports whether it found drift; the command's exit code is the
    # OR of them. The contract itself is stated above `_check_workmux_hook`.
    exit_code = int(_check_wfctl_version())

    try:
        repo_root = get_repo_root()
    except SystemExit:
        console.print("[yellow]⚠[/yellow] not in a git repo — skipping skills check.")
        raise typer.Exit(exit_code)

    # Before the manifest gate below: a repo can have a .workmux.yaml, a recorded
    # spec_root, a wfctl.json or a set of architecture records without having
    # installed skills. Each is drift a repo can carry with nothing pinned, so
    # each is reported either way.
    #
    # A list, not `a or b`: `or` short-circuits, so the first check finding drift
    # would suppress the second and a run would report one problem at a time.
    if any([
        _check_workmux_hook(repo_root),
        _check_spec_root_migration(repo_root),
        _check_verify_config(repo_root),
        _check_arch_records(repo_root),
    ]):
        exit_code = 1

    # Not in the list above, and deliberately: this one warns without ever
    # becoming a finding, so it has no bearing on the exit code to contribute.
    _warn_missing_bootstrap(repo_root)

    manifest = _load_manifest(repo_root)
    layers = _layer_keys(manifest)
    if not layers:
        console.print("Nothing installed — run `wfctl install-skills` first.")
        raise typer.Exit(exit_code)

    # After the gate on purpose: with nothing recorded, every file in the owned
    # trees is unrecorded, and the check would name all of them.
    #
    # A list, not `or`: `or` short-circuits, so the first check finding drift
    # would suppress the second and a run would report one problem at a time.
    if any([
        _check_abandoned_entries(repo_root, manifest),
        _check_managed_hooks(repo_root, manifest),
    ]):
        exit_code = 1

    # Both used only by the recorded-source branch below, which prints a path
    # into a shell-shaped line.
    import shlex

    from rich.markup import escape

    # One hash per distinct bundle root, not one per layer: every entry produced
    # by a single install carries the same value, and layers installed from the
    # same source share the walk. In practice this holds one or two entries.
    running_version = _wfctl_version()
    digests: dict[Path, str] = {}

    def digest_of(root: Path) -> str:
        if root not in digests:
            digests[root] = _bundle.content_hash(root)
        return digests[root]

    try:
        bundle_hash = digest_of(_bundle.BUNDLE_ROOT)
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

        # A layer installed from a named source is measured against that source,
        # never against the running wheel. Comparing it to the wheel is what made
        # the edit-install-test loop report drift on every run — the condition
        # #146 exists to end — and the wheel's digest says nothing about whether
        # the checkout the caller named has moved.
        recorded_source = entry.get("source")
        if recorded_source:
            # A recorded source is a path off this repo's disk, and every line
            # below prints it. Bracketed directory names are legal and parse as
            # rich style tags, so an unescaped `/x/[old]/wfctl` prints as
            # `/x//wfctl` — a different path, with nothing said about it.
            shown_source = escape(recorded_source)
            try:
                source_hash = digest_of(_bundle.resolve_root(Path(recorded_source)))
            except OSError:
                # A warning, not a finding. The install may well be current; what
                # is missing is the only thing that could tell us either way, and
                # a checkout moved or deleted is not a defect in this repo.
                # OSError rather than FileNotFoundError: a source on an unmounted
                # volume or under a directory this user cannot read is unmeasurable
                # for the same reason and has the same remedy. The narrower catch
                # let a PermissionError out as a traceback, and this runs inside
                # `/start-session` before it has reported anything at all.
                console.print(
                    f"[yellow]⚠[/yellow] {agent}: installed from {shown_source} "
                    "— source is gone, can't check",
                    soft_wrap=True,
                )
                continue

            if recorded == source_hash:
                console.print(
                    f"[green]✓[/green] {agent}: skills current (from {shown_source})",
                    soft_wrap=True,
                )
                continue

            exit_code = 1
            console.print(
                f"[cyan]⬆[/cyan] {agent}: source changed since install — {shown_source}",
                soft_wrap=True,
            )
            # `--from` carried through, for the same reason the agent flag is:
            # the printed command is what the reader runs, and a bare install
            # would repair the drift by discarding the source that produced it.
            # `/start-session` runs this repair unattended, so the line has to be
            # correct without anyone reading it.
            # quote() before escape(): this line is copied into a shell, and a
            # source under a directory with a space in its name printed as two
            # arguments — the second one rejected, so the repair that
            # `/start-session` runs unattended failed at parse.
            console.print(
                f"    update: wfctl install-skills{_agent_flag(agent)} "
                f"--from {escape(shlex.quote(recorded_source))}",
                soft_wrap=True,
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
        # Names the layer it is reporting, because the bare form does not repair
        # this finding. `install-skills` rewrites the record only for layers it
        # installed, so a run without `--agent` leaves an agent layer exactly as
        # stale as it found it — and this line is what the reader runs next. The
        # advice then reports the same drift on every later session, each time
        # re-running the same incomplete fix.
        console.print(f"    update: wfctl install-skills{_agent_flag(agent)}")

    raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()
