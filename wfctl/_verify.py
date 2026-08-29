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
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from wfctl._io import append_event, write_json_atomic

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
    write_json_atomic(record_path(agent_dir), record)


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


def run_verification(repo_root: Path, commands: list[list[str]]) -> tuple[int, list[list[str]]]:
    """Run every command in order. Return (exit code, commands that failed).

    Output is inherited, not captured: a suite that runs for minutes behind
    `capture_output=True` prints nothing until it finishes, which is
    indistinguishable from a hang. The verdict comes from the exit code either
    way, so capturing buys nothing the record needs. This is the one place the
    tracker dispatch's buffered pattern is deliberately not reused.

    Every command runs even after one fails (FR-013), so a single run reports
    every problem rather than making the user re-run to find the next one.

    A command that cannot be executed at all is a failure, not a configuration
    problem (FR-023). Reporting complete because the checker is absent is the
    defect this feature exists to remove.

    Never `shell=True`. Tokens arrive from a tracked file and are passed as argv,
    so `$(...)`, backticks and `;` are inert.
    """
    failed: list[list[str]] = []
    for argv in commands:
        console.print(f"[dim]→[/dim] {' '.join(argv)}")
        try:
            result = subprocess.run(argv, cwd=repo_root)
            ok = result.returncode == 0
        except (FileNotFoundError, NotADirectoryError):
            console.print(f"[red]✗ {argv[0]}: no such executable[/red]")
            ok = False
        except PermissionError:
            console.print(f"[red]✗ {argv[0]}: not executable[/red]")
            ok = False
        if not ok:
            failed.append(argv)
    return (1 if failed else 0), failed


def _now() -> str:
    """UTC, second precision — the same format `append_event` writes."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def perform(agent_dir: Path, repo_root: Path) -> int:
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
            console.print(f"[red]✗ {e}[/red]")
        return 1
    if not commands:
        console.print(
            "ℹ No definition of done configured — nothing to verify.\n"
            "  Add a `verify` list to wfctl.json."
        )
        return 0

    sha_before, dirty_before = code_identity(repo_root)
    exit_code, failed = run_verification(repo_root, commands)
    sha_after, dirty_after = code_identity(repo_root)
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
    append_event(
        agent_dir, "verify", exit=exit_code, sha=sha_before,
        failed=[" ".join(c) for c in failed], inconclusive=inconclusive,
    )

    short = sha_before[:7] or "no commit"
    total = len(commands)
    if inconclusive:
        console.print("[red]✗ inconclusive — the tree changed while verifying; re-run[/red]")
        return 1
    if failed:
        console.print(f"[red]✗ failed — {len(failed)} of {total} at {short}[/red]")
        for argv in failed:
            console.print(f"    {' '.join(argv)}")
        return 1

    console.print(f"[green]✓[/green] verified — {total} of {total} passed at {short}")
    if dirty_before:
        console.print(
            "[yellow]⚠[/yellow] working tree has uncommitted changes — "
            "commit to reach ● implement"
        )
    return 0
