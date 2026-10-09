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

A path is judged twice, as written and where the shell lands it, with quotes
removed and `..` resolved, and it is refused if either names another worktree.
`<here>/../<peer>/src` starts with this session's own root and lands in the
peer, and `<here>/..` is the directory holding every feature worktree.

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
                     segment early. That mostly refuses, but in
                     `"<dir>/a;b/../../<peer>"` the `..` climbs from a
                     directory the second half never names. No allowance is
                     granted on this split: the spec and state root exemption
                     below parses quotes properly instead.
    new worktrees    nothing fires unless a path in the segment is owned by a
                     worktree that already exists, so `git worktree add` is
                     caught only when its target is absolute *and* inside a
                     worktree other than this one. `git worktree add wt/new`
                     from anywhere, and any absolute target from the checkout
                     that would own it, both pass. #137 tracks the real fix,
                     which is detecting the resulting state rather than the
                     command that caused it.
    outside stores   a spec repository outside every worktree is judged by no
                     owner, so a commit there is never checked. With its
                     `.git` rewritten to name the main checkout's, the commit
                     lands on the main checkout's branch. The rewrite is
                     itself a write no worktree owns, so checking the commit
                     alone would add friction and close nothing.

Worktrees outside `wt/` are *not* on that list: the roots come from
`git worktree list`, so `.claude/worktrees/agent-*` — eighteen of them in this
repo today — is the same case as `wt/<handle>`, not a gap.

## The spec root and the state root are not peers

Every feature worktree writes its spec, plan, and reviews under the spec root,
because `feature-paths` tells it to. A project that keeps that store checked out
as its own worktree, beside the code, would otherwise see every one of those
writes refused. So the resolved spec root is writable from any worktree, by the
plain writes listed below, and that covers other features' spec dirs as well as
this one's.

The state root is the same case. It normally sits under `~/.local/state`, where
no worktree owns it, but `XDG_STATE_HOME` can put it inside the main checkout or
a checkout of its own, and then a session's own handoff is refused. It is exempt
for the whole project rather than one branch, because a worktree handoff writes
into the child branch's state dir before that branch exists.

A shared root that is the main checkout, or that contains any worktree, is not
honoured, since exempting it would open the peers it holds.

The exemption is an allowlist, and it is granted to a whole command or not at
all. A command earns it only when every simple command in it is one this module
can read completely, and each is either a plain write whose every path lands in
a shared root, this worktree, or no worktree, or a read `refusal()` would allow
anyway. Anything else is judged exactly as if no root were shared. Four rounds
of review patched an exemption that trusted everything but the known tricks,
and each round found new ones: a quoted `;`, a `$(…)`, `env -C`, `git
--work-tree`. So it no longer tries to see through a construct; it declines
one. That means:

    writes      mkdir, touch, cp, mv, rm, tee, and echo, cat, or printf
                with a redirect. `bash <store>/x.sh` is running the store,
                not writing it, and gets no exemption.
    commits     `git -C <root> add` or `commit`, and only in a root the
                caller has asked git about. Which branch a commit lands on
                is decided by files inside the store, which the text cannot
                show: with a plain `<main>/specs` it is the main checkout's,
                and with a `.git` replaced in the store it is whatever the
                replacement names. So the caller asks git, and passes in the
                roots whose commits land in a repository of their own or on
                a branch no other worktree has checked out. Nothing but
                reads may sit beside the commit, since a write in the same
                command could replace that `.git` after the caller asked.
    the text    no `$`, backtick, or backslash outside single quotes, and
                no glob, brace, parenthesis, `~`, or `#` outside any quotes,
                so nothing the shell would rewrite or skip is taken at its
                word. A here-document is read only with a quoted delimiter,
                whose body the shell leaves alone.
    the paths   each one judged where it lands, `..` and symlinks resolved.
                A relative path may not climb with `..`, since where it
                starts is not in the text, and no path may name a `.git`
                in any case, since one in the store redirects whatever git
                command a session later runs there.

A `cd` into a shared root that a worktree owns is refused as it always was: it
is not a write, and the session would then be standing in the store and read it
as its own worktree. A root outside every worktree has no owner to refuse for,
so a `cd` there passes. A symlink made earlier in the same command is not seen,
since the path it checks does not yet exist.
"""
from __future__ import annotations

import posixpath
import re
from collections.abc import Iterable
from dataclasses import dataclass, field

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

# The verbs the spec and state root exemption is for, and nothing else. Each
# writes only the paths it names, and none has an option that moves where a
# relative path lands, which is what put `env -C`, `make -C`, and `uv
# --directory` out of reach of any check on the text. echo, cat, and printf
# write only through a redirect, and a redirect target is a path like any other.
_WRITE_VERBS = frozenset({"mkdir", "touch", "cp", "mv", "rm", "tee", "echo", "cat", "printf"})

# The git writes a spec commit needs, and the only ones exempt. Neither moves a
# ref other than the branch the root has checked out. A commit does run the
# project's hooks, which a session can already run from its own worktree.
_GIT_WRITES = frozenset({"add", "commit"})

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
#
# The leading `/` is load-bearing outside this module: `_hook` returns 0 without
# calling `refusal()` at all when a command contains no `/`, which is only sound
# while no refusal can be reached without one. Teaching `refusal()` to judge a
# `/`-free command — the relative-path gap in the docstring above, #137 — means
# revisiting that early-out in the same change, and nothing here will fail if it
# is not. `test_a_slash_free_command_can_never_be_refused` is what holds it.
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


# The end of the shell word a path sits in. `_ABS_PATH` stops at a quote, so
# `<here>/'..'/x` arrives as `<here>/` and the `..` the shell will see is cut
# off. A path is judged on its whole word instead.
_WORD_END = re.compile(r"[\s;|&<>()]")


def _word(segment: str, start: int) -> str:
    """The shell word the path at `segment[start]` begins, as the shell reads it.

    Quotes and backslashes are removed, so `<here>/'..'/x` keeps the `..` the
    shell will act on. Whitespace ends the word only outside quotes and when not
    escaped: `"<here>/a b/../../<peer>/src"` cut at the space is `<here>/a`,
    which is this worktree's, and the rest of it names no worktree. The scan
    starts at the front of the segment because the path can begin inside a
    quote opened before it.

    Only `,` and `:` are stripped from the end: a trailing `.` is stripped
    later, for a path ending a sentence, and stripped here it would turn a
    trailing `..` into the directory it climbs out of.
    """
    word: list[str] = []
    quote, i = "", 0
    while i < len(segment):
        c = segment[i]
        if not quote and i >= start and _WORD_END.match(c):
            break
        if c == "\\" and quote != "'" and i + 1 < len(segment):
            i += 1
            c = segment[i]
        elif c in "'\"" and quote in ("", c):
            quote = "" if quote else c
            c = ""
        if i >= start:
            word.append(c)
        i += 1
    return "".join(word).rstrip(",:")


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


def _shareable(candidate: str | None, roots: list[str]) -> str | None:
    """`candidate` as the guard may exempt it, or None when it may not.

    The exemption is for a store of spec or state files, and a root declared too
    broadly would hand it to code instead. A spec root of `.` in the main
    checkout's manifest names the main checkout itself, and one of `wt` holds
    every feature worktree, so either would make `rm -rf` on a peer an allowed
    write. Neither is a store, so neither is honoured: the main checkout is the
    first root `git worktree list` prints, and any other root strictly beneath
    the candidate means it holds a worktree. A store that is itself a worktree,
    like a `specs-trunk` checkout beside the project, passes both.

    Both sides are compared resolved, as `_stays` compares a path. A root
    declared as `<main>/wt/../specs` is the store it names, and one declared as a
    symlink to the main checkout is the main checkout.

    A relative root, such as a `WFCTL_SPEC_DIR` of `specs` or `~/specs` read raw
    from the environment, would resolve against the hook process's directory
    rather than the session's, so it names no store this module can find.
    """
    if not candidate or not posixpath.isabs(candidate):
        return None
    shared = posixpath.realpath(candidate)
    real = [posixpath.realpath(r) for r in roots]
    if shared == "/" or (real and real[0] == shared):
        return None
    if any(r.startswith(shared + "/") for r in real):
        return None
    return shared


# What the shell rewrites before a word reaches the filesystem, so a word holding
# one says nothing certain about where it lands. Inside double quotes only the
# first three still act; inside single quotes nothing does. `#` is here for the
# opposite reason: the shell skips the rest of the line as a comment, so a
# here-document operator after it is one this parser would follow and the shell
# would not, and the lines it skipped as a body the shell runs as commands.
_REWRITES = frozenset("$`\\")
_UNQUOTED_REWRITES = _REWRITES | frozenset("*?[]{}()~!#")

# Longest first, so `>>` is not read as `>` followed by a word starting `>`.
# `<<<` and `<>` are not followed, and decline the exemption.
_REDIRECTS = ("&>>", "&>", ">>", ">|", ">&", ">", "<<-", "<<", "<&", "<")


@dataclass
class _Simple:
    """One simple command: its words, and the paths it reads from and writes to."""

    words: list[str] = field(default_factory=list)
    reads: list[str] = field(default_factory=list)
    writes: list[str] = field(default_factory=list)


def _commands(command: str) -> list[_Simple] | None:
    """`command` as the simple commands the shell would run, or None.

    None whenever the text holds anything the shell would rewrite or that this
    does not follow to the end: an unclosed quote, a substitution, a glob, a
    subshell, a here-document with a delimiter the shell would expand inside.
    That is the point of it. `_SEPARATORS` splits quote-blind, which is safe
    only for refusing; an exemption granted on that split cut `rm -rf
    "<store>/a;b/../../<main>/src"` in two and allowed both halves.
    """
    found: list[_Simple] = []
    current = _Simple()
    word: list[str] | None = None
    quoted = False
    target = ""
    heredocs: list[tuple[str, bool]] = []

    def finish_word() -> bool:
        nonlocal word, quoted, target
        if word is None:
            return True
        text = "".join(word)
        if target in ("<<", "<<-"):
            if not quoted:
                return False
            heredocs.append((text, target == "<<-"))
        elif target in (">&", "<&") and (text.isdigit() or text == "-"):
            pass
        elif target.startswith("<"):
            current.reads.append(text)
        elif target:
            current.writes.append(text)
        else:
            current.words.append(text)
        word, quoted, target = None, False, ""
        return True

    def finish_command() -> bool:
        nonlocal current
        if not finish_word() or target:
            return False
        if current.words or current.reads or current.writes:
            found.append(current)
        current = _Simple()
        return True

    i = 0
    while i < len(command):
        c = command[i]
        if c in "'\"":
            close = command.find(c, i + 1)
            if close < 0:
                return None
            body = command[i + 1:close]
            if c == '"' and _REWRITES.intersection(body):
                return None
            word = (word or []) + [body]
            quoted = True
            i = close + 1
        elif c in _UNQUOTED_REWRITES:
            return None
        elif c in " \t":
            if not finish_word():
                return None
            i += 1
        elif c == "\n":
            if not finish_command():
                return None
            i += 1
            # A here-document's body is data, and with a quoted delimiter the
            # shell leaves it alone, so it is skipped rather than parsed.
            for delimiter, strip_tabs in heredocs:
                while True:
                    if i >= len(command):
                        return None
                    end = command.find("\n", i)
                    end = len(command) if end < 0 else end
                    line = command[i:end]
                    i = end + 1
                    if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                        break
            heredocs.clear()
        elif command.startswith(("&&", "||"), i) or (c in ";|&" and not command.startswith("&>", i)):
            if not finish_command():
                return None
            i += 2 if command.startswith(("&&", "||"), i) else 1
        elif c in "<>&":
            op = next(r for r in _REDIRECTS if command.startswith(r, i))
            if command.startswith(("<<<", "<>"), i):
                return None
            # A run of digits right before the operator is the descriptor it
            # redirects, as in `2>`, not a word of the command.
            if word is not None and not quoted and "".join(word).isdigit():
                word = None
            if not finish_word() or target:
                return None
            target = op
            i += len(op)
        else:
            word = (word or []) + [c]
            i += 1
    if heredocs or not finish_command():
        return None
    return found


def _climbs(word: str) -> bool:
    """Whether a relative `word` holds a `..`, which lands wherever it started."""
    return not word.startswith("/") and ".." in re.split(r"[/=:]", word)


def _stays(path: str, here: str, roots: list[str], within: set[str]) -> bool:
    """Whether `path` lands in one of `within`, or else in no worktree but `here`.

    Judged three ways: as written, with `..` resolved, and with symlinks
    resolved too. Only the last can say a link in the store points at a peer,
    and only the first matches what `refusal()` would refuse with nothing shared.
    """
    for p in {path, path.rstrip(",:")}:
        landed = posixpath.realpath(p)
        if any(landed == r or landed.startswith(r + "/") for r in within):
            continue
        owners = {_owner(q, roots) for q in (p.rstrip(".,:"), posixpath.normpath(p), landed)}
        if not owners <= {None, here}:
            return False
    return True


def _commit_target(words: list[str]) -> str | None:
    """Where `git -C <path> add|commit …` commits, resolved, or None.

    Only that spelling, with `-C` as git's sole option. `-c`, `--git-dir` and
    `--work-tree` each move the repository or run something, and a second `-C`
    moves the first.
    """
    if len(words) < 4 or words[:2] != ["git", "-C"] or words[3] not in _GIT_WRITES:
        return None
    if not posixpath.isabs(words[2]):
        return None
    return posixpath.realpath(words[2])


def commit_targets(command: str) -> list[str]:
    """Every directory `command` commits in, resolved, for the caller to ask git about.

    Split the way `refusal()` splits when it picks a commit's message, not the
    way `_exempt` reads, so a commit refused for its spelling is still asked
    about. Otherwise its message would blame the folder for what the spelling
    did.
    """
    targets = (_commit_target(s.split()) for s in _SEPARATORS.split(command))
    return [t for t in targets if t]


def _exempt(
    command: str, here: str, roots: list[str], exempt: set[str], committable: set[str],
) -> bool:
    """Whether `command` only writes where a shared root lets it.

    Each simple command must be a write from the allowlist, a commit into a root
    in `committable`, or a read `_reads_only` accepts, and nothing else: a `cd`
    earlier in the command moves where every relative path after it lands, and
    `uv run` executes whatever it finds. Its paths must then stay in a shared
    root, this worktree, or no worktree, unless it is a read with no redirect,
    which may name any worktree as it always could. One that fails declines the
    exemption for the whole command, and `refusal()` then judges it as if
    nothing were shared.

    A commit is checked against `committable` exactly, not as a prefix: a
    `<root>/129` could hold a `.git` of its own that the caller never asked
    about. A feature's own folder is where `feature-paths` points, so the
    caller asks git about that folder too, and vouches for it when its top
    level is a root that takes commits.
    """
    simple = _commands(command)
    if simple is None:
        return False

    commits = [_commit_target(s.words) for s in simple]
    if any(commits):
        if not all(c in committable for c in commits if c):
            return False
        # A redirect is a write whatever the verb, and one into a link already
        # in the store can rewrite the `.git` it points at.
        if not all(
            c or (_reads_only(" ".join(s.words)) and all(w == "/dev/null" for w in s.writes))
            for s, c in zip(simple, commits)
        ):
            return False

    for s, commit in zip(simple, commits):
        named = s.words + s.reads + s.writes
        # A relative `..` lands wherever the command started, which the text
        # does not say. Judging only its own simple command is not enough: the
        # word holds no absolute path for `_stays` to refuse, so `mkdir
        # <store>/x && rm -rf ../<peer>/src` passed on the strength of the first
        # half. And a `.git` in the store, in any case on a filesystem that
        # ignores it, redirects whatever git command a session later runs there.
        if any(_climbs(w) or ".git" in re.split(r"[/=:]", w.casefold()) for w in named):
            return False
        reads = _reads_only(" ".join(s.words))
        if not reads and not commit and (not s.words or s.words[0] not in _WRITE_VERBS):
            return False

        def stays(word: str) -> bool:
            paths = [word] if word.startswith("/") else [m.group() for m in _ABS_PATH.finditer(word)]
            return all(_stays(p, here, roots, exempt) for p in paths)

        if all(stays(w) for w in named):
            continue
        if reads and all(w == "/dev/null" for w in s.writes):
            continue
        return False
    return True


def refusal(
    command: str,
    here: str,
    worktrees: Iterable[str],
    shared: Iterable[str | None] = (),
    committable: Iterable[str] = (),
) -> str | None:
    """Why `command` may not run from `here`, or None if it may.

    `here` is the session's own worktree root; `worktrees` is every root git
    knows about, `here` included — it is what tells a sibling worktree apart
    from an ordinary subdirectory.

    `shared` holds the spec root and the state root, the directories wfctl hands
    every feature worktree to write in. A command that only writes there, in the
    forms the module docstring lists, is allowed whoever owns the root, so a
    spec root that is a plain directory inside the main checkout is exempt as
    well as one that is a worktree of its own. Any other command is judged
    against `worktrees` alone, exactly as with nothing shared. A None entry is a
    root that could not be resolved, and exempts nothing.

    `committable` holds the directories in a shared root where the caller found
    that git commits to a branch of the store's own: the root itself, and any
    folder below it whose top level is that root. It is a question about the
    filesystem, which this module does not ask, and a directory missing from
    it gets no commit exemption.
    """
    roots = list(worktrees)
    exempt = {s for s in (_shareable(c, roots) for c in shared) if s}
    commits = {
        c for c in (posixpath.realpath(c) for c in committable) if _owner(c, exempt)
    }
    if exempt and _exempt(command, here, roots, exempt, commits):
        return None

    # Segment by segment, each judged against the paths *it* names. Judging the
    # whole command against a trespass found anywhere in it refuses the local
    # half for the sake of the remote one: `uv run pytest && cat <other>/README`
    # was refused with "`uv` is not a read command", about a segment that never
    # left this worktree. Compound commands like that are ordinary, and the `&`
    # separator widened the class.
    #
    # A commit into a shared root the caller has not vouched for is refused
    # whether or not a worktree owns the root. The hook calls this with `shared`
    # only once a first pass refused, so a store outside every worktree never
    # reaches here from it; the module docstring lists that as a limit. The
    # message waits until every other segment has been judged, so a peer write
    # beside it is reported as the peer write it is.
    commit_refusal = None
    for segment in _SEPARATORS.split(command):
        target = _commit_target(segment.split())
        store = next((s for s in exempt if target and _owner(target, [s])), None)
        if store and target:
            commit_refusal = commit_refusal or _commit_message(store, target, commits)
            continue
        trespass = next(
            (
                (root, path)
                for match in _ABS_PATH.finditer(segment)
                for path, word in [(match.group(), _word(segment, match.start()))]
                for root in (
                    _owner(path.rstrip(".,:"), roots),
                    _owner(posixpath.normpath(word).rstrip("."), roots),
                )
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
    return commit_refusal


def _commit_message(store: str, target: str, commits: set[str]) -> str:
    """The refusal for a commit into a shared root, which no handoff fixes.

    A store has no session to hand off to, so the generic message's remedy is
    wrong here. What the agent can act on is the spelling, when the target
    takes commits, or the folder, when the store does and the target does not.
    Otherwise it is the layout, which is the user's to change.
    """
    if target in commits:
        return (
            f"Refused: a commit into {store} is allowed only when it is written "
            f"plainly, as `git -C {store} add <path>` or `git -C {store} commit "
            f"-m '…'`, with nothing beside it but reads: no `$`, no glob, no other "
            f"git option, and no other write in the same command.\n"
            f"Run the writes first, then the commit as a command of its own."
        )
    if store in commits:
        return (
            f"Refused: {target} does not commit into {store}, since git finds a "
            f"repository of its own there, or none at all.\n"
            f"Commit from {store} itself, or from a feature folder git places in "
            f"it, as `git -C {store} add <path>`."
        )
    return (
        f"Refused: `git add` or `git commit` in {store} would not land on a "
        f"branch of its own, so it could land on this project's branch instead.\n"
        f"Specs can be committed from a feature worktree only when the spec root "
        f"is its own repository, or the top of a worktree on a branch no other "
        f"worktree has checked out, such as `specs-trunk`. Ask the user to commit "
        f"it, or to move the spec root to one of those."
    )


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
