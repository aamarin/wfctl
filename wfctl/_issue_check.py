"""May a session open in this worktree, given the issue its branch names?

`wfctl start` asks before it writes anything
(`session-start-worktree-requires-open-issue`). The question is split in two
(`docs/architecture/design/497-issue-check-is-a-pure-verdict.md`): `gather`
does all the IO and returns what git, the manifests and the tracker said, and
`decide` turns those facts into a verdict without touching anything. The order
the questions are settled in lives in `decide` alone, so a new outcome is a row
there and a test beside it.
"""
from __future__ import annotations

import enum
import subprocess
from dataclasses import dataclass
from pathlib import Path

from wfctl import _tracker


class Outcome(enum.Enum):
    MAIN_CHECKOUT = "main_checkout"
    NO_TRACKER = "no_tracker"
    # Reached when nothing earlier decided. Rows added later take its place in
    # the cases they cover.
    UNDECIDED = "undecided"


@dataclass(frozen=True)
class Facts:
    """What `gather` found. Nothing here is inferred from another field."""

    linked: bool
    tracker_configured: bool


@dataclass(frozen=True)
class Verdict:
    outcome: Outcome
    action: str  # "proceed" | "warn" | "refuse"
    lines: tuple[str, ...] = ()


def decide(facts: Facts) -> Verdict:
    """The first row whose condition holds decides. Pure."""
    if not facts.linked:
        return Verdict(Outcome.MAIN_CHECKOUT, "proceed")
    if not facts.tracker_configured:
        return Verdict(Outcome.NO_TRACKER, "proceed")
    return Verdict(Outcome.UNDECIDED, "proceed")


def _is_linked(repo_root: Path) -> bool:
    """Is `repo_root` a linked worktree rather than the checkout holding the repo?

    Asked of git rather than of `main_checkout()`, which returns None for the
    main checkout and for a bare layout's worktrees alike. `cwd=repo_root`
    because the suite runs inside a linked worktree and points
    `WFCTL_REPO_ROOT` elsewhere; without it every test would read as linked. A
    git call that fails reads as not linked: `start` has already found a
    repository by this point, and a git error is no evidence about the issue.
    """
    r = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"],
        cwd=repo_root, capture_output=True, text=True,
    )
    lines = r.stdout.split()
    if r.returncode != 0 or len(lines) != 2:
        return False
    git_dir, common_dir = (Path(p).resolve() for p in lines)
    return git_dir != common_dir


def gather(repo_root: Path, branch: str) -> Facts:
    """Everything `decide` reads, asked of git, the manifests and the tracker."""
    return Facts(
        linked=_is_linked(repo_root),
        tracker_configured=_tracker.configured_key_pattern(repo_root) is not None,
    )
