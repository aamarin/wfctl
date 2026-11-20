"""Codex asks before the agent turns auto-approve on.

Claude Code gets its ask rules (`tests/test_install_hook_merge.py`). Codex reads
a rules file with a `prompt` decision from the project's `.codex/rules/`, so
wfctl ships one (`auto-approve-grant-asks-first`).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()

SHIPPED_RULES = Path(__file__).resolve().parent.parent / "wfctl" / "agents" / "codex" / "rules" / "wfctl.rules"


def _execpolicy(*command: str) -> dict:
    result = subprocess.run(
        ["codex", "execpolicy", "check", "--rules", str(SHIPPED_RULES), "--", *command],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


@pytest.mark.skipif(shutil.which("codex") is None, reason="needs the codex CLI")
@pytest.mark.parametrize(
    "command",
    [["wfctl", "auto-approve", "on"], ["uv", "run", "wfctl", "auto-approve", "on"]],
)
def test_codex_prompts_before_either_form_of_on(command: list[str]) -> None:
    """Codex matches a rule against the argument list as an exact prefix, so
    `uv run` needs a rule of its own, the same reason Claude Code gets a rule for it. A
    rule Codex can't parse fails here rather than loading as no rule at all."""
    assert _execpolicy(*command).get("decision") == "prompt"


@pytest.mark.skipif(shutil.which("codex") is None, reason="needs the codex CLI")
@pytest.mark.parametrize(
    "command",
    [["wfctl", "auto-approve", "off"], ["wfctl", "auto-approve"], ["uv", "run", "wfctl", "auto-approve", "off"]],
)
def test_codex_lets_off_and_the_read_through_without_a_prompt(command: list[str]) -> None:
    """A prompt on `off` would teach people to allowlist wfctl, which takes the
    prompt off `on` as well."""
    assert _execpolicy(*command).get("decision") is None


def test_install_for_codex_writes_the_rules_file_and_records_it(
    agent_dir: Path, bundle: Path
) -> None:
    """The rules file goes under the project's `.codex/rules/` by its own name,
    so a rules file the project wrote beside it is left alone, and the manifest
    records it so `doctor` reports it when it drifts."""
    rules = bundle / "agents" / "codex" / "rules"
    rules.mkdir(parents=True)
    (rules / "wfctl.rules").write_text(SHIPPED_RULES.read_text())
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    own = repo_root / ".codex" / "rules" / "mine.rules"
    own.parent.mkdir(parents=True)
    own.write_text("# the project's own\n")

    result = runner.invoke(app, ["install-skills", "--agent", "codex", "--yes"])

    assert result.exit_code == 0, result.output
    assert (repo_root / ".codex" / "rules" / "wfctl.rules").read_text() == SHIPPED_RULES.read_text()
    assert own.read_text() == "# the project's own\n"
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert [i["path"] for i in manifest["codex"]["items"]] == [".codex/rules/wfctl.rules"]
    assert "trusted" in result.output

