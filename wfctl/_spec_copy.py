"""Copy a worktree's spec files out before the worktree is removed.

This is the half of `wfctl store specs` for a spec dir inside the worktree, which
git can't commit without landing on the code's branch. A spec dir outside it is
committed and pushed by `_spec_store` instead. The removal hook picks between
the two on where the spec dir is. `store specs` also asks git first, so a spec
store checked out inside the worktree is committed rather than copied.

This file holds the result type and the copy-out's outcomes. Comparing and
copying are done by `_copy_out`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from wfctl import _copy_out, _paths

# Outcomes that leave the spec files somewhere that survives the removal.
_SAFE = frozenset({"copied", "already_copied", "empty", "to_unsaved"})


@dataclass
class CopyResult:
    """What one copy-out ended with.

    `stops_removal` is a property here and not a check in the hook, so that
    `wfctl store specs` run by hand and the removal hook read the same answer
    (FR-029).

    `dest` and `different` are what a `differs` outcome found, kept as fields so
    the removal hook's stop block is built from them and not by editing `lines`,
    which would tie it to the wording `store specs` prints (#610).
    """

    outcome: str
    spec_dir: Path | None
    inside: bool
    lines: list[str] = field(default_factory=list)
    dest: Path | None = None
    different: dict[str, str] = field(default_factory=dict)

    @property
    def stops_removal(self) -> bool:
        return self.inside and self.outcome not in _SAFE

    @property
    def exit_code(self) -> int:
        return 1 if self.outcome in {"differs", "copy_failed"} else 0


def _is_inside(spec_dir: Path, worktree: Path) -> bool:
    return spec_dir.resolve().is_relative_to(worktree.resolve())


def inside_worktree(spec_dir: Path, repo_root: Path) -> bool:
    """Whether removing the worktree at `repo_root` would delete `spec_dir`.

    The main checkout is never being removed, so its spec dir is not inside in
    this sense, even though it is under `repo_root`. `store specs` asks this to
    pick between copying the spec dir out and committing it in its spec store.
    """
    return _is_inside(spec_dir, repo_root) and not _paths.is_main_checkout(repo_root)


def difference_rows(different: dict[str, str]) -> list[str]:
    """Each differing file's path, then its diff indented two spaces under it.

    Unindented at the left, because `store specs` and the removal hook each nest
    the block at their own depth.
    """
    rows: list[str] = []
    for rel, diff in different.items():
        rows.append(rel)
        rows.extend(f"  {row}" for row in diff.splitlines())
    return rows


def _count(n: int) -> str:
    return f"{n} spec file" if n == 1 else f"{n} spec files"


def copy_out(
    spec_dir: Path | None,
    branch: str,
    repo_root: Path,
    overwrite: bool = False,
    dry_run: bool = False,
) -> CopyResult:
    """Copy `spec_dir` from the worktree at `repo_root` into the main checkout.

    With `dry_run` nothing is written and the result is the one a real run would
    give. The removal hook uses it to learn whether differing files would stop the
    removal before it copies anything, and reads the answer from `stops_removal`
    like every other caller.
    """
    if spec_dir is None:
        return CopyResult("no_spec_dir", None, False, [f"ℹ no spec dir for {branch}"])

    inside = inside_worktree(spec_dir, repo_root)
    if not inside:
        return CopyResult(
            "not_applicable",
            spec_dir,
            inside,
            [f"ℹ spec dir {spec_dir} is not inside a worktree being removed — nothing to copy"],
        )

    main = _paths.main_checkout(repo_root)
    if main is None:
        return CopyResult(
            "to_unsaved",
            spec_dir,
            True,
            ["ℹ no main checkout — spec files are saved with the unsaved work"],
        )

    dest = _paths.spec_root(main) / spec_dir.name
    # WFCTL_SPEC_DIR is process-global, so it can name a root inside the worktree
    # being removed. The destination is then the spec dir itself, the comparison
    # finds every file already copied, and the removal deletes the only copy.
    if _is_inside(dest, repo_root):
        return CopyResult(
            "to_unsaved",
            spec_dir,
            True,
            [f"ℹ {dest} is inside the worktree — spec files are saved with the unsaved work"],
        )
    # Comparing reads every spec file, so it can fail the way a copy can. Left to
    # propagate, the hook's catch-all would let the removal go ahead (FR-028).
    try:
        plan = _copy_out.plan(spec_dir, dest)
    except OSError as exc:
        return CopyResult(
            "copy_failed",
            spec_dir,
            True,
            [f"✗ couldn't compare spec files with {dest} ({exc})"],
        )

    if plan.different and not overwrite:
        lines = [
            f"✗ {dest} holds different spec files for {branch}",
            *(f"    {row}" for row in difference_rows(plan.different)),
            "  run `wfctl store specs --overwrite` to replace them with the worktree's copies",
        ]
        return CopyResult("differs", spec_dir, True, lines, dest, plan.different)

    # Told apart from `already_copied`, which an empty spec dir also reaches with
    # nothing written: saying "already" there claims a copy nobody made (#612).
    if not (plan.missing or plan.same or plan.different):
        return CopyResult(
            "empty", spec_dir, True, [f"ℹ spec dir {spec_dir} is empty, nothing to copy"]
        )

    written = len(plan.missing) + (len(plan.different) if overwrite else 0)
    if written == 0:
        return CopyResult(
            "already_copied",
            spec_dir,
            True,
            [f"✓ spec files already in {dest}, nothing copied"],
        )

    if not dry_run:
        try:
            _copy_out.apply(plan, overwrite)
        except OSError as exc:
            return CopyResult(
                "copy_failed",
                spec_dir,
                True,
                [f"✗ couldn't copy spec files to {dest} ({exc})"],
            )
    return CopyResult(
        "copied",
        spec_dir,
        True,
        [f"✓ copied {_count(written)} → {dest}", "    nothing backs this copy up"],
    )
