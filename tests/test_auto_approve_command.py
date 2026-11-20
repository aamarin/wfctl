"""`wfctl auto-approve [on|off]`, the command that sets the mode mid-session (#407).

Before it, `wfctl start --auto-approve` was the only setter, and a mid-session
grant through it printed "Already initialized" after the grant, which reads
like a failure. These tests pin what the new command refuses, what it writes,
and what the bare form reports, including the cases the record
`approval-mode-is-stored-intent` lists under "Must keep catching" and "Must let
through".
"""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl import evidence
from wfctl.cli import app

runner = CliRunner()


def _payload() -> dict:
    return json.loads(runner.invoke(app, ["status", "--json"]).output)


def _mode_events(agent_dir: Path) -> list[dict]:
    log = agent_dir / "events.jsonl"
    if not log.exists():
        return []
    events = [json.loads(line) for line in log.read_text().splitlines()]
    return [e for e in events if e["event"] == "mode"]


def test_start_never_reads_the_creation_variable_after_a_revocation(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pane restart runs `wfctl start` with the shell's environment still set.

    If `start` read `WFCTL_AUTO_APPROVE`, the restart right after the review
    cap fired would turn the mode back on, and the cap would never hold. This
    is the record's "Must keep catching" case 5.
    """
    runner.invoke(app, ["auto-approve", "on"])
    evidence.revoke_auto_approve(storyctl_dir.agent_dir, "cap fired")
    monkeypatch.setenv("WFCTL_AUTO_APPROVE", "1")

    runner.invoke(app, ["start"])

    assert _payload()["auto_approve"] is False


def test_start_never_reads_the_creation_variable_over_a_running_grant(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A `0` in a shell profile mustn't turn off a grant made mid-session.

    This is the record's "Must let through" case 5: a restart with no flag
    leaves the mode as it is, and writes no `mode` event.
    """
    runner.invoke(app, ["auto-approve", "on"])
    monkeypatch.setenv("WFCTL_AUTO_APPROVE", "0")

    runner.invoke(app, ["start"])

    assert _payload()["auto_approve"] is True
    assert len(_mode_events(storyctl_dir.agent_dir)) == 1


# --- User Story 1: turn the mode on or off mid-session ---


def _session(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    monkeypatch.setenv("WFCTL_SESSION_ID", name)


def _refuse_the_issue(monkeypatch: pytest.MonkeyPatch, *lines: str) -> None:
    """Make the issue check `start` runs refuse, with the lines it would print."""
    from wfctl import session
    from wfctl.session._issue_check import Outcome, Verdict

    monkeypatch.setattr(
        session, "decide_issue_check", lambda facts: Verdict(Outcome.CLOSED, "refuse", lines),
    )


_CLOSED = (
    "✗ #418 is closed — this worktree works against an issue that is not open.",
    "  Reopen it, or open a new issue and rename the branch to start with its key.",
)
_NO_KEY = (
    "✗ spike-foo names no issue.",
    "  Rename the branch to start with an issue key.",
)


def test_on_grants_the_mode_mid_session_without_already_initialized(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The gap #407 reports, and SC-001.

    The #799 run re-ran `wfctl start --auto-approve` to get the grant, and
    `start` then printed "Already initialized", which reads like a failure.
    """
    _session(monkeypatch, "me")
    runner.invoke(app, ["start"])

    result = runner.invoke(app, ["auto-approve", "on"])

    assert result.exit_code == 0, result.output
    assert "✓ auto-approve — design gates answered into the record" in result.output
    assert "Already initialized" not in result.output
    assert _payload()["auto_approve"] is True
    assert _mode_events(storyctl_dir.agent_dir)[-1]["session"] == "me"


def test_a_repeated_on_answers_again_and_appends_nothing(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario 3, and the record's "Must let through" case 4.

    Refusing would read as a failure to an agent asked to make sure the mode is
    on, and appending would reset the review cap.
    """
    _session(monkeypatch, "me")
    runner.invoke(app, ["start"])
    runner.invoke(app, ["auto-approve", "on"])

    again = runner.invoke(app, ["auto-approve", "on"])

    assert again.exit_code == 0
    assert "✓ auto-approve" in again.output
    assert len(_mode_events(storyctl_dir.agent_dir)) == 1


def test_on_is_refused_while_another_session_holds_the_branch(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario 4, and the record's "Must keep catching" case 1.

    A session that doesn't hold the branch could otherwise grant the mode to a
    run it isn't driving.
    """
    _session(monkeypatch, "them")
    runner.invoke(app, ["start"])
    _session(monkeypatch, "me")

    result = runner.invoke(app, ["auto-approve", "on"])

    assert result.exit_code == 1
    assert "No session is open for this conversation on this branch" in result.output
    assert "Run /start-session first." in result.output
    assert _payload()["auto_approve"] is False
    assert _mode_events(storyctl_dir.agent_dir) == []


def test_on_is_refused_after_this_conversation_ended_its_session(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The holder relation reads "other" here too, and the refusal is true for both.

    A raw comparison of the last session id with the caller would let this case
    through, which is the #200 bug `start`'s comment describes.
    """
    from wfctl._io import append_event

    _session(monkeypatch, "me")
    runner.invoke(app, ["start"])
    append_event(storyctl_dir.agent_dir, "end", branch="418-storyctl")

    result = runner.invoke(app, ["auto-approve", "on"])

    assert result.exit_code == 1
    assert "No session is open for this conversation" in result.output
    assert _mode_events(storyctl_dir.agent_dir) == []


@pytest.mark.parametrize("lines", [_CLOSED, _NO_KEY], ids=["closed", "no-key"])
def test_on_is_refused_with_starts_own_message_when_start_would_refuse(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, lines: tuple[str, ...],
) -> None:
    """Scenario 5, FR-005, and the record's "Must keep catching" case 2.

    One check, not two. A check of its own would drift from `start`'s, and the
    fix line would stop matching what the person needs to do.
    """
    _session(monkeypatch, "me")
    runner.invoke(app, ["start"])
    _refuse_the_issue(monkeypatch, *lines)

    on = runner.invoke(app, ["auto-approve", "on"])
    start = runner.invoke(app, ["start"])

    assert on.exit_code == start.exit_code == 1
    assert on.output == start.output
    assert all(line in on.output for line in lines)
    assert _mode_events(storyctl_dir.agent_dir) == []


def test_on_is_allowed_for_a_caller_with_no_identity(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario 6, FR-006, and the record's "Must let through" case 3.

    A repository nobody wired up presents no identity, and refusing it would
    break auto-approve there entirely.
    """
    monkeypatch.delenv("WFCTL_SESSION_ID", raising=False)
    monkeypatch.delenv("WFCTL_AGENT", raising=False)
    runner.invoke(app, ["start"])

    result = runner.invoke(app, ["auto-approve", "on"])

    assert result.exit_code == 0, result.output
    assert _payload()["auto_approve"] is True
    assert "session" not in _mode_events(storyctl_dir.agent_dir)[-1]


def test_a_failed_write_says_so_and_exits_1(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A traceback naming a state-dir file says nothing about what was asked for."""
    import wfctl.evidence._mode as mode

    _session(monkeypatch, "me")
    runner.invoke(app, ["start"])

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(mode, "append_event", fail)

    result = runner.invoke(app, ["auto-approve", "on"])

    assert result.exit_code == 1
    assert "✗ Couldn't record the auto-approve change: disk full" in result.output


def test_off_still_turns_the_mode_off_when_the_event_log_fails(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A code reviewer found an unwritable event log kept the mode on after
    `off`, since the event was written first. Lowering autonomy shouldn't depend
    on the log, so the mode turns off and the failure is still reported."""
    import wfctl.evidence._mode as mode

    _session(monkeypatch, "me")
    runner.invoke(app, ["start"])
    runner.invoke(app, ["auto-approve", "on"])

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(mode, "append_event", fail)

    result = runner.invoke(app, ["auto-approve", "off"])

    assert result.exit_code == 1
    assert "disk full" in result.output
    assert not mode.auto_approve(storyctl_dir.agent_dir)


def test_off_turns_the_mode_off_and_logs_it(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario 2, and the record's "Must let through" case 1."""
    _session(monkeypatch, "me")
    runner.invoke(app, ["start"])
    runner.invoke(app, ["auto-approve", "on"])

    result = runner.invoke(app, ["auto-approve", "off"])

    assert result.exit_code == 0
    assert "✓ auto-approve off — design gates and review stops wait for a human" in result.output
    assert _payload()["auto_approve"] is False
    assert [e["auto_approve"] for e in _mode_events(storyctl_dir.agent_dir)] == [True, False]


def test_off_is_never_refused_for_the_holder(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-002: turning the mode off raises the bar and needs no person.

    A refusal here would leave a run unattended that someone is trying to stop.
    """
    _session(monkeypatch, "them")
    runner.invoke(app, ["auto-approve", "on"])
    _session(monkeypatch, "me")

    result = runner.invoke(app, ["auto-approve", "off"])

    assert result.exit_code == 0, result.output
    assert _payload()["auto_approve"] is False


@pytest.mark.parametrize("lines", [_CLOSED, _NO_KEY], ids=["closed", "no-key"])
def test_off_is_never_refused_for_the_issue(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, lines: tuple[str, ...],
) -> None:
    """FR-002 again, for the issue: a closed issue is no reason to stay unattended."""
    runner.invoke(app, ["auto-approve", "on"])
    _refuse_the_issue(monkeypatch, *lines)

    result = runner.invoke(app, ["auto-approve", "off"])

    assert result.exit_code == 0, result.output
    assert evidence.auto_approve(storyctl_dir.agent_dir) is False


# --- User Story 2: see who turned the mode on ---


def _show() -> list[str]:
    result = runner.invoke(app, ["auto-approve"])
    assert result.exit_code == 0, result.output
    return result.output.splitlines()


def _write_mode_event(agent_dir: Path, **fields: object) -> None:
    with (agent_dir / "events.jsonl").open("a") as log:
        log.write(json.dumps({"ts": "2026-11-19T14:02:00Z", "event": "mode", **fields}) + "\n")


def test_the_bare_command_says_this_session_turned_it_on(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario 1. The UTC time and the relation, in the spec's own wording."""
    _session(monkeypatch, "me")
    _write_mode_event(storyctl_dir.agent_dir, auto_approve=True, session="me")
    (storyctl_dir.agent_dir / evidence.MODE_NAME).write_text('{"auto_approve": true}')

    lines = _show()

    assert lines[0].startswith("auto-approve on — design gates answered into the record")
    assert lines[1] == "  turned on 2026-11-19 14:02 UTC by this session"


def test_the_bare_command_says_another_session_turned_it_on(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario 2. This is how a reviewer spots a grant the run didn't ask for."""
    _session(monkeypatch, "me")
    evidence.grant_auto_approve(storyctl_dir.agent_dir, True, session="them")

    assert _show()[1].endswith("by another session")


@pytest.mark.parametrize("event_session, caller", [(None, "me"), ("them", None)])
def test_the_bare_command_says_an_unknown_session_when_either_side_has_no_identity(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
    event_session: str | None, caller: str | None,
) -> None:
    """Scenario 3. wfctl can't compare against an identity nobody presented.

    "another session" would claim a difference wfctl can't observe.
    """
    monkeypatch.delenv("WFCTL_AGENT", raising=False)
    if caller is None:
        monkeypatch.delenv("WFCTL_SESSION_ID", raising=False)
    else:
        _session(monkeypatch, caller)
    evidence.grant_auto_approve(storyctl_dir.agent_dir, True, session=event_session)

    assert _show()[1].endswith("by an unknown session")


def test_after_the_cap_fires_the_bare_command_shows_why_and_who_granted(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario 4. The person who granted the mode needs both that it stopped and who started it."""
    _session(monkeypatch, "me")
    evidence.grant_auto_approve(storyctl_dir.agent_dir, True, session="me")
    evidence.revoke_auto_approve(storyctl_dir.agent_dir, "wfctl turned it off after 3 plan reviews")

    lines = _show()

    assert lines[0] == "auto-approve off — wfctl turned it off after 3 plan reviews"
    assert lines[1].startswith("  turned on ")
    assert lines[1].endswith("by this session")


def test_a_mode_never_granted_has_no_grant_on_record(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Scenario 5."""
    assert _show()[:2] == ["auto-approve off", "  no grant on record"]


def test_a_hand_written_mode_file_has_no_grant_on_record(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An older grant doesn't explain the mode the file holds now.

    After a revocation and a hand edit back to on, showing the old grant would
    tell a reviewer a session granted a mode nobody granted.
    """
    _session(monkeypatch, "me")
    evidence.grant_auto_approve(storyctl_dir.agent_dir, True, session="me")
    evidence.revoke_auto_approve(storyctl_dir.agent_dir, "cap fired")
    (storyctl_dir.agent_dir / evidence.MODE_NAME).write_text('{"auto_approve": true}')

    lines = _show()

    assert lines[0].startswith("auto-approve on — ")
    assert lines[1] == "  no grant on record"


def test_a_mode_file_turned_off_outside_wfctl_says_so(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The file and the log disagree, after a hand edit or a failed file write.

    "turned on by this session" over a mode that reads off would contradict the
    line above it.
    """
    _session(monkeypatch, "me")
    evidence.grant_auto_approve(storyctl_dir.agent_dir, True, session="me")
    (storyctl_dir.agent_dir / evidence.MODE_NAME).write_text('{"auto_approve": false}')

    assert _show()[:2] == ["auto-approve off", "  turned off outside wfctl"]


def test_a_person_turning_it_off_is_shown_with_their_session(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The second line is the last change a person made, whichever way it went."""
    _session(monkeypatch, "me")
    evidence.grant_auto_approve(storyctl_dir.agent_dir, True, session="them")
    evidence.grant_auto_approve(storyctl_dir.agent_dir, False, session="me")

    lines = _show()

    assert lines[0] == "auto-approve off"
    assert lines[1].startswith("  turned off ")
    assert lines[1].endswith("by this session")


def test_the_bare_command_never_prints_a_session_id(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario 6. `status` never prints the holder's id, and neither does this."""
    _session(monkeypatch, "sess-7f3a")
    evidence.grant_auto_approve(storyctl_dir.agent_dir, True, session="sess-other-91c2")

    output = runner.invoke(app, ["auto-approve"]).output

    assert "sess-7f3a" not in output
    assert "sess-other-91c2" not in output


def test_the_bare_command_creates_no_state_dir(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """A read on a branch wfctl never used mustn't leave a directory behind."""
    state = tmp_path / "never-used"
    monkeypatch.setenv("WFCTL_STATE_DIR", str(state))

    assert _show()[:2] == ["auto-approve off", "  no grant on record"]
    assert not state.exists()


def test_the_bare_command_reads_on_a_branch_that_names_no_issue(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only `on` runs the issue check; reading the mode is never refused."""
    _refuse_the_issue(monkeypatch, *_NO_KEY)

    assert _show()[0] == "auto-approve off"


# --- User Story 4: find out an existing repo is missing the grant line ---

_SEEDED_BEFORE_407 = (
    "post_create:\n"
    '  - cd "$WM_WORKTREE_PATH" && wfctl install-skills || true\n'
    '  - cd "$WM_WORKTREE_PATH" && wfctl issue start || true\n'
)


def test_the_bare_command_prints_the_line_to_add_when_post_create_lacks_it(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Scenarios 1 - 3, and SC-004.

    `install-config` writes the seed once and never updates it, so a repo
    seeded before #407 has no other way to learn the line exists. The entry
    prints whole on one line so it pastes into YAML as it is.
    """
    from wfctl.install import GRANT_LINE

    (storyctl_dir.repo_root / ".workmux.yaml").write_text(
        _SEEDED_BEFORE_407 + f"  # - {GRANT_LINE}\nwindows:\n  - command: {GRANT_LINE}\n"
    )

    result = runner.invoke(app, ["auto-approve"])

    assert result.exit_code == 0
    assert "ℹ .workmux.yaml has no auto-approve line" in result.output
    assert f"      - {GRANT_LINE}\n" in result.output


def test_no_note_once_post_create_grants(storyctl_dir: types.SimpleNamespace) -> None:
    """This repo's own copy runs `uv run wfctl`, and that counts as the line."""
    (storyctl_dir.repo_root / ".workmux.yaml").write_text(
        _SEEDED_BEFORE_407
        + '  - cd "$WM_WORKTREE_PATH" && [ "$WFCTL_AUTO_APPROVE" = 1 ] '
        "&& uv run wfctl auto-approve on || true\n"
    )

    assert "ℹ" not in runner.invoke(app, ["auto-approve"]).output


def test_no_note_without_a_workmux_file(storyctl_dir: types.SimpleNamespace) -> None:
    """Scenario 4. A repo that doesn't use workmux has nowhere to put the line."""
    assert "ℹ" not in runner.invoke(app, ["auto-approve"]).output


def test_on_and_off_print_no_note(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario 6. The note belongs to the person checking the mode, not to every change."""
    (storyctl_dir.repo_root / ".workmux.yaml").write_text(_SEEDED_BEFORE_407)
    _session(monkeypatch, "me")
    runner.invoke(app, ["start"])

    for switch in ("on", "off"):
        assert "ℹ" not in runner.invoke(app, ["auto-approve", switch]).output


def test_doctor_says_nothing_about_the_grant_line(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Scenario 5, and FR-011. The line is opt-in.

    A repository that never uses auto-approve would otherwise see a warning on
    every `doctor` run.
    """
    (storyctl_dir.repo_root / ".workmux.yaml").write_text(_SEEDED_BEFORE_407)

    output = runner.invoke(app, ["doctor"]).output

    assert "auto-approve" not in output


def test_an_argument_other_than_on_or_off_is_a_usage_error(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`yes`, `true`, and `1` look like they'd grant, and they mustn't."""
    for word in ("yes", "true", "1"):
        result = runner.invoke(app, ["auto-approve", word])
        assert result.exit_code == 2, (word, result.output)
    assert _mode_events(storyctl_dir.agent_dir) == []
