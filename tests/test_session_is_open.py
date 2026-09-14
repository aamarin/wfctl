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
    """Both keys always present, never omitted — `notify`'s rule applied again.

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
