"""The step table agrees with the commands wfctl ships.

`_pipeline` maps each step to the slash command that advances it, and `wfctl next`
prints that command as the first thing a session reads. Nothing verified the
command existed until this file: a wrong name is indistinguishable from a right
one until someone runs it, which is how #23 went a week unnoticed.
"""
import types
from importlib.resources import files
from pathlib import Path

from typer.testing import CliRunner

from wfctl.cli import app
from wfctl._pipeline import (
    STORY_COMPLETE_CONSOLE,
    STORY_COMPLETE_FILE,
    _LOOSE_COMMANDS,
    _STEP_NAMES,
    _STEPS,
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
    ("implement",  "/speckit.implement",  False),
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
    """State advanced and `next-step.md` stayed stale, so the two disagreed
    about where the session was — after a command that reported failure."""
    import json

    _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("brainstorm")
    runner.invoke(app, ["start"])
    before = (storyctl_dir.agent_dir / "current.json").read_text()
    events_before = (storyctl_dir.agent_dir / "events.jsonl").read_text()

    assert runner.invoke(app, ["resume"]).exit_code == 1

    assert (storyctl_dir.agent_dir / "current.json").read_text() == before
    assert (storyctl_dir.agent_dir / "events.jsonl").read_text() == events_before
    assert json.loads(before)  # the state that survived is still readable
