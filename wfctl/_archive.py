"""Keep what a worktree removal would delete, or say why the removal must stop.

`check` looks for work that exists nowhere else: uncommitted edits, commits on no
remote that a merge into trunk would change, and untracked files. `save` copies
the untracked files and the folders `wfctl.json` lists under `save_on_remove`
into `unsaved/` in the branch's state dir.

Spec files are the store's job (`_spec_store`), and the removal hook runs all
three. The predicate for what a removal destroys is containment (`is_inside`),
never whether `spec_root` is set: a configured root that resolves back inside the
worktree is still at risk.
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
