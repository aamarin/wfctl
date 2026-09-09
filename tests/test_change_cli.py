"""`wfctl change check` — what it prints, and what it exits.

`test_change_check.py` covers what a blank field *means*; this covers the states
that need a repository, a config or a failed call. Chiefly the ones nobody would
write by hand: a backend that declined, a read that did not return, a config
nobody can parse. Every one of them has to end in an exit code and a sentence,
because a check that raises has told the reader about the wrong file.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

import wfctl._tracker as _tracker
from wfctl.cli import app

runner = CliRunner()

_CONFIG = {
    "verbs": {
        "list": ["gh", "issue", "list"],
        "fields": ["gh", "issue", "view", "{id}", "--json", "labels"],
    },
    "changes": {
        "list": ["gh", "pr", "list"],
        "view": ["gh", "pr", "view", "{id}"],
        "fields": ["gh", "pr", "view", "{id}", "--json", "labels"],
    },
}


def _configure(repo_root: Path, config: object = _CONFIG) -> None:
    tdir = repo_root / ".agents" / "trackers"
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / "github.json").write_text(json.dumps(config))
    (repo_root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "github"}))


def _answers(monkeypatch: pytest.MonkeyPatch, change: object, issue: object) -> None:
    """Answer the change read then the issue read, in that order.

    Either may be an exception to raise or an exit code to fail with, so a test
    can fail exactly one of the two reads — which is the case the exit code
    turns on and the one a single stub could not express.
    """
    queue = [change, issue]

    def fake_run(argv, **kwargs):
        nxt = queue.pop(0) if queue else {}
        if isinstance(nxt, BaseException):
            raise nxt
        if isinstance(nxt, int):
            return subprocess.CompletedProcess(argv, nxt, stdout="", stderr="unreachable")
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(nxt), stderr="")

    monkeypatch.setattr(_tracker.subprocess, "run", fake_run)


def _require(repo_root: Path, *keys: str) -> None:
    (repo_root / "wfctl.json").write_text(json.dumps({"change_check": list(keys)}))


def test_a_change_missing_what_its_issue_carries_is_reported_and_exits_one(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(agent_dir.parent)
    _answers(monkeypatch, change={"labels": []}, issue={"labels": ["authority:notify"]})
    result = runner.invoke(app, ["change", "check", "301"])
    assert result.exit_code == 1
    assert "labels" in result.output and "authority:notify" in result.output


def test_a_change_carrying_everything_expected_exits_zero_and_says_what_it_read(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The half an exercise skips, and the half a noisy check fails.

    Naming each key it verified is what separates a run that passed from one
    that checked nothing — the same distinction the `ℹ` state below carries.
    """
    _configure(agent_dir.parent)
    _answers(monkeypatch, change={"labels": ["P1"]}, issue={"labels": ["P1"]})
    result = runner.invoke(app, ["change", "check", "301"])
    assert result.exit_code == 0
    assert "✓" in result.output and "labels" in result.output


def test_nothing_required_and_nothing_to_inherit_says_so_rather_than_passing(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`ℹ`, never `✓`. A check that did nothing must not look like one that passed."""
    _configure(agent_dir.parent)
    _answers(monkeypatch, change={"milestone": None}, issue={"milestone": None})
    result = runner.invoke(app, ["change", "check", "305"])
    assert result.exit_code == 0
    assert "nothing to check" in result.output
    assert "✓" not in result.output


def test_a_backend_that_declines_fields_is_skipped_not_failed(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(agent_dir.parent, {"verbs": {"list": ["gh"]}, "changes": {"list": ["gh"]}})
    result = runner.invoke(app, ["change", "check", "301"])
    assert result.exit_code == 0
    assert "skipping" in result.output


def test_no_tracker_at_all_is_skipped_not_failed(agent_dir: Path) -> None:
    result = runner.invoke(app, ["change", "check", "301"])
    assert result.exit_code == 0


def test_a_change_read_that_did_not_return_exits_non_zero(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(agent_dir.parent)
    _answers(monkeypatch, change=1, issue={})
    result = runner.invoke(app, ["change", "check", "301"])
    assert result.exit_code == 1
    assert "unreachable" in result.output


def test_a_timed_out_read_exits_non_zero_without_a_traceback(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(agent_dir.parent)
    _answers(monkeypatch, change=subprocess.TimeoutExpired(["gh"], 15), issue={})
    result = runner.invoke(app, ["change", "check", "301"])
    assert result.exit_code == 1
    assert result.exception is None or isinstance(result.exception, SystemExit)


def test_an_issue_read_that_failed_still_reports_what_was_checkable(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-016. A read that failed is not a source that had nothing to say.

    The required key is knowable without the issue, so it is still judged — and
    the run still refuses, because a run that saw half of what it needed must
    never exit like a clean one.
    """
    _configure(agent_dir.parent)
    _require(agent_dir.parent, "assignees")
    _answers(monkeypatch, change={"assignees": []}, issue=1)
    result = runner.invoke(app, ["change", "check", "301"])
    assert result.exit_code == 1
    assert "assignees" in result.output
    assert "could not read" in result.output


def test_a_payload_the_verb_never_flattened_names_the_config_not_a_traceback(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(agent_dir.parent)
    _answers(monkeypatch, change={"labels": [{"name": "P1"}]}, issue={})
    result = runner.invoke(app, ["change", "check", "301"])
    assert result.exit_code == 1
    assert "labels" in result.output
    assert result.exception is None or isinstance(result.exception, SystemExit)


def test_a_malformed_change_check_declaration_is_reported_before_any_read(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(agent_dir.parent)
    (agent_dir.parent / "wfctl.json").write_text(json.dumps({"change_check": "assignees"}))
    result = runner.invoke(app, ["change", "check", "301"])
    assert result.exit_code == 1
    assert "change_check" in result.output


def test_check_without_a_change_id_refuses(agent_dir: Path) -> None:
    result = runner.invoke(app, ["change", "check"])
    assert result.exit_code == 1


def test_list_and_view_still_dispatch_to_the_backend(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The verb wfctl owns must not have swallowed the ones it does not.

    `change` was a pure passthrough before `check` existed, and the branch that
    makes `check` wfctl's is the kind that quietly captures its neighbours.
    """
    calls: list = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(_tracker.subprocess, "run", fake_run)
    _configure(agent_dir.parent)
    runner.invoke(app, ["change", "view", "128"])
    assert calls == [["gh", "pr", "view", "128"]]
