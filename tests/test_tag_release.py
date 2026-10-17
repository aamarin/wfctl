"""The `tag` job in ci.yml, run against a scratch repository and a stub `gh`.

The job used to be shell inside the workflow, which nothing could run before the
first real release. The cases here are the ones that decide whether a release
ships: the lookup of the release commit, the checks made before anything is
tagged, and the retry when the tag exists and the release does not.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path
from types import ModuleType

import pytest

from tests.conftest import init_release_repo

SCRIPT = Path(__file__).resolve().parent.parent / ".github" / "scripts" / "tag_release.py"

# Records each call. `view` exits 0 when the release exists, and `create` copies
# the notes file it was given, since the script deletes it afterwards.
GH_STUB = textwrap.dedent("""
    import pathlib, sys
    record, released, create = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    args = sys.argv[4:]
    record.write_text((record.read_text() if record.exists() else "") + " ".join(args[:3]) + "\\n")
    if args[0:2] == ["release", "view"]:
        sys.exit(0 if released == "released" else 1)
    if args[0:2] == ["release", "create"]:
        if create == "fail":
            sys.stderr.write("gh failed\\n")
            sys.exit(1)
        pathlib.Path(str(record) + ".notes").write_text(pathlib.Path(args[args.index("--notes-file") + 1]).read_text())
""")


def load_tag_release() -> ModuleType:
    spec = importlib.util.spec_from_file_location("tag_release", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args],
                          check=True, capture_output=True, text=True)
    return done.stdout.strip()


def cut(repo: Path, version: str, body: str = "## Fixes\n\n- A bug is fixed.", subject: str | None = None,
        file_version: str | None = None) -> None:
    """Commit a version bump the way the release script does, and push `main`."""
    path = repo / "pyproject.toml"
    path.write_text(path.read_text().replace('version = "0.23.0"', f'version = "{file_version or version}"'))
    message = f"{subject or f'chore(release): cut {version}'}\n\n{body}\n" if body else f"{subject or f'chore(release): cut {version}'}\n"
    git(repo, "add", "pyproject.toml")
    git(repo, "commit", "--cleanup=verbatim", "-m", message)
    git(repo, "push", "origin", "main")


class Tagger:
    """One run of the job from `repo`. Calling it returns the exit code and output."""

    def __init__(self, repo: Path, stubs: Path, monkeypatch: pytest.MonkeyPatch,
                 capsys: pytest.CaptureFixture[str]) -> None:
        self.repo, self.stubs = repo, stubs
        self.monkeypatch, self.capsys = monkeypatch, capsys
        self.record = stubs / "gh.txt"

    def __call__(self, released: bool = False, create: str = "ok") -> tuple[int, str]:
        self.monkeypatch.chdir(self.repo)
        code = load_tag_release().main(gh=[
            sys.executable, str(self.stubs / "gh.py"), str(self.record),
            "released" if released else "missing", create,
        ])
        return code, self.capsys.readouterr().out

    def calls(self) -> list[str]:
        return self.record.read_text().splitlines() if self.record.exists() else []

    def notes(self) -> str:
        return Path(str(self.record) + ".notes").read_text()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = init_release_repo(tmp_path / "repo", "0.23.0")
    git(path, "tag", "-a", "v0.23.0", "-m", "v0.23.0")
    git(path, "push", "origin", "v0.23.0")
    return path


@pytest.fixture
def tagger(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
           capsys: pytest.CaptureFixture[str]) -> Tagger:
    stubs = tmp_path / "stubs"
    stubs.mkdir()
    (stubs / "gh.py").write_text(GH_STUB)
    return Tagger(repo, stubs, monkeypatch, capsys)


def origin_tags(repo: Path) -> str:
    return git(repo, "ls-remote", "--tags", "origin", "v0.24.0")


def test_a_version_already_tagged_and_released_does_nothing(repo: Path, tagger: Tagger) -> None:
    code, out = tagger(released=True)

    assert code == 0
    assert "v0.23.0 already released" in out
    assert tagger.calls() == ["release view v0.23.0"]


def test_a_new_version_is_tagged_pushed_and_released_with_the_commit_body(
    repo: Path, tagger: Tagger
) -> None:
    cut(repo, "0.24.0", body="## Fixes\n\n- A bug is fixed.")

    code, _ = tagger()

    assert code == 0
    assert origin_tags(repo) != ""
    assert tagger.calls() == ["release view v0.24.0", "release create v0.24.0"]
    assert tagger.notes().strip() == "## Fixes\n\n- A bug is fixed."


def test_a_tag_with_no_release_is_released_without_tagging_again(
    repo: Path, tagger: Tagger
) -> None:
    """The retry the job's two separate checks exist for: the push worked, the
    release call failed, and the next run has to finish the release."""
    cut(repo, "0.24.0")
    first, _ = tagger(create="fail")
    assert first == 1
    assert origin_tags(repo) != ""

    second, out = tagger()

    assert second == 0
    assert "v0.24.0 already tagged" in out
    assert tagger.calls()[-1] == "release create v0.24.0"


def test_a_failing_release_call_is_an_error_not_a_pass(repo: Path, tagger: Tagger) -> None:
    cut(repo, "0.24.0")

    code, out = tagger(create="fail")

    assert code == 1
    assert "::error::couldn't create the release for v0.24.0: gh failed" in out


def test_a_bumped_version_with_no_release_commit_tags_nothing(repo: Path, tagger: Tagger) -> None:
    cut(repo, "0.24.0", subject="chore: bump the version")

    code, out = tagger()

    assert code == 1
    assert "no commit with the subject chore(release): cut 0.24.0" in out
    assert origin_tags(repo) == ""
    assert not any("create" in call for call in tagger.calls())


def test_a_release_commit_carrying_another_version_tags_nothing(repo: Path, tagger: Tagger) -> None:
    """The subject says 0.24.0, but the file it committed says 0.23.5. The
    subject alone would tag the wrong release."""
    cut(repo, "0.24.0", file_version="0.23.5")
    path = repo / "pyproject.toml"
    path.write_text(path.read_text().replace("0.23.5", "0.24.0"))
    git(repo, "commit", "-am", "bump again")

    code, out = tagger()

    assert code == 1
    assert "the commit found for 0.24.0 carries version 0.23.5" in out
    assert origin_tags(repo) == ""


def test_a_release_commit_with_an_empty_body_tags_nothing(repo: Path, tagger: Tagger) -> None:
    cut(repo, "0.24.0", body="")

    code, out = tagger()

    assert code == 1
    assert "the release commit for 0.24.0 has no release notes in its body" in out
    assert origin_tags(repo) == ""


def test_the_merge_of_the_release_pull_request_does_not_hide_the_release_commit(
    repo: Path, tagger: Tagger
) -> None:
    """Merge commits here carry the pull request's title in their body, so the
    merge matches the search for the subject too. Without `--no-merges` the
    lookup returned the merge, failed the subject check, and stopped every release."""
    git(repo, "checkout", "-b", "release/v0.24.0")
    cut_path = repo / "pyproject.toml"
    cut_path.write_text(cut_path.read_text().replace("0.23.0", "0.24.0"))
    git(repo, "commit", "--cleanup=verbatim", "-am", "chore(release): cut 0.24.0\n\n## Fixes\n\n- A bug is fixed.\n")
    git(repo, "checkout", "main")
    git(repo, "merge", "--no-ff", "-m",
        "Merge pull request #9 from aamarin/release/v0.24.0\n\nchore(release): cut 0.24.0", "release/v0.24.0")
    git(repo, "push", "origin", "main")

    code, _ = tagger()

    assert code == 0
    assert tagger.notes().strip() == "## Fixes\n\n- A bug is fixed."


def test_a_later_commit_quoting_the_subject_does_not_block_the_release(
    repo: Path, tagger: Tagger
) -> None:
    cut(repo, "0.24.0")
    (repo / "later.txt").write_text("x")
    git(repo, "add", "later.txt")
    git(repo, "commit", "-m", "docs: explain a release\n\nThe commit is named chore(release): cut 0.24.0 by the script.")
    git(repo, "push", "origin", "main")

    code, _ = tagger()

    assert code == 0
    assert tagger.notes().strip() == "## Fixes\n\n- A bug is fixed."
