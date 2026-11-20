"""The definition of done: read it, run it, record what happened.

Separate from `_pipeline` because this module spawns subprocesses and writes
state, while `_pipeline` is pure inference over files. Folded together, step
inference could not be exercised without a subprocess — and `_infer_steps` is the
most heavily tested function in the package.

The record this module writes is what `_pipeline` reads to decide whether
`implement` is done. Nothing here accepts a verdict from its caller: the whole
point of #69 is that the agent doing the work does not get to certify it.
"""
from __future__ import annotations

import json
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from rich.console import Console
from rich.markup import escape

from wfctl._io import append_event, write_atomic

# highlight=False: this output is read beside a test runner's own, and rich
# colourising argv tokens makes the two hard to tell apart.
console = Console(highlight=False)

CONFIG_PATH = "wfctl.json"
RECORD_NAME = "verify.json"

# Every key a record must carry to be usable. A record missing any of them is
# treated as absent rather than partially trusted — see `load_record`.
_RECORD_FIELDS = ("command", "exit", "failed", "sha", "dirty", "inconclusive", "at")


def load_config(repo_root: Path) -> tuple[list[list[str]], list[str]]:
    """Return (definition of done, problems). Both empty means none configured.

    Problems are returned rather than raised so `doctor` can report them without
    catching, and so a caller that only wants to know "is anything configured"
    does not have to guard. A non-empty problem list always comes with an empty
    command list: a config that is half-valid is not a definition of done.

    A string entry is rejected, never split on whitespace. Splitting is exactly
    how `"pytest && rm -rf /"` becomes two commands, and the repository can ask
    for a shell explicitly — `["sh", "-c", "..."]` — where a reviewer sees it.
    """
    path = repo_root / CONFIG_PATH
    if not path.exists():
        return [], []
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return [], [f"{CONFIG_PATH}: not valid JSON ({e})"]

    if not isinstance(data, dict):
        return [], [f"{CONFIG_PATH}: top level must be an object"]

    verify = data.get("verify")
    if verify is None:
        return [], []
    if not isinstance(verify, list):
        return [], [f"{CONFIG_PATH}: 'verify' must be a list of commands"]

    commands: list[list[str]] = []
    errs: list[str] = []
    for i, entry in enumerate(verify, 1):
        if isinstance(entry, str):
            errs.append(
                f"{CONFIG_PATH}: 'verify' entry {i} must be a non-empty list of "
                "strings, got a string — write it as argv, e.g. [\"pytest\", \"-q\"]"
            )
        elif (
            not isinstance(entry, list)
            or not entry
            or not all(isinstance(t, str) for t in entry)
        ):
            errs.append(
                f"{CONFIG_PATH}: 'verify' entry {i} must be a non-empty list of strings"
            )
        else:
            commands.append(entry)

    return ([], errs) if errs else (commands, [])


def record_path(agent_dir: Path) -> Path:
    return agent_dir / RECORD_NAME


def load_record(agent_dir: Path) -> dict | None:
    """The last completed run's record, or None.

    None for absent, unreadable, unparseable, or missing any field. There is no
    migration path and none is needed — re-running regenerates it — so a record
    this function cannot fully interpret is treated as no record at all. The
    alternative is trusting a verdict whose provenance we cannot read.
    """
    path = record_path(agent_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict) or any(f not in data for f in _RECORD_FIELDS):
        return None
    return data


def write_record(agent_dir: Path, record: dict) -> None:
    """Write atomically: `status` runs constantly while a run takes minutes."""
    write_atomic(record_path(agent_dir), json.dumps(record, indent=2))


def code_identity(repo_root: Path) -> tuple[str, bool]:
    """Return (commit sha, whether the tree has uncommitted changes).

    The sha alone identifies the last commit, not the code on disk — an agent
    that edits without committing leaves HEAD untouched. `--porcelain` counts
    untracked files too, deliberately: a new source file is untracked until it is
    added, and excluding it would let unverified code reach a passing verdict.

    A repository with no commits yields an empty sha, which never matches a later
    read. That is honest: there is nothing to verify against yet.
    """
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True
    )
    sha = head.stdout.strip() if head.returncode == 0 else ""
    porcelain = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True
    )
    return sha, bool(porcelain.stdout.strip())


class CommandResult(NamedTuple):
    """What one verify command did: how it ended and how long it took."""

    argv: list[str]
    exit: int
    seconds: float


def run_verification(repo_root: Path, commands: list[list[str]]) -> list[CommandResult]:
    """Run every command in order and return one result for each.

    Output is inherited, not captured: a suite that runs for minutes behind
    `capture_output=True` prints nothing until it finishes, which is
    indistinguishable from a hang. The verdict comes from the exit code either
    way, so capturing buys nothing the record needs. This is the one place the
    tracker dispatch's buffered pattern is deliberately not reused.

    Every command runs even after one fails (FR-013), so a single run reports
    every problem rather than making the user re-run to find the next one.

    A command that cannot be executed at all is a failure, not a configuration
    problem (FR-023). Reporting complete because the checker is absent is the
    defect this feature exists to remove. It records the shell's own codes, 127
    for a missing executable and 126 for one that can't run.

    Never `shell=True`. Tokens arrive from a tracked file and are passed as argv,
    so `$(...)`, backticks and `;` are inert.
    """
    results: list[CommandResult] = []
    for argv in commands:
        console.print(f"[dim]→[/dim] {escape(shlex.join(argv))}")
        started = time.monotonic()
        try:
            code = subprocess.run(argv, cwd=repo_root).returncode
        except (FileNotFoundError, NotADirectoryError):
            console.print(f"[red]✗ {escape(argv[0])}: no such executable[/red]")
            code = 127
        except OSError as exc:
            # PermissionError, a bare OSError such as ENOEXEC for a file with the
            # execute bit and no format the system can run, and resource errors
            # such as EMFILE. Each names its own cause.
            console.print(f"[red]✗ {escape(argv[0])}: {escape(exc.strerror or str(exc))}[/red]")
            code = 126
        results.append(CommandResult(argv, code, time.monotonic() - started))
    return results


def _now() -> str:
    """UTC, second precision — the same format `append_event` writes."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def perform(agent_dir: Path, repo_root: Path, branch: str) -> int:
    """Run the definition of done, record the outcome, return an exit code.

    Identity is captured before *and* after the run. A suite takes minutes and an
    agent edits while it runs; one capture cannot tell a clean run from a run
    whose tree moved underneath it, and a verdict against a moving tree describes
    neither state (FR-016).

    Identity is `(sha, dirty)` and `dirty` is a boolean, so a change made while
    the tree is *already* dirty leaves the pair unchanged and reads as
    conclusive. That is sound rather than a hole: a record taken on a dirty tree
    never reports complete, so the undetectable case is also the harmless one.
    The case that matters — a clean tree that stops being clean — flips the flag.

    Nothing is written until every command has finished (FR-017), so a record's
    existence is itself proof the run completed. An interrupt leaves the previous
    record untouched — `run_verification` raises straight through this function
    and the write below is never reached.
    """
    commands, errs = load_config(repo_root)
    if errs:
        for e in errs:
            console.print(f"[red]✗ {escape(e)}[/red]")
        return 1
    if not commands:
        console.print(
            "ℹ No definition of done configured — nothing to verify.\n"
            "  Add a `verify` list to wfctl.json."
        )
        return 0

    run_started = time.monotonic()
    sha_before, dirty_before = code_identity(repo_root)
    results = run_verification(repo_root, commands)
    sha_after, dirty_after = code_identity(repo_root)
    total_seconds = time.monotonic() - run_started
    failed = [r.argv for r in results if r.exit != 0]
    exit_code = 1 if failed else 0
    inconclusive = (sha_before, dirty_before) != (sha_after, dirty_after)

    record = {
        "command": commands,
        "exit": exit_code,
        "failed": failed,
        "sha": sha_before,
        "dirty": dirty_before,
        "inconclusive": inconclusive,
        "at": _now(),
    }
    write_record(agent_dir, record)
    # `branch` is what splits a shared `WFCTL_STATE_DIR` log back into branches
    # for `wfctl timings`, as it does for every other event that carries one.
    append_event(
        agent_dir, "verify", branch=branch, exit=exit_code, sha=sha_before,
        failed=[shlex.join(c) for c in failed], inconclusive=inconclusive,
        seconds=round(total_seconds, 1),
        # `wfctl timings` groups runs by this text, so it's `shlex.join`: with a
        # plain join, `["a b"]` and `["a", "b"]` would count as one command.
        commands=[
            {
                "command": shlex.join(r.argv),
                "exit": r.exit,
                "seconds": round(r.seconds, 1),
            }
            for r in results
        ],
    )

    short = sha_before[:7] or "no commit"
    total = len(commands)
    if inconclusive:
        console.print("[red]✗ inconclusive — the tree changed while verifying; re-run[/red]")
        return 1
    if failed:
        console.print(f"[red]✗ failed — {len(failed)} of {total} at {short}[/red]")
        for argv in failed:
            console.print(f"    {escape(shlex.join(argv))}")
        return 1

    console.print(f"[green]✓[/green] verified — {total} of {total} passed at {short}")
    if dirty_before:
        console.print(
            "[yellow]⚠[/yellow] working tree has uncommitted changes — "
            "commit to reach ● implement"
        )
    return 0
