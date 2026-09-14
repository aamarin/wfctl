"""The session commands, after the resume point stopped being a file.

`wfctl start` used to write `current.json` and `current.md`, and every later
read answered from them. Both were written once and never again, so a session
that ran a pipeline step and came back was told where it had been, not where it
was (#42). These assert the shape that replaced them: nothing is written but the
event log and the handoff prose, and every other value is computed when asked.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import CLEAN_SPEC
from wfctl import _session
from wfctl.cli import app

runner = CliRunner()


def _run(*args: str) -> str:
    result = runner.invoke(app, list(args))
    assert result.exit_code == 0, result.output
    return result.output


# ─── Nothing is written that could go stale ──────────────────────────────────

def test_start_writes_no_resume_point(agent_dir: Path) -> None:
    """The two files whose staleness is #42. Neither is written by anything now."""
    _run("start")
    assert not (agent_dir / "current.json").exists()
    assert not (agent_dir / "current.md").exists()


def test_no_command_recreates_the_files_it_no_longer_reads(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Walks the session commands, not just `start`.

    A single write left anywhere in the lifecycle brings the stale resume point
    back, and it would be invisible to a test that only ran the first command.
    """
    for args in (["start"], ["status"], ["next"], ["resume"], ["end"]):
        runner.invoke(app, args)
        for name in ("current.json", "current.md"):
            assert not (storyctl_dir.agent_dir / name).exists(), f"{name} after {args}"


# ─── The position is computed on every read ──────────────────────────────────

def test_the_position_follows_the_artifacts_with_no_command_in_between(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """#42 stated as a test: the artifacts move, nothing is run, the answer moves.

    Under the old shape `status` reported the step written at `wfctl start`, so
    an agent that ran `/speckit.brainstorm` and asked again was sent to
    brainstorm a second time.
    """
    _run("start")
    assert "brainstorm   ○  ← current" in _run("status")

    storyctl_dir.make_spec_artifact("brainstorm")

    # The artifact moved the step off `pending`; the boundary question is what
    # finishes it, so the design gate holds it at `▶` until a record answers.
    assert "brainstorm   ▶" in _run("status")

    arch = storyctl_dir.repo_root / "docs" / "architecture"
    arch.mkdir(parents=True, exist_ok=True)
    (arch / "a-boundary.md").write_text("---\nstatus: proposed\n---\n\n# x\n")

    assert "brainstorm   ●" in _run("status")
    assert "specify      ○  ← current" in _run("status")


def test_switching_branch_is_reflected_without_a_command_in_between(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The branch was seeded into `current.json` at start and never re-read.

    A worktree switched underneath a live session kept answering about the branch
    it opened on.
    """
    _run("start")
    assert "#418  418-storyctl" in _run("status")

    monkeypatch.setenv("WFCTL_BRANCH", "999-somewhere-else")

    assert "#999  999-somewhere-else" in _run("status")


# ─── Every field the deleted file carried is still answered (FR-011) ─────────

def test_each_field_the_session_file_carried_is_still_answered(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Named field by field, because a field can vanish without a line changing.

    `current.json` held issue, branch, repo, workflow_step, next_command,
    updated and status. Deleting the file is only safe if each is reachable from
    somewhere else, and a rendered-output test cannot show that — it asserts the
    lines it knows about and is silent on the field nobody printed.

    `status` is the exception and is deliberately not here: it had no reader at
    all, and work status is the pipeline.
    """
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    _run("start")

    status = _run("status")
    assert "#418" in status                    # issue — extract_issue_key, on every read
    assert "418-storyctl" in status            # branch — resolve_branch, on every read
    assert "plan         ○  ← current" in status   # workflow_step — _infer_steps
    assert "next: /speckit.plan" in status     # next_command — next_step_content

    # repo — resolved from git, and what the state dir is keyed by
    assert storyctl_dir.agent_dir.exists()

    # updated — the last event's timestamp, recorded as it happens rather than
    # rewritten to stay true
    last = json.loads((storyctl_dir.agent_dir / "events.jsonl").read_text().splitlines()[-1])
    assert last["ts"]


# ─── start ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "branch,expected",
    [
        ("342-state-workflow", "342"),
        ("419_auth_lifecycle_update", "419"),
        ("dev", "unknown"),
        ("no-number-here", "unknown"),
    ],
)
def test_the_issue_key_is_read_off_the_branch_on_every_read(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, branch: str, expected: str
) -> None:
    monkeypatch.setenv("WFCTL_BRANCH", branch)
    assert f"#{expected}" in _run("status")


def test_start_infers_the_step_rather_than_naming_a_placeholder(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """It must never report the literal 'start' — that is a placeholder, not a position."""
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    storyctl_dir.make_spec_artifact("plan")

    output = _run("start")

    assert "step: tasks" in output
    assert "next: /speckit.tasks" in output


def test_start_appends_the_event_that_is_now_the_session(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The one fact re-derivation cannot reach, so it is the one thing recorded."""
    _run("start")
    first = json.loads(
        (storyctl_dir.agent_dir / "events.jsonl").read_text().splitlines()[0]
    )
    assert first["event"] == "start"


def test_start_is_idempotent(storyctl_dir: types.SimpleNamespace) -> None:
    _run("start")
    events_before = (storyctl_dir.agent_dir / "events.jsonl").read_text()

    assert "Already initialized" in _run("start")
    assert (storyctl_dir.agent_dir / "events.jsonl").read_text() == events_before


def test_start_force_opens_a_session_over_an_existing_one(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    _run("start")
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    storyctl_dir.make_spec_artifact("plan")

    assert "step: tasks" in _run("start", "--force")


def test_start_outside_a_git_repo_exits_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    monkeypatch.delenv("WFCTL_BRANCH", raising=False)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 1
    assert "git" in result.output.lower()


# ─── resume and end refuse on the event log, not on a file ───────────────────

@pytest.mark.parametrize("command", ["resume", "end"])
def test_a_branch_with_no_start_event_has_no_session(
    agent_dir: Path, command: str
) -> None:
    result = runner.invoke(app, [command])
    assert result.exit_code == 1
    assert "No session found for this branch" in result.output


def test_end_writes_the_summary_once(agent_dir: Path) -> None:
    """Second `end` must not overwrite prose a human or agent filled in."""
    _run("start")
    _run("end")
    original = (agent_dir / "session-summary.md").read_text()

    _run("end")

    assert (agent_dir / "session-summary.md").read_text() == original


# ─── Who holds the branch, and whether that is you ───────────────────────────

def _log(agent_dir: Path, *events: dict) -> None:
    (agent_dir / "events.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in events)
    )


def test_last_session_id_reads_the_most_recent_start(agent_dir: Path) -> None:
    """`session_started` reads the first `start`; this has to read the last.

    A takeover appends a `start` line rather than rewriting one, so a reader that
    stopped at the first match would report the conversation that opened the
    branch as holding it forever — which is #200's own defect, reintroduced one
    function over.
    """
    _log(
        agent_dir,
        {"event": "start", "session_id": "first"},
        {"event": "resume"},
        {"event": "start", "session_id": "second"},
    )
    assert _session.last_session_id(agent_dir) == "second"


def test_a_start_line_carrying_no_identity_leaves_the_holder_absent(
    agent_dir: Path,
) -> None:
    """Every branch recorded before this feature looks like this.

    The holder has to come back absent rather than as some earlier line's value,
    or a takeover would be refused on exactly the branches FR-012 exists for.
    """
    _log(
        agent_dir,
        {"event": "start", "session_id": "was-here"},
        {"event": "start"},
    )
    assert _session.last_session_id(agent_dir) is None


def test_last_session_id_skips_a_line_that_is_not_an_object(
    agent_dir: Path,
) -> None:
    """`json.loads` succeeds on `3`, `null` and `[]`, and none of them has `.get`.

    Both readers are on the path of every gate, so an unguarded line here would
    refuse the whole branch — `session_started` guards the same way now, which
    the next test pins.
    """
    (agent_dir / "events.jsonl").write_text(
        '3\nnull\n[]\nnot json at all\n{"event": "start", "session_id": "held"}\n'
    )
    assert _session.last_session_id(agent_dir) == "held"


def test_session_started_skips_a_line_that_is_not_an_object(
    agent_dir: Path,
) -> None:
    """The parity `last_session_id`'s docstring used to claim without a guard.

    `json.loads("3").get("event")` raises `AttributeError`, uncaught — only
    `JSONDecodeError` was caught, so a line that parses but isn't an object used
    to take down a reader on the path of every gate.
    """
    (agent_dir / "events.jsonl").write_text(
        '3\nnull\n[]\nnot json at all\n{"event": "start", "session_id": "held"}\n'
    )
    assert _session.session_started(agent_dir) is True


def test_session_open_for_returns_unknown_when_no_id_presented(
    agent_dir: Path,
) -> None:
    """FR-006 in one call: an unwired caller gets the answer that changes nothing.

    `"unknown"` and not `"other"` — the gates refuse on `"other"`, so returning
    it here would refuse every repository that never set `WFCTL_SESSION_ID`.
    """
    _log(agent_dir, {"event": "start", "session_id": "someone"})
    assert _session.session_open_for(agent_dir, None) == "unknown"


def test_a_shared_state_dir_does_not_let_one_branch_answer_for_another(
    agent_dir: Path,
) -> None:
    """`WFCTL_STATE_DIR` can point several branches at one log (`_paths.py:672-676`).

    `opens_a_new_sitting` already filters its own reads by branch for this
    reason (`_stall.py:174`); `last_session_id` and `session_open_for` read the
    identical log shape and did not, so a `start` on branch "b" was read as
    branch "a"'s holder — the exact risk
    `session-identity-comes-from-the-caller` names for a value stored unscoped.
    """
    _log(
        agent_dir,
        {"event": "start", "branch": "a", "session_id": "on-a"},
        {"event": "start", "branch": "b", "session_id": "on-b"},
    )
    assert _session.last_session_id(agent_dir, branch="a") == "on-a"
    assert _session.session_open_for(agent_dir, "on-a", branch="a") == "self"
    assert _session.session_open_for(agent_dir, "on-a", branch="b") == "other"


def test_session_started_does_not_let_one_branch_answer_for_another(
    agent_dir: Path,
) -> None:
    """The same risk, one call earlier than the test above.

    `session_started` used to scan for any `"start"` line with no branch filter
    at all, while the holder scan two lines later in `session_open_for` was
    already scoped. Under a shared `WFCTL_STATE_DIR`, branch "b" here never ran
    `start` — but inherited branch "a"'s line, so `session_open_for` fell through
    past `"none"` to the holder scan, found no holder on branch "b", and
    answered `"unknown"` instead. `"unknown"` is the row `resume` and the
    orchestrate gate let through unattended (FR-006) — the wrong row for a
    branch that never started at all.
    """
    _log(agent_dir, {"event": "start", "branch": "a", "session_id": "on-a"})
    assert _session.session_started(agent_dir, branch="b") is False
    assert _session.session_open_for(agent_dir, "on-a", branch="b") == "none"


@pytest.mark.parametrize(
    "holder, presented, expected",
    [
        (None, "anyone", "none"),
        ("me", "me", "self"),
        ("me", "you", "other"),
        ("absent", None, "unknown"),
    ],
    ids=["never-started", "caller-holds-it", "another-holds-it", "caller-unwired"],
)
def test_the_holder_relation_covers_every_state_the_contract_names(
    agent_dir: Path, holder: str | None, presented: str | None, expected: str
) -> None:
    """The four rows of contracts/cli.md § `wfctl status --json`, as one table.

    Written as a parametrised case rather than four functions because the states
    are exclusive and a fifth answer appearing is the failure — which is only
    visible when they are asserted against one another.
    """
    if holder is not None:
        _log(agent_dir, {"event": "start", "session_id": holder})
    assert _session.session_open_for(agent_dir, presented) == expected


def test_a_branch_with_no_start_event_is_none_rather_than_unknown(
    agent_dir: Path,
) -> None:
    """Both leave `session_open` false; only one of them names a remedy.

    A caller that presented nothing on a branch that never had a session is in
    both rows of the contract's table. `"none"` is asked first because it is the
    answer that tells the reader to run `/start-session`.
    """
    assert _session.session_open_for(agent_dir, None) == "none"


def test_empty_session_id_is_absent_not_an_identity(agent_dir: Path) -> None:
    """`${WFCTL_SESSION_ID:+…}` already collapses unset and empty.

    The shipped skill passes the identity through that expansion, so a caller
    with the variable set to `""` omits the flag entirely while one that spells
    `--session-id ""` does not. Both did the same thing and must get the same
    answer, or the behaviour depends on which shell form ran.
    """
    _log(agent_dir, {"event": "start", "session_id": "held"})
    for blank in ("", "   ", "\t\n"):
        assert _session.identity(blank) is None
        assert _session.session_open_for(agent_dir, blank) == "unknown"


def test_a_blank_identity_on_a_start_line_leaves_the_holder_absent(
    agent_dir: Path,
) -> None:
    """The same rule applied at the other end, where a blank could be written.

    Stripping only on the way in would let `--session-id "  "` record a holder
    that no later caller can ever match, wedging the branch for everyone.
    """
    _log(agent_dir, {"event": "start", "session_id": "   "})
    assert _session.last_session_id(agent_dir) is None
    assert _session.session_open_for(agent_dir, "anyone") == "unknown"


def test_the_identity_adds_no_file_to_the_state_dir(agent_dir: Path) -> None:
    """FR-010 forbids a separate file, and every other test here would pass one.

    The rejected alternative in
    `docs/architecture/design/200-session-id-rides-on-the-start-event.md` is a
    `session.json` beside `notify.json` — fifteen lines, and the shape a reader
    reaches for first. Nothing else asserted the negative, so adding it later
    would go green: the holder relation would still be right, and only the crash
    behaviour the record rejected it for would differ.
    """
    before = sorted(p.name for p in agent_dir.iterdir())
    runner.invoke(app, ["start", "--session-id", "first"])
    runner.invoke(app, ["start", "--session-id", "second"])
    after = sorted(p.name for p in agent_dir.iterdir())

    assert set(after) - set(before) == {"events.jsonl"}


# ─── The takeover, and the exit it gives a displaced conversation ────────────

def _starts(agent_dir: Path) -> list[dict]:
    """Every `start` line in the log, in order — what a takeover appends to."""
    lines = (agent_dir / "events.jsonl").read_text().splitlines()
    return [
        data for line in lines
        if isinstance(data := json.loads(line), dict) and data.get("event") == "start"
    ]


def test_start_with_a_new_id_appends_a_start_event(agent_dir: Path) -> None:
    """A different identity takes the branch over rather than being refused.

    `start` is the reversible move (contracts/cli.md): presenting an id the
    branch does not already hold is not an error, it is how a displaced
    conversation gets the branch back.
    """
    runner.invoke(app, ["start", "--session-id", "first"])

    result = runner.invoke(app, ["start", "--session-id", "second"])

    assert result.exit_code == 0
    starts = _starts(agent_dir)
    assert len(starts) == 2
    assert starts[-1]["session_id"] == "second"


def test_a_second_sitting_with_the_same_id_keeps_the_holder(
    agent_dir: Path,
) -> None:
    """`start` → `resume` → `start` under one identity must not drop it.

    The sitting-boundary append (cli.py, the path every session after the first
    takes) used to omit `session_id` even when the caller presented one, which
    reset `last_session_id` to absent and reopened the branch to the next
    identity that showed up — the exact defect #200 exists to close, on the path
    every ordinary `/start-session` re-run takes.
    """
    runner.invoke(app, ["start", "--session-id", "mine"])
    runner.invoke(app, ["resume"])

    result = runner.invoke(app, ["start", "--session-id", "mine"])

    assert result.exit_code == 0
    assert _session.last_session_id(agent_dir) == "mine"
    assert _session.session_open_for(agent_dir, "mine") == "self"


def test_a_wrapped_up_session_no_longer_reads_open_to_itself(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`start` → `end` → `status`, all as the same identity, must not read open.

    The accepted design record states the criterion twice — "a session is open
    when the id a command presents matches the id on the most recent `start`
    event, **and no `end` event follows it**" (Decision), and `data-model.md`
    calls this "not a state": a branch whose session was wrapped up is state C
    to the *next* reader "the same string, the same remedy" whether that reader
    is a different conversation or the one that ended it. Neither `end` nor
    `session_open_for` inspected `"end"` events before this test, so ending a
    session left it reading open to itself indefinitely.
    """
    runner.invoke(app, ["start", "--session-id", "mine"])
    monkeypatch.setenv("WFCTL_SESSION_ID", "mine")

    _run("end")

    assert _session.session_open_for(agent_dir, "mine") == "other"


def test_a_caller_with_no_id_never_takes_over(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-006: an unwired caller must never displace a wired holder.

    Presenting no identity is not "a different identity" — `caller is None`
    short-circuits the takeover branch before the holder is even compared.
    `WFCTL_SESSION_ID` is cleared explicitly: `--session-id` falls back to it,
    and this test needs "presented nothing" to mean that regardless of what a
    developer's own shell happens to export.
    """
    monkeypatch.delenv("WFCTL_SESSION_ID", raising=False)
    runner.invoke(app, ["start", "--session-id", "held"])

    result = runner.invoke(app, ["start"])

    assert result.exit_code == 0
    assert "Already initialized" in result.output
    starts = _starts(agent_dir)
    assert len(starts) == 1
    assert starts[0]["session_id"] == "held"


def test_takeover_is_announced(agent_dir: Path) -> None:
    """SC-007: the console names the takeover rather than reading as routine.

    `"Already initialized"` on a takeover would tell the caller nothing changed,
    when a different conversation now holds the branch.
    """
    runner.invoke(app, ["start", "--session-id", "first"])

    result = runner.invoke(app, ["start", "--session-id", "second"])

    assert "took over from another conversation" in result.output
    assert "Already initialized" not in result.output


def test_a_branch_recorded_before_identities_accepts_the_first_one(
    agent_dir: Path,
) -> None:
    """FR-012: a holder-absent branch — every branch predating this feature.

    The first identified caller takes the branch rather than being refused. The
    branch already looks like the released version, and the released version
    never refused anyone.
    """
    runner.invoke(app, ["start"])
    assert _starts(agent_dir)[0].get("session_id") is None

    result = runner.invoke(app, ["start", "--session-id", "first"])

    assert "took over from another conversation" in result.output
    assert _starts(agent_dir)[-1]["session_id"] == "first"


def test_takeover_appends_and_never_rewrites(agent_dir: Path) -> None:
    """The history of who held the branch survives every takeover.

    `events.jsonl` is append-only end to end
    (`docs/architecture/design/200-session-id-rides-on-the-start-event.md`); a
    reader asking who held the branch a moment ago still finds the answer.
    """
    runner.invoke(app, ["start", "--session-id", "first"])
    first_line = (agent_dir / "events.jsonl").read_text().splitlines()[0]

    runner.invoke(app, ["start", "--session-id", "second"])
    runner.invoke(app, ["start", "--session-id", "third"])

    lines = (agent_dir / "events.jsonl").read_text().splitlines()
    assert lines[0] == first_line
    starts = _starts(agent_dir)
    assert [s["session_id"] for s in starts] == ["first", "second", "third"]


def test_abandoned_sessions_need_no_cleanup(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SC-004: a sequence of interrupted sessions resolves with no file touched.

    Open, abandon without `end`, take over, abandon again, take over again — and
    every gate along the way answers from the log alone. `resume` reads its
    identity from the environment (`_caller_identity`; `resume` and `end` carry
    no `--session-id` flag), so each conversation is a `monkeypatch.setenv`
    rather than a CLI option. Nothing here deletes or edits a file by hand, which
    is the property the direct baseline (`session.json`) could not offer: it
    would need clearing on every abandon.

    `next-step.md` is `resume`'s own ordinary output, written on every
    successful call whether or not a takeover happened — not the manual
    cleanup this test is checking for the absence of.
    """
    before = sorted(p.name for p in agent_dir.iterdir())

    def resume_as(session_id: str) -> int:
        monkeypatch.setenv("WFCTL_SESSION_ID", session_id)
        return runner.invoke(app, ["resume"]).exit_code

    runner.invoke(app, ["start", "--session-id", "a"])
    assert resume_as("a") == 0

    # "a" abandons — no `end` — and "b" takes over without deleting or editing
    # anything.
    assert resume_as("b") != 0
    runner.invoke(app, ["start", "--session-id", "b"])
    assert resume_as("b") == 0
    assert resume_as("a") != 0

    # "b" abandons in turn; "a" takes the branch back the same way.
    runner.invoke(app, ["start", "--session-id", "a"])
    assert resume_as("a") == 0
    assert resume_as("b") != 0

    after = sorted(p.name for p in agent_dir.iterdir())
    assert set(after) - set(before) == {"events.jsonl", "next-step.md"}
