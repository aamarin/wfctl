"""Tests for architecture root resolution and `wfctl arch-root`."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import git_repo
from wfctl._paths import arch_root, arch_root_declaration, is_in_tree
from wfctl.cli import app

runner = CliRunner()

MANIFEST = ".wf-skills-manifest.json"


def _declare(repo: Path, value: str) -> None:
    (repo / MANIFEST).write_text(json.dumps({"arch_root": value}))


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WFCTL_ARCH_DIR", raising=False)


def test_default_is_in_tree(tmp_path: Path) -> None:
    """The default is version-controlled and beside the code it governs — a
    record that never reaches a clone is a record nobody reads."""
    repo = git_repo(tmp_path / "proj")

    assert arch_root(repo) == repo / "docs" / "architecture"
    assert arch_root_declaration(repo) is None


def test_env_override_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A per-invocation escape hatch, above every recorded value."""
    repo = git_repo(tmp_path / "proj")
    _declare(repo, str(tmp_path / "recorded"))
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(tmp_path / "from-env"))

    assert arch_root(repo) == tmp_path / "from-env"


def test_this_repos_manifest_is_read(tmp_path: Path) -> None:
    repo = git_repo(tmp_path / "proj")
    _declare(repo, str(tmp_path / "recorded"))

    assert arch_root(repo) == tmp_path / "recorded"
    assert arch_root_declaration(repo) == (tmp_path / "recorded", repo)


def test_relative_value_anchors_to_the_declaring_manifest(tmp_path: Path) -> None:
    """Anchoring to the cwd would give one recorded value a different meaning
    per shell — the same failure `spec_root` documents."""
    repo = git_repo(tmp_path / "proj")
    _declare(repo, "../shared-architecture")

    assert arch_root(repo) == (tmp_path / "shared-architecture").resolve()


def test_main_checkouts_manifest_is_the_fallback(tmp_path: Path) -> None:
    """The manifest is gitignored, so a fresh worktree has none — without this
    fallback the setting is unreachable exactly when the pipeline first runs."""
    main = git_repo(tmp_path / "proj")
    _declare(main, str(tmp_path / "shared-architecture"))
    wt = main / "wt" / "91-record-module"
    subprocess.run(
        ["git", "-C", str(main), "worktree", "add", "-b", "91-record-module", str(wt)],
        check=True, capture_output=True,
    )

    assert arch_root(wt) == tmp_path / "shared-architecture"
    assert arch_root_declaration(wt) == (tmp_path / "shared-architecture", main)


def test_the_worktrees_own_manifest_beats_the_main_checkouts(tmp_path: Path) -> None:
    main = git_repo(tmp_path / "proj")
    _declare(main, str(tmp_path / "from-main"))
    wt = main / "wt" / "91-record-module"
    subprocess.run(
        ["git", "-C", str(main), "worktree", "add", "-b", "91-record-module", str(wt)],
        check=True, capture_output=True,
    )
    _declare(wt, str(tmp_path / "from-worktree"))

    assert arch_root(wt) == tmp_path / "from-worktree"


def test_resolution_neither_checks_existence_nor_creates(tmp_path: Path) -> None:
    """A not-yet-existing root is the normal case — no repo has records before
    it writes the first one. Checking here is what broke the spec-root create
    path, and adding it back would rebuild the same bug."""
    repo = git_repo(tmp_path / "proj")
    target = tmp_path / "does-not-exist"
    _declare(repo, str(target))

    assert arch_root(repo) == target
    assert not target.exists()
    assert not (repo / "docs").exists(), "the default is not created either"


def test_arch_root_command_prints_the_resolved_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = git_repo(tmp_path / "proj")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))

    result = runner.invoke(app, ["arch-root"])

    assert result.exit_code == 0, result.output
    assert str(repo / "docs" / "architecture") in result.output
    assert "⚠" not in result.output, "the in-tree default costs nothing to warn about"


def test_arch_root_command_warns_when_the_root_is_out_of_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Honoured, with the cost named: records outside the tree share no commit
    with the code they govern and reach nobody who clones the repo."""
    repo = git_repo(tmp_path / "proj")
    _declare(repo, str(tmp_path / "outside"))
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))

    result = runner.invoke(app, ["arch-root"])

    assert result.exit_code == 0, "a configured choice is not drift"
    assert str(tmp_path / "outside") in result.output
    assert "outside the working tree" in result.output


def test_a_relative_override_anchors_to_the_repo_not_the_cwd(tmp_path: Path) -> None:
    """Caught in review: left raw, one setting named a different directory per
    shell, and `arch-root` reported the same config as inside the tree or
    outside it depending on where it ran."""
    repo = git_repo(tmp_path / "proj")

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("WFCTL_ARCH_DIR", "docs/architecture")
        assert arch_root(repo) == repo / "docs" / "architecture"
        assert is_in_tree(arch_root(repo), repo)


def test_is_in_tree_answers_from_plain_paths(tmp_path: Path) -> None:
    """Its own function so the rule can be checked without a CLI runner and a
    real git repo — `plan.md`'s structure decision."""
    repo = tmp_path / "proj"

    assert is_in_tree(repo / "docs" / "architecture", repo)
    assert not is_in_tree(tmp_path / "outside", repo)
    assert is_in_tree(repo, repo), "the root itself is in the tree"


def test_a_root_containing_brackets_is_printed_whole(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Caught in review: rich parsed `[...]` in the path as markup and dropped
    it, so the command's one job — naming a location — produced a directory that
    does not exist. Brackets are legal in a directory name everywhere."""
    repo = git_repo(tmp_path / "proj")
    bracketed = tmp_path / "[bold]arch[/bold]"
    _declare(repo, str(bracketed))
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))

    result = runner.invoke(app, ["arch-root"])

    assert result.exit_code == 0, result.output
    assert str(bracketed) in result.output
