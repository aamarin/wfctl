"""Tests for brainstorm's threat-baseline pass (#818).

A level-2 record with a `## Threat model` section describes one security
control and assumes a whole-system map nobody drew. The pass holds brainstorm
on a branch that adds or edits such a record until `THREAT_MODEL.md` is
committed at the repository root, or until the user says the pass doesn't
apply. The agent saying it built the file doesn't count, since it would be
grading its own work (`security-record-needs-baseline.md`).
"""
from __future__ import annotations

import json
import subprocess
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import write_record
from wfctl import _design_exceptions, _evidence
from wfctl._evidence import (
    BASELINE_UNANSWERED_REASON,
    CHECKS_OFF_REASON,
    GIT_UNANSWERED_HELP,
    GIT_UNANSWERED_REASON,
    THREAT_BASELINE_REASON,
)
from wfctl.cli import app

runner = CliRunner()

_FLOWCHART = "## Boundary\n\n```mermaid\nflowchart LR\n  A --> B\n```\n\n"
_THREAT_MODEL = "## Threat model\n\nWho the control defends against.\n\n"
_CLAIM = [
    "step", "none", "brainstorm.threat-baseline", "--reason", "baseline kept in the wiki",
]


def _arch_root(storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = storyctl_dir.repo_root / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    return root


def _payload() -> dict:
    result = runner.invoke(app, ["status", "--json"])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def _brainstorm(payload: dict | None = None) -> dict:
    steps = (payload or _payload())["steps"]
    return next(s for s in steps if s["name"] == "brainstorm")


def _pass(name: str, payload: dict | None = None) -> dict:
    return next(s for s in _brainstorm(payload)["sub_steps"] if s["name"] == name)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _security_record(root: Path, slug: str = "a-security-control", body: str = _THREAT_MODEL) -> Path:
    """A level-2 record that answers the architecture pass and carries `body`."""
    return write_record(root, slug, diagram="component", boundary=_FLOWCHART + body)


def _branch(storyctl_dir: types.SimpleNamespace) -> None:
    """Move the fixture off its trunk, so a commit lands in `trunk...HEAD`."""
    _git(storyctl_dir.repo_root, "checkout", "-b", "418-storyctl")


def _commit_all(repo: Path, message: str = "x") -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)


def _baseline(repo: Path, text: str = "# Threat model\n") -> Path:
    path = repo / "THREAT_MODEL.md"
    path.write_text(text)
    return path


def _held(storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A branch with `design.md` and an uncommitted security record."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    _security_record(root)
    return root


# User Story 1: brainstorm pauses until the baseline is committed


def test_a_security_record_with_no_baseline_holds_brainstorm(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """US1 AC1 and FR-010. The row names the missing file, and the next
    command is the skill that builds it, run without a person since a missing
    baseline isn't a check that needs one.

    The pass holds on a display line, not a reason. A reason would hold the
    step, and a held step routes to `/speckit.brainstorm`, which doesn't build
    the file."""
    _held(storyctl_dir, monkeypatch)

    payload = _payload()
    row = _pass("threat-baseline", payload)

    assert row["state"] == "in_progress"
    assert row["annotation"] == THREAT_BASELINE_REASON
    assert "THREAT_MODEL.md" in THREAT_BASELINE_REASON
    assert payload["next_command"] == "/threat-baseline"
    assert payload["auto"] is True
    assert _pass("software-design", payload)["state"] == "pending"


def test_the_remedy_names_the_skill_and_leaves_the_exception_to_the_user(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-007b. `step none` has no check on who runs it, and an unattended
    agent acts on remedies. So wherever the remedy offers it, which is the
    warning past specify, it says the exception is the user's decision in the
    same block."""
    _held(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("specify")

    remedy = next(
        w["remedy"] for w in _payload()["warnings"] if w["pass"] == "threat-baseline"
    )

    assert "/threat-baseline" in remedy
    assert "wfctl step none brainstorm.threat-baseline" in remedy
    assert "the user's decision, not the agent's" in remedy
    assert remedy.index("/threat-baseline") < remedy.index("wfctl step none")


def test_a_committed_baseline_releases_the_pass(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """US1 AC2. The record and the baseline are both committed on the branch,
    so the record reaches the pass through `trunk...HEAD`."""
    _branch(storyctl_dir)
    _held(storyctl_dir, monkeypatch)
    _baseline(storyctl_dir.repo_root)
    _commit_all(storyctl_dir.repo_root)

    assert _pass("threat-baseline")["state"] == "done"


def test_a_baseline_already_on_the_trunk_is_done_on_the_first_read(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """US1 AC3 and FR-011. The file arrived before this branch, and the pass
    reads it at `HEAD` whichever branch committed it."""
    _baseline(storyctl_dir.repo_root)
    _commit_all(storyctl_dir.repo_root, "baseline on trunk")
    _branch(storyctl_dir)
    _held(storyctl_dir, monkeypatch)

    assert _pass("threat-baseline")["state"] == "done"


def test_an_empty_committed_baseline_is_done(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-013. wfctl checks that the file is committed and never reads it.
    Upstream enforces its own schema when it writes the file."""
    _held(storyctl_dir, monkeypatch)
    _baseline(storyctl_dir.repo_root, "")
    _git(storyctl_dir.repo_root, "add", "THREAT_MODEL.md")
    _git(storyctl_dir.repo_root, "commit", "-m", "empty baseline")

    assert _pass("threat-baseline")["state"] == "done"


def test_a_directory_named_like_the_baseline_doesnt_count(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`git ls-tree --name-only` lists a directory by its name, so a committed
    `THREAT_MODEL.md/notes.md` read as the baseline and released the pass with
    no threat model in it (CodeRabbit on #856)."""
    _held(storyctl_dir, monkeypatch)
    folder = storyctl_dir.repo_root / "THREAT_MODEL.md"
    folder.mkdir()
    (folder / "notes.md").write_text("x\n")
    _git(storyctl_dir.repo_root, "add", "THREAT_MODEL.md")
    _git(storyctl_dir.repo_root, "commit", "-m", "a folder, not a baseline")

    assert _pass("threat-baseline")["state"] == "in_progress"


@pytest.mark.parametrize("staged", [False, True], ids=["untracked", "staged"])
def test_a_baseline_that_isnt_committed_keeps_the_pass_held(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, staged: bool
) -> None:
    """The spec's first edge case. The PR wouldn't carry an uncommitted file,
    and a staged one isn't in it either, so the reviewer couldn't read the
    baseline the per-control threat model cites."""
    _held(storyctl_dir, monkeypatch)
    _baseline(storyctl_dir.repo_root)
    if staged:
        _git(storyctl_dir.repo_root, "add", "THREAT_MODEL.md")

    assert _pass("threat-baseline")["state"] == "in_progress"


def test_a_baseline_outside_the_root_doesnt_count(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The spec's second edge case. A file under the arch root is somewhere
    else, and the user says so with `step none`."""
    _branch(storyctl_dir)
    root = _held(storyctl_dir, monkeypatch)
    (root / "THREAT_MODEL.md").write_text("# elsewhere\n")
    _commit_all(storyctl_dir.repo_root)

    assert _pass("threat-baseline")["state"] == "in_progress"


def test_a_branch_with_no_threat_model_record_skips_the_pass(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """US1 AC4, FR-009, and SC-002. A branch that changes no security control
    gets no new stop."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    _security_record(root, body="")

    row = _pass("threat-baseline")

    assert row["state"] == "skipped"
    assert _pass("software-design")["state"] != "pending"


def test_a_threat_model_only_on_the_trunk_doesnt_apply(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The spec's fourth edge case. The pass is about the per-control threat
    model this branch writes, not one an earlier branch merged."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _security_record(root, "an-old-control")
    _commit_all(storyctl_dir.repo_root, "old record on trunk")
    _branch(storyctl_dir)
    storyctl_dir.make_spec_artifact("brainstorm")
    _security_record(root, "an-unrelated-change", body="")

    assert _pass("threat-baseline")["state"] == "skipped"


def test_editing_an_existing_security_record_applies_the_pass(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Clarify Q3. An edit to a security record usually means its control is
    changing, so the pass reads records the branch edits as well as adds."""
    root = _arch_root(storyctl_dir, monkeypatch)
    record = _security_record(root)
    _commit_all(storyctl_dir.repo_root, "record on trunk")
    _branch(storyctl_dir)
    storyctl_dir.make_spec_artifact("brainstorm")
    record.write_text(record.read_text() + "\nAn edit.\n")

    assert _pass("threat-baseline")["state"] == "in_progress"


def test_the_pass_reads_the_same_with_auto_approve_on(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-014. A missing baseline isn't a check that needs a person, so the
    agent runs `/threat-baseline` itself and the pass holds either way."""
    _held(storyctl_dir, monkeypatch)
    before = _pass("threat-baseline")
    assert runner.invoke(app, ["auto-approve", "on"]).exit_code == 0

    payload = _payload()
    after = _pass("threat-baseline", payload)

    assert payload["auto_approve"] is True
    assert after["state"] == before["state"] == "in_progress"
    assert after["needs_person"] is False


# Git that can't answer holds the pass rather than skipping it


def test_a_failed_head_read_holds_on_its_own_reason(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Research R5. `GIT_UNANSWERED_REASON` is about whether the branch wrote
    a record, and this read asks something else."""
    _held(storyctl_dir, monkeypatch)
    monkeypatch.setattr(_evidence, "_baseline_committed", lambda repo_root: None)

    row = _pass("threat-baseline")

    assert row["state"] == "in_progress"
    assert _brainstorm()["reason"] == BASELINE_UNANSWERED_REASON
    ev = _evidence.build_evidence(storyctl_dir.spec_dir, storyctl_dir.repo_root)
    verdict = _evidence.brainstorm_threat_baseline(ev)
    assert verdict.remedy == _evidence.BASELINE_UNANSWERED_HELP


def test_the_head_read_tells_absence_apart_from_git_failing(
    storyctl_dir: types.SimpleNamespace, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """`git cat-file -e HEAD:<path>` exits 128 for a missing path and for git
    failing, which would read every missing baseline as git failing. The read
    the pass uses keeps the two apart."""
    repo = storyctl_dir.repo_root
    assert _evidence._baseline_committed(repo) is False
    _baseline(repo)
    _commit_all(repo)
    assert _evidence._baseline_committed(repo) is True
    assert _evidence._baseline_committed(tmp_path_factory.mktemp("not-a-repo")) is None


def test_a_repository_with_no_commits_reads_the_baseline_absent(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """`git ls-tree HEAD` fails when nothing is committed yet, which would hold
    the pass on "git can't see" with no fix. The answer is known, though, and
    `/threat-baseline` is the fix (#818 code review)."""
    repo = tmp_path_factory.mktemp("unborn")
    _git(repo, "init", "-q")

    assert _evidence._baseline_committed(repo) is False


def test_git_that_cant_list_the_records_holds_rather_than_skips(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Research R4. `branch_records` returns an empty mapping when git can't
    answer, which would read as "no record has a threat model" and skip the
    pass silently. Asking `touched_on_this_branch` first is what tells the two
    apart."""
    _held(storyctl_dir, monkeypatch)
    from wfctl import _paths
    real = _paths.touched_on_this_branch

    def fails_for_the_arch_root(repo_root: Path, path: Path, exclude: object = None) -> bool | None:
        if path.name == "architecture":
            return None
        return real(repo_root, path, exclude)  # type: ignore[arg-type]

    monkeypatch.setattr(_paths, "touched_on_this_branch", fails_for_the_arch_root)
    ev = _evidence.build_evidence(storyctl_dir.spec_dir, storyctl_dir.repo_root)
    verdict = _evidence.brainstorm_threat_baseline(ev)

    assert verdict.state == "in_progress"
    assert verdict.reason == GIT_UNANSWERED_REASON
    assert verdict.remedy == GIT_UNANSWERED_HELP


def test_no_trunk_holds_when_a_committed_record_cant_be_seen(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Plan review PR-013. With no trunk, the listing holds only uncommitted
    records, so a committed security record is invisible once any other record
    is uncommitted. The drawing check can skip there because `arch accept`
    catches a bad drawing later, and nothing later catches a missing baseline."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _git(storyctl_dir.repo_root, "branch", "-m", "418-storyctl")
    storyctl_dir.make_spec_artifact("brainstorm")
    _security_record(root)
    _commit_all(storyctl_dir.repo_root, "security record")
    _security_record(root, "a-second-record", body="")

    payload = _payload()

    assert _pass("architecture", payload)["state"] == "done"
    assert _pass("threat-baseline", payload)["state"] == "in_progress"
    assert _brainstorm(payload)["reason"] == GIT_UNANSWERED_REASON


def test_no_trunk_releases_the_pass_once_the_baseline_is_committed(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The hold above exists because a committed security record might need a
    baseline nobody can see. Once the baseline is committed, any such record
    already has one, so holding blocked brainstorm on a requirement already met
    (CodeRabbit on #856)."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _git(storyctl_dir.repo_root, "branch", "-m", "418-storyctl")
    storyctl_dir.make_spec_artifact("brainstorm")
    _security_record(root)
    _baseline(storyctl_dir.repo_root)
    _commit_all(storyctl_dir.repo_root, "security record and baseline")
    _security_record(root, "a-second-record", body="")

    assert _pass("threat-baseline")["state"] == "done"


def test_an_arch_root_outside_the_tree_skips_with_a_display_line(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Nothing failed: git is being asked about a path it doesn't track, as
    `fact_architecture_accepted` reads it. The architecture pass holds such a
    branch first, so this is read through the reader alone."""
    outside = tmp_path_factory.mktemp("outside-architecture")
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(outside))
    _security_record(outside)
    storyctl_dir.make_spec_artifact("brainstorm")
    ev = _evidence.build_evidence(storyctl_dir.spec_dir, storyctl_dir.repo_root)

    verdict = _evidence.brainstorm_threat_baseline(ev)

    assert verdict.state == "skipped"
    assert verdict.reason is None
    assert verdict.display == "records are kept outside this repository"


def test_turning_the_checks_off_skips_the_pass(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same setting turns off both sibling checks, and a display line
    rather than a reason keeps it from warning on every `status`."""
    _held(storyctl_dir, monkeypatch)
    (storyctl_dir.repo_root / "wfctl.json").write_text(json.dumps({"design_record_checks": "off"}))

    row = _pass("threat-baseline")

    assert row["state"] == "skipped"
    assert CHECKS_OFF_REASON in runner.invoke(app, ["status", "--all"]).output


# How the section is found


def test_a_heading_inside_a_fenced_example_doesnt_count(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Research R4. A record that quotes the heading as an example isn't a
    record with a threat model."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    _security_record(root, body="```markdown\n## Threat model\n```\n\n")

    assert _pass("threat-baseline")["state"] == "skipped"


def test_a_heading_with_a_suffix_counts(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The pass matches `^## Threat model`, the pattern `reviewing-security`
    greps for, so the pass and the security reviewers agree on which records
    carry a threat model."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    _security_record(root, body="## Threat model (revised)\n\nx\n\n")

    assert _pass("threat-baseline")["state"] == "in_progress"


# Past specify, and the user's exception


def test_past_specify_a_missing_baseline_is_a_warning(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-012a. A branch already past specify when this check ships isn't sent
    backwards. The missing baseline travels as a warning instead."""
    _held(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("specify")

    payload = _payload()

    assert _pass("threat-baseline", payload)["state"] == "done"
    assert any(
        w["step"] == "brainstorm" and w["pass"] == "threat-baseline"
        and w["reason"] == THREAT_BASELINE_REASON
        for w in payload["warnings"]
    )


def test_past_specify_a_git_failure_is_a_warning_too(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Research R6 row 8 folds every held reading, the git-failure ones
    included, as `brainstorm_software_design`'s `spec.md` escape does."""
    _held(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("specify")
    monkeypatch.setattr(_evidence, "_baseline_committed", lambda repo_root: None)

    payload = _payload()

    assert _pass("threat-baseline", payload)["state"] == "done"
    assert any(w["reason"] == BASELINE_UNANSWERED_REASON for w in payload["warnings"])


def test_the_users_exception_skips_the_pass_and_reaches_the_pr_body(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """US1 AC5 and FR-012. The claim reads `skipped` with its reason, as every
    claimed pass does, and its reason is one `wfctl check-body` asks the PR
    body for."""
    _held(storyctl_dir, monkeypatch)

    result = runner.invoke(app, _CLAIM)
    assert result.exit_code == 0, result.output

    payload = _payload()
    assert _pass("threat-baseline", payload)["state"] == "skipped"
    assert "claimed: baseline kept in the wiki" in runner.invoke(app, ["status", "--all"]).output
    reasons = _design_exceptions.reasons(storyctl_dir.spec_dir)
    assert any("baseline kept in the wiki" in str(r) for r in reasons)
