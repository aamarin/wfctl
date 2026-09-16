"""`wfctl report-block` and `wfctl report-action` — the two facts an agent tells
wfctl that wfctl could not observe (#364, renamed by #384).

The command surface alone. Whether a block holds a step is
`test_report_block_holds_step.py`; how the three event kinds share one timeline
is `test_report_events.py`.
"""
from __future__ import annotations

import inspect
import json
import types

from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def _payload() -> dict:
    return json.loads(runner.invoke(app, ["status", "--json"]).output)


def _events(storyctl_dir: types.SimpleNamespace) -> list[dict]:
    log = storyctl_dir.agent_dir / "events.jsonl"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().splitlines() if line.strip()]


def _params(name: str) -> set[str]:
    command = next(c for c in app.registered_commands if c.name == name)
    assert command.callback is not None
    return set(inspect.signature(command.callback).parameters)


def test_a_block_is_recorded_on_a_branch_nobody_granted_anything(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The ordinary case now, rather than the exception #364 carved out: there
    is no grant for a branch to lack."""
    result = runner.invoke(
        app, ["report-block", "issue-comment", "--reason", "host classifier: External System Writes"]
    )
    assert result.exit_code == 0, result.output
    blocked = [e for e in _events(storyctl_dir) if e.get("event") == "blocked"]
    assert len(blocked) == 1
    assert blocked[0]["action"] == "issue-comment"
    assert blocked[0]["reason"] == "host classifier: External System Writes"


def test_no_spelling_of_report_block_records_a_success(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A property of the surface rather than prose an agent has to have read.
    `--clear` went with #384, and a success-shaped mode added back later fails
    this instead of shipping quietly — the release has its own verb."""
    assert _params("report-block") == {"action", "reason"}


def test_the_step_comes_from_inference_not_from_the_caller(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The agent supplies only the facts it alone witnessed and never names
    which step is held; neither command has a parameter for it."""
    assert "step" not in _params("report-block")
    assert _params("report-action") == {"action"}


def test_a_block_with_no_reason_is_refused_and_stores_nothing(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A block with no reason would hold a step and say nothing about why."""
    result = runner.invoke(app, ["report-block", "issue-comment"])
    assert result.exit_code == 1
    assert not any(e.get("event") == "blocked" for e in _events(storyctl_dir))


def test_a_branch_with_no_feature_still_stores_the_report(
    storyctl_dir: types.SimpleNamespace, monkeypatch,
) -> None:
    """The report is about the run, not the pipeline, so it is stored on a
    branch no feature claims — and the response says plainly nothing is held."""
    import subprocess

    trunk = subprocess.run(
        ["git", "-C", str(storyctl_dir.repo_root), "branch", "--show-current"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    monkeypatch.setenv("WFCTL_BRANCH", trunk)

    result = runner.invoke(app, ["report-block", "push", "--reason", "refused on trunk"])
    assert result.exit_code == 0, result.output
    assert "no step is being held" in result.output
    blocked = [e for e in _events(storyctl_dir) if e.get("event") == "blocked"]
    assert len(blocked) == 1
    assert blocked[0]["step"] is None


def test_a_block_filed_once_the_pipeline_reads_complete_still_holds_the_last_step(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`build_report.current` is `None` both for "no feature claims this branch"
    and "nothing is left to run". `end-session` files `report-block issue-close`
    after implementation and verification finish, which is the second state, and
    it has to hold the last step or the next session reads the work as done."""
    storyctl_dir.stage_upstream_of("tasks")
    assert _payload()["current"] is None

    result = runner.invoke(app, ["report-block", "issue-close", "--reason", "host refused"])
    assert result.exit_code == 0, result.output
    assert "holding `implement`" in result.output

    held = next(s for s in _payload()["steps"] if s["name"] == "implement")
    assert held["state"] == "in_progress"
    assert held["reason"] == "host refused"


def test_recording_an_action_with_no_hold_standing_says_only_that(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A push with nothing held is the ordinary case, so it is not refused — and
    it does not claim a release that did not happen."""
    result = runner.invoke(app, ["report-action", "push"])
    assert result.exit_code == 0, result.output
    assert "recorded: push" in result.output
    assert "lifted" not in result.output
    actions = [e for e in _events(storyctl_dir) if e.get("event") == "notify-action"]
    assert [e["action"] for e in actions] == ["push"]


def test_recording_the_action_names_the_hold_it_lifted(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The check `blocked --clear` made, kept on the verb that replaced it. A
    mistyped name would otherwise exit 0 over a hold still standing, and the
    screen would read the same as a release."""
    storyctl_dir.stage_upstream_of("tasks")
    runner.invoke(app, ["report-block", "push", "--reason", "host refused"])

    typo = runner.invoke(app, ["report-action", "pushh"])
    assert "lifted" not in typo.output
    assert any(s["reason"] == "host refused" for s in _payload()["steps"])

    result = runner.invoke(app, ["report-action", "push"])
    assert result.exit_code == 0, result.output
    assert "lifted the hold on implement" in result.output
    assert not any(s["reason"] == "host refused" for s in _payload()["steps"])


def test_the_removed_verbs_are_gone_rather_than_aliased(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """No aliases, by `384-the-agent-reports-through-two-flat-verbs`: a `notify`
    alias would have silently changed from gated to ungated. A skill installed
    from an older wheel fails loudly instead, and `doctor` names the drift."""
    names = {c.name for c in app.registered_commands}
    assert {"report-action", "report-block"} <= names
    assert not names & {"notify", "blocked"}
    help_text = runner.invoke(app, ["--help"]).output
    assert "report-action" in help_text and "report-block" in help_text
    for gone in (["notify", "push"], ["blocked", "push", "--reason", "x"]):
        assert runner.invoke(app, gone).exit_code != 0, gone


def test_start_no_longer_takes_a_notify_flag(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Typed out of habit, the old flag fails as any unknown option does rather
    than being accepted and ignored — silence there would read as a grant."""
    for flag in ("--allow-notify", "--deny-notify"):
        assert runner.invoke(app, ["start", flag]).exit_code != 0, flag


def test_start_makes_no_tracker_call(
    storyctl_dir: types.SimpleNamespace, monkeypatch,
) -> None:
    """`wfctl start` read the issue's labels on every session to resolve the
    grant — one network round-trip per `/start-session`, and a crash path when
    the tracker config was malformed. With the grant gone nothing on `start`
    asks the tracker anything, so a tracker that fails loudly is never reached.
    """
    from wfctl import _tracker

    def refuse(*args, **kwargs):
        raise AssertionError("wfctl start reached the tracker")

    monkeypatch.setattr(_tracker, "_read_verb", refuse)
    monkeypatch.setattr(_tracker, "dispatch", refuse)
    root = storyctl_dir.repo_root
    (root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "fake"}))
    trackers = root / ".agents" / "trackers"
    trackers.mkdir(parents=True, exist_ok=True)
    (trackers / "fake.json").write_text(json.dumps({"verbs": {"labels": ["false"]}}))

    result = runner.invoke(app, ["start"])
    assert result.exit_code == 0, result.output
    assert "notify" not in result.output


def test_status_says_who_decides_and_what_is_never_taken(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The notify line is gone, and the two lines beside it stay in every state.

    The host line used to say the agent had permission rules "of its own", which
    only made sense next to wfctl's grant; left as it was, it would describe a
    second set of rules that no longer exists.
    """
    from wfctl.cli import _HOST_AUTHORITY_NOTICE, _IRREVERSIBLE_NOTICE

    out = runner.invoke(app, ["status"]).output
    assert "notify" not in out
    assert _IRREVERSIBLE_NOTICE in out
    assert _HOST_AUTHORITY_NOTICE in out
    assert "of its own" not in _HOST_AUTHORITY_NOTICE
    assert "report-block" not in _HOST_AUTHORITY_NOTICE
    for constant in (_IRREVERSIBLE_NOTICE, _HOST_AUTHORITY_NOTICE):
        for physical_line in constant.split("\n"):
            assert len(physical_line) <= 72, physical_line


def test_the_status_payload_carries_no_grant_keys(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`contracts/status-payload.md` for #384: `notify` and `notify_source` leave
    the JSON in the same change as the console line, never after it
    (`pipeline-state-is-one-payload`). A consumer still reading `notify` gets a
    missing key rather than a `false` that looks like a refusal nobody made."""
    payload = _payload()
    assert "notify" not in payload
    assert "notify_source" not in payload
    assert len(payload["facts"]) == 3
