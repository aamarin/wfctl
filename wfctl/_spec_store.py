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
