"""The spec store: which kind of folder the spec root is, and what in it is not
stored yet.

A spec store is a git checkout holding every branch's spec dir, one folder per
branch, on a branch of its own such as `specs-trunk`. A spec dir is stored when
nothing under it is uncommitted and every commit touching it is on the
upstream. The readers here and the store that writes are kept in one module so
the definition of "stored" the store aims for and the one the readers check
cannot drift apart.

Standard library only at module scope. The worktree guard imports this module
for `owns_branch`, and the guard runs before every Bash call an agent makes, so
an import here of `typer`, `rich` or `wfctl.cli` would put back the 47 ms that
`_hook.py` exists to avoid.
"""

from __future__ import annotations

import fcntl
import os
import subprocess
import time
from collections.abc import Callable, Collection, Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal, NamedTuple


def _quiet_env(ssh_command: str | None = None) -> dict[str, str]:
    """The environment every git call here runs with, so that none of them
    can wait on a person.

    The store runs from a removal hook and from an unattended pass, and in
    both nobody is at the terminal. Without `GIT_TERMINAL_PROMPT=0` a missing
    credential makes git ask for a password, and without `BatchMode` ssh asks
    whether to trust a new host key, and either way the hook hangs with no
    output (research R7).

    `BatchMode` is added to the ssh command git would have used anyway rather
    than replacing it. `GIT_SSH_COMMAND` takes precedence over
    `core.sshCommand`, so setting it to a plain `ssh` would drop the identity
    file or agent a person configured in either place, and the push would
    fail for a reason that has nothing to do with the store. The store passes
    `core.sshCommand` in, read from the spec store, and the reads pass
    nothing, since they never reach a remote.

    `GIT_OPTIONAL_LOCKS=0` stops `git status` from rewriting the index. By
    default it refreshes the index under `index.lock`, and the pass runs it
    on every `wfctl status` from any worktree past `implement`. When a store's
    `git add` or `git commit` runs at the same moment, git refuses it because
    the lock file exists, and the store fails for no real reason. `_lock`
    does not help here, because it keeps two stores apart and not a store and
    a reader. The setting only drops locks git can do without, so the store's
    own writes still take theirs.
    """
    base = os.environ.get("GIT_SSH_COMMAND") or ssh_command or "ssh"
    return {
        **os.environ,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_SSH_COMMAND": f"{base} -o BatchMode=yes",
    }


def _read(cwd: str, *args: str) -> str | None:
    """What `git -C cwd <args>` prints, stripped, or None when git cannot answer."""
    try:
        out = subprocess.run(
            ["git", "-C", cwd, *args], capture_output=True, text=True, check=True,
            env=_quiet_env(),
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip()


def _common_dir(cwd: str) -> str | None:
    found = _read(cwd, "rev-parse", "--git-common-dir")
    return os.path.realpath(os.path.join(cwd, found)) if found else None


def top_level(path: str) -> str | None:
    """The top of the checkout git finds from `path`, resolved, or None.

    A folder inside a spec store passes `owns_branch` and is still not a store
    of its own, because a commit from there takes in the whole checkout. Both
    the guard and `layout` compare this against the root to tell the two apart.
    """
    top = _read(path, "rev-parse", "--show-toplevel")
    return os.path.realpath(top) if top else None


def owns_branch(root: str, here: str) -> bool:
    """Whether a commit in `root` lands on a branch of its own rather than on
    the code's.

    Asked of git rather than read from the path, because git picks the
    repository from files inside the root. `root` qualifies when it belongs to
    another repository than `here`, or when it has a branch checked out that no
    other worktree of `here`'s project has. A plain `<main>/specs` fails, since
    git there finds the main checkout and its branch, and so does a store whose
    `.git` was replaced to point at the main checkout's.

    False whenever git cannot answer, for `root` or for `here`. The worktree
    guard reads this before it lets an agent commit, and the store reads it
    before it commits on its own, so an unanswered question has to come out as
    "not a store" for both.

    This does not check that `root` is the top of its checkout. `top_level`
    is that check, and both callers make it separately.
    """
    ours = _common_dir(here)
    theirs = _common_dir(root)
    if ours is None or theirs is None:
        return False
    if theirs != ours:
        return True
    branch = _read(root, "symbolic-ref", "-q", "HEAD")
    if not branch:
        return False
    # Each porcelain block names one worktree and, unless it is detached, the
    # branch it has checked out.
    real = os.path.realpath(root)
    taken: set[str] = set()
    for block in (_read(here, "worktree", "list", "--porcelain") or "").split("\n\n"):
        fields = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        if "worktree" in fields and "branch" in fields:
            if os.path.realpath(fields["worktree"]) != real:
                taken.add(fields["branch"])
    return branch not in taken


LayoutKind = Literal["store", "store_no_upstream", "detached", "in_repo", "unmanaged"]


class Layout(NamedTuple):
    """Which kind of folder a spec root is, and for a `store` where it pushes.

    `remote` and `upstream` are set only for `store`: the remote's name, such
    as `origin`, and the upstream ref as the output prints it, such as
    `origin/specs-trunk`.
    """

    kind: LayoutKind
    root: str
    remote: str | None = None
    upstream: str | None = None


def layout(spec_root: str | os.PathLike[str], repo_root: str | os.PathLike[str]) -> Layout:
    """The kind of folder `spec_root` is, asked of git on every call.

    1. `store` and `store_no_upstream`: the root is the top of its own
       checkout, and `owns_branch` passes, so a commit there lands on a branch
       of the store's own. The two differ only in whether that branch has an
       upstream to push to.
    2. `in_repo`: git, run in the root, finds the code repository, and the
       first kind did not hold. The default `<repo>/specs` is this, and so is
       a worktree of the code repository with a branch some other worktree
       already has checked out.
    3. `detached`: the root is the top of its own checkout and has no branch
       checked out, as during an interrupted rebase or after
       `git checkout <sha>`. It is a spec store in a broken state rather than
       a layout anyone chose, so the store fails there and the pass holds.
       A commit there would sit on no branch, so nothing would push it and
       the next checkout would leave it reachable only from the reflog.
    4. `unmanaged`: anything else. A plain folder, a folder that does not
       exist yet, and a folder nested inside some other repository, where a
       commit would land on that repository's branch.

    The top-of-checkout test is separate from `owns_branch` because a folder
    one level inside a spec store passes `owns_branch` and is still not a
    store: a commit from there takes in the whole store, not this root.

    Raises when git fails for any reason other than the root being in no
    repository, such as git missing from PATH or a `safe.directory` refusal.
    Read as `unmanaged`, those let the pass read `skipped`, and an unattended
    run then finished `implement` with nothing stored.
    """
    root = os.fspath(spec_root)
    repo = os.fspath(repo_root)
    top = _checkout_top(root) if os.path.isdir(root) else None
    if top is None:
        return Layout("unmanaged", root)
    branch = _local_branch(root)
    if not branch and top == os.path.realpath(root):
        return Layout("detached", root)
    if branch and top == os.path.realpath(root) and owns_branch(root, repo):
        upstream = _read(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        remote = _read(root, "config", "--get", f"branch.{branch}.remote")
        if upstream and remote:
            return Layout("store", root, remote, upstream)
        return Layout("store_no_upstream", root)
    theirs = _common_dir(root)
    if theirs is not None and theirs == _common_dir(repo):
        return Layout("in_repo", root)
    return Layout("unmanaged", root)


def _checkout_top(path: str) -> str | None:
    """The top of the checkout git finds from `path`, resolved, or None when
    `path` is in no repository. Raises on every other failure.

    `top_level` answers None for both, which suits the guard, and `layout`
    has to tell them apart. Git's message is read in the C locale, since a
    translated one would turn every plain folder into a failure.
    """
    proc = subprocess.run(
        ["git", "-C", path, "rev-parse", "--show-toplevel"], capture_output=True, text=True,
        env={**_quiet_env(), "LC_ALL": "C"},
    )
    if proc.returncode == 0:
        return os.path.realpath(proc.stdout.strip())
    if "not a git repository" in proc.stderr:
        return None
    raise subprocess.CalledProcessError(proc.returncode, proc.args, proc.stdout, proc.stderr)


# What the store, the pass and `check specs` say about a `detached` spec store.
DETACHED = "the spec store has no branch checked out"


class Unstored(NamedTuple):
    """One spec dir that is not stored: its folder name under the store's
    root, how many files under it are uncommitted, untracked ones included,
    and whether a commit touching it is missing from the upstream."""

    name: str
    uncommitted: int
    unpushed: bool


def unstored(
    root: str | os.PathLike[str], paths: Iterable[str | os.PathLike[str]],
) -> list[Unstored]:
    """The spec dirs under `paths` that are not stored, sorted by name.

    `root` is a store's root, which `layout` has checked is the top of its
    checkout, so every path git prints is relative to it and its first
    component is the spec dir. `paths` are pathspecs: one spec dir for the
    pass and the store, or the whole root for `check specs`, which then costs
    two git calls whatever the number of spec dirs.

    The two reads touch no network. `@{u}` is git's local copy of the remote
    branch, which a push from here updates. Both run with `-z`, since without
    it git quotes a path holding a space or a non-ASCII character, and the
    quote would end up in the spec dir's name.

    A rename counts once in each folder it touches, because a commit of either
    folder alone takes in only that folder's half.

    Without an upstream there is nothing to compare commits against, so no
    spec dir reads as unpushed, and only uncommitted files are reported. A
    pushed state that no command could ever reach would leave `check specs`
    failing for good in a `store_no_upstream` layout. A failing `git status`
    raises instead, because the one answer this must never give for a broken
    checkout is an empty list, which reads as everything stored.
    """
    top = os.fspath(root)
    specs = [os.fspath(p) for p in paths]
    status = subprocess.run(
        ["git", "-C", top, "status", "--porcelain", "-z", "--untracked-files=all", "--", *specs],
        capture_output=True, text=True, check=True, env=_quiet_env(),
    ).stdout
    counts: dict[str, int] = {}
    fields = iter(status.split("\0"))
    for entry in fields:
        if not entry:
            continue
        touched = {_folder(entry[3:])}
        if "R" in entry[:2] or "C" in entry[:2]:
            touched.add(_folder(next(fields, "")))
        for name in touched - {""}:
            counts[name] = counts.get(name, 0) + 1
    log = _read(top, "log", "-z", "--format=", "--name-only", "@{u}..HEAD", "--", *specs)
    unpushed = {_folder(p) for p in (log or "").split("\0") if p}
    return [
        Unstored(name, counts.get(name, 0), name in unpushed)
        for name in sorted(counts.keys() | unpushed)
    ]


def _folder(path: str) -> str:
    return path.split("/", 1)[0]


def _count(n: int, noun: str) -> str:
    """`1 file`, `2 files`. Every count the store, the pass and `check specs`
    print goes through here, so a store of one file never reads "1 files"."""
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def describe(spec_dir: Unstored) -> str:
    """The text one unstored spec dir renders as, shared by the pass, `check
    specs`, and removal.

    The uncommitted count wins when both hold, because committing is the next
    thing that has to happen, and the push carries the older commit with it.
    """
    if spec_dir.uncommitted:
        return f"uncommitted: {_count(spec_dir.uncommitted, 'file')}"
    return "committed, not pushed"


def _check_remote(url: str) -> None:
    """Called with a remote's URL before the store fetches from it or pushes to
    it. It does nothing here.

    The store is the first code path in wfctl that can push. A test that
    forgets to set `WFCTL_SPEC_DIR` resolves the developer's real spec store,
    and its store would push a fixture's commits to the real remote.
    `tests/conftest.py` replaces this function in every test with one that
    refuses a URL outside the test's own `tmp_path`, and it can only do that if
    the store asks first. So every fetch and push asks, with the URL git will
    use for it: `git remote get-url` before a fetch, and `git remote get-url
    --push` before a push, since a remote can push somewhere other than where
    it fetches from.
    """


Outcome = Literal[
    "stored", "already_stored", "not_applicable", "no_spec_dir",
    "committed_not_backed_up", "not_pushed", "push_refused", "conflict",
    "merge_blocked_staged", "merge_refused", "merge_in_progress", "locked",
    "git_failed",
]

# The outcomes `store specs` exits 1 for. Every other one either stored the
# spec dir or met a layout with nowhere to push, and says where the files are
# (research R6). The pass reads `in_progress` in each of these, so an exit of 0
# would tell a script the store worked when the pipeline says it did not.
_FAILED: frozenset[Outcome] = frozenset({
    "not_pushed", "push_refused", "conflict", "merge_blocked_staged",
    "merge_refused", "merge_in_progress", "locked", "git_failed",
})


class StoreResult(NamedTuple):
    """What one run of the store ended with (`data-model.md §Store result`).

    `files` are the files the push carries, relative to the spec dir: every
    file under it that differs from the upstream, which takes in an earlier
    commit of this branch's that never reached the remote (research R9).
    `folders` names the spec dirs a merge stopped on. `message` is git's own
    text, kept for `git_failed` because no summary of an unknown failure is
    more useful than what git said.

    `paths` are the files a refused merge named, relative to the store's
    root, and `untracked` says they are new files in the way rather than
    edited ones, since the two need different remedies (PR-015).
    `store_branch` is the spec store's own branch, which a layout with no
    upstream names in place of the upstream it lacks.

    `inside_worktree` is kept rather than `stops_removal` itself, so the rule
    lives in one place and the removal command cannot apply a second one.
    """

    outcome: Outcome
    branch: str
    spec_dir: str
    inside_worktree: bool
    layout: Layout | None = None
    files: tuple[str, ...] = ()
    sha: str | None = None
    message: str | None = None
    folders: tuple[str, ...] = ()
    paths: tuple[str, ...] = ()
    untracked: bool = False
    store_branch: str | None = None

    @property
    def exit_code(self) -> int:
        return 1 if self.outcome in _FAILED else 0

    @property
    def stops_removal(self) -> bool:
        """Whether removing the worktree would delete the only copy.

        Removal reads this and never the exit code (research R6). A spec dir
        outside the worktree survives the removal whatever the store did, so
        a failed push there is a warning. One inside it, which nothing copied
        out, goes with the worktree, and that includes `not_applicable`: an
        outcome-only rule would let removal delete it without an error. With
        no spec dir there is nothing to lose.
        """
        return self.inside_worktree and self.outcome != "no_spec_dir"


# Fetch and push are the two calls that reach the network. A timeout reads the
# same as an unreachable remote, since both leave the commit local and the next
# store sends it (research R7).
_NETWORK_TIMEOUT = 60

# How long a store waits for another one to finish, and how often it asks
# (FR-027, research R5).
_LOCK_TIMEOUT = 10.0
_LOCK_POLL = 0.2

# What git and ssh print when they could not reach the remote at all. Checked
# after `_REFUSED_ACCESS`, because ssh ends an authentication failure with the
# same "Could not read from remote repository" it prints for a dead host, and
# "unreachable" would send a person to check a network that is fine (PR-010).
# A local path that is gone reads as unreachable too, since a spec store's
# remote can sit on a drive that is not mounted.
_UNREACHABLE = (
    "Could not resolve host", "Connection refused", "Connection timed out",
    "Operation timed out", "Network is unreachable", "No route to host",
    "Connection reset", "Connection closed", "Failed to connect",
    "does not appear to be a git repository",
)
_REFUSED_ACCESS = (
    "Permission denied", "Authentication failed", "could not read Username",
    "could not read Password", "terminal prompts disabled",
    "Host key verification failed", "returned error: 401", "returned error: 403",
)


class _Git:
    """Git run in one spec store, with no prompt and with failures returned.

    `subprocess.run` is looked up on every call rather than bound once, so a
    test can stand in for one call, such as moving the remote just before
    the push, without the store knowing.
    """

    def __init__(self, root: str) -> None:
        self.root = root
        self.env = _quiet_env(_read(root, "config", "--get", "core.sshCommand"))

    def __call__(
        self, *args: str, timeout: float | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", self.root, *args], capture_output=True, text=True,
            env=self.env, timeout=timeout,
        )


def store(
    spec_dir: str | os.PathLike[str], branch: str, repo_root: str | os.PathLike[str],
    *, lock_timeout: float = _LOCK_TIMEOUT,
) -> StoreResult:
    """Commit this branch's spec dir in its spec store, merge the upstream,
    and push.

    The spec root is the spec dir's parent, which is where `resolve_spec_dir`
    looks for it, and the layout is read from that root on every call. A
    `store` layout is committed in and pushed from, and `store_no_upstream`
    is committed in and stops there. A `detached` store fails with
    `git_failed`, since a commit there would land on no branch and a person
    has to check one out first. Every other layout returns `not_applicable`,
    since a commit there would land on the code's branch or in a folder git
    does not track.

    The steps, in order (research R8, R9):

    1. `git add -A -- <dir>` and `git commit -- <dir>`. The pathspec on the
       commit is what leaves another branch's staged files out of this commit
       and still staged (FR-001).
    2. Fetch the upstream branch alone, then `git merge --no-edit @{u}`. A
       rebase refuses to run while any tracked file is edited, and in a shared
       checkout another branch almost always has one
       (`store-specs-merges-before-push.md`).
    3. Push to the upstream branch by its configured name. Never forced, since
       a forced push on this branch can only delete another branch's specs.

    The upstream branch is read from git config and never named here, so the
    store pushes wherever the spec store tracks.

    All three steps run under `_lock`, so a second store waits for this one
    instead of committing between its merge and its push (FR-027).
    `lock_timeout` is there for the tests, which would otherwise wait the
    full 10 seconds to see a store give up.
    """
    path = os.fspath(spec_dir)
    inside = Path(path).resolve().is_relative_to(Path(os.fspath(repo_root)).resolve())
    if not os.path.isdir(path):
        return StoreResult("no_spec_dir", branch, path, inside)
    try:
        found = layout(os.path.dirname(os.path.abspath(path)), repo_root)
    except (OSError, subprocess.CalledProcessError) as e:
        return StoreResult("git_failed", branch, path, inside, message=_error_text(e))
    if found.kind == "detached":
        return StoreResult(
            "git_failed", branch, path, inside, found,
            message=f"{DETACHED}\ncheck out its branch in {found.root}, then run"
            " `wfctl store specs` again",
        )
    if found.kind not in ("store", "store_no_upstream"):
        return StoreResult("not_applicable", branch, path, inside, found)
    try:
        git_dir = _read(found.root, "rev-parse", "--git-dir")
        if not git_dir:
            return StoreResult(
                "git_failed", branch, path, inside, found,
                message="git could not name the spec store's git directory",
            )
        # `--git-dir` prints `.git` relative to the root in a clone of its
        # own, and an absolute path in a worktree. The join handles both.
        with _lock(os.path.join(found.root, git_dir), lock_timeout) as held:
            if not held:
                return StoreResult("locked", branch, path, inside, found)
            return _store(path, branch, repo_root, found, inside)
    except (OSError, subprocess.CalledProcessError) as e:
        return StoreResult("git_failed", branch, path, inside, found, message=_error_text(e))


def _error_text(e: OSError | subprocess.CalledProcessError) -> str:
    said = e.stderr if isinstance(e, subprocess.CalledProcessError) else None
    return (said or str(e)).strip()


@contextmanager
def _lock(git_dir: str, timeout: float = _LOCK_TIMEOUT) -> Iterator[bool]:
    """Hold `wfctl-store.lock` in the spec store's git directory, or give up
    after `timeout` seconds. Yields whether the lock is held.

    `fcntl.flock` rather than a file created with `O_EXCL`, because the OS
    drops a flock when the process exits, a killed removal hook included, so
    no dead store leaves behind a lock a person has to delete (research R5).
    The file sits in the git directory so it never shows up as untracked in
    the store, and in a worktree that directory is the worktree's own, which
    is where the index two stores would fight over lives.

    The file is left in place afterwards. Removing it would race a second
    store that has already opened it and is waiting on the lock: that store
    would then hold a lock on a file nobody else can find.
    """
    fd = os.open(os.path.join(git_dir, "wfctl-store.lock"), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        yield _acquire(fd, timeout)
    finally:
        # Closing the descriptor is what releases the lock.
        os.close(fd)


def _acquire(fd: int, timeout: float) -> bool:
    """Non-blocking attempts every `_LOCK_POLL` seconds, rather than one
    blocking call, because a blocking `flock` takes no timeout and a removal
    hook must not hang on a store that never finishes."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(_LOCK_POLL)


def _store(path: str, branch: str, repo_root: str | os.PathLike[str],
           found: Layout, inside: bool) -> StoreResult:
    git = _Git(found.root)
    name = os.path.basename(os.path.normpath(path))
    # With no upstream the store commits and stops there, since choosing a
    # remote to push to is the person's decision and not the store's (FR-012).
    # Every comparison that would be made with `@{u}` is made with `HEAD`.
    upstream = found.kind == "store"

    def result(
        outcome: Outcome, files: tuple[str, ...] = (),
        sha: str | None = None, message: str | None = None,
        folders: tuple[str, ...] = (), paths: tuple[str, ...] = (), untracked: bool = False,
    ) -> StoreResult:
        return StoreResult(
            outcome, branch, path, inside, found, files, sha, message, folders, paths, untracked,
            None if upstream else _local_branch(found.root),
        )

    def failed(proc: subprocess.CompletedProcess[str]) -> StoreResult:
        return result("git_failed", message=_said(proc))

    if not unstored(found.root, [name]):
        return result("already_stored" if upstream else "committed_not_backed_up")

    # A merge some earlier run left unfinished, whether a store killed partway
    # or a person resolving a conflict by hand. `git commit -- <dir>` refuses
    # to run during a merge with a message that names neither cause. It is
    # reported rather than aborted, because aborting would throw away a
    # resolution a person may be halfway through (PR-011).
    if _merging(git):
        return result("merge_in_progress")

    added = git("add", "-A", "--", name)
    if added.returncode:
        return failed(added)
    # `--no-renames` because a rename would print only its new name, and the
    # file it replaced is one the push deletes from the remote.
    against = ["@{u}"] if upstream else []
    listed = git("diff", "--cached", "--name-only", "--no-renames", "-z", *against, "--", name)
    if listed.returncode:
        return failed(listed)
    files = tuple(p.split("/", 1)[1] for p in listed.stdout.split("\0") if "/" in p)

    if git("diff", "--cached", "--quiet", "--", name).returncode:
        committed = git("commit", "-m", _subject(branch, repo_root, files, name), "--", name)
        if committed.returncode:
            return failed(committed)
    if not upstream:
        return result("committed_not_backed_up", files)

    assert found.remote is not None
    merge_ref = _read(found.root, "config", "--get", f"branch.{_local_branch(found.root)}.merge")
    if not merge_ref:
        return result("git_failed", files, message="the spec store's branch names no upstream")

    _check_remote(_remote_url(git, found.remote))
    try:
        fetched = git("fetch", found.remote, merge_ref, timeout=_NETWORK_TIMEOUT)
    except subprocess.TimeoutExpired:
        return result("not_pushed", files)
    if fetched.returncode:
        return _network_failure(result, files, fetched)

    # The flags are spelled out because a merge takes its defaults from the
    # spec store's git config. With `merge.autoStash` set, git stashes another
    # branch's edits and pops them back as conflict markers, and the store
    # still reports success. With `merge.ff=only`, every store fails once the
    # two branches have diverged.
    merged = git("merge", "--no-edit", "--no-autostash", "--ff", "@{u}")
    if merged.returncode:
        return _merge_failure(git, result, files, merged)

    _check_remote(_remote_url(git, found.remote, "--push"))
    try:
        pushed = git("push", found.remote, f"HEAD:{merge_ref}", timeout=_NETWORK_TIMEOUT)
    except subprocess.TimeoutExpired:
        return result("not_pushed", files)
    if pushed.returncode:
        # `[rejected]` is git's mark for a push the remote turned away as not
        # a fast-forward. `[remote rejected]` is a hook or a protected branch
        # saying no, which another run will not fix, so it is not this case.
        if "[rejected]" in pushed.stderr:
            return result("push_refused", files)
        return _network_failure(result, files, pushed)

    sha = _read(found.root, "rev-parse", "--short", "HEAD")
    return result("stored", files, sha=sha)


def _merging(git: _Git) -> bool:
    return git("rev-parse", "-q", "--verify", "MERGE_HEAD").returncode == 0


def _said(proc: subprocess.CompletedProcess[str]) -> str:
    """What git printed about a failed call. Its error goes to stderr, but a
    few commands, such as `merge` stopping on a conflict, print the reason to
    stdout and leave stderr empty."""
    return (proc.stderr or proc.stdout).strip()


# The headers git prints over the files a merge refused to overwrite. Matched
# up to "would be", so the "removed by merge" form of each is read too.
_EDITED_HEADER = "Your local changes to the following files would be"
_UNTRACKED_HEADER = "The following untracked working tree files would be"


def _merge_failure(
    git: _Git, result: Callable[..., StoreResult], files: tuple[str, ...],
    merged: subprocess.CompletedProcess[str],
) -> StoreResult:
    """A merge that did not finish, told apart by kind in research R8's order.

    1. `MERGE_HEAD` exists, so the merge started and stopped on a conflict.
       The unmerged paths are read before `git merge --abort`, since after it
       the same command prints nothing.
    2. No `MERGE_HEAD`, and the index holds staged files. Git refuses any
       merge that is not a fast-forward while the index differs from `HEAD`,
       whether or not the upstream touches those files.
    3. Nothing staged, and git named files in the way, either edited or
       untracked.

    The `MERGE_HEAD` check comes first because a started merge stages what it
    merged. Reading the index first would call a conflict staged files, skip
    the abort, and leave the spec store mid-merge, which stops every branch's
    store until a person aborts it.

    Anything else is `git_failed` with git's own message.
    """
    said = _said(merged)
    if _merging(git):
        unmerged = git("diff", "--name-only", "--diff-filter=U", "-z")
        aborted = git("merge", "--abort")
        if aborted.returncode:
            return result("git_failed", files, message=_said(aborted))
        return result("conflict", files, folders=_folders(unmerged.stdout))
    staged = git("diff", "--cached", "--name-only", "-z")
    if staged.returncode:
        return result("git_failed", files, message=_said(staged))
    if staged.stdout.strip("\0"):
        return result("merge_blocked_staged", files, folders=_folders(staged.stdout))
    # An edit is reported ahead of an untracked file when git names both. The
    # next run reports the other, and one remedy per run keeps the output true.
    edited = _listed_under(said, _EDITED_HEADER)
    if edited:
        return result("merge_refused", files, paths=edited)
    untracked = _listed_under(said, _UNTRACKED_HEADER)
    if untracked:
        return result("merge_refused", files, paths=untracked, untracked=True)
    return result("git_failed", files, message=said)


def _folders(nul_separated: str) -> tuple[str, ...]:
    return tuple(sorted({_folder(p) for p in nul_separated.split("\0") if p}))


def _listed_under(said: str, header: str) -> tuple[str, ...]:
    """The tab-indented file names git prints under `header`."""
    lines = said.splitlines()
    for i, line in enumerate(lines):
        if header in line:
            names = []
            for entry in lines[i + 1:]:
                if not entry.startswith("\t"):
                    break
                names.append(entry.strip())
            return tuple(names)
    return ()


def _local_branch(root: str) -> str:
    return _read(root, "symbolic-ref", "-q", "--short", "HEAD") or ""


def _remote_url(git: _Git, remote: str, *push: str) -> str:
    """The URL a fetch or a push will use, for `_check_remote` to see first.

    Raises rather than returning an empty string, because a check handed
    nothing would have nothing to refuse, and the call after it would still
    reach whatever git resolves."""
    proc = git("remote", "get-url", *push, remote)
    if proc.returncode or not proc.stdout.strip():
        raise subprocess.CalledProcessError(proc.returncode or 1, proc.args, proc.stdout, proc.stderr)
    return proc.stdout.strip()


def _network_failure(
    result: Callable[..., StoreResult], files: tuple[str, ...],
    proc: subprocess.CompletedProcess[str],
) -> StoreResult:
    """A failed fetch or push, read as unreachable only when git said so."""
    said = _said(proc)
    if not any(mark in said for mark in _REFUSED_ACCESS) and any(
        mark in said for mark in _UNREACHABLE
    ):
        return result("not_pushed", files)
    return result("git_failed", files, message=said)


def _subject(branch: str, repo_root: str | os.PathLike[str],
             files: tuple[str, ...], name: str) -> str:
    """`specs(<issue>): store <first file> and N others` (FR-002).

    The issue key is read the way `wfctl` reads it everywhere else, so it
    matches the `specs(<issue>):` commits already on the spec branch. A
    branch with no key falls back to the branch name, which still says whose
    folder this is.
    """
    from wfctl._paths import extract_issue_key
    from wfctl._tracker import load_key_pattern

    key = extract_issue_key(branch, load_key_pattern(Path(os.fspath(repo_root))))
    if key == "unknown":
        key = branch
    if not files:
        return f"specs({key}): store {name}"
    rest = f" and {_count(len(files) - 1, 'other')}" if len(files) > 1 else ""
    return f"specs({key}): store {files[0]}{rest}"


# What `not_applicable` says for each layout the store does not commit in,
# after the spec dir's path. `store_no_upstream` is not here, since the store
# commits there and reports `committed_not_backed_up` instead.
_NOT_APPLICABLE: dict[LayoutKind, str] = {
    "in_repo": "is inside the code repository — not committed, not backed up",
    "unmanaged": "is not backed up anywhere",
}


def report_lines(result: StoreResult) -> list[str]:
    """What `store specs` prints for `result`, one string per line, as
    `contracts/cli.md` gives it.

    Plain text with no console markup, because removal prints the same lines
    as a warning and has to show exactly what `store specs` would. A line
    after the first that names files is indented four spaces, and so is the
    remedy line under it.
    """
    upstream = result.layout.upstream if result.layout else None
    count = len(result.files)
    names = [f"    {', '.join(result.files)}"] if result.files else []
    if result.outcome == "stored":
        return [f"✓ stored {_count(count, 'file')} → {upstream} ({result.sha})", *names]
    if result.outcome == "already_stored":
        return [f"✓ spec dir already stored on {upstream}"]
    if result.outcome == "no_spec_dir":
        return [f"ℹ no spec dir for {result.branch}"]
    if result.outcome == "not_applicable":
        kind = result.layout.kind if result.layout else "unmanaged"
        return [f"ℹ {result.spec_dir} {_NOT_APPLICABLE.get(kind, _NOT_APPLICABLE['unmanaged'])}"]
    if result.outcome == "committed_not_backed_up":
        # A run with nothing new says so, rather than "committed 0 files",
        # which reads as a commit that did not happen.
        done = f"committed {_count(count, 'file')}" if count else "nothing new to commit"
        return [f"⚠ {done}, not backed up — {result.store_branch} has no upstream branch"]
    if result.outcome == "not_pushed":
        return [
            f"⚠ committed {_count(count, 'file')}, not pushed — {upstream} is unreachable", *names,
            "    the next `wfctl store specs` with files to push sends it",
        ]
    if result.outcome == "push_refused":
        return [
            f"✗ committed {_count(count, 'file')}, push refused — {upstream} moved again", *names,
            "    run `wfctl store specs` again to merge and push",
        ]
    root = result.layout.root if result.layout else ""
    folders = ", ".join(f"{f}/" for f in result.folders)
    # A conflict and an unfinished merge both stop every branch's store, since
    # each store merges the same upstream into the same checkout. So each says
    # that, and names the git commands a person runs to clear it (PR-011).
    if result.outcome == "conflict":
        return [
            f"✗ committed {_count(count, 'file')}, merge conflicts in {folders}",
            "    the merge was aborted and your commit is kept",
            "    every branch's store fails until a person resolves this conflict",
            f"    to resolve it, run `git merge @{{u}}` in {root}, fix the files, run"
            " `git commit`, then `wfctl store specs`",
        ]
    if result.outcome == "merge_in_progress":
        return [
            f"✗ nothing committed, a merge is already in progress in {root}",
            "    every branch's store fails until that merge is finished or aborted",
            f"    to finish it, fix the files and run `git commit` in {root},"
            " or run `git merge --abort` there",
        ]
    if result.outcome == "merge_blocked_staged":
        return [
            f"✗ committed {_count(count, 'file')}, merge blocked by files staged in {folders}",
            "    run `wfctl store specs` from the branch that owns that folder, or unstage",
            "    the files, then run `wfctl store specs` again",
        ]
    if result.outcome == "merge_refused" and result.untracked:
        return [
            f"✗ committed {_count(count, 'file')}, merge blocked by untracked files the upstream"
            f" adds: {', '.join(result.paths)}",
            "    move those files aside, then run `wfctl store specs` again",
        ]
    if result.outcome == "merge_refused":
        return [
            f"✗ committed {_count(count, 'file')}, merge blocked by local edits to {', '.join(result.paths)}",
            "    store or discard that edit, then run `wfctl store specs` again",
        ]
    if result.outcome == "locked":
        return [f"✗ another store is running in {root}"]
    said = (result.message or "git gave no message").splitlines()
    rest = [f"    {line}" for line in said[1:] if line.strip()]
    return [f"✗ store failed: {said[0] if said else ''}", *rest]


# What `check specs` says a spec root is, for each layout with nowhere to push.
# It names the root rather than one spec dir, so it says what the root is and
# leaves out the "not backed up" that `_NOT_APPLICABLE` says about one folder.
_ROOT_LAYOUT: dict[LayoutKind, str] = {
    "store_no_upstream": "is in a spec store with no upstream branch",
    "in_repo": "is inside the code repository",
    "unmanaged": "is not in a spec store",
}


def check_lines(
    found: Layout, spec_dirs: list[Unstored], in_progress: Collection[str],
) -> list[str]:
    """What `check specs` prints, one string per line, as `contracts/cli.md`
    gives it.

    `spec_dirs` is every unstored spec dir under the root, and `in_progress`
    names the ones some worktree of the code repository resolves to. Those are
    listed apart because their branch can still store them, and the command
    exits 1 only for the rest. Kept beside `report_lines` so the two commands'
    wording lives in one place, and plain text for the same reason.

    One column width covers both groups, so the descriptions line up across
    the blank line between them.
    """
    if found.kind == "detached":
        return [f"✗ {DETACHED} in {found.root}", "    check out its branch there"]
    if found.kind != "store":
        return [f"ℹ spec root {found.root} {_ROOT_LAYOUT[found.kind]} — nothing there can be pushed"]
    left = [d for d in spec_dirs if d.name not in in_progress]
    held = [d for d in spec_dirs if d.name in in_progress]
    width = max((len(d.name) for d in spec_dirs), default=0) + 4

    def row(spec_dir: Unstored) -> str:
        return f"    {spec_dir.name.ljust(width)}{describe(spec_dir)}"

    if left:
        lines = [f"✗ {_count(len(left), 'spec dir')} not stored", *map(row, left)]
    elif held:
        lines = ["✓ every spec dir without a worktree is stored"]
    else:
        return ["✓ every spec dir is stored"]
    if held:
        lines += ["", f"In progress ({_count(len(held), 'spec dir')}, still have a worktree):", *map(row, held)]
    return lines
