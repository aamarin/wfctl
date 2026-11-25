"""Under Claude Code, `wfctl start`, `auto-approve on`, and the person-only
commands refuse when the repo's settings lack the worktree guard hook or an ask
rule wfctl ships.

A repo that commits `.claude/settings.json` gives every new worktree an
existing settings file, and an unattended install leaves an existing file
unchanged (`settings-edit-asks-first.md`). That worktree comes up with no guard
and no ask rules, so nothing refuses the forms the guard exists for, and Claude
Code doesn't ask before an accept, a sign-off, or `auto-approve on`.
"""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl import cli
from wfctl.cli import _protection_gaps, app

runner = CliRunner()


def _protected(root: Path, drop: str | None = None) -> Path:
    """Write the settings an attended install would, less any entry
    containing `drop`."""
    copy = cli._load_settings(root, cli.SETTINGS_PATH)
    assert copy.settings is not None
    settings = copy.settings
    for event, command in cli.MANAGED_HOOKS:
        cli.install.merge_hook(settings, event, command, cli._hook_matcher("claude", event))
    for rule in cli._managed_permissions("claude"):
        cli.install.merge_permission(settings, rule.rule, rule.kind)
    if drop is not None:
        settings["permissions"]["ask"] = [
            r for r in settings["permissions"]["ask"] if drop not in r
        ]
        if drop == "guard":
            cli.install.remove_hooks(settings, cli.PRETOOL_EVENT)
    path = root / cli.SETTINGS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings))
    return path


def test_a_full_install_has_no_gaps(tmp_path: Path) -> None:
    _protected(tmp_path)

    assert _protection_gaps(tmp_path) == []


@pytest.mark.parametrize(("drop", "gap"), [
    ("guard", "the worktree guard hook"),
    ("arch accept", "the ask rule Bash(wfctl arch accept:*)"),
    ("review sign-off", "the ask rule Bash(wfctl review sign-off:*)"),
    ("approve-imports", "the ask rule Bash(wfctl arch approve-imports:*)"),
    ("wfctl auto-approve on:*", "the ask rule Bash(wfctl auto-approve on:*)"),
])
def test_each_missing_protection_is_named(tmp_path: Path, drop: str, gap: str) -> None:
    _protected(tmp_path, drop)

    assert gap in _protection_gaps(tmp_path)


def test_a_committed_file_without_wfctls_entries_lacks_all_of_them(tmp_path: Path) -> None:
    """The case the record missed: an existing file holding only the
    project's own entries."""
    path = tmp_path / cli.SETTINGS_PATH
    path.parent.mkdir()
    path.write_text(json.dumps({"permissions": {"allow": ["Bash(make:*)"]}}))

    gaps = _protection_gaps(tmp_path)

    assert "the worktree guard hook" in gaps
    assert "the ask rule Bash(wfctl arch accept:*)" in gaps


def test_a_rule_only_in_the_local_settings_file_does_not_count(tmp_path: Path) -> None:
    """The guard reads only `settings.json`, so the check does too. If the two
    read different files, they could disagree about whether a rule is there."""
    path = _protected(tmp_path, "arch accept")
    local = path.parent / "settings.local.json"
    local.write_text(json.dumps({"permissions": {"ask": ["Bash(wfctl arch accept:*)"]}}))

    assert "the ask rule Bash(wfctl arch accept:*)" in _protection_gaps(tmp_path)


def test_an_unparseable_settings_file_is_a_gap(tmp_path: Path) -> None:
    path = tmp_path / cli.SETTINGS_PATH
    path.parent.mkdir()
    path.write_text("{ not json")

    assert _protection_gaps(tmp_path)[0].startswith("a readable .claude/settings.json")


COMMANDS = [
    ["start"],
    ["auto-approve", "on"],
    ["arch", "accept", "a-decision"],
    ["review", "sign-off", "--head", "abc1234"],
    ["arch", "approve-imports", "--head", "abc1234"],
]


def _name(args: list[str]) -> str:
    return "wfctl " + " ".join(a for a in args if not a.startswith("-") and a not in (
        "a-decision", "abc1234"))


@pytest.mark.parametrize("args", COMMANDS)
def test_each_command_refuses_under_claude_code_without_the_protections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, args: list[str],
) -> None:
    """Refused whether or not a terminal is attached, since a faked terminal
    is one of the forms the missing guard would have refused."""
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setattr("wfctl.cli._get_repo_root_or_exit", lambda: tmp_path)
    monkeypatch.setattr("wfctl.cli._at_terminal", lambda: True)
    monkeypatch.setattr("wfctl.cli._refuse_unless_the_issue_allows_a_session", lambda: None)

    result = runner.invoke(app, args)

    assert result.exit_code == 1
    assert f"✗ {_name(args)} needs wfctl's protections in" in result.output
    assert "install-skills --agent claude" in result.output


def test_the_install_command_carries_the_runner_and_recorded_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bare `wfctl install-skills` would install the released wheel over a
    checkout that installs from source, as this repo does with `uv run`."""
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setattr("wfctl.cli._get_repo_root_or_exit", lambda: tmp_path)
    monkeypatch.setattr("wfctl.cli._runner", lambda root: "uv run wfctl")
    monkeypatch.setattr(
        "wfctl.cli._load_manifest", lambda root: {"claude": {"source": "/src [v2]"}}
    )

    result = runner.invoke(app, ["auto-approve", "on"])

    # No backslash before `[`: the line prints without markup, so an escape
    # meant for rich would land inside the quotes and name another path.
    assert "    uv run wfctl install-skills --agent claude --from '/src [v2]'" in result.output


def test_a_guard_hook_on_the_wrong_tool_is_a_gap(tmp_path: Path) -> None:
    """A guard scoped to a tool the agent's commands never reach refuses
    nothing, so it can't count as protection."""
    path = _protected(tmp_path)
    settings = json.loads(path.read_text())
    for group in settings["hooks"][cli.PRETOOL_EVENT]:
        group["matcher"] = "Read"
    path.write_text(json.dumps(settings))

    assert "the worktree guard hook's tool matcher" in _protection_gaps(tmp_path)


def test_outside_claude_code_nothing_is_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A person at their own terminal has no ask rules to need."""
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.setattr("wfctl.cli._get_repo_root_or_exit", lambda: tmp_path)

    cli._refuse_unprotected("wfctl start")


def test_a_leftover_hook_ahead_of_the_guard_does_not_answer_for_its_matcher(
    tmp_path: Path,
) -> None:
    """The matcher was read from the first managed group on the event. A stale
    wfctl hook placed first under `Bash` made a guard scoped to `Read` pass."""
    path = _protected(tmp_path)
    settings = json.loads(path.read_text())
    for group in settings["hooks"][cli.PRETOOL_EVENT]:
        group["matcher"] = "Read"
    settings["hooks"][cli.PRETOOL_EVENT].insert(0, {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "wfctl hook retired-check"}],
    })
    path.write_text(json.dumps(settings))

    assert "the worktree guard hook's tool matcher" in _protection_gaps(tmp_path)


def test_a_file_that_turns_hooks_off_is_a_gap(tmp_path: Path) -> None:
    """Claude Code runs no hook under `disableAllHooks`, so every entry being
    present still leaves no guard. Install doesn't change the setting, so the
    gap says to remove it."""
    path = _protected(tmp_path)
    settings = json.loads(path.read_text())
    settings["disableAllHooks"] = True
    path.write_text(json.dumps(settings))

    gaps = _protection_gaps(tmp_path)

    assert len(gaps) == 1
    assert "disableAllHooks" in gaps[0]


def test_a_removed_recorded_rule_gets_the_force_form(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A plain install refuses when a rule wfctl recorded was removed, so the
    refusal can't send the user there."""
    _protected(tmp_path, "arch accept")
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setattr("wfctl.cli._get_repo_root_or_exit", lambda: tmp_path)
    monkeypatch.setattr("wfctl.cli._runner", lambda root: "wfctl")
    monkeypatch.setattr("wfctl.cli._load_manifest", lambda root: {"claude": {
        "permissions": [{
            "path": cli.SETTINGS_PATH, "rule": "Bash(wfctl arch accept:*)",
            "kind": "ask", "added": True,
        }],
    }})

    result = runner.invoke(app, ["auto-approve", "on"])

    assert "    wfctl install-skills --agent claude --force" in result.output


def _bob_protected(root: Path, matcher: str | None = None) -> Path:
    """Write the `.bob/settings.json` an attended `--agent bob` install would,
    with the guard's matcher swapped for `matcher` when one is given."""
    settings: dict = {}
    for event, command in cli.MANAGED_HOOKS:
        cli.install.merge_hook(
            settings, event, command, cli._hook_matcher("bob", event)
        )
    if matcher is not None:
        for group in settings["hooks"][cli.PRETOOL_EVENT]:
            group["matcher"] = matcher
    path = root / cli.BOB_SETTINGS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings))
    return path


def test_a_full_bob_install_has_no_gaps(tmp_path: Path) -> None:
    """Bob Shell has no ask rules to need, so the guard hook is the whole
    of what its install has to carry."""
    _bob_protected(tmp_path)

    assert _protection_gaps(tmp_path, "bob") == []


def test_a_bob_file_without_the_guard_lacks_it(tmp_path: Path) -> None:
    """The gap #864's security review found: a committed `.bob/settings.json`
    gives a new worktree an existing file, and the unattended install adds no
    guard to it."""
    path = tmp_path / cli.BOB_SETTINGS_PATH
    path.parent.mkdir()
    path.write_text(json.dumps({"tools": {"allowed": ["git status"]}}))

    assert _protection_gaps(tmp_path, "bob") == ["the worktree guard hook"]


def test_a_bob_guard_on_claude_codes_tool_name_is_a_gap(tmp_path: Path) -> None:
    """Bob Shell names its shell tool `run_shell_command`, so a guard matching
    Claude Code's `Bash` never runs there."""
    _bob_protected(tmp_path, matcher="Bash")

    assert _protection_gaps(tmp_path, "bob") == [
        "the worktree guard hook's tool matcher"
    ]


def test_bob_reads_its_own_file_not_claude_codes(tmp_path: Path) -> None:
    """A repo protected for Claude Code isn't protected for Bob Shell, which
    reads no hook from `.claude/`."""
    _protected(tmp_path)

    assert _protection_gaps(tmp_path, "bob") == ["the worktree guard hook"]


@pytest.mark.parametrize("args", COMMANDS)
def test_each_command_refuses_under_bob_shell_without_the_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, args: list[str],
) -> None:
    """`CLAUDECODE` is set too, as it is for a Bob Shell started from Claude
    Code's shell, and the check still reads Bob Shell's file."""
    _protected(tmp_path)
    monkeypatch.setenv("BOBSHELL_CLI", "1")
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setattr("wfctl.cli._get_repo_root_or_exit", lambda: tmp_path)
    monkeypatch.setattr("wfctl.cli._at_terminal", lambda: True)
    monkeypatch.setattr("wfctl.cli._refuse_unless_the_issue_allows_a_session", lambda: None)
    monkeypatch.setattr("wfctl.cli._runner", lambda root: "wfctl")

    result = runner.invoke(app, args)

    assert result.exit_code == 1
    assert f"✗ {_name(args)} needs wfctl's protections in" in result.output
    assert cli.BOB_SETTINGS_PATH in result.output
    assert "    wfctl install-skills --agent bob" in result.output


def test_a_guarded_bob_worktree_is_let_through(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _bob_protected(tmp_path)
    monkeypatch.setenv("BOBSHELL_CLI", "1")
    monkeypatch.setattr("wfctl.cli._get_repo_root_or_exit", lambda: tmp_path)

    cli._refuse_unprotected("wfctl start")


def test_with_both_markers_set_both_files_are_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Claude Code started from Bob Shell inherits `BOBSHELL_CLI`, and a Bob
    Shell started from Claude Code inherits `CLAUDECODE`. wfctl can't tell
    which one is running the command, so a gap in either file refuses. Both
    security reviewers on run 005 found the Claude-inside-Bob case passing
    with no ask rules."""
    _bob_protected(tmp_path)
    monkeypatch.setenv("BOBSHELL_CLI", "1")
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setattr("wfctl.cli._get_repo_root_or_exit", lambda: tmp_path)
    monkeypatch.setattr("wfctl.cli._runner", lambda root: "wfctl")

    result = runner.invoke(app, ["auto-approve", "on"])

    assert result.exit_code == 1
    assert cli.SETTINGS_PATH in result.output
    assert "    wfctl install-skills --agent claude" in result.output


def test_a_codex_agent_started_from_claude_code_is_not_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Codex inherits `CLAUDECODE` from Claude Code's shell but reads none of
    its settings, so `.claude/settings.json` protects nothing it runs. Run
    006's s1 found the check reading that file once it looked at
    `CLAUDECODE` alone, which refused `wfctl start` in a Codex-only repo."""
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("CODEX_THREAD_ID", "x")
    monkeypatch.setattr("wfctl.cli._get_repo_root_or_exit", lambda: tmp_path)

    cli._refuse_unprotected("wfctl start")


def test_a_codex_agent_started_from_bob_shell_is_not_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Codex inherits `BOBSHELL_CLI` from Bob Shell's shell but reads none of
    its settings. Code reviewer c2 found `wfctl start` refused in a Codex-only
    repo with the remedy `install-skills --agent bob`."""
    monkeypatch.setenv("BOBSHELL_CLI", "1")
    monkeypatch.setenv("CODEX_THREAD_ID", "x")
    monkeypatch.setattr("wfctl.cli._get_repo_root_or_exit", lambda: tmp_path)

    cli._refuse_unprotected("wfctl start")


@pytest.mark.parametrize("contents", [
    "{ not json",
    json.dumps({"disableAllHooks": True}),
])
def test_a_gap_install_cannot_fix_gets_no_install_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, contents: str,
) -> None:
    """Install leaves an unreadable file alone and never changes
    `disableAllHooks`, so sending the user to install would loop them between
    install and the refusal. Code reviewer c1 found both cases."""
    path = _protected(tmp_path)
    if contents.startswith("{ not"):
        path.write_text(contents)
    else:
        settings = json.loads(path.read_text())
        settings.update(json.loads(contents))
        path.write_text(json.dumps(settings))
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setattr("wfctl.cli._get_repo_root_or_exit", lambda: tmp_path)

    result = runner.invoke(app, ["auto-approve", "on"])

    assert result.exit_code == 1
    assert "install-skills" not in result.output
    assert "Fix the file yourself, then try again." in result.output


@pytest.mark.parametrize("contents", ["", "  \n"])
def test_a_blank_settings_file_gets_the_install_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, contents: str,
) -> None:
    """Install reads a blank settings file as `{}` and fills it after asking,
    so the refusal has to send the user to install. Code reviewers c1 and c2
    on run 004 found it read the file as unreadable instead, and said to fix
    it by hand."""
    path = _protected(tmp_path)
    path.write_text(contents)
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setattr("wfctl.cli._get_repo_root_or_exit", lambda: tmp_path)

    result = runner.invoke(app, ["auto-approve", "on"])

    assert result.exit_code == 1
    assert "install-skills --agent claude" in result.output
    assert "Fix the file yourself" not in result.output
