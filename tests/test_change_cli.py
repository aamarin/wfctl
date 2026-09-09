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


def _answers(monkeypatch: pytest.MonkeyPatch, change: object, issue: object) -> list:
    """Answer the change read and the issue read, told apart by their argv.

    Either may be an exception to raise or an exit code to fail with, so a test
    can fail exactly one of the two reads — which is the case the exit code
    turns on and the one a single stub could not express.

    Returns the argv list every call was made with, so a test can assert *which*
    id went to which section rather than only what came back.
    """
    seen: list = []
    queue = [change, issue]

    def fake_run(argv, **kwargs):
        # Keyed on the argv, not on call order. Answering positionally left
        # "which id reaches which section" unpinned: swapping the two reads made
        # the command compare the change against itself and every test here
        # still passed.
        nxt = queue[0] if "pr" in argv else queue[1]
        seen.append(argv)
        if isinstance(nxt, BaseException):
            raise nxt
        if isinstance(nxt, int):
            return subprocess.CompletedProcess(argv, nxt, stdout="", stderr="unreachable")
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(nxt), stderr="")

    monkeypatch.setattr(_tracker.subprocess, "run", fake_run)
    return seen


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


def test_a_backend_that_declines_fields_is_skipped_and_says_how_to_fix_it(
    agent_dir: Path,
) -> None:
    """Exit 0, because a session must not fail on a tracker step that could not
    run — but the reason is the one a reader cannot otherwise discover.

    A bare `install-skills` never refreshes a tracker file already present,
    `doctor` does not look inside `.agents/trackers/`, and `tracker-check`
    prints the `verbs` section only. So a repo whose config predates this verb
    gets a silent skip from every command that would normally tell it, and this
    line is the only place the remedy appears.
    """
    _configure(agent_dir.parent, {"verbs": {"list": ["gh"]}, "changes": {"list": ["gh"]}})
    result = runner.invoke(app, ["change", "check", "301"])
    assert result.exit_code == 0
    assert "skipping" in result.output
    assert "--tracker" in result.output


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
    """"Before any read" is the half worth pinning.

    A declaration nobody can parse decides the run on its own, so spending a
    network call first would be work whose answer is already known — and would
    put a tracker's failure in front of a reader whose actual problem is a file
    in their own repo.
    """
    _configure(agent_dir.parent)
    seen = _answers(monkeypatch, change={}, issue={})
    (agent_dir.parent / "wfctl.json").write_text(json.dumps({"change_check": "assignees"}))
    result = runner.invoke(app, ["change", "check", "301"])
    assert result.exit_code == 1
    assert "change_check" in result.output
    assert seen == []


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


def test_a_branch_with_no_issue_key_still_checks_what_the_repo_requires(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The branch that had no test, and would have failed every worktree made
    outside the naming rule.

    `conftest` pins a branch that always carries a key, so the guard was never
    taken and deleting it left the suite green. What it protects is a real
    worktree: `wfctl change check` is run from trees named for no issue too, and
    the repository's own requirements are knowable without one.
    """
    monkeypatch.setenv("WFCTL_BRANCH", "docs-typo")
    _configure(agent_dir.parent)
    _require(agent_dir.parent, "assignees")
    seen = _answers(monkeypatch, change={"assignees": []}, issue={"labels": ["P1"]})
    result = runner.invoke(app, ["change", "check", "305"])
    assert result.exit_code == 1
    assert "assignees" in result.output
    # One read, not two. There is no issue to ask about, and asking anyway would
    # send a branch name at a tracker as though it were a key.
    assert len(seen) == 1


def test_a_declined_issue_read_is_not_reported_as_an_issue_with_nothing_set(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The one place the command had collapsed a distinction it defends everywhere else.

    `_read_verb` keeps "the backend declined" apart from "the answer was empty"
    on purpose. The `ℹ` line used to say "the issue has none set" when the issue
    existed and its backend simply reports no fields — pointing the reader away
    from the only thing that would fix it.
    """
    _configure(
        agent_dir.parent,
        {"verbs": {"list": ["gh"]},
         "changes": {"list": ["gh"], "fields": ["gh", "pr", "view", "{id}"]}},
    )
    _answers(monkeypatch, change={"labels": []}, issue={})
    result = runner.invoke(app, ["change", "check", "301"])
    assert result.exit_code == 0
    assert "no fields for issues" in result.output
    assert "none set" not in result.output


def test_backend_stderr_carrying_markup_is_shown_rather_than_eaten(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A hand-authored backend prefixing its errors `[error]` had that prefix
    deleted by rich, and one emitting a closing tag took the command down.

    The failure path is the one with nothing else to say, so destroying its only
    diagnostic costs everything. `_tracker.dispatch` answers this with
    `markup=False`; these lines carry a marker of their own and escape instead.
    """
    _configure(agent_dir.parent)

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="[error] no [/x]")

    monkeypatch.setattr(_tracker.subprocess, "run", fake_run)
    result = runner.invoke(app, ["change", "check", "301"])
    assert result.exit_code == 1
    assert "[error]" in result.output
    assert result.exception is None or isinstance(result.exception, SystemExit)


def test_a_key_as_long_as_the_column_still_has_a_gap_after_it(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`reviewRequests` is exactly the width the column used to be fixed at, and
    ships in the default payload — so the shipped config rendered
    `reviewRequestsempty; …` with no separator at all."""
    _configure(agent_dir.parent)
    _require(agent_dir.parent, "reviewRequests")
    _answers(monkeypatch, change={"reviewRequests": []}, issue={})
    result = runner.invoke(app, ["change", "check", "301"])
    assert "reviewRequests " in result.output


def test_a_verdict_over_an_unread_issue_says_what_it_did_not_cover(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The state the panel's fix did not reach, found by the review on the PR.

    A backend declaring `changes.fields` and not `verbs.fields`, against a change
    that satisfies everything `wfctl.json` asked for, produced a screen of green
    ticks and exit 0 — with the issue's labels, milestone and everything else
    never read. Indistinguishable from a complete pass, which is the one thing
    this command must never be.

    Exit stays 0: a declined verb is a repo that opted out, not a failure, and
    the degrade contract says a session must not break on one. What changes is
    that the run says which half it covered.
    """
    _configure(
        agent_dir.parent,
        {"verbs": {"list": ["gh"]},
         "changes": {"list": ["gh"], "fields": ["gh", "pr", "view", "{id}"]}},
    )
    _require(agent_dir.parent, "assignees")
    _answers(monkeypatch, change={"assignees": ["aamarin"]}, issue={})
    result = runner.invoke(app, ["change", "check", "311"])
    assert result.exit_code == 0
    assert "✓" in result.output
    assert "was not read" in result.output
    assert "wfctl.json only" in result.output


def test_a_branch_with_no_issue_key_claims_no_missing_coverage(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The neighbouring state, which must *not* carry that caveat.

    No issue key means no issue, so nothing went unread and the verdict is
    complete for what exists. Printing "was not read" here would teach a reader
    to skim past it in the case above, where it is the whole point.
    """
    monkeypatch.setenv("WFCTL_BRANCH", "docs-typo")
    _configure(agent_dir.parent)
    _require(agent_dir.parent, "assignees")
    _answers(monkeypatch, change={"assignees": ["aamarin"]}, issue={})
    result = runner.invoke(app, ["change", "check", "305"])
    assert result.exit_code == 0
    assert "was not read" not in result.output
