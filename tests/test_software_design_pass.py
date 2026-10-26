"""Tests for brainstorm's software design pass, and for both brainstorm checks
holding when git can't answer (#648).

On #635 an agent answered the level-3 question with a file layout, and the
pipeline moved on because nothing checked that the question was put. The pass
holds brainstorm until the branch writes a record under `<arch-root>/design/` or
claims the pass with `wfctl step none`. The same change made the architecture
check hold where it used to let a branch through silently, when git can't say
whether a record was written, with `design_record_checks` as the way a
repository whose arch root git can't see turns both checks off.
"""
from __future__ import annotations

import json
import subprocess
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import write_record
from wfctl import _paths
from wfctl._evidence import (
    CHECKS_OFF_REASON,
    GIT_UNANSWERED_HELP,
    GIT_UNANSWERED_REASON,
    SOFTWARE_DESIGN_HELP,
    SOFTWARE_DESIGN_REASON,
)
from wfctl.cli import app


def _write_config(repo: Path, config: object) -> None:
    (repo / "wfctl.json").write_text(json.dumps(config))


# --- the `design_record_checks` setting ------------------------------------


def test_a_repo_with_no_wfctl_json_runs_both_checks(tmp_path: Path) -> None:
    """The default has to be on. A repository that never heard of the setting
    is the one the gate was written for, and off-by-default would ship it
    dead."""
    assert _paths.design_record_checks(tmp_path) == (True, [])


def test_a_wfctl_json_without_the_key_runs_both_checks(tmp_path: Path) -> None:
    _write_config(tmp_path, {"trunk": "main"})
    assert _paths.design_record_checks(tmp_path) == (True, [])


def test_on_and_off_are_the_two_values_the_setting_takes(tmp_path: Path) -> None:
    _write_config(tmp_path, {"design_record_checks": "on"})
    assert _paths.design_record_checks(tmp_path) == (True, [])
    _write_config(tmp_path, {"design_record_checks": "off"})
    assert _paths.design_record_checks(tmp_path) == (False, [])


def test_a_typo_leaves_the_checks_on_and_is_reported(tmp_path: Path) -> None:
    """A mistake must never turn a check off. Reading `"no"` or `false` as off
    would let a branch through on a value nobody meant, and the hold this
    feature adds would be gone with nothing saying so."""
    for value in ("yes", "no", False, None):
        _write_config(tmp_path, {"design_record_checks": value})
        on, problems = _paths.design_record_checks(tmp_path)
        assert on is True
        assert problems == [f"'design_record_checks' is {value!r}; use \"on\" or \"off\""]


def test_an_arch_root_outside_the_project_is_a_problem_while_the_checks_are_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every branch in that repo would be held at brainstorm, and `check config`
    is where the maintainer hears it before the first branch does."""
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(tmp_path / "outside"))

    problems = _paths.design_record_checks_problems(repo)
    assert len(problems) == 1
    assert "outside the project" in problems[0]
    assert '"design_record_checks": "off"' in problems[0]

    _write_config(repo, {"design_record_checks": "off"})
    assert _paths.design_record_checks_problems(repo) == []


def test_an_arch_root_inside_the_project_is_no_problem(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(tmp_path / "docs" / "architecture"))
    assert _paths.design_record_checks_problems(tmp_path) == []


# --- the pass itself ---------------------------------------------------------

runner = CliRunner()

_FLOWCHART = "## Boundary\n\n```mermaid\nflowchart LR\n  A --> B\n```\n\n"
_CLAIM = ["step", "none", "brainstorm.software-design", "--reason", "no new module"]


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


def _answer_architecture() -> None:
    result = runner.invoke(app, ["arch", "none", "--reason", "no boundary"])
    assert result.exit_code == 0, result.output


def _held_branch(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """`design.md` and an architecture answer, and nothing for level 3."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    _answer_architecture()
    return root


def _write_design_record(root: Path, slug: str = "a-structural-choice") -> Path:
    path = root / "design" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {slug}\n")
    return path


# User Story 1: a branch that skipped software design is held


def test_a_branch_with_no_software_design_answer_is_held_at_brainstorm(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The defect #635 showed: brainstorm finished with the level-3 question
    never put, because nothing read for it. The pass's own reason and remedy
    reach the step, so `next:` names both answers rather than the boundary
    help the architecture pass would print."""
    _held_branch(storyctl_dir, monkeypatch)

    payload = _payload()
    step = _brainstorm(payload)

    assert payload["current"] == "brainstorm"
    assert step["state"] == "in_progress"
    assert _pass("architecture", payload)["state"] == "done"
    assert _pass("software-design", payload)["state"] == "in_progress"
    assert _pass("design-doc", payload)["state"] == "pending"
    assert step["reason"] == SOFTWARE_DESIGN_REASON
    assert step["remedy"] == SOFTWARE_DESIGN_HELP.format(location="docs/architecture/design")
    out = runner.invoke(app, ["status"]).output
    assert "no software design record for this change" in out
    assert "wfctl step none brainstorm.software-design" in out


def test_a_record_outside_design_answers_architecture_and_not_software_design(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The two questions read two folders. A level-2 record at the arch root is
    the boundary answer, and counting it as the level-3 one too would let a
    branch skip level 3 by writing level 2, which is the layering the passes
    exist to keep apart."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "a-boundary", diagram="component", boundary=_FLOWCHART)

    payload = _payload()

    assert _pass("architecture", payload)["state"] == "done"
    assert _pass("software-design", payload)["state"] == "in_progress"


def test_a_design_record_already_on_trunk_does_not_answer_this_branch(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """US2 acceptance 2. A record that exists is not one this branch wrote, and
    a check that read the folder rather than the branch would release every
    branch in a repository with one old record."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _write_design_record(root, "an-older-choice")
    _git(storyctl_dir.repo_root, "add", "-A")
    _git(storyctl_dir.repo_root, "commit", "-m", "on trunk")
    _git(storyctl_dir.repo_root, "checkout", "-b", "418-storyctl")
    storyctl_dir.make_spec_artifact("brainstorm")
    _answer_architecture()

    assert _pass("software-design")["state"] == "in_progress"


def test_an_unattended_run_stops_at_a_held_software_design_pass(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """US1 acceptance 3. Orchestration reads `auto` from `next-step.md`, and a
    `true` here would carry an auto-approving run on to specify with the
    question still unput."""
    _arch_root(storyctl_dir, monkeypatch)
    assert runner.invoke(app, ["start", "--auto-approve"]).exit_code == 0
    storyctl_dir.make_spec_artifact("brainstorm")
    _answer_architecture()

    result = runner.invoke(app, ["resume"])

    assert "/speckit.brainstorm" in result.output
    assert "auto: false" in (storyctl_dir.agent_dir / "next-step.md").read_text()


def test_a_declared_pass_named_software_design_is_a_check_config_finding(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A repository's own pass by the built-in name would shadow the gate, so
    it is dropped and reported, as every other built-in name is."""
    _write_config(storyctl_dir.repo_root, {"steps": {"brainstorm": [
        {"name": "software-design", "manual": True},
    ]}})

    result = runner.invoke(app, ["check", "config"])

    assert result.exit_code == 1
    assert "brainstorm.software-design is wfctl's own pass" in result.output


def _pass_rows(output: str, names: list[str]) -> list[str]:
    return [
        line for line in output.splitlines()
        if line.startswith("  ") and line.strip().split(" ")[0] in names
    ]


def test_every_pass_name_is_separated_from_its_glyph(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The old fixed width left one space before the glyph for
    `software-design`, and none for a declared `plan-walkthrough`. A declared
    name longer than every built-in one is what fails a width hard-coded to fit
    the built-ins."""
    _held_branch(storyctl_dir, monkeypatch)
    long_name = "a-very-long-declared-pass"
    _write_config(storyctl_dir.repo_root, {"steps": {"specify": [
        {"name": long_name, "manual": True, "evidence": "long.md"},
    ]}})

    out = runner.invoke(app, ["status", "--all"]).output
    names = ["architecture", "software-design", long_name]
    rows = _pass_rows(out, names)

    assert {row.strip().split(" ")[0] for row in rows} == set(names)
    for row in rows:
        name = row.strip().split(" ")[0]
        assert row.startswith(f"  {name}  "), row


# User Story 2: a design record releases the hold


def test_an_uncommitted_design_record_releases_the_pass(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _held_branch(storyctl_dir, monkeypatch)
    _write_design_record(root)

    payload = _payload()

    assert _pass("software-design", payload)["state"] == "done"
    assert payload["current"] == "specify"


def test_a_committed_design_record_releases_the_pass(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Committed on the branch, so it is only in `trunk...HEAD`, the half of the
    listing an uncommitted record never reaches."""
    _git(storyctl_dir.repo_root, "checkout", "-b", "418-storyctl")
    root = _held_branch(storyctl_dir, monkeypatch)
    _write_design_record(root)
    _git(storyctl_dir.repo_root, "add", "-A")
    _git(storyctl_dir.repo_root, "commit", "-m", "the record")

    assert _pass("software-design")["state"] == "done"


# User Story 3: a claim releases the hold


def test_a_claim_releases_the_pass_with_no_wfctl_json(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The "no" answer. The pass ships with wfctl, so a repository that has
    declared nothing can still claim it."""
    _held_branch(storyctl_dir, monkeypatch)
    assert not (storyctl_dir.repo_root / "wfctl.json").exists()

    result = runner.invoke(app, _CLAIM)
    assert result.exit_code == 0, result.output

    payload = _payload()
    assert _pass("software-design", payload)["state"] == "skipped"
    assert payload["current"] == "specify"
    assert "software-design" not in runner.invoke(app, ["status"]).output
    assert "claimed: no new module" in runner.invoke(app, ["status", "--all"]).output


def test_a_claim_beside_a_record_still_reads_as_the_claim(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Claims are read before the reader runs, for every pass. A branch that
    claimed and then wrote a record anyway keeps the claim's reason in front of
    the reviewer."""
    root = _held_branch(storyctl_dir, monkeypatch)
    _write_design_record(root)
    assert runner.invoke(app, _CLAIM).exit_code == 0

    assert "claimed: no new module" in runner.invoke(app, ["status", "--all"]).output


def test_a_branch_past_specify_is_not_held(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SC-003. A branch that left brainstorm before the pass existed must not
    move backwards when wfctl upgrades."""
    _held_branch(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("specify")

    assert _pass("software-design")["state"] == "done"
    assert _brainstorm()["state"] == "done"


# User Story 5: a repo where git can't answer is held until it says why


def _no_git_branch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A feature folder with `design.md`, in a directory git knows nothing
    about, so every git command the checks run fails."""
    feature = tmp_path / "specs" / "418-storyctl"
    feature.mkdir(parents=True)
    (feature / "design.md").write_text("# design\n")
    monkeypatch.setenv("WFCTL_STATE_DIR", str(tmp_path / ".agent-runs"))
    monkeypatch.setenv("WFCTL_BRANCH", "418-storyctl")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(tmp_path / "specs"))
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(tmp_path))
    return feature


def _drop_trunk(repo: Path) -> None:
    """Rename the fixture's default branch to one `trunk_branch` won't guess."""
    _git(repo, "branch", "-m", "418-storyctl")


def _assert_held_on_git(payload: dict) -> None:
    step = _brainstorm(payload)
    assert step["state"] == "in_progress"
    assert step["reason"] == GIT_UNANSWERED_REASON
    assert step["remedy"] == GIT_UNANSWERED_HELP
    assert '"trunk"' in step["remedy"]
    assert '"design_record_checks": "off"' in step["remedy"]


def test_a_branch_with_no_trunk_is_held_on_the_git_reason(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-006. Before #648 the architecture check let this branch through, so
    a repo whose base branch wfctl couldn't find never knew the check wasn't
    running. Nothing is uncommitted, so git has only `trunk...HEAD` to ask."""
    _arch_root(storyctl_dir, monkeypatch)
    _drop_trunk(storyctl_dir.repo_root)
    storyctl_dir.make_spec_artifact("brainstorm")

    payload = _payload()

    _assert_held_on_git(payload)
    assert _pass("architecture", payload)["state"] == "in_progress"
    assert _pass("software-design", payload)["state"] == "pending"
    # The runner renders at 80 columns. A reason that wrapped would break the
    # row under the step table and read as a new one, and the string would no
    # longer be found whole.
    assert GIT_UNANSWERED_REASON in runner.invoke(app, ["status"]).output


def test_a_directory_git_knows_nothing_about_is_held_the_same_way(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The third way git can't answer: the command fails. That is a broken
    checkout rather than a setting, and the hold is what says so."""
    _no_git_branch(tmp_path, monkeypatch)

    _assert_held_on_git(_payload())


def test_naming_the_trunk_makes_both_checks_compare_against_it(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """US5 acceptance 2. `trunk` is the remedy's first line, so it has to be a
    way out: once declared, the checks ask git again and get an answer."""
    root = _arch_root(storyctl_dir, monkeypatch)
    repo = storyctl_dir.repo_root
    _git(repo, "branch", "-m", "base")
    _git(repo, "checkout", "-b", "418-storyctl")
    _write_config(repo, {"trunk": "base"})
    _git(repo, "add", "wfctl.json")
    _git(repo, "commit", "-m", "declare the trunk")
    storyctl_dir.make_spec_artifact("brainstorm")
    _answer_architecture()

    assert _brainstorm()["reason"] == SOFTWARE_DESIGN_REASON

    _write_design_record(root)
    assert _pass("software-design")["state"] == "done"


def test_an_arch_root_outside_the_project_is_held_on_the_git_reason(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """A record there is one git can't see, so neither check can tell whether
    the branch wrote one, whatever is in the folder."""
    outside = tmp_path_factory.mktemp("outside-architecture")
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(outside))
    write_record(outside, "a-boundary", diagram="component", boundary=_FLOWCHART)
    storyctl_dir.make_spec_artifact("brainstorm")

    _assert_held_on_git(_payload())


@pytest.mark.parametrize("repo_kind", ["no trunk", "outside arch root"])
def test_turning_the_checks_off_skips_both_and_warns_about_neither(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
    tmp_path_factory: pytest.TempPathFactory, repo_kind: str,
) -> None:
    """FR-006a. The two rows carry their text as display, not as a reason. A
    finished pass's reason is a warning, and a repository that turned the
    checks off on purpose would be warned on every `status`."""
    if repo_kind == "no trunk":
        _arch_root(storyctl_dir, monkeypatch)
        _drop_trunk(storyctl_dir.repo_root)
    else:
        monkeypatch.setenv("WFCTL_ARCH_DIR", str(tmp_path_factory.mktemp("outside")))
    _write_config(storyctl_dir.repo_root, {"design_record_checks": "off"})
    storyctl_dir.make_spec_artifact("brainstorm")

    payload = _payload()

    assert payload["warnings"] == []
    assert payload["current"] == "specify"
    for name in ("architecture", "software-design"):
        row = _pass(name, payload)
        assert row["state"] == "skipped"
        assert row["annotation"] == CHECKS_OFF_REASON
    assert "turned off" not in runner.invoke(app, ["status"]).output
    shown = runner.invoke(app, ["status", "--all"]).output
    assert shown.count(CHECKS_OFF_REASON) == 2
    assert "⚠" not in shown


def test_a_value_other_than_on_or_off_is_a_finding_and_leaves_the_checks_on(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    _held_branch(storyctl_dir, monkeypatch)
    _write_config(storyctl_dir.repo_root, {"design_record_checks": "yes"})

    result = runner.invoke(app, ["check", "config"])

    assert result.exit_code == 1
    assert "'design_record_checks' is 'yes'; use \"on\" or \"off\"" in result.output
    assert _pass("software-design")["state"] == "in_progress"


@pytest.mark.parametrize("has_config", [True, False], ids=["wfctl.json", "no wfctl.json"])
def test_an_outside_arch_root_with_the_checks_on_is_a_finding(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
    tmp_path_factory: pytest.TempPathFactory, has_config: bool,
) -> None:
    """FR-006b. The repo with no `wfctl.json` is the one this finding is
    written for, since its outside arch root is declared in the manifest or the
    environment. A finding that waited for the file would never print there."""
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(tmp_path_factory.mktemp("outside")))
    if has_config:
        _write_config(storyctl_dir.repo_root, {"trunk": "main"})

    result = runner.invoke(app, ["check", "config"])

    assert result.exit_code == 1
    assert "outside the project" in result.output
    assert "no configuration to check" not in result.output


def test_the_architecture_check_no_longer_lets_a_branch_through_on_silence(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The change to the old check, asserted on that check alone: an
    architecture declaration answers it, and with no trunk and nothing
    uncommitted, git can't say whether one was written."""
    _arch_root(storyctl_dir, monkeypatch)
    _drop_trunk(storyctl_dir.repo_root)
    storyctl_dir.make_spec_artifact("brainstorm")

    architecture = _pass("architecture")

    assert architecture["state"] == "in_progress"
    assert architecture["annotation"] == GIT_UNANSWERED_REASON


def test_both_checks_let_blocks_decide_what_gits_silence_means(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With `blocks` saying silence never stops a step, both checks must read
    done where git can't answer. A reader that settled `inconclusive` itself
    before asking `blocks` would still hold here.
    `test_every_inconclusive_verdict_goes_through_blocks` can't see that: it
    checks that each reader calls `blocks`, not when."""
    from wfctl import _evidence

    monkeypatch.setattr(_evidence, "blocks", lambda verdict, source: verdict == "unsatisfied")
    _arch_root(storyctl_dir, monkeypatch)
    _drop_trunk(storyctl_dir.repo_root)
    storyctl_dir.make_spec_artifact("brainstorm")

    payload = _payload()

    assert _pass("architecture", payload)["state"] == "done"
    assert _pass("software-design", payload)["state"] == "done"


def test_brainstorm_reads_pending_when_git_cant_answer_and_nothing_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A held check with no `design.md` is the same as a branch where nothing
    has happened yet, as it is in a repo where git can answer."""
    feature = _no_git_branch(tmp_path, monkeypatch)
    (feature / "design.md").unlink()

    assert _brainstorm()["state"] == "pending"


def test_with_the_checks_off_an_empty_branch_starts_at_the_design_doc(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Off reads both checks as answered, so `brainstorm` is under way from the
    first read, with `design.md` the one thing missing. A repo whose arch root
    is outside the tree read this way before #648 as well."""
    _arch_root(storyctl_dir, monkeypatch)
    _write_config(storyctl_dir.repo_root, {"design_record_checks": "off"})

    payload = _payload()

    assert _brainstorm(payload)["state"] == "in_progress"
    assert _pass("design-doc", payload)["state"] == "in_progress"
