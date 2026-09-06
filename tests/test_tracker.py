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

def _add_tracker_and_runtime(bundle: Path) -> None:
    """Add what the shared `bundle` fixture leaves out of the fake bundle.

    Skills and commands come from the fixture; the tracker config and the
    speckit runtime are absent there so their own warning branches stay
    reachable, and these tests are the ones that need them present.
    """
    trackers = bundle / "agents" / "trackers"
    trackers.mkdir(parents=True)
    (trackers / "github.json").write_text(json.dumps(_GITHUB_VERBS))
    (trackers / "github-board.sh").write_text("#!/usr/bin/env bash\nexit 0\n")
    # Speckit runtime — installed as a repo-level managed mirror alongside skills.
    scripts = bundle / "specify" / "scripts" / "bash"
    scripts.mkdir(parents=True)
    (scripts / "setup-plan.sh").write_text("#!/usr/bin/env bash\necho plan\n")
    templates = bundle / "specify" / "templates"
    templates.mkdir(parents=True)
    (templates / "plan-template.md").write_text("# plan\n")


def test_install_copies_specify_runtime(bundle: Path, agent_dir: Path) -> None:
    """install-skills provisions the .specify/ runtime (scripts + templates)."""
    repo_root = agent_dir.parent
    _add_tracker_and_runtime(bundle)
    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0
    assert (repo_root / ".specify" / "scripts" / "bash" / "setup-plan.sh").exists()
    assert (repo_root / ".specify" / "templates" / "plan-template.md").exists()


def test_install_tracker_github_copies_config_and_sets_manifest(
    bundle: Path, agent_dir: Path
) -> None:
    repo_root = agent_dir.parent
    _add_tracker_and_runtime(bundle)
    result = runner.invoke(
        app, ["install-skills", "--tracker", "github"]
    )
    assert result.exit_code == 0
    assert (repo_root / ".agents" / "trackers" / "github.json").exists()
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert manifest["tracker"] == "github"


def test_install_tracker_github_copies_the_script_its_verbs_invoke(
    bundle: Path, agent_dir: Path
) -> None:
    """A board write is two API calls, so `start`/`stop` invoke a script by path.

    Installing the config without it is the failure this guards: the verbs are
    declared, `tracker-check` passes, and every call dies on a missing file.
    """
    repo_root = agent_dir.parent
    _add_tracker_and_runtime(bundle)
    result = runner.invoke(app, ["install-skills", "--tracker", "github"])
    assert result.exit_code == 0
    assert (repo_root / ".agents" / "trackers" / "github-board.sh").exists()


def test_shipped_github_config_is_valid_and_its_argv_paths_exist() -> None:
    """The config wfctl ships validates, and every file it names is shipped too.

    Two things drift apart on their own: a verb added to `github.json` without
    `ALLOWED` learning it, and an argv naming a helper that never entered the
    bundle. Both read as fine in a diff.
    """
    trackers = Path(_tracker.__file__).parent / "agents" / "trackers"
    config = json.loads((trackers / "github.json").read_text())
    assert _tracker.validate_config(config) == []
    for argv in config["verbs"].values():
        for token in argv:
            if token.startswith(".agents/trackers/"):
                assert (trackers / Path(token).name).exists(), token


def test_board_script_refuses_an_issue_key_that_is_not_a_number(tmp_path: Path) -> None:
    """A key that is not a key stops at the door, before any call is made.

    Not an injection test — nothing below the guard reaches a shell, and the
    canary here would not fire even if the guard were deleted. What it pins is
    that the script answers a bad key itself, with an exit code the hooks treat
    as nothing-to-do, rather than passing it to `gh` and surfacing an API error
    from a worktree create.
    """
    script = Path(_tracker.__file__).parent / "agents" / "trackers" / "github-board.sh"
    canary = tmp_path / "pwned"
    result = subprocess.run(
        ["bash", str(script), f"$(touch {canary})", "In Progress"],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "is not an issue number" in result.stderr
    assert not canary.exists()


_BOARD_VERBS = {
    "verbs": {
        "start": ["gh", "board", "start", "{id}"],
        "stop": ["gh", "board", "stop", "{id}"],
        "view": ["gh", "issue", "view", "{id}"],
    }
}


def test_start_takes_the_issue_key_off_the_branch(
    agent_dir: Path, captured_argv: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The hooks call `wfctl issue start` bare, so the key has to come from here.

    Deriving it in the hook instead means a regex in a committed `.workmux.yaml`,
    and the key shape belongs to the tracker — a hardcoded `[0-9]+` is right for
    GitHub and wrong for every repo whose keys are not numbers.
    """
    repo_root = agent_dir.parent
    # `captured_argv` patches subprocess.run for the whole module, so a real
    # `git checkout` here would be swallowed by the same fake.
    monkeypatch.setattr("wfctl.cli.resolve_branch", lambda _: "71-slug")
    _configure_tracker(repo_root, "github", _BOARD_VERBS)
    result = runner.invoke(app, ["issue", "start"])
    assert result.exit_code == 0
    assert captured_argv == [["gh", "board", "start", "71"]]


def test_start_on_a_branch_with_no_issue_key_reports_and_does_nothing(
    agent_dir: Path, captured_argv: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A worktree made outside the naming rule has no issue to report about.

    Dispatching anyway sends the literal "unknown" to the backend, which reaches
    the board as an API error from a `workmux add` — a red line during worktree
    creation, for a worktree that was never going to be on the board.
    """
    repo_root = agent_dir.parent
    monkeypatch.setattr("wfctl.cli.resolve_branch", lambda _: "spike-no-key")
    _configure_tracker(repo_root, "github", _BOARD_VERBS)
    result = runner.invoke(app, ["issue", "start"])
    assert result.exit_code == 0
    assert "No issue key in branch" in result.output
    assert captured_argv == []


def test_view_does_not_default_its_id_to_the_branch(
    agent_dir: Path, captured_argv: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only `start`/`stop` default. A verb a person types means what they typed.

    `close` sharing the default would close the branch's issue on a bare
    `wfctl issue close`, which is the reason the set is a list and not "any verb
    taking {id}".
    """
    repo_root = agent_dir.parent
    monkeypatch.setattr("wfctl.cli.resolve_branch", lambda _: "71-slug")
    _configure_tracker(repo_root, "github", _BOARD_VERBS)
    result = runner.invoke(app, ["issue", "view"])
    assert result.exit_code == 1
    assert "requires --id" in result.output
    assert captured_argv == []


@pytest.mark.parametrize("config", [
    Path(__file__).resolve().parent.parent / ".workmux.yaml",
    Path(_tracker.__file__).parent / "agents" / "configs" / "workmux" / ".workmux.yaml",
])
def test_board_hooks_cannot_gate_a_worktree(config: Path) -> None:
    """Every `issue start`/`stop` hook swallows its own failure.

    The rule is written in both files as prose, and prose is what a later edit
    reformats away. `workmux add` is how every worktree in this repo is created,
    including for work answering to no issue and on a machine with no network,
    and `pre_remove` failing is documented to abort a removal outright — so a
    hook that can exit non-zero is one that strands a worktree.

    Both copies, because the template is seeded once into other repos and never
    revisited: a rule that holds here and not there reaches every repo seeded
    afterwards and none of the ones seeded before.
    """
    # Comment lines are skipped, and the rationale above each hook names the
    # command it explains — so a scan that keeps them counts prose as a hook.
    hooks = [
        line for line in config.read_text().splitlines()
        if not line.lstrip().startswith("#")
        and ("wfctl issue start" in line or "wfctl issue stop" in line)
    ]
    assert len(hooks) == 2, f"expected a start and a stop hook, got {hooks}"
    for line in hooks:
        assert line.rstrip().endswith("|| true"), line


def test_install_custom_tracker_warns_when_config_absent(
    bundle: Path, agent_dir: Path
) -> None:
    repo_root = agent_dir.parent
    _add_tracker_and_runtime(bundle)
    result = runner.invoke(
        app, ["install-skills", "--tracker", "jira"]
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
