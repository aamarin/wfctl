"""The guard's record checks: a pull request doesn't open or merge while the
branch's level-2 records contradict its own answer, or wait on a person.

Two rules, run by `_review_gate._judge` once every review group has reviewed
the commit the command acts on (`design-exceptions-live-with-specs`):

1. The branch's own spec folder says no boundary moved, and the branch changes a
   level-2 record anyway. The gate reads the boundary exception before it asks
   git about records, so an agent that wrote "no new boundary" early and added
   a record later passes the gate with a wrong answer. The record answers the
   question, so the refusal prints the command that removes the exception.
2. A level-2 record the branch changes has a status nobody ruled on. Before this,
   an unattended run could open and merge a PR whose boundary nobody approved,
   and `wfctl status` showing an unmet fact was the only sign.

The records are read at the commit the command acts on, through git, never from
the working tree: `gh pr merge` from the `main` checkout judges a branch that
isn't checked out, and the working tree there holds `main`'s records.

Like the review check, any error refuses. Nothing here imports `typer`, `rich`
or `_evidence`, since the guard runs before every Bash call. `rich` still loads
through `resolve_spec_dir`, once a command has matched.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wfctl._review_gate import _Session


def touched(session: _Session, trunk: str, head: str) -> list[Path]:
    """The level-2 records the branch adds or modifies, as repo-relative paths.

    Three dots, so a record the trunk gained after the branch point isn't the
    branch's. Deleted files are left out, since a deleted record decides nothing
    a person has to rule on. A path counts only when its parent is the arch
    root, which is the set `_evidence._branch_records` reads: level-3 records,
    views, scans and an old declaration all sit one level down.
    """
    from wfctl._paths import arch_root, is_in_tree

    root = session.root
    arch = arch_root(root)
    if not is_in_tree(arch, root):
        # An arch root outside the working tree is never in the diff, so the
        # branch can't be shown to change a record there.
        return []
    relative = arch.resolve().relative_to(root.resolve())
    listed = session.run(
        "git", "diff", "--name-only", "--diff-filter=d", f"{trunk}...{head}", "--", str(relative),
    )
    return [
        Path(line) for line in listed.splitlines()
        if line.endswith(".md") and Path(line).parent == relative
    ]


def _status(session: _Session, head: str, path: Path) -> str:
    from wfctl._arch import parse_status

    return parse_status(session.run("git", "show", f"{head}:{path}"))


def refusal(session: _Session, branch: str, head: str, trunk: str) -> str | None:
    """The refusal for the branch's records at `head`, or None to allow it.

    `trunk` is the ref `trunk_branch` returned, `origin/` prefix and all, since
    that is the ref git diffs against.
    """
    from wfctl import _design_exceptions
    from wfctl._arch import RULED_ON
    from wfctl._paths import is_own_spec_dir, resolve_spec_dir

    records = touched(session, trunk, head)
    if not records:
        return None

    # An epic's folder that a sub-issue falls back to isn't the sub-issue's: the
    # epic's "no" stays true for its other sub-issues, and the record answers it
    # for this one.
    spec_dir = resolve_spec_dir(branch, session.root)
    if (
        spec_dir is not None
        and is_own_spec_dir(spec_dir, branch, session.root)
        and _design_exceptions.boundary(spec_dir) is not None
    ):
        exception = _design_exceptions.path(spec_dir, _design_exceptions.BOUNDARY)
        return "\n".join([
            f"✗ {branch} touches {records[0]}, but its spec folder says no boundary moved.",
            "  The record answers the boundary question, so delete the exception:",
            f"  rm '{exception}'",
        ])

    statuses = ((p.stem, _status(session, head, p)) for p in records)
    waiting = [(slug, status) for slug, status in statuses if status not in RULED_ON]
    if not waiting:
        return None
    lines = [f"✗ {branch} touches records nobody has accepted:"]
    lines += [f"  {slug} ({status or 'unreadable'})" for slug, status in waiting]
    lines.append("  Ask a person to accept or reject each one before the PR opens.")
    return "\n".join(lines)
