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

import os
import subprocess
from collections.abc import Iterable
from typing import Literal, NamedTuple


def _read(cwd: str, *args: str) -> str | None:
    """What `git -C cwd <args>` prints, stripped, or None when git cannot answer."""
    try:
        out = subprocess.run(
            ["git", "-C", cwd, *args], capture_output=True, text=True, check=True
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


LayoutKind = Literal["store", "store_no_upstream", "in_repo", "unmanaged"]


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
    3. `unmanaged`: anything else. A plain folder, a folder that does not
       exist yet, and a folder nested inside some other repository, where a
       commit would land on that repository's branch.

    The top-of-checkout test is separate from `owns_branch` because a folder
    one level inside a spec store passes `owns_branch` and is still not a
    store: a commit from there takes in the whole store, not this root. A
    detached HEAD in a repository of its own still passes `owns_branch`, and
    reads `store_no_upstream` here, since a detached HEAD has no upstream.
    """
    root = os.fspath(spec_root)
    repo = os.fspath(repo_root)
    top = top_level(root) if os.path.isdir(root) else None
    if top is None:
        return Layout("unmanaged", root)
    if top == os.path.realpath(root) and owns_branch(root, repo):
        upstream = _read(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        branch = _read(root, "symbolic-ref", "-q", "--short", "HEAD")
        remote = _read(root, "config", "--get", f"branch.{branch}.remote") if branch else None
        if upstream and remote:
            return Layout("store", root, remote, upstream)
        return Layout("store_no_upstream", root)
    theirs = _common_dir(root)
    if theirs is not None and theirs == _common_dir(repo):
        return Layout("in_repo", root)
    return Layout("unmanaged", root)


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
        capture_output=True, text=True, check=True,
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


def describe(spec_dir: Unstored) -> str:
    """The text one unstored spec dir renders as, shared by the pass, `check
    specs`, and removal.

    The uncommitted count wins when both hold, because committing is the next
    thing that has to happen, and the push carries the older commit with it.
    """
    if spec_dir.uncommitted:
        return f"uncommitted: {spec_dir.uncommitted} files"
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
