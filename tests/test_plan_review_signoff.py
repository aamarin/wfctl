"""`wfctl step sign-off`, which accepts one edit to a reviewed plan without a
review (FR-023, research R8).

One test per row of contracts/cli.md § `wfctl step sign-off`. Every refusal
asserts that nothing was written, neither the sign-off section nor the
`sign-off` event, since the event is what the reader takes a sign-off from and
a refusal that left one behind would read the pass done.

Since #598 the section goes in the spec folder's `scans/plan-review.md`, which
the PR doesn't carry, so the command no longer asks git about it. The reason
reaches a person through the PR body instead, and `check-body` asks for it.
"""
from __future__ import annotations

import json
import subprocess
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import CLEAN_PLAN, CLEAN_SPEC, write_plan_review
from wfctl._paths import spec_scan
from wfctl._pipeline import build_report
from wfctl._plan_review import COPY_NAME, REPORT_NAME, identity
from wfctl.cli import app

runner = CliRunner()

_REASON = "typo in the reader section"


def _scan(storyctl_dir: types.SimpleNamespace) -> Path:
    return spec_scan(storyctl_dir.spec_dir, "plan-review")


def _reviewed(storyctl_dir: types.SimpleNamespace, *, copy: bool = True) -> Path:
    """A plan reviewed clean, with the copy and the scan the review keeps beside
    it, then edited once. Returns `plan.md`."""
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    plan = storyctl_dir.make_spec_artifact("plan", content=CLEAN_PLAN)
    write_plan_review(storyctl_dir.spec_dir)
    if copy:
        (storyctl_dir.spec_dir / COPY_NAME).write_bytes(plan.read_bytes())
    plan.write_text(plan.read_text() + "\nThe reader returns pending.\n")
    return plan


def _events(agent_dir: Path, kind: str) -> list[dict]:
    log = agent_dir / "events.jsonl"
    if not log.exists():
        return []
    return [e for e in map(json.loads, log.read_text().splitlines()) if e["event"] == kind]


def _pass_state(storyctl_dir: types.SimpleNamespace) -> str:
    report = build_report(storyctl_dir.spec_dir, storyctl_dir.repo_root, storyctl_dir.agent_dir)
    plan = next(s for s in report.steps if s["name"] == "plan")
    return next(p for p in plan["sub_steps"] if p["name"] == "plan-review")["state"]


def _sign_off(reason: str = _REASON, qualified: str = "plan.plan-review"):
    return runner.invoke(app, ["step", "sign-off", qualified, "--reason", reason])


def _nothing_written(storyctl_dir: types.SimpleNamespace) -> None:
    scan = _scan(storyctl_dir)
    assert not scan.exists() or "## Sign-off" not in scan.read_text()
    assert _events(storyctl_dir.agent_dir, "sign-off") == []


def test_a_sign_off_prints_the_diff_records_the_plan_and_reads_done(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The whole of User Story 6's first scenario. The diff comes first because
    FR-023 says the command shows what changed before it records anything, and
    a person who signs off a plan they have not looked at has signed nothing."""
    plan = _reviewed(storyctl_dir)

    result = _sign_off()

    assert result.exit_code == 0, result.output
    out = result.output
    assert "plan.md since the review:" in out
    assert "--- plan-review.plan.md" in out
    assert "+++ plan.md" in out
    assert "+The reader returns pending." in out
    assert out.index("+The reader returns pending.") < out.index("Signed off")
    now = identity(plan)
    assert f'✓ Signed off plan.md {now[:7]} — "{_REASON}"' in out
    assert "Written to" in out and "scans/plan-review.md" in out
    assert "Put the reason in the PR body." in out
    assert "Commit it" not in out

    text = _scan(storyctl_dir).read_text()
    assert "## Sign-off " in text
    assert f"- Signed off: plan.md {now}\n" in text
    assert f"- Reason: {_REASON}\n" in text
    assert "- Reviewed copy: compared\n" in text

    [event] = _events(storyctl_dir.agent_dir, "sign-off")
    assert (event["branch"], event["plan"], event["reason"]) == ("418-storyctl", now, _REASON)
    assert _pass_state(storyctl_dir) == "done"


def test_a_sign_off_writes_nothing_under_the_arch_root(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """#598's acceptance: the branch adds no file under `<arch-root>/scans/`.
    Before it, the section went there and the command refused unless the branch
    carried the file."""
    _reviewed(storyctl_dir)

    assert _sign_off().exit_code == 0

    assert not (storyctl_dir.repo_root / "docs" / "architecture" / "scans").exists()


def test_the_sign_off_commits_nothing(storyctl_dir: types.SimpleNamespace) -> None:
    """Research R8: the verb never commits. A command that committed would put
    a commit on the branch under an agent's name that no person asked for."""
    _reviewed(storyctl_dir)
    head = subprocess.run(
        ["git", "-C", str(storyctl_dir.repo_root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout

    assert _sign_off().exit_code == 0

    assert subprocess.run(
        ["git", "-C", str(storyctl_dir.repo_root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout == head


def test_a_second_sign_off_appends_a_section_and_keeps_the_first(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Research R10: one section per run. The scan file is the history of the
    pass, and a sign-off that replaced the review sections before it would
    erase the review the step reader looks for."""
    plan = _reviewed(storyctl_dir)
    _scan(storyctl_dir).write_text(
        "# Plan review scan for #418\n\n## Review 2026-09-28T14:02Z\n\n- Verdict: satisfied\n"
    )

    assert _sign_off().exit_code == 0
    plan.write_text(plan.read_text() + "\nA second harmless edit.\n")
    assert _sign_off("second typo").exit_code == 0

    text = _scan(storyctl_dir).read_text()
    assert text.startswith("# Plan review scan for #418\n\n## Review 2026-09-28T14:02Z")
    assert text.count("## Sign-off ") == 2
    assert text.index("Reason: typo in the reader section") < text.index("Reason: second typo")


def test_a_sign_off_with_no_review_section_leaves_the_pass_held(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A sign-off needs a review report, so a review ran and had to write its
    section. With none, that review skipped its scan, and the sign-off's own
    section, which has no verdict, mustn't hide it."""
    _reviewed(storyctl_dir)
    _scan(storyctl_dir).unlink()

    assert _sign_off().exit_code == 0

    assert _pass_state(storyctl_dir) == "in_progress"


def test_a_missing_copy_still_signs_off_and_says_so(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Research R8: showing the diff without a copy would strand the sign-off
    exactly when it is needed, so the missing copy is reported and the
    sign-off still records."""
    _reviewed(storyctl_dir, copy=False)

    result = _sign_off()

    assert result.exit_code == 0, result.output
    assert (
        "plan.md since the review: no reviewed copy to compare against "
        "(missing, or not the plan the review recorded)"
    ) in result.output
    assert "- Reviewed copy: missing\n" in _scan(storyctl_dir).read_text()
    assert _pass_state(storyctl_dir) == "done"


def test_a_report_with_no_plan_identity_refuses_the_sign_off(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`## A review that could not run` (report-format.md) writes `absent` for
    a missing plan.md's identity row, which never named a plan to accept. A
    sign-off has nothing to bind to either, so it is refused the same way
    `_evidence.plan_review` refuses to read that report as done, rather than
    recording the plan on disk now as if the report had named it."""
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    plan = storyctl_dir.make_spec_artifact("plan", content=CLEAN_PLAN)
    report = storyctl_dir.spec_dir / REPORT_NAME
    report.write_text(
        "# Plan review\n\n"
        "## Summary\n\nThe review did not run: plan.md was missing.\n\n"
        "## Reviewed inputs\n\n"
        "| Input | Identity | Role |\n"
        "| --- | --- | --- |\n"
        "| plan.md | absent | technical strategy |\n\n"
        "## Findings\n\nnone\n"
    )

    result = _sign_off()

    assert result.exit_code == 1, result.output
    assert "the review recorded no plan.md identity" in result.output
    _nothing_written(storyctl_dir)
    assert identity(plan)  # sanity: plan.md exists and is readable


def test_a_copy_that_is_not_the_reviewed_plan_counts_as_missing(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-025: a copy whose identity differs from the report's is not the plan
    the review read, so a diff against it would show the wrong change."""
    _reviewed(storyctl_dir)
    (storyctl_dir.spec_dir / COPY_NAME).write_text("some other plan\n")

    result = _sign_off()

    assert result.exit_code == 0, result.output
    assert "no reviewed copy to compare against" in result.output
    assert "- Reviewed copy: missing\n" in _scan(storyctl_dir).read_text()


def test_the_next_edit_after_a_sign_off_reads_stale(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """User Story 6, scenario 2. A sign-off covers the plan identity it
    recorded and nothing after it, so an edit made once the sign-off landed is
    as unreviewed as any other."""
    plan = _reviewed(storyctl_dir)
    assert _sign_off().exit_code == 0

    plan.write_text(plan.read_text() + "\nAnother line nobody looked at.\n")

    assert _pass_state(storyctl_dir) == "in_progress"


def test_a_sign_off_line_typed_into_the_scan_file_signs_nothing_off(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Research R8. The agent writes the scan file on every review, so a line
    it typed there is byte-identical to one wfctl wrote. Read as a sign-off,
    it would read the pass done without adding to the review cap, and the cap
    exists because the agent is the party being bounded."""
    plan = _reviewed(storyctl_dir)
    _scan(storyctl_dir).write_text(
        "# Plan review scan for #418\n\n- Verdict: satisfied\n\n"
        "| Check | Status |\n| --- | --- |\n| Deterministic checks | Clear |\n\n"
        "## Sign-off 2026-09-28T14:02Z\n\n"
        f"- Signed off: plan.md {identity(plan)}\n- Reason: trust me\n"
        "- Reviewed copy: compared\n"
    )

    assert _pass_state(storyctl_dir) == "in_progress"


@pytest.mark.parametrize("reason", ["", "   "])
def test_an_empty_reason_writes_nothing(
    storyctl_dir: types.SimpleNamespace, reason: str
) -> None:
    """The sign-off exists to be a sentence a reviewer can disagree with, and
    an empty one is a sign-off nobody can review."""
    _reviewed(storyctl_dir)

    result = _sign_off(reason)

    assert result.exit_code == 1
    assert "--reason cannot be empty" in result.output
    _nothing_written(storyctl_dir)


def test_a_placeholder_reason_writes_nothing(storyctl_dir: types.SimpleNamespace) -> None:
    """The contract's own example writes `"<why>"`, and a reader who pastes it
    back would otherwise record a sign-off whose reason is the placeholder."""
    _reviewed(storyctl_dir)

    result = _sign_off("<why>")

    assert result.exit_code == 1
    assert "placeholder" in result.output
    _nothing_written(storyctl_dir)


def test_a_pass_other_than_the_plan_review_is_refused(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """No other pass binds an identity, so a sign-off of one would record a
    value nothing reads."""
    _reviewed(storyctl_dir)

    result = _sign_off(qualified="brainstorm.architecture")

    assert result.exit_code == 1
    assert (
        "✗ brainstorm.architecture binds no identity; only plan.plan-review can be signed off"
    ) in result.output
    _nothing_written(storyctl_dir)


def test_a_plan_nobody_reviewed_is_refused_and_named_as_step_none(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Research R8 keeps the two claims apart. A sign-off accepts one edit to
    a reviewed plan, and a plan never reviewed is `step none`'s case."""
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    storyctl_dir.make_spec_artifact("plan", content=CLEAN_PLAN)

    result = _sign_off()

    assert result.exit_code == 1
    assert "✗ nothing was reviewed to sign off." in result.output
    assert 'wfctl step none plan.plan-review --reason "…"' in result.output
    _nothing_written(storyctl_dir)


def test_no_plan_is_refused(storyctl_dir: types.SimpleNamespace) -> None:
    plan = _reviewed(storyctl_dir)
    plan.unlink()

    result = _sign_off()

    assert result.exit_code == 1
    assert "✗ there is no plan.md to sign off" in result.output
    _nothing_written(storyctl_dir)


def test_a_branch_with_no_issue_key_signs_off_under_a_heading_with_no_issue(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The refusal this replaced said the scan file had no name without an
    issue. Since #598 the file is `scans/plan-review.md` in the spec folder,
    so only the heading needed the key, and it now names none."""
    monkeypatch.setenv("WFCTL_BRANCH", "storyctl-nokey")
    storyctl_dir.spec_dir = storyctl_dir.spec_dir.parent / "storyctl-nokey"
    storyctl_dir.spec_dir.mkdir()
    (storyctl_dir.spec_dir / "spec.md").write_text(CLEAN_SPEC)
    (storyctl_dir.spec_dir / "plan.md").write_text(CLEAN_PLAN)
    write_plan_review(storyctl_dir.spec_dir)
    _scan(storyctl_dir).unlink()

    result = _sign_off()

    assert result.exit_code == 0, result.output
    assert _scan(storyctl_dir).read_text().startswith("# Plan review scan\n")


def test_check_body_asks_for_the_sign_off_reason(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path
) -> None:
    """FR-012. An agent's sign-off can clear an open BLOCKER, and the PR used to
    show its section. Now the body is where a person reads why, so a body
    missing the reason is a finding, as it is for a design exception."""
    _reviewed(storyctl_dir)
    assert _sign_off().exit_code == 0
    body = tmp_path / "body.md"

    body.write_text("## Summary\n\nNothing about the plan.\n")
    missing = runner.invoke(app, ["check-body", str(body)])
    assert f"the plan sign-off's reason isn't in the body: \"{_REASON}\"" in missing.output

    body.write_text(f"## Summary\n\nPlan sign-off: {_REASON}.\n")
    carried = runner.invoke(app, ["check-body", str(body)])
    assert "plan sign-off's reason" not in carried.output


def test_check_body_reads_the_sign_offs_without_creating_a_state_dir(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`check-body` only reads. Looking up the event log with the default
    `create=True` left a state dir behind for every branch it checked, and would
    fail outright where the state location isn't writable.

    The repo declares `verify` so the body check reaches the verification
    record too. That lookup created the dir on its own after the event log's
    stopped, and a fixture with no `verify` returns before it."""
    (storyctl_dir.repo_root / "wfctl.json").write_text('{"verify": [["true"]]}\n')
    absent = tmp_path / "no-state-yet"
    monkeypatch.setenv("WFCTL_STATE_DIR", str(absent))
    body = tmp_path / "body.md"
    body.write_text("## Summary\n\nNothing about the plan.\n")

    result = runner.invoke(app, ["check-body", str(body)])

    assert "plan sign-off's reason" not in result.output
    assert not absent.exists()


def test_next_reads_a_signed_off_plan_as_status_does(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`next` builds its own evidence rather than going through `build_report`,
    and it writes the file an agent acts on. Without the state dir it sees no
    sign-off, and it would send the agent back to `/plan-review` while `status`
    names `/speckit.tasks`."""
    _reviewed(storyctl_dir)
    assert _sign_off().exit_code == 0

    assert runner.invoke(app, ["next"]).exit_code == 0

    assert "Next step: /speckit.tasks" in (storyctl_dir.agent_dir / "next-step.md").read_text()
