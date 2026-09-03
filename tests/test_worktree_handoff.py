"""`state-dir --branch` resolves a branch that is not checked out, and the
`worktree-handoff` skill's own copy of that invocation still runs.

The flag exists for one caller: a session writing a handoff into the state dir
of a branch it has never been on. Two ways that goes wrong silently, and both
end with the handoff in the wrong directory rather than with an error —
`WFCTL_STATE_DIR` answering for the active branch under another branch's name,
and the skill's prose drifting from the flag it names.
"""
import re
import subprocess
from importlib.resources import files
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import git_repo
from wfctl.cli import app

runner = CliRunner()

_SKILL = (
    Path(str(files("wfctl"))) / "agents" / "skills" / "worktree-handoff" / "SKILL.md"
)


@pytest.fixture
def xdg_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A repo whose state resolves through XDG, not through the pin.

    The suite's `agent_dir` fixture sets `WFCTL_STATE_DIR`, which is exactly the
    condition `--branch` refuses — so it cannot be used to test the resolution
    it is meant to do.
    """
    repo = git_repo(tmp_path / "repo")
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("WFCTL_BRANCH", "100-active")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))
    return repo


def test_branch_resolves_a_branch_that_is_not_checked_out(xdg_repo: Path) -> None:
    """The whole point: the child branch does not exist yet at handoff time."""
    active = runner.invoke(app, ["state-dir"])
    other = runner.invoke(app, ["state-dir", "--branch", "200-never-created"])
    assert other.exit_code == 0
    assert other.stdout.strip() != active.stdout.strip()
    assert Path(other.stdout.strip()).name == "200-never-created"
    assert Path(other.stdout.strip()).is_dir()


def test_the_pin_is_refused_rather_than_answered_with(
    xdg_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`WFCTL_STATE_DIR` has no branch component, so answering with it would hand
    back the *active* branch's dir — and the caller is about to write a handoff
    into whatever it gets. A wrong path here overwrites this session's own
    summary, which is the artifact the feature exists to protect."""
    monkeypatch.setenv("WFCTL_STATE_DIR", str(tmp_path / "pinned"))
    result = runner.invoke(app, ["state-dir", "--branch", "200-other"])
    assert result.exit_code == 1
    assert "WFCTL_STATE_DIR" in result.output


def test_the_pin_still_answers_for_the_active_branch(
    xdg_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Naming the branch you are already on is not the ambiguous case, and
    refusing it would break `--branch "$(git branch --show-current)"`."""
    pinned = tmp_path / "pinned"
    monkeypatch.setenv("WFCTL_STATE_DIR", str(pinned))
    result = runner.invoke(app, ["state-dir", "--branch", "100-active"])
    assert result.exit_code == 0
    assert result.stdout.strip() == str(pinned)


def test_a_branch_name_git_would_reject_does_not_become_a_path(
    xdg_repo: Path
) -> None:
    """The name arrives as an argument, not from git, and is about to be a path
    component. `..` would resolve outside the project's state dir entirely."""
    result = runner.invoke(app, ["state-dir", "--branch", "../../escaped"])
    assert result.exit_code == 1
    assert "not a valid branch name" in result.output


def test_the_skill_runs_the_command_it_tells_the_agent_to_run(
    xdg_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The skill spells `wfctl state-dir --branch <branch>` into a shell block.
    A renamed flag leaves the prose passing every other test in this suite and
    failing only in the worktree of whoever followed it."""
    invocations = re.findall(r"wfctl state-dir [^\n\"')]*", _SKILL.read_text())
    assert invocations, "skill no longer names the command it depends on"
    for inv in invocations:
        cmd = inv.replace("<branch>", "200-derived-from-the-skill").split()
        out = subprocess.run(cmd, capture_output=True, text=True, cwd=xdg_repo)
        assert out.returncode == 0, out.stderr
        assert Path(out.stdout.strip()).name == "200-derived-from-the-skill"
