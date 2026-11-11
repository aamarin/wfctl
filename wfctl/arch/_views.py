"""The architecture views every repository needs, and which of them exist.

wfctl decides the list (`required-views-are-wfctls`): a system context view and
a container view in every repository, and one component view for each context
on the domain page's `Contexts` line. The agent draws each view and the user
reviews it, so nothing here reads what a view draws. What this module reads is
whether the file exists and which code its `covers` line names.

A view is not a record. `views/` is on `_paths.non_record_subtrees`, so no
reader of records counts one, and nothing here refuses anything.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import NamedTuple

from wfctl._paths import VIEWS_DIR

from . import _contexts, _records

# The kinds of view, in the order they print. A component view is one per
# context; the other two are one per repository. The shipped templates under
# `architecture-design/views/` carry these names, and a test compares the two.
VIEW_KINDS = ("system-context", "container", "component")


class RequiredView(NamedTuple):
    """One view wfctl expects a repository to have.

    `path` is relative to the architecture root. `name` is the kind for the
    two repository-wide views and the context's name for a component view.
    `covers` is empty when the view is missing or has no `covers` line.
    """

    kind: str
    name: str
    path: Path
    present: bool
    covers: tuple[str, ...]


def _covers_in(text: str) -> tuple[str, ...]:
    return _records.split_list(_records._frontmatter(text).get("covers", ""))


def _covers(file: Path) -> tuple[str, ...]:
    try:
        text = file.read_text()
    except (OSError, UnicodeDecodeError):
        return ()
    return _covers_in(text)


def _view(arch: Path, kind: str, name: str, path: Path) -> RequiredView:
    file = arch / path
    present = file.is_file()
    return RequiredView(kind, name, path, present, _covers(file) if present else ())


def required_views(arch: Path) -> tuple[RequiredView, ...]:
    """Every view the repository needs, in print order: the system context
    view, the container view, then one component view per context in the
    `Contexts` line's order. A repository with no architecture folder still
    needs the first two."""
    views = Path(VIEWS_DIR)
    found = [
        _view(arch, "system-context", "system-context", views / "system-context.md"),
        _view(arch, "container", "container", views / "container.md"),
    ]
    for context in _contexts.contexts(arch) or ():
        found.append(_view(arch, "component", context, views / "components" / f"{context}.md"))
    return tuple(found)


def for_branch(
    views: tuple[RequiredView, ...],
    contexts: tuple[str, ...] | None,
    listed: tuple[str, ...] | None,
    every: bool,
) -> tuple[RequiredView, ...]:
    """The views a branch listing `listed` is shown, present ones first.

    The filter applies to component views only, and follows `select`: a branch
    whose list names only contexts on the `Contexts` line sees those contexts'
    views. No list, an empty one, or a name that isn't there shows every view,
    since leaving out a view that applies is worse than showing one that
    doesn't. An outside party has no component view, so a branch listing one
    sees every view too, where `select` would narrow its records.

    Reads no files, like `select`. Within each group the order is
    `required_views`' order, which is the `Contexts` line's, not the branch's.
    """
    known = set(contexts or ())
    narrow = not every and bool(listed) and known.issuperset(listed or ())
    wanted = set(listed or ())
    shown = [v for v in views if v.kind != "component" or not narrow or v.name in wanted]
    return tuple([v for v in shown if v.present] + [v for v in shown if not v.present])


class Freshness(NamedTuple):
    """Whether a present view still matches the code it covers.

    `state` is `current`, `stale`, or `unchecked`. `detail` is the text that
    prints in brackets after the path, and is empty when the view is current.
    """

    state: str
    detail: str


_CURRENT = Freshness("current", "")
_NO_HISTORY = Freshness("unchecked", "not in this repository's history")


def _run(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
    """The finished `git` call, or None when it couldn't run, `git` missing
    included. Output that isn't UTF-8 is decoded with replacement characters
    rather than raising, since a view's text is the repository's to write and
    freshness never changes the exit code."""
    try:
        return subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _git(repo_root: Path, *args: str) -> str | None:
    """`git`'s output, or None when the call fails for any reason."""
    done = _run(repo_root, *args)
    return done.stdout.strip() if done is not None and done.returncode == 0 else None


def _committed_covers(view_path: Path, commit: str, repo_root: Path) -> tuple[str, ...] | None:
    """The `covers` line as `commit` holds it, or None when git can't show it.

    The count runs from the view's last commit, so `covers` has to come from
    the same commit. Read from the working tree instead, a redraw that narrows
    `covers` clears a stale mark before anything is committed."""
    try:
        rel = view_path.resolve().relative_to(repo_root.resolve())
    except (OSError, ValueError):
        return None
    text = _git(repo_root, "show", f"{commit}:{rel.as_posix()}")
    return None if text is None else _covers_in(text)


def _missing(path: str, repo_root: Path) -> Freshness:
    """Why git counts no commits to `path`. Only the wording reads the working
    tree; the state is unchecked either way."""
    if os.path.lexists(repo_root / path):
        return Freshness("unchecked", f"covers names {path}, which git doesn't track")
    return Freshness("unchecked", f"covers names {path}, which doesn't exist")


def _outside(path: str, repo_root: Path) -> bool:
    """Whether `path` falls outside the repository. git refuses such a path
    with an error, and that error isn't a failed call to read as the history
    reason, since the view is in the history and the path is what's wrong.

    Decided from the path's text, never by following it. git tracks a symlink
    as the link itself, so one pointing outside the repository has commits to
    count, and what it points at on disk mustn't decide a committed view."""
    for root in (Path(os.path.abspath(repo_root)), repo_root.resolve()):
        try:
            Path(os.path.normpath(root / path)).relative_to(root)
        except ValueError:
            continue
        return False
    return True


def _commits_since(last: str, paths: tuple[str, ...], repo_root: Path) -> int | None:
    """How many commits after `last` change any of `paths`, or None when the
    call fails.

    git's default history leaves out a merged branch with no net change to a
    path, so a file changed and changed back there would count 0 and the view
    would read current. `--full-history` keeps that branch, and `--no-merges`
    keeps the merge commit itself from counting as a second change.

    Counting commits rather than the merged result has two costs:

    1. An edit made in a merge commit itself, such as a conflict resolution,
       isn't counted. The commits that were merged still count.
    2. A branch whose changes the merge threw away, such as one merged with
       `-s ours`, still counts, so the view reads stale over code that never
       landed."""
    count = _git(
        repo_root, "rev-list", "--count", "--full-history", "--no-merges",
        f"{last}..HEAD", "--", *paths,
    )
    return None if count is None else int(count)


def _in_history(path: str, last: str, repo_root: Path) -> bool | None:
    """Whether `path` is in the view's last commit or HEAD, or has commits
    between them, or None when a call fails. A path in neither commit is one
    added and deleted again since the view, or one that never existed."""
    for commit in (last, "HEAD"):
        listed = _git(repo_root, "ls-tree", commit, "--", path)
        if listed is None:
            return None
        if listed:
            return True
    count = _commits_since(last, (path,), repo_root)
    return None if count is None else count > 0


def _drawing(view: RequiredView, view_path: str, repo_root: Path) -> Freshness:
    """A view with no commit yet, which is being drawn now. Its `covers` line
    can only come from the working tree, and so can the paths it names."""
    if not view.covers:
        return Freshness("unchecked", "no covers line")
    for path in view.covers:
        if _outside(path, repo_root) or not os.path.lexists(repo_root / path):
            return _missing(path, repo_root)
        tracked = _git(repo_root, "ls-files", "--", path)
        if tracked is None:
            return _NO_HISTORY
        if not tracked:
            return _missing(path, repo_root)
    ignored = _run(repo_root, "check-ignore", "-q", "--", view_path)
    if ignored is None or ignored.returncode not in (0, 1):
        return _NO_HISTORY
    if ignored.returncode == 0:
        return Freshness("unchecked", "git ignores the view")
    return _CURRENT


def freshness(view: RequiredView, arch: Path, repo_root: Path) -> Freshness:
    """Whether `view` is current, stale, or unchecked, read from commits only.

    The order of the checks is the order the reasons win in (data-model
    §Required view). The view's history comes first, because a failed `git`
    call applies to every view under the same root, the way it does for a root
    outside the working tree. A failed call is never read as "no commit yet",
    since the view would then print as current forever when nothing checked it.
    Then the `covers` line, then the paths it names. Once the view has a commit,
    both come from commits, so a path deleted or added since the view reads as
    stale, and an uncommitted edit to the view or the code changes nothing. A
    view with no commit yet is current, since it's being drawn now, unless git
    ignores it.

    The last commit leaves out the view's own deletion. A view deleted and
    being redrawn is measured against the commit that last held it, rather
    than reading as outside the history. Unlike the counts, the last commit is
    found with git's default history. When a merge keeps one side's copy of
    the view, default history follows that side, so the commit it finds wrote
    the view HEAD holds. Full history can instead find a later commit on a
    branch whose copy of the view the merge threw away.

    Each check below that isn't the stale count closes a way for the view to
    read current forever. git counts no commits to a path it doesn't track,
    whether the path is gone, ignored, or outside the repository, and an
    ignored view never gets the commit that would end "being drawn now".
    """
    view_path = str(arch / view.path)
    last = _git(repo_root, "log", "-1", "--diff-filter=ACMRT", "--format=%H", "--", view_path)
    if last is None:
        return _NO_HISTORY
    if not last:
        return _drawing(view, view_path, repo_root)
    covers = _committed_covers(arch / view.path, last, repo_root)
    if covers is None:
        return _NO_HISTORY
    if not covers:
        return Freshness("unchecked", "no covers line")
    for path in covers:
        if _outside(path, repo_root):
            return _missing(path, repo_root)
        found = _in_history(path, last, repo_root)
        if found is None:
            return _NO_HISTORY
        if not found:
            return _missing(path, repo_root)
    n = _commits_since(last, covers, repo_root)
    if n is None:
        return _NO_HISTORY
    if n == 0:
        return _CURRENT
    plural = "" if n == 1 else "s"
    return Freshness("stale", f"{n} commit{plural} to {', '.join(covers)} since the view changed")
