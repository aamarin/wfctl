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
from tests.conftest import write_design_record, write_record
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
    write_design_record(root)

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


def test_a_failing_record_past_specify_warns_and_names_the_fix(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The check used to go quiet once `spec.md` existed, so a record added or
    edited after specify said nothing until someone ran `accept` on it. It now
    reports through `warnings`, with the same reason and fix line the held step
    carries before specify, and the step stays done. Read from the payload and
    the console both, since a line only one of them shows is a view deriving
    state below the payload."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact("specify")
    write_record(root, "a-decision", diagram="component")

    payload = _payload()

    assert _brainstorm(payload)["state"] == "done"
    assert payload["warnings"] == [{
        "step": "brainstorm",
        "pass": "architecture",
        "reason": f"a-decision: {_first_blocker(root, 'a-decision')}",
        "remedy": _dry_run("a-decision"),
    }]
    # The blocker sentence wraps at the runner's 80 columns, so the slug and the
    # fix line stand in for it.
    shown = runner.invoke(app, ["next"]).output
    assert "a-decision:" in shown
    assert _dry_run("a-decision").strip() in shown


def test_a_good_drawing_past_specify_carries_no_warning(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`_warning_block` writes nothing when there is nothing to say, so a
    passing drawing must leave `warnings` empty and not add a line to every file."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact("specify")
    write_record(root, "a-decision", diagram="component", boundary=_FLOWCHART)

    assert _payload()["warnings"] == []


def test_with_no_trunk_past_specify_the_unchecked_line_is_a_warning(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same sentence #529 put before specify, from the same constant, so the
    two arms cannot drift. It travels as a reason here because only a reason
    reaches `warnings`, and past specify a reason holds nothing."""
    from wfctl._evidence import DRAWINGS_UNCHECKED

    _failing_record_with_no_trunk(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("specify")
    _git(storyctl_dir.repo_root, "add", "-A")
    _git(storyctl_dir.repo_root, "commit", "-m", "a decision")

    payload = _payload()

    assert _brainstorm(payload)["state"] == "done"
    assert [w["reason"] for w in payload["warnings"]] == [DRAWINGS_UNCHECKED]


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
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    assert runner.invoke(app, ["arch", "none", "--reason", "copy edit"]).exit_code == 0
    write_design_record(root)

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
    from wfctl._paths import arch_location
    from wfctl._pipeline import DESIGN_BLOCK_HELP

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
    write_design_record(root)

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
    write_design_record(root)

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
    write_design_record(root)

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
    write_design_record(root)

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
    write_design_record(root)

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
    there is no list of this branch's records to judge. Before specify the
    boundary question holds on that silence (#648), so the drawing check is
    reached past specify, where it runs as a warning. It has to find nothing
    there rather than warn about every record kept outside the repository."""
    root = tmp_path_factory.mktemp("outside") / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact("specify")
    write_record(root, "a-decision", diagram="component")

    step = _brainstorm()

    assert step["state"] == "done"
    assert _architecture_pass(step)["annotation"] is None
    assert _payload()["warnings"] == []


# --- A repository with no trunk (#508) ----------------------------------------
#
# The fixture's repo has no remote, so renaming its one branch to `trunk` leaves
# `trunk_branch` nothing to find. That is the issue's reproduction, and a test in
# which a trunk resolves has not exercised it.


def _architecture_pass(step: dict) -> dict:
    return next(s for s in step["sub_steps"] if s["name"] == "architecture")


def _failing_record_with_no_trunk(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> Path:
    root = _arch_root(storyctl_dir, monkeypatch)
    _git(storyctl_dir.repo_root, "branch", "-m", "trunk")
    storyctl_dir.make_spec_artifact("brainstorm")
    write_record(root, "a-decision", diagram="component")
    return root


def test_with_no_trunk_an_uncommitted_failing_record_still_holds_the_step(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without a trunk the listing holds only what `git status` reports, and an
    uncommitted record is in it. The gap is committed records alone, so the step
    that finishes on those must still hold on this one."""
    root = _failing_record_with_no_trunk(storyctl_dir, monkeypatch)

    step = _brainstorm()

    assert step["state"] == "in_progress"
    assert step["reason"] == f"a-decision: {_first_blocker(root, 'a-decision')}"


def test_with_no_trunk_a_committed_failing_record_finishes_the_step_and_says_so(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Once committed, the record is unseen: there is no base to diff against, so
    git can't say whether the branch answered the boundary question at all. The
    step used to finish here, first silently and then with a line saying the
    committed records went unchecked. Since #648 it holds on that silence and
    names the setting that settles it, so a repository with no trunk finds out
    before any record goes unjudged."""
    from wfctl._evidence import GIT_UNANSWERED_HELP, GIT_UNANSWERED_REASON

    _failing_record_with_no_trunk(storyctl_dir, monkeypatch)
    _git(storyctl_dir.repo_root, "add", "-A")
    _git(storyctl_dir.repo_root, "commit", "-m", "a decision")

    step = _brainstorm()

    assert step["state"] == "in_progress"
    assert step["reason"] == GIT_UNANSWERED_REASON
    assert step["remedy"] == GIT_UNANSWERED_HELP


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
    write_design_record(root)
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
    never asked about them, trunk or not. Past specify, since before it the
    boundary question holds on git's silence (#648)."""
    root = tmp_path_factory.mktemp("outside") / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    _git(storyctl_dir.repo_root, "branch", "-m", "trunk")
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact("specify")
    write_record(root, "a-decision", diagram="component")

    step = _brainstorm()

    assert step["state"] == "done"
    assert _architecture_pass(step)["annotation"] is None


# --- #649: `context_gap`, the one function every context reader calls --------

from tests.conftest import branch_design, write_domain_page  # noqa: E402
from wfctl import _contexts, _design_exceptions, _evidence  # noqa: E402
from wfctl._paths import arch_root  # noqa: E402


def _gap(storyctl_dir: types.SimpleNamespace, level: _contexts.Level = _contexts.ARCHITECTURE):
    repo = storyctl_dir.repo_root
    return _evidence.context_gap(repo, arch_root(repo), storyctl_dir.spec_dir, level)


def _listing(storyctl_dir: types.SimpleNamespace, root: Path, listed: str | None, known: str = "a, b, c") -> None:
    write_domain_page(root, known)
    storyctl_dir.make_spec_artifact("brainstorm", content=branch_design(listed))


def test_context_gap_is_none_when_every_listed_context_is_answered(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One record answers `a` and a per-context "no" answers `b`, so nothing is
    left to pause on."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _listing(storyctl_dir, root, "a, b")
    write_record(root, "a-decision", diagram="component", governs="a")
    _design_exceptions.write(storyctl_dir.spec_dir, "boundary", "Copy only", context="b")

    assert _gap(storyctl_dir) is None


def test_context_gap_names_the_first_context_a_record_about_another_one_leaves(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gap #649 describes: a record that governs `b` must not answer `a`."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _listing(storyctl_dir, root, "a")
    write_record(root, "a-decision", diagram="component", governs="b")

    gap = _gap(storyctl_dir)

    assert gap is not None
    assert gap.reason == "no architecture record governs a"
    assert not gap.git_silent
    assert "wfctl arch none --context a" in gap.remedy


def test_context_gap_reads_level_3_records_only_for_the_software_design_level(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Level 2 answers with a record in the arch root and level 3 with one under
    `design/`. A record at the wrong level answers nothing."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _listing(storyctl_dir, root, "a")
    write_record(root, "a-decision", diagram="component", governs="a")

    gap = _gap(storyctl_dir, _contexts.SOFTWARE_DESIGN)
    assert gap is not None and gap.reason == "no software design record governs a"

    write_design_record(root, governs="a")
    assert _gap(storyctl_dir, _contexts.SOFTWARE_DESIGN) is None


def test_context_gap_skips_a_record_the_branch_deleted(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A deleted record is listed by git and has no file, so it answers nothing."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _listing(storyctl_dir, root, "a")
    path = write_record(root, "a-decision", diagram="component", governs="a")
    _git(storyctl_dir.repo_root, "add", "-A")
    _git(storyctl_dir.repo_root, "commit", "-m", "record")
    path.unlink()

    gap = _gap(storyctl_dir)

    assert gap is not None and gap.reason == "no architecture record governs a"


def test_a_missing_contexts_line_is_reported_even_when_git_cannot_list_the_branch(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """git's silence only matters for a context nobody answered. A missing line
    pauses whatever git says (PR-012)."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _git(storyctl_dir.repo_root, "branch", "-m", "trunk")
    _listing(storyctl_dir, root, None)

    gap = _gap(storyctl_dir)

    assert gap is not None
    assert gap.reason == "design.md lists no contexts"
    assert not gap.git_silent


def test_an_unknown_name_is_reported_even_when_git_cannot_list_the_branch(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _arch_root(storyctl_dir, monkeypatch)
    _git(storyctl_dir.repo_root, "branch", "-m", "trunk")
    _listing(storyctl_dir, root, "sesion")

    gap = _gap(storyctl_dir)

    assert gap is not None
    assert gap.reason == "sesion is not a context on the domain page"
    assert not gap.git_silent


def test_with_no_trunk_an_earlier_commit_leaves_git_silent(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no trunk the listing holds only uncommitted work. A governing record
    committed earlier on the branch is invisible, so one uncommitted change must
    not make `a` read as unanswered (PR-012, item 2)."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _git(storyctl_dir.repo_root, "branch", "-m", "trunk")
    _listing(storyctl_dir, root, "a, b")
    write_record(root, "a-decision", diagram="component", governs="a")
    _git(storyctl_dir.repo_root, "add", "-A")
    _git(storyctl_dir.repo_root, "commit", "-m", "the record for a")
    write_record(root, "b-decision", diagram="component", governs="b")

    gap = _gap(storyctl_dir)

    assert gap is not None
    assert gap.git_silent
    held = _evidence.context_hold(gap)
    assert held is not None and held[0] == _evidence.GIT_UNANSWERED_REASON


def test_an_arch_root_outside_the_repository_leaves_git_silent(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("elsewhere") / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(outside))
    _listing(storyctl_dir, outside, "a")

    gap = _gap(storyctl_dir)

    assert gap is not None and gap.git_silent


# --- #649 User Story 1: a record about the wrong context does not pass --------


def _branch(
    storyctl_dir: types.SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    listed: str | None,
    known: str | None = "session-continuity, install-and-drift, attention",
    *,
    outside: str = "workmux",
) -> Path:
    """A branch in brainstorm: `design.md` listing `listed`, a domain page naming
    `known` (none when `known` is None), and a level-3 record so the software
    design pass has nothing to say."""
    root = _arch_root(storyctl_dir, monkeypatch)
    if known is not None:
        write_domain_page(root, known, outside=outside)
    storyctl_dir.make_spec_artifact("brainstorm", content=branch_design(listed))
    write_design_record(root)
    return root


def test_a_record_about_another_context_leaves_brainstorm_paused_on_the_listed_one(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gap #649 describes. The record governs install-and-drift, and the
    branch lists session-continuity, so the old check passed on any record."""
    root = _branch(storyctl_dir, monkeypatch, "session-continuity")
    write_record(root, "a-decision", diagram="component", boundary=_FLOWCHART,
                 governs="install-and-drift")

    step = _brainstorm()

    assert step["state"] == "in_progress"
    assert step["reason"] == "no architecture record governs session-continuity"


def test_the_pause_remedy_names_a_record_and_the_per_context_no(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _branch(storyctl_dir, monkeypatch, "session-continuity")
    write_record(root, "a-decision", diagram="component", boundary=_FLOWCHART,
                 governs="install-and-drift")

    remedy = _brainstorm()["remedy"]

    assert "governs field names session-continuity" in remedy
    assert 'wfctl arch none --context session-continuity --reason "<why>"' in remedy


def test_two_listed_contexts_with_a_record_for_only_the_second_name_the_first(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _branch(storyctl_dir, monkeypatch, "session-continuity, install-and-drift")
    write_record(root, "a-decision", diagram="component", boundary=_FLOWCHART,
                 governs="install-and-drift")

    assert _brainstorm()["reason"] == "no architecture record governs session-continuity"


# --- #649 User Story 3: a bad or missing line pauses --------------------------


def test_a_misspelled_context_is_named_with_the_list_as_the_remedy(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    _branch(storyctl_dir, monkeypatch, "session-continuty")

    step = _brainstorm()

    assert step["reason"] == "session-continuty is not a context on the domain page"
    assert "session-continuity" in step["remedy"]


@pytest.mark.parametrize("line", [None, ""], ids=["no line", "empty line"])
def test_a_missing_or_empty_contexts_line_pauses_brainstorm(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, line: str | None
) -> None:
    root = _branch(storyctl_dir, monkeypatch, line)
    write_record(root, "a-decision", diagram="component", boundary=_FLOWCHART,
                 governs="session-continuity")

    step = _brainstorm()

    assert step["reason"] == "design.md lists no contexts"
    assert "Contexts: <names from the domain page>" in step["remedy"]


def test_an_outside_party_is_a_valid_name(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """workmux is an outside party, not a context, and a record may govern it."""
    root = _branch(storyctl_dir, monkeypatch, "session-continuity, workmux")
    write_record(root, "a-decision", diagram="component", boundary=_FLOWCHART,
                 governs="session-continuity, workmux")

    assert _brainstorm()["state"] == "done"


# --- #649 User Story 4: a repo with no name list sees no change ----------------


def test_without_a_name_list_any_record_passes_whatever_it_governs(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _branch(storyctl_dir, monkeypatch, "session-continuity", known=None)
    write_record(root, "a-decision", diagram="component", boundary=_FLOWCHART,
                 governs="anything-at-all")

    assert _brainstorm()["state"] == "done"


def test_without_a_name_list_no_record_keeps_todays_reason(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    _branch(storyctl_dir, monkeypatch, None, known=None)

    assert _brainstorm()["reason"] == "no architecture record for this change"


def test_a_domain_page_that_is_not_accepted_is_ignored(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _arch_root(storyctl_dir, monkeypatch)
    write_domain_page(root, "session-continuity", state="proposed")
    storyctl_dir.make_spec_artifact("brainstorm", content=branch_design("session-continuity"))
    write_design_record(root)
    write_record(root, "a-decision", diagram="component", boundary=_FLOWCHART)

    assert _brainstorm()["state"] == "done"


def test_past_specify_the_context_check_does_not_pause(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-013. A branch that left brainstorm before the check existed must not
    move backwards, so `spec.md` ends the check as it ends the general one."""
    _branch(storyctl_dir, monkeypatch, "session-continuity")
    storyctl_dir.make_spec_artifact("specify")

    assert _brainstorm()["state"] == "done"
