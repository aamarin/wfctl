"""Tests for the design gate asking a record's drawing (#498).

The architecture pass used to read done as soon as any record existed on the
branch, so brainstorm finished with a drawing that `wfctl arch accept` would
refuse weeks later, after the code it describes was written. These pin the pass
asking `_arch.accept_blockers` itself, and the fix line it hands back beside the
reason.

Blocker wording is read from `_arch` rather than typed here. `_arch` owns it and
rewords it freely, as #495 did; a test that copied the sentence would fail on a
rewording that changed nothing this file is about.
"""
from __future__ import annotations

import json
import shlex
import subprocess
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl import _arch
from tests.conftest import write_record
from wfctl.cli import app

runner = CliRunner()

_FLOWCHART = "## Boundary\n\n```mermaid\nflowchart LR\n  A --> B\n```\n\n"
_HAPPY_SEQUENCE = (
    "## Boundary\n\n```mermaid\nsequenceDiagram\n"
    "  A->>B: ask\n  B-->>A: answer\n```\n\n"
)
_FAILING_SEQUENCE = (
    "## Boundary\n\n```mermaid\nsequenceDiagram\n"
    "  A->>B: ask\n  alt refused\n    B-->>A: no\n  else\n    B-->>A: answer\n  end\n```\n\n"
)


def _arch_root(storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = storyctl_dir.repo_root / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    return root


def _first_blocker(root: Path, slug: str) -> str:
    record = next(r for r in _arch.load_records(root) if r.slug == slug)
    return _arch.accept_blockers(record)[0]


def _payload() -> dict:
    result = runner.invoke(app, ["status", "--json"])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def _brainstorm(payload: dict | None = None) -> dict:
    steps = (payload or _payload())["steps"]
    return next(s for s in steps if s["name"] == "brainstorm")


def _dry_run(slug: str) -> str:
    return f"  wfctl arch accept --dry-run -- {slug}"


# Every record `accept` refuses, and the same record once fixed. Kwargs to
# `write_record`, so each row is the whole difference between failing and passing.
_FAILING = {
    "no drawing": ({"diagram": "component"}, {"diagram": "component", "boundary": _FLOWCHART}),
    "no declared kind": ({"boundary": _FLOWCHART}, {"diagram": "component", "boundary": _FLOWCHART}),
    "an unknown kind": (
        {"diagram": "blueprint", "boundary": _FLOWCHART},
        {"diagram": "component", "boundary": _FLOWCHART},
    ),
    "no step that fails": (
        {"diagram": "sequence", "boundary": _HAPPY_SEQUENCE},
        {"diagram": "sequence", "boundary": _FAILING_SEQUENCE},
    ),
    "no log": (
        {"diagram": "component", "boundary": _FLOWCHART, "log": False},
        {"diagram": "component", "boundary": _FLOWCHART},
    ),
}


# --- User Story 1: brainstorm does not finish on a refusable drawing ---------


@pytest.mark.parametrize("case", sorted(_FAILING))
def test_a_proposed_record_acceptance_would_refuse_holds_the_design_step(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    """Each record `accept` refuses holds brainstorm, naming the record and the
    blocker. Before this, every one read `brainstorm ●` and the refusal arrived
    only when someone tried to accept, after implement had built against it."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    broken, _ = _FAILING[case]
    write_record(root, "a-decision", **broken)

    step = _brainstorm()

    assert step["state"] == "in_progress"
    assert step["reason"] == f"a-decision: {_first_blocker(root, 'a-decision')}"
    out = runner.invoke(app, ["status"]).output
    assert "brainstorm   ▶" in out
    assert "a-decision" in out


@pytest.mark.parametrize("case", sorted(_FAILING))
def test_fixing_the_drawing_releases_the_step_on_the_next_read(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    """Nothing is cached and nothing needs resetting (`session-state-is-re-derived`):
    the edit to the record is the whole of what releases it. A gate that stored its
    verdict would need a command between the two reads, and there is none here."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    broken, fixed = _FAILING[case]
    write_record(root, "a-decision", **broken)
    assert _brainstorm()["state"] == "in_progress"

    write_record(root, "a-decision", **fixed)

    step = _brainstorm()
    assert step["state"] == "done"
    assert step["reason"] is None
    assert step["remedy"] is None


def test_two_failing_records_name_the_first_and_hand_back_a_line_for_each(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The step table has room for one reason, so it names one record, and slug
    order makes it the same one on every read. The fix names every record, since
    a person who fixes only the named one would otherwise meet the next on the
    following read, one at a time. Written in reverse order so git's order and
    slug order disagree."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "b-second", diagram="component")
    write_record(root, "a-first", diagram="component")

    step = _brainstorm()

    assert step["reason"] == f"a-first: {_first_blocker(root, 'a-first')}"
    assert step["remedy"] == f"{_dry_run('a-first')}\n{_dry_run('b-second')}"


def test_a_slug_carrying_shell_syntax_is_quoted_in_the_fix_line(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fix is a line the reader pastes, and a slug is a filename nothing
    constrains. Unquoted, a record named `a;id` handed back a fix that ran `id`
    when pasted, which a reviewer confirmed in a scratch repo."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "a;id", diagram="component")

    assert _brainstorm()["remedy"] == "  wfctl arch accept --dry-run -- 'a;id'"


def test_a_slug_starting_with_a_dash_gets_a_fix_line_that_runs(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Quoting leaves `-decision` as it is, and Click reads it as an option, so the
    fix line exited with "No such option" instead of listing the blockers. The
    line is run here rather than compared to a string, because running is the
    promise a fix line makes."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "-decision", diagram="component")

    fix = shlex.split(_brainstorm()["remedy"])
    result = runner.invoke(app, fix[1:])

    assert fix[:3] == ["wfctl", "arch", "accept"]
    assert result.exit_code == 1
    assert _first_blocker(root, "-decision") in result.output


def test_rewording_a_blocker_changes_the_reason_and_not_the_fix(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The level-3 record's third verification item. The fix is built from the
    slug the pass holds, never parsed back out of the reason; parsing it couples
    the fix to wording `_arch` owns, and a rewording would break it with no test
    failing where the wording changed."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "a-decision", diagram="component")
    before = _brainstorm()

    monkeypatch.setattr(_arch, "accept_blockers", lambda record: ["worded: some other way"])
    after = _brainstorm()

    assert after["reason"] == "a-decision: worded: some other way"
    assert after["reason"] != before["reason"]
    assert after["remedy"] == before["remedy"] == _dry_run("a-decision")


def test_a_failing_drawing_routes_back_to_brainstorm_and_never_automatically(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Re-entering brainstorm is where the drawing gets fixed, and an automatic
    loop re-entering it would rewrite `design.md` without touching the record. The
    handoff file carries the reason and the fix, because it is what an unattended
    session reads after a restart."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "a-decision", diagram="component")

    payload = _payload()
    assert payload["next_command"] == "/speckit.brainstorm"
    assert payload["auto"] is False

    runner.invoke(app, ["next"])
    handoff = (storyctl_dir.agent_dir / "next-step.md").read_text()
    assert f"why: a-decision: {_first_blocker(root, 'a-decision')}" in handoff
    assert f"how:\n{_dry_run('a-decision')}" in handoff
    assert "auto: false" in handoff


def test_a_failing_record_beside_an_arch_none_declaration_still_holds_the_step(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A declaration says no boundary was drawn, and the record beside it says one
    was. The record is the stronger claim, and letting the declaration clear it
    would make `arch none` a way past the drawing rules."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    assert runner.invoke(app, ["arch", "none", "--reason", "copy edit"]).exit_code == 0
    write_record(root, "a-decision", diagram="component")

    step = _brainstorm()

    assert step["state"] == "in_progress"
    assert step["reason"].startswith("a-decision: ")


def test_a_failing_record_does_not_hold_a_branch_already_past_specify(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Moving past the design step is one transition, and a gate that came back up
    through plan and implement would refuse work that had already answered it by
    moving on. The pass runs here, with `design.md` and `spec.md` both present,
    which its old docstring said never happened."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact("specify")
    write_record(root, "a-decision", diagram="component")

    step = _brainstorm()

    assert step["state"] == "done"
    assert step["reason"] is None


def test_a_failing_record_with_no_design_doc_still_reads_brainstorm_started(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The record is the first thing brainstorm writes, before `design.md`. Judging
    the drawing inside `_architecture_answered` would read that branch as never
    having started, and send the reader to begin a step already half done."""
    root = _arch_root(storyctl_dir, monkeypatch)
    write_record(root, "a-decision", diagram="component")

    step = _brainstorm()

    assert step["state"] == "in_progress"
    assert step["reason"] == f"a-decision: {_first_blocker(root, 'a-decision')}"


# --- User Story 3: branches the gate does not judge are unaffected -----------
#
# Regression guards, so they pass before this change and after it. Each pins a
# state the drawing check could have broken by judging a record it should not.


def test_an_arch_none_declaration_alone_still_answers_the_design_step(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A change that draws no boundary has no drawing to judge, and a gate that
    looked for one there would hold every copy edit in the repository."""
    _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    assert runner.invoke(app, ["arch", "none", "--reason", "copy edit"]).exit_code == 0

    step = _brainstorm()

    architecture = next(s for s in step["sub_steps"] if s["name"] == "architecture")
    assert architecture["state"] == "done"
    assert step["state"] == "done"


def test_a_branch_with_no_record_keeps_the_existing_reason_and_fix(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The unanswered boundary question still gets its own reason and its two-way
    fix, built from the reason by `_design_remedy` as before. A roll-up that
    copied the pass's empty remedy would have dropped it."""
    from wfctl._evidence import DESIGN_BLOCK_REASON
    from wfctl._pipeline import DESIGN_BLOCK_HELP, arch_location

    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")

    step = _brainstorm()

    assert step["reason"] == DESIGN_BLOCK_REASON
    assert step["remedy"] == DESIGN_BLOCK_HELP.format(
        location=arch_location(root, storyctl_dir.repo_root)
    )


def test_an_accepted_record_is_not_judged_for_its_drawing(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A person ruled on an accepted record, some of them before a drawing was
    required at all. Judging it again would hold a branch that only edited one
    on a rule its acceptance already answered."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "a-decision", "accepted", boundary=_FLOWCHART)

    assert _brainstorm()["state"] == "done"


def test_a_failing_record_marked_rejected_by_hand_releases_the_step(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rejecting a record is a ruling on it, and a rejected record is never
    accepted, so its drawing no longer matters to anyone."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "a-decision", diagram="component")
    assert _brainstorm()["state"] == "in_progress"

    write_record(root, "a-decision", "rejected", diagram="component")

    assert _brainstorm()["state"] == "done"


@pytest.mark.parametrize("corner", ["design", "scans"])
def test_a_failing_looking_file_outside_the_records_is_not_judged(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, corner: str
) -> None:
    """`design/` holds level-3 records and `scans/` holds what a review covered.
    Neither is a level-2 record `accept` would ever be run on, so neither has a
    drawing the gate can ask about."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    assert runner.invoke(app, ["arch", "none", "--reason", "copy edit"]).exit_code == 0
    write_record(root / corner, "a-decision", diagram="component")

    assert _brainstorm()["state"] == "done"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _commit_on_trunk_then_branch(repo: Path) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "on trunk")
    _git(repo, "checkout", "-b", "418-storyctl")


def test_a_failing_record_already_on_trunk_is_not_judged(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate judges what this branch decided, not the repository. This repo
    carries proposed records whose drawings predate the rules `accept` enforces,
    so a gate that read the whole arch root would hold every branch at
    brainstorm. Every other test here writes its records untracked, which never
    reaches the `trunk...HEAD` half of the listing."""
    root = _arch_root(storyctl_dir, monkeypatch)
    write_record(root, "an-older-decision", diagram="component")
    _commit_on_trunk_then_branch(storyctl_dir.repo_root)
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "a-decision", diagram="component", boundary=_FLOWCHART)

    assert _brainstorm()["state"] == "done"


@pytest.mark.parametrize("committed", [False, True], ids=["uncommitted", "committed"])
def test_an_edit_to_a_failing_record_from_trunk_is_not_judged(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, committed: bool
) -> None:
    """The gate judges records the branch added, not ones it edited. This repo
    holds proposed records that `accept` refuses, since their drawings predate
    its rules, and judging edits held any branch that fixed a typo in one of them
    until the drawing was redone. Both halves of the listing are pinned, since
    the working tree reports an edit as ` M` and the trunk diff as `M`."""
    root = _arch_root(storyctl_dir, monkeypatch)
    path = write_record(root, "an-older-decision", diagram="component")
    assert _first_blocker(root, "an-older-decision"), "the record must be one accept refuses"
    _commit_on_trunk_then_branch(storyctl_dir.repo_root)
    storyctl_dir.make_spec_artifact("brainstorm")
    path.write_text(path.read_text() + "A typo, fixed.\n")
    if committed:
        _git(storyctl_dir.repo_root, "commit", "-am", "fix a typo")

    step = _brainstorm()

    assert step["state"] == "done", step["reason"]


def test_an_edited_record_is_still_listed_by_the_accepted_fact(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate and the fact share one listing and ask it different questions.
    The gate narrows to added records, and the fact must not narrow with it: an
    edit to a proposed record is a decision this branch made, and a person has
    not ruled on it yet."""
    root = _arch_root(storyctl_dir, monkeypatch)
    path = write_record(root, "an-older-decision", diagram="component")
    _commit_on_trunk_then_branch(storyctl_dir.repo_root)
    path.write_text(path.read_text() + "A typo, fixed.\n")

    fact = next(f for f in _payload()["facts"] if f["name"] == "architecture accepted")

    assert fact["value"] == "unmet"
    assert "an-older-decision (proposed)" in fact["detail"]


# Each way git can hold a new file, as the git calls that put it there.
_NEW_RECORD_STATES = {
    "untracked": [],
    "intent to add": [["add", "-N", "."]],
    "staged": [["add", "-A"]],
    "committed": [["add", "-A"], ["commit", "-m", "a decision"]],
}


@pytest.mark.parametrize("state", sorted(_NEW_RECORD_STATES))
def test_a_failing_record_the_branch_added_holds_the_step_in_every_git_state(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    """A record is new when the branch base does not have it, however git
    happens to hold it. An earlier version read git's change codes instead, and
    a record added with `git add -N` reads ` A`, which that version dropped; so
    did a staged `A` once a reviewer removed it, and no test noticed."""
    root = _arch_root(storyctl_dir, monkeypatch)
    write_record(root, "an-older-decision", diagram="component", boundary=_FLOWCHART)
    _commit_on_trunk_then_branch(storyctl_dir.repo_root)
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "a-decision", diagram="component")
    for args in _NEW_RECORD_STATES[state]:
        _git(storyctl_dir.repo_root, *args)

    step = _brainstorm()

    assert step["state"] == "in_progress"
    assert step["reason"] == f"a-decision: {_first_blocker(root, 'a-decision')}"


@pytest.mark.parametrize("committed", [False, True], ids=["uncommitted", "committed"])
def test_a_renamed_record_is_judged_whether_or_not_the_rename_is_committed(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, committed: bool
) -> None:
    """A rename is a record at a path the base does not have, so it is judged.
    Reading git's rename code instead made the verdict flip on commit, since a
    plain `mv` is `??` until staged and `R` after, and it moved with each
    machine's `diff.renames`. Judging it fails closed on an older record's new
    name, and never lets a new record through as a rename."""
    root = _arch_root(storyctl_dir, monkeypatch)
    write_record(root, "an-older-decision", diagram="component")
    _commit_on_trunk_then_branch(storyctl_dir.repo_root)
    storyctl_dir.make_spec_artifact("brainstorm")
    _git(storyctl_dir.repo_root, "mv", str(root / "an-older-decision.md"), str(root / "renamed.md"))
    if committed:
        _git(storyctl_dir.repo_root, "commit", "-m", "rename")

    step = _brainstorm()

    assert step["state"] == "in_progress"
    assert step["reason"].startswith("renamed: ")


def test_a_new_record_git_pairs_with_a_deleted_one_is_still_judged(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Git calls a delete and an add a rename when the two files are similar
    enough, and a record written from the same template as the one it replaces
    usually is. A reviewer saw a genuinely new record reported as `R099` and let
    through; asking the base's tree cannot be fooled by the pairing."""
    root = _arch_root(storyctl_dir, monkeypatch)
    write_record(root, "an-older-decision", diagram="component")
    _commit_on_trunk_then_branch(storyctl_dir.repo_root)
    storyctl_dir.make_spec_artifact("brainstorm")
    (root / "an-older-decision.md").unlink()
    write_record(root, "a-decision", diagram="component")
    _git(storyctl_dir.repo_root, "add", "-A")
    _git(storyctl_dir.repo_root, "-c", "diff.renames=true", "commit", "-m", "replace")

    step = _brainstorm()

    assert step["state"] == "in_progress"
    assert step["reason"].startswith("a-decision: ")


def test_a_level_3_record_sharing_a_slug_does_not_judge_the_level_2write_record(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The branch listing matches on bare stems, so a `design/` file named like a
    top-level record on trunk read as that record being touched, and the gate
    held the branch on a drawing it never changed. A reviewer confirmed it in a
    scratch repo: committing only `design/foo.md` held brainstorm on `foo.md`."""
    root = _arch_root(storyctl_dir, monkeypatch)
    write_record(root, "a-decision", diagram="component")
    _commit_on_trunk_then_branch(storyctl_dir.repo_root)
    storyctl_dir.make_spec_artifact("brainstorm")
    assert runner.invoke(app, ["arch", "none", "--reason", "copy edit"]).exit_code == 0
    write_record(root / "design", "a-decision", diagram="component", boundary=_FLOWCHART)

    step = _brainstorm()
    assert step["state"] == "done", step["reason"]


def test_a_failing_record_under_an_arch_root_outside_the_repository_is_not_judged(
    storyctl_dir: types.SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Git cannot say what this branch changed under a root it does not track, so
    there is no list of this branch's records to judge. The boundary question
    already proceeds on that silence, and the drawing check has to agree with it
    rather than hold the step on every record kept outside the repository."""
    root = tmp_path_factory.mktemp("outside") / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "a-decision", diagram="component")

    assert _brainstorm()["state"] == "done"


# --- A repository with no trunk (#508) ----------------------------------------
#
# The fixture's repo has no remote, so renaming its one branch to `trunk` leaves
# `trunk_branch` nothing to find. That is the issue's reproduction, and a test in
# which a trunk resolves has not exercised it.


def _architecture_pass(step: dict) -> dict:
    return next(s for s in step["sub_steps"] if s["name"] == "architecture")


@pytest.mark.parametrize("committed", [False, True], ids=["uncommitted", "committed"])
def test_with_no_trunk_a_failing_record_holds_the_step_until_it_is_committed(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, committed: bool
) -> None:
    """Without a trunk there is no base to diff against, so the listing holds only
    what `git status` reports. The uncommitted record is still judged and holds the
    step. Once committed it is unseen, and the step used to finish with nothing on
    screen to say why; it now finishes and says the committed records went
    unchecked, in `display`, so no caller reads the line as a held step."""
    from wfctl._evidence import DRAWINGS_UNCHECKED

    root = _arch_root(storyctl_dir, monkeypatch)
    _git(storyctl_dir.repo_root, "branch", "-m", "trunk")
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "a-decision", diagram="component")
    if committed:
        _git(storyctl_dir.repo_root, "add", "-A")
        _git(storyctl_dir.repo_root, "commit", "-m", "a decision")

    step = _brainstorm()

    if not committed:
        assert step["state"] == "in_progress"
        assert step["reason"] == f"a-decision: {_first_blocker(root, 'a-decision')}"
        return
    assert step["state"] == "done"
    assert step["reason"] is None
    assert step["remedy"] is None
    assert _architecture_pass(step)["annotation"] == DRAWINGS_UNCHECKED
    assert DRAWINGS_UNCHECKED in runner.invoke(app, ["status"]).output


def test_with_a_trunk_a_finished_pass_carries_no_unchecked_line(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The line is true only when the trunk cannot be resolved. Printed on every
    pass it would be noise a reader learns to skip, and the one repository where
    it is true would lose it with the rest. The trunk is named `main` here rather
    than left to `init.defaultBranch`, which differs between machines."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _git(storyctl_dir.repo_root, "branch", "-m", "main")
    _git(storyctl_dir.repo_root, "checkout", "-b", "418-storyctl")
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "a-decision", diagram="component", boundary=_FLOWCHART)
    _git(storyctl_dir.repo_root, "add", "-A")
    _git(storyctl_dir.repo_root, "commit", "-m", "a decision")

    step = _brainstorm()

    assert step["state"] == "done"
    assert _architecture_pass(step)["annotation"] is None


def test_with_no_trunk_an_arch_root_outside_the_repository_carries_no_unchecked_line(
    storyctl_dir: types.SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Records kept outside the repository are never committed on this branch, so
    a line saying the committed ones went unchecked would be false there. Git was
    never asked about them, trunk or not."""
    root = tmp_path_factory.mktemp("outside") / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    _git(storyctl_dir.repo_root, "branch", "-m", "trunk")
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "a-decision", diagram="component")

    step = _brainstorm()

    assert step["state"] == "done"
    assert _architecture_pass(step)["annotation"] is None
