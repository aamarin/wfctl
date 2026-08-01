"""Archive a story's speckit artifacts before its worktree is deleted.

`specs/` and `.agent/` are gitignored — deliberately, so the implementation is
what ships and the repo doesn't accumulate every spec/plan/tasks tree. The
consequence is that they live nowhere but the worktree, so `workmux remove`
destroys them. This copies them into wfctl's per-branch state dir, which
already holds current.md and session-summary.md and outlives the worktree.

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

# The design doc, which lives outside the spec dir — brainstorming writes it
# before speckit has a directory to write into.
_DESIGN_DOC = (".agent/spec.md", "1-design.md")

# Spec-dir-relative source -> archived name, in the order the pipeline produces
# them. Order is the point: this list *is* the numbering, so a plain iteration
# stays correct past 9 entries where sorting the results would not
# (10-delivery.md sorts before 2-spec.md).
_SPEC_MAP: list[tuple[str, str]] = [
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
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
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


def archive(
    worktree: Path, handle: str, branch: str, commit: str, spec_dir: Path | None, state_dir: Path
) -> tuple[Path | None, list[tuple[str, str]]]:
    """Copy this story's artifacts into `state_dir/archive`.

    Returns (archive_dir, mapped) — `(None, [])` when there was nothing to
    archive, which is a normal outcome, not a failure.
    """
    design = worktree / _DESIGN_DOC[0]
    if spec_dir is None and not design.is_file():
        return None, []

    archive_dir = state_dir / "archive"
    # A re-archive of the same branch should refresh, not accumulate. Any
    # previous run moves aside rather than being deleted, so a rerun never
    # destroys an earlier story.
    if archive_dir.exists():
        stamp = _utc_now().strftime("%Y%m%dT%H%M%SZ")
        archive_dir.rename(archive_dir.with_name(f"{archive_dir.name}-{stamp}"))
    archive_dir.mkdir(parents=True, exist_ok=True)

    mapped: list[tuple[str, str]] = []
    claimed: set[Path] = set()

    if design.is_file():
        _copy(design, archive_dir / _DESIGN_DOC[1])
        mapped.append((_DESIGN_DOC[1], _describe(worktree, design)))

    if spec_dir is not None:
        for rel, dst in _SPEC_MAP:
            src = spec_dir / rel
            if not src.is_file():
                continue
            _copy(src, archive_dir / dst)
            claimed.add(src.resolve())
            mapped.append((dst, _describe(worktree, src)))

        # Anything the map didn't name is still archived, so a speckit artifact
        # this list has never heard of is never silently dropped. Sorted, unlike
        # the shell version's `find` order, so the index is reproducible.
        for src in sorted(p for p in spec_dir.rglob("*") if p.is_file()):
            if src.resolve() in claimed:
                continue
            inner = src.relative_to(spec_dir)
            _copy(src, archive_dir / "extra" / inner)
            mapped.append((f"extra/{inner}", _describe(worktree, src)))

    (archive_dir / "README.md").write_text(
        _render_index(handle, branch, commit, worktree, mapped)
    )
    return archive_dir, mapped
