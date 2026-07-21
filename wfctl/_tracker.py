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

# highlight=False: don't let rich wrap quoted tokens (issue ids, verb names) in
# ANSI — this output is parsed by agents, so keep it plain.
console = Console(highlight=False)

_PLACEHOLDER = re.compile(r"\{(\w+)\}")

# The verb contract: verb -> the placeholders its argv may use. The key set here
# IS the set of valid verbs; a config using anything else is rejected. Kept in
# sync with the scaffold-tracker skill's table.
ALLOWED = {
    "list": set(), "view": {"id"}, "close": {"id", "comment"},
    "comment": {"id", "body"}, "create": {"title", "body"},
    "label": {"id", "action", "label"},
}


def validate_config(config: dict) -> list[str]:
    """Return a list of problems with a tracker config; empty list means valid.

    A malformed config doesn't crash ``wfctl issue`` — the loader treats it as
    "no config" and every verb silently no-ops. This surfaces the problems
    instead. Checks the same things the /scaffold-tracker skill documents:
    a non-empty ``verbs`` map, known verb names, argv as non-empty string lists,
    only the placeholders each verb allows, and a compilable ``key_pattern``.
    """
    errs: list[str] = []
    kp = config.get("key_pattern")
    if kp is not None:
        if not isinstance(kp, str):
            errs.append("key_pattern must be a string")
        else:
            try:
                re.compile(kp)
            except re.error as e:
                errs.append(f"key_pattern is not a valid regex: {e}")

    verbs = config.get("verbs")
    if not isinstance(verbs, dict) or not verbs:
        errs.append("missing non-empty 'verbs' object")
        return errs

    for verb, argv in verbs.items():
        if verb not in ALLOWED:
            errs.append(f"unknown verb '{verb}' (allowed: {sorted(ALLOWED)})")
            continue
        if not isinstance(argv, list) or not argv or not all(isinstance(t, str) for t in argv):
            errs.append(f"'{verb}': must be a non-empty list of strings")
            continue
        used = {m for tok in argv for m in _PLACEHOLDER.findall(tok)}
        bad = used - ALLOWED[verb]
        if bad:
            errs.append(
                f"'{verb}': placeholder(s) {sorted(bad)} not allowed "
                f"(allowed: {sorted(ALLOWED[verb]) or 'none'})"
            )
    return errs


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


def load_key_pattern(repo_root: Path) -> str:
    """Return the active tracker's issue-key regex, or the default.

    Degrades to DEFAULT_KEY_PATTERN when no tracker is configured, its config is
    missing/invalid, the field is absent, or the value won't compile — key
    resolution must never fail because a tracker step couldn't run.
    """
    from wfctl._paths import DEFAULT_KEY_PATTERN
    from wfctl.cli import _load_manifest

    name = _load_manifest(repo_root).get("tracker")
    if not name:
        return DEFAULT_KEY_PATTERN
    config = _load_tracker_config(repo_root, name)
    pattern = (config or {}).get("key_pattern")
    if not pattern:
        return DEFAULT_KEY_PATTERN
    try:
        re.compile(pattern)
    except re.error:
        return DEFAULT_KEY_PATTERN
    return pattern


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
        console.print(
            f"ℹ No tracker configured — skipping '{verb}'. "
            "Author one with the /scaffold-tracker skill."
        )
        return 0

    config = _load_tracker_config(repo_root, name)
    if config is None:
        console.print(
            f"[yellow]⚠[/yellow] Tracker '{name}' config missing or invalid "
            f"(.agents/trackers/{name}.json) — skipping '{verb}'. "
            "Fix it with the /scaffold-tracker skill (or `wfctl tracker-check "
            f"{name}` to see what's wrong)."
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
