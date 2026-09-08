"""Declining authority you hold, and the row no grant reaches (#280).

Two absences that look identical in the tracker and are different facts about
the run: the agent judged it should not act, and nobody allowed it to. Only one
of them is a sign the grant should be widened, so a report that files them
together loses the only thing it was collected for (FR-011).

The irreversible row is here too, and it is asserted from the *granted* side
throughout. Against the default every claim below passes on code that refuses
everything, which is exactly the shape that let a guard gap survive 863 tests.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

from typer.testing import CliRunner

from wfctl import _tracker
from wfctl.cli import _IRREVERSIBLE_NOTICE, app

runner = CliRunner()


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


def _backend(root: Path, verbs: dict) -> None:
    (root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "fake"}))
    trackers = root / ".agents" / "trackers"
    trackers.mkdir(parents=True, exist_ok=True)
    (trackers / "fake.json").write_text(json.dumps({"verbs": verbs}))


def test_declining_and_being_refused_are_different_events(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-011, at the level the report is actually assembled from.

    Both leave the tracker unchanged. The log is where the difference survives,
    and it has to, because by the time anyone reads the report the only evidence
    left is what was written down.
    """
    agent_dir, root = storyctl_dir.agent_dir, storyctl_dir.repo_root
    _backend(root, {"comment": ["true"]})

    runner.invoke(app, ["start", "--allow-notify"])
    runner.invoke(app, [
        "notify", "issue-create", "--declined",
        "--reason", "the delivery plan has rows with no issue number",
    ])

    runner.invoke(app, ["start", "--deny-notify"])
    _tracker.dispatch(agent_dir, root, "comment", {"id": "418"})

    declined = _events(agent_dir, "notify-declined")
    refused = _events(agent_dir, "notify-refused")
    assert [d["action"] for d in declined] == ["issue-create"]
    assert [r["action"] for r in refused] == ["comment"]
    assert refused[0]["source"] == "deny"


def test_the_decline_line_leads_with_the_permission_it_had(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """What separates the agent choosing not to act from not being allowed to.

    Drop the "may notify people, but" clause and the two read the same, which is
    the failure the requirement is about rather than a matter of phrasing.
    """
    runner.invoke(app, ["start", "--allow-notify"])
    out = runner.invoke(app, [
        "notify", "issue-create", "--declined", "--reason", "rows with no key",
    ]).output
    assert out.startswith("may notify people, but skipped issue-create")
    assert "rows with no key" in out


def test_a_decline_without_a_reason_is_refused(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A decline with no reason is indistinguishable from a failure, and the
    reason is the only part a reader can act on."""
    runner.invoke(app, ["start", "--allow-notify"])
    result = runner.invoke(app, ["notify", "issue-create", "--declined"])
    assert result.exit_code == 1
    assert _events(storyctl_dir.agent_dir, "notify-declined") == []


def test_an_ungranted_run_cannot_record_an_action_it_was_not_allowed_to_take(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The log is the report, so a line claiming people were told is a false
    report — and this command is the one surface an actor could write one from."""
    result = runner.invoke(app, ["notify", "push"])
    assert result.exit_code == 1
    assert _events(storyctl_dir.agent_dir, "notify-action") == []


def test_a_granted_run_records_an_action_wfctl_did_not_perform(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The gap this command exists for. No wfctl verb pushes, and a push is in
    the notifying class all the same."""
    runner.invoke(app, ["start", "--allow-notify"])
    assert runner.invoke(app, ["notify", "push"]).exit_code == 0
    assert [a["action"] for a in _events(storyctl_dir.agent_dir, "notify-action")] == ["push"]


# --- the row no grant reaches --------------------------------------------------

def test_the_irreversible_notice_prints_even_when_the_run_is_granted(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Asserted from the granted side, which is the only side that can fail.

    On an ungranted branch this passes on a line printed unconditionally *and* on
    one keyed to refusal, because both render there. Granted is where a line
    wrongly tied to the verdict would vanish — and vanishing is the failure,
    since the reader who has just been told the run may notify people is exactly
    the one who will ask what else it may do.
    """
    runner.invoke(app, ["start", "--allow-notify"])
    out = runner.invoke(app, ["status"]).output
    assert "may notify people" in out
    assert _IRREVERSIBLE_NOTICE in out


def test_no_grant_value_changes_the_irreversible_notice(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-013. The line is not keyed on the grant, and the test is that it cannot
    be — every value of the setting renders the same sentence."""
    rendered = set()
    for args in (["start", "--allow-notify"], ["start", "--deny-notify"], ["start"]):
        runner.invoke(app, args)
        out = runner.invoke(app, ["status"]).output
        assert _IRREVERSIBLE_NOTICE in out
        rendered.add(_IRREVERSIBLE_NOTICE in out)
    assert rendered == {True}


def test_the_notice_says_no_setting_rather_than_a_missing_grant(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A reader hitting this line will otherwise go hunting for the flag that
    turns it on. Saying "nobody has allowed it" would send them looking for one
    that does not exist, which is a worse outcome than saying nothing."""
    assert "no setting for it" in _IRREVERSIBLE_NOTICE
    assert "allowed" not in _IRREVERSIBLE_NOTICE
    assert len(_IRREVERSIBLE_NOTICE) <= 72


def test_closing_an_issue_is_unaffected_by_a_grant_being_present(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path,
) -> None:
    """The irreversible row is kept safe by never being granted, not by being
    refused here — refusing it would block the human who is the only actor
    allowed to do it, and wfctl cannot tell a human from an agent.

    So the property is that the grant makes no difference: `close` behaves the
    same either way, and never lands in the report as something that notified
    anyone.
    """
    agent_dir, root = storyctl_dir.agent_dir, storyctl_dir.repo_root
    marker = tmp_path / "ran.log"
    _backend(root, {"close": ["sh", "-c", f"echo ran >> {marker}"]})

    runner.invoke(app, ["start", "--deny-notify"])
    assert _tracker.dispatch(agent_dir, root, "close", {"id": "418"}) == 0

    runner.invoke(app, ["start", "--allow-notify"])
    assert _tracker.dispatch(agent_dir, root, "close", {"id": "418"}) == 0

    assert len(marker.read_text().splitlines()) == 2
    assert _events(agent_dir, "notify-action") == []
