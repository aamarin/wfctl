"""Archive a story's speckit artifacts before its worktree is deleted.

`specs/` is gitignored — deliberately, so the implementation is what ships and
the repo doesn't accumulate every spec/plan/tasks tree. The consequence is that
it lives nowhere but the worktree, so `workmux remove` destroys it. This copies
it into wfctl's per-branch state dir, which already holds current.md and
session-summary.md and outlives the worktree.

Files are flattened and numbered in pipeline order, so the archive reads as the
story of the branch rather than as a directory to dig through. That makes it a
forensic snapshot, not a tree anyone can copy back.

Ported from scripts/archive-story.sh. One deliberate behaviour change: the spec
directory is resolved through `_paths.resolve_spec_dir` rather than a literal
`specs/<handle>`, so a worktree whose handle doesn't match its spec directory
now archives instead of silently finding nothing.
"""
from __future__ import annotations

import datetime
import shutil
from pathlib import Path

# Spec-dir-relative source -> archived name, in the order the pipeline produces
# them. Order is the point: this list *is* the numbering, so a plain iteration
# stays correct past 9 entries where sorting the results would not
# (10-delivery.md sorts before 2-spec.md).
_SPEC_MAP: list[tuple[str, str]] = [
    ("design.md", "1-design.md"),
    ("spec.md", "2-spec.md"),
    ("checklists/requirements.md", "3-requirements-checklist.md"),
    ("plan.md", "4-plan.md"),
    ("research.md", "5-research.md"),
    ("data-model.md", "6-data-model.md"),
    ("contracts/cli.md", "7-contract-cli.md"),
    ("quickstart.md", "8-quickstart.md"),
    ("tasks.md", "9-tasks.md"),
    ("delivery.md", "10-delivery.md"),
    ("checklists/analysis-report.md", "11-analysis-report.md"),
]


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _describe(worktree: Path, path: Path) -> str:
    """A source path as it should read in the index — worktree-relative if it
    lives inside one, absolute otherwise (WFCTL_SPEC_DIR can point anywhere)."""
    try:
        return str(path.relative_to(worktree))
    except ValueError:
        return str(path)


def _copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def _render_index(
    handle: str, branch: str, commit: str, worktree: Path, mapped: list[tuple[str, str]]
) -> str:
    lines = [
        f"# Story archive: {handle}",
        "",
        "| | |",
        "|---|---|",
        f"| Branch | `{branch}` |",
        f"| Last commit | `{commit}` |",
        f"| Archived | {_utc_now().strftime('%Y-%m-%dT%H:%M:%SZ')} |",
        f"| Source | `{worktree}` (removed) |",
        "",
        "Speckit artifacts, flattened and numbered in the order the pipeline",
        "produced them. Read top to bottom for the full story.",
        "",
        "| File | Was |",
        "|---|---|",
    ]
    # No sort: `mapped` is already in pipeline order, and sorting would be
    # lexicographic — which puts 10-delivery.md ahead of 2-spec.md.
    lines += [f"| [{dst}]({dst}) | `{src}` |" for dst, src in mapped]
    return "\n".join(lines) + "\n"


def _plan(spec_dir: Path | None) -> list[tuple[Path, str]]:
    """Every (source, archived name) pair this story would produce, pipeline order.

    Separate from the copying so `archive` knows whether there is anything to
    archive *before* it moves the previous run aside — a spec dir that has been
    emptied must not displace a good archive with an empty one.
    """
    plan: list[tuple[Path, str]] = []

    if spec_dir is None:
        return plan

    claimed: set[Path] = set()
    for rel, dst in _SPEC_MAP:
        src = spec_dir / rel
        if not src.is_file():
            continue
        claimed.add(src.resolve())
        plan.append((src, dst))

    # Anything the map didn't name is still archived, so a speckit artifact this
    # list has never heard of is never silently dropped. Sorted, unlike the shell
    # version's `find` order, so the index is reproducible.
    #
    # Symlinks are skipped: `is_file()` follows them, so a link pointing outside
    # the spec dir would copy its target's content in. The shell version's
    # `find -type f` tested the link itself and never matched one. `rglob` does
    # not descend into symlinked directories, so only links to files are at
    # issue. The `_SPEC_MAP` loop above still follows them, matching the shell
    # version's `[ -e ]` test.
    for src in sorted(p for p in spec_dir.rglob("*") if p.is_file() and not p.is_symlink()):
        if src.resolve() not in claimed:
            plan.append((src, f"extra/{src.relative_to(spec_dir)}"))

    return plan


def archive(
    worktree: Path, handle: str, branch: str, commit: str, spec_dir: Path | None, state_dir: Path
) -> tuple[Path | None, list[tuple[str, str]]]:
    """Copy this story's artifacts into `state_dir/archive`.

    Returns (archive_dir, mapped) — `(None, [])` when there was nothing to
    archive, which is a normal outcome, not a failure.
    """
    plan = _plan(spec_dir)
    if not plan:
        return None, []

    archive_dir = state_dir / "archive"
    # A re-archive of the same branch should refresh, not accumulate. Any
    # previous run moves aside rather than being deleted, so a rerun never
    # destroys an earlier story. Microseconds in the stamp, not just seconds:
    # renaming onto a non-empty directory raises, so a same-second rerun would
    # otherwise fail and skip the archive entirely.
    if archive_dir.exists():
        stamp = _utc_now().strftime("%Y%m%dT%H%M%S%fZ")
        archive_dir.rename(archive_dir.with_name(f"{archive_dir.name}-{stamp}"))
    archive_dir.mkdir(parents=True, exist_ok=True)

    for src, dst in plan:
        _copy(src, archive_dir / dst)
    mapped = [(dst, _describe(worktree, src)) for src, dst in plan]

    (archive_dir / "README.md").write_text(
        _render_index(handle, branch, commit, worktree, mapped)
    )
    return archive_dir, mapped
