"""`wfctl start` refuses a worktree whose branch names no open issue (#497)."""
from __future__ import annotations

import dataclasses
import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from tests.conftest import git_repo
from wfctl._issue_check import Facts, Outcome, decide, gather
from wfctl.cli import app

runner = CliRunner()


def _facts(**overrides: object) -> Facts:
    """A linked worktree with a tracker configured, overridden per test."""
    base = Facts(linked=True, tracker_configured=True)
    return dataclasses.replace(base, **overrides)


def _add_worktree(main: Path, name: str, *args: str) -> Path:
    wt = main.parent / name
    subprocess.run(
        ["git", "-C", str(main), "worktree", "add", "-q", str(wt), *args],
        check=True, capture_output=True,
    )
    return wt


def _install(root: Path, **manifest: object) -> None:
    """A wfctl install as `gather` sees one: the manifest at the checkout root."""
    (root / ".wf-skills-manifest.json").write_text(json.dumps(manifest))


# --- decide ---


def test_the_main_checkout_proceeds_on_any_branch() -> None:
    """`/start-session` and orchestration from `main` work as they did."""
    verdict = decide(_facts(linked=False))
    assert (verdict.outcome, verdict.action, verdict.lines) == (
        Outcome.MAIN_CHECKOUT, "proceed", ()
    )


def test_a_repository_with_no_tracker_proceeds() -> None:
    """A repository that declined a tracker creates no issues to name."""
    verdict = decide(_facts(tracker_configured=False))
    assert (verdict.outcome, verdict.action) == (Outcome.NO_TRACKER, "proceed")


# --- gather ---


def test_gather_reads_the_main_checkout_as_not_linked(tmp_path: Path) -> None:
    """Asked of git at `repo_root`, not of the directory the suite runs in.

    The suite itself runs inside a linked worktree, so a git call without
    `cwd=repo_root` would read every test repository as linked.
    """
    main = git_repo(tmp_path / "main")
    assert gather(main, "main").linked is False


def test_gather_reads_a_linked_worktree_as_linked(tmp_path: Path) -> None:
    main = git_repo(tmp_path / "main")
    wt = _add_worktree(main, "wt", "-b", "7-x")
    assert gather(wt, "7-x").linked is True


def test_gather_reads_a_directory_git_cannot_answer_for_as_not_linked(tmp_path: Path) -> None:
    assert gather(tmp_path, "main").linked is False


def test_gather_reads_the_tracker_from_this_checkouts_own_manifest(tmp_path: Path) -> None:
    main = git_repo(tmp_path / "main")
    wt = _add_worktree(main, "wt", "-b", "7-x")
    _install(main, tracker="github")
    assert gather(wt, "7-x").tracker_configured is False
    _install(wt, tracker="github")
    assert gather(wt, "7-x").tracker_configured is True


# --- start ---


def test_start_in_a_main_checkout_prints_what_it_printed_before(agent_dir: Path) -> None:
    """The check adds nothing to the output of a checkout it exempts."""
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 0, result.output
    assert result.output.startswith("✓ Session started")
