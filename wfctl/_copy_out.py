"""Copy a worktree's spec files to the spec dir in the main checkout.

The spec dir inside a worktree is deleted with it, so a removal has to put its
files somewhere that survives. In the default layout that place is the same
branch's folder under the main checkout's spec root, which is where every other
wfctl command already looks for them.

This module only compares and copies. Whether a difference stops a removal is the
store's decision, and it makes that decision between `plan` and `apply`, so
nothing is written for a removal that is about to be refused.
"""
from __future__ import annotations

import difflib
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CopyPlan:
    """What copying `source` into `dest` would do, computed without writing anything.

    A path that exists only under `dest` is in none of the three, so nothing here
    can reach it (FR-025).
    """

    source: Path
    dest: Path
    missing: list[str] = field(default_factory=list)
    same: list[str] = field(default_factory=list)
    # Relative path -> the text shown to the person. A unified diff, or the single
    # line "binary file differs" when either side is not valid UTF-8.
    different: dict[str, str] = field(default_factory=dict)


def _diff(source_file: Path, dest_file: Path, rel: str) -> str:
    try:
        mine = source_file.read_bytes().decode("utf-8")
        theirs = dest_file.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return "binary file differs"
    return "".join(
        difflib.unified_diff(
            theirs.splitlines(keepends=True),
            mine.splitlines(keepends=True),
            fromfile=f"main checkout/{rel}",
            tofile=f"worktree/{rel}",
        )
    )


def plan(source: Path, dest: Path) -> CopyPlan:
    """Compare every file under `source` with the file at the same path under `dest`.

    Byte for byte, with no git involved. A symlink is compared and copied as a link
    and never followed: following one would copy its target's content in, which
    could be a large folder or a file outside the spec dir (FR-019). Two links are
    the same when they point at the same text.
    """
    result = CopyPlan(source=source, dest=dest)
    for src in sorted(p for p in source.rglob("*") if p.is_symlink() or p.is_file()):
        rel = src.relative_to(source).as_posix()
        target = dest / rel
        if src.is_symlink():
            if not os.path.lexists(target):
                result.missing.append(rel)
            elif target.is_symlink() and os.readlink(src) == os.readlink(target):
                result.same.append(rel)
            else:
                result.different[rel] = f"symlink differs: the worktree's points to {os.readlink(src)}"
        elif not target.is_file():
            result.missing.append(rel)
        elif src.read_bytes() == target.read_bytes():
            result.same.append(rel)
        else:
            result.different[rel] = _diff(src, target, rel)
    return result


def apply(copy_plan: CopyPlan, overwrite: bool) -> None:
    """Write the files a plan says are missing, and the differing ones when `overwrite`.

    Raises on the first failure and leaves the files already copied. Each is a
    complete copy of the worktree's file, so a partial result is harmless, and the
    caller turns the exception into a stop. Swallowing it here would let a removal
    go ahead with the only copy unwritten (FR-028).
    """
    wanted = list(copy_plan.missing)
    if overwrite:
        wanted += list(copy_plan.different)
    for rel in wanted:
        source = copy_plan.source / rel
        target = copy_plan.dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            if os.path.lexists(target):
                target.unlink()
            os.symlink(os.readlink(source), target)
        else:
            shutil.copy2(source, target)
