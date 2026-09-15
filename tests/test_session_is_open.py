"""Is a session open *now*, and is it yours — the second session question (#200).

`test_session_existence.py` covers the first one: has a session ever run on this
branch. It is true from the first `start` line a branch ever recorded and nothing
rescinds it, so six speckit skills gated on it were asking "has anyone ever
worked here" while reading the answer as "am I the one working here".

These assert the second question beside the first, never instead of it. Every
test that pins `session_started` unchanged lives in its own file and is SC-006;
what is here is the new answer and the refusals it makes possible.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl._io import append_event
from wfctl._pipeline import build_report
from wfctl.cli import app

runner = CliRunner()


def _report(tmp_path: Path, agent_dir: Path, session_id: str | None = None):
    return build_report(None, tmp_path, agent_dir, session_id)


# ─── The report carries both answers ─────────────────────────────────────────

def test_report_carries_both_session_answers(agent_dir: Path, tmp_path: Path) -> None:
    """One inference, two questions — `pipeline-state-is-one-payload`.

    Derived in `build_report` rather than by whoever needs it, because a second
    reader of the same log is a second chance to disagree with it, and the
    console and the JSON would then be two inferences rather than two renderings.
    """
    append_event(agent_dir, "start", session_id="mine")

    report = _report(tmp_path, agent_dir, "mine")

    assert report.session_started is True
    assert report.session_open is True
    assert report.session_holder == "self"


def test_build_report_without_an_id_reports_unknown(
    agent_dir: Path, tmp_path: Path
) -> None:
    """The default exists so every caller that predates this keeps its answer.

    `None` is not a placeholder for something wfctl could work out. The caller
    owns the identity and wfctl cannot derive it
    (`session-identity-comes-from-the-caller`), so "nothing was presented" is the
    honest input and `"unknown"` — mirroring `session_started` — is the honest
    output.
    """
    append_event(agent_dir, "start", session_id="someone-else")

    report = _report(tmp_path, agent_dir)

    assert report.session_holder == "unknown"
    assert report.session_open is report.session_started is True


@pytest.mark.parametrize(
    "started", [True, False], ids=["a-session-has-run", "never-started"]
)
def test_unwired_caller_sees_the_released_answer(
    agent_dir: Path, tmp_path: Path, started: bool
) -> None:
    """FR-006, SC-002: `session_open` mirrors `session_started` under `"unknown"`.

    Named for the row `contracts/cli.md` calls D — a caller presenting nothing —
    and parametrised over both values `session_started` can hold, because a
    mirror that only agreed on `True` would still regress a fresh branch that
    never ran `wfctl start` at all.
    """
    if started:
        append_event(agent_dir, "start", session_id="someone")

    report = _report(tmp_path, agent_dir, None)

    assert report.session_open is report.session_started is started


def test_a_held_branch_reports_open_false_to_another_conversation(
    agent_dir: Path, tmp_path: Path
) -> None:
    """#200 stated as an assertion: the two answers have to be able to disagree.

    `session_started` stays true — a session did run here — while `session_open`
    goes false, because the conversation asking is not the one in it. A change
    that repointed the old field instead would make this test impossible to
    write.
    """
    append_event(agent_dir, "start", session_id="theirs")

    report = _report(tmp_path, agent_dir, "mine")

    assert report.session_started is True
    assert report.session_open is False
    assert report.session_holder == "other"


# ─── What `status --json` publishes ──────────────────────────────────────────

def test_json_payload_carries_the_new_fields(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both keys always present, never omitted — the payload's rule applied again.

    A consumer reading a missing key as false cannot tell a closed session from a
    wfctl too old to know the question, and `speckit-orchestrate` is the consumer:
    it gates on `session_open` and would read absence as "not open" on every
    older wfctl.
    """
    monkeypatch.setenv("WFCTL_SESSION_ID", "mine")
    runner.invoke(app, ["start"])

    payload = json.loads(runner.invoke(app, ["status", "--json"]).output)

    assert payload["session_started"] is True
    assert payload["session_open"] is True
    assert payload["session_holder"] == "self"


def test_the_payload_never_carries_the_identity_itself(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`data-model.md`: the holder is reported as a fact about whether it is you.

    Printing the value would make it copyable, and a second conversation that
    copied it would hold the branch without ever having opened a session — which
    defeats the gate rather than passing it.
    """
    monkeypatch.setenv("WFCTL_SESSION_ID", "a-very-distinctive-identity")
    runner.invoke(app, ["start"])

    output = runner.invoke(app, ["status", "--json"]).output

    assert "a-very-distinctive-identity" not in output


# ─── Two refusals, and the gates that print them ─────────────────────────────

def test_the_two_refusals_are_distinct(agent_dir: Path) -> None:
    """FR-007, asserted as distinctness rather than as either one's wording.

    Pinning the strings would fail the suite on a copy edit, which teaches the
    next person to change the test rather than think about it. What has to hold
    is that a reader can tell the two states apart from the string alone — so
    neither may be a substring of the other either, or the shorter one would
    match inside the longer in any `in` check downstream.
    """
    from wfctl.cli import _HELD_ELSEWHERE, _NO_SESSION

    assert _NO_SESSION != _HELD_ELSEWHERE
    assert _NO_SESSION not in _HELD_ELSEWHERE
    assert _HELD_ELSEWHERE not in _NO_SESSION


def test_resume_refuses_a_conversation_that_does_not_hold_the_branch(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`resume` keeps its own guard even though orchestrate gates before it.

    `speckit-orchestrate` gates at step 0 and calls `wfctl resume` at step 3, so
    on a pipeline run both fire and this looks redundant. It is not: `resume` is
    also typed by hand, and that path reaches this guard and no gate at all.
    """
    monkeypatch.setenv("WFCTL_SESSION_ID", "first")
    runner.invoke(app, ["start"])

    monkeypatch.setenv("WFCTL_SESSION_ID", "second")
    result = runner.invoke(app, ["resume"])

    assert result.exit_code == 1
    assert "this conversation" in result.output


def test_end_refuses_rather_than_taking_over(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Where `end` parts company with `start`, and why it is the asymmetric one.

    A takeover is reversible: the displaced conversation runs `/start-session`
    and takes the branch back. Ending someone else's session writes *their*
    handoff, and `end` writes `session-summary.md` once and never again — so the
    prose they would have written has nowhere left to go.
    """
    monkeypatch.setenv("WFCTL_SESSION_ID", "first")
    runner.invoke(app, ["start"])

    monkeypatch.setenv("WFCTL_SESSION_ID", "second")
    result = runner.invoke(app, ["end"])

    assert result.exit_code == 1
    assert not (storyctl_dir.agent_dir / "session-summary.md").exists()


def test_console_names_the_holder_relation(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SC-005 on the console, where a person reads it rather than a skill.

    The JSON carries `session_holder`, and nobody reads JSON to find out why a
    command just refused them. Without this line the held state and a fresh
    branch render identically.
    """
    monkeypatch.setenv("WFCTL_SESSION_ID", "first")
    runner.invoke(app, ["start"])

    monkeypatch.setenv("WFCTL_SESSION_ID", "second")
    held = runner.invoke(app, ["status"]).output

    monkeypatch.setenv("WFCTL_SESSION_ID", "first")
    mine = runner.invoke(app, ["status"]).output

    assert "this branch is not open for you" in held
    assert "this branch is not open for you" not in mine


def test_the_warning_does_not_name_a_party_that_may_not_exist(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same console warning covers both readings of state C.

    `session_holder == "other"` fires for a genuinely different holder and for
    the caller's own session, wrapped up with no `start` since — `data-model.md`
    § State transitions calls the second one "not a state": the same string as
    the first. Wording that claimed "another conversation holds this branch"
    was true of the first reading and false of the second — the ordinary case of
    checking `status` right after `/end-session` on the very branch you were
    just working on.
    """
    monkeypatch.setenv("WFCTL_SESSION_ID", "mine")
    runner.invoke(app, ["start"])
    runner.invoke(app, ["end"])

    result = runner.invoke(app, ["status"])

    assert "this branch is not open for you" in result.output
    assert "another conversation" not in result.output


@pytest.mark.parametrize("command", ["resume", "end"])
def test_an_unwired_caller_passes_every_gate_this_feature_touches(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    """FR-006 at the two call sites that gained a refusal.

    The new guard reads `"other"`, and a caller presenting nothing resolves to
    `"unknown"` however the branch was opened. Were that wrong, every repository
    that never set the variable would be refused at once — a blast radius larger
    than the defect being fixed.
    """
    monkeypatch.setenv("WFCTL_SESSION_ID", "someone-else")
    runner.invoke(app, ["start"])

    monkeypatch.delenv("WFCTL_SESSION_ID")
    result = runner.invoke(app, [command])

    assert result.exit_code == 0, result.output


# ─── `session_started` itself, across every state this feature adds ─────────

@pytest.mark.parametrize(
    "start_line, presented",
    [
        (None, None),
        ("no-identity", "caller"),
        ("holder", "holder"),
        ("holder", "caller"),
        ("holder", None),
    ],
    ids=[
        "A-never-started",
        "D-holder-absent-caller-identified",
        "B-self",
        "C-other",
        "D-caller-unwired",
    ],
)
def test_session_started_is_unchanged(
    agent_dir: Path,
    tmp_path: Path,
    start_line: str | None,
    presented: str | None,
) -> None:
    """SC-006: the field six speckit skills already read answers exactly as
    before, whatever the new `session_id` argument carries.

    `start_line` is the identity written on the branch's one `start` line —
    `None` when no line exists at all, `"no-identity"` for a line predating this
    feature. `session_started` reads only whether that line exists
    (`wfctl/_session.py`); it has no way to see an identity, on either side. This
    is the regression the released behaviour cannot survive silently — a change
    that made `build_report` derive `session_started` from the holder relation
    would pass every test above it and fail only this one.
    """
    if start_line == "no-identity":
        append_event(agent_dir, "start")
    elif start_line is not None:
        append_event(agent_dir, "start", session_id=start_line)

    report = _report(tmp_path, agent_dir, presented)

    assert report.session_started is (start_line is not None)


# ─── Two call sites the panel found, where the holder relation was recomputed
#     instead of reused ──────────────────────────────────────────────────────

def test_a_session_that_ended_can_start_again_with_the_same_identity(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: the takeover check used to compare raw identity, which does
    not know about an `end`. `start` → `end` → `start`, all as `"mine"`, has to
    leave the branch reading `"self"` to `"mine"` — not lock it out of the
    session it just closed and reopened.
    """
    monkeypatch.setenv("WFCTL_SESSION_ID", "mine")
    runner.invoke(app, ["start"])
    runner.invoke(app, ["end"])

    restarted = runner.invoke(app, ["start"])
    assert restarted.exit_code == 0, restarted.output

    resumed = runner.invoke(app, ["resume"])
    assert resumed.exit_code == 0, resumed.output


def test_an_unwired_start_at_a_sitting_boundary_keeps_the_wired_holder(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: the sitting-boundary append used to write the *current*
    caller's identity verbatim, including absent — which reset the holder to
    `None` and let the next caller of any identity take the branch over
    uncontested. An unwired `start` here must be a true no-op on identity.
    """
    monkeypatch.setenv("WFCTL_SESSION_ID", "mine")
    runner.invoke(app, ["start"])
    runner.invoke(app, ["resume"])

    monkeypatch.delenv("WFCTL_SESSION_ID")
    runner.invoke(app, ["start"])

    monkeypatch.setenv("WFCTL_SESSION_ID", "mine")
    still_mine = runner.invoke(app, ["status", "--json"])
    assert json.loads(still_mine.output)["session_holder"] == "self"
