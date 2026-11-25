"""Install asks before it changes an existing settings file (#859).

`settings-edit-asks-first.md` lets `install-skills` change an existing
`.claude/settings.json` or `.bob/settings.json` only after the user says yes at
a terminal, and never on `--yes`, which the agent passes itself. Each "Must
keep catching" and "Must let through" item in that record has a test here.

`_interactive` is patched in every test, since `CliRunner` never has a
terminal and the question is what these tests are about. Attended runs pass
`--yes` too, so the tracker and overwrite prompts stay out of the way, which
also shows `--yes` doesn't answer the settings question.
"""
from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from wfctl import cli
from wfctl.cli import (
    ASK_RULES,
    DENY_RULE,
    GUARD_HOOK_COMMAND,
    MANAGED_HOOKS,
    _HOOK_GONE,
    _HOOK_GONE_PREFIX,
    _HOOK_OUTDATED,
    _WORKTREE_GUARD,
    _load_settings,
    _managed_permissions,
    _rule_removed,
    _run_settings_passes,
    app,
)

runner = CliRunner()

# The `--project` ask rule 0.31.0 shipped and this wfctl retires.
_OLD_RULE = "Bash(uv run --project * wfctl auto-approve on:*)"
# The `Stop` command a wfctl before #476 installed, which the hooks pass prunes.
_OLD_STOP = "wfctl hook response-shape 2>/dev/null || true"
# Every change a fresh `.claude/settings.json` gets: three hooks and eight rules.
_FRESH_CHANGES = len(MANAGED_HOOKS) + len(_managed_permissions("claude"))


def _root() -> Path:
    return Path(os.environ["WFCTL_REPO_ROOT"])


def _claude(root: Path) -> Path:
    return root / ".claude" / "settings.json"


def _bob(root: Path) -> Path:
    return root / ".bob" / "settings.json"


def _manifest_path(root: Path) -> Path:
    return root / ".wf-skills-manifest.json"


def _manifest(root: Path) -> dict:
    return json.loads(_manifest_path(root).read_text())


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


class _Prompt:
    """The settings question, patched. Counts calls, and answers or raises."""

    def __init__(self) -> None:
        self.calls = 0
        self.answer: bool | BaseException = True
        self.before: Callable[[], None] | None = None

    def __call__(self, *args: object, **kwargs: object) -> bool:
        self.calls += 1
        if self.before is not None:
            self.before()
        if isinstance(self.answer, BaseException):
            raise self.answer
        return self.answer


@pytest.fixture
def terminal(agent_dir: Path, monkeypatch: pytest.MonkeyPatch) -> _Prompt:
    """A user at a terminal, answering yes unless the test says otherwise."""
    prompt = _Prompt()
    monkeypatch.setattr(cli, "_interactive", lambda: True)
    monkeypatch.setattr(typer, "confirm", prompt)
    return prompt


@pytest.fixture
def no_terminal(agent_dir: Path, monkeypatch: pytest.MonkeyPatch) -> _Prompt:
    """No terminal attached. The prompt is patched only to count: any call is a bug."""
    prompt = _Prompt()
    monkeypatch.setattr(cli, "_interactive", lambda: False)
    monkeypatch.setattr(typer, "confirm", prompt)
    return prompt


@pytest.fixture
def writes(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """Count `_write_settings` calls per settings file."""
    counts: dict[str, int] = {}
    real = cli._write_settings

    def counting(path: Path, settings: dict) -> None:
        key = f"{path.parent.name}/{path.name}"
        counts[key] = counts.get(key, 0) + 1
        real(path, settings)

    monkeypatch.setattr(cli, "_write_settings", counting)
    return counts


def _install(*args: str, input: str | None = None) -> str:
    result = runner.invoke(app, ["install-skills", *args], input=input)
    assert result.exit_code == 0, result.output
    return result.output


def _installed_then(root: Path, edit: Callable[[dict], None], agent: str = "claude") -> bytes:
    """Install `agent` into a repo with no settings file, so it's created without
    a question, then apply `edit` to it. Returns the edited bytes."""
    _install("--agent", agent, "--yes")
    path = _claude(root) if agent == "claude" else _bob(root)
    settings = json.loads(path.read_text())
    edit(settings)
    _write_json(path, settings)
    return path.read_bytes()


def _drop_guard(settings: dict) -> None:
    del settings["hooks"]["PreToolUse"]


def _drop_guard_and_deny(settings: dict) -> None:
    del settings["hooks"]["PreToolUse"]
    settings["permissions"]["deny"].remove(DENY_RULE)


def _forget_receipt(root: Path, rule: str) -> None:
    manifest = _manifest(root)
    manifest["claude"]["permissions"] = [
        r for r in manifest["claude"]["permissions"] if r["rule"] != rule
    ]
    _write_json(_manifest_path(root), manifest)


def _add_retired_rule(root: Path, rule: str = _OLD_RULE, *, added: bool = True) -> None:
    """Leave the repo as 0.31.0 left it: a retired rule in the file, with its receipt."""
    path = _claude(root)
    settings = json.loads(path.read_text())
    settings["permissions"]["ask"].append(rule)
    _write_json(path, settings)
    manifest = _manifest(root)
    manifest["claude"]["permissions"].append(
        {"path": ".claude/settings.json", "rule": rule, "kind": "ask", "added": added}
    )
    _write_json(_manifest_path(root), manifest)


# --- Phase 2: the shared copy ------------------------------------------------


def test_load_settings_reads_each_kind_of_file(agent_dir: Path) -> None:
    """A zero-byte file is read as `{}` so install asks about it, but it isn't
    `parsed`, so a rule missing from it isn't one the user removed. A missing
    file isn't `existed`, so install creates it without a question."""
    root = _root()
    rel = ".claude/settings.json"

    missing = _load_settings(root, rel)
    assert (missing.existed, missing.settings, missing.parsed) == (False, {}, False)
    assert missing.read_bytes is None

    _claude(root).parent.mkdir(parents=True)
    for raw in (b"", b"  \n\t\n"):
        _claude(root).write_bytes(raw)
        empty = _load_settings(root, rel)
        assert (empty.existed, empty.settings, empty.parsed) == (True, {}, False)
        assert empty.read_bytes == raw

    _claude(root).write_text('{"a": 1}\n')
    valid = _load_settings(root, rel)
    assert (valid.existed, valid.settings, valid.parsed) == (True, {"a": 1}, True)
    assert valid.read_bytes == b'{"a": 1}\n'

    _claude(root).write_text("{not json")
    broken = _load_settings(root, rel)
    assert broken.settings is None and broken.problem and not broken.parsed


@pytest.mark.parametrize(
    "state, receipts, expected",
    [
        ("no file", [{"added": True}], False),
        ("zero bytes", [{"added": True}], False),
        ("unparseable", [{"added": True}], False),
        ("dangling link", [{"added": True}], False),
        ("rule present", [{"added": True}], False),
        ("rule removed", [], False),
        ("rule removed", [{"added": True}], True),
        ("rule removed", [{"added": False}], True),
    ],
)
def test_a_rule_counts_as_removed_only_from_a_parsed_file_with_a_receipt(
    agent_dir: Path, state: str, receipts: list[dict], expected: bool
) -> None:
    """A fresh clone with a committed manifest has every receipt and no
    settings file, and `post_create` runs install there unattended. Reading
    that, a zero-byte file, an unparseable one, or a dangling link as a removed
    rule refused the one install that most needs to run."""
    root = _root()
    path = _claude(root)
    path.parent.mkdir(parents=True)
    if state == "zero bytes":
        path.write_bytes(b"")
    elif state == "unparseable":
        path.write_text("{oops")
    elif state == "dangling link":
        path.symlink_to(root / "nowhere.json")
    elif state == "rule present":
        _write_json(path, {"permissions": {"deny": [DENY_RULE]}})
    elif state == "rule removed":
        _write_json(path, {"permissions": {"deny": []}})
    copy = _load_settings(root, ".claude/settings.json")
    assert _rule_removed(root, copy, receipts, DENY_RULE, "deny") is expected


def test_install_saves_each_settings_file_once(
    terminal: _Prompt, writes: dict[str, int]
) -> None:
    """Every pass edits one copy, and the save step writes it once. Before
    #859 the hooks and rules passes saved once per entry, up to eleven saves
    of one file, each of which would have needed its own question (SC-003)."""
    root = _root()
    _write_json(_claude(root), {"permissions": {"allow": ["Bash(npm test)"]}})

    output = _install("--agent", "claude", "--yes")

    assert writes == {".claude/settings.json": 1}
    assert terminal.calls == 1
    assert f"✓ .claude/settings.json updated ({_FRESH_CHANGES} changes)" in output


# --- US1: approve settings changes at a terminal -----------------------------


def test_a_yes_at_a_terminal_asks_once_and_saves_once(
    terminal: _Prompt, writes: dict[str, int]
) -> None:
    """Must let through 1. A hook and a rule pending in one file are one
    question and one save."""
    root = _root()
    _installed_then(root, _drop_guard_and_deny)
    # A rule with a receipt that's missing is one the user removed, which
    # install refuses over. Without one, it's a rule install adds.
    _forget_receipt(root, DENY_RULE)
    writes.clear()

    output = _install("--agent", "claude", "--yes")

    assert terminal.calls == 1
    assert writes == {".claude/settings.json": 1}
    settings = json.loads(_claude(root).read_text())
    assert DENY_RULE in settings["permissions"]["deny"]
    assert "PreToolUse" in settings["hooks"]
    assert "✓ .claude/settings.json updated (2 changes)" in output


def test_a_no_at_a_terminal_leaves_the_file_and_its_receipts(terminal: _Prompt) -> None:
    """US1 scenario 4. A no leaves the bytes and the manifest's receipts for
    that file as they were, so the manifest still describes the file, and the
    next install at a terminal asks about the same changes again."""
    root = _root()
    before = _installed_then(root, _drop_guard)
    receipts = {k: _manifest(root)["claude"][k] for k in ("merged", "permissions")}
    terminal.answer = False

    output = _install("--agent", "claude", "--yes")

    assert _claude(root).read_bytes() == before
    assert {k: _manifest(root)["claude"][k] for k in ("merged", "permissions")} == receipts
    assert "⚠ .claude/settings.json left unchanged: 1 change needs your yes." in output
    assert "Run in your terminal: wfctl install-skills --agent claude" in output

    again = _install("--agent", "claude", "--yes")
    assert terminal.calls == 2
    assert "+ hook  PreToolUse wfctl hook worktree-guard" in again


def test_an_empty_answer_at_the_real_prompt_is_a_no(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-005. The default is no, so pressing enter changes nothing. This
    runs the real `typer.confirm`, fed an empty line."""
    root = _root()
    before = _installed_then(root, _drop_guard)
    monkeypatch.setattr(cli, "_interactive", lambda: True)

    output = _install("--agent", "claude", "--yes", input="\n")

    assert "Apply them? [y/N]:" in output
    assert _claude(root).read_bytes() == before
    assert "left unchanged" in output


def test_the_question_lists_each_change_with_its_reason(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """US1 scenario 2, against `contracts/install-question.md`. The user is
    deciding about a file they own, so each line says what the entry is for,
    or that wfctl no longer ships it."""
    root = _root()
    _installed_then(root, _drop_guard)
    _add_retired_rule(root)
    monkeypatch.setattr(cli, "_interactive", lambda: True)

    output = _install("--agent", "claude", "--yes", input="n\n")

    assert (
        ".claude/settings.json needs these changes:\n"
        "  + hook      PreToolUse wfctl hook worktree-guard\n"
        "              nothing stops a Bash call reaching into a sibling worktree\n"
        f"  - ask rule  {_OLD_RULE}\n"
        "              wfctl no longer ships this\n"
        "Apply them? [y/N]:"
    ) in output


def test_every_change_kind_carries_a_reason(agent_dir: Path) -> None:
    """FR-013. A change with no reason gives the user nothing to decide on.
    One settings file needing every kind of change, so a new kind added
    without a reason fails here."""
    root = _root()
    _write_json(_claude(root), {
        "hooks": {
            "Stop": [{"hooks": [{"type": "command", "command": _OLD_STOP}]}],
            "PreToolUse": [
                {"matcher": "Read", "hooks": [{"type": "command", "command": GUARD_HOOK_COMMAND}]}
            ],
        },
        "permissions": {"ask": [_OLD_RULE]},
    })
    _write_json(_bob(root), {"tools": {"allowed": ["read_file"]}})
    manifest = {
        "claude": {"permissions": [
            {"path": ".claude/settings.json", "rule": _OLD_RULE, "kind": "ask", "added": True}
        ]},
        "bob": {"tools": [{"path": ".bob/settings.json", "entry": "read_file", "added": True}]},
    }

    changes = []
    for agent in ("claude", "bob"):
        copies = {rel: _load_settings(root, rel) for rel in cli._settings_paths(agent)}
        _run_settings_passes(root, agent, manifest, copies, force=False)
        changes += [c for copy in copies.values() for c in copy.changes]

    assert {(c.sign, c.kind) for c in changes} >= {
        ("+", "hook"), ("~", "hook"), ("-", "hook"), ("+", "deny rule"),
        ("+", "ask rule"), ("-", "ask rule"), ("-", "tool approval"),
    }
    assert all(c.why.strip() for c in changes), changes


@pytest.mark.parametrize("matcher, command, why", [
    ("Bash", f"{GUARD_HOOK_COMMAND} --older-flag", _HOOK_OUTDATED),
    ("Read", GUARD_HOOK_COMMAND, _HOOK_GONE[_WORKTREE_GUARD].removeprefix(_HOOK_GONE_PREFIX)),
])
def test_an_updated_hook_gets_the_cost_line_only_when_it_doesnt_fire(
    agent_dir: Path, matcher: str, command: str, why: str,
) -> None:
    """A guard whose command is only out of date still refuses what it should,
    so the cost of losing it doesn't apply. Code reviewer c2 on run 004 found
    the question saying "nothing stops a Bash call reaching into a sibling
    worktree" for every update. A guard scoped to `Read` never sees a Bash
    call, so for that one the cost line is right."""
    root = _root()
    _write_json(_claude(root), {"hooks": {"PreToolUse": [
        {"matcher": matcher, "hooks": [{"type": "command", "command": command}]}
    ]}})
    copies = {rel: _load_settings(root, rel) for rel in cli._settings_paths("claude")}

    _run_settings_passes(root, "claude", {}, copies, force=False)

    updated = [c for copy in copies.values() for c in copy.changes if c.sign == "~"]
    assert [c.why for c in updated] == [why]


def test_every_hook_cost_starts_with_the_prefix_the_question_trims() -> None:
    """The question trims "is gone — " off a hook's cost line. A new hook
    whose line doesn't start with it would print "is gone" with no hook name
    before it."""
    assert all(line.startswith(_HOOK_GONE_PREFIX) for line in _HOOK_GONE.values())


@pytest.mark.parametrize("interrupt", [typer.Abort(), EOFError(), KeyboardInterrupt()])
def test_an_interrupted_question_leaves_the_file_and_records_the_skills(
    terminal: _Prompt, interrupt: BaseException
) -> None:
    """Ctrl-C or Ctrl-D at the question is a no. Raising instead skipped the
    manifest write, and the skills already copied had no record."""
    root = _root()
    before = _installed_then(root, _drop_guard)
    # Remove the command and its receipt, so only this run can record it.
    command = ".claude/commands/test-cmd.md"
    (root / command).unlink()
    manifest = _manifest(root)
    manifest["claude"]["items"] = [
        i for i in manifest["claude"]["items"] if i["path"] != command
    ]
    _write_json(_manifest_path(root), manifest)
    terminal.answer = interrupt

    result = runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    assert result.exit_code == 0, result.output
    assert _claude(root).read_bytes() == before
    assert (root / command).is_file()
    paths = {i["path"] for i in _manifest(root)["claude"]["items"]}
    assert command in paths
    assert "left unchanged" in result.output


def test_a_file_changed_during_the_question_is_not_saved_over(terminal: _Prompt) -> None:
    """The user can edit the file while the question waits, through Claude
    Code's `/permissions` for one. Saving wfctl's older copy over it would
    discard their edit."""
    root = _root()
    _installed_then(root, _drop_guard)
    edited = b'{"permissions": {"allow": ["Bash(make)"]}}\n'
    terminal.before = lambda: _claude(root).write_bytes(edited)

    output = _install("--agent", "claude", "--yes")

    assert _claude(root).read_bytes() == edited
    changed = output.index(
        "⚠ .claude/settings.json changed while the question was open, "
        "so wfctl didn't save over it."
    )
    assert output.index(".claude/settings.json left unchanged") > changed
    # The user already said yes, so the line can't ask for it again.
    assert "need your yes" not in output
    assert "needs your yes" not in output
    assert ".claude/settings.json left unchanged: 1 change not saved." in output


def test_a_failed_save_keeps_the_old_file_and_its_receipts(
    terminal: _Prompt, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec edge case "Saving the file fails". The rest of the install has
    landed, so it exits 0, and the manifest keeps describing the file as it
    still is."""
    root = _root()
    before = _installed_then(root, _drop_guard)
    receipts = _manifest(root)["claude"]["merged"]

    def refuse(path: Path, settings: dict) -> None:
        raise PermissionError(13, "Permission denied", str(path))

    monkeypatch.setattr(cli, "_write_settings", refuse)
    output = _install("--agent", "claude", "--yes")

    assert _claude(root).read_bytes() == before
    assert _manifest(root)["claude"]["merged"] == receipts
    assert output.index("Permission denied") < output.index("left unchanged")


def test_rule_text_from_a_receipt_prints_literally(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A removed rule's text comes from manifest receipts, which a person can
    edit. Printed as rich markup, `[bold]` would vanish and `[/x]` would raise."""
    root = _root()
    _installed_then(root, lambda s: None)
    rule = "Bash([bold]x[/bold]:*)"
    _add_retired_rule(root, rule)
    monkeypatch.setattr(cli, "_interactive", lambda: True)

    output = _install("--agent", "claude", "--yes", input="n\n")

    assert f"- ask rule  {rule}" in output


def test_a_zero_byte_settings_file_is_asked_about_and_filled(terminal: _Prompt) -> None:
    """Spec edge case "The settings file is empty". It exists, so it's the
    user's and gets the question, and a yes writes every managed entry."""
    root = _root()
    _claude(root).parent.mkdir(parents=True)
    _claude(root).write_bytes(b"")

    _install("--agent", "claude", "--yes")

    assert terminal.calls == 1
    settings = json.loads(_claude(root).read_text())
    assert DENY_RULE in settings["permissions"]["deny"]
    assert set(ASK_RULES) <= set(settings["permissions"]["ask"])


def test_each_agent_install_asks_about_its_own_file(terminal: _Prompt) -> None:
    """US1 scenario 5. `--agent` takes one value, so each run touches one
    agent's settings file and asks once about it."""
    root = _root()
    _write_json(_claude(root), {"x": 1})
    _write_json(_bob(root), {"x": 1})

    bob = _install("--agent", "bob", "--yes")
    assert terminal.calls == 1
    assert ".bob/settings.json needs these changes:" in bob
    assert ".claude/settings.json" not in bob

    claude = _install("--agent", "claude", "--yes")
    assert terminal.calls == 2
    assert ".claude/settings.json needs these changes:" in claude
    assert ".bob/settings.json" not in claude


# --- US2: an unattended install leaves the file alone -------------------------


def _keep_catching_yes_adds(root: Path) -> list[str]:
    _write_json(_claude(root), {"permissions": {"allow": ["Bash(npm test)"]}})
    return ["--yes", "--agent", "claude"]


def _keep_catching_devnull(root: Path) -> list[str]:
    _write_json(_claude(root), {"permissions": {"allow": ["Bash(npm test)"]}})
    return ["--agent", "claude"]


def _keep_catching_prune(root: Path) -> list[str]:
    _write_json(_claude(root), {"permissions": {"allow": ["Bash(npm test)"]}})
    return ["--prune", "--yes", "--agent", "claude"]


def _keep_catching_force(root: Path) -> list[str]:
    _installed_then(root, lambda s: s["permissions"]["deny"].remove(DENY_RULE))
    return ["--force", "--yes", "--agent", "claude"]


def _keep_catching_retire(root: Path) -> list[str]:
    _installed_then(root, lambda s: None)
    _add_retired_rule(root)
    return ["--yes", "--agent", "claude"]


def _keep_catching_bob(root: Path) -> list[str]:
    _write_json(_bob(root), {"x": 1})
    return ["--yes", "--agent", "bob"]


@pytest.mark.parametrize(
    "setup",
    [
        _keep_catching_yes_adds,
        _keep_catching_devnull,
        _keep_catching_prune,
        _keep_catching_force,
        _keep_catching_retire,
        _keep_catching_bob,
    ],
    ids=["yes-adds", "stdin-devnull", "prune", "force", "retire", "bob"],
)
def test_an_unattended_install_never_changes_an_existing_settings_file(
    no_terminal: _Prompt, setup: Callable[[Path], list[str]]
) -> None:
    """SC-001, one per "Must keep catching" item. Each command is one an
    agent or a hook runs with nobody at a terminal, and each would change a
    file the user owns."""
    root = _root()
    args = setup(root)
    path = _bob(root) if "bob" in args else _claude(root)
    before = path.read_bytes()

    result = runner.invoke(app, ["install-skills", *args], input="")

    assert result.exit_code == 0, result.output
    assert path.read_bytes() == before
    assert no_terminal.calls == 0


def test_an_unattended_install_warns_once_and_still_copies_the_skills(
    no_terminal: _Prompt,
) -> None:
    """US2 scenarios 2 and 3. The skills land either way, and the warning
    names the command for the user to run in their own terminal."""
    root = _root()
    _write_json(_claude(root), {"permissions": {"allow": ["Bash(npm test)"]}})

    output = _install("--agent", "claude", "--yes")

    assert output.count("left unchanged") == 1
    assert (
        f"⚠ .claude/settings.json left unchanged: {_FRESH_CHANGES} changes need your yes.\n"
        "  Run in your terminal: wfctl install-skills --agent claude"
    ) in output
    assert (root / ".claude" / "commands" / "test-cmd.md").exists()
    assert (root / ".agents" / "skills" / "test-skill" / "SKILL.md").exists()


# --- US3: a new worktree still gets its settings file -------------------------


def test_a_missing_settings_file_is_created_without_a_question(no_terminal: _Prompt) -> None:
    """Must let through 2. A new worktree has no settings file, and
    `post_create` runs install with nobody watching. Without the file the
    worktree guard isn't installed at all. The change list still prints, so
    the `cd` deny rule's reason is in front of the user."""
    root = _root()

    output = _install("--agent", "claude", "--yes")

    assert no_terminal.calls == 0
    settings = json.loads(_claude(root).read_text())
    assert DENY_RULE in settings["permissions"]["deny"]
    assert "PreToolUse" in settings["hooks"]
    assert output.index("+ deny rule  Bash(cd:*)") < output.index(
        f"✓ .claude/settings.json created ({_FRESH_CHANGES} changes)"
    )
    assert "Apply them?" not in output


def test_a_committed_manifest_with_no_settings_file_gets_every_rule(
    no_terminal: _Prompt,
) -> None:
    """A fresh clone carries every receipt and no `.claude/`. The file is
    created with every receipted rule rather than read as rules the user
    removed."""
    root = _root()
    _write_json(_manifest_path(root), {"claude": {"items": [], "permissions": [
        {"path": ".claude/settings.json", "rule": m.rule, "kind": m.kind, "added": True}
        for m in _managed_permissions("claude")
    ]}})

    _install("--agent", "claude", "--yes")

    settings = json.loads(_claude(root).read_text())
    present = set(settings["permissions"]["deny"]) | set(settings["permissions"]["ask"])
    assert {m.rule for m in _managed_permissions("claude")} <= present


def test_an_install_that_changes_no_settings_file_says_nothing_about_one(
    no_terminal: _Prompt,
) -> None:
    """Must let through 3. `/start-session` refreshes skills with `--yes` and
    no terminal, and with every entry already in place there's nothing to
    ask about or warn about."""
    root = _root()
    _install("--agent", "claude", "--yes")

    output = _install("--agent", "claude", "--yes")

    assert "settings.json" not in output
    assert (root / ".claude" / "commands" / "test-cmd.md").exists()


# --- US4: doctor reminds the user of pending changes --------------------------


def test_doctor_lists_pending_changes_and_exits_0(no_terminal: _Prompt) -> None:
    """Must let through 4, SC-004. A missing hook, a shipped rule never added,
    and a retired rule still present are each a change the next attended
    install would make, so doctor lists them with the command. Only the user
    can apply them, so none fails the run."""
    root = _root()
    rule = ASK_RULES[0]
    _installed_then(root, lambda s: (_drop_guard(s), s["permissions"]["ask"].remove(rule)))
    _forget_receipt(root, rule)
    _add_retired_rule(root)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0, result.output
    assert "⚠ .claude/settings.json needs these changes:" in result.output
    assert "+ hook      PreToolUse wfctl hook worktree-guard" in result.output
    assert f"+ ask rule  {rule}" in result.output
    assert f"- ask rule  {_OLD_RULE}" in result.output
    assert "  Run in your terminal: wfctl install-skills --agent claude" in result.output


def test_doctor_warns_when_the_settings_file_was_deleted(no_terminal: _Prompt) -> None:
    """US4 scenario 1. The guard hook lives in that file, so deleting it
    removes the guard. Without the warning doctor exits 0 and says nothing,
    and under Bob Shell, where `wfctl start` checks nothing, the loss
    reaches no one."""
    root = _root()
    _install("--agent", "claude", "--yes")
    _claude(root).unlink()

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0, result.output
    assert "⚠ .claude/settings.json is missing, so wfctl's hooks and rules in it are gone" in (
        result.output
    )
    assert "  Run: wfctl install-skills --agent claude" in result.output


def test_doctor_says_nothing_when_no_settings_change_is_pending(no_terminal: _Prompt) -> None:
    """US4 scenario 4. A settings file is the user's, and a line on every
    clean run trains them to skim the run that has one."""
    _install("--agent", "claude", "--yes")

    result = runner.invoke(app, ["doctor"])

    assert "settings.json" not in result.output


@pytest.mark.parametrize("added", [True, False])
def test_a_removed_rule_is_not_pending_and_is_warned_about_once(
    no_terminal: _Prompt, added: bool
) -> None:
    """A rule the user removed is their decision, not a change for install to
    make, so it isn't listed as pending. Install refuses over it whether or
    not wfctl added it, so doctor warns either way, once."""
    root = _root()
    _installed_then(root, lambda s: s["permissions"]["deny"].remove(DENY_RULE))
    manifest = _manifest(root)
    for r in manifest["claude"]["permissions"]:
        if r["rule"] == DENY_RULE:
            r["added"] = added
    _write_json(_manifest_path(root), manifest)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0, result.output
    assert "needs these changes" not in result.output
    assert result.output.count(f"{DENY_RULE}, which wfctl") == 1
    whose = "which wfctl installed" if added else "which wfctl recorded as already yours"
    assert f"{DENY_RULE}, {whose}, is gone" in result.output


def test_an_unparseable_settings_file_is_reported_once_and_left_alone(
    no_terminal: _Prompt,
) -> None:
    """Install and doctor each name the file once, rather than once per pass
    and per entry, and neither touches it."""
    root = _root()
    _install("--agent", "claude", "--yes")
    _claude(root).write_text("{not json")

    install_output = _install("--agent", "claude", "--yes")
    doctor_output = runner.invoke(app, ["doctor"]).output

    assert install_output.count(".claude/settings.json: ") == 1
    assert doctor_output.count(".claude/settings.json: ") == 1
    assert _claude(root).read_text() == "{not json"


# --- Uninstall keeps removing without asking ----------------------------------


def test_uninstall_removes_wfctls_entries_from_both_files_without_asking(
    no_terminal: _Prompt,
) -> None:
    """FR-012. Uninstall removes only wfctl's own entries, and the person
    running it asked for exactly that, so it doesn't ask again."""
    root = _root()
    _install("--agent", "claude", "--yes")
    _install("--agent", "bob", "--yes")
    claude = json.loads(_claude(root).read_text())
    claude["permissions"]["allow"] = ["Bash(npm test)"]
    _write_json(_claude(root), claude)
    bob = json.loads(_bob(root).read_text())
    bob["tools"] = {"allowed": ["read_file", "mine"]}
    _write_json(_bob(root), bob)
    manifest = _manifest(root)
    manifest["bob"]["tools"] = [
        {"path": ".bob/settings.json", "entry": "read_file", "added": True}
    ]
    _write_json(_manifest_path(root), manifest)

    for agent in ("claude", "bob"):
        result = runner.invoke(app, ["uninstall-skills", "--agent", agent, "--yes"])
        assert result.exit_code == 0, result.output

    assert no_terminal.calls == 0
    assert json.loads(_claude(root).read_text()) == {"permissions": {"allow": ["Bash(npm test)"]}}
    after = json.loads(_bob(root).read_text())
    assert "hooks" not in after
    assert after["tools"]["allowed"] == ["mine"]


# --- #864 review --------------------------------------------------------------


def test_a_settings_file_that_appears_during_install_is_not_replaced(
    no_terminal: _Prompt, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The file was missing at load, so install would create it without a
    question. One that another process wrote since then is someone's, and the
    create would have replaced it."""
    root = _root()
    theirs = b'{"permissions": {"allow": ["Bash(make)"]}}\n'
    real = cli._run_settings_passes

    def passes_then_appear(*args: object, **kwargs: object) -> object:
        result = real(*args, **kwargs)  # type: ignore[arg-type]
        _claude(root).parent.mkdir(parents=True, exist_ok=True)
        _claude(root).write_bytes(theirs)
        return result

    monkeypatch.setattr(cli, "_run_settings_passes", passes_then_appear)
    output = _install("--agent", "claude", "--yes")

    assert _claude(root).read_bytes() == theirs
    assert "⚠ .claude/settings.json appeared while install ran" in output


def test_a_declined_forced_install_offers_the_forced_retry(terminal: _Prompt) -> None:
    """Without `--force`, the retry refuses on the rule the first run was
    forced past instead of asking again."""
    root = _root()
    _installed_then(root, _drop_guard_and_deny)
    terminal.answer = False

    output = _install("--agent", "claude", "--yes", "--force")

    assert "install-skills --agent claude --force" in output
    assert terminal.calls == 1
    plain = runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    assert plain.exit_code == 1, plain.output
    _install("--agent", "claude", "--yes", "--force")
    assert terminal.calls == 2


def test_doctor_runs_past_a_permission_receipt_with_no_rule(no_terminal: _Prompt) -> None:
    """A hand-edited receipt missing its `rule` raised `KeyError` while the
    receipts were keyed, and stopped every check after it."""
    root = _root()
    _installed_then(root, _drop_guard)
    manifest = _manifest(root)
    manifest["claude"]["permissions"].append({"path": ".claude/settings.json"})
    _write_json(_manifest_path(root), manifest)

    result = runner.invoke(app, ["doctor"])

    assert not isinstance(result.exception, KeyError), result.output
    assert "⚠ .claude/settings.json needs these changes:" in result.output


@pytest.mark.parametrize("field", ["path", "rule"])
def test_doctor_runs_past_a_permission_receipt_holding_a_list(
    no_terminal: _Prompt, field: str
) -> None:
    """A list in `path` or `rule` passed the emptiness check and raised
    `TypeError` when the receipt became a dict key, stopping `doctor`."""
    root = _root()
    _installed_then(root, _drop_guard)
    manifest = _manifest(root)
    receipt = {"path": ".claude/settings.json", "rule": DENY_RULE, "kind": "deny"}
    receipt[field] = ["x"]  # type: ignore[assignment]
    manifest["claude"]["permissions"].append(receipt)
    _write_json(_manifest_path(root), manifest)

    result = runner.invoke(app, ["doctor"])

    assert not isinstance(result.exception, TypeError), result.output
    assert "⚠ .claude/settings.json needs these changes:" in result.output


def test_doctor_warns_only_about_a_removed_rule_install_refuses_on(
    no_terminal: _Prompt,
) -> None:
    """A receipt naming a shipped rule in a file install never writes, here
    `.claude/settings.local.json`, made doctor say every install refuses and
    print a `--force` that writes only `.claude/settings.json`. Install
    doesn't refuse on that receipt."""
    root = _root()
    _install("--agent", "claude", "--yes")
    _write_json(root / ".claude" / "settings.local.json", {"permissions": {}})
    manifest = _manifest(root)
    manifest["claude"]["permissions"].append(
        {"path": ".claude/settings.local.json", "rule": DENY_RULE, "kind": "deny",
         "added": True}
    )
    _write_json(_manifest_path(root), manifest)

    result = runner.invoke(app, ["doctor"])
    install = runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    assert "is gone from" not in result.output
    assert install.exit_code == 0, install.output


def test_two_spellings_of_the_bob_settings_path_share_one_copy(agent_dir: Path) -> None:
    """With a copy for each spelling, the second save would put back the
    approval the first one removed."""
    root = _root()
    _write_json(_bob(root), {"tools": {"allowed": ["a", "b", "mine"]}})
    records = [
        {"path": ".bob/settings.json", "entry": "a", "added": True},
        {"path": "./.bob/settings.json", "entry": "b", "added": True},
    ]
    copies: dict = {}

    cli._unmerge_bob_tool_allows(root, records, copies)

    assert list(copies) == [".bob/settings.json"]
    assert copies[".bob/settings.json"].settings["tools"]["allowed"] == ["mine"]
