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
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl import _arch
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


def _record(
    root: Path, slug: str, status: str = "proposed", *, diagram: str = "", boundary: str = ""
) -> Path:
    """A level-2 record with a `## Log`, so the only blockers are the drawing's."""
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{slug}.md"
    front = f"---\nstatus: {status}\n"
    if diagram:
        front += f"diagram: {diagram}\n"
    front += "---\n\n"
    path.write_text(f"{front}# {slug}\n\n{boundary}## Log\n\n- 2026-09-26  proposed  — x\n")
    return path


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
    return f"  wfctl arch accept {slug} --dry-run"


# The three drawings `accept` refuses, and the same record once fixed. Kwargs to
# `_record`, so each row is the whole difference between failing and passing.
_FAILING = {
    "no drawing": ({"diagram": "component"}, {"diagram": "component", "boundary": _FLOWCHART}),
    "no declared kind": ({"boundary": _FLOWCHART}, {"diagram": "component", "boundary": _FLOWCHART}),
    "no step that fails": (
        {"diagram": "sequence", "boundary": _HAPPY_SEQUENCE},
        {"diagram": "sequence", "boundary": _FAILING_SEQUENCE},
    ),
}


# --- User Story 1: brainstorm does not finish on a refusable drawing ---------


@pytest.mark.parametrize("case", sorted(_FAILING))
def test_a_proposed_record_acceptance_would_refuse_holds_the_design_step(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    """Each drawing `accept` refuses holds brainstorm, naming the record and the
    blocker. Before this, all three read `brainstorm ●` and the refusal arrived
    only when someone tried to accept, after implement had built against it."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    broken, _ = _FAILING[case]
    _record(root, "a-decision", **broken)

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
    _record(root, "a-decision", **broken)
    assert _brainstorm()["state"] == "in_progress"

    _record(root, "a-decision", **fixed)

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
    _record(root, "b-second", diagram="component")
    _record(root, "a-first", diagram="component")

    step = _brainstorm()

    assert step["reason"] == f"a-first: {_first_blocker(root, 'a-first')}"
    assert step["remedy"] == f"{_dry_run('a-first')}\n{_dry_run('b-second')}"


def test_rewording_a_blocker_changes_the_reason_and_not_the_fix(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The level-3 record's third verification item. The fix is built from the
    slug the pass holds, never parsed back out of the reason; parsing it couples
    the fix to wording `_arch` owns, and a rewording would break it with no test
    failing where the wording changed."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    _record(root, "a-decision", diagram="component")
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
    _record(root, "a-decision", diagram="component")

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
    _record(root, "a-decision", diagram="component")

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
    _record(root, "a-decision", diagram="component")

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
    _record(root, "a-decision", diagram="component")

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
    _record(root, "a-decision", "accepted", boundary=_FLOWCHART)

    assert _brainstorm()["state"] == "done"


def test_a_failing_record_marked_rejected_by_hand_releases_the_step(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rejecting a record is a ruling on it, and a rejected record is never
    accepted, so its drawing no longer matters to anyone."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    _record(root, "a-decision", diagram="component")
    assert _brainstorm()["state"] == "in_progress"

    _record(root, "a-decision", "rejected", diagram="component")

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
    _record(root / corner, "a-decision", diagram="component")

    assert _brainstorm()["state"] == "done"


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
    _record(root, "a-decision", diagram="component")

    assert _brainstorm()["state"] == "done"
