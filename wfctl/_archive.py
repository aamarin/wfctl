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
forensic snapshot, not a tree anyone can copy back. `git stash` is the
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
import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from wfctl._paths import trunk_branch

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

# Where rescued `.agent/` files land. Private on purpose: it names files, and
# nothing may infer *which* files were rescued from it. Unmapped spec artifacts
# land under `extra/` too, so a spec file named `legacy-agent-notes.md` matches
# this prefix without having come from `.agent/` at all — counting by it reported
# a superseded directory in repos that had none, and those repos could then never
# go silent, which is the one signal the rescue notice exists to give. `_plan`
# counts rescues as it makes them and returns the number; use that.
_LEGACY_DEST_PREFIX = "extra/legacy-agent"


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


@dataclass
class UnsavedCheck:
    """What `archive unsaved` found in a worktree before it copied anything.

    Only `edits`, `unmerged` and `listing_error` refuse a removal. `warnings`
    records each check git couldn't answer, and each unusable `save_on_remove`
    entry, and never refuses.

    `listing_error` is the one check that fails closed. When git can't list
    untracked files, going ahead would delete every one of them, and a stopped
    removal costs one manual step (#600 item 5).
    """

    worktree: Path
    edits: list[str] = field(default_factory=list)
    unmerged: list[str] = field(default_factory=list)
    trunk: str | None = None
    warnings: list[str] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)
    folders: list[str] = field(default_factory=list)
    listing_error: str | None = None

    @property
    def refuses(self) -> bool:
        return bool(self.edits or self.unmerged or self.listing_error)


@dataclass
class SavedResult:
    """The copy in `unsaved/`: where it landed, and every file in it, sorted."""

    dest: Path
    files: list[str]


class SaveFailed(Exception):
    """Copying into `unsaved/` failed, and the worktree still holds the only copy."""


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


def _git(worktree: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=worktree, capture_output=True, text=True
    )


def _reason(done: subprocess.CompletedProcess[str]) -> str:
    """The first line git printed to explain a failure, for a warning to carry."""
    lines = (done.stderr or done.stdout).strip().splitlines()
    return lines[0] if lines else f"git exited {done.returncode}"


def _unanswered(check: str, reason: str) -> str:
    return f"couldn't check for {check} ({reason}) — removal goes ahead"


def _uncommitted_edits(worktree: Path, found: UnsavedCheck) -> None:
    """Fill `edits` from `git status`, with untracked files left out on purpose.

    Untracked files are saved, not refused, so listing them here would stop a
    removal that `unsaved/` can handle. `-z` keeps a path with a space or a
    newline in it whole. A rename or copy entry is followed by a second entry
    holding the old path, and that one is not an edit of its own.
    """
    done = _git(worktree, "status", "--porcelain=v1", "-z", "--untracked-files=no")
    if done.returncode != 0:
        found.warnings.append(_unanswered("uncommitted edits", _reason(done)))
        return
    entries = done.stdout.split("\0")
    skip_next = False
    for entry in entries:
        if skip_next:
            skip_next = False
            continue
        if len(entry) < 4:
            continue
        found.edits.append(entry[3:])
        skip_next = "R" in entry[:2] or "C" in entry[:2]


def _unmerged_commits(worktree: Path, found: UnsavedCheck) -> None:
    """Fill `unmerged` with the commits that exist nowhere but this worktree.

    Three questions in order, and the first one keeps the common case fast. A
    commit on any remote branch survives the removal, so it never needs a stop.
    For the commits that are left, asking whether trunk holds them by hash
    stops every removal after a squash merge, since a squash commit shares a
    hash with none of the commits it replaced. So the check merges the branch
    into trunk in memory and asks whether that changes trunk's tree. A clean
    merge into an identical tree means trunk already holds the work, however it
    got there.

    The cost is a branch squash-merged and then followed by a change to the same
    lines on trunk. That merge conflicts, git can't tell the work is already
    there, and the removal stops (SC-004, accepted on #600 item 2).
    """
    local = _git(worktree, "log", "--format=%h %s", "HEAD", "--not", "--remotes")
    if local.returncode != 0:
        found.warnings.append(_unanswered("unmerged commits", _reason(local)))
        return
    commits = [line for line in local.stdout.splitlines() if line]
    if not commits:
        return

    found.trunk = trunk_branch(worktree)
    if found.trunk is None:
        found.warnings.append(_unanswered("unmerged commits", "no trunk branch found"))
        return

    merged = _git(worktree, "merge-tree", "--write-tree", found.trunk, "HEAD")
    if merged.returncode == 1:
        found.unmerged = commits
        return
    if merged.returncode != 0:
        found.warnings.append(_unanswered("unmerged commits", _reason(merged)))
        return
    trunk_tree = _git(worktree, "rev-parse", f"{found.trunk}^{{tree}}")
    if trunk_tree.returncode != 0:
        found.warnings.append(_unanswered("unmerged commits", _reason(trunk_tree)))
        return
    if merged.stdout.split("\n", 1)[0].strip() != trunk_tree.stdout.strip():
        found.unmerged = commits


# Spelled out rather than imported, for the reason `_paths` gives for `wfctl.json`.
_CONFIG_PATH = "wfctl.json"
SAVE_KEY = "save_on_remove"


def declared_folders(repo_root: Path) -> tuple[list[str], list[str]]:
    """Return (the folders `wfctl.json` lists under `save_on_remove`, problems).

    Same shape as `_paths.declared_trunk`. An entry that can't be used comes back
    as a problem and is left out of the folders, so removal skips it with a
    warning and `check config` reports it. A folder that doesn't exist is
    neither: most worktrees have no `research/` yet, and that is the expected
    state (FR-016, FR-034).

    A file that won't parse is "none declared" here, since `doctor` and
    `check config` already report it and this runs inside a removal.
    """
    path = repo_root / _CONFIG_PATH
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return [], []
    if not isinstance(data, dict) or SAVE_KEY not in data:
        return [], []
    entries = data[SAVE_KEY]
    if not isinstance(entries, list):
        return [], [f"'{SAVE_KEY}' must be a list of folders, such as [\"notes/\"]"]

    folders: list[str] = []
    problems: list[str] = []
    root = repo_root.resolve()
    for entry in entries:
        if not isinstance(entry, str) or not entry.strip():
            problems.append(f"'{SAVE_KEY}' entry {entry!r} must be a non-empty folder path")
        elif Path(entry).is_absolute():
            problems.append(
                f"'{SAVE_KEY}' entry '{entry}' is an absolute path; "
                "use a path relative to the repository"
            )
        elif (resolved := (root / entry).resolve()) == root:
            problems.append(
                f"'{SAVE_KEY}' entry '{entry}' is the repository itself; "
                "list a folder inside it"
            )
        elif root not in resolved.parents:
            problems.append(f"'{SAVE_KEY}' entry '{entry}' resolves outside the repository")
        else:
            folders.append(entry)
    return folders, problems


def _under(rel: str, folder: Path) -> bool:
    """Is the listed path `rel` the folder `folder` or inside it?"""
    path = Path(rel.rstrip("/"))
    return path == folder or folder in path.parents


def _untracked_files(worktree: Path, spec_dir: Path | None, found: UnsavedCheck) -> None:
    """Fill `untracked` with every untracked file that isn't ignored.

    A nested repository is listed once, as its folder with a trailing `/`, since
    git doesn't descend into it. Anything under the spec dir is dropped: it has
    its own destination, and a repository that doesn't ignore `specs/` would
    otherwise save it twice (FR-018).
    """
    done = _git(worktree, "ls-files", "--others", "--exclude-standard", "-z")
    if done.returncode != 0:
        found.listing_error = _reason(done)
        return
    listed = [entry for entry in done.stdout.split("\0") if entry]
    if spec_dir is not None and is_inside(worktree, spec_dir):
        spec_rel = spec_dir.resolve().relative_to(worktree.resolve())
        listed = [entry for entry in listed if not _under(entry, spec_rel)]
    found.untracked = listed


def _listed_folders(worktree: Path, spec_dir: Path | None, found: UnsavedCheck) -> None:
    """Fill `folders` from the worktree's own `wfctl.json`, which is committed.

    A listed folder that holds the spec dir, or is inside it, is skipped with a
    warning. Spec files have their own destination, and listing `specs/` would
    save them twice (FR-018).
    """
    listed, problems = declared_folders(worktree)
    found.warnings += [f"wfctl.json: {problem} — skipped" for problem in problems]
    spec_rel = (
        spec_dir.resolve().relative_to(worktree.resolve())
        if spec_dir is not None and is_inside(worktree, spec_dir)
        else None
    )
    for entry in listed:
        folder = Path(entry.rstrip("/"))
        if spec_rel is not None and (
            folder == spec_rel or folder in spec_rel.parents or spec_rel in folder.parents
        ):
            found.warnings.append(
                f"wfctl.json: '{SAVE_KEY}' entry '{entry}' holds the spec dir, "
                "which is saved separately — skipped"
            )
        elif (worktree / folder).is_dir():
            found.folders.append(entry)


def check(worktree: Path, spec_dir: Path | None) -> UnsavedCheck:
    """Everything `archive unsaved` finds in a worktree before it copies anything.

    A check git can't answer adds a warning and never a refusal, so an unrelated
    git error can't leave a worktree stuck (FR-013). The untracked listing is the
    exception, for the reason `UnsavedCheck` gives.
    """
    found = UnsavedCheck(worktree=worktree)
    _uncommitted_edits(worktree, found)
    _unmerged_commits(worktree, found)
    _untracked_files(worktree, spec_dir, found)
    _listed_folders(worktree, spec_dir, found)
    return found


def _staging_files(staging: Path) -> list[str]:
    """Every file and symlink under `staging`, relative and sorted.

    A link to a folder counts as the link and is never walked into, so the count
    is what `save` wrote and not what the link points at.
    """
    found: list[str] = []
    for root, dirs, files in os.walk(staging):
        base = Path(root)
        for name in list(dirs):
            if (base / name).is_symlink():
                dirs.remove(name)
                files.append(name)
        found.extend(str((base / name).relative_to(staging)) for name in files)
    return sorted(found)


def _copy_into(worktree: Path, staging: Path, files: list[Path], folders: list[Path]) -> None:
    for rel in files:
        src, dest = worktree / rel, staging / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_symlink():
            os.symlink(os.readlink(src), dest)
        else:
            shutil.copy2(src, dest)
    for rel in folders:
        # `symlinks=True` keeps a link inside the folder as a link. The folder may
        # be a nested repository, and its own history has to come across as it is.
        shutil.copytree(worktree / rel, staging / rel, symlinks=True)


def _relative(worktree: Path, path: Path) -> Path:
    return path.resolve().relative_to(worktree.resolve()) if path.is_absolute() else path


def save(check: UnsavedCheck, state_dir: Path, extra: list[Path]) -> SavedResult | None:
    """Copy what a removal would delete into `state_dir/unsaved`, or return None.

    Returns None when nothing needs saving, and creates no folder in that case.
    `extra` holds folders beyond the check's own, such as the spec dir in a layout
    with no main checkout.

    A folder and a file inside it can both be on the list, for instance a
    `save_on_remove` folder that git doesn't ignore. The folder copy already
    holds the file, and copying both makes `copytree` raise on the existing
    destination and stops every removal in that repository. So any path under a
    listed folder is dropped, and so is a folder under another listed folder
    (#600 item 6).
    """
    worktree = check.worktree
    folder_candidates = (
        [Path(entry.rstrip("/")) for entry in check.untracked if entry.endswith("/")]
        + [Path(entry.rstrip("/")) for entry in check.folders]
        + [_relative(worktree, path) for path in extra]
    )
    folders = sorted(
        {f for f in folder_candidates if not any(o != f and o in f.parents for o in folder_candidates)}
    )
    files = [
        Path(entry)
        for entry in check.untracked
        if not entry.endswith("/") and not any(_under(entry, f) for f in folders)
    ]
    if not files and not folders:
        return None

    dest = state_dir / "unsaved"
    staging = state_dir / "unsaved.staging"

    # The copy goes into staging and is renamed into place only when it is
    # complete. Writing into `unsaved/` directly meant a mid-copy failure left a
    # partial under the canonical name, and the retry then moved that partial
    # aside, where nothing told it apart from a real earlier save. Copy and
    # rename are both inside the `try`: a rename that fails must refuse the
    # removal too, or the worktree is deleted with nothing promoted.
    try:
        # Cleared first, and not with `ignore_errors`: a staging folder we can't
        # remove holds stale files the copy would merge into this run and
        # promote as files this run never copied. Failing here blocks the
        # removal, which is the right answer.
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        _copy_into(worktree, staging, files, folders)
        saved = _staging_files(staging)

        # An earlier save moves aside rather than being deleted, so a second
        # removal never destroys the first. Microseconds in the stamp, since
        # renaming onto a non-empty folder raises and a same-second rerun would
        # otherwise fail outright.
        if dest.exists():
            stamp = _utc_now().strftime("%Y%m%dT%H%M%S%fZ")
            dest.rename(dest.with_name(f"{dest.name}-{stamp}"))
        staging.rename(dest)
    except Exception as exc:
        # Best effort, in its own `try`: this runs while another exception is in
        # flight, and anything raised here would replace `SaveFailed` and let the
        # removal go ahead. Cleanup must not be able to undo the refusal. A
        # residue is cleared by the un-ignored rmtree at the top of the next run.
        try:
            shutil.rmtree(staging, ignore_errors=True)
        except Exception:  # noqa: BLE001 — the refusal outranks cleanup
            pass
        raise SaveFailed(str(exc)) from exc

    return SavedResult(dest=dest, files=saved)


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


def _plan(worktree: Path, spec_dir: Path | None) -> tuple[list[tuple[Path, str]], int]:
    """Every (source, archived name) pair this story would produce, pipeline order,
    and how many of them were rescued from the superseded directory.

    Separate from the copying so `archive` knows whether there is anything to
    archive *before* it moves the previous run aside — a spec dir that has been
    emptied must not displace a good archive with an empty one.

    The rescue count is returned rather than left for the caller to recover from
    the destination names: unmapped spec files land under `extra/` too, so a spec
    artifact merely *named* like a rescue — `extra/legacy-agent-notes.md` — was
    counted as one, and the machine reported a superseded directory it did not
    have. Only this loop knows which files actually came from there.
    """
    plan: list[tuple[Path, str]] = []
    rescued = 0

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
    # ponytail: transition-only. Delete once the rescue notice the caller prints
    # from this plan has stopped appearing during teardowns on every machine —
    # that silence is the end condition, and making it observable is why the
    # notice exists. #36 removed the doctor check that reported these directories
    # because it only fired where someone happened to run doctor; this fires
    # where the files are actually about to be destroyed. Delete this read, the
    # notice, and the `archive-story` alias together.
    legacy_dir = worktree / ".agent"
    for src in sorted(p for p in legacy_dir.rglob("*") if p.is_file() and not p.is_symlink()):
        # Not `rel`: the `_SPEC_MAP` loop below rebinds that name to a str in this
        # same scope, and mypy reads the two as one variable.
        legacy_rel = src.relative_to(legacy_dir)
        # `spec.md` keeps the name it already has on disk in every archive written
        # so far; the rest land under a directory so the two are told apart.
        plan.append((
            src,
            f"{_LEGACY_DEST_PREFIX}-spec.md"
            if legacy_rel == Path("spec.md")
            else f"{_LEGACY_DEST_PREFIX}/{legacy_rel}",
        ))
        rescued += 1

    # Archive what this teardown would destroy; skip what it would not. A spec dir
    # outside the worktree survives `workmux remove` untouched, so copying it
    # produces a lossy duplicate that drifts from the original the moment either
    # changes — and the copy was never protecting anything.
    #
    # Tested once against the directory rather than per file: every source below
    # is under `spec_dir`, so a per-file test would ask the same question N times
    # and answer it identically.
    if spec_dir is None or not is_inside(worktree, spec_dir):
        return plan, rescued

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

    return plan, rescued


def archive(
    worktree: Path, handle: str, branch: str, commit: str, spec_dir: Path | None, state_dir: Path
) -> tuple[Path | None, list[tuple[str, str]], int]:
    """Copy this story's artifacts into `state_dir/archive`.

    Returns (archive_dir, mapped, rescued) — `(None, [], 0)` when there was
    nothing to archive, which is a normal outcome, not a failure. `rescued`
    counts the files taken from the superseded directory, for the caller's
    notice; it is reported here because only `_plan` can tell a rescue from a
    spec artifact that happens to share its archived-name prefix.
    """
    plan, rescued = _plan(worktree, spec_dir)
    if not plan:
        return None, [], 0

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

    return archive_dir, mapped, rescued
