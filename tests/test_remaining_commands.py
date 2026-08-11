"""Tests for wfctl resume, end, and checkpoint commands (Phase 7)."""
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


def test_checkpoint_creates_patch(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    result = runner.invoke(app, ["checkpoint"])
    assert result.exit_code == 0
    assert (agent_dir / "checkpoint-1.patch").exists()


def test_checkpoint_creates_md(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["checkpoint"])
    assert (agent_dir / "checkpoint-1.md").exists()


def test_checkpoint_not_initialized_exits_one(agent_dir: Path) -> None:
    result = runner.invoke(app, ["checkpoint"])
    assert result.exit_code == 1


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


def test_checkpoint_increments(agent_dir: Path) -> None:
    runner.invoke(app, ["start"])
    runner.invoke(app, ["checkpoint"])
    runner.invoke(app, ["checkpoint"])
    assert (agent_dir / "checkpoint-2.patch").exists()


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
    """Run doctor with the TTY seam forced. `_interactive` exists for this."""
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


def test_doctor_exit_code_is_unchanged_by_this_warning(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Matches the `no pinned commit` precedent: warnings continue, they don't fail."""
    repo_root = agent_dir.parent
    _seed_workmux(repo_root)
    assert _doctor(monkeypatch, interactive=False).exit_code == 0


# --- doctor: the leftover `.agent/` lint (#24) ------------------------------
#
# Per-branch artifacts moved into `specs/<branch>/`. A surviving `.agent/` is
# evidence that something wrote there, and the symptom is silent: a design doc
# left at the old path is one step inference no longer reads. The message is the
# deliverable here too, so its strings are asserted.


def test_doctor_warns_when_the_superseded_dir_exists(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Names the path, where artifacts moved to, and the move-then-remove fix."""
    repo_root = agent_dir.parent
    (repo_root / ".agent").mkdir()
    result = _doctor(monkeypatch, interactive=False)
    assert "`.agent/` exists" in result.output
    assert "specs/<branch>/design.md" in result.output
    assert "remove `.agent/`" in result.output


def test_doctor_names_the_repos_own_spec_root_not_a_hardcoded_path(
    agent_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """A repo whose specs live outside it must not be told to use `specs/`.

    Naming a path the layout does not use is worse than saying nothing — the
    reader would create the wrong directory and the doc would stay unread.

    `tmp_path_factory`, not `tmp_path`: the `agent_dir` fixture's repo root *is*
    `tmp_path`, so a root created under it would render relative and prove the
    opposite of what this test is for.
    """
    repo_root = agent_dir.parent
    (repo_root / ".agent").mkdir()
    outside = tmp_path_factory.mktemp("specs-outside-repo")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(outside))

    result = _doctor(monkeypatch, interactive=False)

    # Rich hard-wraps at the console width, and an absolute tmp path is long
    # enough to be split mid-token. Assert on the content, not the layout.
    unwrapped = result.output.replace("\n", "")
    assert f"{outside}/<branch>/design.md" in unwrapped
    assert "specs/<branch>/" not in result.output


def test_doctor_does_not_claim_the_pipeline_is_broken(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A leftover beside a correct spec dir is inert — don't call it breakage.

    The directory cannot distinguish a stale leftover from a component still
    writing, so the message must not assert either.
    """
    repo_root = agent_dir.parent
    (repo_root / ".agent").mkdir()
    result = _doctor(monkeypatch, interactive=False)
    assert "will be wrong" not in result.output
    assert "still writes" not in result.output


def test_doctor_is_silent_without_the_superseded_dir(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _doctor(monkeypatch, interactive=False)
    assert "`.agent/` exists" not in result.output


def test_doctor_exit_code_is_unchanged_by_the_superseded_dir(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Drift, not failure — same precedent as the teardown-hook lint above."""
    repo_root = agent_dir.parent
    (repo_root / ".agent").mkdir()
    assert _doctor(monkeypatch, interactive=False).exit_code == 0


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


def test_doctor_reports_a_pre_remove_still_naming_the_former_command(
    agent_dir: Path, tmp_path: Path
) -> None:
    """The signal that lets the compatibility alias eventually be deleted."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    (repo_root / ".workmux.yaml").write_text(
        'pre_remove:\n  - command -v wfctl && wfctl archive-story "$X" || true\n'
    )

    result = runner.invoke(app, ["doctor"])

    assert "archive-story" in result.output
    assert "archive-specs" in result.output
    # Never "not archiving": the alias works, so this repo is protected.
    assert "does not call" not in result.output


def test_doctor_does_not_fail_over_a_stale_hook_name(
    agent_dir: Path, tmp_path: Path
) -> None:
    """Drift, reported like the superseded-path checks beside it — never the
    exit code. /start-session runs doctor and must not read this as broken."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    (repo_root / ".workmux.yaml").write_text(
        'pre_remove:\n  - command -v wfctl && wfctl archive-story "$X" || true\n'
    )
    stale = runner.invoke(app, ["doctor"]).exit_code

    (repo_root / ".workmux.yaml").write_text(
        'pre_remove:\n  - wfctl archive-specs "$X"\n'
    )
    current = runner.invoke(app, ["doctor"]).exit_code

    assert stale == current


def test_doctor_is_quiet_about_a_hook_using_the_current_name(
    agent_dir: Path, tmp_path: Path
) -> None:
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    (repo_root / ".workmux.yaml").write_text(
        'pre_remove:\n  - wfctl archive-specs "$WM_WORKTREE_PATH" "$WM_HANDLE"\n'
    )

    out = runner.invoke(app, ["doctor"]).output

    assert "renamed to" not in out
    assert "does not call" not in out


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
