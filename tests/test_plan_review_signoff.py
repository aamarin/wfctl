"""`wfctl step sign-off`, which accepts one edit to a reviewed plan without a
review (FR-023, research R8).

One test per row of contracts/cli.md § `wfctl step sign-off`. Every refusal
asserts that nothing was written, neither the scan section nor the `sign-off`
event, since the event is what the reader takes a sign-off from and a refusal
that left one behind would read the pass done.
"""
from __future__ import annotations

import json
import subprocess
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import CLEAN_PLAN, CLEAN_SPEC, write_plan_review
from wfctl._pipeline import build_report
from wfctl._plan_review import COPY_NAME, identity
from wfctl.cli import app

runner = CliRunner()

_REASON = "typo in the reader section"


def _arch_root(storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> Path:
    """`docs/architecture` inside the fixture's own repo, so the scan file
    lands in the working tree `touched_on_this_branch` inspects."""
    root = storyctl_dir.repo_root / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    return root


def _scan(root: Path) -> Path:
    return root / "scans" / "418-plan-review.md"


def _reviewed(storyctl_dir: types.SimpleNamespace, *, copy: bool = True) -> Path:
    """A plan reviewed clean, with the copy the review keeps beside it, then
    edited once. Returns `plan.md`."""
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


def _nothing_written(storyctl_dir: types.SimpleNamespace, root: Path) -> None:
    assert not _scan(root).exists()
    assert _events(storyctl_dir.agent_dir, "sign-off") == []


def test_a_sign_off_prints_the_diff_records_the_plan_and_reads_done(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The whole of User Story 6's first scenario. The diff comes first because
    FR-023 says the command shows what changed before it records anything, and
    a person who signs off a plan they have not looked at has signed nothing."""
    root = _arch_root(storyctl_dir, monkeypatch)
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
    assert "Written to docs/architecture/scans/418-plan-review.md" in out
    assert (
        'Commit it: git commit -m "docs(scans): sign off plan.md for #418" '
        "-- docs/architecture/scans/418-plan-review.md"
    ) in out

    text = _scan(root).read_text()
    assert "## Sign-off " in text
    assert f"- Signed off: plan.md {now}\n" in text
    assert f"- Reason: {_REASON}\n" in text
    assert "- Reviewed copy: compared\n" in text

    [event] = _events(storyctl_dir.agent_dir, "sign-off")
    assert (event["branch"], event["plan"], event["reason"]) == ("418-storyctl", now, _REASON)
    assert _pass_state(storyctl_dir) == "done"


def test_the_sign_off_is_left_for_whoever_ran_it_to_commit(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Research R8: the verb prints the commit line and never runs it. A
    command that committed would put a commit on the branch under an agent's
    name that no person asked for."""
    root = _arch_root(storyctl_dir, monkeypatch)
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
    assert _scan(root).exists()


def test_a_second_sign_off_appends_a_section_and_keeps_the_first(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Research R10: one section per run. The scan file is the pull request
    reviewer's history of the pass, and a sign-off that replaced the review
    sections before it would erase what the reviewer came to read."""
    root = _arch_root(storyctl_dir, monkeypatch)
    plan = _reviewed(storyctl_dir)
    _scan(root).parent.mkdir(parents=True)
    _scan(root).write_text("# Plan review scan for #418\n\n## Review 2026-09-28T14:02Z\n\n- Verdict: satisfied\n")

    assert _sign_off().exit_code == 0
    plan.write_text(plan.read_text() + "\nA second harmless edit.\n")
    assert _sign_off("second typo").exit_code == 0

    text = _scan(root).read_text()
    assert text.startswith("# Plan review scan for #418\n\n## Review 2026-09-28T14:02Z")
    assert text.count("## Sign-off ") == 2
    assert text.index("Reason: typo in the reader section") < text.index("Reason: second typo")


def test_a_missing_copy_still_signs_off_and_says_so(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Research R8: showing the diff without a copy would strand the sign-off
    exactly when it is needed, so the missing copy is reported and the
    sign-off still records."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _reviewed(storyctl_dir, copy=False)

    result = _sign_off()

    assert result.exit_code == 0, result.output
    assert (
        "plan.md since the review: no reviewed copy to compare against "
        "(missing, or not the plan the review recorded)"
    ) in result.output
    assert "- Reviewed copy: missing\n" in _scan(root).read_text()
    assert _pass_state(storyctl_dir) == "done"


def test_a_copy_that_is_not_the_reviewed_plan_counts_as_missing(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-025: a copy whose identity differs from the report's is not the plan
    the review read, so a diff against it would show the wrong change."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _reviewed(storyctl_dir)
    (storyctl_dir.spec_dir / COPY_NAME).write_text("some other plan\n")

    result = _sign_off()

    assert result.exit_code == 0, result.output
    assert "no reviewed copy to compare against" in result.output
    assert "- Reviewed copy: missing\n" in _scan(root).read_text()


def test_the_next_edit_after_a_sign_off_reads_stale(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """User Story 6, scenario 2. A sign-off covers the plan identity it
    recorded and nothing after it, so an edit made once the sign-off landed is
    as unreviewed as any other."""
    _arch_root(storyctl_dir, monkeypatch)
    plan = _reviewed(storyctl_dir)
    assert _sign_off().exit_code == 0

    plan.write_text(plan.read_text() + "\nAnother line nobody looked at.\n")

    assert _pass_state(storyctl_dir) == "in_progress"


def test_a_sign_off_line_typed_into_the_scan_file_signs_nothing_off(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Research R8. The agent writes the scan file on every review, so a line
    it typed there is byte-identical to one wfctl wrote. Read as a sign-off,
    it would read the pass done without adding to the review cap, and the cap
    exists because the agent is the party being bounded."""
    root = _arch_root(storyctl_dir, monkeypatch)
    plan = _reviewed(storyctl_dir)
    _scan(root).parent.mkdir(parents=True)
    _scan(root).write_text(
        "# Plan review scan for #418\n\n## Sign-off 2026-09-28T14:02Z\n\n"
        f"- Signed off: plan.md {identity(plan)}\n- Reason: trust me\n"
        "- Reviewed copy: compared\n"
    )

    assert _pass_state(storyctl_dir) == "in_progress"


@pytest.mark.parametrize("reason", ["", "   "])
def test_an_empty_reason_writes_nothing(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, reason: str
) -> None:
    """The sign-off exists to be a sentence a reviewer can disagree with, and
    an empty one is a sign-off nobody can review."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _reviewed(storyctl_dir)

    result = _sign_off(reason)

    assert result.exit_code == 1
    assert "--reason cannot be empty" in result.output
    _nothing_written(storyctl_dir, root)


def test_a_placeholder_reason_writes_nothing(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The contract's own example writes `"<why>"`, and a reader who pastes it
    back would otherwise commit a sign-off whose reason is the placeholder."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _reviewed(storyctl_dir)

    result = _sign_off("<why>")

    assert result.exit_code == 1
    assert "placeholder" in result.output
    _nothing_written(storyctl_dir, root)


def test_a_pass_other_than_the_plan_review_is_refused(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No other pass binds an identity, so a sign-off of one would record a
    value nothing reads."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _reviewed(storyctl_dir)

    result = _sign_off(qualified="brainstorm.architecture")

    assert result.exit_code == 1
    assert (
        "✗ brainstorm.architecture binds no identity; only plan.plan-review can be signed off"
    ) in result.output
    _nothing_written(storyctl_dir, root)


def test_a_plan_nobody_reviewed_is_refused_and_named_as_step_none(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Research R8 keeps the two claims apart. A sign-off accepts one edit to
    a reviewed plan, and a plan never reviewed is `step none`'s case."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    storyctl_dir.make_spec_artifact("plan", content=CLEAN_PLAN)

    result = _sign_off()

    assert result.exit_code == 1
    assert "✗ nothing was reviewed to sign off." in result.output
    assert 'wfctl step none plan.plan-review --reason "…"' in result.output
    _nothing_written(storyctl_dir, root)


def test_no_plan_is_refused(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _arch_root(storyctl_dir, monkeypatch)
    plan = _reviewed(storyctl_dir)
    plan.unlink()

    result = _sign_off()

    assert result.exit_code == 1
    assert "✗ there is no plan.md to sign off" in result.output
    _nothing_written(storyctl_dir, root)


def test_a_branch_with_no_issue_key_is_refused(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The scan file is named for the issue, so a branch without one has no
    file to write, and guessing a name would put the sign-off where no reviewer
    looks."""
    root = _arch_root(storyctl_dir, monkeypatch)
    monkeypatch.setenv("WFCTL_BRANCH", "storyctl-nokey")
    storyctl_dir.spec_dir = storyctl_dir.spec_dir.parent / "storyctl-nokey"
    storyctl_dir.spec_dir.mkdir()
    (storyctl_dir.spec_dir / "spec.md").write_text(CLEAN_SPEC)
    (storyctl_dir.spec_dir / "plan.md").write_text(CLEAN_PLAN)
    write_plan_review(storyctl_dir.spec_dir)

    result = _sign_off()

    assert result.exit_code == 1
    assert "✗ this branch carries no issue key, so the scan file has no name" in result.output
    assert not (root / "scans").exists()
    assert _events(storyctl_dir.agent_dir, "sign-off") == []


def test_a_scan_file_outside_the_working_tree_writes_nothing(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, tmp_path_factory
) -> None:
    """The scan section is the pull request reviewer's copy, so one written
    where the change under review does not carry it is a sign-off nobody can
    see. The event is held back too, since it is what reads the pass done."""
    root = tmp_path_factory.mktemp("elsewhere") / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    _reviewed(storyctl_dir)

    result = _sign_off()

    assert result.exit_code == 1
    assert "Did not sign off plan.md" in result.output
    assert "nothing" in result.output
    _nothing_written(storyctl_dir, root)
    assert _pass_state(storyctl_dir) == "in_progress"


def test_an_ignored_scan_file_writes_nothing_and_keeps_an_earlier_section(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Git ignoring the arch root is the in-tree way to hide the section. An
    earlier review section already in the file is left byte for byte as it
    was, since the refusal restores what it found rather than deleting it."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _reviewed(storyctl_dir)
    (storyctl_dir.repo_root / ".gitignore").write_text(".agent-runs/\nspecs/\ndocs/\n")
    _scan(root).parent.mkdir(parents=True)
    earlier = "# Plan review scan for #418\n\n## Review 2026-09-28T14:02Z\n\n- Verdict: satisfied\n"
    _scan(root).write_text(earlier)

    result = _sign_off()

    assert result.exit_code == 1
    assert "Did not sign off plan.md" in result.output
    assert _scan(root).read_text() == earlier
    assert _events(storyctl_dir.agent_dir, "sign-off") == []


def test_next_reads_a_signed_off_plan_as_status_does(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`next` builds its own evidence rather than going through `build_report`,
    and it writes the file an agent acts on. Without the state dir it sees no
    sign-off, and it would send the agent back to `/plan-review` while `status`
    names `/speckit.tasks`."""
    _arch_root(storyctl_dir, monkeypatch)
    _reviewed(storyctl_dir)
    assert _sign_off().exit_code == 0

    assert runner.invoke(app, ["next"]).exit_code == 0

    assert "Next step: /speckit.tasks" in (storyctl_dir.agent_dir / "next-step.md").read_text()
