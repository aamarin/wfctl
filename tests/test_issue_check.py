"""`wfctl start` refuses a worktree whose branch names no open issue (#497)."""
from __future__ import annotations

import dataclasses
import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from tests.conftest import git_repo
from wfctl import _tracker
from wfctl._issue_check import Facts, Outcome, decide, gather
from wfctl.cli import app

runner = CliRunner()


def _facts(**overrides: object) -> Facts:
    """A linked worktree on an open issue's branch, overridden per test."""
    base = Facts(
        linked=True, tracker_configured=True, detached=False,
        branch="497-start-refuses", key="497", state="open",
    )
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


def test_a_detached_head_refuses_with_a_remedy_that_works_there() -> None:
    """A detached HEAD has no branch to rename, so the rename remedy cannot apply.

    wfctl substitutes the short hash for a missing branch name, and an all-digit
    one such as `5611469` parses as issue 5611469, which is why `detached` is a
    fact asked of git and settled before any key is read.
    """
    verdict = decide(_facts(detached=True, branch="5611469", key="5611469"))
    assert (verdict.outcome, verdict.action) == (Outcome.DETACHED, "refuse")
    assert verdict.lines == (
        "✗ this worktree is on a detached HEAD — it names no branch, so no issue.",
        "  Switch to the branch this worktree works on:",
        "    git switch <key>-<slug>",
        "  then run `wfctl start` again.",
    )


def test_a_branch_naming_no_issue_refuses_and_names_the_rename() -> None:
    verdict = decide(_facts(branch="spike-foo", key=None))
    assert (verdict.outcome, verdict.action) == (Outcome.NO_KEY, "refuse")
    assert verdict.lines == (
        "✗ 'spike-foo' names no issue — every worktree works against one.",
        "  Open an issue, then rename the branch to start with its key:",
        "    git branch -m <key>-spike-foo",
    )


def test_a_closed_issue_refuses() -> None:
    verdict = decide(_facts(key="495", state="closed"))
    assert (verdict.outcome, verdict.action) == (Outcome.CLOSED, "refuse")
    assert verdict.lines == (
        "✗ #495 is closed — this worktree works against an issue that is not open.",
        "  Reopen it, or open a new issue and rename the branch to start with its key.",
    )


def test_a_missing_issue_refuses() -> None:
    """A pull request number reaches this row too; the backend calls it missing."""
    verdict = decide(_facts(key="9999", state="missing"))
    assert (verdict.outcome, verdict.action) == (Outcome.MISSING, "refuse")
    assert verdict.lines == (
        "✗ #9999 is not an issue in this tracker.",
        "  Open one, then rename the branch to start with its key.",
    )


def test_an_open_issue_proceeds_and_prints_nothing() -> None:
    verdict = decide(_facts(state="open"))
    assert (verdict.outcome, verdict.action, verdict.lines) == (Outcome.OPEN, "proceed", ())


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


def test_gather_asks_git_whether_head_is_detached(tmp_path: Path, monkeypatch) -> None:
    """Asked of git, not read off the name wfctl substitutes for the branch.

    `WFCTL_BRANCH` is how the suite and a person name a branch explicitly, so a
    worktree with it set is not treated as detached.
    """
    main = git_repo(tmp_path / "main")
    wt = _add_worktree(main, "wt", "--detach", "HEAD")
    monkeypatch.delenv("WFCTL_BRANCH", raising=False)
    assert gather(wt, "abc1234").detached is True
    monkeypatch.setenv("WFCTL_BRANCH", "7-x")
    assert gather(wt, "7-x").detached is False


def test_gather_reads_the_key_through_the_trackers_pattern(tmp_path: Path) -> None:
    main = git_repo(tmp_path / "main")
    wt = _add_worktree(main, "wt", "-b", "497-x")
    _install(wt, tracker="github")
    assert gather(wt, "497-x").key == "497"
    assert gather(wt, "spike-foo").key is None


def test_gather_never_asks_the_tracker_when_the_local_facts_decide(
    tmp_path: Path, monkeypatch
) -> None:
    """An exempt checkout pays for no network call, and a keyless branch neither."""
    asked: list[str] = []
    monkeypatch.setattr(
        _tracker, "read_state", lambda root, key: asked.append(key) or ("open", None)
    )
    main = git_repo(tmp_path / "main")
    _install(main, tracker="github")
    gather(main, "main")
    wt = _add_worktree(main, "wt", "-b", "spike-foo")
    _install(wt, tracker="github")
    gather(wt, "spike-foo")
    assert asked == []

    wt2 = _add_worktree(main, "wt2", "-b", "497-x")
    _install(wt2, tracker="github")
    assert gather(wt2, "497-x").state == "open"
    assert asked == ["497"]


# --- start ---


def test_start_in_a_main_checkout_prints_what_it_printed_before(agent_dir: Path) -> None:
    """The check adds nothing to the output of a checkout it exempts."""
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 0, result.output
    assert result.output.startswith("✓ Session started")


def _refusing_worktree(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    """A linked worktree on `spike-foo`, with a tracker, as `start` sees it.

    Returns the worktree and the state directory `start` would write to, which
    is outside the worktree so that its absence can be asserted.
    """
    main = git_repo(tmp_path / "main")
    wt = _add_worktree(main, "wt", "-b", "spike-foo")
    _install(main, tracker="github")
    _install(wt, tracker="github")
    state = tmp_path / "state"
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(wt))
    monkeypatch.setenv("WFCTL_STATE_DIR", str(state))
    monkeypatch.delenv("WFCTL_BRANCH", raising=False)
    monkeypatch.chdir(wt)
    return wt, state


def test_a_refused_start_refuses_again_and_writes_nothing(tmp_path: Path, monkeypatch) -> None:
    """The refusal holds on every run, `--force` and `--auto-approve` included.

    A refusal that wrote a `start` event would let `resume` and `end` through on
    the second run, and one that wrote an auto-approve grant would leave a mode
    set on a branch that never had a session.
    """
    _, state = _refusing_worktree(tmp_path, monkeypatch)
    for args in (["start"], ["start"], ["start", "--force"], ["start", "--auto-approve"]):
        result = runner.invoke(app, args)
        assert result.exit_code == 1, result.output
        assert "names no issue" in result.output
    assert not state.exists()


def test_a_refused_start_leaves_an_existing_state_directory_byte_identical(
    tmp_path: Path, monkeypatch
) -> None:
    """`_resolve_context()` deletes fossil files, so the check has to run first."""
    _, state = _refusing_worktree(tmp_path, monkeypatch)
    state.mkdir()
    (state / "events.jsonl").write_text('{"event": "note"}\n')
    (state / "current.md").write_text("fossil\n")
    before = {p.name: p.read_bytes() for p in state.iterdir()}

    result = runner.invoke(app, ["start"])

    assert result.exit_code == 1, result.output
    assert {p.name: p.read_bytes() for p in state.iterdir()} == before
