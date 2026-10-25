"""The session id comes from the agent named in `WFCTL_AGENT` when the caller names none (#629).

The #200 gates compared an id that only a line in the developer's shell profile
ever set, and no profile carried it, so every comparison read `unknown` and the
gates let every conversation through. `session-identity-from-named-agent` moves
the mapping from that profile line into wfctl: `--session-id`, then
`WFCTL_SESSION_ID`, then the session variable of the agent `WFCTL_AGENT` names.

These pin that order and its two edges: an agent wfctl has no entry for, and an
agent nobody named, both present nothing rather than a guess.
"""
from __future__ import annotations

import json
import types

import pytest
from typer.testing import CliRunner

from wfctl import _session
from wfctl.cli import app

runner = CliRunner()

CLAUDE_VAR = "CLAUDE_CODE_SESSION_ID"


def _holder() -> str:
    return json.loads(runner.invoke(app, ["status", "--json"]).output)["session_holder"]


def _recorded(storyctl_dir: types.SimpleNamespace) -> str | None:
    return _session.last_session_id(storyctl_dir.agent_dir)


def test_claude_conversation_holds_the_branch_with_no_profile_line(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bug as measured in the #629 worktree: agent named, host id exported,
    `WFCTL_SESSION_ID` unset, and `status` reported `unknown` to the conversation
    that had just run `start`."""
    monkeypatch.delenv("WFCTL_SESSION_ID", raising=False)
    monkeypatch.setenv("WFCTL_AGENT", "claude")
    monkeypatch.setenv(CLAUDE_VAR, "conversation-a")

    runner.invoke(app, ["start"])

    assert _recorded(storyctl_dir) == "conversation-a"
    assert _holder() == "self"


def test_a_second_claude_conversation_reads_the_branch_as_held_by_another(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The refusal #200 exists for, now reachable without any wiring. `/clear`
    gives Claude Code a new id over the same process, so this is the
    conversation that skipped `/start-session`."""
    monkeypatch.delenv("WFCTL_SESSION_ID", raising=False)
    monkeypatch.setenv("WFCTL_AGENT", "claude")
    monkeypatch.setenv(CLAUDE_VAR, "conversation-a")
    runner.invoke(app, ["start"])

    monkeypatch.setenv(CLAUDE_VAR, "conversation-b")

    assert _holder() == "other"


def test_wfctl_session_id_wins_over_the_agents_variable(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A developer who wired the profile line, or a host wfctl has no entry for,
    keeps the id they chose. Reversing this order would silently change the
    holder on every machine that had followed the old instruction."""
    monkeypatch.setenv("WFCTL_AGENT", "claude")
    monkeypatch.setenv(CLAUDE_VAR, "from-host")
    monkeypatch.setenv("WFCTL_SESSION_ID", "from-profile")

    runner.invoke(app, ["start"])

    assert _recorded(storyctl_dir) == "from-profile"
    assert _holder() == "self"


def test_the_flag_is_recorded_when_later_commands_present_no_identity(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A plain terminal with the agent named in the profile but no conversation
    behind it. The flag is the only id on offer, so `start` records it, and the
    commands after it present nothing and read `unknown` as they always have."""
    monkeypatch.delenv("WFCTL_SESSION_ID", raising=False)
    monkeypatch.setenv("WFCTL_AGENT", "claude")
    monkeypatch.delenv(CLAUDE_VAR, raising=False)

    result = runner.invoke(app, ["start", "--session-id", "typed"])

    assert result.exit_code == 0, result.output
    assert _recorded(storyctl_dir) == "typed"


def test_the_flag_is_accepted_when_it_matches_what_later_commands_present(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Typing the conversation's own id is redundant, not a conflict, so it must
    not be refused alongside a flag that differs."""
    monkeypatch.delenv("WFCTL_SESSION_ID", raising=False)
    monkeypatch.setenv("WFCTL_AGENT", "claude")
    monkeypatch.setenv(CLAUDE_VAR, "from-host")

    result = runner.invoke(app, ["start", "--session-id", "from-host"])

    assert result.exit_code == 0, result.output
    assert _holder() == "self"


@pytest.mark.parametrize(
    "variable", ["WFCTL_SESSION_ID", CLAUDE_VAR], ids=["profile", "host"]
)
def test_a_flag_later_commands_cannot_present_is_refused(
    storyctl_dir: types.SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    variable: str,
) -> None:
    """Codex on PR #645. `resume`, `end` and the orchestrate gate take no flag, so
    they present the environment's id. A typed id that differs from it would make
    the conversation that typed it read `other` on its own branch, and the gates
    would refuse it. The profile case predates #629. The host case is new with
    the agent fallback, and it reaches every Claude Code pane with `WFCTL_AGENT`
    set, since the host always exports its own id."""
    monkeypatch.setenv("WFCTL_AGENT", "claude")
    if variable == "WFCTL_SESSION_ID":
        monkeypatch.setenv("WFCTL_SESSION_ID", "from-profile")
    else:
        monkeypatch.delenv("WFCTL_SESSION_ID", raising=False)
        monkeypatch.setenv(CLAUDE_VAR, "from-host")

    result = runner.invoke(app, ["start", "--session-id", "typed"])

    assert result.exit_code == 1, result.output
    assert "WFCTL_SESSION_ID" in result.output
    assert _recorded(storyctl_dir) is None


def test_a_blank_wfctl_session_id_falls_through_to_the_agent(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`export WFCTL_SESSION_ID=` is the same caller as one never exported
    (`_session.identity`), so it must not mask the host's id either."""
    monkeypatch.setenv("WFCTL_AGENT", "claude")
    monkeypatch.setenv(CLAUDE_VAR, "from-host")
    monkeypatch.setenv("WFCTL_SESSION_ID", "  ")

    runner.invoke(app, ["start"])

    assert _recorded(storyctl_dir) == "from-host"


@pytest.mark.parametrize("agent", [None, "", "codex", "no-such-agent"])
def test_an_agent_with_no_entry_presents_nothing(
    storyctl_dir: types.SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    agent: str | None,
) -> None:
    """No probing. With `WFCTL_AGENT` unset the Claude variable is still in the
    environment, the way a nested agent inherits it from its parent, and wfctl
    must not take it as this caller's id. The holder stays `unknown`, which is
    what every unwired caller read before #629."""
    monkeypatch.delenv("WFCTL_SESSION_ID", raising=False)
    if agent is None:
        monkeypatch.delenv("WFCTL_AGENT", raising=False)
    else:
        monkeypatch.setenv("WFCTL_AGENT", agent)
    monkeypatch.setenv(CLAUDE_VAR, "parent-conversation")

    runner.invoke(app, ["start"])

    assert _recorded(storyctl_dir) is None
    assert _holder() == "unknown"


def test_a_blank_host_variable_presents_nothing(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`export CLAUDE_CODE_SESSION_ID=` is no identity, for the same reason a
    blank `WFCTL_SESSION_ID` isn't."""
    monkeypatch.delenv("WFCTL_SESSION_ID", raising=False)
    monkeypatch.setenv("WFCTL_AGENT", "claude")
    monkeypatch.setenv(CLAUDE_VAR, "")

    runner.invoke(app, ["start"])

    assert _recorded(storyctl_dir) is None
