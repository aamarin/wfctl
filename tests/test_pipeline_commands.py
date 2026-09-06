"""The step table agrees with the commands wfctl ships.

`_pipeline` maps each step to the slash command that advances it, and `wfctl next`
prints that command as the first thing a session reads. Nothing verified the
command existed until this file: a wrong name is indistinguishable from a right
one until someone runs it, which is how #23 went a week unnoticed.
"""
import json
import subprocess
import types
from importlib.resources import files
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import CLEAN_SPEC
from wfctl import _verify
from wfctl.cli import app
from wfctl._pipeline import (
    STORY_COMPLETE_CONSOLE,
    STORY_COMPLETE_FILE,
    _LOOSE_COMMANDS,
    _STEP_NAMES,
    _STEPS,
    _infer_steps,
    next_step_content,
)

runner = CliRunner()

# Resolved the way `_bundle` resolves it — `files("wfctl")`, not a second
# mechanism that agrees with it only by coincidence — but called here rather than
# read from `_bundle.BUNDLE_ROOT`, which conftest's autouse `bundle` fixture
# repoints at a temporary tree holding one fake command. Reading the real shipped
# tree is this file's whole purpose, so it is that fixture's one exception.
_COMMANDS = Path(str(files("wfctl"))) / "agents" / "commands"

# The pipeline as it must remain. Spelled out rather than derived from the table
# under test — an expectation that reads its subject proves only that the subject
# is self-consistent. Order is part of it: `_STEP_NAMES` is the sequence the
# pipeline advances through, so a reordered table reroutes the workflow.
_EXPECTED_STEPS = [
    ("brainstorm", "/speckit.brainstorm", False),
    ("specify",    "/speckit.specify",    True),
    ("clarify",    "/speckit.clarify",    False),
    ("plan",       "/speckit.plan",       True),
    ("tasks",      "/speckit.tasks",      True),
    ("analyze",    "/speckit.analyze",    False),
    ("decompose",  "/speckit.decompose",  False),
    ("implement",  "/speckit.implement",  True),
]


def _shipped() -> set[str]:
    return {p.stem for p in _COMMANDS.glob("*.md")}


def _shipped_with_plan_renamed() -> set[str]:
    """The #23 shape: a command file renamed out from under the table."""
    return (_shipped() - {"speckit.plan"}) | {"plan"}


def _named_commands() -> dict[str, str]:
    """Label → command, for every slash command wfctl emits.

    Not just the step table. `/end-session` is named only in `cli`'s completion
    messages, so a check that walked `_STEPS` alone would pass while the last
    instruction a session receives pointed at nothing.
    """
    named = {step: cmd for step, (cmd, _) in _STEPS.items()}
    named.update({f"story complete → {cmd}": cmd for cmd in _LOOSE_COMMANDS})
    return named


def _unresolved(shipped: set[str]) -> dict[str, str]:
    """Label → command, for every command absent from `shipped`.

    Takes the shipped names rather than globbing for them, so the failure cases
    below are ordinary values instead of filesystem states — no renaming tracked
    files and restoring them, which leaves the repo broken if a run is cut short.

    One-directional on purpose: shipped commands that nothing names are not
    drift. `speckit.checklist`, `speckit.brief` and `speckit.orchestrate` are
    commands the pipeline never advances to, and reporting them would be noise
    forever.
    """
    return {
        label: cmd
        for label, cmd in _named_commands().items()
        if cmd.removeprefix("/") not in shipped
    }


def _report(missing: dict[str, str], shipped: set[str]) -> str:
    """Both sides of the disagreement, so the reader can see which one moved.

    No candidate is nominated. Every command shares the `speckit.` prefix, which
    dominates similarity scoring and makes an automatic guess least reliable for
    exactly the prefix-added and prefix-dropped renames this file exists to
    catch. Showing both lists costs two lines and cannot be wrong.
    """
    return (
        f"commands wfctl names with no shipped file: {missing}\n"
        f"shipped commands: {sorted(shipped)}"
    )


def test_step_table_resolves_in_order() -> None:
    """Every step yields its command and auto flag, in pipeline order."""
    assert [(n, *next_step_content(n)) for n in _STEP_NAMES] == _EXPECTED_STEPS


def test_an_undefined_step_yields_an_empty_command() -> None:
    """`next_cmd` treats an empty command as a finished pipeline.

    So an unknown step must come back empty rather than raise: "complete" is not
    a table entry, and it is the value `_current_step_name` returns for a story
    with nothing left to do.
    """
    assert next_step_content("complete") == ("", False)
    assert next_step_content("no-such-step") == ("", False)


def test_every_step_command_ships_in_the_bundle() -> None:
    shipped = _shipped()
    missing = _unresolved(shipped)
    assert not missing, _report(missing, shipped)


def test_a_renamed_command_is_caught() -> None:
    assert _unresolved(_shipped_with_plan_renamed()) == {"plan": "/speckit.plan"}


def test_an_empty_command_set_fails_rather_than_passing_vacuously() -> None:
    """A bundle with no commands cannot satisfy the table.

    Guards the partial-install case, and the check itself: an implementation that
    silently produced an empty comparison would pass every other test here.
    """
    assert _unresolved(set()) == _named_commands()


def test_commands_no_step_names_are_not_reported() -> None:
    """Shipped commands outside the pipeline are not drift, in either direction."""
    shipped = _shipped()
    assert "speckit.checklist" in shipped, "precondition: a non-step command ships"
    assert not _unresolved(shipped)


def test_end_session_is_covered_by_the_drift_check() -> None:
    """`/end-session` is named by no step, so only the loose inventory reaches it."""
    assert _unresolved(_shipped() - {"end-session"}) == {
        "story complete → /end-session": "/end-session"
    }


def test_a_finished_pipeline_prints_the_checked_completion_messages(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`cli` emits the constants the drift check guards — not its own literals.

    Asserting the constants contain `/end-session` proves nothing on its own:
    `cli` could inline the literal again and every other test here would still
    pass, which is exactly the drift this file exists to catch. So drive the real
    command to a finished pipeline and compare its output against the constants.
    """
    for step in ("brainstorm", "plan", "analyze", "decompose"):
        storyctl_dir.make_spec_artifact(step)
    # A spec that reads as clarified: the section clarify writes, no open markers.
    storyctl_dir.make_spec_artifact("specify", "# Spec\n\n## Clarifications\n\nnone\n")
    storyctl_dir.make_spec_artifact("tasks", "- [x] T001 done\n")

    result = runner.invoke(app, ["next"])

    assert result.exit_code == 0
    assert STORY_COMPLETE_CONSOLE in result.output
    assert (storyctl_dir.agent_dir / "next-step.md").read_text() == STORY_COMPLETE_FILE


def test_the_failure_report_carries_both_sides() -> None:
    shipped = _shipped_with_plan_renamed()
    report = _report(_unresolved(shipped), shipped)
    assert "/speckit.plan" in report, "names the entry that failed to resolve"
    assert "'plan'" in report, "shows the new name, so a rename is visible as one"


# --- the design-step advance check --------------------------------------------
#
# `storyctl_dir` is a real git repo, which this check needs: "was the arch root
# touched by this change?" is a git question, and the answer is what separates a
# record written for this feature from one written last year.


def _arch_root(storyctl_dir: types.SimpleNamespace, monkeypatch) -> Path:
    root = storyctl_dir.repo_root / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    return root


def test_advancing_past_design_needs_an_answer(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """The gate: a design step that drew a boundary and recorded nothing.

    0 of 11 designs carried the Boundaries and Ownership section the skill
    mandates, which is the evidence this check exists on — the question was not
    refused, it went unanswered.
    """
    _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")

    result = runner.invoke(app, ["next"])

    assert result.exit_code == 1
    assert "no architecture record for this change" in result.output
    assert "wfctl arch none --reason" in result.output
    assert "docs/architecture" in result.output


def test_a_record_written_for_this_change_advances(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """A record in the working tree is the answer, whatever its status — a
    proposed record still means the question was put."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    root.mkdir(parents=True)
    (root / "layer-model.md").write_text("---\nstatus: proposed\n---\n\n# x\n")

    result = runner.invoke(app, ["next"])

    assert result.exit_code == 0
    assert "Next step:" in result.output


def test_a_level_3_record_alone_does_not_answer_the_boundary_question(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """`design/` sits under the arch root, and "was the root touched?" is a
    recursive question in git. So a feature that moves a boundary and writes
    only a level-3 record — which governs one feature and is barred from drawing
    a boundary at all — would satisfy a gate asking who owns the truth. #121
    item 3 makes every such record land in the branch diff, so without this the
    gate would be permanently answered for any feature that writes one."""
    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    (root / "design").mkdir(parents=True)
    (root / "design" / "122-a-choice.md").write_text("---\nstatus: proposed\n---\n\n# x\n")

    result = runner.invoke(app, ["next"])

    assert result.exit_code == 1
    assert "no architecture record for this change" in result.output


def test_a_declaration_advances(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """`arch none` is the whole escape hatch. Without it the check has no
    answer for a change that genuinely draws no boundary, and the only way past
    would be to write a record that says nothing."""
    _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")

    declared = runner.invoke(app, ["arch", "none", "--reason", "copy edit, no new state"])
    assert declared.exit_code == 0
    assert "no boundary changed" in declared.output

    assert runner.invoke(app, ["next"]).exit_code == 0


def test_the_declaration_lands_in_the_change_not_in_state(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """FR-010a. wfctl cannot verify the claim — whether a change draws a
    boundary is a judgment with no objective test — so the only thing that
    makes it honest is a reviewer seeing it. In the state dir nobody would.
    """
    import subprocess

    root = _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")

    runner.invoke(app, ["arch", "none", "--reason", "copy edit, no new state"])

    tracked = subprocess.run(
        # -uall: the default collapses an untracked tree to `?? docs/`, which
        # would pass this assertion without the declaration ever being written.
        ["git", "-C", str(storyctl_dir.repo_root), "status", "--porcelain", "-uall"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "docs/architecture/declarations/" in tracked

    written = list((root / "declarations").glob("*.md"))
    assert len(written) == 1
    assert "copy edit, no new state" in written[0].read_text()


def test_a_feature_with_no_design_step_is_not_gated(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """Not every change needs a design. `design-levels` excludes bug fixes and
    copy edits, and a pipeline that never reached design has nothing to advance
    past — gating it would demand a record for work no boundary question was
    ever asked about."""
    _arch_root(storyctl_dir, monkeypatch)

    assert runner.invoke(app, ["next"]).exit_code == 0


def test_the_gate_is_one_transition_not_the_rest_of_the_pipeline(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """Held up through plan and tasks, the gate refuses work that already
    answered by moving on — and there is no `arch none` for a feature that is
    three steps past the question. Eight existing `next` tests failed on the
    wide version, which is the blast radius in miniature."""
    _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact("specify", "# Spec\n\n## Clarifications\n\nnone\n")

    result = runner.invoke(app, ["next"])

    assert result.exit_code == 0
    assert "/speckit.plan" in result.output


def test_resume_is_gated_too(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """`speckit-orchestrate` advances the pipeline with `wfctl resume`, not
    `wfctl next` — so a gate wired only into `next` is walked past by the one
    path that actually runs. Both write `next-step.md`; both are the advance."""
    _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    runner.invoke(app, ["start"])

    result = runner.invoke(app, ["resume"])

    assert result.exit_code == 1
    assert "no architecture record for this change" in result.output

    runner.invoke(app, ["arch", "none", "--reason", "no new state"])
    assert runner.invoke(app, ["resume"]).exit_code == 0


def test_resume_reports_the_auto_flag_of_the_step_it_resumed_to(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """`resume` re-sourced `auto` from the report; nothing covered its output.

    Every `auto: true/false` assertion in the suite targeted `wfctl next`, so
    `resume` could have written the wrong flag — or stopped writing one — with
    the suite green. Both values, because a flag hardcoded either way passes a
    test that only checks the other.
    """
    _arch_root(storyctl_dir, monkeypatch)
    runner.invoke(app, ["start"])

    stops = runner.invoke(app, ["resume"])

    assert "step: brainstorm" in stops.output
    assert "auto: false" in stops.output

    storyctl_dir.make_spec_artifact("brainstorm")
    runner.invoke(app, ["arch", "none", "--reason", "no new state"])

    advances = runner.invoke(app, ["resume"])

    assert "/speckit.specify" in advances.output
    assert "auto: true" in advances.output
    assert "auto: true" in (storyctl_dir.agent_dir / "next-step.md").read_text()


def test_a_declaration_git_will_not_carry_is_refused(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """The deadlock: a gitignored arch root made `arch none` print ✓ while
    writing a file git never reports, so the gate refused forever and the
    escape hatch it names had no effect. Both silent failures — ignored, and
    out-of-tree — are the same question: did the claim reach the reviewer?"""
    import subprocess

    _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    (storyctl_dir.repo_root / ".gitignore").write_text("docs/\n")
    subprocess.run(["git", "-C", str(storyctl_dir.repo_root), "add", ".gitignore"],
                   check=True, capture_output=True)

    result = runner.invoke(app, ["arch", "none", "--reason", "copy edit"])

    assert result.exit_code == 1
    assert "not part of the change under" in result.output
    assert "✓" not in result.output


def test_an_out_of_tree_declaration_is_refused(
    storyctl_dir: types.SimpleNamespace, monkeypatch, tmp_path_factory
) -> None:
    """FR-002a allows an out-of-tree root, so this configuration is supported —
    but a declaration written there never appears in the change, and the gate
    is inert. Reporting success would be a lie in a state the spec permits."""
    outside = tmp_path_factory.mktemp("outside-the-repo")
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(outside))
    storyctl_dir.make_spec_artifact("brainstorm")

    result = runner.invoke(app, ["arch", "none", "--reason", "copy edit"])

    assert result.exit_code == 1
    assert "not part of the change under" in result.output


def test_an_empty_reason_is_refused(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """An empty claim is the silent omission the check exists to stop, with an
    extra command in front of it."""
    _arch_root(storyctl_dir, monkeypatch)
    assert runner.invoke(app, ["arch", "none", "--reason", "   "]).exit_code == 1


def test_a_bracketed_root_reaches_the_reader(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """`[wip]` is a legal directory name that rich reads as a style tag: the
    refusal named `docs//architecture/`, a path that does not exist, and
    `[/y]` raised MarkupError so the message never printed at all."""
    root = storyctl_dir.repo_root / "docs" / "[wip]" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    storyctl_dir.make_spec_artifact("brainstorm")

    result = runner.invoke(app, ["next"])

    assert result.exit_code == 1
    assert "docs/[wip]/architecture/<slug>.md" in result.output


def test_a_refused_resume_does_not_advance_state(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """The event log advanced and `next-step.md` stayed stale, so the two
    disagreed about where the session was — after a command that reported
    failure.

    The log is the whole assertion now that the resume point is derived: nothing
    else is written, so an event appended past the refusal is the only way the
    session can claim to have moved."""
    _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    runner.invoke(app, ["start"])
    events_before = (storyctl_dir.agent_dir / "events.jsonl").read_text()

    assert runner.invoke(app, ["resume"]).exit_code == 1

    assert (storyctl_dir.agent_dir / "events.jsonl").read_text() == events_before


# --- the implement arm, once a definition of done exists (#69) ----------------
#
# Before #69 `implement` read complete from two artifacts the implementing agent
# writes: a sentinel file, or every checkbox ticked. These assert that a
# configured definition of done gets the last word over both.


def _implement_state(spec_dir: Path, repo_root: Path) -> tuple[str, str]:
    """Return (state, annotation) for the implement step."""
    step = next(s for s in _infer_steps(spec_dir, repo_root) if s.name == "implement")
    return step.state, step.annotation or ""


def _commit_all(root: Path, message: str = "c") -> None:
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-m", message], check=True, capture_output=True
    )


@pytest.fixture
def gated(storyctl_dir: types.SimpleNamespace) -> types.SimpleNamespace:
    """A story whose tasks are all complete, in a repo with a definition of done.

    Every test below starts from the state that used to read `●` unconditionally.
    """
    storyctl_dir.stage_upstream_of("tasks", tasks="- [x] T001 done\n- [x] T002 done\n")
    ok = storyctl_dir.repo_root / "ok.py"
    ok.write_text("pass\n")
    storyctl_dir.command = ["python3", str(ok)]
    (storyctl_dir.repo_root / _verify.CONFIG_PATH).write_text(
        json.dumps({"verify": [storyctl_dir.command]})
    )
    _commit_all(storyctl_dir.repo_root, "definition of done")
    return storyctl_dir


def _record(d: types.SimpleNamespace, **over: object) -> dict:
    sha, dirty = _verify.code_identity(d.repo_root)
    rec = {
        "command": [d.command], "exit": 0, "failed": [],
        "sha": sha, "dirty": dirty, "inconclusive": False,
        "at": "2026-08-25T00:00:00Z",
    }
    rec.update(over)
    return rec


def test_no_definition_of_done_leaves_the_old_behaviour_untouched(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """SC-001. A repository that never adopts this sees no change at all."""
    storyctl_dir.stage_upstream_of("tasks")
    assert _implement_state(storyctl_dir.spec_dir, storyctl_dir.repo_root)[0] == "done"


def test_a_sentinel_alone_no_longer_reports_complete(
    gated: types.SimpleNamespace,
) -> None:
    """FR-005, and the defect in #69's title.

    The sentinel is written by the agent that did the work. With a definition of
    done configured it stops being sufficient on its own.
    """
    (gated.spec_dir / "checklists").mkdir(exist_ok=True)
    (gated.spec_dir / "checklists" / "implement-complete.md").write_text("done\n")
    state, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert state == "in_progress"
    assert "unverified" in annotation


def test_never_verified_reports_unverified(gated: types.SimpleNamespace) -> None:
    state, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert state == "in_progress"
    assert "run `wfctl verify`" in annotation


def test_a_passing_current_record_reports_complete(gated: types.SimpleNamespace) -> None:
    _verify.write_record(gated.agent_dir, _record(gated))
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "done"


def test_a_failed_run_names_the_failing_commands(gated: types.SimpleNamespace) -> None:
    """SC-006: which command failed, from `status` alone, without opening a file."""
    _verify.write_record(
        gated.agent_dir, _record(gated, exit=1, failed=[["uv", "run", "mypy", "wfctl/"]])
    )
    state, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert state == "in_progress"
    assert "failed" in annotation and "uv run mypy wfctl/" in annotation


def test_an_inconclusive_run_asks_for_a_rerun(gated: types.SimpleNamespace) -> None:
    _verify.write_record(gated.agent_dir, _record(gated, inconclusive=True))
    state, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert state == "in_progress" and "inconclusive" in annotation


def test_a_passing_record_with_open_checkboxes_stays_in_progress(
    gated: types.SimpleNamespace,
) -> None:
    """Verification is an additional condition, never a replacement.

    A green definition of done says the code is sound, not that the work is
    finished.
    """
    gated.make_spec_artifact("tasks", "- [x] T001 done\n- [ ] T002 not done\n")
    _verify.write_record(gated.agent_dir, _record(gated))
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "in_progress"


def test_a_record_with_no_tasks_file_still_reports_not_started(
    gated: types.SimpleNamespace,
) -> None:
    """A verdict about nothing does not begin the step."""
    (gated.spec_dir / "tasks.md").unlink()
    _verify.write_record(gated.agent_dir, _record(gated))
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "pending"


def test_status_never_runs_the_definition_of_done(gated: types.SimpleNamespace) -> None:
    """FR-009 and SC-002. Inferring the step must stay cheap enough for every
    session start; shelling out to a test suite there is not acceptable."""
    marker = gated.repo_root / "ran.txt"
    prog = gated.repo_root / "sentinel.py"
    prog.write_text(f"open({str(marker)!r}, 'w').write('1')\n")
    (gated.repo_root / _verify.CONFIG_PATH).write_text(
        json.dumps({"verify": [["python3", str(prog)]]})
    )
    _infer_steps(gated.spec_dir, gated.repo_root)
    assert not marker.exists()


def test_a_blocked_implement_routes_to_verification(gated: types.SimpleNamespace) -> None:
    """FR-008. Sending the user back to `/speckit.implement` here is advice that
    cannot work: every task is already ticked, so there is nothing to implement."""
    result = runner.invoke(app, ["next"])
    assert result.exit_code == 0
    assert "wfctl verify" in result.output
    assert (gated.agent_dir / "next-step.md").read_text().startswith("Next step: wfctl verify")


def test_a_blocked_implement_does_not_advance_unattended(
    gated: types.SimpleNamespace,
) -> None:
    """#148. `implement` advances without a prompt, so the halt is now carried by
    one `False` — the one `next_step_content` returns alongside `wfctl verify`.

    Before the flip both branches said `auto: false` and the route above was the
    only thing this state proved. Orchestration reads the flag, not the command:
    a `true` here would emit `EXECUTE_COMMAND` for a story whose definition of
    done has not passed.
    """
    runner.invoke(app, ["next"])
    assert "auto: false" in (gated.agent_dir / "next-step.md").read_text()


def test_open_tasks_still_route_to_the_step_command(gated: types.SimpleNamespace) -> None:
    """The work itself is what remains, so the step command is right.

    #148 added the flag assertion. Routing and advancing are two answers here,
    and the command alone pinned only the first: a `next_step_content` that
    returned the step command with a hardcoded `False` — implement never
    advancing unattended, the whole point of the flip undone — passed all 863
    tests. `test_step_table_resolves_in_order` does not reach this, because it
    calls `next_step_content` without a repo or a spec dir and so never enters
    the implement branch at all.
    """
    gated.make_spec_artifact("tasks", "- [ ] T001 not done\n")
    result = runner.invoke(app, ["next"])
    assert "/speckit.implement" in result.output
    assert "auto: true" in (gated.agent_dir / "next-step.md").read_text()


def test_the_sentinel_closes_the_tasks_even_with_a_box_left_open(
    gated: types.SimpleNamespace,
) -> None:
    """#262. `speckit-implement` writes the sentinel when it reaches step 9b,
    precisely for the story whose boxes were never a reliable signal — tasks
    executed outside the skill. So the sentinel beside an open box is the
    ordinary state, not a corrupt one.

    `_infer_steps` reads both routes and reports `in_progress`; the routing path
    read only the boxes, saw work left, and returned `auto: true` for a story
    whose definition of done has not passed. `state` is what the two disagreed
    about, so an assertion on it passes against the defect — the flag is the
    whole test.
    """
    gated.make_spec_artifact("tasks", "- [x] T001 done\n- [ ] T002 open\n")
    (gated.spec_dir / "checklists" / "implement-complete.md").write_text("done\n")
    result = runner.invoke(app, ["next"])
    assert "wfctl verify" in result.output
    assert "auto: false" in (gated.agent_dir / "next-step.md").read_text()


def test_a_verified_story_reports_complete_rather_than_a_next_step(
    gated: types.SimpleNamespace,
) -> None:
    _verify.write_record(gated.agent_dir, _record(gated))
    result = runner.invoke(app, ["next"])
    assert STORY_COMPLETE_CONSOLE in result.output


# --- US2: a stale pass is not a pass -----------------------------------------

def test_a_moved_commit_makes_a_passing_record_stale(gated: types.SimpleNamespace) -> None:
    _verify.write_record(gated.agent_dir, _record(gated))
    (gated.repo_root / "later.py").write_text("pass\n")
    _commit_all(gated.repo_root, "later")
    state, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert state == "in_progress"
    assert "stale" in annotation and "HEAD is" in annotation


def test_an_uncommitted_edit_makes_a_passing_record_stale(
    gated: types.SimpleNamespace,
) -> None:
    """The commit did not move, and the code did.

    A sha-only record still matches here, which is why identity carries the tree
    state too — this is the row an agent spends most of its life in.
    """
    _verify.write_record(gated.agent_dir, _record(gated))
    (gated.repo_root / "ok.py").write_text("raise SystemExit(1)\n")
    state, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert state == "in_progress"
    assert "uncommitted changes" in annotation


def test_an_untracked_file_makes_a_passing_record_stale(
    gated: types.SimpleNamespace,
) -> None:
    """A new source file is untracked until it is added, so excluding untracked
    files would let never-verified code sit inside a green verdict."""
    _verify.write_record(gated.agent_dir, _record(gated))
    (gated.repo_root / "brand_new.py").write_text("def f(): ...\n")
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "in_progress"


def test_changing_the_definition_of_done_makes_a_passing_record_stale(
    gated: types.SimpleNamespace,
) -> None:
    """A pass under the old definition is not a pass under the new one.

    The record stores the commands it ran, not just the verdict, so this is
    detectable without re-running anything.
    """
    _verify.write_record(gated.agent_dir, _record(gated))
    (gated.repo_root / _verify.CONFIG_PATH).write_text(
        json.dumps({"verify": [gated.command, ["python3", "-c", "pass"]]})
    )
    _commit_all(gated.repo_root, "stricter definition")
    state, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert state == "in_progress"
    assert "definition of done changed" in annotation


def test_a_reordered_definition_of_done_is_a_different_definition(
    gated: types.SimpleNamespace,
) -> None:
    """Comparison is exact, order included.

    Reordering does not change what gets checked, but a permissive comparison
    would have to justify each permission it grants — and every one of those is a
    way for a record to outlive the thing it described.
    """
    second = ["python3", "-c", "pass"]
    (gated.repo_root / _verify.CONFIG_PATH).write_text(
        json.dumps({"verify": [gated.command, second]})
    )
    _commit_all(gated.repo_root, "two commands")
    _verify.write_record(gated.agent_dir, _record(gated, command=[gated.command, second]))
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "done"

    (gated.repo_root / _verify.CONFIG_PATH).write_text(
        json.dumps({"verify": [second, gated.command]})
    )
    _commit_all(gated.repo_root, "same two, swapped")
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "in_progress"


def test_a_failure_on_a_moved_commit_reports_the_failure_not_the_staleness(
    gated: types.SimpleNamespace,
) -> None:
    """Branch order, pinned deliberately rather than left to the implementation.

    Both conditions hold. The user can act on the failure; the staleness is only
    reachable after fixing it, so naming staleness first would send them to
    re-run a definition of done that is going to fail again.
    """
    _verify.write_record(gated.agent_dir, _record(gated, exit=1, failed=[gated.command]))
    (gated.repo_root / "later.py").write_text("pass\n")
    _commit_all(gated.repo_root, "later")
    state, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert state == "in_progress"
    assert annotation.count("failed") and "HEAD is" not in annotation


def test_a_fresh_checkout_of_a_verified_branch_reports_unverified(
    gated: types.SimpleNamespace, tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SC-005. The record is per-checkout and never committed, so a clone has none.

    That reads as 'nothing has been verified here', which is true: no definition
    of done has run on this machine against this tree.
    """
    _verify.write_record(gated.agent_dir, _record(gated))
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "done"

    clone = tmp_path_factory.mktemp("clone") / "wfctl"
    subprocess.run(
        ["git", "clone", "-q", str(gated.repo_root), str(clone)],
        check=True, capture_output=True,
    )
    fresh_state = clone / ".agent-runs"
    fresh_state.mkdir()
    monkeypatch.setenv("WFCTL_STATE_DIR", str(fresh_state))
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(clone))

    state, annotation = _implement_state(gated.spec_dir, clone)
    assert state == "in_progress" and "unverified" in annotation


# --- US3: projects without a definition of done are untouched ----------------

@pytest.mark.parametrize(
    "tasks, expected",
    [
        ("", "pending"),
        ("- [ ] T001 not done\n", "in_progress"),
        ("- [x] T001 done\n", "done"),
        ("- [x] T001 done\n- [ ] T002 not done\n", "in_progress"),
    ],
    ids=["no-tasks", "open-boxes", "all-ticked", "partly-ticked"],
)
def test_every_implement_state_is_unchanged_without_a_definition_of_done(
    storyctl_dir: types.SimpleNamespace, tasks: str, expected: str
) -> None:
    """SC-001. The degrade path, asserted across the whole arm rather than once.

    A repository that never adopts this must see the release it had before. One
    spot check would not catch a branch that changed only for, say, the sentinel
    route.
    """
    storyctl_dir.stage_upstream_of("tasks", tasks=tasks or "- [ ] x\n")
    if not tasks:
        (storyctl_dir.spec_dir / "tasks.md").unlink()
    else:
        (storyctl_dir.spec_dir / "tasks.md").write_text(tasks)
    assert not (storyctl_dir.repo_root / _verify.CONFIG_PATH).exists()
    assert _implement_state(storyctl_dir.spec_dir, storyctl_dir.repo_root)[0] == expected


def test_the_sentinel_route_still_works_without_a_definition_of_done(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The sentinel keeps its existing job: tasks run outside the skill.

    Verification is an AND on top, so removing this route would break every
    project that has not adopted the feature.
    """
    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 not done\n")
    (storyctl_dir.spec_dir / "checklists").mkdir(exist_ok=True)
    (storyctl_dir.spec_dir / "checklists" / "implement-complete.md").write_text("done\n")
    assert _implement_state(storyctl_dir.spec_dir, storyctl_dir.repo_root)[0] == "done"


def test_an_empty_verify_list_is_the_same_as_no_file(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Three spellings of 'not adopted' must be indistinguishable."""
    storyctl_dir.stage_upstream_of("tasks")
    for payload in ("{}", '{"verify": []}', '{"other": 1}'):
        (storyctl_dir.repo_root / _verify.CONFIG_PATH).write_text(payload)
        assert _implement_state(storyctl_dir.spec_dir, storyctl_dir.repo_root)[0] == "done"


def test_a_malformed_definition_of_done_blocks_rather_than_degrades(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The one case that must NOT degrade quietly.

    Silent degradation on a broken config is indistinguishable from the defect
    this feature removes: the step would read complete because the checker never
    ran.
    """
    storyctl_dir.stage_upstream_of("tasks")
    (storyctl_dir.repo_root / _verify.CONFIG_PATH).write_text('{"verify": ["pytest -q"]}')
    state, annotation = _implement_state(storyctl_dir.spec_dir, storyctl_dir.repo_root)
    assert state == "in_progress" and "malformed" in annotation


# --- what the four states draw (#74) ------------------------------------------
#
# `_infer_steps` carries names now; `cli._STATE_GLYPH` is the only place one
# becomes a symbol. These pin the rendered line for each state, so the encoding
# change is provably invisible to a human reading `wfctl status`.


def _status_lines(storyctl_dir: types.SimpleNamespace) -> list[str]:
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0, result.output
    return result.output.splitlines()


def test_each_state_draws_the_symbol_it_drew_before_it_had_a_name(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Three of the four states in one render, asserted as literal lines.

    A spec with no design and no plan: brainstorm was passed by, specify and
    clarify are behind, plan is where the reader is sent. Byte-identical to the
    output before the state names existed — the renderer is the only thing that
    knows a glyph, and it knows the same ones.
    """
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)

    lines = _status_lines(storyctl_dir)
    assert "brainstorm   –" in lines          # skipped
    assert "specify      ●" in lines          # done
    assert "plan         ○  ← current" in lines  # pending, and the cursor
    assert "tasks        ○" in lines


def test_in_progress_draws_the_cursor_glyph(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The fourth state, which needs a spec that clarify has not finished with.

    Separate from the test above because no single feature directory reaches all
    four: `in_progress` is what a step in flight reads, and every step before it
    has to be behind the reader for it to be the one drawn.
    """
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact(
        "specify", content="# Spec\n\n[NEEDS CLARIFICATION: which?]\n"
    )

    lines = _status_lines(storyctl_dir)
    assert "brainstorm   ●" in lines
    assert "clarify      ▶  ← current" in lines


def test_the_json_view_and_the_console_view_agree(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Asserting the two agree is the point of the flag, not a side check.

    A fact added to one branch and not the other is the drift `--json` exists to
    prevent: an agent reading the machine view and a human reading the block
    would be told different things about the same feature directory.
    """
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    storyctl_dir.make_spec_artifact("plan")
    storyctl_dir.make_spec_artifact("tasks", content="- [ ] T001 open\n")

    result = runner.invoke(app, ["status", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    console = _status_lines(storyctl_dir)

    glyphs = {"done": "●", "in_progress": "▶", "pending": "○", "skipped": "–"}
    for step in payload["steps"]:
        expected = f"{step['name'].ljust(12)} {glyphs[step['state']]}"
        if step["annotation"]:
            expected += f"  {step['annotation']}"
        if step["is_current"]:
            expected += "  ← current"
        assert expected in console

    assert f"next: {payload['next_command']}" in console
    assert payload["current"] == "analyze"
    assert payload["branch"] == "418-storyctl"
    assert payload["issue"] == "418"
    assert payload["session_started"] is False


def test_no_glyph_reaches_the_json_view(storyctl_dir: types.SimpleNamespace) -> None:
    """At any depth, not just on `state` — an annotation carrying one is the same defect."""
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)

    result = runner.invoke(app, ["status", "--json"])

    assert not set(result.output) & set("●▶○–")


# --- the six states from design.md, as literal rendered lines ------------------
#
# Every one of these was captured from the real command before the change, and
# four of the six were wrong. Asserting the literal line rather than a substring
# is the point: the defects were in what the line *said*, not in whether it
# appeared.


def test_state_1_nothing_exists_yet(storyctl_dir: types.SimpleNamespace) -> None:
    """No spec dir at all. Brainstorm is where a new feature starts."""
    import shutil
    shutil.rmtree(str(storyctl_dir.spec_dir))

    lines = _status_lines(storyctl_dir)

    assert "(no spec dir found)" in lines
    assert "brainstorm   ○  ← current" in lines
    assert "next: /speckit.brainstorm" in lines


def test_state_2_an_empty_spec_dir_renders_the_same_as_no_spec_dir(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """States 1 and 2 are the same situation and used to get opposite advice.

    An empty directory read `brainstorm –`, which routed past design to specify.
    Whether a directory happens to exist is not a fact about the feature.
    """
    lines = _status_lines(storyctl_dir)

    assert "brainstorm   ○  ← current" in lines
    assert "specify      ○" in lines
    assert "next: /speckit.brainstorm" in lines


def test_state_3_a_marked_spec_routes_to_clarify(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Markers are clarify's job, so specify is not where the reader is sent back to."""
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact(
        "specify", content="# Spec\n\n[NEEDS CLARIFICATION: which?]\n"
    )

    lines = _status_lines(storyctl_dir)

    assert "specify      ▶" in lines
    assert "clarify      ▶  ← current" in lines
    assert "next: /speckit.clarify" in lines


def test_state_4_a_spec_that_predates_the_gate_shows_clarify_skipped(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Planning already passed through where clarify now sits.

    True for a human who has read `_pipeline.py`; the drawing was false for an
    agent, because `–` and `●` are both "does not block" and nothing recovers
    which one it has. `--json` is where that difference now survives.
    """
    storyctl_dir.make_spec_artifact("brainstorm")
    storyctl_dir.make_spec_artifact("specify", content="# Spec\n\nNo markers.\n")
    storyctl_dir.make_spec_artifact("plan")

    lines = _status_lines(storyctl_dir)

    assert "specify      ●" in lines
    assert "clarify      –" in lines
    assert "plan         ●" in lines

    payload = json.loads(runner.invoke(app, ["status", "--json"]).output)
    states = {s["name"]: s["state"] for s in payload["steps"]}
    assert states["clarify"] == "skipped"
    assert states["specify"] == "done"


def test_state_5_implementing_but_unverified(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Two observed facts, neither concluded — the state the others should look like."""
    storyctl_dir.stage_upstream_of("tasks", tasks="- [x] T001 done\n")
    (storyctl_dir.repo_root / _verify.CONFIG_PATH).write_text(
        json.dumps({"verify": [["true"]]})
    )

    lines = _status_lines(storyctl_dir)

    assert "implement    ▶  1/1 done  unverified — run `wfctl verify`  ← current" in lines
    assert "next: wfctl verify" in lines


def test_state_6_a_finished_story_says_so(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The terminal state used to render as an absence: no cursor, no line.

    The sentence existed only in `resume`, so the one command an agent asks for
    position told it nothing at the moment there was nothing left to do.
    """
    storyctl_dir.stage_upstream_of("tasks", tasks="- [x] T001 done\n")
    storyctl_dir.make_spec_artifact("decompose")

    lines = _status_lines(storyctl_dir)

    assert "implement    ●  1/1 done" in lines
    assert not any("← current" in line for line in lines)
    assert f"next: {STORY_COMPLETE_CONSOLE}" in lines


@pytest.mark.parametrize("command", ["next", "resume"])
def test_the_file_an_agent_reads_names_the_command_status_prints(
    storyctl_dir: types.SimpleNamespace, command: str
) -> None:
    """`next-step.md` and the `next:` line are two views of one payload.

    They diverged in the state that matters most: tasks all ticked and the
    definition of done not passed. `status` routed to `wfctl verify`, and
    `resume` sent the session back to `/speckit.implement`, where there was no
    task left to do — so the agent ran the step again, changed nothing, and was
    told the same thing next time.
    """
    storyctl_dir.stage_upstream_of("tasks", tasks="- [x] T001 done\n")
    (storyctl_dir.repo_root / _verify.CONFIG_PATH).write_text(
        json.dumps({"verify": [["true"]]})
    )
    runner.invoke(app, ["start"])

    runner.invoke(app, [command])
    written = (storyctl_dir.agent_dir / "next-step.md").read_text()

    assert "Next step: wfctl verify" in written
    assert "next: wfctl verify" in runner.invoke(app, ["status"]).output
