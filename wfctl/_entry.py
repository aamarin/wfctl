"""The console script, and the one path that must not load the CLI to run.

`wfctl` resolves here rather than to `cli:app` so that `hook worktree-guard` —
which fires before every Bash call an agent makes — can reach its decision
without importing `typer` and `rich`. Everything else falls through unchanged.

A dispatcher rather than a second console script (`wfctl-hook`, say), because
the installed command string is an interface: it is written into every
consumer's `.claude/settings.json`, it is quoted in `docs/reference.md`, and
#136 is about to install it for everyone. A second name would have to be threaded
through all three and would strand the settings files already pointing at this
one. Nothing outside this file learns that the fast path exists.
"""

from __future__ import annotations

import sys

# Exactly this argv, and nothing longer. `hook worktree-guard --help` has to
# reach typer to print anything, and a future flag on the subcommand would
# otherwise be silently ignored rather than rejected.
_GUARD_ARGV = ["hook", "worktree-guard"]
# The same exact-argv rule. This one fires on every reply end rather than every
# Bash call, and decides nothing on nearly all of them.
_RESTART_ARGV = ["hook", "session-restart"]


def main() -> None:
    if sys.argv[1:] == _GUARD_ARGV:
        from wfctl._hook import worktree_guard

        # `.buffer`, so an undecodable payload reaches the guard as bytes and is
        # swallowed by its own `except` rather than tracebacking out here.
        raise SystemExit(worktree_guard(sys.stdin.buffer.read()))

    if sys.argv[1:] == _RESTART_ARGV:
        from wfctl._restart import hook_main

        raise SystemExit(hook_main())

    from wfctl.cli import app

    app()
