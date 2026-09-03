"""State directories written by an older wfctl are cleaned up on first touch.

`current.md` and `current.json` are inert to this code, which reads neither. They
are not inert to an older `start-session` still installed in some other checkout
on the same machine: it reads `current.md` and gets a resume point frozen at
whenever `wfctl start` last ran. A developer has tens of state directories and
upgrades the tool once, so the fossils outlive the code that wrote them.
"""
from __future__ import annotations

import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def _run(*args: str) -> str:
    result = runner.invoke(app, list(args))
    assert result.exit_code == 0, result.output
    return result.output


def test_a_fossil_from_an_older_wfctl_is_removed_on_sight(agent_dir: Path) -> None:
    """An older `start-session` elsewhere on the machine still reads `current.md`.

    Left in place it answers with a resume point frozen at whenever `wfctl start`
    last ran — the exact failure this feature removes, reintroduced by a copy of
    the skill the upgrade did not reach.
    """
    (agent_dir / "current.md").write_text("# Working Context: stale\n")
    (agent_dir / "current.json").write_text('{"workflow_step": "implement"}')

    output = _run("status")

    assert not (agent_dir / "current.md").exists()
    assert not (agent_dir / "current.json").exists()
    # The fossil claimed `implement`. The answer comes from the artifacts, which
    # here are none, so nothing it said survives the read.
    assert "next: /speckit.brainstorm" in output


@pytest.mark.parametrize("command", ["start", "status", "next", "resume", "end", "log"])
def test_every_command_that_resolves_a_state_dir_clears_them(
    storyctl_dir: types.SimpleNamespace, command: str
) -> None:
    """The cleanup hangs off state-dir resolution, not off one command.

    A user reaches an upgraded wfctl through whichever command they happen to
    run first, and gating on `start` would leave the fossil readable for anyone
    who runs `status` in a worktree whose session is already open.
    """
    (storyctl_dir.agent_dir / "current.md").write_text("# stale\n")
    (storyctl_dir.agent_dir / "current.json").write_text("{}")

    runner.invoke(app, [command])

    assert not (storyctl_dir.agent_dir / "current.md").exists()
    assert not (storyctl_dir.agent_dir / "current.json").exists()


def test_a_state_dir_without_them_is_untouched(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Nothing is printed and nothing else is removed.

    Silence is deliberate: the files are tool-written and never hand-edited, and
    a notice about a file the reader did not know existed is noise.
    """
    result = runner.invoke(app, ["start"])

    assert "current" not in result.output
    assert (storyctl_dir.agent_dir / "events.jsonl").exists()
