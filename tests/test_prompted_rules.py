"""The host rules follow the table of prompted spellings (#833).

The worktree guard lets the agent run a person-only command only in a
spelling `PROMPTED` lists, so the user can stop it at the host's prompt. A
spelling with no rule leaves the agent refused with no prompt to answer, and a
rule with no spelling widens what the host asks about for nothing. These tests
build what each host should carry from the table and compare.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app
from wfctl.evidence import PROMPTED

runner = CliRunner()

# These tests are about what a change to an existing settings file does, so the
# user at the terminal says yes. `test_settings_ask.py` covers the no and the
# missing terminal.
pytestmark = pytest.mark.usefixtures("settings_yes")

_CODEX_RULES = (
    Path(__file__).resolve().parent.parent / "wfctl" / "agents" / "codex" / "rules" / "wfctl.rules"
)
_RULES = [f"Bash({e.text}:*)" for e in PROMPTED]


def _settings(repo_root: Path) -> Path:
    return repo_root / ".claude" / "settings.json"


def test_install_writes_one_ask_rule_per_prompted_spelling(agent_dir: Path) -> None:
    """Claude Code asks only for a command its rule matches, so a spelling
    the guard lets through with no rule would never reach the user."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])

    assert result.exit_code == 0, result.output
    ask = json.loads(_settings(repo_root).read_text())["permissions"]["ask"]
    assert [r for r in ask if r in _RULES] == _RULES
    # A created file isn't asked about, so each rule's reason prints with it.
    assert all(
        re.search(rf"\+ ask rule +{re.escape(r)}", result.output) for r in _RULES
    ), result.output
    assert "since Claude Code wouldn't ask you first" in result.output


@pytest.mark.parametrize("rule", _RULES)
def test_doctor_reports_each_prompted_rule_that_goes_missing(
    agent_dir: Path, rule: str,
) -> None:
    """Without the rule, the guard refuses the command and the agent has no
    way to ask the user, so `doctor` names the rule and what it costs. It
    warns rather than fails, like every managed rule: the guard refuses with
    the rule gone, so nothing runs unasked, and a repo's CI stays green."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    path = _settings(repo_root)
    settings = json.loads(path.read_text())
    settings["permissions"]["ask"].remove(rule)
    path.write_text(json.dumps(settings, indent=2) + "\n")

    result = runner.invoke(app, ["doctor"])

    assert f"⚠ claude: {rule}, which wfctl installed, is gone from .claude/settings.json" in result.output
    assert "since Claude Code wouldn't ask you first" in result.output


def test_uninstall_removes_every_prompted_rule(agent_dir: Path) -> None:
    """Uninstall returns the settings file to what the repo had."""
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    path = _settings(repo_root)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"permissions": {"allow": ["Bash(npm test)"]}}, indent=2) + "\n")
    runner.invoke(app, ["install-skills", "--agent", "claude"])

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude", "--yes"])

    assert result.exit_code == 0, result.output
    assert json.loads(path.read_text()) == {"permissions": {"allow": ["Bash(npm test)"]}}


def test_the_codex_rules_file_prompts_for_exactly_the_tables_spellings() -> None:
    """The Codex file is written by hand, since a Codex user reads it to see
    what wfctl asks for. This keeps it in step with the table, the same way
    `required-sections-are-wfctls.md` keeps its constants in step with the
    templates."""
    text = _CODEX_RULES.read_text()
    patterns = [
        tuple(re.findall(r'"([^"]+)"', m))
        for m in re.findall(r"pattern = \[([^\]]*)\]", text)
    ]
    auto_approve = [p for p in patterns if "auto-approve" in p]

    assert [p for p in patterns if p not in auto_approve] == [e.words for e in PROMPTED]
    assert text.count('decision = "prompt"') == len(patterns)
