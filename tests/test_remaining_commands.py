"""Tests for wfctl resume and end commands (Phase 7)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl import _workmux
from wfctl.cli import app

runner = CliRunner()


def test_resume_appends_event(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["resume"])
    events = (agent_dir / "events.jsonl").read_text().splitlines()
    event_types = [json.loads(e)["event"] for e in events]
    assert "resume" in event_types


def test_resume_exits_zero(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    result = runner.invoke(app, ["resume"])
    assert result.exit_code == 0


def test_resume_not_initialized_exits_one(agent_dir: Path) -> None:
    result = runner.invoke(app, ["resume"])
    assert result.exit_code == 1


def test_resume_re_infers_step_from_filesystem(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    # Force stale step into current.json
    current_json = agent_dir / "current.json"
    data = json.loads(current_json.read_text())
    data["workflow_step"] = "implement"  # stale — no artifacts to back this up
    current_json.write_text(json.dumps(data))
    runner.invoke(app, ["resume"])
    fresh = json.loads(current_json.read_text())
    assert fresh["workflow_step"] != "implement"  # re-inferred from empty spec dir → brainstorm


def test_end_sets_status_complete(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["end"])
    data = json.loads((agent_dir / "current.json").read_text())
    assert data["status"] == "complete"


def test_end_writes_session_summary(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["end"])
    assert (agent_dir / "session-summary.md").exists()


def test_end_current_json_valid(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["end"])
    # Must be parseable — no corruption
    json.loads((agent_dir / "current.json").read_text())


def test_log_shows_events(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["next"])
    result = runner.invoke(app, ["log"])
    assert result.exit_code == 0
    assert "start" in result.output
    assert "next" in result.output


def test_log_empty_before_start(agent_dir: Path) -> None:
    result = runner.invoke(app, ["log"])
    assert result.exit_code == 0
    assert "No events" in result.output


def test_state_dir_path_not_wrapped(agent_dir: Path, monkeypatch) -> None:
    """Output is consumed by $(wfctl state-dir); a wrapped path breaks callers."""
    monkeypatch.setenv("COLUMNS", "40")  # narrower than the path
    result = runner.invoke(app, ["state-dir"])
    assert result.exit_code == 0
    assert result.stdout.strip() == str(agent_dir)
    assert "\n" not in result.stdout.strip()


# --- doctor: the .workmux.yaml teardown-hook lint (#17) ---------------------
#
# `install-config` is seed-once, so fixing the upstream template never reaches a
# repo that was already seeded. This lint is the only path by which such a repo
# becomes protected, which is why its output strings are asserted rather than
# just its behaviour — the message *is* the deliverable.

_UNWIRED = "worktree_dir: wt\npre_remove: []\n"


def _seed_workmux(repo_root: Path, text: str = _UNWIRED) -> Path:
    wf = repo_root / ".workmux.yaml"
    wf.write_text(text)
    return wf


def _doctor(monkeypatch: pytest.MonkeyPatch, *, interactive: bool, answer: str = "y"):
    """Run doctor with the TTY seam forced. `_interactive` exists for this.

    Exit-code assertions below are safe because conftest stubs the tool-version
    check suite-wide — see `_tool_version_is_not_under_test`.
    """
    monkeypatch.setattr("wfctl.cli._interactive", lambda: interactive)
    return runner.invoke(app, ["doctor"], input=answer if interactive else "")


def test_doctor_warns_when_pre_remove_is_not_wired(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = agent_dir.parent
    _seed_workmux(repo_root)
    result = _doctor(monkeypatch, interactive=False)
    assert "pre_remove does not call" in result.output
    assert "discard its specs" in result.output


def test_doctor_non_interactive_changes_nothing(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The path /start-session takes: report, never prompt, never write."""
    repo_root = agent_dir.parent
    wf = _seed_workmux(repo_root)
    before = wf.read_text()
    _doctor(monkeypatch, interactive=False)
    assert wf.read_text() == before


def test_doctor_non_interactive_names_how_to_reach_the_fix(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without this the automated path reports a problem with no route to a fix."""
    repo_root = agent_dir.parent
    _seed_workmux(repo_root)
    result = _doctor(monkeypatch, interactive=False)
    assert "from a terminal" in result.output


def test_doctor_states_the_archive_destination_before_asking(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Consent to a change whose entire value is a destination the developer
    cannot otherwise see."""
    repo_root = agent_dir.parent
    _seed_workmux(repo_root)
    result = _doctor(monkeypatch, interactive=False)
    assert "Archives would be written to:" in result.output
    assert "/archive/" in result.output


def test_doctor_fails_over_an_unwired_hook_with_no_terminal(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The path CI takes. No TTY means the offer is skipped, so the hook is still
    unwired when doctor returns — and the exit code says so."""
    repo_root = agent_dir.parent
    _seed_workmux(repo_root)

    assert _doctor(monkeypatch, interactive=False).exit_code == 1


def test_doctor_fails_over_an_unwired_hook_when_the_fix_is_declined(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Declining leaves the drift in place, so it is still a finding."""
    repo_root = agent_dir.parent
    _seed_workmux(repo_root)
    monkeypatch.setattr("typer.confirm", lambda *a, **k: False)

    assert _doctor(monkeypatch, interactive=True).exit_code == 1


def test_doctor_passes_when_the_offered_fix_is_accepted(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exit code describes the repo when the run ends, not what was seen along
    the way. Accepting the offer leaves the repo protected, so there is nothing
    left to report — the one case where a check resolves its own finding.

    Asserts the file too: an exit code of 0 with the hook still unwired would be
    the dangerous version of this passing.
    """
    repo_root = agent_dir.parent
    _seed_workmux(repo_root)
    monkeypatch.setattr("typer.confirm", lambda *a, **k: True)

    result = _doctor(monkeypatch, interactive=True)

    assert result.exit_code == 0
    assert _workmux.pre_remove_wired((repo_root / ".workmux.yaml").read_text())


# --- doctor: the swept transition reports (#36) -----------------------------
#
# Two reports were removed here: the leftover `.agent/` lint (#24) and the
# stale `archive-story` hook name. Both were transitional — nothing creates
# either condition any more — and each is now handled where it actually
# matters: the superseded directory by the rescue path in `archive-specs`,
# which runs at teardown rather than whenever someone happens to run doctor,
# and the retired hook name by the archive command reporting its own
# invocation. What follows guards their *absence*, because a silently
# reintroduced check is how this sweep gets undone.


def test_doctor_ignores_the_superseded_dir_entirely(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A leftover `.agent/` is not doctor's business since #36.

    Deleting it destroys data, so the directory itself is untouched and still
    rescued at teardown — but reporting it here told the reader about a path
    they could not lose anything through, in a repo that may never be torn down.
    """
    repo_root = agent_dir.parent
    (repo_root / ".agent").mkdir()
    (repo_root / ".agent" / "spec.md").write_text("legacy design\n")

    result = _doctor(monkeypatch, interactive=False)

    assert ".agent/" not in result.output
    assert "superseded" not in result.output
    assert result.exit_code == 0


def test_doctor_ignores_a_hook_naming_the_former_command(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Such a repo is protected — the alias dispatches — so doctor stays quiet.

    The report moved to `archive-specs` itself, which fires at the moment the
    hook runs rather than whenever doctor happens to be invoked. Asserting the
    silence here is what keeps the two from both reporting it.
    """
    repo_root = agent_dir.parent
    _seed_workmux(
        repo_root,
        'pre_remove:\n  - command -v wfctl && wfctl archive-story "$X" || true\n',
    )

    result = _doctor(monkeypatch, interactive=False)

    assert "archive-story" not in result.output
    assert "renamed" not in result.output
    assert result.exit_code == 0


def test_doctor_wires_the_hook_when_confirmed(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = agent_dir.parent
    wf = _seed_workmux(repo_root)
    _doctor(monkeypatch, interactive=True, answer="y\n")
    text = wf.read_text()
    assert _workmux.pre_remove_wired(text)
    assert "worktree_dir: wt" in text, "the rest of the file must survive"


def test_doctor_replaces_the_placeholder_with_the_hook(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The retrofit writes into a file the repo owns and has customized.

    Sized from WIRED_PRE_REMOVE rather than a literal, so the hook's shape can
    change — as it did when it became a block scalar — without this asserting the
    old one back into place.
    """
    from wfctl import _workmux
    repo_root = agent_dir.parent
    wf = _seed_workmux(repo_root)
    before = wf.read_text().splitlines()
    _doctor(monkeypatch, interactive=True, answer="y\n")
    grew = len(_workmux.WIRED_PRE_REMOVE.rstrip("\n").splitlines()) - 1
    assert len(wf.read_text().splitlines()) == len(before) + grew


def test_doctor_declining_writes_nothing_and_is_not_recorded(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Drift recurs, so it is re-reported rather than silenced by one decline."""
    repo_root = agent_dir.parent
    wf = _seed_workmux(repo_root)
    _doctor(monkeypatch, interactive=True, answer="n\n")
    assert wf.read_text() == _UNWIRED
    again = _doctor(monkeypatch, interactive=False)
    assert "pre_remove does not call" in again.output


def test_doctor_refuses_a_customized_pre_remove(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = agent_dir.parent
    custom = "worktree_dir: wt\npre_remove:\n  - echo mine\n"
    wf = _seed_workmux(repo_root, custom)
    result = _doctor(monkeypatch, interactive=True, answer="y\n")
    assert wf.read_text() == custom, "a hook we don't understand is never rewritten"
    assert "yourself" in result.output
    assert _workmux.ARCHIVE_HOOK in result.output


def test_doctor_silent_when_no_workmux_config(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Not every repo uses workmux."""
    result = _doctor(monkeypatch, interactive=False)
    assert "pre_remove" not in result.output


def test_doctor_silent_when_already_wired(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = agent_dir.parent
    _seed_workmux(repo_root, f"worktree_dir: wt\n{_workmux.WIRED_PRE_REMOVE}")
    result = _doctor(monkeypatch, interactive=False)
    assert "pre_remove does not call" not in result.output


def test_doctor_never_reports_an_unsubstituted_prefix(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A cosmetic warning beside a data-loss warning trains the reader to skim
    past both. This has no task-level symptom, so only a test holds the line."""
    repo_root = agent_dir.parent
    _seed_workmux(
        repo_root,
        f'# window_prefix: "<project>__"\n{_workmux.WIRED_PRE_REMOVE}',
    )
    result = _doctor(monkeypatch, interactive=False)
    assert "window_prefix" not in result.output
    assert "<project>" not in result.output


def test_doctor_still_warns_when_archive_story_appears_outside_the_hook(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A mention elsewhere in the file must not silence the warning.

    The lint scans the `pre_remove:` block only. Scanning the whole file let an
    unrelated occurrence — a pane command here — report the repo as protected
    while `pre_remove: []` left teardown unwired.
    """
    repo_root = agent_dir.parent
    _seed_workmux(
        repo_root,
        "windows:\n"
        "  - name: term\n"
        "    panes:\n"
        "      - command: wfctl archive-story --help\n"
        "pre_remove: []\n",
    )
    result = _doctor(monkeypatch, interactive=False)
    assert "pre_remove does not call" in result.output


def test_doctor_treats_either_command_name_identically(
    agent_dir: Path, tmp_path: Path
) -> None:
    """Both names archive, so both must read as protected and exit the same.

    The report distinguishing them was removed in #36. What survives is that
    neither produces the "not archiving" warning and neither moves the exit
    code — /start-session runs doctor and must not read a pre-rename hook as
    broken.
    """
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    (repo_root / ".workmux.yaml").write_text(
        'pre_remove:\n  - command -v wfctl && wfctl archive-story "$X" || true\n'
    )
    former = runner.invoke(app, ["doctor"])

    (repo_root / ".workmux.yaml").write_text(
        'pre_remove:\n  - wfctl archive-specs "$X"\n'
    )
    current = runner.invoke(app, ["doctor"])

    assert former.exit_code == current.exit_code
    for out in (former.output, current.output):
        # Keyed to `pre_remove` specifically: `post_create` has its own
        # "does not call" warning, and a bare substring match would catch it.
        assert "pre_remove does not call" not in out
        assert "renamed to" not in out


def test_unwired_warning_names_the_current_command(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The message is the deliverable — it tells someone what to add.

    It named `archive-story` after the rename, so following it would have wired
    the compatibility alias rather than the command. The existing warning test
    asserts the sentence but not the command, so nothing caught it.
    """
    repo_root = agent_dir.parent
    _seed_workmux(repo_root)

    out = _doctor(monkeypatch, interactive=False).output

    assert "archive-specs" in out
    assert "`wfctl archive-story`" not in out


# --- wfctl arch context -------------------------------------------------------
#
# `agent_dir` supplies the repo root; the arch root is pointed at a directory
# under it per test, so a record set is built by writing files and nothing else.


def _record(root: Path, slug: str, status: str, decision: str = "x") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{slug}.md"
    path.write_text(
        f"---\nstatus: {status}\n---\n\n# {slug}\n\n## Decision\n\n{decision}\n"
    )
    return path


def _arch_root(agent_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = agent_dir.parent / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    return root


def test_arch_context_lists_only_accepted_records(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The projection is the whole point: a superseded record read as live is
    the confusion `status` exists to prevent."""
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "layer-model", "accepted", "wfctl/agents/ is source.")
    _record(root, "old-way", "superseded", "The way it used to work.")
    _record(root, "dead-idea", "rejected", "Never built.")

    result = runner.invoke(app, ["arch", "context"])

    assert result.exit_code == 0
    assert "1 accepted decision" in result.output
    assert "layer-model" in result.output
    assert "wfctl/agents/ is source." in result.output
    assert "old-way" not in result.output
    assert "The way it used to work." not in result.output


def test_arch_context_counts_what_it_left_out(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A record silently missing from the contract reads as a decision nobody
    made — so the excluded ones are counted by status, not dropped."""
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "in-force", "accepted")
    _record(root, "replaced", "superseded")
    _record(root, "gone", "retired")

    out = runner.invoke(app, ["arch", "context"]).output

    assert "2 records not shown" in out
    assert "1 superseded" in out
    assert "1 retired" in out


def test_arch_context_empty_root_is_not_an_error(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A repo has no records until it writes its first one. Reporting that
    state as a failure would describe a normal repo as broken."""
    _arch_root(agent_dir, monkeypatch)

    result = runner.invoke(app, ["arch", "context"])

    assert result.exit_code == 0
    assert "no accepted decisions" in result.output
    assert "holds no records yet" in result.output


def test_arch_context_names_an_unreadable_record(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Excluded and said so. Dropping it silently loses the one signal that a
    record needs fixing, and the author is the only one who can fix it."""
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "good", "accepted")
    root.mkdir(parents=True, exist_ok=True)
    (root / "draft-notes.md").write_text("no frontmatter here\n")

    result = runner.invoke(app, ["arch", "context"])

    assert result.exit_code == 0
    assert "1 record has no readable status" in result.output
    assert "draft-notes.md" in result.output
    assert "good" in result.output


def test_arch_context_unrecognised_status_is_never_in_force(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The load-bearing case (quickstart.md): defaulting an unparseable record
    to in-force presents an unreviewed decision as binding."""
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "garbage", "acepted", "Typo'd status, not a decision.")

    out = runner.invoke(app, ["arch", "context"]).output

    assert "no accepted decisions" in out
    assert "Typo'd status, not a decision." not in out


def test_doctor_reports_a_malformed_definition_of_done(agent_dir: Path) -> None:
    """A broken `wfctl.json` is drift, and drift fails the build (#41's contract).

    Absent degrades honestly; broken means the implement gate silently never
    runs. Only someone who runs `wfctl verify` would otherwise find out, and the
    people who most need to know are the ones whose CI calls `doctor`.
    """
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    (repo_root / "wfctl.json").write_text('{"verify": ["pytest -q"]}\n')

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "wfctl.json" in result.output


def test_doctor_is_silent_when_no_definition_of_done_exists(agent_dir: Path) -> None:
    """Not adopting the feature is not a finding."""
    result = runner.invoke(app, ["doctor"])
    assert "wfctl.json" not in result.output
