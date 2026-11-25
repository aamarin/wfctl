"""The spellings of the person-only commands that the agent host asks about.

The agent can run `wfctl arch accept`, `wfctl review sign-off`, and `wfctl arch
approve-imports` once the user approves each run at the host's permission
prompt (`prompt-approves-person-commands.md`). That holds only while three
lists agree: the Claude Code `ask` rules `install-skills` writes, the Codex
rules file, and the spellings the worktree guard lets through. This table is
the one list the other three follow (`design/prompted-spellings-one-table.md`).

It lives in evidence because the guard reads it, and the guard can import
evidence but not install. `cli.py` is wiring and can import either.

Nothing here imports `typer` or `rich`, since the guard runs before every Bash
call.
"""
from __future__ import annotations

import os
from typing import NamedTuple


class Prompted(NamedTuple):
    """One spelling the host asks for. `command` is the wfctl command it runs,
    such as `arch accept`, and `words` are the words it starts with."""

    command: str
    words: tuple[str, ...]

    @property
    def text(self) -> str:
        """The words as Claude Code's rule and the guard compare them, joined
        by single spaces."""
        return " ".join(self.words)


# No command has a `uv run` spelling, because each runs the installed wfctl on
# purpose. The user approves a command by its text, and `uv run wfctl` runs the
# branch's own copy, which the agent may have edited to do something else.
PROMPTED = (
    Prompted("arch accept", ("wfctl", "arch", "accept")),
    Prompted("review sign-off", ("wfctl", "review", "sign-off")),
    Prompted("arch approve-imports", ("wfctl", "arch", "approve-imports")),
)


def prompted_match(text: str) -> Prompted | None:
    """The entry whose words open the raw command text, or None.

    Only trailing whitespace is removed. The comparison is literal and
    case-sensitive, and the words must be followed by a space or the end, which
    is how Claude Code matches a `Bash(<words>:*)` rule. So `wfctl "arch" accept
    s` and `WFCTL arch accept s` match nothing, though the shell runs both as
    the accept, and a leading space matches nothing either.
    """
    text = text.rstrip()
    for entry in PROMPTED:
        prefix = entry.text
        if text == prefix or text.startswith(prefix + " "):
            return entry
    return None


# Variables Codex sets in every shell it starts, checked on 0.171.0. Codex
# runs no guard and `codex exec` shows no prompt, and a Codex reviewer started
# from Claude Code's shell inherits `CLAUDECODE`.
_CODEX_MARKERS = ("CODEX_THREAD_ID", "CODEX_SANDBOX")

# Bob Shell sets this in every shell its tools start, both the plain child
# process and the pseudo-terminal one, checked on 2.1.0. Bob Shell runs the
# guard but can't ask the user first.
_BOB_MARKER = "BOBSHELL_CLI"


def _codex_shell() -> bool:
    return any(os.environ.get(name, "").strip() for name in _CODEX_MARKERS)


def claude_code_shell() -> bool:
    """Whether Claude Code may be the host running this command, so its
    settings file is the one that protects it.

    `CLAUDECODE` set means a Claude Code shell started this command or one of
    its parents. A Codex marker turns the answer to no, since Codex reads no
    Claude Code settings. A Bob Shell marker doesn't, unlike in
    `prompted_host`, because a Claude Code started from Bob Shell carries it
    too, and the question here is which file a host might read, not whether
    anything will ask."""
    if _codex_shell():
        return False
    return bool(os.environ.get("CLAUDECODE", "").strip())


def bob_host() -> bool:
    """Whether Bob Shell may be the host running this command. Any non-blank
    value counts, for the same reason `prompted_host` reads `CLAUDECODE` that
    way. A Codex marker turns the answer to no, as in `claude_code_shell`,
    since Codex reads no Bob Shell settings."""
    if _codex_shell():
        return False
    return bool(os.environ.get(_BOB_MARKER, "").strip())


def prompted_host() -> bool:
    """Whether the command runs under a host that asks the user first.

    Claude Code sets `CLAUDECODE=1` in every shell it starts. Any non-blank
    value counts, so the check holds if that value changes. Every child process
    inherits the variable, so a Codex agent started from Claude Code's shell
    would pass with no prompt, and a Codex or Bob Shell marker turns the
    answer to no. Any other agent started the same way still passes. The
    record accepts that gap, since this check stops a mistake rather than a
    deliberate bypass.
    """
    return claude_code_shell() and not bob_host()
