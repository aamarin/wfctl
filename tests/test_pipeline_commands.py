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


# --- the implement arm, once a definition of done exists (#69) ----------------
#
# Before #69 `implement` read complete from two artifacts the implementing agent
# writes: a sentinel file, or every checkbox ticked. These assert that a
# configured definition of done gets the last word over both.


def _implement_state(spec_dir: Path, repo_root: Path) -> tuple[str, str]:
    """Return (symbol, annotation) for the implement step."""
    step = next(s for s in _infer_steps(spec_dir, repo_root) if s.name == "implement")
    return step.symbol, step.annotation or ""


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
    assert _implement_state(storyctl_dir.spec_dir, storyctl_dir.repo_root)[0] == "●"


def test_a_sentinel_alone_no_longer_reports_complete(
    gated: types.SimpleNamespace,
) -> None:
    """FR-005, and the defect in #69's title.

    The sentinel is written by the agent that did the work. With a definition of
    done configured it stops being sufficient on its own.
    """
    (gated.spec_dir / "checklists").mkdir(exist_ok=True)
    (gated.spec_dir / "checklists" / "implement-complete.md").write_text("done\n")
    symbol, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert symbol == "▶"
    assert "unverified" in annotation


def test_never_verified_reports_unverified(gated: types.SimpleNamespace) -> None:
    symbol, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert symbol == "▶"
    assert "run `wfctl verify`" in annotation


def test_a_passing_current_record_reports_complete(gated: types.SimpleNamespace) -> None:
    _verify.write_record(gated.agent_dir, _record(gated))
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "●"


def test_a_failed_run_names_the_failing_commands(gated: types.SimpleNamespace) -> None:
    """SC-006: which command failed, from `status` alone, without opening a file."""
    _verify.write_record(
        gated.agent_dir, _record(gated, exit=1, failed=[["uv", "run", "mypy", "wfctl/"]])
    )
    symbol, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert symbol == "▶"
    assert "failed" in annotation and "uv run mypy wfctl/" in annotation


def test_an_inconclusive_run_asks_for_a_rerun(gated: types.SimpleNamespace) -> None:
    _verify.write_record(gated.agent_dir, _record(gated, inconclusive=True))
    symbol, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert symbol == "▶" and "inconclusive" in annotation


def test_a_passing_record_with_open_checkboxes_stays_in_progress(
    gated: types.SimpleNamespace,
) -> None:
    """Verification is an additional condition, never a replacement.

    A green definition of done says the code is sound, not that the work is
    finished.
    """
    gated.make_spec_artifact("tasks", "- [x] T001 done\n- [ ] T002 not done\n")
    _verify.write_record(gated.agent_dir, _record(gated))
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "▶"


def test_a_record_with_no_tasks_file_still_reports_not_started(
    gated: types.SimpleNamespace,
) -> None:
    """A verdict about nothing does not begin the step."""
    (gated.spec_dir / "tasks.md").unlink()
    _verify.write_record(gated.agent_dir, _record(gated))
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "○"


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


def test_open_tasks_still_route_to_the_step_command(gated: types.SimpleNamespace) -> None:
    """The work itself is what remains, so the step command is right."""
    gated.make_spec_artifact("tasks", "- [ ] T001 not done\n")
    result = runner.invoke(app, ["next"])
    assert "/speckit.implement" in result.output


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
    symbol, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert symbol == "▶"
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
    symbol, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert symbol == "▶"
    assert "uncommitted changes" in annotation


def test_an_untracked_file_makes_a_passing_record_stale(
    gated: types.SimpleNamespace,
) -> None:
    """A new source file is untracked until it is added, so excluding untracked
    files would let never-verified code sit inside a green verdict."""
    _verify.write_record(gated.agent_dir, _record(gated))
    (gated.repo_root / "brand_new.py").write_text("def f(): ...\n")
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "▶"


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
    symbol, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert symbol == "▶"
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
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "●"

    (gated.repo_root / _verify.CONFIG_PATH).write_text(
        json.dumps({"verify": [second, gated.command]})
    )
    _commit_all(gated.repo_root, "same two, swapped")
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "▶"


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
    symbol, annotation = _implement_state(gated.spec_dir, gated.repo_root)
    assert symbol == "▶"
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
    assert _implement_state(gated.spec_dir, gated.repo_root)[0] == "●"

    clone = tmp_path_factory.mktemp("clone") / "wfctl"
    subprocess.run(
        ["git", "clone", "-q", str(gated.repo_root), str(clone)],
        check=True, capture_output=True,
    )
    fresh_state = clone / ".agent-runs"
    fresh_state.mkdir()
    monkeypatch.setenv("WFCTL_STATE_DIR", str(fresh_state))
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(clone))

    symbol, annotation = _implement_state(gated.spec_dir, clone)
    assert symbol == "▶" and "unverified" in annotation


# --- US3: projects without a definition of done are untouched ----------------

@pytest.mark.parametrize(
    "tasks, expected",
    [
        ("", "○"),
        ("- [ ] T001 not done\n", "▶"),
        ("- [x] T001 done\n", "●"),
        ("- [x] T001 done\n- [ ] T002 not done\n", "▶"),
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
    assert _implement_state(storyctl_dir.spec_dir, storyctl_dir.repo_root)[0] == "●"


def test_an_empty_verify_list_is_the_same_as_no_file(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Three spellings of 'not adopted' must be indistinguishable."""
    storyctl_dir.stage_upstream_of("tasks")
    for payload in ("{}", '{"verify": []}', '{"other": 1}'):
        (storyctl_dir.repo_root / _verify.CONFIG_PATH).write_text(payload)
        assert _implement_state(storyctl_dir.spec_dir, storyctl_dir.repo_root)[0] == "●"


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
    symbol, annotation = _implement_state(storyctl_dir.spec_dir, storyctl_dir.repo_root)
    assert symbol == "▶" and "malformed" in annotation
