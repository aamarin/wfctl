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


def _ancestor_branches(branch: str, repo_root: Path) -> list[str]:
    """Local branches other than `branch` that are git ancestors of it, nearest first.

    Covers the "epic planning branch as worktree base" convention: a child issue's
    worktree branches off its parent epic's planning branch (which carries
    specs/{feature}/), rather than off the target branch directly.
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

    # Every branch descends from the trunk (dev/main), so it always qualifies as an
    # "ancestor" too — nearest-first ranking is what keeps that from being a problem.
    # A real spec dir on a closer branch (e.g. the epic branch) is checked, and
    # returned, before the walk ever reaches the trunk. If nothing closer matched
    # and the walk does reach the trunk, it can't match by accident either: a base
    # branch name (dev/main) has no leading issue number, so the key-glob check is
    # closed to it — only literally-named `specs/dev` would match, never a stray
    # collision. Reaching the trunk with nothing found is therefore a legitimate
    # "no spec exists yet" signal (new branch, still pre-spec), not a false positive
    # to guard against.
    candidates = [b for b in result.stdout.split() if b and b != branch]
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


def resolve_agent_dir(repo_root: Path, branch: str) -> Path:
    """Return state dir: WFCTL_STATE_DIR → XDG path; creates the dir."""
    override = os.environ.get(_STATE_DIR_OVERRIDE)
    if override:
        d = Path(override)
        d.mkdir(parents=True, exist_ok=True)
        return d

    repo_name = repo_root.name
    xdg_base = Path(os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state"))
    d = xdg_base / "wfctl" / "repos" / repo_name / "stories" / branch
    d.mkdir(parents=True, exist_ok=True)
    return d
