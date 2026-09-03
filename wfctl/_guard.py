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
    new worktrees    nothing fires unless a path in the segment is owned by a
                     worktree that already exists, so `git worktree add` is
                     caught only when its target is absolute *and* inside a
                     worktree other than this one. `git worktree add wt/new`
                     from anywhere, and any absolute target from the checkout
                     that would own it, both pass. #137 tracks the real fix,
                     which is detecting the resulting state rather than the
                     command that caused it.

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

# workmux is the handoff mechanism the refusal message points at, and naming
# another worktree is what most of it is *for* — refusing it wholesale would
# block the escape hatch the guard recommends. Still by subcommand, not in full:
# `workmux run` is documented as "run a command in a worktree's window", which
# is the exact verb refused everywhere else in this module. Allowing it because
# of the tool it arrives under would make the allowlist self-defeating.
#
# Lifecycle verbs (`add`, `remove`, `merge`) are here on purpose. Creating and
# tearing down worktrees from anywhere is correct and is how work gets handed
# off; the guard is about work *landing* in the wrong tree, not about which
# session may manage them.
_WORKMUX_OK = frozenset({
    "add", "remove", "rm", "merge", "rename", "open", "close",
    "list", "ls", "path", "status", "send", "capture", "wait",
})

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
# the single-character alternatives so the alternation does not split them in
# half.
#
# The lone `&` needs both lookarounds. Without it as a separator, `echo hi & rm
# -rf <other>` is one segment whose verb is `echo`, and the whole command is
# allowed — a false allow in precisely the class this exists to stop. Splitting
# on every `&` instead breaks `2>&1` into a segment whose first word is `1`,
# refusing a form that appears in half the read commands anyone writes. So:
# not after `>` or `&`, and not before `>` or `&`.
#
# `$(`, a backtick and `)` are separators too, so the command inside a
# substitution is judged on its own verb. Without them `echo $(rm -rf <other>)`
# is one segment that runs as `echo` — the trespass is found, and only the verb
# check fails open. This is not the documented indirection gap, where the path
# never appears at all; here it does.
_SEPARATORS = re.compile(r"\|\||&&|(?<![>&])&(?![&>])|\$\(|[|;\n`()]")

# A redirect that writes somewhere. Refused rather than resolved: working out
# where a redirect points is shell parsing, and the segment has already been
# found naming another worktree.
#
# The lookbehind is the whole subtlety, and the first attempt at it — requiring
# whitespace or a file descriptor in front — was a false *allow*: shell needs
# neither, so `echo pwned>/other/f` slipped straight through while the segment's
# verb read as `echo`. What actually distinguishes a redirect from an arrow in a
# quoted pattern is the character before it, and only for the handful that form
# operators. `=>` and `->` are excluded; `>` after a letter is a redirect.
#
# `&` is deliberately not excluded, so `&>` (redirect both streams) is caught.
# `grep '>=' <other>` is a false refusal and the accepted cost — visible and
# recoverable, which a false allow is not.
#
# The `&` in the lookahead exempts a descriptor dup (`2>&1`, `>&2`) and nothing
# else, so it has to check what follows it: `>& <file>` is bash redirecting both
# streams to a file, which is a write. Exempting every `>&` allowed it.
#
# The possessive quantifiers are what stop `>> /dev/null` matching: a plain
# `>>?` backtracks to a single `>` when the lookahead fails, and that shorter
# match then succeeds against the second `>`. `\s*+` is the same hazard one step
# later — a greedy `\s*` gives back the space it ate so the lookahead passes on
# ` /dev/null`, which is not the exemption failing but the exemption being
# stepped around. `/dev/null` ends at whitespace or end of segment rather than a
# word boundary, which would exempt `>/dev/null.evil`.
_WRITE_REDIRECT = re.compile(r"(?<![=<>!-])>>?+\s*+(?!&[\d-]|/dev/null(?:\s|$))")

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
        #
        # Barely a guard on that, and the second attempt at saying so — the
        # first narrowed an overclaim to a smaller overclaim. It fires only when
        # the target is written absolute *and* lands inside a worktree that is
        # not this one. From the main checkout, `git worktree add /repo/wt/new`
        # is owned by the main checkout itself, so there is no trespass at all;
        # the ordinary relative spelling `git worktree add wt/new` matches no
        # root from anywhere. #137 tracks catching the state instead: a worktree
        # that never ran `post_create` is detectable after the fact, which is
        # where this belongs.
        if sub[:1] == ["worktree"]:
            return sub[1:2] == ["list"]
        return bool(sub) and sub[0] in _GIT_READ
    if verb == "find":
        return not _FIND_ACTIONS.intersection(words[1:])
    if verb == "workmux":
        sub = [w for w in words[1:] if not w.startswith("-")]
        return bool(sub) and sub[0] in _WORKMUX_OK
    return verb in _READ_VERBS


def refusal(command: str, here: str, worktrees: Iterable[str]) -> str | None:
    """Why `command` may not run from `here`, or None if it may.

    `here` is the session's own worktree root; `worktrees` is every root git
    knows about, `here` included — it is what tells a sibling worktree apart
    from an ordinary subdirectory.
    """
    roots = list(worktrees)

    # Segment by segment, each judged against the paths *it* names. Judging the
    # whole command against a trespass found anywhere in it refuses the local
    # half for the sake of the remote one: `uv run pytest && cat <other>/README`
    # was refused with "`uv` is not a read command", about a segment that never
    # left this worktree. Compound commands like that are ordinary, and the `&`
    # separator widened the class.
    for segment in _SEPARATORS.split(command):
        trespass = next(
            (
                (root, path)
                for path in _ABS_PATH.findall(segment)
                for root in [_owner(path.rstrip(".,:"), roots)]
                if root and root != here
            ),
            None,
        )
        if trespass is None:
            continue
        if _WRITE_REDIRECT.search(segment):
            why = "it redirects output"
        elif not _reads_only(segment):
            why = f"`{verb_of(segment)}` is not a read command"
        else:
            continue
        return _message(here, *trespass, why)
    return None


def _message(here: str, root: str, path: str, why: str) -> str:
    """The refusal an agent reads. Exit 2 hands this to the model, so it is the
    whole interface: it has to say what was refused, why, and what to do instead
    — a refusal without the last part produces the retrying this exists to stop."""
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
