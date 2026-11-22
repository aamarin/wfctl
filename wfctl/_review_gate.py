"""The guard's review check: a pull request doesn't open or merge while a review
group has commits it hasn't reviewed.

`wfctl hook worktree-guard` runs this before its worktree check, in the same
process, rather than as a second hook entry that would charge every Bash call a
second interpreter start (`622-review-check-in-worktree-guard.md`). The guard
imports this module only when the command holds `gh` in any case, `merge`,
`sign`, `approve`, `accept`, `arch`, `notes`, `mirror`, `.push`, both `push`
and `*`, `wfctl` beside a `$`, a backtick, or a `{`, or `$'`, so a command
holding none of them pays a substring test and nothing else.

The check reads the command in two passes. The first reads only the text and
refuses what the text alone settles: the literal words of the accept, the
sign-off, or the import approval anywhere in the command, unless Claude Code
will ask the user before the command runs, it is the accept's dry run, or one
program that only reads text holds them; one of those built some other way
that the guard can read; a hand-written git note or a push of a notes ref, a `gh` command word
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
call (`guard/_hook.py`).
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
APPROVE_IMPORTS_REFUSAL = (
    "✗ wfctl arch approve-imports is for a person to run in their own terminal, not an agent."
)
ACCEPT_REFUSAL = (
    "✗ wfctl arch accept is for a person to run in their own terminal, not an agent. "
    "An agent can check a record with wfctl arch check-accept."
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
_SEPARATOR = re.compile(r"[;&|\n]")

NOTES_REFUSAL = (
    "✗ wfctl writes review notes itself when a run completes or a person signs off.\n"
    "  To send a note that didn't reach origin, run `wfctl store reviews`."
)
# Every `git notes` subcommand that changes a note. Reading stays allowed, so
# `show`, `list`, and `git log --notes` still run.
_NOTES_WRITES = frozenset({"add", "append", "edit", "copy", "merge", "remove", "prune"})
# The options before git's own subcommand, and after `notes`, that take their
# value as the next word.
_GIT_VALUE = frozenset({"-c", "-C", "--git-dir", "--work-tree", "--namespace"})
_NOTES_VALUE = frozenset({"--ref"})
# zsh's `=(…)` runs its body into a temporary file, but only at the start of
# a word, since `a=(x)` assigns an array.
_SUBSTITUTION = re.compile(r"\$\(|`|<\(|>\(|(?<![^\s;&|(])=\(")
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


def refusal(command: str, cwd: object, payload: object = None) -> str | None:
    """The refusal for one command, or None to allow it.

    The text is read first, and anything it refuses is refused without a git
    or `gh` call. A command the text pass judged is then judged against the
    reviews of the branch it acts on.

    A check that can't reach an answer raises, and its message is the reason.
    The guard catches it and prints the refusal, because the guard prints the
    same refusal when this module fails to import, and evidence may not import
    the guard (`contexts-are-packages`).
    """
    refused, targets = read(command, cwd, payload)
    if refused:
        return "\n".join(refused)
    if not targets:
        return None
    try:
        session = _Session.open(cwd)
        found = [r for r in (_judge(t, session) for t in targets) if r]
    except subprocess.TimeoutExpired as e:
        # The exception's own message prints the whole argv, which buries the
        # program name in a `-C` path and a dozen flags.
        raise _Failed(f"{_name(e.cmd)} timed out after {e.timeout:g}s") from e
    return "\n".join(dict.fromkeys(found)) or None


def _name(cmd: object) -> str:
    """`gh pr view` or `git rev-parse`, for a command that timed out."""
    words = [str(w) for w in cmd] if isinstance(cmd, (list, tuple)) else str(cmd).split()
    program, rest = (words[0], words[1:]) if words else ("?", [])
    if rest[:1] == ["-C"]:
        rest = rest[2:]
    plain = [w for w in rest if not w.startswith("-")]
    return " ".join([program, *plain[: 2 if program == "gh" else 1]])


# --- the text pass ---------------------------------------------------------------


def read(
    command: str, cwd: object = None, payload: object = None,
) -> tuple[list[str], list[Target]]:
    """What the text alone refuses, and the commands left to judge.

    Every match is read, and one refusal refuses the whole text. Each refusal
    is a line of its own, so a command that trips two rules names both.

    A person-only command passes when the host will ask the user before it
    runs, which `_prompt_will_ask` decides from the hook's `payload` and the
    repository at `cwd`. With no payload, every one is refused.
    """
    refused: list[str] = []
    targets: list[Target] = []
    # The shell deletes a backslash-newline before it splits words, so
    # `wfctl arch \<newline>accept` is one command, not two parts.
    joined = command.replace("\\\n", "")
    # The heredoc is read from the text as written, because the shell keeps a
    # backslash-newline in a quoted heredoc's body. In the joined text, a body
    # line ending in `\` merges with the closing line after it, so the body
    # would seem to run past the line where the shell ends it.
    for p in () if _writes_heredoc_only(command) else _PERSON_COMMANDS:
        if _runs_person_command(joined, p):
            refused.extend(_person_refusal(p, command, cwd, payload))
    if any(_writes_notes(part) for part in _SEPARATOR.split(command)):
        refused.append(NOTES_REFUSAL)
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


# --- the host's prompt -----------------------------------------------------------

# The first line of a refusal the user can clear by approving at the prompt,
# as opposed to the person-only line, which says the agent can't run it here.
_NEEDS_APPROVAL = "✗ {name} needs your approval at Claude Code's prompt."
_PERSON_ONLY = "✗ {name} is for a person to run in their own terminal, not an agent."
_NO_PROMPT_HOST = "  Bob Shell can't ask you first."
# Modes where Claude Code is known to stop at an `ask` rule. Auto mode is left
# out because a matching `ask` rule let the accept run with no prompt there,
# although Claude Code's docs say it should still ask (#833). The bypass and
# `dontAsk` modes are left out because nobody answers in them. A payload that
# names no mode comes from a Claude Code too old to say, so it's refused too.
_PROMPTING_MODES = frozenset({"default", "acceptEdits", "plan"})


def _mode_line(mode: object) -> str:
    if not isinstance(mode, str) or not mode:
        return "  Claude Code didn't say which permission mode it's in, so wfctl can't tell it will ask you."
    return (
        f"  Claude Code is in {mode} mode, where it doesn't reliably ask you first. "
        "Switch to the default mode, or run it in your own terminal."
    )
_NO_REPO = (
    "  wfctl couldn't find the repository, so it can't check that Claude Code will ask."
)
# Names `doctor` rather than the install command, because the guard can't tell
# which wfctl the repo installs with, and a bare `wfctl install-skills` in a
# working copy of wfctl reinstalls the release over the branch (#524). Doctor
# prints the command with the right runner.
_RULE_MISSING = (
    "  .claude/settings.json is missing the rule that makes Claude Code ask. "
    "wfctl doctor prints the command that puts it back."
)
# A command holding one of these could run something the prompt shows as part
# of the command, or run the command in a form the rule doesn't match. Refusing
# them anywhere, a citation included, spares the check from parsing quotes.
# A glob, a brace, or a tilde is on the list because the shell expands it after
# the user approves the text, so `decision-*` could name a record nobody saw.
_SHELL_CHARACTERS = "$`\\;&|<>()*?[]{}~\n"


def _person_refusal(
    p: _PersonCommand, command: str, cwd: object, payload: object,
) -> list[str]:
    """The refusal of `p`, or none when the host will ask the user first.

    With no payload there's no host to ask, so the refusal is the person-only
    line as it was before the prompt could stand in for a terminal.
    """
    if payload is None:
        return [p.refusal]
    try:
        reason = _prompt_will_ask(p, command, payload, cwd)
    except Exception as e:
        raise _Failed(f"couldn't check whether Claude Code will ask first: {e}") from e
    if reason is None:
        return []
    # One entry, since `read` drops a repeated entry and two commands refused
    # for the same reason would otherwise lose the second one's reason line.
    first, line = reason
    return [f"{first.format(name=p.name)}\n{line}"]


def _prompt_will_ask(
    p: _PersonCommand, command: str, payload: object, cwd: object,
) -> tuple[str, str] | None:
    """None when Claude Code will ask the user before `command` runs `p`, or
    the first line and the reason line of the refusal when it won't.

    The host asks only for a plain spelling its rule matches, so the guard
    lets one through only when every condition holds. The reasons are checked
    in the order the refusal reports them, so the first one that fails is the
    one the user has to fix first:

    1. git names the repository, since the rule is read from its settings.
    2. The payload names Claude Code's `Bash` tool. Bob Shell runs the guard
       and can't ask, and a payload with no tool name names no host.
    3. The payload's `permission_mode` is one of `_PROMPTING_MODES`.
    4. `.claude/settings.json` parses and holds the entry's `ask` rule.
    5. The raw text is one entry of `PROMPTED`, compared literally, with no
       shell character and nothing `shlex` reads differently once comments
       count, so an unquoted `#` can't hide the rest of the command.

    wfctl's auto-approve isn't one of them. It lets the agent through wfctl's
    own stops, and Claude Code still holds the command at its prompt until
    the user answers, which is the agreement the command needs.

    The settings file is read only here, after a command has already matched
    a person-only command, so every other command pays nothing for it.
    """
    from wfctl.evidence import prompted_match

    # Claude Code reads its project settings from the directory the session
    # was launched in, and exports that directory to hooks. The payload's
    # `cwd` follows the agent's `cd`, so a session launched in a checkout
    # with no rule could `cd` into one that has it and pass a check keyed on
    # `cwd`, while the host, reading the launch checkout, would not ask. The
    # directory is used as given, not widened to its git top level, since a
    # session launched in a subfolder reads that subfolder's settings.
    launched = os.environ.get("CLAUDE_PROJECT_DIR")
    root = Path(launched) if launched else _repo_root(cwd)
    if root is None:
        return _PERSON_ONLY, _NO_REPO
    tool = payload.get("tool_name") if isinstance(payload, dict) else None
    if tool != "Bash":
        return _PERSON_ONLY, _NO_PROMPT_HOST
    mode = payload.get("permission_mode") if isinstance(payload, dict) else None
    if mode not in _PROMPTING_MODES:
        return _PERSON_ONLY, _mode_line(mode)
    entry = prompted_match(command)
    if entry is not None and entry.command == p.command:
        if f"Bash({entry.text}:*)" not in _ask_rules(root):
            return _NEEDS_APPROVAL, _RULE_MISSING
        if _plain(command):
            return None
    return _NEEDS_APPROVAL, _not_plain(p, command)


def _repo_root(cwd: object) -> Path | None:
    """The repository holding `cwd`, or None when git can't name one."""
    if not isinstance(cwd, str) or not cwd:
        return None
    found = subprocess.run(
        ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, timeout=TIMEOUT,
    )
    root = found.stdout.strip()
    return Path(root) if found.returncode == 0 and root else None


def _ask_rules(root: Path) -> list[str]:
    """The `ask` rules in the repository's Claude Code settings. A file that
    is missing or doesn't parse holds none, so the check refuses."""
    try:
        data = json.loads((root / ".claude" / "settings.json").read_text())
    except (OSError, ValueError):
        return []
    permissions = data.get("permissions") if isinstance(data, dict) else None
    rules = permissions.get("ask") if isinstance(permissions, dict) else None
    return [r for r in rules if isinstance(r, str)] if isinstance(rules, list) else []


def _plain(command: str) -> bool:
    """Whether the shell runs the text as the words it shows: no shell
    character, quotes that close, and no unquoted comment."""
    if any(c in command for c in _SHELL_CHARACTERS):
        return False
    try:
        return shlex.split(command) == shlex.split(command, comments=True)
    except ValueError:
        return False


def _not_plain(p: _PersonCommand, command: str) -> str:
    """The reason line for a form the rule doesn't match, naming each shell
    character the command holds so the user knows what to remove."""
    found = [c for c in _SHELL_CHARACTERS if c in command]
    try:
        if shlex.split(command) != shlex.split(command, comments=True):
            found.append("#")
    except ValueError:
        found.append("an unclosed quote")
    named = ", ".join("a newline" if c == "\n" else c for c in found)
    held = f" It holds {named}." if named else ""
    usage = f"{p.name} <slug>" if p.dry_run else p.name
    return (
        f"  Run it plainly, as {usage}, with no wrapper or second command, "
        f"and with no shell characters such as $ ; & | < > ( ) or a backslash or "
        f"backtick.{held}"
    )


def _runs_person_command(text: str, p: _PersonCommand, nested: str = "") -> bool:
    """Whether the text runs the real person-only command `p`, such as `wfctl
    arch accept` (research R-013), or spells out its three words anywhere.

    The accept was read this way first, and sign-off and approve-imports
    share the reading, so a `grep` or a commit message naming either runs and
    every wrapped form stays refused. The docstrings below say "the accept"
    for whichever command `p` is.

    The outer text goes to `_spells_out` first, which refuses the
    literal words wherever they appear, unless they are a dry run that runs
    wfctl or one program that only reads text holds them. The rest of this
    function reads the forms built at run time, on a best-effort basis.

    The check reads shell words rather than the raw text, so quoting a word
    (`wfctl "arch" accept`) or reaching wfctl through an expansion
    (`"$(command -v wfctl)" arch accept`) still matches. A word holding
    whitespace is read again as a nested command. Text `shlex` can't split is
    refused when `_ACCEPT` finds the command in it, since what the shell
    would run can't be read.

    For those forms, a nested word is usually prose, such as a commit message
    or a grep pattern that names wfctl. So in a nested word the name
    has to stand where the shell would run it, while the outer command
    matches it anywhere. In a `script`, the value of a `-c` option or an
    argument to a shell, that is the start of a command or of a
    substitution. In `prose`, any other word, only a substitution runs, since
    the shell runs `$(…)` and backticks inside double quotes. Every rule
    keyed on an expansion needs the name in one of those positions at any
    level, so `grep -n wfctl "$f"` runs.

    The accept's dry run stays open because it writes nothing, and a person
    checking a drawing runs it. `_dry_run` says which `--dry-run` words count.
    """
    text = _ansi_c_unquoted(text)
    # Quotes and backslashes removed, since `ar""ch` and `acc\ept` are the
    # words `arch` and `accept` to the shell. Either word is enough, because a
    # variable can stand in for the other.
    plain = _QUOTING.sub("", text)
    if not nested and _spells_out(plain, text, p):
        return True
    # A program that only reads text runs nothing, so the readings below,
    # which treat a backtick in a single-quoted message as a substitution,
    # would only add false refusals.
    if not nested and _reads_text_only(text):
        return False
    if p.group not in plain and p.verb not in plain and not (
        "wfctl" in plain.lower() and _expands(plain)
    ):
        return False
    # The shell runs a substitution's body as a script of its own, so a
    # runner or a separator inside it, as in `"$(cd /tmp && wfctl …)"`,
    # starts a command the word-level reading can't see. A prose word has lost
    # the quotes that said whether the shell runs its `$(`, so the bodies
    # are read from the text that still has them, one level up.
    if nested != "prose" and any(
        _runs_person_command(body, p, how)
        for body, how in map(_body_reading, _substitution_bodies(text))
    ):
        return True
    # A comment runs nothing, but a quoting form the guard misreads can make
    # a command look like one, so a comment naming the accept is refused.
    if p.loose.search(_QUOTING.sub("", _uncommented(text)[1])):
        return True
    try:
        commands = _commands(text)
    except ValueError:
        return bool(p.loose.search(plain)) or _in_order(_runnable(text), p)
    # Command substitution runs text the split can't scope: in
    # `echo $(wfctl arch accept …) --dry-run` the flag belongs to `echo`.
    substituted = bool(_SUBSTITUTION.search(text))
    # A shell among the commands can read the others' output as its script, as
    # in `echo '…' | sh`, so every quoted word in the text reads as a script.
    # tmux runs its arguments but never reads its input as a script, so
    # `tmux capture-pane -p | grep '…'` only searches text. Its own `\;`
    # chains subcommands, though, and the split leaves the ones after it
    # reading as commands of their own, so a tmux chain counts too.
    programs = [_program(words) for words in commands]
    piped = any(p in _SHELLS - {"tmux"} for p in programs) or (
        "tmux" in programs and bool(_TMUX_CHAIN.search(text))
    )
    return any(_runs_in(words, p, substituted, nested, piped) for words in commands)


def _spells_out(plain: str, text: str, p: _PersonCommand) -> bool:
    """Whether the literal words of the accept appear anywhere in the text,
    other than as a dry run.

    The readings below each follow one way the shell can run a string, and
    the security rounds on #792 each found a way they missed. The record
    `guard-catches-literal-accept.md` promises the literal words are refused
    wherever the shell runs them. Refusing them wherever they appear keeps
    that promise without knowing every program that runs a string. The one
    exception is a command `_reads_text_only` accepts, such as a commit
    message or a grep, since the threat model record says those must run.

    A dry run still passes, but only when nothing in the text substitutes,
    since `echo $(wfctl arch accept …) --dry-run` gives the flag to `echo`,
    when no shell or heredoc could run the words after another stage drops
    the flag, and when every place the words appear is a command the split
    reads as a dry run that runs wfctl. Words the split doesn't see as a command, such as a quoted
    message or a comment, count against it.

    The split's words are read as well, whether or not the text search found
    anything, since a redirection target such as `> wfctl` can hide the words
    from the search. A quoted word is split again, up to three levels, since
    it may be a script that `bash -c` or `git rebase -x` runs.
    """
    hits = len(p.literal.findall(plain))
    if hits and _reads_text_only(text):
        return False
    if hits and _SUBSTITUTION.search(text):
        return True
    try:
        commands = _commands(text)
    except ValueError:
        return bool(hits) or _in_order(_runnable(text), p)
    # A dry run counts only as the whole command line. An earlier command
    # can put code between the typed words and wfctl: a function or alias
    # named wfctl, zsh's `functions[wfctl]=`, or a `DEBUG` trap, each of which
    # can drop the flag. Listing every way to do that kept missing one.
    # This count has to read the same split as the dry-run check below. If
    # the two disagree about where a command ends, a program before the
    # boundary goes unread, and it can run the accept without the flag. The
    # split ends a command at the `&` of `2>&1` and `&>` too, so a dry run
    # carrying either is refused until #821 reads those redirections.
    if hits and len(commands) != 1:
        return True
    # A shell in the command can read another command's output as its
    # script, after a stage such as `cut` has dropped the flag. A heredoc
    # body is input to a command, not commands, though the split reads each
    # line as one, so a dry run there counts for nothing.
    if hits and (
        any(_program(words) in _SHELLS for words in commands)
        or _HEREDOC.search(text)
    ):
        return True
    dry_runs = 0
    for depth, words in _commands_within(commands):
        # A redirection target naming wfctl, as in `wfctl >wfctl arch accept
        # x --dry-run`, starts a second match that ends where the first one
        # does. The text search counts that once, so the dry run counts once.
        counted: set[int] = set()
        if depth == _UNREADABLE_DEPTH:
            unreadable = _QUOTING.sub("", words[0])
            if p.literal.search(unreadable) or _in_order(unreadable, p):
                return True
            continue
        # A dry run counts only where wfctl is the program the command runs.
        # `echo wfctl arch accept x --dry-run` prints the words, and a later
        # stage such as `cut` can drop the flag before any reader of the
        # output, whether a shell or `source /dev/stdin`, runs them. An
        # assignment in front of it, such as zsh's `functions[wfctl]=…`, can
        # redefine what runs, so it leaves no dry run either. Nor does
        # `xargs`, whose `-I--dry-run` swaps the flag for each input line.
        runs = _command_starts(words, True)[0]
        rewrites = any(_ASSIGNMENT.match(w) for w in words[:runs]) or "xargs" in words[:runs]
        for i in range(len(words)):
            end = _past_words(words, i + 1, p) if _names_wfctl(words[i]) else None
            if end is not None:
                # A second match that ends where the counted dry run ends,
                # as from `>wfctl` in `wfctl >wfctl arch accept x --dry-run`,
                # shares its `arch accept` with the command wfctl runs, so
                # it runs nothing of its own.
                if i != runs and end in counted:
                    continue
                if i != runs or rewrites or not p.excused(words[end:]):
                    return True
                # Only a dry run the count above saw can offset it. One
                # named `$X` or `wf?tl`, one quoted inside another command,
                # or one whose words the count reads differently was never
                # a hit, so counting it would excuse a literal accept
                # quoted somewhere else. The count read the text with every
                # quote removed, so the dry run is read the same way.
                span = _QUOTING.sub("", " ".join(words[i:end]))
                if depth == 0 and end not in counted and p.literal.search(span):
                    counted.add(end)
                    dry_runs += 1
    return dry_runs < hits


# The programs that only read their arguments as text, each with the words
# that must open the command. `git commit` takes no global option, since
# `git -c core.editor=…` runs a program, and git won't let an alias replace
# `commit`. `rg` is left out because its `--pre` option runs a program.
_TEXT_READERS = (
    ("git", "commit"),
    ("grep",),
    ("uv", "run", "towncrier", "create"),
    ("towncrier", "create"),
    ("echo",),
    ("printf",),
)
# `echo` can be aliased to a program that takes long options, the same as
# grep, so it takes only short ones too.
_SHORT_OPTIONS_ONLY = frozenset({("git", "commit"), ("grep",), ("echo",)})
# `printf -v 'a[$(…)]' x` runs the substitution, since bash and zsh expand an
# array subscript in the variable name, single quotes or not. A printed string
# never needs an option, so `printf` takes none.
_NO_OPTIONS = frozenset({("printf",)})
# A heredoc that `cat` writes to a file. The quoted delimiter stops the shell
# from expanding the body, so the body is text, whatever it says.
_WRITTEN_HEREDOC = re.compile(
    r"[ \t]*cat[ \t]+>>?[ \t]*[\w./@+-]+[ \t]+"
    r"<<(-?)[ \t]*(?:'(\w+)'|\"(\w+)\"|\\(\w+))[ \t]*\n"
)
# The characters a word outside quotes may hold. Every other character can
# start a separator, a redirection, a substitution, a glob, or a zsh glob
# qualifier such as `*(e:'…':)`, which runs code.
_PLAIN_WORD_CHARACTER = re.compile(r"[\w \t./,:@+%=-]")
# Claude Code runs `grep` as ugrep, and so can a user's alias. ugrep's
# `--filter`, `--pager`, `--view`, and `--config` run a program, and each is a
# long option, so a grep that names the accept may only take short ones.
# `git commit --trailer` runs a command when git config sets one for the key,
# and git takes any unique prefix of a long option, such as `--trai`, so a
# commit may only take short ones too.
_SHORT_OPTIONS = re.compile(r"-[A-Za-z0-9]+")


def _reads_text_only(text: str) -> bool:
    """Whether the text is one command whose program only reads its
    arguments, so the accept's words in them run nothing.

    A commit message, a grep pattern, or a release note that names the
    accept is ordinary work, and `accept-check-threat-model.md` says the
    guard lets it through. The rule is narrow on purpose, since every looser
    reading in the #792 security rounds let an accept through:

    1. The text is one command, and its first words are one of
       `_TEXT_READERS`, with no assignment or runner in front of them. A
       grep or a commit takes only short options.
    2. Outside quotes, every character is a plain word character.
    3. Inside double quotes there is no `$`, backtick, or backslash, since
       the shell expands those there. Single-quoted text is never expanded.
    4. The text is one line, even inside quotes, since the split that counts
       commands reads a newline as a separator.
    """
    outside: list[str] = []
    quote = ""
    for c in text:
        if quote == "'":
            if c == "'":
                quote = ""
        elif quote == '"':
            if c in "$`\\":
                return False
            if c == '"':
                quote = ""
        elif c in "'\"":
            quote = c
        else:
            outside.append(c)
    if quote or "\n" in text:
        return False
    if not all(_PLAIN_WORD_CHARACTER.fullmatch(c) for c in outside):
        return False
    words = shlex.split(text)
    reader = next((r for r in _TEXT_READERS if tuple(words[: len(r)]) == r), None)
    if reader is None:
        return False
    if reader in _NO_OPTIONS:
        return not words[len(reader)].startswith("-") if len(words) > len(reader) else True
    if reader in _SHORT_OPTIONS_ONLY:
        return all(_SHORT_OPTIONS.fullmatch(w) for w in words[1:] if w.startswith("-"))
    return True


def _writes_heredoc_only(text: str) -> bool:
    """Whether the text is one `cat > file <<'EOF'` command and its body,
    with nothing after the closing line.

    The body ends at the first line that matches the delimiter, which is
    where the shell ends it too, so the text has to be the command as
    written, with no backslash-newline joined. Any text after that line is a command, so
    the heredoc only counts when nothing but whitespace follows. The file
    name may hold only plain characters, so it can't be a substitution or a
    second redirection.
    """
    m = _WRITTEN_HEREDOC.match(text)
    if not m:
        return False
    delimiter = m[2] or m[3] or m[4]
    tabs = "\t*" if m[1] else ""
    end = re.compile(rf"^{tabs}{re.escape(delimiter)}$", re.M).search(text, m.end())
    return end is not None and not text[end.end():].strip()


def _commands_within(commands: list[list[str]]) -> list[tuple[int, list[str]]]:
    """Each command with its depth: the split's own at 0, then the commands
    inside any word that holds whitespace or a separator, up to depth 3.

    A word the split can't read, such as a script holding a heredoc with an
    apostrophe, comes back as one command of its own, `[word]`, at depth 4.
    The guard can't tell what it runs, so the caller reads it as an accept
    when the literal words appear in it.
    """
    found = [(0, words) for words in commands]
    k = 0
    while k < len(found):
        depth, words = found[k]
        k += 1
        if depth == 3:
            # Past the deepest level read, a word holding whitespace is a
            # script the guard can't see into, like one the split can't read.
            found.extend(
                (_UNREADABLE_DEPTH, [word]) for word in words
                if any(c in word for c in " \t\n;&|")
            )
        if depth >= 3:
            continue
        for word in words:
            if any(c in word for c in " \t\n;&|"):
                try:
                    found.extend((depth + 1, inner) for inner in _commands(word))
                except ValueError:
                    found.append((_UNREADABLE_DEPTH, [word]))
    return found


def _past_words(words: list[str], j: int, p: _PersonCommand) -> int | None:
    """The index past the command's two words, such as `arch accept`, read
    from `words[j]`, or None when the words there aren't those two.

    The shell drops a redirection before wfctl sees its arguments, and
    wfctl's parser drops a `--`, so either one between the words still runs
    the accept, and the command's `literal` pattern counts it as a hit.

    More than `_MAX_SKIPPED` such words reads as the accept with no dry run,
    since no real command needs that many, and reading on would rescan the
    same run of words from every name before it.

    The shell ends a word at `<` or `>`, so `arch>/dev/null` is the word
    `arch` and a redirection, though the split keeps them as one word.
    """
    skipped = 0
    for expected in (p.group, p.verb):
        while j < len(words):
            if words[j] == "--" or _REDIRECT_WORD.match(words[j]):
                j += 1
            elif _REDIRECT.match(words[j]):
                j += 2
            else:
                break
            skipped += 1
            if skipped > _MAX_SKIPPED:
                return len(words)
        if j >= len(words) or not words[j].startswith(expected):
            return None
        attached = words[j][len(expected):]
        if attached and not _ATTACHED_REDIRECT.match(attached):
            return None
        j += 2 if attached and _skips_next_word(attached) else 1
    return j


def _substitution_bodies(text: str) -> list[str]:
    """The text inside each outermost `$(…)` the shell would run, or running
    to the end of the text when it never closes.

    A `$(` inside single quotes is text, so it opens nothing. Inside double
    quotes the shell still runs it, so it opens a body there.
    """
    bodies = []
    k, double = 0, False
    while k < len(text):
        c = text[k]
        if c == "\\":
            k += 2
        elif c == "'" and not double:
            k = _past_quote(text, k)
        elif c == '"':
            double, k = not double, k + 1
        elif text.startswith("$(", k):
            end = _body_end(text, k + 2)
            bodies.append(text[k + 2:end])
            k = end + 1
        else:
            k += 1
    return bodies


def _body_end(text: str, start: int) -> int:
    """Where the `$(` body starting at `start` closes, or the end of the text.

    A body starts a new quoting context, so a quoted or escaped `)` doesn't
    close it, and neither does the `)` that ends a `case` pattern, as in
    `$(case a in a) wfctl …;; esac)`. Counting either one let the rest of
    the body go unread as a script.
    """
    # Open `case` statements are counted as the scan passes each keyword,
    # since recounting the body at every `)` made a long body quadratic.
    depth, cases, k = 1, 0, start
    while k < len(text):
        c = text[k]
        if c == "\\":
            k += 2
            continue
        if c in "'\"":
            k = _past_quote(text, k)
            continue
        if keyword := _CASE_KEYWORD.match(text, k):
            if k == 0 or not (text[k - 1].isalnum() or text[k - 1] == "_"):
                cases += 1 if keyword[1] == "case" else -1
            k = keyword.end()
            continue
        if c == "(":
            depth += 1
        elif c == ")" and not (depth == 1 and cases > 0):
            depth -= 1
            if depth == 0:
                return k
        k += 1
    return len(text)


def _past_quote(text: str, at: int) -> int:
    """The position just past the quote that closes the one at `at`, or the
    end of the text. A backslash escapes the next character only inside
    double quotes, as in the shell."""
    quote, k = text[at], at + 1
    while k < len(text) and text[k] != quote:
        k += 2 if quote == '"' and text[k] == "\\" else 1
    return min(k + 1, len(text))


def _program(words: list[str]) -> str:
    """The name of the program a command runs, past assignments and runners."""
    first, _ = _command_starts(words, True)
    return words[first].rsplit("/", 1)[-1] if first < len(words) else ""


def _runs_in(
    words: list[str], p: _PersonCommand, substituted: bool, nested: str, piped: bool,
) -> bool:
    """Whether one command's words run the real command `p`.
    `_runs_person_command` says why a nested command reads the name only
    where the shell would run it."""
    first, starts = _command_starts(words, nested != "prose")
    program = _program(words)
    subcommand = words[first + 1] if first + 1 < len(words) else ""
    # `wm send` types its string into another pane's shell, the way `tmux
    # send-keys` does. Every tmux subcommand counts, since even `display`
    # runs a `#(…)` through a shell, and a stored buffer runs once pasted.
    runs_scripts = piped or program in _SHELLS or program == "screen" or (
        program in ("wm", "workmux") and subcommand == "send"
    )
    # ssh joins every argument after the host into one command line for the
    # remote shell, so `ssh host bash -c "'wfctl …'"` runs a script no single
    # word holds. The words are already unquoted, as ssh joins them.
    if program == "ssh" and _runs_person_command(" ".join(words[first + 1:]), p, "script"):
        return True
    # osascript runs AppleScript, which can type any string into a terminal,
    # so a script naming the accept is refused however it's quoted.
    if program == "osascript" and p.loose.search(_QUOTING.sub("", " ".join(words))):
        return True
    # The outer command reads the name anywhere unless its program only reads
    # text, since a runner such as `script -q /dev/null wfctl $C` puts the
    # name after arguments no list of runners can skip.
    anywhere = not nested and program not in _TEXT_TOOLS
    # A script is a command line the shell runs, so the literal words read
    # anywhere in it too, as in `bash -c 'sudo -u root wfctl arch accept …'`,
    # where an option's value hides the start of the command. Only the
    # literal words, since an expansion after the name is common in a script
    # that only names wfctl.
    literal_anywhere = anywhere or (nested == "script" and program not in _TEXT_TOOLS)
    # Whether the words before `i` open a substitution, and how many
    # backticks they hold, kept as the loop goes, since rebuilding that text
    # at every name made a command naming wfctl many times quadratic.
    opened, ticks = False, 0
    for i, word in enumerate(words):
        if i:
            opened = opened or "$(" in words[i - 1] or "${" in words[i - 1]
            ticks += words[i - 1].count("`")
        if any(c.isspace() for c in word):
            script = runs_scripts or (i > 0 and _SCRIPT_OPTION.match(words[i - 1]))
            # `env -S` and `--split-string` split their value into a command
            # line and run it, the way a shell runs `-c`. Only an `env` the
            # shell runs does, so `echo env -S '…'` prints the string, and so
            # does a quoted message. env can sit behind a wrapper no list of
            # runners holds, such as `unbuffer`, so any earlier word naming
            # it counts.
            if nested != "prose" and program not in _TEXT_TOOLS and any(
                w.rsplit("/", 1)[-1] == "env" for w in words[:i]
            ):
                value = _env_split_value(words[i - 1] if i else "", word)
                if value is not None:
                    word, script = value, True
            # tmux runs `#(…)` through a shell, which would otherwise read as
            # the start of a comment and drop the rest of the string.
            if program == "tmux":
                word = word.replace("#(", "$(")
            if _runs_person_command(word, p, "script" if script else "prose"):
                return True
        if 0 < i < len(words) - 1 and _names_wfctl(words[i - 1]):
            placed = not nested or i - 1 in starts or _called(words[i - 1])
            if placed or literal_anywhere:
                view = _closer_dropped(words, i - 1)
                if (
                    (view[i] == p.group or (placed and _expands(view[i])))
                    and (view[i + 1] == p.verb or (placed and _expands(view[i + 1])))
                    and (substituted or not p.excused(words[i + 2:]))
                ):
                    return True
        # The literal name followed by an expansion, in the same word or the
        # next, can become `arch accept` when the shell runs it: one variable
        # can hold both words, and `wfctl${IFS}arch${IFS}accept` splits only
        # then.
        #
        # Two narrowings clear prose that only names wfctl, and both read the
        # word as literal text. Inside a substitution it isn't: the slash in
        # `$(command -v wfctl 2>/dev/null)` and the space in `$(command -v
        # wfctl )` vanish when the shell replaces it. So both apply only when
        # nothing before the name opens one, in its own word or an earlier
        # one, since `shlex` splits an unquoted `$(dirname /x/wfctl/y)`. An
        # even count of backticks before the name closes every one it opens,
        # as in a message that formats `x` as code before naming wfctl.
        #
        # 1. The next word counts only when the name is in the word's last
        #    path component, since `…-wfctl/scratchpad/x` runs a program named
        #    `x`. That keeps what can follow the name and still run it, such
        #    as a glob's `*` or a brace's `,}`.
        # 2. In the same word, only text up to the first space counts, unless
        #    the path's last segment before the first expansion names wfctl
        #    and holds no space. A space inside a word was quoted, so an
        #    expansion after it lands in an argument holding the name and a
        #    space, which is no path to wfctl. A later segment can start the
        #    path again, as in `"/tmp/wfctl x/bin/wfctl"$C`, but a slash in a
        #    file name later in a commit message doesn't. That clears a jq
        #    filter such as `"wfctl") | {number,id}`, and an issue body that
        #    quotes `wfctl owns "…"` before naming `docs/a.md`.
        at = word.lower().find("wfctl")
        if (anywhere or i in starts) and at >= 0:
            view = _closer_dropped(words, i)
            # A backtick touching the name opens the substitution the name
            # runs, as in `` `wfctl status` ``, rather than one around it, so
            # it leaves the name literal.
            before = word[:at - (view is not words)]
            literal = (
                not opened
                and not any(o in before for o in ("$(", "${"))
                and (ticks + before.count("`")) % 2 == 0
            )
            same = view[i][at:]
            head, *tail = re.split(r"\s", same, maxsplit=1)
            if literal and tail and not _restarts_path(same):
                same = head
            if (
                _expands(same)
                or (i + 1 < len(words) and _expands(view[i + 1]) and (
                    not literal or "wfctl" in word.lower().rsplit("/", 1)[-1]))
            ) and (substituted or not p.excused(words[i + 1:])):
                return True
    return False


def _env_split_value(previous: str, word: str) -> str | None:
    """The command line env's split option makes of `word`, or None when
    `word` isn't that option's value.

    env takes the value as the next word after `-S`, a cluster ending in it
    such as `-vS`, or any unambiguous start of `--split-string`, and as the
    rest of the word in `-S'…'` or `--split=…`. The command line it runs
    starts past env's own options, as in `env -S '-u HOME wfctl …'`, so
    those are skipped too.
    """
    def is_long(name: str) -> bool:
        return len(name) > 3 and "--split-string".startswith(name)

    if re.fullmatch(r"-[A-Za-z]*S", previous) or is_long(previous):
        value = word
    elif m := re.match(r"-[A-Za-z]*S(.+)", word, re.S):
        value = m[1]
    elif is_long(word.partition("=")[0]) and "=" in word:
        value = word.partition("=")[2]
    else:
        return None
    rest = value.split()
    k = 0
    while k < len(rest) and (rest[k].startswith("-") or _ASSIGNMENT.match(rest[k])):
        k += 2 if rest[k] in ("-u", "-C", "-P", "-a", "--unset", "--chdir", "--argv0") else 1
    return " ".join(rest[k:])


def _restarts_path(same: str) -> bool:
    """Whether a word holding the name and a space reaches wfctl again before
    its first expansion, as `wfctl x/bin/wfctl$C` or `wfctl x/bin/wf?tl$C`
    do. The segment after the last slash is the program, so it has to name
    wfctl, or hold a glob that can match it, with no space."""
    cuts = [at for at in (same.find("$"), same.find("`")) if at >= 0]
    brace = _BRACE.search(same)
    if brace:
        cuts.append(brace.start())
    last = same[:min(cuts, default=len(same))].rsplit("/", 1)[-1]
    return not any(c.isspace() for c in last) and (
        "wfctl" in last.lower() or any(c in last for c in "*?[")
    )


def _closer_dropped(words: list[str], n: int) -> list[str]:
    """The words without the backtick that closes a substitution opened right
    before the name in `words[n]`, as in `` `wfctl status` ``.

    That backtick ends the command the name runs, so it can't stand in for
    `arch` or `accept`. Only a backtick touching the name opens it, because
    `shlex` has already dropped the quoting that would show an earlier one is
    literal: with `'x`' wfctl …`, pairing across words would let a real
    substitution after the name read as a closer. A literal backtick touching
    the name makes the program's name start with one, and a slash after the
    name would let such a path still reach wfctl, so either leaves the words
    as they are.
    """
    word = words[n]
    at = word.lower().find("wfctl")
    # Only a slash before the closer can extend the program's path, so
    # `` `wfctl status`. See `docs/a.md` `` still pairs.
    end = word.find("`", at + 5)
    if at < 1 or word[at - 1] != "`" or "/" in word[at:end if end >= 0 else None]:
        return words
    view = list(words)
    for k in range(n, len(view)):
        j = view[k].find("`", at + 5 if k == n else 0)
        if j >= 0:
            view[k] = view[k][:j] + view[k][j + 1:]
            break
    return view


# The words that run the command after them, such as `env wfctl …` or `uv
# run wfctl …`. A runner missing here hides the name only inside a nested
# word, and research R-013 lists that gap.
_RUNNERS = frozenset({
    "env", "command", "exec", "nohup", "sudo", "time", "nice", "timeout", "xargs",
    "stdbuf", "caffeinate", "uv", "uvx",
    # The shell's own keywords, so `do wfctl $C` in a loop starts at `wfctl`.
    "if", "then", "else", "elif", "while", "until", "do", "!", "{", "(",
})
# Programs that read their arguments as text, so `grep -n wfctl "$f"` and
# `echo $HOME wfctl` aren't read as building the command. A few can still run
# a program through an option, such as `rg --pre`, which is why
# `_TEXT_READERS` is a shorter list of its own.
# `sed` and `awk` stay off, since each can run a command of its own.
_TEXT_TOOLS = frozenset({
    "grep", "egrep", "fgrep", "rg", "ag", "ack", "echo", "printf", "cat", "head",
    "tail", "wc", "less", "ls", "sort", "uniq", "diff",
})
# The commands whose quoted arguments are shell text, and the option that
# hands one a script: `-c`, or a cluster ending in it such as `-lc`.
_SHELLS = frozenset({
    "sh", "bash", "zsh", "dash", "ksh", "fish", "eval", "ssh", "su", "watch", "script",
    "tmux", "parallel",
})
_SCRIPT_OPTION = re.compile(r"-[A-Za-z]*c\Z")
# The `;` tmux reads as a separator between its own subcommands: escaped or
# quoted, so the shell hands it to tmux rather than ending the command.
_TMUX_CHAIN = re.compile(r"\\;|';'|\";\"")
_CASE_KEYWORD = re.compile(r"(case|esac)\b")
# A command's `literal` pattern, built from the gaps `_gap` returns, matches the
# accept's three words as typed, with quotes and backslashes already
# removed. The name ignores case, since macOS finds `WFCTL` on a
# case-insensitive disk. A redirection or a `--` may sit between the words,
# since neither reaches wfctl as an argument. The quotes are gone by now, so
# a target such as `'a b'` can't be told from the words around it. Anything
# that starts with a word holding `<` or `>`, or with `--`, counts as the gap.
# The word holding `<` or `>` is taken whole, so a target such as `>wfctl`
# doesn't end the gap. Each gap stops at the name or at the word it waits
# for, which keeps the scan linear. A target that holds one of those words,
# such as `> arch`, ends the gap early, and the split's words catch it. The
# shell ends a word at `<` or `>`, so a redirection can start with no space,
# as in `arch>/dev/null`.
def _gap(stop: str) -> str:
    return (
        # Atomic, so the scan after a redirection word never hands part of
        # the word back to it, which made one long word quadratic.
        # A bare operator takes the next word as its target first, so a
        # file named `arch` in `2> arch arch` isn't read as the `arch` word.
        rf"(?:(?:\s+(?:--(?=\s)|(?>[^\s<>]*[<>]+[&!|-]?)\s+(?>\S+)"
        rf"|(?>\S*[<>]\S*))|(?>&?[<>]\S*))"
        rf"(?:(?!(?i:wfctl)|{stop})[\s\S])*?)?\s+"
    )


@dataclass(frozen=True)
class _PersonCommand:
    """One of the three commands only a person may agree to, and the patterns
    that read it in a command's text.

    `group` and `verb` are the two words after `wfctl`, such as `arch` and
    `accept`. Only the accept has a dry run, so `dry_run` says whether a
    `--dry-run` after the words leaves the command allowed.

    `literal` matches the three words as typed, with quotes and backslashes
    already removed, and `_gap` says what may sit between them.

    `loose` is the reading for text `shlex` can't split, such as a heredoc
    body holding an apostrophe. So it reads the name the way the word path
    does: in any case, through an expansion or a glob, with an expansion or a
    brace in the `group` and `verb` positions. It starts at the start of a
    word, or the leading `\\S*` would rescan a long word from every character
    in it.

    `words` holds one pattern per word for `_in_order`.
    """

    group: str
    verb: str
    dry_run: bool
    refusal: str
    literal: re.Pattern[str]
    loose: re.Pattern[str]
    words: tuple[re.Pattern[str], ...]

    @classmethod
    def of(cls, group: str, verb: str, dry_run: bool, refusal: str) -> _PersonCommand:
        g, v = re.escape(group), re.escape(verb)
        return cls(
            group, verb, dry_run, refusal,
            re.compile(rf"(?i:wfctl){_gap(g)}{g}{_gap(v)}{v}(?![\w-])"),
            re.compile(
                rf"(?<!\S)(?i:\S*wfctl\S*|\S*[$`*?\[]\S*)\s+(?:{g}|\S*[$`{{]\S*)"
                rf"\s+(?:{v}|\S*[$`{{]\S*)"
            ),
            tuple(
                re.compile(rf"(?i)(?<![\w-]){re.escape(w)}(?![\w-])")
                for w in ("wfctl", group, verb)
            ),
        )

    @property
    def command(self) -> str:
        """The command as `PROMPTED` names it, such as `arch accept`."""
        return f"{self.group} {self.verb}"

    @property
    def name(self) -> str:
        return f"wfctl {self.command}"

    def excused(self, rest: list[str]) -> bool:
        """Whether the words after the command make it a dry run."""
        return self.dry_run and _dry_run(rest)


_ACCEPT = _PersonCommand.of("arch", "accept", True, ACCEPT_REFUSAL)
_SIGN_OFF = _PersonCommand.of("review", "sign-off", False, SIGN_OFF_REFUSAL)
_APPROVE_IMPORTS = _PersonCommand.of("arch", "approve-imports", False, APPROVE_IMPORTS_REFUSAL)
_PERSON_COMMANDS = (_ACCEPT, _SIGN_OFF, _APPROVE_IMPORTS)
_MAX_SKIPPED = 64
_UNREADABLE_DEPTH = 4
# A heredoc's `<<` or `<<-`, not a here-string's `<<<`.
_HEREDOC = re.compile(r"(?<!<)<<(?!<)")


def _in_order(plain: str, p: _PersonCommand = _ACCEPT) -> bool:
    """Whether `wfctl` and the command's two words appear as words, in that
    order, with anything between them.

    The reading for text the split can't read, such as a heredoc holding an
    apostrophe. The text search's gaps stop at `arch` or `wfctl` inside a
    redirection target such as `/tmp/research`, and with no split to catch
    what they miss, the guard refuses on the words alone.
    """
    at = 0
    for pattern in p.words:
        m = pattern.search(plain, at)
        if not m:
            return False
        at = m.end()
    return True


# A line that only prints a heredoc with a quoted delimiter, such as
# `cat <<'EOF'`, to the terminal.
_PRINTED_HEREDOC = re.compile(
    r"[ \t]*cat[ \t]+<<(-?)[ \t]*(?:'(\w+)'|\"(\w+)\"|\\(\w+))[ \t]*\n"
)


def _runnable(text: str) -> str:
    """The text `_in_order` reads, with quotes removed, or nothing when the
    text only prints heredocs.

    `cat <<'EOF'` with a quoted delimiter prints its body as it is, so a
    message in it that mentions wfctl, arch, and accept, in that order,
    runs nothing. That holds only while `cat` is the real `cat`. An earlier
    line can make it a shell without a pipe or a group, as with `hash -p
    /bin/sh cat`, `alias cat=sh`, or a new `PATH`, so the bodies are left
    out only when the text holds nothing but printed heredocs, each with
    its closing line. The literal accept is still searched for in the whole
    text, bodies included.
    """
    at = 0
    while True:
        while at < len(text) and text[at] in " \t\n":
            at += 1
        if at == len(text):
            return ""
        m = _PRINTED_HEREDOC.match(text, at)
        if not m:
            return _QUOTING.sub("", text)
        delimiter = m[2] or m[3] or m[4]
        tabs = "\t*" if m[1] else ""
        end = re.compile(rf"^{tabs}{re.escape(delimiter)}$", re.M).search(text, m.end())
        if not end:
            return _QUOTING.sub("", text)
        at = end.end()


_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
_OPENS_COMMAND = ("$(", "`", "(", "<(", ">(")


def _command_starts(words: list[str], with_first: bool) -> tuple[int, set[int]]:
    """Where the shell would run a word as a command: the first word past any
    assignments and runners, and each word that opens a substitution or a
    subshell. A substitution such as `$(command -v wfctl)` stands for the
    name, so the word that closes it counts as a start too.

    Returns the first word's position, and the set of starts, which leaves
    the first word out when `with_first` is false.

    A redirection can come before the program, as in `>/dev/null wfctl …`,
    and the shell removes it and its target before running the command, so
    both are skipped too. A process substitution such as `<(…)` runs a
    command of its own, so the reading stops there, whether it stands as a
    word or as a redirection's target, as in `> >(sh)`.
    """
    first = 0
    while first < len(words):
        word = words[first]
        target = words[first + 1] if first + 1 < len(words) else ""
        skips = _skips_next_word(word)
        if _REDIRECT_START.match(word) and "(" not in word and not (
            skips and "(" in target
        ):
            first += 2 if skips else 1
        elif (
            _ASSIGNMENT.match(words[first])
            or words[first] in _RUNNERS
            or (words[first] == "run" and first > 0 and words[first - 1] == "uv")
            or (first > 0 and words[first - 1] in _RUNNERS
                and (words[first].startswith("-") or words[first].isdigit()))
            # An option's number, as in `nice -n 5`.
            or (first > 1 and words[first - 2] in _RUNNERS
                and words[first - 1].startswith("-") and words[first].isdigit())
        ):
            first += 1
        else:
            break
    first = min(first, len(words))
    opens = [i for i, w in enumerate(words) if w.startswith(_OPENS_COMMAND)]
    if with_first:
        opens.insert(0, first)
    starts = set(opens)
    for i in opens:
        if i < len(words) and words[i].startswith(("$(", "`")):
            closer = ")" if words[i].startswith("$(") else "`"
            close = next(
                (k for k in range(i, len(words))
                 if words[k].endswith(closer) and (k > i or len(words[i]) > 2)),
                None,
            )
            if close is not None:
                starts.add(close)
    return first, starts


def _commands(text: str) -> list[list[str]]:
    """The text's commands as shell words, split at `;`, `&`, `|`, and a
    newline only where they stand outside quotes, so a separator inside a
    `bash -c` script stays in the script's word. Raises ValueError on text
    `shlex` can't split.

    Comments are dropped here rather than by `shlex`, which would also drop
    the newline ending one and join the two commands around it. The shell
    drops everything after an unquoted `#`, so a `--dry-run` there never
    reaches wfctl.

    `shlex` returns a quoted `'|'` as the word `|`, the same as a real pipe.
    So each separator inside quotes or after a backslash is swapped for a
    stand-in before the split and swapped back in each word, and only a
    separator the shell would act on ends a command.
    """
    uncommented = _uncommented(text)[0]
    stand_ins = _stand_ins(uncommented)
    lexer = shlex.shlex(
        _quoted_separators_held(uncommented, stand_ins),
        posix=True, punctuation_chars=";&|\n",
    )
    # Not `\r`, which bash and zsh keep inside a word: `2>e\r--dry-run`
    # redirects to a file whose name holds the flag.
    lexer.whitespace = " \t"
    lexer.whitespace_split = True
    lexer.commenters = ""
    returned = str.maketrans(stand_ins, _SEPARATORS)
    commands: list[list[str]] = [[]]
    for token in lexer:
        if token and set(token) <= set(_SEPARATORS):
            commands.append([])
        else:
            commands[-1].append(token.translate(returned))
    return [words for words in commands if words]


# The separators `shlex` reads as punctuation, each swapped for a
# private-use stand-in while it is quoted or escaped.
_SEPARATORS = ";&|\n"


def _stand_ins(text: str) -> str:
    """Four private-use characters, one per separator, none of them in the
    text, so a character typed into the text never comes back from the
    split as a separator. Raises ValueError, which reads as text the split
    can't read, when every block of four is taken."""
    for base in range(0xE000, 0xF900, 4):
        block = "".join(map(chr, range(base, base + 4)))
        if not any(c in text for c in block):
            return block
    raise ValueError("no free stand-in characters")


def _quoted_separators_held(text: str, stand_ins: str) -> str:
    """The text with each separator the shell reads as a literal character,
    inside quotes or after a backslash, swapped for its stand-in.

    Quotes are read the way `_uncommented` reads them: a backslash escapes
    the next character outside single quotes, and a single quote inside
    double quotes is a plain character.

    An unquoted `&` stays a separator even in `2>&1`. Holding it there let
    the accept through wherever the guard misread which `>` was an operator:
    an escaped `\\>`, zsh's `>&!`, and the `>` closing zsh's `<->` glob each
    leave the `&` sending the command to the background without the flag.
    """
    held = str.maketrans(_SEPARATORS, stand_ins)
    out, k, double = [], 0, False
    while k < len(text):
        c = text[k]
        if c == "\\":
            out.append(c + text[k + 1:k + 2].translate(held))
            k += 2
        elif c == "'" and not double:
            end = _past_quote(text, k)
            out.append(text[k:end].translate(held))
            k = end
        elif c == '"':
            double = not double
            out.append(c)
            k += 1
        else:
            out.append(c.translate(held) if double else c)
            k += 1
    return "".join(out)


def _uncommented(text: str) -> tuple[str, str]:
    """The text with each comment removed up to the newline that ends it,
    and the comments it removed.

    The shell starts a comment only at an unquoted `#` that begins a word.
    The words `shlex` returns have lost their quotes, so `echo "#"` would
    read as a comment there and hide every command after it. Quotes are
    read here, on the raw text, instead.

    An escaped space doesn't end a word, so `one\\ #two` is one word and
    starts no comment.
    """
    out, dropped, k, double, word_start = [], [], 0, False, True
    while k < len(text):
        c = text[k]
        if c == "\\":
            out.append(text[k:k + 2])
            k += 2
            word_start = False
        elif c == "'" and not double:
            end = _past_quote(text, k)
            out.append(text[k:end])
            k = end
            word_start = False
        elif c == '"':
            double = not double
            out.append(c)
            k += 1
            word_start = False
        elif c == "#" and not double and word_start:
            end = text.find("\n", k)
            end = len(text) if end < 0 else end
            dropped.append(text[k:end])
            k = end
        else:
            out.append(c)
            k += 1
            word_start = not double and c in " \t\n;&|()"
    return "".join(out), "\n".join(dropped)


_ANSI_C_ESCAPES = {
    "n": "\n", "t": "\t", "r": "\r", "a": "\a", "b": "\b", "e": "\x1b", "E": "\x1b",
    "f": "\f", "v": "\v", "\\": "\\", "'": "'", '"': '"', "?": "?",
}


def _ansi_c_unquoted(text: str) -> str:
    """The text with each `$'…'` rewritten as the plain single-quoted string
    the shell makes of it.

    Inside `$'…'` a backslash escapes the next character, so `$'\\''` is one
    apostrophe. `shlex` and every scanner here read it as a plain quote that
    runs on to the next one, which hid the commands after it.
    """
    if "$'" not in text:
        return text
    out, k, double = [], 0, False
    while k < len(text):
        c = text[k]
        if c == "\\":
            out.append(text[k:k + 2])
            k += 2
        elif c == "'" and not double:
            end = _past_quote(text, k)
            out.append(text[k:end])
            k = end
        elif c == '"':
            double = not double
            out.append(c)
            k += 1
        elif text.startswith("$$", k):
            # The shell's process id, so a quote after it is a plain one.
            out.append("$$")
            k += 2
        elif not double and text.startswith("$'", k):
            value, k = _ansi_c_value(text, k + 2)
            out.append("'" + value.replace("'", "'\\''") + "'")
        else:
            out.append(c)
            k += 1
    return "".join(out)


def _ansi_c_value(text: str, k: int) -> tuple[str, int]:
    """The string a `$'…'` body starting at `k` stands for, and the position
    past its closing quote. Hex, octal, Unicode, and control escapes are
    decoded too, since `$'\\x77fctl'` and `$'\\u0077fctl'` are the word
    `wfctl` to the shell."""
    value = []
    while k < len(text) and text[k] != "'":
        if text[k] == "\\" and k + 1 < len(text):
            nxt = text[k + 1]
            if m := re.match(
                r"x([0-9A-Fa-f]{1,2})|u([0-9A-Fa-f]{1,4})|U([0-9A-Fa-f]{1,8})",
                text[k + 1:k + 10],
            ):
                code = int(m[1] or m[2] or m[3], 16)
                value.append(chr(code) if code <= 0x10FFFF else "�")
                k += 1 + len(m[0])
                continue
            if nxt == "c" and k + 2 < len(text) and text[k + 2] != "'":
                value.append(chr(ord(text[k + 2]) & 0x1F))
                k += 3
                continue
            if m := re.match(r"[0-7]{1,3}", text[k + 1:k + 4]):
                value.append(chr(int(m[0], 8)))
                k += 1 + len(m[0])
                continue
            value.append(_ANSI_C_ESCAPES.get(nxt, "\\" + nxt))
            k += 2
        else:
            value.append(text[k])
            k += 1
    return "".join(value), k + 1


# A `$(…)` body that only prints a heredoc, the usual way to pass a commit
# message or a PR body. Its lines are the message, not commands.
_HEREDOC_MESSAGE = re.compile(
    r"\s*cat\s+<<-?\s*(['\"]?)(\w+)\1[ \t]*\n(.*?)\n[ \t]*\2[ \t]*\n?\s*", re.S
)


def _body_reading(body: str) -> tuple[str, str]:
    """The text to read for a `$(…)` body, and how to read it.

    A body that only prints a heredoc is a message. With a quoted delimiter
    the shell runs nothing in it. Without one it still runs each `$(…)` and
    backtick, so the message reads as prose, where those still count.
    """
    m = _HEREDOC_MESSAGE.fullmatch(body)
    # The shell ends a heredoc at the first delimiter line, so a body with a
    # second one runs the lines between them as commands.
    if not m or re.search(rf"^[ \t]*{m[2]}[ \t]*$", m[3], re.M):
        return body, "script"
    return ("", "prose") if m[1] else (m[3], "prose")


def _called(word: str) -> bool:
    """Whether the name sits right after a quote or an opening bracket, as in
    awk's `system("wfctl` or perl's `system('wfctl`, which is code another
    interpreter runs rather than prose naming the command."""
    at = word.lower().find("wfctl")
    return at > 0 and word[at - 1] in "(\"'[{"


_QUOTING = re.compile(r"[\"'\\]")


def _expands(word: str) -> bool:
    """Whether the shell replaces the word with text the guard can't see: an
    expansion, a substitution, or a brace such as `{arch,}`."""
    return "$" in word or "`" in word or bool(_BRACE.search(word))


def _names_wfctl(word: str) -> bool:
    """Whether the word before `arch accept` can run wfctl: its name in any
    case, since macOS file systems usually ignore case, a path ending in it, an
    expansion whose result the text can't show, or a glob such as `wf?tl`."""
    return "wfctl" in word.lower() or _expands(word) or any(c in word for c in "*?[")


# A redirection operator split off as its own word, such as `>`, `2>>`, `&>`,
# zsh's `>!` and `>|`, a named descriptor's `{fd}>`, or the heredoc's `<<-`.
# `<<-` is the one operator ending in a dash, since `2>-` redirects to a file
# named `-` and takes no word after it.
_REDIRECT = re.compile(r"(?:\d*|\{\w+\})(?:<<-|&?[<>]+[&!|]?)\Z")
# A redirection the shell starts inside a word, as in `arch>/dev/null`.
_ATTACHED_REDIRECT = re.compile(r"&?[<>]")
# A redirection with its target in the same word, such as `2>/dev/null`.
_REDIRECT_WORD = re.compile(r"(?:\d*|\{\w+\})&?[<>]+(?:-|[&!|])?.+\Z", re.DOTALL)


# The operator a redirection word opens with, such as `2>` in `2>-`, so the
# rest of the word is its target.
_REDIRECT_START = re.compile(r"(?:\d*|\{\w+\})&?[<>]+")


def _takes_next_word(word: str) -> bool:
    """Whether the shell reads the word after this one as a redirection's
    target. It does after an operator on its own, such as `>` or `2>>`, and
    after a word that ends at an operator, such as `x<` or `rec>`, since the
    shell splits the word there. A word holding its own target, such as
    `2>-` or `2>/dev/null`, leaves the next word alone, unless the target
    holds another operator, as in `>a>`. The same holds after an argument,
    so `review>/dev/null` leaves the next word alone and `rec>` doesn't.

    A quoted citation such as `--agreed 'a>b'` reads the same way, since
    the split has lost its quotes. That's safe either way: quoted, the
    shell hands wfctl the citation and the next word, and unquoted, it
    hands wfctl `a` and the next word.
    """
    at = _ATTACHED_REDIRECT.search(word)
    if not at:
        return False
    if _REDIRECT.match(word):
        return True
    start = _REDIRECT_START.match(word)
    if start:
        return bool(_ATTACHED_REDIRECT.search(word[start.end():]))
    # The whole operator, so `rec>|` and `rec>&` still wait for a target.
    operator = _OPERATOR.match(word, at.start())
    rest = word[operator.end():] if operator else ""
    return not rest or bool(_ATTACHED_REDIRECT.search(rest))


_OPERATOR = re.compile(r"&?[<>]+[&!|]?")


# A word that ends at an operator, such as `x<`, `rec>`, or `>>|`.
_ENDS_AT_REDIRECT = re.compile(r"[<>][&!|]?\Z")


def _skips_next_word(word: str) -> bool:
    """Whether the next word is a redirection's target, for reading past it.

    `_takes_next_word` leans toward yes, which is safe when the answer only
    stops a `--dry-run` from counting. Skipping a word on that answer isn't
    safe, since the skipped word can be `--agreed`. So this one says yes
    only for an operator on its own or a word ending at one, and leaves
    `rec<f`, which holds its own target, alone.
    """
    return bool(_REDIRECT.match(word) or _ENDS_AT_REDIRECT.search(word))


def _dry_run(rest: list[str]) -> bool:
    """Whether `--dry-run` among the words after `accept` reaches wfctl as the flag.

    It doesn't when it is the value of `--agreed`, which the option parser
    takes as the citation, or the target of a redirection, or after `--`,
    where it is the record's slug.

    Nor after a word holding `#`, since a shell that reads the words again,
    such as `eval` or `sh`, starts a comment there, and the split has lost
    the quotes that would say which shell reads them last. Nor after a word
    closing a group, since `(wfctl …)# --dry-run` comments the flag out and
    zsh hands the words after `() { … }` to the function. A citation such
    as `--agreed 'fix(guard)'` can end in `)`, and a subshell's `)` followed
    by `--dry-run` is a syntax error in both shells, so the value of
    `--agreed` may.
    """
    # The shell removes a redirection and its target before wfctl starts, so
    # `--agreed >f --dry-run` hands wfctl `--agreed --dry-run`. The word
    # wfctl sees before the flag is the last one outside a redirection. The
    # split has lost quotes, so `'>'` reads as an operator too, and the
    # word typed right before the flag is checked as well: whichever
    # reading is right, neither may be `--agreed`.
    previous = typed = ""
    target = False
    for word in rest:
        # The split ends a word at a space only outside quotes, so a word
        # holding one, such as the citation `'issue {draft}'`, was quoted,
        # and its `}` closes nothing.
        closes = not any(c in word for c in " \t") and (
            word.endswith("}") or (word.endswith(")") and previous != "--agreed")
        )
        if word == "--" or "#" in word or closes:
            return False
        if word == "--dry-run" and "--agreed" not in (previous, typed) and not (
            _takes_next_word(typed)
        ):
            return True
        typed = word
        if target:
            target = False
            continue
        at = _ATTACHED_REDIRECT.search(word)
        if at:
            # `--agreed<f` leaves `--agreed` as an argument, while `2>/dev/null`
            # leaves none.
            if not _REDIRECT_START.match(word):
                previous = word[:at.start()]
            target = _skips_next_word(word)
            continue
        previous = word
    return False


def _writes_notes(command: str) -> bool:
    """Whether one command writes a git note or pushes a notes ref
    (`627-guard-blocks-note-writes.md`, research R9).

    It reads `git`, skips git's own options, and looks at the subcommand. A
    `notes` write is refused whichever ref it names, so `--ref`, `-c
    core.notesRef`, and `GIT_NOTES_REF` need no rule of their own. A `push`
    is refused when a word holds `notes/`, which git resolves the short
    `notes/wfctl-review` to, or it carries `--mirror`, which pushes every
    ref, or a wildcard refspec reaching outside branches and tags, such as
    `refs/*:refs/*`. An `update-ref` or a `fetch` naming `refs/notes/` is
    refused, since each writes the ref without `git notes`. So is setting a
    remote's `push` or `mirror`, with `-c` or `git config`, which makes a
    plain push carry refs it doesn't name; reading that setting is refused
    with it. A push that names no notes ref pushes none, unless the remote
    was configured to before, which no text can show. An alias or a script
    that runs these is out of reach of any text rule.
    """
    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    words = [w.lstrip("\\") for w in words]
    for i, word in enumerate(words):
        if word.rsplit("/", 1)[-1] != "git":
            continue
        rest = words[i + 1:]
        sub, after = _subcommand(rest, _GIT_VALUE)
        if sub == "notes":
            verb, _ = _subcommand(after, _NOTES_VALUE)
            if verb in _NOTES_WRITES:
                return True
        if sub == "push" and any(
            "notes/" in w or w == "--mirror" or _wide_wildcard(w) for w in after
        ):
            return True
        if sub in ("update-ref", "fetch") and any("refs/notes/" in w for w in after):
            return True
        # git's own options, and a `config` command's words, rather than every
        # word, so a commit message naming the setting isn't refused.
        options = rest[:len(rest) - len(after) - 1] if sub else rest
        if any(_PUSH_CONFIG.search(w) for w in (*options, *(after if sub == "config" else ()))):
            return True
    return False


# A remote's `push` or `mirror` setting, given with `-c` or written with `git
# config`, makes a plain `git push` push refs no word of it names.
_PUSH_CONFIG = re.compile(r"remote\.\S+\.(push|mirror)\b", re.IGNORECASE)


def _wide_wildcard(word: str) -> bool:
    """Whether a push refspec is a wildcard whose source can match a notes
    ref. `refs/heads/*` and `refs/tags/*` can't, and refusing them would
    refuse pushing every branch."""
    if word.startswith("-") or "*" not in word:
        return False
    source = word.removeprefix("+").split(":", 1)[0]
    return not source.startswith(("refs/heads/", "refs/tags/"))


def _subcommand(words: list[str], valued: frozenset[str]) -> tuple[str | None, list[str]]:
    """The first word that isn't an option, and the words after it. An option
    in `valued` takes the next word as its value."""
    skip = False
    for i, word in enumerate(words):
        if skip:
            skip = False
        elif word in valued:
            skip = True
        elif not word.startswith("-"):
            return word, words[i + 1:]
    return None, []


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

    def run(self, *args: str, keep_cr: bool = False) -> str:
        """The command's output. `keep_cr` decodes it without translating a
        lone carriage return into a newline, for a file whose lines have to be
        counted the way git counts them."""
        r = subprocess.run(list(args), cwd=self.root, capture_output=True, timeout=TIMEOUT)
        if r.returncode != 0:
            stderr = r.stderr.decode(errors="replace").strip()
            raise _Failed(f"{_name(args)} failed: {stderr or f'exit {r.returncode}'}")
        out = r.stdout.decode()
        return out if keep_cr else out.replace("\r\n", "\n").replace("\r", "\n")

    def name_with_owner(self) -> str:
        if self._name_with_owner is None:
            found = json.loads(self.run("gh", "repo", "view", "--json", "nameWithOwner"))
            self._name_with_owner = str(found["nameWithOwner"])
        return self._name_with_owner


def _judge(target: Target, session: _Session) -> str | None:
    """The refusal for one judged command, or None when every group has
    reviewed the commit it acts on, or a sign-off covers what they haven't."""
    from wfctl import _paths, _review

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
    # The trunk's groups plus the head's, both as committed, so a branch that
    # drops a group from its own `wfctl.json` is refused here as CI refuses it
    # (FR-010). `wfctl status` reads the review step through the same call, so
    # the two can't disagree (`review-step-reads-guard-state`).
    coverage = _review.pending_at_head(session.root, branch, TIMEOUT, head=head)
    if coverage.error is not None:
        raise _Failed(coverage.error)
    pending = coverage.pending
    if not pending:
        # After the reviews, so a branch with unreviewed commits hears about
        # those first, and the record checks judge the commit the reviews did.
        from wfctl import _record_gate

        assert coverage.trunk_ref is not None  # set whenever `error` is None
        return _record_gate.refusal(session, branch, head, coverage.trunk_ref)
    subjects = _review.subjects(session.root, [c for cs in pending.values() for c in cs], TIMEOUT)
    lines = [f"✗ {branch} has commits no review covered:"]
    lines += [f"  {line}" for line in _review.pending_lines(pending, subjects)]
    lines += [
        "  Run the review groups (wfctl review start <group>), or ask the user to sign off",
        "  and run `wfctl review sign-off` once they say to.",
    ]
    return "\n".join(lines)
