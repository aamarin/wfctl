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
