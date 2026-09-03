"""The cross-worktree guard: may this shell command run from this worktree?

Pure functions. The caller resolves the session's own worktree root and the set
git knows about, then passes both in — the same constraint as `_workmux`, for
the same reason. The decision table is the part worth testing, and testing it
must not cost two real worktrees.

Three verbs, three answers:

    create   `workmux add`, `git worktree list`               allowed
    read     cat, head, grep, ls, diff, `git -C <other> log`  allowed
    mutate   sed -i, tee, rm, or *running* anything there     refused

Reading another worktree is legitimate and common — comparing two branches,
checking what a PR touched, reading a sibling's AGENTS.md. A guard that blocked
reads would break ordinary review work to prevent a failure reads cannot cause.

Executing is not reading, though it looks like it. `uv run pytest` in another
worktree writes a `.venv`, builds the package and reports a result about a
branch this session is not on. It belongs with `sed -i`, not with `cat`.

That split is why the check is an **allowlist of read verbs, never a denylist of
write verbs**. The set of ways to mutate a file from a shell has no bottom; the
set of commands worth allowing across the boundary is a dozen long and is
written out below. A verb nobody thought of is therefore refused, not allowed,
and that asymmetry is the whole design.

## What this cannot catch

Stated because a guard believed complete is worse than one known partial: the
first one gets trusted. This sees the command as text. Resolving every path
argument means parsing shell, which is a losing game, so it does not try.

    relative paths   `../105-mypy-cold-venv/AGENTS.md` contains no worktree
                     root, so nothing matches. `cd` is the usual way to get
                     there and is not an allowlisted verb, but `../` alone is
                     invisible here.
    indirection      a path built in a variable, a `$(…)`, or a script that
                     cd's — the command text never contains the path.
    quoting          segments are split on `|`, `&&` and `;` without honouring
                     quotes, so a separator inside a quoted string splits a
                     segment early. It fails toward refusing.

Worktrees outside `wt/` are *not* on that list: the roots come from
`git worktree list`, so `.claude/worktrees/agent-*` — eighteen of them in this
repo today — is the same case as `wt/<handle>`, not a gap.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

# Verbs that only read, and may therefore name another worktree. Absence is the
# refusal: this list does not need to be complete, it needs to be small.
#
# `sed` is deliberately absent even though `sed -n '1,10p'` is a read. `sed -i`
# is the canonical mutation, and telling the two apart means parsing flags —
# a game this module does not play. `cat`, `head` and `tail` cover reading.
_READ_VERBS = frozenset({
    "cat", "head", "tail", "less", "more",
    "ls", "find", "tree", "stat", "file", "du", "wc",
    "grep", "rg", "diff", "cmp", "sort", "uniq", "cut",
    "realpath", "readlink", "basename", "dirname", "pwd", "echo",
})

# `find` is the one allowlisted verb that carries its own way out: these actions
# run or delete, so `find /other/wt -delete` would pass a check on the verb
# alone. Named individually rather than dropping `find` from the list, because
# `find /other -name '*.py'` is exactly the cross-worktree read worth allowing.
_FIND_ACTIONS = frozenset({"-delete", "-exec", "-execdir", "-ok", "-okdir",
                           "-fls", "-fprint", "-fprintf"})

# workmux in full, not verb by verb. It is the handoff mechanism the refusal
# message points at, and `add`, `send` and `remove` all name another worktree by
# design — refusing it would block the escape hatch the guard recommends.
_HANDOFF_TOOLS = frozenset({"workmux"})

# git is decided by subcommand: most of it reads, and `git -C <other> log|diff`
# is ordinary review work. `branch`, `tag` and `remote` are absent because each
# has a mutating form (`-D`, a bare name, `add`) that shares the subcommand with
# the listing one, and refs are shared across worktrees anyway — reading them
# needs no `-C`.
_GIT_READ = frozenset({
    "log", "show", "diff", "status", "blame", "shortlog",
    "rev-parse", "ls-files", "cat-file", "describe", "grep",
})

# git options that swallow the next word, so the subcommand scan does not mistake
# an option's value for the subcommand. `-C <path>` is the whole reason: it is
# how a legitimate cross-worktree read is spelled.
_GIT_OPTS_WITH_VALUE = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace"})

# Quote-blind on purpose — see the module docstring. `||` and `&&` come before
# the single-character class so the alternation does not split them in half. A
# lone `&` is not a separator here: it would split `2>&1` into a segment whose
# first word is `1`, refusing a form that appears in half the read commands
# anyone writes.
_SEPARATORS = re.compile(r"\|\||&&|[|;\n]")

# A redirect that writes somewhere. `2>&1` and `>/dev/null` are noise rather than
# writes and stay allowed; everything else is a write whose target this module
# will not try to resolve, so the command is refused wholesale once it has
# already been found naming another worktree.
_WRITE_REDIRECT = re.compile(r">>?\s*(?!&|/dev/null\b)")

# Absolute paths, stopping at whitespace and the shell metacharacters that
# cannot appear unescaped inside one. Deliberately greedy about `-` and `.` so
# `/…/wt/129-cross-worktree-guard/wfctl/_guard.py` arrives whole.
_ABS_PATH = re.compile(r"/[^\s'\"`;|&<>()]+")


def _owner(path: str, roots: Iterable[str]) -> str | None:
    """The worktree root `path` lives in — the longest one that prefixes it.

    Longest wins because worktree roots nest: `wt/<handle>` sits inside the main
    checkout, so a path in a worktree matches both and only the inner one is its
    owner. Taking the first match instead would report every worktree path as
    belonging to the main checkout.
    """
    matches = [r for r in roots if path == r or path.startswith(r.rstrip("/") + "/")]
    return max(matches, key=len) if matches else None


def _git_words(args: list[str]) -> list[str]:
    """`args` with git's own options (and their values) removed.

    What is left starts with the subcommand: `["-C", "/other", "log"]` → `["log"]`.
    """
    words, skip = [], False
    for arg in args:
        if skip:
            skip = False
        elif arg in _GIT_OPTS_WITH_VALUE:
            skip = True
        elif not arg.startswith("-"):
            words.append(arg)
    return words


def verb_of(segment: str) -> str:
    """The command word a segment runs, bare of any path — `/usr/bin/cat` → `cat`.

    Empty for an empty segment, which is what a trailing `&&` leaves behind.
    """
    words = segment.split()
    return words[0].rsplit("/", 1)[-1] if words else ""


def _reads_only(segment: str) -> bool:
    """Whether a single command may name another worktree."""
    words = segment.split()
    if not words:
        return True
    verb = verb_of(segment)
    if verb == "git":
        sub = _git_words(words[1:])
        # `worktree` is here for `git worktree list` alone. `git worktree add`
        # is how #129's first failure happened — a worktree created outside
        # workmux, so `post_create` never ran and it came up with no skills.
        if sub[:1] == ["worktree"]:
            return sub[1:2] == ["list"]
        return bool(sub) and sub[0] in _GIT_READ
    if verb == "find":
        return not _FIND_ACTIONS.intersection(words[1:])
    return verb in _READ_VERBS or verb in _HANDOFF_TOOLS


def refusal(command: str, here: str, worktrees: Iterable[str]) -> str | None:
    """Why `command` may not run from `here`, or None if it may.

    `here` is the session's own worktree root; `worktrees` is every root git
    knows about, `here` included — it is what tells a sibling worktree apart
    from an ordinary subdirectory.
    """
    roots = list(worktrees)
    trespass = next(
        (
            (root, path)
            for path in _ABS_PATH.findall(command)
            for root in [_owner(path.rstrip(".,:"), roots)]
            if root and root != here
        ),
        None,
    )
    if trespass is None:
        return None
    root, path = trespass

    if _WRITE_REDIRECT.search(command):
        why = "it redirects output"
    else:
        offender = next(
            (s for s in _SEPARATORS.split(command) if not _reads_only(s)), None
        )
        if offender is None:
            return None
        why = f"`{verb_of(offender)}` is not a read command"

    handle = root.rstrip("/").rsplit("/", 1)[-1]
    return (
        f"Refused: {path} is in another worktree ({root}), and {why}.\n"
        f"This session is in {here}. Reading across worktrees is fine — cat, "
        f"grep, diff, `git -C <path> log`. Mutating or running there is not: it "
        f"puts work on a branch this session's own checks never run on.\n"
        # The handle is the worktree's directory name, which is what `workmux
        # send` takes. A worktree created outside workmux has no session to send
        # to, hence the second half — the point is that retrying differently is
        # not one of the options.
        f'Hand off instead: workmux send {handle} "…" — or ask the user, if '
        f"that worktree has no session."
    )
