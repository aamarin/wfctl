"""The review cap: auto-approve turned off after 3 plan reviews or sign-offs
while the pass is still outstanding (FR-022, research R9).

The count is derived from `events.jsonl` on every read, never held anywhere
else, so each test here drives the real `start`, `resume`, and `step sign-off`
commands and reads the mode file and the log they leave. A review is a lap of
the loop an unattended run makes: edit `plan.md`, write a report of it, and
run `resume`, which records the report's hash.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import CLEAN_PLAN, CLEAN_SPEC, write_plan_review
from wfctl import _plan_review, _session
from wfctl.cli import app

runner = CliRunner()

_REVOKED_LINE = (
    "auto-approve off — wfctl turned it off after 3 plan reviews or sign-offs "
    "since it was granted"
)


@pytest.fixture
def planned(storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch):
    """A planned feature with a session open, and an arch root in the tree so
    a sign-off can write its scan section."""
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(storyctl_dir.repo_root / "docs" / "architecture"))
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    storyctl_dir.make_spec_artifact("plan", content=CLEAN_PLAN)
    assert runner.invoke(app, ["start"]).exit_code == 0
    storyctl_dir.laps = 0
    return storyctl_dir


def _edit(sd: types.SimpleNamespace) -> None:
    sd.laps += 1
    plan = sd.spec_dir / "plan.md"
    plan.write_text(plan.read_text() + f"\nRevision {sd.laps}.\n")


def _lap(sd: types.SimpleNamespace, blockers: int = 1) -> str:
    """One review: an edit, a report of the edited plan, then `resume`.
    Returns `resume`'s output."""
    _edit(sd)
    write_plan_review(sd.spec_dir, blockers)
    result = runner.invoke(app, ["resume"])
    assert result.exit_code == 0, result.output
    return result.output


def _mode(sd: types.SimpleNamespace) -> dict:
    return json.loads((sd.agent_dir / _session.MODE_NAME).read_text())


def _events(agent_dir: Path) -> list[dict]:
    return [json.loads(line) for line in (agent_dir / "events.jsonl").read_text().splitlines()]


def _count(sd: types.SimpleNamespace) -> int:
    return _plan_review.review_count(sd.agent_dir, "418-storyctl")


def _grant() -> None:
    assert runner.invoke(app, ["start", "--auto-approve"]).exit_code == 0


def test_with_no_grant_nothing_is_counted(planned: types.SimpleNamespace) -> None:
    """Data model step 1: with no grant there is nothing to revoke, and an
    attended run that reviewed three times is a person doing their job."""
    for _ in range(3):
        _lap(planned)

    assert _count(planned) == 0
    assert not (planned.agent_dir / _session.MODE_NAME).exists()
    assert not [e for e in _events(planned.agent_dir) if e["event"] == "mode"]


def test_three_reviews_with_the_pass_outstanding_revoke(planned: types.SimpleNamespace) -> None:
    """SC-007. Three reviews that each left a BLOCKER open are the loop FR-022
    bounds, and the third turns the mode off and records why."""
    _grant()
    _lap(planned)
    _lap(planned)
    assert _mode(planned) == {"auto_approve": True}

    _lap(planned)

    assert _mode(planned) == {
        "auto_approve": False,
        "revoked": "wfctl turned it off after 3 plan reviews or sign-offs since it was granted",
    }
    revocation = [e for e in _events(planned.agent_dir) if e["event"] == "mode"][-1]
    assert revocation["auto_approve"] is False
    assert revocation["by"] == "wfctl"
    assert "3 plan reviews or sign-offs" in revocation["reason"]


def test_a_resume_records_the_report_it_saw(planned: types.SimpleNamespace) -> None:
    """The count reads the `review` field, and a report's hash is wfctl's own
    observation that a review ran, never the agent's claim that one did."""
    _lap(planned)

    resume = [e for e in _events(planned.agent_dir) if e["event"] == "resume"][-1]
    assert resume["review"] == _plan_review.identity(planned.spec_dir / _plan_review.REPORT_NAME)


def test_the_same_report_seen_twice_counts_once(planned: types.SimpleNamespace) -> None:
    """A `resume` typed by hand between reviews sees the same report, and
    counting it again would stop a run that reviewed once."""
    _grant()
    _lap(planned)
    for _ in range(3):
        assert runner.invoke(app, ["resume"]).exit_code == 0

    assert _count(planned) == 1
    assert _mode(planned)["auto_approve"] is True


def test_two_reviews_and_a_sign_off_revoke(planned: types.SimpleNamespace) -> None:
    """A sign-off counts as a review. Without that, an agent under the grant
    could sign off each edit and loop past the cap with none of it reviewed.

    The sign-off itself reads the pass done, so the revocation lands on the
    next `resume` after an edit, the first moment the pass is outstanding."""
    _grant()
    _lap(planned)
    _lap(planned)
    assert runner.invoke(app, ["step", "sign-off", "plan.plan-review", "--reason", "typo"]).exit_code == 0
    assert _count(planned) == 3
    assert _mode(planned)["auto_approve"] is True

    _edit(planned)
    runner.invoke(app, ["resume"])

    assert _mode(planned)["auto_approve"] is False


def test_a_clean_third_review_does_not_revoke_and_the_next_stale_one_does(
    planned: types.SimpleNamespace,
) -> None:
    """FR-022's narrowing. A clean third review leaves nothing for a person to
    decide, so the run goes on to `tasks`. The count does not reset, so the
    next edit that leaves the plan unreviewed stops at once."""
    _grant()
    _lap(planned)
    _lap(planned)
    _lap(planned, blockers=0)
    assert _mode(planned) == {"auto_approve": True}

    _edit(planned)
    runner.invoke(app, ["resume"])

    assert _mode(planned)["auto_approve"] is False


def test_a_new_grant_resets_the_count(planned: types.SimpleNamespace) -> None:
    """The count starts after the last grant, so a person granting again is
    the one thing that gives the run three more laps."""
    _grant()
    for _ in range(3):
        _lap(planned)
    assert _mode(planned)["auto_approve"] is False

    _grant()

    assert _mode(planned) == {"auto_approve": True}
    assert _count(planned) == 0
    _lap(planned)
    _lap(planned)
    assert _mode(planned)["auto_approve"] is True


def test_a_restart_changes_neither_the_count_nor_the_mode(planned: types.SimpleNamespace) -> None:
    """FR-022 and SC-007. `/start-session` runs `wfctl start` with no flag
    after every `/clear`, and a `start` that reset the count would give an
    unattended run three fresh laps each time its context filled."""
    _grant()
    _lap(planned)
    _lap(planned)

    assert runner.invoke(app, ["start"]).exit_code == 0
    with (planned.agent_dir / "events.jsonl").open("a") as log:
        log.write(json.dumps({"ts": "2026-09-28T00:00:00Z", "event": "start",
                              "branch": "418-storyctl"}) + "\n")

    assert _count(planned) == 2
    assert _mode(planned) == {"auto_approve": True}
    _lap(planned)
    assert _mode(planned)["auto_approve"] is False


def test_the_revoking_resume_writes_auto_false(planned: types.SimpleNamespace) -> None:
    """The revocation lands before `next-step.md` is written. An agent reads
    that file, and one that read `auto: true` on the lap that revoked would run
    the fourth review anyway."""
    _grant()
    _lap(planned)
    _lap(planned)
    assert "auto: true" in (planned.agent_dir / "next-step.md").read_text()

    output = _lap(planned)

    assert "auto: false" in (planned.agent_dir / "next-step.md").read_text()
    assert "(auto: false)" in output


def test_status_and_resume_print_the_revocation_in_place_of_the_notice(
    planned: types.SimpleNamespace,
) -> None:
    """A mode that turned itself off has to say so and why, or the person who
    granted it reads an attended status and has no idea the run stopped on its
    own."""
    _grant()
    _lap(planned)
    _lap(planned)

    resumed = _lap(planned)
    status = runner.invoke(app, ["status"]).output

    for output in (resumed, status):
        assert _REVOKED_LINE in output
        assert "review stops run through" not in output


def test_a_mode_a_person_turned_off_prints_no_revocation(planned: types.SimpleNamespace) -> None:
    """Only wfctl writes `revoked`, and `--no-auto-approve` is a person's
    choice with no reason owed to anyone."""
    _grant()
    assert runner.invoke(app, ["start", "--no-auto-approve"]).exit_code == 0

    assert _mode(planned) == {"auto_approve": False}
    assert "wfctl turned it off" not in runner.invoke(app, ["status"]).output


def test_the_count_skips_a_damaged_line(planned: types.SimpleNamespace) -> None:
    """Every command appends to this log, and a truncated write must not stop
    the count or crash the `resume` that reads it."""
    _grant()
    _lap(planned)
    with (planned.agent_dir / "events.jsonl").open("a") as log:
        log.write('{"event": "resume", "review": \n[]\nnull\n')
    _lap(planned)

    assert _count(planned) == 2
