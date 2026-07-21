"""Tests for the wfctl issue dispatcher (_tracker) and install --tracker."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

import wfctl._tracker as _tracker
from wfctl.cli import app

runner = CliRunner()

_GITHUB_VERBS = {
    "verbs": {
        "list": ["gh", "issue", "list", "--state", "open"],
        "view": ["gh", "issue", "view", "{id}"],
        "close": ["gh", "issue", "close", "{id}", "--comment", "{comment}"],
        "comment": ["gh", "issue", "comment", "{id}", "--body", "{body}"],
        "create": ["gh", "issue", "create", "--title", "{title}", "--body", "{body}"],
        "label": ["gh", "issue", "edit", "{id}", "--{action}-label", "{label}"],
    }
}


def _configure_tracker(repo_root: Path, name: str, config: dict) -> None:
    """Write a tracker config + point the manifest at it."""
    tdir = repo_root / ".agents" / "trackers"
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / f"{name}.json").write_text(json.dumps(config))
    (repo_root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": name}))


@pytest.fixture
def captured_argv(monkeypatch: pytest.MonkeyPatch) -> list:
    """Capture argv passed to subprocess.run instead of executing it."""
    calls: list = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(_tracker.subprocess, "run", fake_run)
    return calls


def test_close_builds_expected_argv(agent_dir: Path, captured_argv: list) -> None:
    repo_root = agent_dir.parent
    _configure_tracker(repo_root, "github", _GITHUB_VERBS)
    result = runner.invoke(app, ["issue", "close", "71", "--comment", "Done in abc"])
    assert result.exit_code == 0
    assert captured_argv == [["gh", "issue", "close", "71", "--comment", "Done in abc"]]


def test_free_text_lands_as_single_inert_argv_token(agent_dir: Path, captured_argv: list) -> None:
    repo_root = agent_dir.parent
    _configure_tracker(repo_root, "github", _GITHUB_VERBS)
    payload = '$(rm -rf /); "quoted" & backtick`x`'
    runner.invoke(app, ["issue", "comment", "9", "--body", payload])
    # The dangerous string is exactly one argv element, never shell-interpreted.
    assert captured_argv == [["gh", "issue", "comment", "9", "--body", payload]]


def test_within_token_substitution_for_label(agent_dir: Path, captured_argv: list) -> None:
    repo_root = agent_dir.parent
    _configure_tracker(repo_root, "github", _GITHUB_VERBS)
    runner.invoke(app, ["issue", "label", "5", "--action", "add", "--label", "in-progress"])
    assert captured_argv == [["gh", "issue", "edit", "5", "--add-label", "in-progress"]]


def test_unsupported_verb_skips_gracefully(agent_dir: Path, captured_argv: list) -> None:
    repo_root = agent_dir.parent
    minimal = {"verbs": {"list": ["gh", "issue", "list"], "view": ["gh", "issue", "view", "{id}"]}}
    _configure_tracker(repo_root, "jira", minimal)
    result = runner.invoke(app, ["issue", "create", "--title", "x", "--body", "y"])
    assert result.exit_code == 0
    assert "does not support 'create'" in result.output
    assert captured_argv == []


def test_no_tracker_configured_skips(agent_dir: Path, captured_argv: list) -> None:
    result = runner.invoke(app, ["issue", "view", "1"])
    assert result.exit_code == 0
    assert "No tracker configured" in result.output
    assert captured_argv == []


def test_missing_config_file_degrades(agent_dir: Path, captured_argv: list) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "jira"}))
    result = runner.invoke(app, ["issue", "view", "1"])
    assert result.exit_code == 0
    assert "missing or invalid" in result.output
    assert captured_argv == []


def test_missing_placeholder_errors(agent_dir: Path, captured_argv: list) -> None:
    repo_root = agent_dir.parent
    _configure_tracker(repo_root, "github", _GITHUB_VERBS)
    result = runner.invoke(app, ["issue", "close", "71"])  # no --comment
    assert result.exit_code == 1
    assert "requires --comment" in result.output
    assert captured_argv == []


def test_nonzero_subprocess_propagates_exit_code(agent_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = agent_dir.parent
    _configure_tracker(repo_root, "github", _GITHUB_VERBS)

    def fail_run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 3, stdout="", stderr="boom")

    monkeypatch.setattr(_tracker.subprocess, "run", fail_run)
    result = runner.invoke(app, ["issue", "view", "1"])
    assert result.exit_code == 3


def test_successful_dispatch_logs_event(agent_dir: Path, captured_argv: list) -> None:
    repo_root = agent_dir.parent
    _configure_tracker(repo_root, "github", _GITHUB_VERBS)
    runner.invoke(app, ["issue", "view", "1"])
    events = (agent_dir / "events.jsonl").read_text()
    assert '"event": "issue"' in events
    assert '"verb": "view"' in events


# --- change (changes section) + {me} identity ---

_CHANGES_CFG = {
    "identity": "@me",
    "verbs": {"list": ["gh", "issue", "list"]},
    "changes": {
        "list": ["gh", "pr", "list", "--state", "open", "--author", "{me}"],
        "view": ["gh", "pr", "view", "{id}"],
    },
}


def test_change_list_dispatches_changes_section(agent_dir: Path, captured_argv: list) -> None:
    _configure_tracker(agent_dir.parent, "github", _CHANGES_CFG)
    result = runner.invoke(app, ["change", "list"])
    assert result.exit_code == 0
    assert captured_argv == [["gh", "pr", "list", "--state", "open", "--author", "@me"]]


def test_change_view_substitutes_id(agent_dir: Path, captured_argv: list) -> None:
    _configure_tracker(agent_dir.parent, "github", _CHANGES_CFG)
    runner.invoke(app, ["change", "view", "128"])
    assert captured_argv == [["gh", "pr", "view", "128"]]


def test_issue_and_change_read_different_sections(agent_dir: Path, captured_argv: list) -> None:
    _configure_tracker(agent_dir.parent, "github", _CHANGES_CFG)
    runner.invoke(app, ["issue", "list"])
    runner.invoke(app, ["change", "list"])
    assert captured_argv == [
        ["gh", "issue", "list"],
        ["gh", "pr", "list", "--state", "open", "--author", "@me"],
    ]


def test_me_placeholder_filled_from_identity(agent_dir: Path, captured_argv: list) -> None:
    cfg = {"identity": "@me", "verbs": {"list": ["gh", "issue", "list", "--assignee", "{me}"]}}
    _configure_tracker(agent_dir.parent, "github", cfg)
    runner.invoke(app, ["issue", "list"])
    assert captured_argv == [["gh", "issue", "list", "--assignee", "@me"]]


def test_me_without_identity_errors(agent_dir: Path, captured_argv: list) -> None:
    cfg = {"verbs": {"list": ["gh", "issue", "list", "--assignee", "{me}"]}}  # no identity
    _configure_tracker(agent_dir.parent, "github", cfg)
    result = runner.invoke(app, ["issue", "list"])
    assert result.exit_code == 1
    assert "identity" in result.output
    assert captured_argv == []


def test_change_unsupported_verb_skips_gracefully(agent_dir: Path, captured_argv: list) -> None:
    _configure_tracker(agent_dir.parent, "github", {"verbs": {"list": ["gh", "issue", "list"]}})
    result = runner.invoke(app, ["change", "list"])  # no 'changes' section
    assert result.exit_code == 0
    assert "does not support 'list'" in result.output
    assert captured_argv == []


def test_change_logs_change_event(agent_dir: Path, captured_argv: list) -> None:
    _configure_tracker(agent_dir.parent, "github", _CHANGES_CFG)
    runner.invoke(app, ["change", "list"])
    events = (agent_dir / "events.jsonl").read_text()
    assert '"event": "change"' in events
    assert '"verb": "list"' in events


# --- tracker-check ---

def test_tracker_check_ok(agent_dir: Path) -> None:
    repo_root = agent_dir.parent
    _configure_tracker(repo_root, "github", _GITHUB_VERBS)
    result = runner.invoke(app, ["tracker-check", "github"])
    assert result.exit_code == 0
    assert "OK:" in result.output


def test_tracker_check_missing_file(agent_dir: Path) -> None:
    result = runner.invoke(app, ["tracker-check", "nope"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_tracker_check_reports_bad_placeholder_and_verb(agent_dir: Path) -> None:
    repo_root = agent_dir.parent
    _configure_tracker(repo_root, "jp", {
        "verbs": {
            "view": ["jp", "read", "{issue_id}"],  # {issue_id} is not a valid placeholder — it's {id}
            "frobnicate": ["jp", "frob"],           # unknown verb
        },
    })
    result = runner.invoke(app, ["tracker-check", "jp"])
    assert result.exit_code == 1
    assert "issue_id" in result.output
    assert "frobnicate" in result.output


def test_tracker_check_reports_bad_key_pattern(agent_dir: Path) -> None:
    repo_root = agent_dir.parent
    _configure_tracker(repo_root, "jp", {"key_pattern": "[unclosed", "verbs": {"list": ["jp", "ls"]}})
    result = runner.invoke(app, ["tracker-check", "jp"])
    assert result.exit_code == 1
    assert "key_pattern" in result.output


def test_tracker_check_accepts_identity_me_and_changes(agent_dir: Path) -> None:
    """A config using {me} (with identity) + a changes section validates OK."""
    _configure_tracker(agent_dir.parent, "github", _CHANGES_CFG)
    result = runner.invoke(app, ["tracker-check", "github"])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_tracker_check_me_without_identity_is_invalid(agent_dir: Path) -> None:
    cfg = {"verbs": {"list": ["gh", "issue", "list", "--assignee", "{me}"]}}  # {me}, no identity
    _configure_tracker(agent_dir.parent, "github", cfg)
    result = runner.invoke(app, ["tracker-check", "github"])
    assert result.exit_code == 1
    assert "identity" in result.output


def test_tracker_check_rejects_bad_changes_verb(agent_dir: Path) -> None:
    cfg = {"verbs": {"list": ["gh", "issue", "list"]}, "changes": {"merge": ["gh", "pr", "merge"]}}
    _configure_tracker(agent_dir.parent, "github", cfg)
    result = runner.invoke(app, ["tracker-check", "github"])
    assert result.exit_code == 1
    assert "changes" in result.output and "merge" in result.output


# --- install-skills --tracker ---

def _make_wf_skills_repo_with_tracker(base: Path) -> Path:
    src = base / "wf-skills-src"
    src.mkdir()
    subprocess.run(["git", "init", str(src)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "config", "user.email", "t@t.com"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "config", "user.name", "T"], check=True, capture_output=True)
    skill = src / ".agents" / "skills" / "test-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# test-skill\n")
    cmd = src / ".agents" / "commands"
    cmd.mkdir(parents=True)
    (cmd / "test-cmd.md").write_text("# test-cmd\n")
    trackers = src / ".agents" / "trackers"
    trackers.mkdir(parents=True)
    (trackers / "github.json").write_text(json.dumps(_GITHUB_VERBS))
    # Speckit runtime — installed as a repo-level managed mirror alongside skills.
    scripts = src / ".specify" / "scripts" / "bash"
    scripts.mkdir(parents=True)
    (scripts / "setup-plan.sh").write_text("#!/usr/bin/env bash\necho plan\n")
    templates = src / ".specify" / "templates"
    templates.mkdir(parents=True)
    (templates / "plan-template.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(src), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "commit", "-m", "init"], check=True, capture_output=True)
    return src


def test_install_copies_specify_runtime(agent_dir: Path, tmp_path: Path) -> None:
    """install-skills provisions the .specify/ runtime (scripts + templates)."""
    repo_root = agent_dir.parent
    src = _make_wf_skills_repo_with_tracker(tmp_path)
    result = runner.invoke(app, ["install-skills", "--repo", f"file://{src}", "--ref", "master"])
    assert result.exit_code == 0
    assert (repo_root / ".specify" / "scripts" / "bash" / "setup-plan.sh").exists()
    assert (repo_root / ".specify" / "templates" / "plan-template.md").exists()


def test_install_tracker_github_copies_config_and_sets_manifest(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    src = _make_wf_skills_repo_with_tracker(tmp_path)
    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--tracker", "github"]
    )
    assert result.exit_code == 0
    assert (repo_root / ".agents" / "trackers" / "github.json").exists()
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert manifest["tracker"] == "github"


def test_install_custom_tracker_warns_when_config_absent(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    src = _make_wf_skills_repo_with_tracker(tmp_path)
    result = runner.invoke(
        app, ["install-skills", "--repo", f"file://{src}", "--ref", "master", "--tracker", "jira"]
    )
    assert result.exit_code == 0
    assert "no .agents/trackers/jira.json found" in result.output
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert manifest["tracker"] == "jira"


def test_branch_issue_parser_default_is_numeric(agent_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With no tracker, _resolve_context extracts a numeric key; slug is optional."""
    from wfctl.cli import _resolve_context
    for branch, want in [("251-slug", "251"), ("251", "251"), ("251_slug", "251"),
                         ("PROJ-123-slug", "unknown"), ("no-issue", "unknown")]:
        monkeypatch.setenv("WFCTL_BRANCH", branch)
        assert _resolve_context()[3] == want


def test_branch_issue_parser_uses_configured_key_pattern(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A tracker's key_pattern lets _resolve_context read non-numeric keys."""
    from wfctl.cli import _resolve_context
    repo_root = agent_dir.parent
    _configure_tracker(repo_root, "jira", {"key_pattern": r"[A-Z]+-\d+", "verbs": {}})
    for branch, want in [("PROJ-123-slug", "PROJ-123"), ("ENG-42-x", "ENG-42"),
                         ("251-slug", "unknown")]:
        monkeypatch.setenv("WFCTL_BRANCH", branch)
        assert _resolve_context()[3] == want
