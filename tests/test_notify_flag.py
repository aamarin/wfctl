"""Granting from the terminal, and the run reporting what it did (#280).

The flag is tri-state and `None` is the value that carries the design: neither
flag given leaves the stored answer alone. A plain bool would default to False
and revoke on every later `wfctl start` — which `/start-session` runs at each
handoff, so an overnight run would go quiet without anyone touching it. That is
the failure `--auto-approve` documents beside itself, and this flag inherits it.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

from typer.testing import CliRunner

from wfctl._session import NOTIFY_NAME, resolved_notify
from wfctl.cli import app

runner = CliRunner()


def _stored(agent_dir: Path) -> dict | None:
    path = agent_dir / NOTIFY_NAME
    return json.loads(path.read_text()) if path.exists() else None


def _events(agent_dir: Path, kind: str) -> list[dict]:
    log = agent_dir / "events.jsonl"
    if not log.exists():
        return []
    out = []
    for line in log.read_text().splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if data.get("event") == kind:
            out.append(data)
    return out


def test_allow_notify_grants_and_deny_notify_revokes(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    agent_dir = storyctl_dir.agent_dir
    runner.invoke(app, ["start", "--allow-notify"])
    assert _stored(agent_dir)["state"] == "granted"
    assert resolved_notify(agent_dir).granted is True

    runner.invoke(app, ["start", "--deny-notify"])
    assert _stored(agent_dir)["state"] == "denied"
    assert resolved_notify(agent_dir).granted is False


def test_neither_flag_leaves_the_stored_answer_alone(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The tri-state's whole reason, and the bug a plain bool would ship.

    `/start-session` runs `wfctl start` on every handoff. If the absent flag
    meant False, the second run below would revoke a grant nobody withdrew and
    the session would go quiet mid-flight.
    """
    agent_dir = storyctl_dir.agent_dir
    runner.invoke(app, ["start", "--allow-notify"])
    for _ in range(3):
        runner.invoke(app, ["start"])
    assert _stored(agent_dir)["state"] == "granted"
    assert resolved_notify(agent_dir).granted is True


def test_the_flag_takes_on_a_session_that_is_already_open(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`start` is idempotent about the session and must not be about this.

    `/start-session` opens the session on a worktree's first turn, so by the time
    anyone types the flag the session is already recorded. Swallowed by the
    idempotence guard, the grant would print "Already initialized" over a flag
    that did nothing.
    """
    agent_dir = storyctl_dir.agent_dir
    runner.invoke(app, ["start"])
    result = runner.invoke(app, ["start", "--allow-notify"])

    assert "Already initialized" in result.output
    assert resolved_notify(agent_dir).granted is True


def test_the_granted_line_names_which_surface_answered(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-005. The two surfaces can disagree, and a reader resolving a surprise
    needs to know which one answered — a bare "granted" cannot say."""
    result = runner.invoke(app, ["start", "--allow-notify"])
    assert "may notify people — you allowed it in this worktree" in result.output

    status = runner.invoke(app, ["status"]).output
    assert "you allowed it in this worktree" in status
    assert "on issue" not in status


def test_the_help_text_connects_the_status_line_to_the_flag(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`status` says "may notify people" and never prints a flag name, so
    `--help` is the only place a reader who saw that line can find the command
    that sets it. Without the phrase, the two surfaces share no word."""
    help_text = runner.invoke(app, ["start", "--help"]).output
    assert "--allow-notify" in help_text
    assert "--deny-notify" in help_text
    assert "notify people outside" in help_text


def test_a_granted_run_records_each_notifying_action_it_took(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path,
) -> None:
    """FR-010, and unprompted is the requirement rather than a nicety.

    The log is the required destination because it is the one that cannot fail
    to be written — no change need be open, and the session need not end
    cleanly. The summary and the PR body are renderings of it.
    """
    from wfctl import _tracker

    root = storyctl_dir.repo_root
    (root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "fake"}))
    trackers = root / ".agents" / "trackers"
    trackers.mkdir(parents=True, exist_ok=True)
    (trackers / "fake.json").write_text(json.dumps({"verbs": {
        "comment": ["true"], "view": ["true"],
    }}))

    runner.invoke(app, ["start", "--allow-notify"])
    _tracker.dispatch(storyctl_dir.agent_dir, root, "comment", {"id": "418"})

    actions = _events(storyctl_dir.agent_dir, "notify-action")
    assert [a["action"] for a in actions] == ["comment"]

    # A read is not a notifying action and must not be filed as one, or the
    # report would claim people were told about a `view`.
    _tracker.dispatch(storyctl_dir.agent_dir, root, "view", {"id": "418"})
    assert len(_events(storyctl_dir.agent_dir, "notify-action")) == 1


def test_a_refused_action_records_nothing(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The negative half, and the one that would misreport if it broke: a run
    that was refused must not leave a line saying it notified anyone."""
    from wfctl import _tracker

    root = storyctl_dir.repo_root
    (root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "fake"}))
    trackers = root / ".agents" / "trackers"
    trackers.mkdir(parents=True, exist_ok=True)
    (trackers / "fake.json").write_text(json.dumps({"verbs": {"comment": ["true"]}}))

    runner.invoke(app, ["start", "--deny-notify"])
    assert _tracker.dispatch(
        storyctl_dir.agent_dir, root, "comment", {"id": "418"}
    ) == 1
    assert _events(storyctl_dir.agent_dir, "notify-action") == []


def test_granting_is_recorded_as_an_event_the_file_cannot_hold(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-007. `notify.json` holds one value and is overwritten, so it cannot
    answer *when was this given* — and that question is the whole of what makes
    a grant nobody made legible after the fact."""
    agent_dir = storyctl_dir.agent_dir
    runner.invoke(app, ["start", "--allow-notify"])
    runner.invoke(app, ["start", "--deny-notify"])

    grants = _events(agent_dir, "notify-grant")
    assert [g["state"] for g in grants] == ["granted", "denied"]
    assert all(g["source"] == "local" for g in grants)
