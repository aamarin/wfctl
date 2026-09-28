"""A pass that needs a person, read under each approval mode
(`autonomous-agent-skips-human-checks`, data-model.md § Pass reading).

Every assertion reads a report built by `build_report`, the one inference every
view renders, so the skip is proven where `status`, `resume` and orchestrate all
get it from. The pass is declared on `decompose` for the reason
`test_status_attention.py` gives: `brainstorm`'s own passes would sit first in
the cascade on a fresh repository and the declared one would never be reached.
"""
from __future__ import annotations

import json
import types

from typer.testing import CliRunner

from wfctl._pipeline import build_report
from wfctl._session import grant_auto_approve
from wfctl.cli import app

runner = CliRunner()

SKIP_REASON = "needs a person; auto-approve is on"


def _declare(storyctl_dir: types.SimpleNamespace, passes: list[dict]) -> None:
    (storyctl_dir.repo_root / "wfctl.json").write_text(
        json.dumps({"steps": {"decompose": passes}})
    )


def _walkthrough(**extra: object) -> dict:
    return {"name": "walk", "command": "/walk", "evidence": "walked.md",
            "needs_person": True, **extra}


def _pass(storyctl_dir: types.SimpleNamespace, name: str = "walk") -> dict:
    report = build_report(storyctl_dir.spec_dir, storyctl_dir.repo_root, storyctl_dir.agent_dir)
    decompose = next(s for s in report.steps if s["name"] == "decompose")
    return next(p for p in decompose["sub_steps"] if p["name"] == name)


def test_an_autonomous_run_skips_a_pass_that_needs_a_person_and_says_why(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The whole point: nobody is there to answer, so the pass is passed by,
    and the reason travels with it rather than leaving a bare `skipped`."""
    storyctl_dir.stage_upstream_of("tasks")
    _declare(storyctl_dir, [_walkthrough()])
    grant_auto_approve(storyctl_dir.agent_dir, True)

    walk = _pass(storyctl_dir)
    assert walk["state"] == "skipped"
    assert walk["annotation"] == SKIP_REASON
    assert walk["claimed"] is None
    assert walk["needs_person"] is True


def test_the_skip_writes_nothing(storyctl_dir: types.SimpleNamespace) -> None:
    """A skip computed at read time has nothing to clean up later. A file
    written here would outlive the mode it describes, which is the cost the
    rejected claim-based design carried."""
    storyctl_dir.stage_upstream_of("tasks")
    _declare(storyctl_dir, [_walkthrough()])
    grant_auto_approve(storyctl_dir.agent_dir, True)
    before = sorted(p for p in storyctl_dir.repo_root.rglob("*") if ".git" not in p.parts)

    _pass(storyctl_dir)

    after = sorted(p for p in storyctl_dir.repo_root.rglob("*") if ".git" not in p.parts)
    assert after == before


def test_a_skipped_pass_does_not_hold_back_the_pass_after_it(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A pass that is not `done` normally leaves every later pass `pending`
    unread. A skip is the run moving on, like a claim, so the next pass is
    read on its own evidence."""
    storyctl_dir.stage_upstream_of("tasks")
    _declare(storyctl_dir, [
        _walkthrough(),
        {"name": "after", "manual": True, "evidence": "after.md"},
    ])
    grant_auto_approve(storyctl_dir.agent_dir, True)

    assert _pass(storyctl_dir, "after")["state"] == "in_progress"


def test_an_autonomous_run_moves_past_the_skipped_pass(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """If the next command still named the pass, orchestrate would start the
    walkthrough on every loop and the run would end stalled rather than
    skipped."""
    storyctl_dir.stage_upstream_of("tasks")
    _declare(storyctl_dir, [_walkthrough()])
    grant_auto_approve(storyctl_dir.agent_dir, True)

    report = build_report(storyctl_dir.spec_dir, storyctl_dir.repo_root, storyctl_dir.agent_dir)
    assert report.next_command != "/walk"
    assert report.attention is None


def test_with_auto_approve_off_the_pass_waits_for_a_person(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Coming back is turning the mode off, and nothing else. The pass is
    outstanding again with no file created or deleted."""
    storyctl_dir.stage_upstream_of("tasks")
    _declare(storyctl_dir, [_walkthrough()])
    grant_auto_approve(storyctl_dir.agent_dir, True)
    assert _pass(storyctl_dir)["state"] == "skipped"

    grant_auto_approve(storyctl_dir.agent_dir, False)

    walk = _pass(storyctl_dir)
    assert walk["state"] == "in_progress"
    assert walk["annotation"] is None


def test_evidence_counts_whichever_mode_is_on(storyctl_dir: types.SimpleNamespace) -> None:
    """A walkthrough someone finished stays finished after auto-approve comes
    back on: evidence is checked before the skip, so it cannot be hidden by
    one."""
    storyctl_dir.stage_upstream_of("tasks")
    _declare(storyctl_dir, [_walkthrough()])
    (storyctl_dir.spec_dir / "walked.md").write_text("Mode: plan\n")

    for granted in (False, True):
        grant_auto_approve(storyctl_dir.agent_dir, granted)
        assert _pass(storyctl_dir)["state"] == "done"


def test_a_claim_wins_whichever_mode_is_on(storyctl_dir: types.SimpleNamespace) -> None:
    """A person's own statement that the pass does not apply is checked first,
    as it is for every pass, so the skip never replaces its reason."""
    storyctl_dir.stage_upstream_of("tasks")
    _declare(storyctl_dir, [_walkthrough()])
    claimed = runner.invoke(
        app, ["step", "none", "decompose.walk", "--reason", "docs-only change"]
    )
    assert claimed.exit_code == 0, claimed.output

    for granted in (False, True):
        grant_auto_approve(storyctl_dir.agent_dir, granted)
        walk = _pass(storyctl_dir)
        assert walk["state"] == "skipped"
        assert walk["claimed"] == "docs-only change"


def test_a_pass_without_the_flag_is_not_skipped_on_an_autonomous_run(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Auto-approve alone skips nothing. Only the repository's declaration
    decides that a pass needs a person."""
    storyctl_dir.stage_upstream_of("tasks")
    _declare(storyctl_dir, [_walkthrough(needs_person=False)])
    grant_auto_approve(storyctl_dir.agent_dir, True)

    assert _pass(storyctl_dir)["state"] == "in_progress"


def test_the_payload_says_which_passes_need_a_person(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A consumer tells this skip from a claimed one and an inherited one by
    fields, not by parsing the annotation, so every pass carries the key."""
    storyctl_dir.stage_upstream_of("tasks")
    _declare(storyctl_dir, [_walkthrough()])

    report = build_report(storyctl_dir.spec_dir, storyctl_dir.repo_root, storyctl_dir.agent_dir)
    flags = {
        p["name"]: p["needs_person"] for s in report.steps for p in s["sub_steps"]
    }
    assert flags == {"architecture": False, "design-doc": False, "walk": True}
