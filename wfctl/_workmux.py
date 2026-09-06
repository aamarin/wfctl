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

# Column 0, matching how `patch_seed` finds `agent:`: a commented key is not a
# setting.
#
# Three alternatives rather than one `\S+`, because the thing a quoted YAML
# scalar exists for is a space — `"my trees"` read by `\S+` yields `my`, and
# ignoring `my/` while `my trees/` stays tracked is the failure this key is
# being read to prevent, one space over. Unquoted stops at the whitespace YAML
# requires before a trailing comment, which is what the shipped template's
# `wt          # worktrees land in ...` needs; `[^\s#]` first means a key with
# only a comment after it (`worktree_dir:   # TBD`) matches nothing rather than
# yielding `#`, which git would write into `.gitignore` as a comment line.
_WORKTREE_DIR_LINE = re.compile(
    r"""^worktree_dir:[ \t]*(?:'([^']*)'|"([^"]*)"|([^\s#]\S*))"""
)
_EMPTY_PRE_REMOVE_LINE = re.compile(r"^pre_remove:\s*\[\]\s*$")

# The command was renamed in #27; `archive-story` survives as a hidden alias.
_FORMER_COMMAND = "archive-story"
_COMMAND = "archive-specs"

# A block scalar (`- |`), and that is load-bearing rather than stylistic. YAML
# folds a multi-line *plain* scalar's break into a space, which would turn `else`
# into an argument instead of a keyword. That form passes `bash -n`, then invokes
# wfctl with four junk arguments — non-zero, and a non-zero pre_remove aborts the
# removal, so every teardown in the repo would be refused — while the missing-wfctl
# branch silently never fires.
#
# No `|| true`: a failed archive must abort the removal. `archive-specs` exits
# non-zero only when at-risk artifacts were lost, so an unrelated internal failure
# still cannot strand a worktree. The wfctl-absent branch proceeds deliberately —
# blocking there would strand every worktree on a machine that never had the tool.
ARCHIVE_HOOK = (
    "  - |\n"
    "    if command -v wfctl >/dev/null; then\n"
    f'      wfctl {_COMMAND} "$WM_WORKTREE_PATH" "$WM_HANDLE"\n'
    "    else\n"
    '      echo "⚠ wfctl not on PATH — specs in $WM_WORKTREE_PATH not archived"\n'
    "    fi\n"
)

# Kept identical to wfctl's own reviewed config so template and reference cannot
# drift — the divergence this feature exists to close.
WIRED_PRE_REMOVE = f"pre_remove:\n{ARCHIVE_HOOK}"

_COMMENTED_AGENT = (
    "# agent: claude   # per-developer; set here or in "
    "~/.config/workmux/config.yaml\n"
)


def _yaml_scalar(value: str) -> str:
    """`value` as a YAML scalar, quoted only when writing it bare would change it.

    Quoting everything would rewrite the ordinary `wt` as `'wt'` on every
    re-seed — a diff in a committed file saying nothing happened.
    """
    if value.strip() == value and not any(c in value for c in " '\"#:"):
        return value
    return "'" + value.replace("'", "''") + "'"


def tmux_safe(name: str) -> str:
    """Rewrite the characters tmux would rewrite itself, so the written name
    matches the session tmux actually creates."""
    return _TMUX_UNSAFE.sub("_", name)


def patch_seed(
    text: str, *, agent: str | None, project: str, worktree_dir: str | None = None
) -> str:
    """Fill `window_prefix`, `agent` and `worktree_dir` in a freshly copied template.

    `project` must already be `tmux_safe`. Sanitizing here instead would hide the
    substitution from the caller, which is the only place able to report it.

    A key that isn't in the template is left alone rather than appended: this runs
    on a file wfctl is about to hand to the repo, and inventing keys in it is a
    worse failure than not substituting one.

    `worktree_dir` is a value carried in, not derived — the directory the repo
    already declared, so a re-seed does not relocate every worktree in it. None
    leaves the template's own value, which is the fresh-repo case.
    """
    escaped = project.replace("'", "''")  # YAML single-quote escaping
    prefix_done = False
    agent_done = False
    worktree_dir_done = False
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
        elif (
            worktree_dir is not None
            and not worktree_dir_done
            and _WORKTREE_DIR_LINE.match(line)
        ):
            # The template's trailing comment goes with the line it annotates:
            # it reads "worktrees land in ./wt/<handle>", which a carried value
            # makes false.
            out.append(f"worktree_dir: {_yaml_scalar(worktree_dir)}\n")
            worktree_dir_done = True
        else:
            out.append(line)
    return "".join(out)


def worktree_dir(text: str) -> str | None:
    """Where this config puts worktrees, or None when it does not say.

    The one reader of that value. `install-config` used to gitignore a literal
    `wt/` beside the template that declares the key, so the two could disagree
    the moment either moved — the shape #35 is about.

    None rather than a `"wt"` fallback: a default returned here is
    indistinguishable at the call site from a value the config actually
    declared, and re-instates the hardcode one layer down.
    """
    for line in text.splitlines():
        m = _WORKTREE_DIR_LINE.match(line)
        if m:
            # One of the three alternatives matched; an empty quoted value
            # (`worktree_dir: ''`) leaves all of them falsey and is the same
            # answer as an absent key — the config names no directory.
            return next((g for g in m.groups() if g), None)
    return None


def unsubstituted_placeholder(text: str) -> bool:
    """Did `<project>` survive the patch?

    Watches the symptom, not the mechanism. A key-presence check passes when the
    template renames `window_prefix` upstream — exactly when the placeholder does
    ship. tmux accepts `<` and `>` verbatim, so an unsubstituted prefix becomes a
    real session named `<project>__<branch>`, committed, for everyone on the repo.
    """
    return PROJECT_PLACEHOLDER in text


def _block(text: str, key: str) -> list[str]:
    """`key`'s own line plus the lines belonging to it.

    A block member is indented or blank; the first line at column 0 starts the
    next key. Empty list when the key is absent.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(key):
            block = [line]
            for nxt in lines[i + 1:]:
                if nxt and not nxt[0].isspace():
                    break
                block.append(nxt)
            return block
    return []


def _live_lines(text: str, key: str) -> list[str]:
    """`key` block lines that are not commented out.

    Scoped to the block on purpose. A whole-file scan reports wired when the
    command appears anywhere else — a pane command, another hook — while the
    key itself is empty. That is a check failing *open* on the one question it
    exists to answer, so it stays narrow.

    A hook someone commented out is not a hook.
    """
    return [ln for ln in _block(text, key) if not ln.lstrip().startswith("#")]


def pre_remove_wired(text: str) -> bool:
    """Does the `pre_remove` hook archive at all — under either name?

    Both count. A repo wired before the rename is genuinely protected, because
    `archive-story` still dispatches; reporting it as unwired would offer to add
    a second hook beside the one already there. Which of the two names it uses is
    not this function's business — the archive command itself reports that, at
    the moment the hook actually runs.
    """
    return any(
        _COMMAND in ln or _FORMER_COMMAND in ln
        for ln in _live_lines(text, "pre_remove:")
    )


def post_create_wired(text: str) -> bool:
    """Does `post_create` reinstall the skills a fresh worktree lacks?

    Unlike `pre_remove_wired`, no missing-hook case here is data loss: a worktree
    without skills is recoverable by running the install by hand. That is why the
    caller warns rather than failing — see `_check_workmux_config`.

    Matches on the command, not on `--agent`, which is per-developer: a repo
    passing the flag explicitly is as wired as one reading WFCTL_AGENT.
    """
    return any("install-skills" in ln for ln in _live_lines(text, "post_create:"))


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
