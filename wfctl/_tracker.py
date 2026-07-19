"""Issue-tracker dispatch — run the active backend's command for a verb.

The active backend is named by the ``tracker`` key in ``.wf-skills-manifest.json``
and defined by ``.agents/trackers/<name>.json``, a map of verb -> argv template.
The supported-verb set IS the map's keys, so a backend cannot misdeclare its
capabilities. Substitution builds argv *tokens* (never a shell string), so a
``{comment}`` containing ``$(...)`` or quotes is inert.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from rich.console import Console

from wfctl._io import append_event

console = Console()

_PLACEHOLDER = re.compile(r"\{(\w+)\}")


class _MissingParam(Exception):
    def __init__(self, key: str) -> None:
        self.key = key


def _load_tracker_config(repo_root: Path, name: str) -> dict | None:
    path = repo_root / ".agents" / "trackers" / f"{name}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _substitute(token: str, params: dict) -> str:
    """Replace every {name} in one argv token from params; missing -> _MissingParam."""
    def repl(m: re.Match) -> str:
        key = m.group(1)
        val = params.get(key)
        if val is None:
            raise _MissingParam(key)
        return str(val)

    return _PLACEHOLDER.sub(repl, token)


def dispatch(agent_dir: Path, repo_root: Path, verb: str, params: dict) -> int:
    """Run the configured tracker's command for verb; return an exit code.

    Degrades gracefully (returns 0) when no tracker is configured, its config
    is missing/invalid, or the verb is unsupported — a session must not fail
    because a tracker step could not run.
    """
    from wfctl.cli import _load_manifest

    name = _load_manifest(repo_root).get("tracker")
    if not name:
        console.print(f"ℹ No tracker configured — skipping '{verb}'")
        return 0

    config = _load_tracker_config(repo_root, name)
    if config is None:
        console.print(
            f"[yellow]⚠[/yellow] Tracker '{name}' config missing or invalid "
            f"(.agents/trackers/{name}.json) — skipping '{verb}'"
        )
        return 0

    verbs = config.get("verbs", {})
    if verb not in verbs:
        console.print(f"ℹ Tracker '{name}' does not support '{verb}' — skipped")
        return 0

    try:
        argv = [_substitute(tok, params) for tok in verbs[verb]]
    except _MissingParam as e:
        console.print(f"[red]✗ '{verb}' requires --{e.key}[/red]")
        return 1

    result = subprocess.run(argv, capture_output=True, text=True, cwd=repo_root)
    if result.stdout:
        print(result.stdout, end="")  # passthrough; no rich markup/reflow
    if result.returncode != 0:
        console.print((result.stderr or "").rstrip(), style="red", markup=False)
        return result.returncode

    append_event(agent_dir, "issue", verb=verb, tracker=name)
    return 0
