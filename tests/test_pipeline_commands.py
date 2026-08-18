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
