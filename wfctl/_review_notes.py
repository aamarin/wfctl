"""Review notes: what wfctl records on a commit when a review completes there
or a person signs off through it, read back by the CI check.

A note lives under `refs/notes/wfctl-review` and holds one plain line per
event, such as `reviewed by security` or `signed off by a person`
(`627-review-note-line-per-event.md`). The line carries no run number or time,
so two machines that record the same event write the same line, and git's
`cat_sort_uniq` merge keeps one copy.

`_review` keeps the state directory and the range rules, and touches no
remote. This module is the half that reads and writes git notes, and sends
them to `origin` (research R11). Like `_review`, it imports nothing that loads
`typer` or `rich`.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from wfctl import _review
from wfctl._review_config import Group

NOTES_REF = "refs/notes/wfctl-review"
SIGN_OFF_LINE = "signed off by a person"
_GROUP_PREFIX = "reviewed by "


def group_line(group: str) -> str:
    return f"{_GROUP_PREFIX}{group}"


def coverage_from_notes(
    repo_root: Path,
    head: str,
    groups: Sequence[Group],
    timeout: float | None = None,
    *,
    branch: str | None = None,
    trunk: str | None = None,
) -> tuple[dict[str, str | None], tuple[str, ...]]:
    """What the notes say was reviewed: each group's last reviewed commit, and
    every signed-off commit. `_review.coverage_from_state` returns the same two
    values from the state directory.

    Only the branch's own commits are read, the ones `head` reaches and the
    trunk refs don't (research R3). Commits on the trunk carry notes from
    their own PRs, and reading those would make the two readers disagree. A
    group's last reviewed commit is the newest branch commit whose note names
    it, since a run starts where the last one ended, and so the note covers
    every branch commit before it (research R1).

    The notes are read one commit at a time rather than through `git log
    --notes`, because that reads a note whose content is missing as empty,
    and the commit then passes as unreviewed with no word about why.
    """
    refs = _review.trunk_refs(repo_root, timeout, branch=branch, trunk=trunk)
    commits = _review.branch_commits(repo_root, head, refs, timeout)
    noted = _noted(repo_root, timeout)
    names = {g.name for g in groups}
    last: dict[str, str | None] = {g.name: None for g in groups}
    signed: list[str] = []
    for sha in commits:
        blob = noted.get(sha)
        if blob is None:
            continue
        for line in _read(repo_root, sha, blob, timeout):
            if line == SIGN_OFF_LINE:
                if sha not in signed:
                    signed.append(sha)
            elif line.startswith(_GROUP_PREFIX):
                name = line.removeprefix(_GROUP_PREFIX)
                if name in names and last[name] is None:
                    last[name] = sha
    return last, tuple(signed)


def _noted(repo_root: Path, timeout: float | None) -> dict[str, str]:
    """Each noted commit's note blob. A repository with no notes ref has none,
    which `git notes list` reports by printing nothing."""
    listed = _review.git(
        repo_root, "notes", f"--ref={NOTES_REF}", "list", timeout=timeout,
    ).stdout.splitlines()
    found: dict[str, str] = {}
    for entry in listed:
        blob, _, sha = entry.partition(" ")
        if sha:
            found[sha] = blob
    return found


def _read(repo_root: Path, sha: str, blob: str, timeout: float | None) -> list[str]:
    """The note's lines, stripped, with blank lines dropped."""
    try:
        text = _review.git(repo_root, "cat-file", "blob", blob, timeout=timeout).stdout
    except _review.ReviewError as e:
        raise _review.ReviewError(f"can't read the note on {sha[:7]}: {e}") from e
    return [line.strip() for line in text.splitlines() if line.strip()]


@dataclass(frozen=True)
class Unlisted:
    """What a note on a run's head would claim that no run reviewed."""

    trunk: str
    commits: tuple[str, ...]


def unlisted(
    repo_root: Path,
    agent_dir: Path,
    group: str,
    head: str,
    timeout: float | None = None,
    *,
    branch: str | None = None,
) -> Unlisted:
    """The commits CI would count as reviewed by `group` once `head` carries
    its note, and that no completed run of the group listed, oldest first.

    A run lists its commits against the trunk on `origin` and the local trunk
    branch. CI measures against `origin/<base>` alone, and reads a note as
    covering every branch commit under it. So a commit on a local `main` that
    was never pushed is left out of the run and covered by its note. This
    recomputes the range CI would read, against `origin/<trunk>` only, and the
    caller writes no note while it finds anything.

    A commit a sign-off note covers is left out, since CI counts it as
    reviewed for every group, and a person saw it when they signed off.

    A trunk `origin` doesn't have raises, since CI's range can't be
    recomputed, and a note written anyway would cover whatever CI finds. The
    trunk is the one `review_trunk` reads from the default branch. In a clone
    with no default branch wfctl can trust, the working tree's `trunk` still
    decides, so a PR into a different base is measured against the wrong
    branch. Declaring one is a deliberate step, the same as forging a note.
    """
    # The same trunk `review start` and the guard measure against, read from
    # the default branch's `wfctl.json`, so a branch that declares its own
    # trunk can't move the range a sign-off covers (`review-round-cap`).
    trunk = _review.review_trunk(repo_root, timeout, branch=branch).name.removeprefix("origin/")
    last, signed = coverage_from_notes(
        repo_root, head, [Group(group, "", ())], timeout, branch=branch, trunk=trunk,
    )
    commits = _review.commit_range(
        repo_root, head, last[group], timeout, branch=branch, trunk=trunk,
    ).commits
    listed = _review.reviewed_commits(agent_dir, group)
    present = _review.present_tips(repo_root, signed, timeout)
    return Unlisted(trunk, tuple(
        c for c in reversed(commits)
        if c not in listed and not _review.is_under(repo_root, c, present, timeout)
    ))


# --- writing and sending ---------------------------------------------------------


# The spec store's network timeout. A push that times out reads the same as an
# unreachable remote, since the note stays here and `wfctl store reviews`
# sends it later.
NETWORK_TIMEOUT = 60
# `gh` reaches GitHub's API, and a rerun that hangs would hold up a review
# command whose own work is already done.
_GH_TIMEOUT = 30

_JOB_LINK = re.compile(r"/actions/runs/(\d+)/job/(\d+)")


class NoOrigin(_review.ReviewError):
    def __init__(self) -> None:
        super().__init__("no origin remote to send review notes to")


def record(repo_root: Path, sha: str, line: str, timeout: float | None = None) -> bool:
    """Add `line` to the commit's note, unless the note already holds it.
    Returns whether it added the line.

    The note is read first because `git notes append` adds a copy every time,
    and `review check` on a run that's already complete records again
    (research R6). Reading only skips a duplicate and never merges anything,
    so wfctl still needs no merge of its own.

    `--no-separator` because `append` otherwise puts a blank line between
    entries, and the note is one line per event. It needs git 2.42 or later.
    """
    shown = _review.git(
        repo_root, "notes", f"--ref={NOTES_REF}", "show", sha, timeout=timeout, answers=(0, 1),
    )
    if shown.returncode == 0 and line in (x.strip() for x in shown.stdout.splitlines()):
        return False
    _review.git(
        repo_root, "notes", f"--ref={NOTES_REF}", "append", "--no-separator", "-m", line, sha,
        timeout=timeout,
    )
    return True


def has_origin(repo_root: Path, timeout: float | None = None) -> bool:
    """Whether the repository has an `origin` remote. `git remote get-url`
    exits 2 for a remote that isn't configured."""
    return _review.git(
        repo_root, "remote", "get-url", "origin", timeout=timeout, answers=(0, 2),
    ).returncode == 0


def _require_origin(repo_root: Path, timeout: float) -> None:
    if not has_origin(repo_root, timeout):
        raise NoOrigin()


def unsent(repo_root: Path, timeout: float = NETWORK_TIMEOUT) -> bool:
    """Whether this machine has review notes `origin` doesn't. False with no
    local notes ref, since there's nothing to send.

    Raises `NoOrigin` when there's no `origin`, and `ReviewError` when
    `origin` can't be reached.
    """
    _require_origin(repo_root, timeout)
    local = _review.git(
        repo_root, "rev-parse", "--verify", "--quiet", NOTES_REF,
        timeout=timeout, answers=(0, 1),
    ).stdout.strip()
    if not local:
        return False
    remote = _network(repo_root, ["ls-remote", "origin", NOTES_REF], timeout).stdout.split()
    return remote[:1] != [local]


def send(
    repo_root: Path, agent_dir: Path, branch: str, timeout: float = NETWORK_TIMEOUT,
) -> str:
    """Push the notes ref to `origin`, and record the push as the outward
    action `store-reviews`. Returns `"sent"`, or `"joined"` when `origin`
    rejected the first push and its notes were joined with these.

    A push is rejected when another machine sent notes first. `send` then
    fetches `origin`'s ref beside this one, joins the two with git's
    `cat_sort_uniq`, which keeps every distinct line from both, and pushes
    once more (research R7). One retry is enough for one user, and a second
    rejection raises with git's message.

    Raises `NoOrigin` when there's no `origin`, and `ReviewError` holding
    git's message when the push fails.
    """
    from wfctl._session import record_outward_action

    _require_origin(repo_root, timeout)
    push = ["push", "origin", f"{NOTES_REF}:{NOTES_REF}"]
    try:
        _network(repo_root, push, timeout)
        outcome = "sent"
    except _review.ReviewError as e:
        if "rejected" not in str(e):
            raise
        _join(repo_root, timeout)
        _network(repo_root, push, timeout)
        outcome = "joined"
    record_outward_action(agent_dir, branch, "store-reviews")
    return outcome


_REMOTE_REF = f"{NOTES_REF}-remote"


def _join(repo_root: Path, timeout: float) -> None:
    """Merge `origin`'s notes into this machine's, through a temporary ref
    that is deleted afterwards. Nothing to join when `origin` has none, such
    as when a hook refused the first push."""
    has = _network(repo_root, ["ls-remote", "origin", NOTES_REF], timeout).stdout.strip()
    if not has:
        return
    _network(repo_root, ["fetch", "origin", f"+{NOTES_REF}:{_REMOTE_REF}"], timeout)
    try:
        _review.git(
            repo_root, "notes", f"--ref={NOTES_REF}", "merge", "-q", "-s", "cat_sort_uniq",
            _REMOTE_REF, timeout=timeout,
        )
    finally:
        _review.git(
            repo_root, "update-ref", "-d", _REMOTE_REF, timeout=timeout, answers=(0, 1),
        )


def _network(repo_root: Path, args: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    """A git call that reaches `origin`. A timeout reads the same as a
    refusal, since either way the notes stay here to send later."""
    try:
        r = subprocess.run(
            ["git", *args], cwd=repo_root, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise _review.ReviewError(f"git {args[0]} timed out after {timeout:g}s") from None
    if r.returncode != 0:
        raise _review.ReviewError(r.stderr.strip() or f"git {args[0]} exited {r.returncode}")
    return r


@dataclass(frozen=True)
class Rerun:
    """What `rerun` did. `pr` is the branch's open PR when it found one,
    `reran` whether it reran the failed job, and `error` is `gh`'s message
    when a call failed."""

    pr: int | None
    reran: bool
    error: str | None


def rerun(repo_root: Path, branch: str, timeout: float = _GH_TIMEOUT) -> Rerun:
    """Rerun the failed `review` job on the branch's open PR, so it reads the
    notes just pushed. Pushing a notes ref doesn't start a CI run.

    `gh pr checks` reports checks on the PR's head whichever event made them,
    which suits a `pull_request_target` job whose run may not name the PR's
    branch. The job is rerun by its id, so any other failed job is left alone
    (research R8).

    Without `gh`, or with an `origin` that isn't on GitHub, there's no check to
    rerun, so it does nothing and returns no error. Any other failure returns
    `gh`'s message and is never retried, since the user can rerun the check on
    the PR themselves.
    """
    nothing = Rerun(None, False, None)
    if shutil.which("gh") is None:
        return nothing
    url = _review.git(
        repo_root, "remote", "get-url", "origin", timeout=timeout, answers=(0, 2),
    ).stdout
    if "github.com" not in url:
        return nothing

    def gh(*args: str, answers: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
        try:
            r = subprocess.run(
                ["gh", *args], cwd=repo_root, capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            raise _review.ReviewError(f"gh {args[0]} {args[1]} timed out after {timeout:g}s")
        if r.returncode not in answers:
            raise _review.ReviewError(r.stderr.strip() or f"gh exited {r.returncode}")
        return r

    pr: int | None = None
    try:
        viewed = gh("pr", "view", branch, "--json", "number,state", answers=(0, 1))
        if viewed.returncode == 1:
            if "no pull requests found" in viewed.stderr:
                return nothing
            raise _review.ReviewError(viewed.stderr.strip() or "gh exited 1")
        found = json.loads(viewed.stdout)
        if found.get("state") != "OPEN":
            return nothing
        pr = int(found["number"])
        # `gh pr checks` exits 1 when a check failed and 8 when one is
        # pending, and prints the JSON either way.
        listed = gh("pr", "checks", str(pr), "--json", "name,state,link", answers=(0, 1, 8))
        check = next(
            (c for c in json.loads(listed.stdout or "[]") if c.get("name") == "review"), None,
        )
        if check is None or check.get("state") != "FAILURE":
            return Rerun(pr, False, None)
        ids = _JOB_LINK.search(str(check.get("link", "")))
        if ids is None:
            raise _review.ReviewError(f"can't read the job from {check.get('link')!r}")
        gh("run", "rerun", ids.group(1), "--job", ids.group(2))
    except (_review.ReviewError, ValueError, KeyError, TypeError) as e:
        return Rerun(pr, False, str(e))
    return Rerun(pr, True, None)


# --- approving imports ---------------------------------------------------------------
#
# The import check fails a branch that adds a baseline line, a map arrow, a
# shared package, a context-to-package pair, or a change to a file CI runs the
# check with, until a person approves it (`contexts-are-packages`, FR-015). The
# approval is a note line carrying a digest of the additions, and only the
# default branch's copy of the check computes that digest, since a branch's
# copy is code an agent may have edited to list fewer additions.
#
# These refusals stop an agent taking a shortcut. They don't stop one set on
# getting around them, for example by calling `approve_imports` from its own
# Python, which is the protection the person-only review command gives today.
# CI's comparison is the enforcement.

IMPORTS_APPROVED_PREFIX = "imports approved "
_CHECK = ".github/scripts/check_imports.py"
_TERMINAL_REFUSAL = "wfctl arch approve-imports needs a person at an interactive terminal"


def _at_terminal() -> bool:
    import sys

    return sys.stdin.isatty() and sys.stdout.isatty()


def _wfctl_source() -> Path:
    import wfctl

    return Path(wfctl.__file__).resolve().parent


@dataclass(frozen=True)
class Approval:
    """What `approve_imports` did. `sent` is git's message when the push to
    `origin` failed, and None when it succeeded."""

    head: str
    sent: str | None
    rerun: Rerun


def approve_imports(repo_root: Path, digest: str) -> Approval:
    """Write `imports approved <digest>` on HEAD's note, send the notes to
    `origin`, and rerun the PR's failed `review` job, since pushing a notes ref
    starts no CI run and the approval check runs in that job.

    It repeats the command's terminal check, so an agent calling this from a
    one-line script with no terminal is refused too.
    """
    from wfctl._paths import resolve_agent_dir, resolve_branch

    if not _at_terminal():
        raise _review.ReviewError(_TERMINAL_REFUSAL)
    head = _review.head_commit(repo_root)
    record(repo_root, head, f"{IMPORTS_APPROVED_PREFIX}{digest}")
    branch = resolve_branch(repo_root)
    try:
        send(repo_root, resolve_agent_dir(repo_root, branch), branch)
    except _review.ReviewError as e:
        return Approval(head, str(e) or type(e).__name__, Rerun(None, False, None))
    return Approval(head, None, rerun(repo_root, branch))


def _run(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True,
        timeout=NETWORK_TIMEOUT,
    )


def _inside_a_worktree(repo_root: Path) -> bool:
    listed = _run(repo_root, "worktree", "list", "--porcelain")
    source = _wfctl_source().resolve()
    for line in listed.stdout.splitlines():
        if line.startswith("worktree "):
            if source.is_relative_to(Path(line.removeprefix("worktree ")).resolve()):
                return True
    return False


def _branch_matches_origin(repo_root: Path) -> str | None:
    """None when HEAD is the commit `origin/<branch>` names, after fetching
    it. Otherwise the refusal to print. The approval has to land on the commit
    CI checks, or the check stays red with nothing on screen saying why.

    It compares against the branch of the same name rather than the
    configured upstream, since a branch created from `origin/main` often
    tracks `origin/main`.
    """
    named = _run(repo_root, "symbolic-ref", "--short", "-q", "HEAD")
    if named.returncode != 0:
        return "✗ HEAD is detached, so there's no branch to compare. First check out the PR's branch."
    branch = named.stdout.strip()
    remote = f"origin/{branch}"
    found = _run(repo_root, "ls-remote", "--exit-code", "origin", f"refs/heads/{branch}")
    if found.returncode == 2:
        return f"✗ origin has no {remote}. Run `git push` first, then approve."
    if found.returncode != 0:
        return f"✗ can't reach origin to fetch {remote}: {found.stderr.strip()}"
    fetched = _run(repo_root, "fetch", "-q", "origin",
                   f"+refs/heads/{branch}:refs/remotes/{remote}")
    if fetched.returncode != 0:
        return f"✗ git fetch {remote} failed: {fetched.stderr.strip()}"
    head = _run(repo_root, "rev-parse", "HEAD").stdout.strip()
    there = _run(repo_root, "rev-parse", remote).stdout.strip()
    if head == there:
        return None
    if _run(repo_root, "merge-base", "--is-ancestor", there, head).returncode == 0:
        return f"✗ HEAD is ahead of {remote}. Run `git push` first, so CI checks the commit you approve."
    if _run(repo_root, "merge-base", "--is-ancestor", head, there).returncode == 0:
        return f"✗ HEAD is behind {remote}. Run `git pull` first, so you approve the commit CI checks."
    return f"✗ HEAD and {remote} have diverged. Use `git push` or `git pull` until they match."


def _shown(text: str) -> str:
    """`text` with every non-printing character written as an escape. The
    branch writes the diff and the addition lines this command prints, and a
    carriage return or a cursor code in them could redraw the screen over the
    change the person is approving."""
    return "".join(
        c if c in "\n\t" or c.isprintable() else repr(c)[1:-1] for c in text
    )


def run_approve_imports(repo_root: Path) -> int:
    """List a branch's additions with the default branch's copy of the import
    check, and approve them once the person types the digest back. Returns
    the exit code, and prints every line it says."""
    import sys
    import tempfile

    if not _at_terminal():
        print(f"✗ {_TERMINAL_REFUSAL}")
        return 1
    if _inside_a_worktree(repo_root):
        print(
            "✗ this wfctl runs from a worktree of this repository, so it's the branch's own "
            "code, which an agent may have edited. Run the installed wfctl, not `uv run wfctl`."
        )
        return 1
    refused = _branch_matches_origin(repo_root)
    if refused:
        print(refused)
        return 1
    default = _run(repo_root, "symbolic-ref", "--short", "-q", "refs/remotes/origin/HEAD")
    if default.returncode != 0:
        print(
            "✗ origin/HEAD isn't set, so there's no default branch to compare against. "
            "Run `git remote set-head origin --auto`."
        )
        return 1
    trunk = default.stdout.strip()
    name = trunk.removeprefix("origin/")
    fetched = _run(repo_root, "fetch", "-q", "origin", f"+refs/heads/{name}:refs/remotes/{trunk}")
    if fetched.returncode != 0:
        print(f"✗ git fetch {trunk} failed: {fetched.stderr.strip()}")
        return 1
    script = _run(repo_root, "show", f"{trunk}:{_CHECK}")
    if script.returncode != 0:
        print(
            f"✗ {trunk} has no {_CHECK}, so there's nothing on the trunk to check additions "
            "against. The first baseline is approved by merging its PR by hand."
        )
        return 1
    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / "check_imports.py"
        copy.write_text(script.stdout)
        listed = subprocess.run(
            [sys.executable, "-I", str(copy), "--approvals", "--base", trunk, "--json"],
            cwd=repo_root, capture_output=True, text=True,
        )
    if listed.returncode != 0:
        print(_shown(listed.stdout.strip() or listed.stderr.strip()))
        return 1
    found = json.loads(listed.stdout)
    merge_base, additions, digest = found["merge_base"], found["additions"], found["digest"]
    print(f"merge base {merge_base[:12]}")
    if not additions:
        print("✓ this branch adds nothing that needs approving")
        return 0
    for line in additions:
        print(f"    {_shown(line)}")
        if line.startswith("changed "):
            path = line.split()[1]
            # Bytes, since text mode turns a lone carriage return into a
            # newline, and the person should see the file as the branch wrote it.
            # `--text` because the branch's own `.gitattributes`, which needs no
            # approval, could mark the file binary and hide every line.
            # A failed diff prints nothing, and the prompt below is the only
            # point where the person decides. So a failure stops here rather
            # than warning above a prompt they might answer out of habit.
            failed: str | None
            try:
                diff = subprocess.run(
                    ["git", "diff", "--text", "--no-ext-diff", "--no-textconv", merge_base,
                     "HEAD", "--", path],
                    cwd=repo_root, capture_output=True, timeout=NETWORK_TIMEOUT,
                )
            except subprocess.TimeoutExpired:
                failed = f"timed out after {NETWORK_TIMEOUT}s"
            else:
                failed = (None if diff.returncode == 0 else
                          f"failed: {diff.stderr.decode('utf-8', 'replace').strip()}")
            if failed is not None:
                print(f"✗ git diff of {_shown(path)} {_shown(failed)}")
                print("  Nothing written, since you couldn't read the change.")
                return 1
            print(_shown(diff.stdout.decode("utf-8", "replace").rstrip()))
    code = digest[:12]
    try:
        typed = input(f"Type {code} to approve these additions: ")
    except EOFError:
        typed = ""
    if typed.strip() != code:
        print("✗ not approved; nothing written")
        return 1
    try:
        done = approve_imports(repo_root, digest)
    except _review.ReviewError as e:
        print(f"✗ {e}")
        return 1
    print(f"✓ approved {len(additions)} addition{'s' if len(additions) != 1 else ''} "
          f"at {done.head[:7]}")
    if done.sent is not None:
        print(f"⚠ couldn't send review notes: {' '.join(done.sent.split())}")
        print("  The note is saved here. Run `wfctl store reviews` to send it.")
    else:
        print("✓ sent review notes to origin")
        if done.rerun.reran:
            print("↻ reran the failed review check")
        elif done.rerun.error is not None:
            print(f"⚠ couldn't rerun the review check: {' '.join(done.rerun.error.split())}")
    return 0
