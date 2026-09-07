"""The cross-worktree guard, reachable without importing `wfctl.cli`.

`hook worktree-guard` is a `PreToolUse` hook on `Bash`, so it runs before every
shell command an agent issues, and what it costs is charged to every one of them
— including the overwhelming majority that name no path and could never trespass.

Measured on `main` at 1146f44, the guard was 81.7 ms per call and `wfctl
--version` on its own was 68.5 of it: `typer` (47.5 ms) and `rich.console`
(26.7 ms) imported at `cli` module scope, neither used on this path. The guard
reads stdin, runs three regexes and writes to `sys.stderr` — `cli.py` already
explains that it bypasses `rich` deliberately, so the 26.7 ms bought a `Console`
it then refused to use.

So this module holds the decision's whole runtime and imports `json`,
`subprocess`, `sys` and `wfctl._guard` — the last of which costs only `re`.
`wfctl/_entry.py` is what reaches it without loading the CLI.

What none of this reaches is 27.1 ms of interpreter startup, which is the floor
for a hook spawned per Bash call and is not worth another pass.
"""

from __future__ import annotations

import json
import sys


def worktree_roots(cwd: str) -> tuple[str, list[str]]:
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


def worktree_guard(stdin_text: str | bytes) -> int:
    """The guard's exit code for one payload: 2 to refuse, 0 to allow.

    Returning rather than raising so a caller can test the decision without a
    process. `cli.py` turns a 2 into the `typer.Exit` the hook contract wants.

    Bytes, from both callers, because the decode has to happen under the `except`
    below. Reading stdin as text in the caller moves the decode outside it, and
    an undecodable payload then leaves as a traceback and exit 1 instead of the
    silent 0 this function promises. `str` stays accepted for the tests.

    Every field is read defensively, because this runs before *every* Bash call
    and a traceback from it reaches the agent as a hook error on work that had
    nothing wrong with it. A payload this code cannot read describes no command,
    and no command crosses no boundary. Types too, not just presence:
    `{"tool_input": "…"}` raises on `.get` and a list `command` raises inside
    `re.findall`, both of which the first version of this block still allowed.
    """
    try:
        payload = json.loads(stdin_text or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str):
        return 0

    # The two `git` subprocesses below are ~10 ms, and a command with no "/" in
    # it can reach no worktree but this one: `_guard._ABS_PATH` only ever matches
    # a string containing one, so `refusal()` was always going to return None.
    # Cheaper than the regex it guards, and it sits here rather than lower down
    # because below this line the subprocesses have already been paid for.
    if "/" not in command:
        return 0

    # The payload's `cwd` is the session's, which is the one the guard is about.
    # This process's own cwd is the agent's project directory and can differ.
    here, roots = worktree_roots(payload.get("cwd") or ".")
    if not here:
        return 0

    from wfctl import _guard

    message = _guard.refusal(command, here, roots)
    if not message:
        return 0
    # Straight to stderr, not through rich: exit 2 hands stderr to the model
    # verbatim, and rich would wrap it to this process's terminal width — which,
    # running under a hook, is whatever the agent inherited.
    print(message, file=sys.stderr)
    return 2
