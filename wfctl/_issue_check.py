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

import dataclasses
import enum
import subprocess
from dataclasses import dataclass
from pathlib import Path

from wfctl import _paths, _tracker


class Outcome(enum.Enum):
    MAIN_CHECKOUT = "main_checkout"
    TRUNK = "trunk"
    NO_TRACKER = "no_tracker"
    DETACHED = "detached"
    NO_KEY = "no_key"
    CLOSED = "closed"
    MISSING = "missing"
    OPEN = "open"
    KEY_ONLY = "key_only"
    NO_ANSWER = "no_answer"


@dataclass(frozen=True)
class Facts:
    """What `gather` found. Nothing here is inferred from another field.

    The tracker's three fields default to "not asked": `gather` fills them only
    when the local facts leave the verdict open, so an exempt checkout pays for
    no network call.
    """

    linked: bool
    on_trunk: bool
    tracker_configured: bool
    detached: bool
    branch: str
    key: str | None
    state: str | None = None
    state_declined: bool = False
    state_detail: str | None = None


@dataclass(frozen=True)
class Verdict:
    outcome: Outcome
    action: str  # "proceed" | "warn" | "refuse"
    lines: tuple[str, ...] = ()


def _refuse(outcome: Outcome, *lines: str) -> Verdict:
    return Verdict(outcome, "refuse", lines)


def _local_verdict(facts: Facts) -> Verdict | None:
    """The rows the checkout alone can settle, or None when the tracker must be asked.

    Separate from `decide` so that `gather` can ask it whether a tracker call is
    needed at all, without a second copy of the order to drift from this one.
    """
    if not facts.linked:
        return Verdict(Outcome.MAIN_CHECKOUT, "proceed")
    # What the main-checkout row protects is working on trunk, and a bare layout
    # has no main checkout: its `main` is a linked worktree like any other.
    if facts.on_trunk:
        return Verdict(Outcome.TRUNK, "proceed")
    if not facts.tracker_configured:
        return Verdict(Outcome.NO_TRACKER, "proceed")
    # Before the key: wfctl substitutes the short hash for a missing branch name,
    # and an all-digit hash parses as an issue key.
    if facts.detached:
        return _refuse(
            Outcome.DETACHED,
            "✗ this worktree is on a detached HEAD — it names no branch, so no issue.",
            "  Switch to the branch this worktree works on:",
            "    git switch <key>-<slug>",
            "  then run `wfctl start` again.",
        )
    if facts.key is None:
        return _refuse(
            Outcome.NO_KEY,
            f"✗ '{facts.branch}' names no issue — every worktree works against one.",
            "  Open an issue, then rename the branch to start with its key:",
            f"    git branch -m <key>-{facts.branch}",
        )
    return None


def decide(facts: Facts) -> Verdict:
    """The first row whose condition holds decides. Pure."""
    local = _local_verdict(facts)
    if local is not None:
        return local
    if facts.state_declined:
        return Verdict(Outcome.KEY_ONLY, "proceed")
    # No network, an expired token, a rate limit, a timeout. A session that
    # cannot start offline is the worse failure, and the `post_create` hooks
    # already take that stance with `|| true`.
    if facts.state is None:
        reason = (facts.state_detail or "no reason given").splitlines()[0]
        return Verdict(Outcome.NO_ANSWER, "warn", (
            f"⚠ could not ask the tracker whether #{facts.key} is open ({reason})"
            " — starting anyway",
        ))
    if facts.state == "closed":
        return _refuse(
            Outcome.CLOSED,
            f"✗ #{facts.key} is closed — this worktree works against an issue that is not open.",
            "  Reopen it, or open a new issue and rename the branch to start with its key.",
        )
    # A pull request number arrives here too: the backend reports it as missing.
    if facts.state == "missing":
        return _refuse(
            Outcome.MISSING,
            f"✗ #{facts.key} is not an issue in this tracker.",
            "  Open one, then rename the branch to start with its key.",
        )
    return Verdict(Outcome.OPEN, "proceed")


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """`cwd=repo_root` on every call: the suite runs inside a linked worktree and
    points `WFCTL_REPO_ROOT` elsewhere, so a call without it reads the wrong repo."""
    return subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True)


def _is_linked(repo_root: Path) -> bool:
    """Is `repo_root` a linked worktree rather than the checkout holding the repo?

    Asked of git rather than of `main_checkout()`, which returns None for the
    main checkout and for a bare layout's worktrees alike. A git call that fails
    reads as not linked: `start` has already found a repository by this point,
    and a git error is no evidence about the issue.
    """
    r = _git(repo_root, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir")
    lines = r.stdout.split()
    if r.returncode != 0 or len(lines) != 2:
        return False
    git_dir, common_dir = (Path(p).resolve() for p in lines)
    return git_dir != common_dir


def _on_trunk(repo_root: Path, branch: str) -> bool:
    """`trunk_branch` answers `origin/main` when the remote publishes its HEAD,
    and a local branch is never named that."""
    trunk = _paths.trunk_branch(repo_root)
    if trunk is None:
        return False
    return branch == trunk.removeprefix("origin/")


def gather(repo_root: Path, branch: str) -> Facts:
    """Everything `decide` reads, asked of git, the manifests and the tracker."""
    pattern = _tracker.configured_key_pattern(repo_root)
    key = _paths.extract_issue_key(branch, pattern) if pattern is not None else "unknown"
    facts = Facts(
        linked=_is_linked(repo_root),
        on_trunk=_on_trunk(repo_root, branch),
        tracker_configured=pattern is not None,
        detached=_paths.is_detached(repo_root),
        branch=branch,
        key=None if key == "unknown" else key,
    )
    if _local_verdict(facts) is not None or facts.key is None:
        return facts
    state, detail = _tracker.read_state(repo_root, facts.key)
    return dataclasses.replace(
        facts, state=state, state_declined=state is None and detail is None,
        state_detail=detail,
    )
