"""Text transforms for a repo's `.workmux.yaml`.

Every function here is pure `str -> str` (or `str -> bool`). This module
**imports nothing from `wfctl.*` and never calls `subprocess`** — the caller
resolves values (project name, agent, repo root) and passes them in.

That constraint is the point, not decoration. It is what lets the substitution
logic be tested with a plain function call instead of two git repos and a
`file://` clone, which is what asserting `"agent: bob" in text` used to require.
Reach for `subprocess` here and the tests go back to needing a fixture.

No YAML parser: wfctl's runtime dependencies are `typer` and `rich`, and every
existing config edit is a line scan. `ruamel.yaml` would remove the smell but
adds a runtime dependency for a 62-line file, so line scanning stays the house
style — concentrated here, where it can be tested, rather than inline in `cli.py`.
"""
from __future__ import annotations

import re

# The one placeholder seeding owns. `<agent>` is workmux's *own* runtime token,
# resolved by workmux from its config — flagging it would be a false positive.
PROJECT_PLACEHOLDER = "<project>"

# tmux silently rewrites these two characters in session names, and then cannot
# be targeted by the original string — it reports `can't find pane: <fragment>`,
# which reads as a missing pane rather than a bad name. Measured against a live
# server: these two and no others. Spaces, `$`, `-` and `_` survive verbatim, so
# widening this set would mangle legitimate names.
_TMUX_UNSAFE = re.compile(r"[.:]")

_WINDOW_PREFIX_LINE = re.compile(r"^\s*#?\s*window_prefix:")
_EMPTY_PRE_REMOVE_LINE = re.compile(r"^pre_remove:\s*\[\]\s*$")

ARCHIVE_HOOK = (
    'command -v wfctl >/dev/null && wfctl archive-story '
    '"$WM_WORKTREE_PATH" "$WM_HANDLE" || true'
)

# Kept identical to wfctl's own reviewed config so template and reference cannot
# drift — the divergence this feature exists to close.
WIRED_PRE_REMOVE = f"pre_remove:\n  - {ARCHIVE_HOOK}\n"

_COMMENTED_AGENT = (
    "# agent: claude   # per-developer; set here or in "
    "~/.config/workmux/config.yaml\n"
)


def tmux_safe(name: str) -> str:
    """Rewrite the characters tmux would rewrite itself, so the written name
    matches the session tmux actually creates."""
    return _TMUX_UNSAFE.sub("_", name)


def patch_seed(text: str, *, agent: str | None, project: str) -> str:
    """Fill `window_prefix` and `agent` in a freshly copied template.

    `project` must already be `tmux_safe`. Sanitizing here instead would hide the
    substitution from the caller, which is the only place able to report it.

    A key that isn't in the template is left alone rather than appended: this runs
    on a file wfctl is about to hand to the repo, and inventing keys in it is a
    worse failure than not substituting one.
    """
    escaped = project.replace("'", "''")  # YAML single-quote escaping
    prefix_done = False
    agent_done = False
    out = []
    for line in text.splitlines(keepends=True):
        if not prefix_done and _WINDOW_PREFIX_LINE.match(line):
            # Written active, not commented. Unlike `agent:` — which is
            # per-developer and has no correct value to infer — a project name is
            # derivable, and every real consumer hand-edited to exactly this.
            out.append(f"window_prefix: '{escaped}__'\n")
            prefix_done = True
        elif not agent_done and line.startswith("agent:"):
            out.append(f"agent: {agent}\n" if agent else _COMMENTED_AGENT)
            agent_done = True
        else:
            out.append(line)
    return "".join(out)


def unsubstituted_placeholder(text: str) -> bool:
    """Did `<project>` survive the patch?

    Watches the symptom, not the mechanism. A key-presence check passes when the
    template renames `window_prefix` upstream — exactly when the placeholder does
    ship. tmux accepts `<` and `>` verbatim, so an unsubstituted prefix becomes a
    real session named `<project>__<branch>`, committed, for everyone on the repo.
    """
    return PROJECT_PLACEHOLDER in text


def pre_remove_wired(text: str) -> bool:
    """Does a non-comment line invoke `archive-story`?

    The comment test is what stops a repo that documents archiving — or explains
    why it deliberately skips it — from reading as wired.
    """
    return any(
        "archive-story" in line and not line.lstrip().startswith("#")
        for line in text.splitlines()
    )


def wire_pre_remove(text: str) -> str | None:
    """Wire the archive hook, or return None when that can't be done safely.

    Patches exactly one shape: `pre_remove: []` alone on a line. That is the only
    shape in the wild — it is what the template seeded, and what every
    already-seeded repo therefore holds.

    None means refuse, and the caller prints manual instructions. A `pre_remove`
    holding real entries has hooks whose ordering and intent we would be guessing
    at, and appending a top-level key to an EOF we never parsed is how a config
    file gets mangled. Refusing is cheaper than being clever.
    """
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if _EMPTY_PRE_REMOVE_LINE.match(line.rstrip("\n")):
            lines[i] = WIRED_PRE_REMOVE
            return "".join(lines)
    return None
