"""The release note check: a branch that makes a change commits a note for it.

The check is a standalone script under `.github/scripts/`, so it is loaded by
path and run against scratch repositories built by `init_release_repo`.
"""
from __future__ import annotations

import importlib.util
import subprocess
import tomllib
from pathlib import Path
from types import ModuleType

import pytest

from tests.conftest import init_release_repo

SCRIPT = Path(__file__).resolve().parent.parent / ".github" / "scripts" / "check_release_note.py"


@pytest.fixture(autouse=True)
def _ci_branch_variables_are_not_ours(monkeypatch: pytest.MonkeyPatch) -> None:
    """GitHub sets both variables for every step of a pull request run.

    That includes this suite's own step, so without clearing them every test
    here would read the pull request's branch name instead of the name of its
    scratch repository's branch, and pass or fail on CI for the wrong reason.
    """
    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
    monkeypatch.delenv("GITHUB_REF_NAME", raising=False)


def load_check() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_release_note", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args],
                          check=True, capture_output=True, text=True)
    return done.stdout.strip()


def test_release_repo_helper_builds_a_repository_the_check_can_compare_against(
    tmp_path: Path,
) -> None:
    """The helper both new test files rely on has to produce what they assume.

    `origin/main` has to exist for the check's merge base, and the four
    categories have to be copied across, or every later test would be written
    against a repository unlike the real one.
    """
    repo = init_release_repo(tmp_path / "repo", "0.23.0")

    assert git(repo, "rev-parse", "--verify", "origin/main")
    table = tomllib.loads((repo / "pyproject.toml").read_text())
    kinds = [t["directory"] for t in table["tool"]["towncrier"]["type"]]
    assert kinds == ["change", "addition", "fix", "none"]
    assert table["project"]["version"] == "0.23.0"


def start_branch(repo: Path, name: str, notes: dict[str, str] | None = None) -> Path:
    """Branch off `main` and commit `notes`, a map of file name to content."""
    git(repo, "checkout", "-b", name)
    for filename, text in (notes or {}).items():
        target = repo / "changes" / filename
        target.parent.mkdir(exist_ok=True)
        target.write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "--allow-empty", "-m", f"work on {name}")
    return repo


def run_check(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> tuple[int, str]:
    monkeypatch.chdir(repo)
    code = load_check().main()
    return code, capsys.readouterr().out


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return init_release_repo(tmp_path / "repo", "0.23.0")


# --- a note for the branch's own issue ---------------------------------------


def test_a_branch_with_no_note_fails_and_says_which_file_to_add(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The message is the only instruction a contributor gets, so it names the
    file, the four categories, and the command that creates it (FR-007)."""
    start_branch(repo, "571-release-automation")

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "no release note for #571" in out
    assert "changes/571.<category>.md" in out
    for category in ("change", "addition", "fix", "none"):
        assert category in out
    assert 'uv run towncrier create 571.change.md --content' in out


def test_a_branch_with_a_note_for_its_issue_passes(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    start_branch(repo, "571-release-automation", {"571.change.md": "Releases are scripted.\n"})

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 0
    assert "✓ release note for #571: changes/571.change.md" in out


def test_a_stacked_branch_needs_a_note_for_its_own_issue_not_its_parents(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A child's diff from `main` includes its parent's note, so counting any
    note would let a child skip its own."""
    start_branch(repo, "571-parent", {"571.change.md": "Parent.\n"})
    start_branch(repo, "580-child")

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "no release note for #580" in out


def test_a_branch_with_no_issue_passes_with_a_plus_note(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    start_branch(repo, "bump-ruff", {"+bump-ruff.fix.md": "Ruff is on 0.15.4.\n"})

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 0


def test_a_branch_with_no_issue_and_no_note_fails(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    start_branch(repo, "bump-ruff")

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "no release note on this branch" in out
    assert "changes/+<what-changed>.<category>.md" in out


def test_main_itself_has_nothing_to_check(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 0
    assert "on main, nothing to check" in out


def test_a_missing_changes_folder_counts_as_no_notes_not_an_error(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Git keeps no empty folder and every release empties `changes/`, so the
    ordinary state right after a release is that the folder does not exist."""
    start_branch(repo, "572-something")
    assert not (repo / "changes").exists()

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "no release note for #572" in out


# --- notes that are malformed ------------------------------------------------


def test_a_note_naming_a_category_that_does_not_exist_is_refused(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    start_branch(repo, "571-x", {"571.feature.md": "Something.\n"})

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert 'changes/571.feature.md names the category "feature", which doesn\'t exist' in out
    assert "use change, addition, fix, or none" in out


def test_a_file_that_is_not_a_note_name_is_refused(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    start_branch(repo, "571-x", {"571.change.md": "Fine.\n", "notes.md": "stray\n"})

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "changes/notes.md isn't a release note name" in out


def test_a_note_still_holding_towncrier_placeholder_text_is_unwritten(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`towncrier create` opens an editor on this text. Leaving it in would put
    "Add your info here" on a release page."""
    start_branch(repo, "571-x", {"571.change.md": "Add your info here\n"})

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "changes/571.change.md has no release note written in it" in out
    assert 'replace "Add your info here" with what a user of wfctl will notice' in out


@pytest.mark.parametrize("content", ["", "  \n\n"])
def test_an_empty_or_whitespace_note_says_the_file_is_empty(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    content: str,
) -> None:
    start_branch(repo, "571-x", {"571.change.md": content})

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "has no release note written in it" in out
    assert "the file is empty" in out


def test_every_finding_prints_before_the_check_exits(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A contributor with two bad files should fix both in one pass, not learn
    about the second after the first is fixed."""
    start_branch(repo, "571-x", {"571.feature.md": "A.\n", "notes.md": "B.\n"})

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "names the category" in out
    assert "isn't a release note name" in out


@pytest.mark.parametrize("name", ["571.change.md", "571.change.2.md", "+thing.fix.md"])
def test_all_three_note_name_forms_are_accepted(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    name: str,
) -> None:
    branch = "thing" if name.startswith("+") else "571-x"
    start_branch(repo, branch, {name: "Something.\n"})

    code, _ = run_check(repo, monkeypatch, capsys)

    assert code == 0


def test_a_plus_note_does_not_satisfy_a_branch_that_names_an_issue(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The `+` form is for work with no issue. On `571-x` it would let a branch
    skip the note the issue's release line is built from."""
    start_branch(repo, "571-x", {"+thing.fix.md": "Something.\n"})

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "no release note for #571" in out


# --- the release branch rule -------------------------------------------------


def release_branch(repo: Path, name: str, version: str) -> None:
    start_branch(repo, name)
    text = (repo / "pyproject.toml").read_text()
    (repo / "pyproject.toml").write_text(text.replace('version = "0.23.0"', f'version = "{version}"'))
    git(repo, "commit", "-am", "chore(release): bump")


def test_a_release_branch_that_raises_the_version_to_its_name_needs_no_note(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    release_branch(repo, "release/v0.24.0", "0.24.0")

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 0
    assert "✓ release branch for 0.24.0, no note needed" in out


def test_a_release_branch_whose_version_differs_from_its_name_fails_naming_both(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    release_branch(repo, "release/v0.24.0", "0.23.1")

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "release/v0.24.0 carries version 0.23.1 in pyproject.toml" in out


def test_a_release_branch_that_leaves_the_version_alone_is_not_exempt(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A branch named for the current version matches its own name without
    raising anything, so the name alone would let any branch skip the note."""
    start_branch(repo, "release/v0.23.0")

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "release/v0.23.0 carries version 0.23.0, and main already carries 0.23.0" in out
    assert "needs no note only when it raises the version" in out


def test_versions_compare_as_integers_so_0_10_0_is_higher_than_0_9_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = init_release_repo(tmp_path / "ten", "0.9.0")
    start_branch(repo, "release/v0.10.0")
    text = (repo / "pyproject.toml").read_text()
    (repo / "pyproject.toml").write_text(text.replace('version = "0.9.0"', 'version = "0.10.0"'))
    git(repo, "commit", "-am", "chore(release): bump")

    code, _ = run_check(repo, monkeypatch, capsys)

    assert code == 0


def test_a_branch_that_only_starts_with_release_follows_the_ordinary_rules(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    start_branch(repo, "release/foo")

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "no release note on this branch" in out


# --- how the check finds its inputs ------------------------------------------


def test_the_branch_name_comes_from_github_head_ref_on_a_detached_head(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`actions/checkout` leaves a pull request on a detached merge commit, so
    `git rev-parse --abbrev-ref HEAD` answers "HEAD" there."""
    start_branch(repo, "scratch", {"571.change.md": "Something.\n"})
    git(repo, "checkout", "--detach")
    monkeypatch.setenv("GITHUB_HEAD_REF", "571-release-automation")

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 0
    assert "#571" in out


def test_an_empty_github_head_ref_counts_as_unset(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """GitHub sets it to the empty string on push runs."""
    start_branch(repo, "571-x", {"571.change.md": "Something.\n"})
    monkeypatch.setenv("GITHUB_HEAD_REF", "")

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 0
    assert "#571" in out


def test_the_branch_name_falls_back_to_github_ref_name_when_head_is_detached(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    start_branch(repo, "scratch", {"580.fix.md": "Something.\n"})
    git(repo, "checkout", "--detach")
    monkeypatch.setenv("GITHUB_REF_NAME", "580-thing")

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 0
    assert "#580" in out


def test_no_main_to_compare_against_is_a_finding_not_a_crash(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    start_branch(repo, "571-x", {"571.change.md": "Something.\n"})
    git(repo, "branch", "-m", "main", "trunk")
    git(repo, "remote", "remove", "origin")

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "can't find main to compare this branch against" in out
    assert "run git fetch origin main, then check again" in out


def test_a_branch_that_merged_main_in_is_judged_only_on_what_it_added(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Another branch's note arriving through a merge of `main` is not this
    branch's note."""
    start_branch(repo, "571-x")
    git(repo, "checkout", "main")
    (repo / "changes").mkdir()
    (repo / "changes" / "999.change.md").write_text("Someone else's.\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "someone else merged")
    git(repo, "push", "origin", "main")
    git(repo, "checkout", "571-x")
    git(repo, "merge", "--no-edit", "main")

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 1
    assert "no release note for #571" in out


def test_a_renamed_note_counts_as_added(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without `--no-renames`, git reports a moved note as a rename and the
    `A` filter drops it, so the branch would read as having added nothing."""
    git(repo, "checkout", "main")
    (repo / "changes").mkdir()
    (repo / "changes" / "999.change.md").write_text("Same text in both names.\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "note on main")
    git(repo, "push", "origin", "main")
    git(repo, "checkout", "-b", "571-x")
    git(repo, "mv", "changes/999.change.md", "changes/571.change.md")
    git(repo, "commit", "-m", "rename")

    code, out = run_check(repo, monkeypatch, capsys)

    assert code == 0
