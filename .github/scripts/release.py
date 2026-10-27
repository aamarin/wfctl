#!/usr/bin/env python3
"""Cut a wfctl release: propose a version, draft the release notes, open the pull request.

    uv run python .github/scripts/release.py

Run from an up-to-date `main`. The script reads the release notes under
`changes/`, proposes the next version, and shows the draft that towncrier
builds from them. After the version and the draft are confirmed, it makes one
commit on a `release/v<version>` branch, pushes that branch, and opens a pull
request into `main`. It never pushes `main` and never merges.

Nothing before the branch is created touches the repository. The draft is built
in a temporary directory outside it, and stopping at either prompt leaves the
tree and the branches as they were.

The lock command, the pull request command, and the prompt are parameters so
the tests can replace `uv lock`, `gh pr create`, and `input` with stubs.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Callable, Sequence
from pathlib import Path

# The check script decides what a note's name looks like and which categories
# exist, and this script reads the same answer instead of keeping a second copy.
# A copy that fell behind would leave a note the check accepts out of the draft,
# and the release commit would then delete it. Running this file directly puts
# its folder on the path already; the tests load it by file path and do not.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_release_note import NOTE_NAME, towncrier_settings  # noqa: E402

# The one fact this script holds about the categories. Which ones exist, and in
# what order the draft prints them, is towncrier's table in pyproject.toml.
MINOR_CATEGORIES = ("change", "addition")
# How a category reads in the proposal's reason. A category added to the table
# later falls back to its directory name.
LABELS = {"change": "behaviour change", "addition": "addition"}

MERGE_SUBJECT = re.compile(r"^Merge pull request #(?P<number>\d+) from \S+")
VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
NO_CHANGES = "No significant changes."


class Abort(Exception):
    """Stop before anything is changed."""


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, cwd=cwd)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return run("git", *args)


def plural(count: int, noun: str) -> str:
    if count == 1:
        return f"{count} {noun}"
    return f"{count} {noun}{'es' if noun.endswith('x') else 's'}"


def version_tuple(text: str) -> tuple[int, int, int] | None:
    match = VERSION.match(text)
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def refuse(message: str) -> int:
    print(f"✗ {message}")
    return 1


def precondition_failure() -> str | None:
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if branch != "main":
        return f"releases are cut from main, and this is {branch}"
    if git("status", "--porcelain").stdout.strip():
        return "the working tree has changes, commit or stash them first"
    if git("fetch", "origin", "main").returncode != 0:
        return "couldn't fetch origin main"
    if git("rev-parse", "main").stdout != git("rev-parse", "origin/main").stdout:
        return "main isn't at origin/main, run git pull --ff-only"
    if not last_tag():
        return "no release tag found to compare against"
    return None


def last_tag() -> str:
    tags = git("tag", "--list", "v*", "--sort=-v:refname").stdout.split()
    return tags[0] if tags else ""


def current_version() -> tuple[int, int, int]:
    text = tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]
    parsed = version_tuple(text)
    assert parsed is not None, f"pyproject.toml carries version {text!r}"
    return parsed


def notes_by_category(
    directory: str, categories: list[str]
) -> tuple[dict[str, list[str]], list[str]]:
    """The notes under `directory` by category, and the files that aren't notes.

    A file with a note's name but a category towncrier doesn't list counts as
    not a note, since towncrier would skip it when drafting. The release commit
    removes the whole folder, so anything left out here has to stop the release
    instead of being deleted without a trace.
    """
    found: dict[str, list[str]] = {}
    stray: list[str] = []
    # `-z`, since git otherwise quotes a path with an accented letter, and the
    # quoted name would read as a stray file and stop the release.
    for path in filter(None, git("ls-files", "-z", directory).stdout.split("\0")):
        name = path.removeprefix(directory + "/")
        match = NOTE_NAME.match(name) if "/" not in name else None
        if match and match["category"] in categories:
            found.setdefault(match["category"], []).append(path)
        else:
            stray.append(path)
    return found, stray


def merges_since(tag: str, directory: str) -> tuple[int, list[int]]:
    """Every pull request merged since `tag`, and the ones that added no note.

    The merge commit's first parent is `main` before the merge, so the files it
    added under `changes/` are the notes that pull request brought. A squash or
    rebase merge leaves no merge commit, which is why the repository allows only
    merge commits.
    """
    total = 0
    unnoted: list[int] = []
    log = git("log", "--merges", "--format=%H %s", f"{tag}..HEAD").stdout.splitlines()
    for line in log:
        sha, _, subject = line.partition(" ")
        match = MERGE_SUBJECT.match(subject)
        if not match:
            continue
        total += 1
        diff = git("diff", "-z", "--name-only", "--no-renames", "--diff-filter=A",
                   f"{sha}^1", sha, "--", directory)
        added = [path for path in diff.stdout.split("\0") if path]
        if not added:
            unnoted.append(int(match["number"]))
    return total, sorted(unnoted)


def propose(
    notes: dict[str, list[str]], unnoted: list[int]
) -> tuple[tuple[int, int, int], str]:
    major, minor, patch = current_version()
    counts = {c: len(notes[c]) for c in notes if c != "none"}
    if any(counts.get(c) for c in MINOR_CATEGORIES):
        parts = [plural(counts[c], LABELS.get(c, c)) for c in MINOR_CATEGORIES if counts.get(c)]
        kind, version = "minor", (major, minor + 1, 0)
    else:
        parts = [plural(counts["fix"], "fix")] if counts.get("fix") else ["no notes yet"]
        kind, version = "patch", (major, minor, patch + 1)
    reason = ", ".join(parts)
    if unnoted:
        reason += f", and {plural(len(unnoted), 'merge')} with no release note to read first"
    return version, f"{kind}: {reason}"


def build_draft(version: str, directory: str, notes: dict[str, list[str]]) -> str:
    """The release notes towncrier would write, without writing anything.

    The `none` notes are left out by building from a copy of the notes folder
    in a temporary directory, so the working tree stays untouched until the
    version is confirmed. Towncrier needs the folder inside a base directory, which `--dir`
    names, and the config is read from the repository's own pyproject.toml.
    """
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / directory).mkdir()
        for category, paths in notes.items():
            if category == "none":
                continue
            for path in paths:
                (base / path).write_text(git("show", f"HEAD:{path}").stdout)
        done = run(sys.executable, "-m", "towncrier", "build", "--draft",
                   "--version", version, "--config", str(Path("pyproject.toml").resolve()),
                   "--dir", str(base))
    if done.returncode != 0:
        raise Abort(f"towncrier couldn't build the draft:\n{done.stderr.strip()}")
    # towncrier says "What is seen below is what would be written." on stderr,
    # so stdout is the draft alone.
    kept: list[str] = []
    dropped_title = False
    for line in done.stdout.splitlines():
        if not dropped_title and line.startswith("# "):
            dropped_title = True
            continue
        if line.strip() == NO_CHANGES:
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def ask_version(ask: Callable[[str], str], proposed: str) -> str:
    current = current_version()
    while True:
        try:
            answer = ask(f"Confirm the version [{proposed}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            raise Abort("") from None
        chosen = answer or proposed
        parsed = version_tuple(chosen)
        if parsed is None:
            print(f"✗ {chosen!r} isn't a version, use X.Y.Z")
        elif parsed <= current:
            print(f"✗ {chosen} isn't higher than the current version, {'.'.join(map(str, current))}")
        else:
            return chosen


def edit(draft: str, workdir: Path) -> str:
    """Open the draft in git's editor and return what was saved.

    Git itself is not used to edit: its default cleanup strips every line
    starting with `#` as a comment, and every heading in the draft does.
    """
    editor = git("var", "GIT_EDITOR").stdout.strip()
    path = workdir / "RELEASE_NOTES.md"
    path.write_text(draft + "\n" if draft else "")
    try:
        done = subprocess.run(["sh", "-c", f'{editor} "$@"', "sh", str(path)])
    except KeyboardInterrupt:
        raise Abort("") from None
    saved = path.read_text().strip()
    if done.returncode != 0 or not saved:
        raise Abort("")
    return saved


def set_version(version: str) -> None:
    """Replace the version under `[project]`, then read it back with tomllib.

    Not a grep for `^version =`: a version key in any other section would match.
    """
    path = Path("pyproject.toml")
    text = path.read_text()
    section = re.search(r"(?ms)^\[project\]\n(.*?)(?=^\[|\Z)", text)
    if section is None:
        raise RuntimeError("pyproject.toml has no [project] section")
    body = re.sub(r'(?m)^version\s*=\s*["\'][^"\']*["\']', f'version = "{version}"',
                  section[1], count=1)
    path.write_text(text[:section.start(1)] + body + text[section.end(1):])
    if tomllib.loads(path.read_text())["project"]["version"] != version:
        raise RuntimeError("the version line wasn't updated")


def main(
    *,
    lock_command: Sequence[str] = ("uv", "lock"),
    pr_command: Sequence[str] = ("gh", "pr", "create"),
    ask: Callable[[str], str] = input,
) -> int:
    top = git("rev-parse", "--show-toplevel").stdout.strip()
    if top:
        os.chdir(top)

    failure = precondition_failure()
    if failure:
        return refuse(failure)

    tag = last_tag()
    directory, categories = towncrier_settings()
    notes, stray = notes_by_category(directory, categories)
    if stray:
        listing = "\n".join(f"  {path}" for path in stray)
        return refuse(
            f"these files under {directory}/ aren't release notes, and the release commit would delete them:\n"
            f"{listing}\n"
            f"  rename each to <issue>.<category>.md with a category from pyproject.toml, or remove it"
        )
    total, unnoted = merges_since(tag, directory)

    releasable = [c for c in notes if c != "none"]
    if not releasable and not unnoted:
        if total:
            print(f"Nothing to release: {plural(total, 'change')} merged since {tag}, all marked none.")
        else:
            print(f"Nothing to release: nothing has merged since {tag}.")
        return 0

    version, reason = propose(notes, unnoted)
    proposed = ".".join(map(str, version))
    try:
        draft = build_draft(proposed, directory, notes)
        print(f"Proposed version: {proposed} ({reason})")
        if unnoted:
            print("Merged with no release note: " + ", ".join(f"#{n}" for n in unnoted))
        print()
        if draft:
            print(draft)
            print()
        confirmed = ask_version(ask, proposed)
        branch = f"release/v{confirmed}"
        local = git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}")
        remote = git("ls-remote", "--exit-code", "--heads", "origin", branch)
        if local.returncode == 0 or remote.returncode == 0:
            return refuse(f"{branch} already exists, close its pull request or delete the branch first")
        with tempfile.TemporaryDirectory() as tmp:
            final = edit(draft, Path(tmp))
            return cut_release(confirmed, branch, final, directory,
                               Path(tmp), lock_command, pr_command)
    except Abort as stop:
        if str(stop):
            print(f"✗ {stop}")
        print("Stopped, nothing was changed.")
        return 1


def cut_release(
    version: str,
    branch: str,
    body: str,
    directory: str,
    workdir: Path,
    lock_command: Sequence[str],
    pr_command: Sequence[str],
) -> int:
    created = False
    removed_notes = False

    def roll_back(step: str, detail: str = "") -> int:
        """Undo exactly what this run wrote, then leave the branch behind.

        The version bump, the relock, and the staged note deletions are
        uncommitted here, and a plain switch would carry them onto `main`. The
        restore names its paths rather than running `git reset --hard`, because
        the editor session sits between the clean-tree check and now, and a
        tracked file edited in another window would be lost to a reset. `uv.lock`
        and `changes/` are named only when git knows them: git refuses the whole
        command over a pathspec that matches nothing.
        """
        paths = ["pyproject.toml"]
        if git("cat-file", "-e", "HEAD:uv.lock").returncode == 0:
            paths.append("uv.lock")
        if removed_notes:
            paths.append(directory + "/")
        git("restore", "--staged", "--worktree", "--source=HEAD", "--", *paths)
        git("switch", "main")
        if created:
            git("branch", "-D", branch)
        print(f"✗ {step} failed{': ' + detail if detail else ''}")
        print("Stopped, nothing was changed.")
        return 1

    if git("switch", "-c", branch).returncode != 0:
        return roll_back("creating the branch")
    created = True

    try:
        set_version(version)
    except RuntimeError as problem:
        return roll_back("setting the version", str(problem))

    locked = run(*lock_command)
    if locked.returncode != 0:
        return roll_back("relocking", locked.stderr.strip())

    if git("ls-files", directory).stdout.strip():
        if git("rm", "-r", "-q", directory).returncode != 0:
            return roll_back("removing the notes")
        removed_notes = True

    message = workdir / "COMMIT_MESSAGE"
    message.write_text(f"chore(release): cut {version}\n\n{body}\n")
    git("add", "pyproject.toml", "uv.lock")
    committed = git("commit", "--cleanup=verbatim", "-F", str(message))
    if committed.returncode != 0:
        return roll_back("committing", committed.stderr.strip())

    push = ["git", "push", "-u", "origin", branch]
    pushed = run(*push)
    if pushed.returncode != 0:
        git("switch", "main")
        print(f"✗ pushing {branch} failed: {pushed.stderr.strip()}")
        print(f"The release commit is on {branch}. Run it again: {' '.join(push)}")
        return 1

    opening = [*pr_command, "--base", "main", "--head", branch, "--fill"]
    opened = run(*opening)
    if opened.returncode != 0:
        git("switch", "main")
        print(f"✗ opening the pull request failed: {opened.stderr.strip()}")
        print(f"The release commit is pushed on {branch}. Run it again: {' '.join(opening)}")
        return 1

    git("switch", "main")
    print(f"Release pull request opened: {opened.stdout.strip()}. Merge it once its checks pass.")
    print(f"To change the release notes, amend the commit on {branch} with --cleanup=verbatim and force-push it.")
    print("Editing the pull request's description doesn't change the release.")
    # A release PR gets no review panel, so its `review` check needs a person's
    # sign-off. It's printed, never run: a scripted sign-off would let an agent
    # that runs this script cut and merge a release with nobody involved. The
    # switch comes first because the script ends on main, where the sign-off
    # refuses to run.
    print("Before merging, sign off on the release commit from your own terminal:")
    print(f"  git switch {branch}")
    print("  wfctl review sign-off")
    return 0


if __name__ == "__main__":
    sys.exit(main())
