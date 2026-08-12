"""Rescue a story's speckit artifacts from a worktree about to be deleted.

**This is a rescue, not a presentation.** Copying is justified by risk of loss
and by nothing else. That decision reverses what this docstring said before: it
argued the flattened, numbered snapshot was worth producing regardless of risk,
so a durable spec root should still be archived. It should not. The numbering and
the generated index remain — they are how the archive *reads* — but they stopped
being the reason it exists.

The gap this fills is structural. `specs/` is gitignored deliberately, so the
implementation is what ships and the repo does not accumulate every
spec/plan/tasks tree. The consequence is that a worktree holding only design
artifacts reads *clean* to `git status`, so every version-control-based check
sees nothing to protect and `workmux remove` destroys them without complaint.
Work git *can* see — tracked edits, untracked files — already stops the removal
on its own. This covers exactly the set nothing else can.

So the predicate is containment: archive what this teardown would destroy, skip
what it would not (`is_inside`). A spec root outside the worktree survives
removal untouched; copying it produced a lossy duplicate that drifted from the
original the moment either changed, and protected nothing. Path containment,
never "is `spec_root` set" — a configured root resolving back inside the worktree
is still at risk.

That same predicate decides the exit code. Failing to copy at-risk artifacts
raises `ArchiveIncomplete`, which the CLI turns into a non-zero exit; a failing
`pre_remove` hook aborts the removal, so the worktree survives to be retried
rather than being destroyed with a warning printed after the fact.

`archive()` is promote-on-success: nothing reaches `archive/` until every copy
has landed. Writing in place meant a mid-copy failure left an unindexed partial
under the canonical name, and — since failure now prompts a retry — the retry
displaced that partial into the timestamped pool where nothing distinguished it
from a real previous run.

Files are flattened and numbered in pipeline order, so the archive reads as the
story of the branch rather than as a directory to dig through. That makes it a
forensic snapshot, not a tree anyone can copy back. `wfctl checkpoint` is the
restorable half; keeping the two in separate containers is deliberate.

Ported from scripts/archive-story.sh, and named `archive-specs` since #27 —
`archive-story` remains as a hidden alias. One deliberate behaviour change from
the shell version: the spec directory is resolved through
`_paths.resolve_spec_dir` rather than a literal `specs/<handle>`, so a worktree
whose handle doesn't match its spec directory now archives instead of silently
finding nothing.
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
    ("checklists/implement-complete.md", "12-implement-complete.md"),
]


class ArchiveIncomplete(Exception):
    """Copying at-risk artifacts failed partway; `at_risk` is how many were planned.

    The channel the CLI needs. `cli.py` wraps this whole command in one `try` and
    exits 0 on anything it catches — correct for a teardown hook, which must not
    strand a worktree over an unrelated bug. But a bare `OSError` carries no
    indication that the plan was non-empty, so without a distinct type the caller
    cannot tell "artifacts were lost" from "git rev-parse failed", and those two
    must produce opposite exit codes.

    Carries the count rather than making the caller recompute it: re-running
    `_plan` after a failure would re-stat a directory mid-failure and could
    disagree with what the failed run actually attempted.
    """

    def __init__(self, at_risk: int, cause: BaseException) -> None:
        super().__init__(str(cause))
        self.at_risk = at_risk


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def is_inside(worktree: Path, path: Path) -> bool:
    """Would deleting `worktree` destroy `path`?

    The whole predicate. Path containment, never "is `spec_root` set" — a repo
    whose configured root resolves back inside the worktree is still at risk, and
    a flag keyed on the setting would silently skip it.

    Resolved on both sides so a symlinked state dir or a `/private/var` vs `/var`
    mismatch does not read as "outside" and quietly stop archiving files that are
    in fact about to be deleted.
    """
    try:
        path.resolve().relative_to(worktree.resolve())
    except ValueError:
        return False
    return True


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
        # No "(removed)": the hook runs *before* removal and the command is also
        # invokable by hand, so existence is not knowable here. Where the artifacts
        # came from is a fact; whether that path still exists is not this file's
        # claim to make, and a stale archive asserting it is the failure mode.
        f"| Source | `{worktree}` |",
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


def _plan(worktree: Path, spec_dir: Path | None) -> list[tuple[Path, str]]:
    """Every (source, archived name) pair this story would produce, pipeline order.

    Separate from the copying so `archive` knows whether there is anything to
    archive *before* it moves the previous run aside — a spec dir that has been
    emptied must not displace a good archive with an empty one.
    """
    plan: list[tuple[Path, str]] = []

    # A branch that predates the move still has its artifacts at the old path, and
    # this runs from `pre_remove` — declining to archive them means deleting them.
    # `extra/` is precisely the shelf for artifacts the map does not name, so the
    # numbered sequence stays honest about what the current pipeline produces.
    #
    # The whole directory, not `spec.md` alone. Reading one filename out of a
    # directory about to be deleted rescues that file and destroys its neighbours:
    # three `brief.md` files survived the 2026-08-11 worktree cleanup only because
    # they were copied out by hand first. The new-layout path has never had this
    # problem — the spec-dir sweep below takes everything it does not map.
    #
    # Reconciling aamarin/wf-skills#11 FR-013, "Tooling MUST read exactly one
    # artifact location — the new one. No component reads both." That requirement
    # is about *inference*: two locations feeding pipeline state is how the two
    # disagree and a branch reports the wrong step. Nothing infers from this read.
    # It copies bytes out of a directory that is about to be deleted, and the
    # alternative to reading it is destroying it. The requirement's own purpose —
    # one source of truth for what the pipeline has produced — is unaffected;
    # `_pipeline.py` still reads only the new location. Recorded here because that
    # epic is closed, so this is the only place the reconciliation can live.
    # ponytail: transition-only; delete once no worktree predates the move.
    legacy_dir = worktree / ".agent"
    for src in sorted(p for p in legacy_dir.rglob("*") if p.is_file() and not p.is_symlink()):
        # Not `rel`: the `_SPEC_MAP` loop below rebinds that name to a str in this
        # same scope, and mypy reads the two as one variable.
        legacy_rel = src.relative_to(legacy_dir)
        # `spec.md` keeps the name it already has on disk in every archive written
        # so far; the rest land under a directory so the two are told apart.
        plan.append((
            src,
            "extra/legacy-agent-spec.md"
            if legacy_rel == Path("spec.md")
            else f"extra/legacy-agent/{legacy_rel}",
        ))

    # Archive what this teardown would destroy; skip what it would not. A spec dir
    # outside the worktree survives `workmux remove` untouched, so copying it
    # produces a lossy duplicate that drifts from the original the moment either
    # changes — and the copy was never protecting anything.
    #
    # Tested once against the directory rather than per file: every source below
    # is under `spec_dir`, so a per-file test would ask the same question N times
    # and answer it identically.
    if spec_dir is None or not is_inside(worktree, spec_dir):
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
    plan = _plan(worktree, spec_dir)
    if not plan:
        return None, []

    archive_dir = state_dir / "archive"
    staging = archive_dir.with_name(f"{archive_dir.name}.staging")

    # Nothing is written to `archive/` until every copy has landed. Writing into
    # it directly meant a mid-copy failure left an unindexed partial under the
    # canonical name while the complete result sat under a timestamp reading as
    # superseded — and since a failed archive now refuses the removal, the retry
    # that follows displaced that partial into the timestamped pool, where nothing
    # distinguished it from a real previous run. The safety mechanism was
    # manufacturing the ambiguity.
    #
    # Copy *and* promotion are both inside the `try`. Leaving the renames outside
    # it meant a failed promotion raised a bare OSError, which the CLI's generic
    # handler turns into exit 0 — teardown proceeds and the worktree is deleted
    # while nothing was ever promoted. Every way this function can fail with a
    # non-empty plan must reach `ArchiveIncomplete`, or the refusal has a hole.
    try:
        # Cleared first, and *not* with `ignore_errors`: a staging directory we
        # cannot remove is one whose stale files `_copy` would merge into this run
        # (it mkdirs with `exist_ok`) and promote as phantom entries. Failing here
        # blocks teardown, which is the right answer — the alternative is an
        # archive quietly claiming files this run never copied.
        if staging.exists():
            shutil.rmtree(staging)

        for src, dst in plan:
            _copy(src, staging / dst)
        mapped = [(dst, _describe(worktree, src)) for src, dst in plan]
        # Into staging, not the live directory: an index promoted separately would
        # describe files this run may not have copied.
        (staging / "README.md").write_text(
            _render_index(handle, branch, commit, worktree, mapped)
        )

        # A previous run moves aside rather than being deleted, so a rerun never
        # destroys an earlier story. Microseconds in the stamp, not just seconds:
        # renaming onto a non-empty directory raises, so a same-second rerun would
        # otherwise fail outright.
        if archive_dir.exists():
            stamp = _utc_now().strftime("%Y%m%dT%H%M%S%fZ")
            archive_dir.rename(archive_dir.with_name(f"{archive_dir.name}-{stamp}"))
        staging.rename(archive_dir)
    except Exception as exc:
        # Best effort, and wrapped in its own `try` rather than trusting
        # `ignore_errors` alone: this runs while another exception is in flight,
        # and *anything* raised here would replace `ArchiveIncomplete` with a
        # bare error the CLI treats as exit 0 — turning a refused teardown into a
        # completed one. Cleanup must not be able to undo the refusal.
        # A residue left behind is handled by the un-ignored rmtree at the top of
        # the next run.
        #
        # If the first rename succeeded and the second did not, the previous
        # archive now sits under its timestamp with no `archive/` beside it.
        # Nothing is lost and teardown is blocked, so the retry resolves it;
        # rolling back would add a failure path of its own for a rarer case.
        try:
            shutil.rmtree(staging, ignore_errors=True)
        except Exception:  # noqa: BLE001 — see above; the refusal outranks cleanup
            pass
        raise ArchiveIncomplete(len(plan), exc) from exc

    return archive_dir, mapped
