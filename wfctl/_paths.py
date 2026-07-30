"""Path resolution for wfctl state, branch, spec dir, and repo root."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


_STATE_DIR_OVERRIDE = "WFCTL_STATE_DIR"
_BRANCH_OVERRIDE = "WFCTL_BRANCH"
_SPEC_DIR_OVERRIDE = "WFCTL_SPEC_DIR"
_REPO_ROOT_OVERRIDE = "WFCTL_REPO_ROOT"

# Default issue-key shape: a plain leading number (GitHub / stock spec-kit).
# Trackers with non-numeric keys override this via "key_pattern" in their config.
DEFAULT_KEY_PATTERN = r"\d+"


def extract_issue_key(branch: str, pattern: str) -> str:
    """Pull the issue key off the front of a branch name; 'unknown' if none.

    The key is `pattern` anchored at the start, with an *optional* slug: it may
    stand alone (`342`) or be followed by a `-`/`_` separator (`342-foo`,
    `PROJ-123_bar`). A bad pattern degrades to no match, never raises.
    """
    try:
        m = re.match(rf"^({pattern})(?:[-_]|$)", branch)
    except re.error:
        return "unknown"
    return m.group(1) if m else "unknown"


def get_repo_root() -> Path:
    """Return git repo root; raises SystemExit(1) if not in a git repo."""
    override = os.environ.get(_REPO_ROOT_OVERRIDE)
    if override:
        return Path(override)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        raise SystemExit("wfctl: not a git repository")


def resolve_branch(repo_root: Path) -> str:
    """Return branch name: WFCTL_BRANCH → git → short SHA → 'detached'."""
    override = os.environ.get(_BRANCH_OVERRIDE)
    if override:
        return override
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, check=True,
            cwd=repo_root,
        )
        branch = result.stdout.strip()
        if branch:
            return branch
        # Detached HEAD — return short SHA
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
            cwd=repo_root,
        )
        return r.stdout.strip() or "detached"
    except subprocess.CalledProcessError:
        return "detached"


def _trunk_branch(repo_root: Path) -> str | None:
    """The repo's trunk — origin/HEAD when the remote publishes it, else the
    first local main/master/dev that exists. None when nothing looks like one."""
    head = subprocess.run(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        cwd=repo_root, capture_output=True, text=True,
    )
    if head.returncode == 0 and head.stdout.strip():
        return head.stdout.strip()
    for name in ("main", "master", "dev"):
        if subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", name],
            cwd=repo_root, capture_output=True,
        ).returncode == 0:
            return name
    return None


def _ancestor_branches(branch: str, repo_root: Path) -> list[str]:
    """Local branches other than `branch` that are git ancestors of it, nearest first.

    Covers the "epic planning branch as worktree base" convention: a child issue's
    worktree branches off its parent epic's planning branch (which carries
    specs/{feature}/), rather than off the target branch directly.

    Once a parent epic merges, its spec dir lives on the trunk and ancestry stops
    identifying it; the delivery.md "Issue Grouping Map" scan in speckit-orchestrate
    is what resolves a sub-issue's spec dir from that point on.
    """
    try:
        result = subprocess.run(
            ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads/"],
            capture_output=True, text=True, check=True, cwd=repo_root,
        )
    except subprocess.CalledProcessError:
        return []

    def commits_ahead(candidate: str) -> int | None:
        is_ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", candidate, branch],
            cwd=repo_root, capture_output=True,
        )
        if is_ancestor.returncode != 0:
            return None
        count = subprocess.run(
            ["git", "rev-list", "--count", f"{candidate}..{branch}"],
            capture_output=True, text=True, check=True, cwd=repo_root,
        )
        return int(count.stdout.strip())

    trunk = _trunk_branch(repo_root)

    def carries_own_work(candidate: str) -> bool:
        """Does `candidate` hold commits the trunk doesn't?

        Every branch descends from the trunk, so plain ancestry makes every
        *merged* branch an ancestor of every branch cut after it — and a merged
        feature branch still has its `specs/<its-name>/` in the tree, so the
        exact-name match in `resolve_spec_dir` hits it and hands back a finished
        story's pipeline. Nearest-first ranking doesn't save us: the trunk has no
        `specs/<trunk>` to match, so the walk sails past it into the merged
        siblings behind it.

        Carrying unmerged commits is what separates a live parent epic (it holds
        its own spec commit) from a merged or empty sibling (it holds nothing the
        trunk lacks). Robust to the trunk advancing, unlike comparing tips.
        """
        if trunk is None:
            return True
        r = subprocess.run(
            ["git", "rev-list", "--count", f"{trunk}..{candidate}"],
            cwd=repo_root, capture_output=True, text=True,
        )
        return r.returncode == 0 and r.stdout.strip() not in ("", "0")

    candidates = [
        b for b in result.stdout.split() if b and b != branch and carries_own_work(b)
    ]
    ranked = sorted(
        ((b, ahead) for b in candidates if (ahead := commits_ahead(b)) is not None),
        key=lambda pair: pair[1],
    )
    return [b for b, _ in ranked]


def resolve_spec_dir(branch: str, repo_root: Path) -> Path | None:
    """Return spec dir: WFCTL_SPEC_DIR/{branch-prefix}-* → None if not found.

    Falls back to the same lookup against ancestor branches (nearest first) when
    `branch` itself has no match — handles worktrees branched off a parent epic's
    planning branch instead of the target branch.
    """
    spec_root_override = os.environ.get(_SPEC_DIR_OVERRIDE)
    spec_root = Path(spec_root_override) if spec_root_override else repo_root / "specs"

    from wfctl import _tracker  # lazy: avoids import cycle at module load

    def match(candidate: str) -> Path | None:
        exact = spec_root / candidate
        if exact.is_dir():
            return exact
        key = extract_issue_key(candidate, _tracker.load_key_pattern(repo_root))
        if key != "unknown":
            matches = sorted(spec_root.glob(f"{key}[-_]*"))
            if matches:
                return matches[0]
        return None

    found = match(branch)
    if found is not None:
        return found

    for ancestor in _ancestor_branches(branch, repo_root):
        found = match(ancestor)
        if found is not None:
            return found

    return None


def _project_name(repo_root: Path) -> str:
    """The project's name — the main checkout's directory, not the worktree's.

    The `<project>/` level separates one project's state from another's, but a
    linked worktree's own directory is named after the branch, so keying on it
    fabricates a project per branch (`440-editable-table-row/440-editable-table-row/`)
    and splits a project's state across every worktree it has ever had.
    `--git-common-dir` points at the main checkout's .git from anywhere in the
    repo, including from a worktree.
    """
    common = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=repo_root, capture_output=True, text=True,
    )
    if common.returncode != 0 or not common.stdout.strip():
        return repo_root.name
    # Relative ('.git') from the main checkout, absolute from a worktree.
    git_dir = (repo_root / common.stdout.strip()).resolve()
    return git_dir.parent.name or repo_root.name


def resolve_agent_dir(repo_root: Path, branch: str) -> Path:
    """Return state dir: WFCTL_STATE_DIR → `$XDG_STATE_HOME/wfctl/<project>/<branch>`.

    Creates the dir. Project directories sit directly under wfctl's own XDG
    namespace — no `repos/` or `stories/` level, since everything wfctl stores
    is a project, and everything under a project is a branch.
    """
    override = os.environ.get(_STATE_DIR_OVERRIDE)
    if override:
        d = Path(override)
        d.mkdir(parents=True, exist_ok=True)
        return d

    repo_name = _project_name(repo_root)
    xdg_base = Path(os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state"))
    d = xdg_base / "wfctl" / repo_name / branch
    d.mkdir(parents=True, exist_ok=True)
    return d
