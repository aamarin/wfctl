"""Where design approval happens, as a per-feature value (#127).

The mode is the first field on `PipelineReport` that no artifact produces — it
is a choice someone made, not a state inference read off disk. That makes two
things worth pinning that inference never needed: that it survives the commands
which run between sessions, and that losing it fails toward stopping for a
human rather than toward running without one.
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


def _payload(args: list[str] | None = None) -> dict:
    result = runner.invoke(app, args or ["status", "--json"])
    return json.loads(result.output)


def _events(agent_dir: Path) -> list[dict]:
    log = agent_dir / "events.jsonl"
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


def test_a_feature_nobody_granted_anything_to_reports_attended(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The default, asserted positively rather than by the absence of a key.

    `test_the_json_view_carries_the_auto_flag` records what happens otherwise:
    deleting `auto` from the payload left 824 tests green, because the one test
    reading that output compared it against itself. A round-trip assertion
    cannot see a field that vanished from both sides.
    """
    assert _payload()["auto_approve"] is False
    assert "auto-approve" not in runner.invoke(app, ["status"]).output


def test_the_flag_grants_the_mode_and_the_payload_carries_it(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Scope item 2: a run whose mode is invisible is a run you cannot trust.

    Scope item 5 rides on the same line and is provisional — the issue names the
    PR body, a `doctor` check and this output as candidates and says the choice
    wants one round of real use. What it has to achieve is that the records an
    auto-approving run wrote are hard to scroll past; naming them where the mode
    is announced is the cheapest thing that does.
    """
    result = runner.invoke(app, ["auto-approve", "on"])
    assert result.exit_code == 0
    assert "auto-approve" in result.output

    assert _payload()["auto_approve"] is True

    (storyctl_dir.repo_root / "docs" / "architecture").mkdir(parents=True)
    (storyctl_dir.repo_root / "docs" / "architecture" / "who-owns-the-clock.md").write_text(
        "---\nstatus: proposed\n---\n"
    )
    console = runner.invoke(app, ["status"]).output
    assert "auto-approve" in console
    assert "who-owns-the-clock" in console


def test_start_auto_approve_is_refused_and_names_the_command(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A security reviewer found `start --auto-approve` granted the mode with no
    prompt, since the host's ask rules match only `wfctl auto-approve on` and a
    flag can sit anywhere in `start`'s arguments. Refusing it leaves one grant
    form, and the one the prompt covers. The refusal runs before `start` does
    anything, so a script relying on the flag stops instead of running on with
    the mode off."""
    result = runner.invoke(app, ["start", "--force", "--auto-approve"])

    assert result.exit_code == 1
    assert "wfctl auto-approve on" in result.output
    assert _payload()["auto_approve"] is False
    assert not [e for e in _events(storyctl_dir.agent_dir) if e["event"] in ("mode", "start")]


def test_a_later_bare_start_does_not_revoke_the_mode(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The reason the option is tri-state rather than a plain `bool`.

    Defaulting to False would revoke the mode on every subsequent `wfctl start`
    — which `/start-session` runs at each handoff — ending an overnight run at
    its first context clear, silently and in the safe-looking direction.
    """
    runner.invoke(app, ["auto-approve", "on"])
    runner.invoke(app, ["start"])

    assert _payload()["auto_approve"] is True


def test_the_mode_can_be_handed_back_to_a_human(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """#100's escalate-never-waive, in the direction it permits.

    An agent may raise the bar and never lower it, so revoking has to be
    reachable — a mode that could only ever be granted would make the rule
    one-way in the wrong direction.

    Both the payload and the line, because they fail separately: a payload-only
    assertion passes over a revocation that reports nothing, which is what a
    person who typed the flag would be reading.
    """
    granted = runner.invoke(app, ["auto-approve", "on"])
    assert "auto-approve" in granted.output

    revoked = runner.invoke(app, ["start", "--no-auto-approve"])
    assert revoked.exit_code == 0
    assert "auto-approve off" in revoked.output
    assert _payload()["auto_approve"] is False




def test_each_grant_leaves_a_line_in_the_event_log(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """What makes a self-grant visible after the fact.

    `wfctl start*` is in `start-session`'s allowlist and the glob admits any
    flag, so an agent can grant itself the mode unprompted. Nothing available
    prevents that; the log is what a reader consults instead, which is why the
    file alone is not the whole store.
    """
    runner.invoke(app, ["auto-approve", "on"])
    runner.invoke(app, ["start", "--no-auto-approve"])

    grants = [e for e in _events(storyctl_dir.agent_dir) if e["event"] == "mode"]
    assert [e["auto_approve"] for e in grants] == [True, False]
    assert all("ts" in e for e in grants)


def test_a_lost_or_damaged_mode_file_reads_as_attended(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The direction the failure has to fall, across every shape of damage.

    A truncated write or a hand-edited file must leave the design gates stopping
    for a human. Reading a damaged file as a grant would let a corrupted byte
    hand an agent the authority the flag exists to gate.

    The shapes matter more than the count, and the first version of this test
    caught none of the ones that bit. `null`, `3` and `[]` all parse, so a guard
    written against `JSONDecodeError` alone lets them reach `.get`; an invalid
    UTF-8 byte raises `UnicodeDecodeError`, which is not an `OSError`. Every one
    of those reaches `build_report`, so the failure is not a wrong field — it is
    `status`, `start`, `resume` and `end` all raising for that branch.
    """
    mode_file = storyctl_dir.agent_dir / evidence.MODE_NAME
    for body in ("{not json", "null", "true", "3", "[]", '"granted"', "{}"):
        runner.invoke(app, ["auto-approve", "on"])
        mode_file.write_text(body)
        result = runner.invoke(app, ["status", "--json"])
        assert result.exit_code == 0, f"{body!r} raised: {result.output}"
        assert json.loads(result.output)["auto_approve"] is False, body

    runner.invoke(app, ["auto-approve", "on"])
    mode_file.write_bytes(b'{"auto_approve": "\xff"}')
    assert runner.invoke(app, ["status", "--json"]).exit_code == 0
    assert _payload()["auto_approve"] is False

    mode_file.unlink()
    assert _payload()["auto_approve"] is False


def test_the_mode_survives_a_finished_story(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Why the field is outside the report's None-together pairing.

    `current`, `next_command` and `auto` are all None once every step is done,
    because there is no step left to run. The mode is still true of that story
    — it ran under one — and a reviewer reading the PR is asking exactly then.
    """
    runner.invoke(app, ["auto-approve", "on"])
    storyctl_dir.stage_upstream_of("tasks")
    storyctl_dir.make_spec_artifact("decompose")
    (storyctl_dir.spec_dir / "checklists" / "implement-complete.md").write_text("done\n")

    payload = _payload()
    assert (payload["current"], payload["next_command"], payload["auto"]) == (None, None, None)
    assert payload["auto_approve"] is True


def test_resume_says_the_mode_on_its_own_line(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """#127's named mitigation: `auto` and `auto_approve` are different questions.

    `resume` already prints `(auto: …)` for whether this step advances
    unprompted. Folding the mode into that parenthetical is what the issue says
    will make the two read as one axis.

    The two values have to disagree, or a `resume` that printed the mode into the
    `(auto: …)` slot — the fold this test forbids — reads identical to one that
    did not. `clarify` supplied the disagreement until #325 flipped it; no step is
    `review_required` now, so it comes from a blocked step instead. A design
    document with no record behind it is the cheapest one, and it is also the
    sharper case for this test's own subject: `auto_approve` moves where a design
    gate is answered, and a gate nobody answered at all still blocks under it.
    """
    runner.invoke(app, ["start"])
    runner.invoke(app, ["auto-approve", "on"])
    storyctl_dir.make_spec_artifact("brainstorm")

    output = runner.invoke(app, ["resume"]).output

    assert "auto-approve" in output
    assert "(auto: false)" in output
    mode_line = next(line for line in output.splitlines() if "auto-approve" in line)
    assert "(auto:" not in mode_line


# --- #407: the grant helper's session field, write order, and repeat skip ---


def _mode_events(agent_dir: Path) -> list[dict]:
    return [e for e in _events(agent_dir) if e["event"] == "mode"]


def test_a_grant_names_the_session_that_made_it(tmp_path: Path) -> None:
    """A grant the agent can make on its own is only checkable afterwards.

    wfctl can't tell a grant someone asked for from one nobody did, so the event
    carries the session. Without it, a reviewer asking how an unattended run got
    the mode has a timestamp and nothing to compare it with.
    """
    evidence.grant_auto_approve(tmp_path, True, session="abc")

    assert _mode_events(tmp_path)[-1]["session"] == "abc"


def test_a_grant_from_a_caller_with_no_identity_writes_no_session_key(tmp_path: Path) -> None:
    """One absent shape for "unknown", not two.

    Events written before #407 have no `session` key. Writing `session: null`
    for a caller with no identity would give readers a second spelling of the
    same fact to handle.
    """
    evidence.grant_auto_approve(tmp_path, True)

    assert "session" not in _mode_events(tmp_path)[-1]


def test_a_repeated_on_appends_nothing_and_keeps_the_review_count(tmp_path: Path) -> None:
    """Every `mode` event with `auto_approve: true` restarts the review count.

    If a repeated `on` appended one, an agent could hand itself three more plan
    reviews by running `on` before the cap fired, which is the bypass the cap
    exists to close.
    """
    from wfctl._plan_review import review_count

    evidence.grant_auto_approve(tmp_path, True, session="abc")
    append_resume = (tmp_path / "events.jsonl").open("a")
    append_resume.write(json.dumps({"event": "resume", "review": "h1"}) + "\n")
    append_resume.write(json.dumps({"event": "resume", "review": "h2"}) + "\n")
    append_resume.close()
    before = review_count(tmp_path, "418-storyctl")

    evidence.grant_auto_approve(tmp_path, True, session="abc")

    assert len(_mode_events(tmp_path)) == 1
    assert review_count(tmp_path, "418-storyctl") == before == 2


def test_on_over_a_hand_written_mode_file_writes_the_grant(tmp_path: Path) -> None:
    """The skip needs a grant on record, not just a mode file that reads on.

    A hand-written `mode.json` leaves no event, so the review cap has nothing to
    count from and never fires. The `on` that follows has to write the grant to
    give the cap its starting point.
    """
    (tmp_path / evidence.MODE_NAME).write_text('{"auto_approve": true}')

    evidence.grant_auto_approve(tmp_path, True, session="abc")

    assert [e["auto_approve"] for e in _mode_events(tmp_path)] == [True]


def test_on_over_a_hand_edit_made_after_a_revocation_writes_the_grant(tmp_path: Path) -> None:
    """The newest event decides, not the last grant.

    After the cap revokes, a hand edit back to on leaves an older grant in the
    log. Checking for "any grant" would skip the write, and the cap would count
    from a grant it already ended.
    """
    evidence.grant_auto_approve(tmp_path, True, session="abc")
    evidence.revoke_auto_approve(tmp_path, "cap fired")
    (tmp_path / evidence.MODE_NAME).write_text('{"auto_approve": true}')

    evidence.grant_auto_approve(tmp_path, True, session="abc")

    assert [e["auto_approve"] for e in _mode_events(tmp_path)] == [True, False, True]


def test_on_after_a_revocation_is_a_new_grant(tmp_path: Path) -> None:
    """A revoked mode reads as off, so `on` grants again and the count restarts.

    The record gives three more reviews after a revocation only through a new
    grant, and this is that grant.
    """
    evidence.grant_auto_approve(tmp_path, True)
    evidence.revoke_auto_approve(tmp_path, "cap fired")

    evidence.grant_auto_approve(tmp_path, True)

    assert evidence.auto_approve(tmp_path) is True
    assert evidence.revoked(tmp_path) is None
    assert [e["auto_approve"] for e in _mode_events(tmp_path)] == [True, False, True]


def test_off_always_writes(tmp_path: Path) -> None:
    """`off` never resets the review count, so it has no reason to skip.

    Skipping a repeated `off` would leave nothing in the log when a person turns
    off a mode that a hand edit turned on.
    """
    evidence.grant_auto_approve(tmp_path, False)
    evidence.grant_auto_approve(tmp_path, False)

    assert [e["auto_approve"] for e in _mode_events(tmp_path)] == [False, False]


def test_a_failed_append_leaves_the_mode_file_as_it_was(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The event goes first, so a failed append changes nothing.

    In the other order, a failed append after `on` would leave the mode on with
    no grant in the log, and the review cap would never fire.
    """
    import wfctl.evidence._mode as mode

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(mode, "append_event", fail)

    with pytest.raises(OSError):
        evidence.grant_auto_approve(tmp_path, True)

    assert not (tmp_path / evidence.MODE_NAME).exists()


def test_a_failed_file_write_after_the_append_leaves_the_old_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The spec's first edge case: the event lands and the file write fails.

    The mode keeps its old value, which after `on` is off, the safe direction.
    The bare command then reports the mismatch, and the next `on` or `off`
    repairs it.
    """
    import wfctl.evidence._mode as mode

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(mode, "write_atomic", fail)

    with pytest.raises(OSError):
        evidence.grant_auto_approve(tmp_path, True, session="abc")

    assert evidence.auto_approve(tmp_path) is False
    assert [e["auto_approve"] for e in _mode_events(tmp_path)] == [True]


# --- #407: the two readers the bare command needs ---


def test_last_change_is_none_with_no_mode_events(tmp_path: Path) -> None:
    """"No grant on record" needs its own answer, distinct from an old grant."""
    assert evidence.last_change(tmp_path) is None


def test_last_change_is_the_newest_change_a_person_made(tmp_path: Path) -> None:
    """The bare command shows who turned the mode on or off, whichever was last."""
    evidence.grant_auto_approve(tmp_path, True, session="abc")
    evidence.grant_auto_approve(tmp_path, False, session="def")

    change = evidence.last_change(tmp_path)

    assert change is not None
    assert (change.on, change.session) == (False, "def")
    assert change.ts


def test_last_change_skips_the_review_caps_revocation(tmp_path: Path) -> None:
    """The cap isn't a person, and after it fires the reader wants the grant it ended.

    Reading the revocation as a change would print "turned off by an unknown
    session" over a mode a named session turned on.
    """
    evidence.grant_auto_approve(tmp_path, True, session="abc")
    evidence.revoke_auto_approve(tmp_path, "cap fired")

    change = evidence.last_change(tmp_path)

    assert change is not None
    assert (change.on, change.session) == (True, "abc")


def test_a_grant_written_before_407_reads_as_no_session(tmp_path: Path) -> None:
    """Old events have no `session`, and they read as an unknown session."""
    (tmp_path / "events.jsonl").write_text(
        json.dumps({"ts": "2026-11-01T10:00:00Z", "event": "mode", "auto_approve": True}) + "\n"
    )

    change = evidence.last_change(tmp_path)

    assert change is not None
    assert change.session is None


def test_newest_is_grant_reads_the_newest_mode_event_of_any_kind(tmp_path: Path) -> None:
    """The skip and the bare command both read this, so they agree on when a grant stands.

    The revocation counts as newest. Otherwise a hand edit after the cap fired
    would look like it had a grant behind it.
    """
    assert evidence.newest_is_grant(tmp_path) is False

    evidence.grant_auto_approve(tmp_path, True)
    assert evidence.newest_is_grant(tmp_path) is True

    evidence.revoke_auto_approve(tmp_path, "cap fired")
    assert evidence.newest_is_grant(tmp_path) is False

    evidence.grant_auto_approve(tmp_path, True)
    evidence.grant_auto_approve(tmp_path, False)
    assert evidence.newest_is_grant(tmp_path) is False


def test_a_mode_change_waits_while_another_holds_the_lock(tmp_path: Path) -> None:
    """A code reviewer found an `on` and an `off` running together could leave
    the file on while the newest event said off, since each change is two
    writes in a different order. A change waits for the one already writing."""
    import fcntl
    import os
    import threading

    fd = os.open(tmp_path / "mode.lock", os.O_RDWR | os.O_CREAT, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)
    worker = threading.Thread(target=evidence.grant_auto_approve, args=(tmp_path, True))
    worker.start()
    worker.join(timeout=0.5)
    try:
        assert worker.is_alive()
        assert not evidence.auto_approve(tmp_path)
    finally:
        os.close(fd)
    worker.join(timeout=5)
    assert evidence.auto_approve(tmp_path)
