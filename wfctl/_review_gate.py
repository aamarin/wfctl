"""The guard's review check: a pull request doesn't open or merge while a review
group has commits it hasn't reviewed.

`wfctl hook worktree-guard` runs this before its worktree check, in the same
process, rather than as a second hook entry that would charge every Bash call a
second interpreter start (`622-review-check-in-worktree-guard.md`). The guard
imports this module only when the command holds `gh` in any case, `merge`, or
`sign`, so a command holding none of them pays a substring test and nothing
else.

The check reads the command in two passes. The first reads only the text and
refuses what the text alone settles: the sign-off command, a `gh` command word
it can't read, a chained or substituted pull request command, an environment
prefix, and the `gh api` and GraphQL forms that hide which branch they act on
(research.md R4 and R6). The second runs only for a command the first pass
judged, and asks git and `gh` which branch and commit the command acts on, then
whether every review group has reviewed that commit.

Once a command has matched, any error refuses it. Every bug in a check that
allowed on error would let an unreviewed pull request through, and a wrong
refusal costs one command run in a person's own terminal, where the hook
doesn't run.

Nothing here imports `typer` or `rich`, since the guard runs before every Bash
call (`_hook.py`).
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

# Each `gh` and `git` call gets this bound, well under the host's own hook
# timeout. A hook the host kills exits without code 2, and the command runs.
TIMEOUT = 5.0

SIGN_OFF_REFUSAL = (
    "✗ wfctl review sign-off is for a person to run in their own terminal, not an agent."
)

# `gh help` in gh 2.91, less `copilot` and `agent-task`, since each hands the
# request to another agent that can open or merge a pull request. Listed rather
# than refused one by one, because every installed extension and every
# one-word alias adds a command word the check has never seen, and `gh stack
# merge` merges a whole stack.
GH_COMMANDS = frozenset({
    "alias", "api", "attestation", "auth", "browse", "cache", "codespace",
    "completion", "config", "extension", "gist", "gpg-key", "help", "issue",
    "label", "licenses", "org", "pr", "preview", "project", "release", "repo",
    "ruleset", "run", "search", "secret", "skill", "ssh-key", "status",
    "variable", "version", "workflow",
})

# The program word matches in any case, since macOS runs `GH pr merge` as `gh`.
# Everything after it is case-sensitive, because `-R` and `-r` are different
# flags.
_GH = r"\b(?i:gh)"
_REPO = r"(?:(?:-R|--repo)(?:\s+|=)\S+|-R\S+)"
_PR_COMMAND = re.compile(
    rf"{_GH}\s+(?P<pre>{_REPO}\s+)?pr\s+(?P<mid>{_REPO}\s+)?(?P<verb>create|new|merge)\b"
)
_API_MERGE = re.compile(r"pulls/(?P<number>\d+)/merge(?:-async)?\b")
_REPOS_PATH = re.compile(r"(?:^|[^\w])repos/(?P<owner>[^/\s\"']+)/(?P<repo>[^/\s\"']+)/\Z")
_GH_WORD = re.compile(rf"{_GH}\s+")
_GH_API = re.compile(rf"{_GH}\s+api\b")
_CREATE_MUTATION = re.compile(r"createPullRequest")
_MERGE_MUTATION = re.compile(r"mergePullRequest|enablePullRequestAutoMerge|enqueuePullRequest")
# Loose on purpose: a wrong refusal of text that mentions both words costs one
# rewording, and the terminal check in `review sign-off` backs it up.
_SIGN_OFF = re.compile(r"\breview\b.*\bsign.?off\b", re.S)

_SEPARATOR = re.compile(r"[;&|\n]")
_SUBSTITUTION = re.compile(r"\$\(|`|<\(|>\(")
# `env` matches after a `/` or a backslash too, since `/usr/bin/env -C` and
# `\\env -C` move `gh` to another directory just as `env -C` does.
_ENV_PREFIX = re.compile(
    r"(?:^|[\s\"'`(])[A-Za-z_][A-Za-z0-9_]*=|(?:^|[\s\"'`(/\\])env(?=[\s\"']|$)"
)
_PLAIN_REPO = re.compile(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)?")
_UNPLAIN_VERB = re.compile(r"[$\\*?\[{'\"`]")
_PULLS_CREATE = re.compile(r"(?:^|/)pulls/?(?:\?.*)?\Z")
_PR_URL = re.compile(r"https?://(?P<host>[^/]+)/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/\d+")
# The shell expands `{a,b}` and `{1..3}` into several words, and a glob into
# the files it matches, after the check has read the command as one word.
_BRACE = re.compile(r"\{[^{}]*(?:,|\.\.)[^{}]*\}")
# The redirections the check reads, and nothing else: a `<` or `>` in any
# other word refuses. A list of allowed spellings rather than a pattern for
# every one the shell accepts, since `631&>/dev/null` and `-tx> --help` each
# read as a redirection to a looser pattern while the shell passed `631` and
# `-tx` to `gh`.
# A heredoc and a here-string are on the list because `gh api --input -
# <<'EOF'` is how a body is written by hand. The shell consumes the delimiter
# or the string, so `gh` never receives it as an argument.
_FD_COPY = re.compile(r"[12]?>&[12]")
_REDIRECT_ALONE = re.compile(r"[12]?>>?|<(?:<-?|<<)?|&>>?")
_REDIRECT_TO = re.compile(r"(?:[12]?>>?|<(?:<-?|<<)?|&>>?)[^<>&|]+")

_MERGE_VALUE = frozenset({
    "-t", "--subject", "-b", "--body", "-F", "--body-file", "-A", "--author-email",
    "--match-head-commit", "-R", "--repo",
})
_MERGE_FLAG = frozenset({
    "-s", "--squash", "-m", "--merge", "-r", "--rebase", "-d", "--delete-branch",
    "--admin", "--disable-auto", "--auto", "-h", "--help",
})
_CREATE_VALUE = frozenset({
    "-H", "--head", "-B", "--base", "-t", "--title", "-b", "--body", "-F", "--body-file",
    "-a", "--assignee", "-l", "--label", "-m", "--milestone", "-p", "--project",
    "-r", "--reviewer", "-T", "--template", "--recover", "-R", "--repo",
})
_API_VALUE = frozenset({
    "-X", "--method", "-f", "--raw-field", "-F", "--field", "-H", "--header", "--input",
    "-q", "--jq", "-t", "--template", "-p", "--preview", "--hostname", "--cache",
})
_API_BODY = frozenset({"-f", "--raw-field", "-F", "--field", "--input"})

_FLAGS_MESSAGE = (
    "move flags after the verb, and write -R as OWNER/REPO; "
    "the check reads only one plain -R before pr or the verb"
)
_UNREADABLE = "can't read the pull request this command names"


class _Failed(Exception):
    """A question the check couldn't answer. The message names which."""


@dataclass(frozen=True)
class Target:
    """A command the check judges against a branch's reviews.

    `pr` is what `gh pr view` is asked about, as the command wrote it, and None
    for the current branch's pull request. `repo` is the repository the
    command names, and `named_by` says where: `-R` as written, the
    `owner/repo` of a `repos/` path, or a pull request URL. `head` and `owner`
    come from `--head [owner:]branch` on a create.
    """

    create: bool
    pr: str | None = None
    repo: str | None = None
    named_by: str = "-R"
    head: str | None = None
    owner: str | None = None


def refusal(command: str, cwd: object) -> str | None:
    """The refusal for one command, or None to allow it.

    The text is read first, and anything it refuses is refused without a git
    or `gh` call. A command the text pass judged is then judged against the
    reviews of the branch it acts on, inside one `try`, so any error refuses
    with the error refusal.
    """
    refused, targets = read(command)
    if refused:
        return "\n".join(refused)
    if not targets:
        return None
    try:
        session = _Session.open(cwd)
        found = [r for r in (_judge(t, session) for t in targets) if r]
    except subprocess.TimeoutExpired as e:
        return _error(f"{_name(e.cmd)} timed out after {e.timeout:g}s")
    except Exception as e:
        return _error(str(e) or type(e).__name__)
    return "\n".join(dict.fromkeys(found)) or None


def _error(reason: str) -> str:
    # The text lives in `_guard`, since `_hook` also prints it when this module
    # can't be imported or raises outside its own `try`.
    from wfctl._guard import review_check_failed

    return review_check_failed(reason)


def _name(cmd: object) -> str:
    """`gh pr view` or `git rev-parse`, for a command that timed out."""
    words = [str(w) for w in cmd] if isinstance(cmd, (list, tuple)) else str(cmd).split()
    program, rest = (words[0], words[1:]) if words else ("?", [])
    if rest[:1] == ["-C"]:
        rest = rest[2:]
    plain = [w for w in rest if not w.startswith("-")]
    return " ".join([program, *plain[: 2 if program == "gh" else 1]])


# --- the text pass ---------------------------------------------------------------


def read(command: str) -> tuple[list[str], list[Target]]:
    """What the text alone refuses, and the commands left to judge.

    Every match is read, and one refusal refuses the whole text. Each refusal
    is a line of its own, so a command that trips two rules names both.
    """
    refused: list[str] = []
    targets: list[Target] = []
    if _SIGN_OFF.search(command):
        refused.append(SIGN_OFF_REFUSAL)
    for m in _GH_WORD.finditer(command):
        problem = _command_words(command, m.end())
        if problem:
            refused.append(f"✗ {problem}")
    for m in _GH_API.finditer(command):
        text = command[m.end():_command_end(command, m.end())]
        problem, writes = _api_call(_api_words(text))
        if problem is None and writes:
            words = _shell_words(text, "gh api", False)
            problem = words if isinstance(words, str) else None
        if problem:
            refused.append(f"✗ {problem}")
    if _CREATE_MUTATION.search(command):
        refused.append(
            "✗ open the pull request with gh pr create so the review check can judge its branch"
        )
    if _MERGE_MUTATION.search(command):
        refused.append(
            "✗ merge the pull request with gh pr merge so the review check can judge its branch"
        )
    for m in _PR_COMMAND.finditer(command):
        verb = m.group("verb")
        name = "gh pr merge" if verb == "merge" else "gh pr create"
        end = _command_end(command, m.start("verb"))
        problem = _shape(command, m.start(), end, name)
        if problem is None:
            pre = [m.group(g) for g in ("pre", "mid") if m.group(g)]
            read_args = _arguments(name, command[m.start("verb"):end], pre)
            if isinstance(read_args, Target):
                targets.append(read_args)
                continue
            problem = read_args
        if problem:
            refused.append(f"✗ {problem}")
    for m in _API_MERGE.finditer(command):
        end = _command_end(command, m.start())
        problem = _shape(command, m.start(), end, "gh api")
        if problem:
            refused.append(f"✗ {problem}")
            continue
        path = _REPOS_PATH.search(command[:m.start()])
        repo = None
        if path and (path["owner"], path["repo"]) != ("{owner}", "{repo}"):
            repo = f"{path['owner']}/{path['repo']}"
        targets.append(Target(False, m["number"], repo, named_by="the path"))
    return list(dict.fromkeys(refused)), targets


def _words(text: str, start: int) -> Iterator[str]:
    """The whitespace-separated words from `start`, each with one closing quote
    or backtick dropped, since it closes an outer quote: `rg 'gh pr'` reads
    `pr`."""
    for m in re.finditer(r"\S+", text[start:]):
        word = m.group()
        yield word[:-1] if word[-1] in "'\"`" else word


def _plain_repo_flag(word: str, words: Iterator[str]) -> bool:
    """Whether `word` starts one plain `-R` flag, consuming its value."""
    if word in ("-R", "--repo"):
        value = next(words, "")
    elif word.startswith(("-R=", "--repo=")):
        value = word.split("=", 1)[1]
    elif word.startswith("-R") and not word.startswith("--"):
        value = word[2:]
    else:
        return False
    return bool(_PLAIN_REPO.fullmatch(value))


def _command_words(text: str, start: int) -> str | None:
    """Why the check can't read the `gh` command starting at `start`, if it can't
    (research.md R6 pattern 8).

    One plain `-R` is the only flag allowed before the command word or before
    the verb after `pr`, since `gh` reads a verb's flags there too, and each
    plan review found one more spelling a list of refused ones missed.
    """
    words = _words(text, start)
    repos = 0
    for word in words:
        if word.startswith("-"):
            repos += 1
            if repos > 1 or not _plain_repo_flag(word, words):
                return _FLAGS_MESSAGE
            continue
        if word not in GH_COMMANDS:
            return f"run gh {word} in your own terminal; the check knows only gh's own commands"
        if word != "pr":
            return None
        break
    else:
        return None
    for word in words:
        if word.startswith("-"):
            repos += 1
            if repos > 1 or not _plain_repo_flag(word, words):
                return _FLAGS_MESSAGE
            continue
        if _UNPLAIN_VERB.search(word):
            return "write gh's command words out plainly; the check can't read them"
        return None
    return None


def _quote_at(text: str, end: int) -> str | None:
    """The quote character open at `end`, reading the text as the shell does."""
    quote: str | None = None
    i = 0
    while i < end:
        c = text[i]
        if c == "\\" and quote != "'":
            i += 2
            continue
        if quote is None and c in "'\"":
            quote = c
        elif c == quote:
            quote = None
        i += 1
    return quote


def _command_end(text: str, start: int) -> int:
    """Where the command holding `start` ends: the next separator outside any
    quote opened after `start`, or the quote that was open at `start` closing.

    A match inside quotes, as in `bash -c "gh pr create"` or `echo "gh pr
    create"`, ends where its quote does, so the closing quote isn't read as one
    of its arguments.
    """
    outer = _quote_at(text, start)
    inner: str | None = None
    i = start
    while i < len(text):
        c = text[i]
        if c == "\\" and inner != "'" and outer != "'":
            i += 2
            continue
        if inner is None:
            # `2>&1`, `&>`, `<&` and `>|` are redirections, not separators.
            redirect = (c == "&" and (text[i - 1:i] in ("<", ">") or text[i + 1:i + 2] == ">")) or (
                c == "|" and text[i - 1:i] == ">"
            )
            if c == outer or (c in ";|&\n" and not redirect):
                return i
            if c in "'\"":
                inner = c
        elif c == inner:
            inner = None
        i += 1
    return len(text)


def _shape(text: str, start: int, end: int, name: str) -> str | None:
    """Why the text around a matched command keeps the check from judging it.

    The check reads the branch and its newest commit before any of the text
    runs. A command before the match, a substitution up to its end, or an
    environment prefix can each change what the pull request command acts on
    after the check has judged it, and the check's own `git` and `gh` calls
    don't see a prefix. Quoted or not, since `bash -c` runs what is quoted.
    """
    if _SEPARATOR.search(text, 0, start):
        return (
            f"run {name} on its own; the check judges the branch before anything "
            "earlier in the command runs"
        )
    if _SUBSTITUTION.search(text, 0, end):
        return (
            f"run {name} without a substitution; the shell runs it after the check "
            "has judged the branch"
        )
    if _ENV_PREFIX.search(text, 0, start):
        return (
            f"run {name} without an environment prefix or env; the check can't see "
            "where it points gh"
        )
    return None


def _flags(
    words: Sequence[str], takes_value: frozenset[str], known: frozenset[str] | None,
) -> tuple[list[tuple[str, str | None]], list[str]] | None:
    """Each flag with its value, and the other words, the way `gh` reads them.

    A short group is read letter by letter: a flag that takes no value stands
    on its own, so `-sd` is `-s -d`, and one that takes a value takes the rest
    of the word or the next word, so `-tfix` and `-st fix` both name `fix`.
    None when a flag isn't in `known`, or a value is missing. `known` None
    means every other flag takes no value. A long flag that takes no value
    keeps one written after `=`, since `--help=false` turns help off and `gh`
    then runs the command.
    """
    pairs: list[tuple[str, str | None]] = []
    args: list[str] = []
    it = iter(words)
    for word in it:
        if word.startswith("--") and len(word) > 2:
            name, eq, value = word.partition("=")
            if name in takes_value:
                found = value if eq else next(it, None)
                if found is None:
                    return None
                pairs.append((name, found))
            elif known is None or name in known:
                pairs.append((name, value if eq else None))
            else:
                return None
        elif word.startswith("-") and len(word) > 1 and word != "--":
            letters = word[1:]
            for i, letter in enumerate(letters):
                flag = f"-{letter}"
                if flag in takes_value:
                    found = letters[i + 1:].removeprefix("=") or next(it, None)
                    if found is None:
                        return None
                    pairs.append((flag, found))
                    break
                if known is not None and flag not in known:
                    return None
                pairs.append((flag, None))
        else:
            args.append(word)
    return pairs, args


def _repo_value(flag: str) -> str:
    """The value of an `-R` flag as pattern 1 captured it, such as `-R=o/r `."""
    flag = flag.strip()
    for prefix in ("--repo=", "-R=", "--repo", "-R"):
        if flag.startswith(prefix):
            return flag[len(prefix):].strip()
    return flag


def _arguments(name: str, text: str, pre: Sequence[str]) -> Target | str:
    """The command a matched `gh pr` verb runs, or why the check can't read it.

    `--help` is judged like any other flag. Allowing it as help, since `gh`
    prints help and does nothing else, let a `--help` the shell drops or
    redirects carry a merge past the check unjudged, in more spellings than
    one review round could list.
    """
    words = _shell_words(text, name, True)
    if isinstance(words, str):
        return words
    words = words[1:]
    create = name == "gh pr create"
    read_flags = _flags(
        words, _CREATE_VALUE if create else _MERGE_VALUE, None if create else _MERGE_FLAG,
    )
    if read_flags is None:
        return _UNREADABLE
    pairs, args = read_flags
    flags = {flag for flag, _ in pairs}
    if "--auto" in flags:
        return "auto-merge would merge a head this check never judged"
    repos = [_repo_value(p) for p in pre] + [v or "" for f, v in pairs if f in ("-R", "--repo")]
    if len(repos) > 1:
        return "name the repository once; the check can't tell which -R gh uses"
    if len(args) > (0 if create else 1):
        return _UNREADABLE
    repo = repos[0] if repos else None
    named_by = "-R"
    url = _PR_URL.match(args[0]) if args else None
    if url:
        if repo is not None:
            return "name the repository once; the check can't tell which -R gh uses"
        repo, named_by = f"{url['host']}/{url['owner']}/{url['repo']}", "the URL"
    if repo is not None:
        parts = repo.split("/")
        if not 2 <= len(parts) <= 3 or (len(parts) == 3 and parts[0].lower() != "github.com"):
            return f"{named_by} names another repository; its reviews aren't here"
    heads = [v for f, v in pairs if f in ("-H", "--head") and v is not None]
    owner, _, head = heads[-1].rpartition(":") if heads else ("", "", "")
    return Target(
        create, pr=args[0] if args else None, repo=repo, named_by=named_by,
        head=head or None, owner=owner or None,
    )


def _shell_words(text: str, name: str, variables: bool) -> list[str] | str:
    """The words `gh` receives from `text`, or why the check can't tell.

    `shlex` keeps what the shell changes before `gh` starts, so the words are
    read as written first, quotes kept. A word starting with `#` begins a
    comment, a brace or a glob expands into other words, an unquoted variable
    splits into words, and a redirection names a file rather than an argument.
    A comment hid a `--help` the shell drops, and a brace slid a second pull
    request in after the check had read one.

    `variables` is False for `gh api`, since `_api_call` has already judged a
    variable path, with a message that names the path.
    """
    written = _raw_words(text)
    if any(word.startswith("#") and bare.startswith("#") for word, bare in written):
        return (
            f"run {name} without a # comment; the shell drops it, and the check "
            "would read it as part of the command"
        )
    if any(_BRACE.search(bare) or set(bare) & set("*?[") for _, bare in written):
        return (
            f"write {name}'s arguments without a brace or a glob; the shell expands "
            "them after the check has read the command"
        )
    if variables and any("$" in bare for _, bare in written):
        return (
            f"write {name}'s arguments without an unquoted variable; the shell splits "
            "it into words after the check has read the command"
        )
    kept: list[str] = []
    target = False
    for word, bare in written:
        if target:
            target = False
            if not set(bare) & set("<>&|"):
                continue
        elif not set(bare) & set("<>"):
            kept.append(word)
            continue
        elif word == bare and _FD_COPY.fullmatch(word):
            continue
        elif word == bare and _REDIRECT_ALONE.fullmatch(word):
            target = True
            continue
        elif _REDIRECT_TO.fullmatch(word):
            continue
        return (
            f"write {name}'s redirections as words of their own, such as 2>&1 or "
            "> out.txt; the check can't read this one"
        )
    if target:
        return _UNREADABLE
    try:
        return shlex.split(" ".join(kept))
    except ValueError:
        return _UNREADABLE


def _raw_words(text: str) -> list[tuple[str, str]]:
    """Each word as written, quotes kept, beside its characters outside quotes.

    A character escaped with a backslash counts as quoted, since the shell
    gives it no meaning of its own.
    """
    words: list[tuple[str, str]] = []
    word: list[str] = []
    bare: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(text):
        c = text[i]
        if quote is None and c.isspace():
            if word:
                words.append(("".join(word), "".join(bare)))
                word, bare = [], []
        elif c == "\\" and quote != "'" and i + 1 < len(text):
            word.append(text[i:i + 2])
            i += 1
        else:
            word.append(c)
            if quote is None and c in "'\"":
                quote = c
            elif c == quote:
                quote = None
            elif quote is None:
                bare.append(c)
        i += 1
    if word:
        words.append(("".join(word), "".join(bare)))
    return words


def _api_words(text: str) -> list[str]:
    """The words of a `gh api` call, read only far enough to tell whether it
    writes: the redirections the check reads are dropped, and every other word
    is kept as written.

    Not `_shell_words`, which refuses a glob, a comment, or an odd redirection
    outright. A read can't open or merge a pull request, and refusing those
    shapes in every `gh api` call refused `gh api repos/o/r/pulls?state=open`,
    `rg "gh api [a-z]+/"` and a commit message that mentioned `gh api`. A
    redirection is still dropped, since one taken as the path turned every
    `gh api` refusal off.
    """
    kept: list[str] = []
    target = False
    for word, bare in _raw_words(text):
        if target:
            target = False
        elif word == bare and _REDIRECT_ALONE.fullmatch(word):
            target = True
        elif not (word == bare and _FD_COPY.fullmatch(word) or _REDIRECT_TO.fullmatch(word)):
            kept.append(word)
    try:
        return shlex.split(" ".join(kept))
    except ValueError:
        return " ".join(kept).split()


def _api_call(words: Sequence[str]) -> tuple[str | None, bool]:
    """Why a `gh api` call refuses every time, if it does (R6 patterns 3, 6, 7),
    and whether it writes.

    A create through the `pulls` endpoint and a GraphQL query read from a file
    each act on a branch named in a body the check can't read reliably. A
    write to a variable path could be a merge. A read can't open or merge a
    pull request, so a variable path with no body and no method passes.
    """
    path: str | None = None
    body = False
    reads_file = False
    method: str | None = None
    it = iter(words)
    for word in it:
        if word.startswith("--"):
            name, eq, value = word.partition("=")
            if name in _API_VALUE and not eq:
                value = next(it, "")
        elif word.startswith("-") and len(word) > 1:
            name, value = word[:2], word[2:].removeprefix("=")
            if name in _API_VALUE and not value:
                value = next(it, "")
        else:
            path = word if path is None else path
            continue
        if name in _API_BODY:
            body = True
            reads_file = reads_file or name == "--input" or (
                name in ("-F", "--field") and value.startswith("query=@")
            )
        elif name in ("-X", "--method"):
            method = value.upper()
    writes = body or (method is not None and method != "GET")
    if path is None:
        return None, writes
    # `/graphql` and a full URL reach the same endpoint as `graphql`, since
    # `gh` sends a body to any path as a POST.
    endpoint = path.split("?", 1)[0].rstrip("/")
    if endpoint == "graphql" or endpoint.endswith("/graphql"):
        if reads_file:
            return "put the GraphQL query in the command; the check doesn't read files", writes
        return None, writes
    if ("$" in path or "`" in path) and writes:
        return "write the gh api path out plainly; the check can't read where it writes", writes
    if _PULLS_CREATE.search(path) and (body or method == "POST"):
        return (
            "open the pull request with gh pr create so the review check can judge its branch",
            writes,
        )
    return None, writes


# --- the judging pass ------------------------------------------------------------


@dataclass
class _Session:
    """The session's checkout, read from the hook payload's `cwd`.

    The hook process runs in the agent's project directory, and that differs
    from the session's once an earlier command has run `cd`. Judging the hook's
    own directory would let a session in the `main` checkout `cd` into a
    worktree and open its pull request against `main`'s reviews.
    """

    cwd: str
    root: Path
    branch: str
    _name_with_owner: str | None = None

    @classmethod
    def open(cls, cwd: object) -> _Session:
        from wfctl import _paths

        if not isinstance(cwd, str) or not cwd:
            raise _Failed("the hook payload names no working directory")
        found = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        if found.returncode != 0 or not found.stdout.strip():
            raise _Failed(f"the working directory {cwd} isn't inside a git repository")
        root = Path(found.stdout.strip())
        return cls(cwd, root, _paths.resolve_branch(root, timeout=TIMEOUT))

    def run(self, *args: str) -> str:
        r = subprocess.run(
            list(args), cwd=self.root, capture_output=True, text=True, timeout=TIMEOUT,
        )
        if r.returncode != 0:
            raise _Failed(f"{_name(args)} failed: {r.stderr.strip() or f'exit {r.returncode}'}")
        return r.stdout

    def name_with_owner(self) -> str:
        if self._name_with_owner is None:
            found = json.loads(self.run("gh", "repo", "view", "--json", "nameWithOwner"))
            self._name_with_owner = str(found["nameWithOwner"])
        return self._name_with_owner


def _judge(target: Target, session: _Session) -> str | None:
    """The refusal for one judged command, or None when every group has
    reviewed the commit it acts on, or a sign-off covers what they haven't."""
    from wfctl import _paths, _review, _review_config

    override = os.environ.get("WFCTL_BRANCH")
    if override:
        checked_out = session.run("git", "branch", "--show-current").strip()
        if checked_out != override:
            return (
                f"✗ WFCTL_BRANCH names {override}, but {session.cwd} is on "
                f"{checked_out or 'a detached HEAD'}; the override names a different branch "
                "from the session's directory, so unset it"
            )

    if target.repo is not None:
        repo = target.repo.split("/")[-2:]
        if "/".join(repo).casefold() != session.name_with_owner().casefold():
            return f"✗ {target.named_by} names another repository; its reviews aren't here"
    if target.owner is not None:
        if target.owner.casefold() != session.name_with_owner().split("/")[0].casefold():
            return "✗ --head names another owner's branch; its reviews aren't here"

    if target.create and target.head is None:
        branch, head = session.branch, _review.head_commit(session.root, TIMEOUT)
    elif target.create:
        branch = str(target.head)
        # `ls-remote` matches a pattern by its end, so `a/refs/heads/<branch>`
        # is listed too, and can sort first.
        ref = f"refs/heads/{branch}"
        listed = session.run("git", "ls-remote", "origin", ref).splitlines()
        exact = [line.split()[0] for line in listed if line.split()[1:] == [ref]]
        if not exact:
            raise _Failed(f"origin has no branch {branch}")
        head = exact[0]
    else:
        view = ["gh", "pr", "view", *([target.pr] if target.pr else [])]
        if target.repo is not None and target.named_by == "-R":
            view += ["-R", target.repo]
        found = json.loads(session.run(*view, "--json", "headRefName,headRefOid"))
        branch, head = str(found["headRefName"]), str(found["headRefOid"])

    trunk_ref = _paths.trunk_branch(session.root, timeout=TIMEOUT)
    if trunk_ref is None:
        raise _review.NoTrunk()
    trunk = trunk_ref.removeprefix("origin/")
    # Compared with the judged branch, never the checked-out one, since the
    # `main` checkout judges other branches with the trunk checked out. A
    # trunk that is the judged branch makes every commit on it read as already
    # on the trunk, and a `wfctl.json` edit is all it takes.
    if branch == trunk:
        return (
            f"✗ the trunk branch is {trunk}, the branch this command acts on; "
            "check trunk in wfctl.json"
        )
    if branch != session.branch:
        if session.branch != trunk:
            return (
                f"✗ run this from the checkout on {trunk}; a worktree opens and merges only "
                "its own branch's pull request"
            )
        if os.environ.get("WFCTL_STATE_DIR"):
            return (
                f"✗ WFCTL_STATE_DIR names one branch's state directory, so the check can't "
                f"read {branch}'s reviews; unset it"
            )

    if not _review.is_commit(session.root, head, TIMEOUT):
        raise _Failed(f"{head[:7]} isn't in this repository; run git fetch")
    groups, problems = _review_config.load(session.root)
    if problems:
        raise _Failed(f"can't read the review config: {problems[0]}")
    agent_dir = _paths.resolve_agent_dir(session.root, branch, create=False, timeout=TIMEOUT)
    pending = _review.unreviewed(session.root, agent_dir, groups, head, TIMEOUT, branch=branch)
    if not pending:
        # After the reviews, so a branch with unreviewed commits hears about
        # those first, and the record checks judge the commit the reviews did.
        from wfctl import _record_gate

        return _record_gate.refusal(session, branch, head, trunk_ref)
    subjects = _review.subjects(session.root, [c for cs in pending.values() for c in cs], TIMEOUT)
    lines = [f"✗ {branch} has commits no review covered:"]
    lines += [f"  {line}" for line in _review.pending_lines(pending, subjects)]
    lines += [
        "  Run the review groups (wfctl review start <group>), or ask a person to run",
        "  `wfctl review sign-off` in their own terminal.",
    ]
    return "\n".join(lines)
