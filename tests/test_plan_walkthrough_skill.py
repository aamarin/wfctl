"""The plan walkthrough ships as a skill and a command, and ships nothing else.

The suite cannot check how the interview reads (`AGENTS.md`); what it can check
is that the pieces a repository installs are present, that no per-vendor
manifest rides along (FR-017, `layer-model`), and that the refusal the skill
owes an autonomous run is actually written into it (FR-014).
"""
from __future__ import annotations

from pathlib import Path

import wfctl

AGENTS = Path(wfctl.__file__).parent / "agents"
SKILL_DIR = AGENTS / "skills" / "plan-walkthrough"
COMMAND = AGENTS / "commands" / "plan-walkthrough.md"


def test_the_skill_ships_under_its_own_name() -> None:
    skill = (SKILL_DIR / "SKILL.md").read_text()
    assert "\nname: plan-walkthrough\n" in skill


def test_the_skill_ships_every_reference_it_loads() -> None:
    """SKILL.md tells the agent to read each of these; one missing is a step the
    agent is told to take and cannot."""
    shipped = sorted(p.name for p in (SKILL_DIR / "references").iterdir())
    assert shipped == [
        "artifact-contract.md",
        "examples.md",
        "interrogation-lenses.md",
        "question-quality.md",
        "source-map.md",
    ]


def test_the_skill_carries_no_per_vendor_manifest() -> None:
    """The candidate shipped `agents/openai.yaml`. A vendor file inside a skill
    directory is a shape `layer-model` has no layer for, and install-skills
    would copy it into every agent's tree."""
    assert not (SKILL_DIR / "agents").exists()


def test_the_command_runs_the_skill() -> None:
    command = COMMAND.read_text()
    assert "skills/plan-walkthrough/SKILL.md" in command
    assert "disable-model-invocation: true" in command


def test_the_skill_refuses_while_auto_approve_is_on() -> None:
    """The skill cannot tell a person who typed the command from an autonomous
    agent that ran it, so the mode alone decides. The refusal has to name the
    way out, or a person present with auto-approve on is simply stuck."""
    skill = (SKILL_DIR / "SKILL.md").read_text()
    assert "auto_approve" in skill
    assert "wfctl start --no-auto-approve" in skill


def test_the_skill_writes_answers_outside_the_feature_directory() -> None:
    """The answers stay private (`plan-walkthrough-is-private`), which holds only
    while the contract names the state directory as their one destination."""
    contract = (SKILL_DIR / "references" / "artifact-contract.md").read_text()
    assert "wfctl state-dir" in contract
    assert "walkthrough/" in contract
