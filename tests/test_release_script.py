"""The release script: one run proposes a version, drafts the notes, and opens a pull request.

The script is a standalone file under `.github/scripts/`, loaded by path and run
against scratch repositories with a bare `origin`. `uv lock`, `gh pr create`, and
the editor are replaced by stubs that record what they were given, so the push
runs for real and nothing touches the network.
"""
from __future__ import annotations

import importlib.util
import shlex
import subprocess
import sys
import textwrap
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

from tests.conftest import init_release_repo

SCRIPT = Path(__file__).resolve().parent.parent / ".github" / "scripts" / "release.py"

LOCK_STUB = textwrap.dedent("""
    import pathlib, sys
    record, mode = pathlib.Path(sys.argv[1]), sys.argv[2]
    record.write_text((record.read_text() if record.exists() else "") + "lock\\n")
    if mode == "fail":
        sys.stderr.write("lock failed\\n")
        sys.exit(1)
    lock = pathlib.Path("uv.lock")
    lock.write_text(lock.read_text() + "# relocked\\n")
""")

PR_STUB = textwrap.dedent("""
    import pathlib, sys
    pathlib.Path(sys.argv[1]).write_text(" ".join(sys.argv[3:]))
    if sys.argv[2] == "fail":
        sys.stderr.write("gh failed\\n")
        sys.exit(1)
    print("https://example.test/pull/7")
""")

# keep leaves the draft as it was, append adds a closing line, empty saves
# nothing, and fail exits non-zero the way vim's `:cq` does. Every mode records
# what the file held when the editor opened it.
EDITOR_STUB = textwrap.dedent("""
    import pathlib, sys
    mode, saw, path = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
    saw.write_text(path.read_text())
    if mode == "append":
        path.write_text(path.read_text() + "\\nWritten by hand.\\n")
    elif mode == "empty":
        path.write_text("")
    elif mode == "fail":
        sys.exit(1)
""")


def load_release() -> ModuleType:
    spec = importlib.util.spec_from_file_location("release", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str, check: bool = True) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args],
                          check=check, capture_output=True, text=True)
    return done.stdout.strip()


def merge_pr(repo: Path, number: int, branch: str, notes: dict[str, str] | None = None) -> None:
    """Merge a branch into `main` the way GitHub does, and push `main`."""
    git(repo, "checkout", "-b", branch, "main")
    for name, text in (notes or {}).items():
        (repo / "changes").mkdir(exist_ok=True)
        (repo / "changes" / name).write_text(text)
    (repo / f"{branch}.txt").write_text(branch)
    git(repo, "add", "-A")
    git(repo, "commit", "-m", f"work on {branch}")
    git(repo, "checkout", "main")
    git(repo, "merge", "--no-ff", "-m", f"Merge pull request #{number} from aamarin/{branch}", branch)
    git(repo, "push", "origin", "main")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = init_release_repo(tmp_path / "repo", "0.23.0")
    (path / "uv.lock").write_text('version = "0.23.0"\n')
    git(path, "add", "uv.lock")
    git(path, "commit", "-m", "lock")
    git(path, "tag", "v0.23.0")
    git(path, "push", "origin", "main")
    return path


class Release:
    """One run of the script from `repo`, with the stubs' records kept to read.

    Calling it returns the exit code and what the script printed. `lock_record`
    and `pr_record` hold what the stub commands were given, and `saw` holds what
    the draft contained when the editor opened it.
    """

    def __init__(
        self,
        repo: Path,
        stubs: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self.repo, self.stubs = repo, stubs
        self.monkeypatch, self.capsys = monkeypatch, capsys
        self.lock_record = stubs / "lock.txt"
        self.pr_record = stubs / "pr.txt"
        self.saw = stubs / "saw.txt"

    def __call__(
        self,
        answers: list[str] | None = None,
        editor: str = "keep",
        lock: str = "ok",
        pr: str = "ok",
        ask: Callable[[str], str] | None = None,
    ) -> tuple[int, str]:
        queue = iter([""] if answers is None else answers)
        self.monkeypatch.setenv(
            "GIT_EDITOR",
            f"{shlex.quote(sys.executable)} {self.stubs / 'editor.py'} {editor} {self.saw}",
        )
        self.monkeypatch.chdir(self.repo)
        code = load_release().main(
            lock_command=[sys.executable, str(self.stubs / "lock.py"), str(self.lock_record), lock],
            pr_command=[sys.executable, str(self.stubs / "pr.py"), str(self.pr_record), pr],
            ask=ask or (lambda prompt: next(queue)),
        )
        return code, self.capsys.readouterr().out


@pytest.fixture
def release(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> Release:
    stubs = tmp_path / "stubs"
    stubs.mkdir()
    for name, body in (("lock.py", LOCK_STUB), ("pr.py", PR_STUB), ("editor.py", EDITOR_STUB)):
        (stubs / name).write_text(body)
    return Release(repo, stubs, monkeypatch, capsys)


def nothing_changed(repo: Path) -> None:
    """On `main`, a clean tree, and no release branch anywhere."""
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert git(repo, "status", "--porcelain") == ""
    assert git(repo, "branch", "--list", "release/*") == ""
    assert git(repo, "ls-remote", "--heads", "origin", "release/*") == ""


# --- the proposal and the draft ----------------------------------------------


def test_a_behaviour_change_and_a_fix_propose_a_minor(repo: Path, release: Release) -> None:
    merge_pr(repo, 1, "one", {"1.change.md": "Releases are scripted.\n"})
    merge_pr(repo, 2, "two", {"2.fix.md": "A bug is fixed.\n"})

    code, out = release()

    assert code == 0
    assert "Proposed version: 0.24.0 (minor: 1 behaviour change)" in out


def test_fixes_and_none_notes_propose_a_patch(repo: Path, release: Release) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})
    merge_pr(repo, 2, "two", {"2.none.md": "Internal only.\n"})

    code, out = release()

    assert code == 0
    assert "Proposed version: 0.23.1 (patch: 1 fix)" in out


def test_none_notes_leave_no_section_and_no_line_in_the_draft(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})
    merge_pr(repo, 2, "two", {"2.none.md": "Internal only.\n"})

    _, out = release()

    assert "Nothing to notice" not in out
    assert "Internal only." not in out


def test_the_draft_drops_towncrier_title_and_keeps_the_sections(
    repo: Path, release: Release
) -> None:
    """The release page already shows the version, so the title is dropped, and
    the draft doesn't depend on which version gets confirmed."""
    merge_pr(repo, 1, "one", {"1.change.md": "Releases are scripted.\n"})

    _, out = release()

    assert not any(line.startswith("# ") for line in out.splitlines())
    assert "## Behaviour changes" in out
    assert "- Releases are scripted. (#1)" in out


def test_two_notes_with_one_sentence_render_as_one_line_linking_both_issues(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"601.fix.md": "Same sentence.\n"})
    merge_pr(repo, 2, "two", {"602.fix.md": "Same sentence.\n"})

    _, out = release()

    assert out.count("Same sentence.") == 1
    assert "(#601, #602)" in out


# --- merges with no note -----------------------------------------------------


def test_a_merge_that_added_no_note_is_listed_before_the_draft(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.change.md": "Releases are scripted.\n"})
    merge_pr(repo, 2, "two")

    _, out = release()

    assert "Merged with no release note: #2" in out
    assert out.index("Merged with no release note") < out.index("## Behaviour changes")


def test_a_merge_whose_branch_carries_a_plus_note_is_not_listed(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "bump-ruff", {"+bump-ruff.fix.md": "Ruff is updated.\n"})

    _, out = release()

    assert "Merged with no release note" not in out


def test_a_merge_of_main_into_a_branch_is_not_read_as_a_pull_request(
    repo: Path, release: Release
) -> None:
    """Only `Merge pull request #<n> from <owner>/<branch>` is a pull request.
    Merging main into a branch leaves a merge commit with another subject."""
    git(repo, "checkout", "-b", "topic")
    (repo / "changes").mkdir()
    (repo / "changes" / "3.fix.md").write_text("A bug is fixed.\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "topic work")
    git(repo, "checkout", "main")
    (repo / "elsewhere.txt").write_text("y")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "main moved")
    git(repo, "checkout", "topic")
    git(repo, "merge", "--no-edit", "main")
    git(repo, "checkout", "main")
    git(repo, "merge", "--no-ff", "-m", "Merge pull request #3 from aamarin/topic", "topic")
    git(repo, "push", "origin", "main")

    _, out = release()

    assert "Merged with no release note" not in out


def test_a_merge_that_added_two_notes_counts_as_having_one(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "First.\n", "2.fix.md": "Second.\n"})

    _, out = release()

    assert "Merged with no release note" not in out


# --- nothing to release ------------------------------------------------------


def test_only_none_notes_with_every_merge_noted_releases_nothing(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.none.md": "Internal.\n"})
    merge_pr(repo, 2, "two", {"2.none.md": "Internal too.\n"})

    code, out = release()

    assert code == 0
    assert "Nothing to release: 2 changes merged since v0.23.0, all marked none." in out
    nothing_changed(repo)


def test_no_notes_with_unnoted_merges_still_proposes_a_patch_and_opens_an_empty_draft(
    repo: Path, release: Release
) -> None:
    """A merge with no note is never read as `none`. Dropping towncrier's
    "No significant changes." leaves the draft empty, so Andre writes those
    merges into it by hand and the line can't reach a release page."""
    merge_pr(repo, 1, "one")
    merge_pr(repo, 2, "two")

    code, out = release(editor="append")

    assert code == 0
    assert "Proposed version: 0.23.1 (patch: no notes yet, and 2 merges with no release note to read first)" in out
    assert "Merged with no release note: #1, #2" in out
    assert "No significant changes." not in out
    assert release.saw.read_text() == ""
    assert git(repo, "log", "-1", "--format=%b", "origin/release/v0.23.1") == "Written by hand."


# --- the prompts and the refusals --------------------------------------------


def test_a_typed_version_is_used_for_the_commit_and_the_branch(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})

    code, _ = release(answers=["0.30.0"])

    assert code == 0
    assert git(repo, "log", "-1", "--format=%s", "origin/release/v0.30.0") == "chore(release): cut 0.30.0"


def test_a_version_not_above_the_current_one_is_asked_again(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})

    code, out = release(answers=["0.23.0", "banana", "0.24.0"])

    assert code == 0
    assert "isn't higher than the current version" in out
    assert "isn't a version" in out
    assert git(repo, "ls-remote", "--heads", "origin", "release/v0.24.0")


def test_not_on_main_refuses_and_changes_nothing(repo: Path, release: Release) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})
    git(repo, "checkout", "-b", "topic")

    code, out = release()

    assert code == 1
    assert "releases are cut from main, and this is topic" in out
    assert git(repo, "branch", "--list", "release/*") == ""


def test_a_dirty_tree_refuses_and_changes_nothing(repo: Path, release: Release) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})
    (repo / "uv.lock").write_text("edited\n")

    code, out = release()

    assert code == 1
    assert "the working tree has changes, commit or stash them first" in out
    assert (repo / "uv.lock").read_text() == "edited\n"
    assert git(repo, "branch", "--list", "release/*") == ""


def test_a_main_behind_origin_refuses_and_changes_nothing(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})
    git(repo, "reset", "--hard", "HEAD~1")

    code, out = release()

    assert code == 1
    assert "main isn't at origin/main, run git pull --ff-only" in out
    nothing_changed(repo)


def test_no_release_tag_refuses_and_changes_nothing(repo: Path, release: Release) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})
    git(repo, "tag", "-d", "v0.23.0")

    code, out = release()

    assert code == 1
    assert "no release tag found to compare against" in out
    nothing_changed(repo)


def test_end_of_input_at_the_version_prompt_changes_nothing(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})

    def closed(prompt: str) -> str:
        raise EOFError

    code, out = release(ask=closed)

    assert code == 1
    assert "Stopped, nothing was changed." in out
    nothing_changed(repo)


def test_an_empty_saved_draft_changes_nothing(repo: Path, release: Release) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})

    code, out = release(editor="empty")

    assert code == 1
    assert "Stopped, nothing was changed." in out
    nothing_changed(repo)
    assert (repo / "changes" / "1.fix.md").exists()


def test_an_editor_that_exits_non_zero_changes_nothing(repo: Path, release: Release) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})

    code, out = release(editor="fail")

    assert code == 1
    assert "Stopped, nothing was changed." in out
    nothing_changed(repo)


def test_a_release_branch_that_exists_locally_is_refused_by_name(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})
    git(repo, "branch", "release/v0.23.1")

    code, out = release()

    assert code == 1
    assert "release/v0.23.1 already exists, close its pull request or delete the branch first" in out
    assert git(repo, "ls-remote", "--heads", "origin", "release/v0.23.1") == ""


def test_a_release_branch_that_exists_only_on_origin_is_refused_by_name(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})
    git(repo, "push", "origin", "main:refs/heads/release/v0.23.1")

    code, out = release()

    assert code == 1
    assert "release/v0.23.1 already exists" in out
    assert git(repo, "branch", "--list", "release/*") == ""


# --- the release commit ------------------------------------------------------


def test_the_pushed_branch_holds_one_commit_that_carries_the_release(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.change.md": "Releases are scripted.\n"})
    merge_pr(repo, 2, "two", {"2.fix.md": "A bug is fixed.\n"})
    main_before = git(repo, "rev-parse", "origin/main")

    code, out = release(editor="append")

    assert code == 0
    branch = "origin/release/v0.24.0"
    assert git(repo, "rev-list", "--count", f"main..{branch}") == "1"
    assert git(repo, "log", "-1", "--format=%s", branch) == "chore(release): cut 0.24.0"
    body = git(repo, "log", "-1", "--format=%b", branch)
    assert body.startswith("## Behaviour changes")
    assert "- Releases are scripted. (#1)" in body
    assert body.endswith("Written by hand.")
    assert 'version = "0.24.0"' in git(repo, "show", f"{branch}:pyproject.toml")
    assert "# relocked" in git(repo, "show", f"{branch}:uv.lock")
    assert git(repo, "ls-tree", "-r", "--name-only", branch, "--", "changes") == ""
    assert release.pr_record.read_text() == "--base main --head release/v0.24.0 --fill"
    assert "Release pull request opened: https://example.test/pull/7." in out
    assert "amend the commit on release/v0.24.0 and force-push it" in out
    assert "doesn't change the release" in out
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert git(repo, "rev-parse", "origin/main") == main_before
    assert git(repo, "rev-parse", "main") == main_before


def test_the_commit_body_equals_the_draft_when_the_editor_changes_nothing(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.change.md": "Releases are scripted.\n"})

    release()

    drafted = release.saw.read_text().strip()
    assert git(repo, "log", "-1", "--format=%b", "origin/release/v0.24.0") == drafted


def test_a_failing_lock_restores_the_paths_it_wrote_and_deletes_the_branch(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.change.md": "Releases are scripted.\n"})

    code, out = release(lock="fail")

    assert code == 1
    assert "relocking failed" in out
    nothing_changed(repo)
    assert 'version = "0.23.0"' in (repo / "pyproject.toml").read_text()
    assert (repo / "changes" / "1.change.md").exists()


def test_a_failing_lock_with_no_tracked_notes_still_restores_cleanly(
    repo: Path, release: Release
) -> None:
    """Git refuses a whole `restore` over a pathspec that matches nothing, and
    `changes/` is gone after every release. Naming it only when the notes were
    removed is what keeps the rollback from failing on top of the failure."""
    merge_pr(repo, 1, "one")

    code, _ = release(editor="append", lock="fail")

    assert code == 1
    nothing_changed(repo)
    assert 'version = "0.23.0"' in (repo / "pyproject.toml").read_text()


def test_a_failing_push_leaves_the_branch_and_prints_the_command(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})
    git(repo, "remote", "set-url", "--push", "origin", str(repo.parent / "nowhere.git"))

    code, out = release()

    assert code == 1
    assert "git push -u origin release/v0.23.1" in out
    assert git(repo, "branch", "--list", "release/v0.23.1")
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"


def test_a_failing_pull_request_leaves_the_pushed_branch_and_prints_the_command(
    repo: Path, release: Release
) -> None:
    merge_pr(repo, 1, "one", {"1.fix.md": "A bug is fixed.\n"})

    code, out = release(pr="fail")

    assert code == 1
    assert "--base main --head release/v0.23.1 --fill" in out
    assert git(repo, "ls-remote", "--heads", "origin", "release/v0.23.1")
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
