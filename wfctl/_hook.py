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
`wfctl/_entry.py` is what reaches it without loading the CLI. A command already
headed for a refusal also imports `wfctl._paths`, to find the spec and state
roots, and one of those that runs git imports `wfctl._spec_store`, to ask
whether the spec root takes commits. That path is rare enough to leave out of
the measurement above.

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


def shared_roots(here: str) -> list[str | None]:
    """The spec root and the state root a session in `here` writes under.

    The same `_paths` calls `feature-paths` and `state-dir` make, so the guard
    exempts the directories an agent was told to write to. They read this
    process's environment, though, and a `WFCTL_SPEC_DIR` set only inside the
    agent's shell does not reach it, so the two can still disagree. When they
    do, the store is refused like any peer, which is the safe direction.

    None in place of a root that cannot be resolved. A malformed manifest makes
    `spec_root` raise on purpose, which is right for a command but wrong for a
    hook that runs before every Bash call, and a manifest of the wrong shape
    raises `AttributeError` or `TypeError` rather than a JSON error, hence the
    broad catch. When git cannot name the project, `project_name` falls back to
    the directory's own name, so the state root may be one nothing writes to,
    and exempting an unused directory allows no write that matters.
    """
    from pathlib import Path

    from wfctl._paths import spec_root, state_root

    found: list[str | None] = []
    for find in (spec_root, state_root):
        try:
            found.append(str(find(Path(here))))
        except Exception:
            found.append(None)
    return found


def committable(
    here: str, shared: list[str | None], targets: list[str] | None = None,
) -> list[str]:
    """The shared roots, and folders in them, where a commit lands on a branch of
    the store's own.

    Whether a root qualifies is `_spec_store.owns_branch`, the same rule the
    store applies before it commits on its own, so the guard never refuses a
    hand commit in a folder where the store commits, or the other way round. A
    spec root one level inside a store worktree passes that rule and is still
    not a store, since it reads exactly like `<main>/specs` or a folder in a
    peer: the root has to be the top of its checkout, and that is checked here
    for the folders a commit names.

    A commit is often run from a feature's own folder, `<root>/129`, since that
    is the path `feature-paths` prints. Each of `targets` below a qualifying
    root is returned as well when git names that root as its top level. One
    that is a repository of its own names itself, and is left out.

    `_spec_store` is imported here rather than at the top because most guard
    calls never reach this function, and a module imported at the top is paid
    for on every Bash call.

    This reads the hook's environment, so a `GIT_DIR` exported only in the
    agent's shell is not seen, the same limit `shared_roots` states.
    """
    import os

    from wfctl import _spec_store

    found = [
        r for r in shared if r and os.path.isdir(r) and _spec_store.owns_branch(r, here)
    ]
    qualified = {os.path.realpath(r) for r in found}
    folders: list[str] = []
    for target in dict.fromkeys(os.path.realpath(t) for t in targets or []):
        if not any(target.startswith(r + "/") for r in qualified):
            continue
        if _spec_store.top_level(target) in qualified:
            folders.append(target)
    return found + folders


def worktree_guard(stdin_text: str | bytes) -> int:
    """The guard's exit code for one payload: 2 to refuse, 0 to allow.

    Two checks run here, each in its own `try`. The review check refuses a
    pull request command while a review group has unreviewed commits
    (`_review_gate`), and refuses when it can't reach an answer. The worktree
    check refuses a command that reaches into another worktree, and allows
    when it can't decide. They share a process so every Bash call pays one
    interpreter start, not two (`622-review-check-in-worktree-guard.md`).

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

    # The review check comes first because `gh pr create` holds no "/", and the
    # fast path below would allow it. The substring test keeps a command that
    # can't match from importing `_review_gate` at all. An exception escaping
    # the check refuses rather than allows, since it was only reached by a
    # command that might open or merge a pull request.
    if "gh" in command.lower() or "merge" in command or "sign" in command:
        try:
            from wfctl import _review_gate

            refused = _review_gate.refusal(command, payload.get("cwd"))
        except Exception as e:
            from wfctl._guard import review_check_failed

            refused = review_check_failed(str(e) or type(e).__name__)
        if refused:
            print(refused, file=sys.stderr)
            return 2

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
    # The spec and state roots are resolved only once a command is already
    # headed for a refusal. Each can cost another git subprocess, for the main
    # checkout's manifest and for the project name, and nearly every command
    # that names a path names one in this worktree and was never going to need
    # either.
    # Whether a root takes commits costs up to five more, and one per feature
    # folder a commit names, so it is asked only of a command that runs git at
    # all.
    # Only the spec root is asked: nothing commits handoffs, and a state root
    # under a dotfiles repository would otherwise take commits nobody meant it
    # to.
    if message:
        shared = shared_roots(here)
        commits = (
            committable(here, shared[:1], _guard.commit_targets(command))
            if "git" in command else []
        )
        message = _guard.refusal(command, here, roots, shared=shared, committable=commits)
    if not message:
        return 0
    # Straight to stderr, not through rich: exit 2 hands stderr to the model
    # verbatim, and rich would wrap it to this process's terminal width — which,
    # running under a hook, is whatever the agent inherited.
    print(message, file=sys.stderr)
    return 2
