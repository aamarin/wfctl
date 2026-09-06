"""Tests for the wfctl issue dispatcher (_tracker) and install --tracker."""
from __future__ import annotations

import json
import os
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


def test_scaffold_skill_documents_every_verb_the_contract_allows() -> None:
    """The skill is where a backend author learns what to implement.

    A verb added to `ALLOWED` and not to the skill is a verb no hand-authored
    backend will ever declare — which is how `start`/`stop` reached the contract
    while the scaffold step still asked about six. Checked against `ALLOWED`
    rather than against a count, because a count beside a list is a second copy
    of the list and the copy is what goes stale.
    """
    skill = (
        Path(_tracker.__file__).parent
        / "agents" / "skills" / "scaffold-tracker" / "SKILL.md"
    ).read_text()
    missing = [verb for verb in _tracker.ALLOWED if f"`{verb}`" not in skill]
    assert missing == [], f"scaffold-tracker documents no {missing}"


def test_stop_is_silent_while_another_worktree_holds_the_same_issue(
    agent_dir: Path, captured_argv: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One worktree stopping is not the issue stopping.

    Two handles may carry one issue key — `175-fix-a` and `175-fix-b` both
    resolve to 175 — and removing either fires `pre_remove`. The backend is
    handed a key and nothing about the tree it came from, so it cannot tell that
    work is still live somewhere; wfctl can, and owes it a fact about the issue
    rather than about the caller.
    """
    repo_root = agent_dir.parent
    monkeypatch.setattr("wfctl.cli.resolve_branch", lambda _: "175-fix-a")
    monkeypatch.setattr(
        "wfctl.cli.worktree_branches", lambda _: ["main", "175-fix-a", "175-fix-b"]
    )
    _configure_tracker(repo_root, "github", _BOARD_VERBS)
    result = runner.invoke(app, ["issue", "stop"])
    assert result.exit_code == 0
    assert "still checked out in another worktree" in result.output
    assert captured_argv == []


def test_stop_fires_when_it_is_the_last_worktree_on_the_issue(
    agent_dir: Path, captured_argv: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The guard must not make `stop` unreachable — that is the ordinary case."""
    repo_root = agent_dir.parent
    monkeypatch.setattr("wfctl.cli.resolve_branch", lambda _: "175-fix-a")
    monkeypatch.setattr(
        "wfctl.cli.worktree_branches", lambda _: ["main", "175-fix-a", "42-other"]
    )
    _configure_tracker(repo_root, "github", _BOARD_VERBS)
    assert runner.invoke(app, ["issue", "stop"]).exit_code == 0
    assert captured_argv == [["gh", "board", "stop", "175"]]


def test_an_explicit_id_is_not_second_guessed(
    agent_dir: Path, captured_argv: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`wfctl issue stop 175` is a person asserting it; the guard is for hooks.

    Applying it to the typed form would make the explicit command the one that
    silently does nothing.
    """
    repo_root = agent_dir.parent
    monkeypatch.setattr("wfctl.cli.resolve_branch", lambda _: "175-fix-a")
    monkeypatch.setattr(
        "wfctl.cli.worktree_branches", lambda _: ["175-fix-a", "175-fix-b"]
    )
    _configure_tracker(repo_root, "github", _BOARD_VERBS)
    assert runner.invoke(app, ["issue", "stop", "175"]).exit_code == 0
    assert captured_argv == [["gh", "board", "stop", "175"]]


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


def _stub_gh(tmp_path: Path, state: str, current: str) -> Path:
    """A `gh` that answers the query with one row and records the mutation.

    The row is emitted with the same unit separator the script splits on, so an
    empty `current` reaches the parse as an empty field rather than a missing
    one — which is the shape a tab folded away.
    """
    calls = tmp_path / "calls"
    fake_gh = tmp_path / "gh"
    fake_gh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$*" >> "{calls}"\n'
        'case "$*" in\n'
        '  *"repo view"*) echo "owner repo" ;;\n'
        '  *mutation*) : ;;\n'
        f'  *) printf "{state}\\x1f{current}\\x1fPVTI_item\\x1fPVT_proj'
        '\\x1fPVTSSF_field\\x1fopt123\\n" ;;\n'
        'esac\n'
    )
    fake_gh.chmod(0o755)
    return calls


def _run_board_script(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                      *args: str) -> list[str]:
    """Run the shipped script against the stub; return the mutation calls."""
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    script = Path(_tracker.__file__).parent / "agents" / "trackers" / "github-board.sh"
    result = subprocess.run(
        ["bash", str(script), *args], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    calls = tmp_path / "calls"
    return [ln for ln in calls.read_text().splitlines() if "mutation" in ln]


@pytest.mark.parametrize("state,current,guard,writes", [
    ("OPEN", "Todo", (), True),
    ("OPEN", "", (), True),
    ("OPEN", "Code Review", (), True),
    ("CLOSED", "Done", (), False),
    ("CLOSED", "In Progress", ("--only-from", "In Progress"), False),
    ("OPEN", "In Progress", ("--only-from", "In Progress"), True),
    ("OPEN", "Code Review", ("--only-from", "In Progress"), False),
    ("OPEN", "", ("--only-from", "In Progress"), False),
])
def test_board_script_write_preconditions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    state: str, current: str, guard: tuple, writes: bool
) -> None:
    """One table for every precondition on the write, rather than one per verb.

    The rows without a guard are `start`, the rows with one are `stop`. Reviewers
    found the same structural weakness three times from different angles — the
    script fetches an issue's state and its current column, and each verb was
    consulting whichever half its own flag named. `stop` ignoring the column let
    it drag a card out of `Code Review`; `start` ignoring the state let a
    worktree for a closed issue move its card out of `Done`, which `stop` then
    declined to undo because the issue was closed.

    Both are gone because the closed rule stopped being a caller's flag. Keeping
    the whole table in one place is what makes the next one visible as a missing
    row rather than as a fourth report.
    """
    _stub_gh(tmp_path, state, current)
    mutation = _run_board_script(
        tmp_path, monkeypatch, "175", "In Progress" if not guard else "Todo", *guard
    )
    assert bool(mutation) is writes


def test_board_script_survives_an_item_whose_status_is_unset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An item on the board with no `Status` value must still be movable.

    That row comes back with an empty second field, and it is the population the
    script exists to move: 21 items on this project were in exactly that state
    before the board was reconciled by hand. Parsed on a tab — IFS whitespace,
    which bash folds a run of into one separator — the empty field vanishes and
    every id shifts one place left, so the mutation is sent an option id where a
    project id belongs. GitHub answers `Could not resolve to a node with the
    global id`, the hook swallows it, and the item silently does not move.

    The stub stands in for `gh` so the row can be forced; what is pinned is that
    each id arrives in the argument named for it.
    """
    calls = tmp_path / "calls"
    fake_gh = tmp_path / "gh"
    fake_gh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$*" >> "{calls}"\n'
        'case "$*" in\n'
        '  *"repo view"*) echo "owner repo" ;;\n'
        '  *mutation*) : ;;\n'
        # state, an unset column, then the four ids.
        '  *) printf "OPEN\\x1f\\x1fPVTI_item\\x1fPVT_proj\\x1fPVTSSF_field\\x1fopt123\\n" ;;\n'
        'esac\n'
    )
    fake_gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")

    script = Path(_tracker.__file__).parent / "agents" / "trackers" / "github-board.sh"
    result = subprocess.run(
        ["bash", str(script), "175", "In Progress"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr

    mutation = [ln for ln in calls.read_text().splitlines() if "mutation" in ln]
    assert len(mutation) == 1, calls.read_text()
    assert "project=PVT_proj" in mutation[0]
    assert "item=PVTI_item" in mutation[0]
    assert "field=PVTSSF_field" in mutation[0]
    assert "option=opt123" in mutation[0]


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
