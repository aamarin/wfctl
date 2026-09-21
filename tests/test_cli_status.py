"""`wfctl status`'s pass rendering — indentation, `--all`, and the
no-passes-declared regression every repository would see first.

The state-name tests live in `test_pipeline_state_names.py`; this file is
about what the console draws from them, the way `test_pipeline_commands.py`
is for the eight built-in rows.
"""
from __future__ import annotations

import json
import types

from typer.testing import CliRunner

from wfctl._session import record_blocked
from wfctl.cli import app

runner = CliRunner()


def _declare(storyctl_dir: types.SimpleNamespace, steps: dict) -> None:
    (storyctl_dir.repo_root / "wfctl.json").write_text(json.dumps({"steps": steps}))


def _stall_on(storyctl_dir: types.SimpleNamespace) -> None:
    assert runner.invoke(app, ["start"]).exit_code == 0
    for _ in range(4):
        assert runner.invoke(app, ["resume"]).exit_code == 0


def test_a_repository_that_declares_nothing_renders_byte_identically(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """US1 acceptance 4: the regression every repository would see first — no
    indented rows, no blank line, no header, for the seven steps that carry no
    pass at all."""
    storyctl_dir.make_spec_artifact("specify", content="# Spec\nsomething\n")

    before = runner.invoke(app, ["status"]).output
    (storyctl_dir.repo_root / "wfctl.json").write_text("{}")
    after = runner.invoke(app, ["status"]).output

    assert before == after
    for line in after.splitlines():
        assert not line.startswith("  "), f"an indented row appeared with nothing declared: {line!r}"


def test_a_declared_pass_renders_indented_under_its_step(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    _declare(storyctl_dir, {
        "brainstorm": [
            {"name": "ui-design", "command": "/pfms-ui-design-workflow", "evidence": "x.md"},
        ],
    })
    (storyctl_dir.repo_root / ".agents" / "commands").mkdir(parents=True)
    (storyctl_dir.repo_root / ".agents" / "commands" / "pfms-ui-design-workflow.md").write_text("x")

    out = runner.invoke(app, ["status"]).output

    lines = out.splitlines()
    brainstorm_idx = next(i for i, line in enumerate(lines) if line.startswith("brainstorm"))
    assert lines[brainstorm_idx + 3].strip().startswith("ui-design")


def test_a_settled_away_pass_is_hidden_by_default_and_shown_with_all(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "ui-design", "manual": True, "evidence": "x.md"}],
    })
    runner.invoke(app, ["step", "none", "brainstorm.ui-design", "--reason", "backend-only change"])

    default = runner.invoke(app, ["status"]).output
    everything = runner.invoke(app, ["status", "--all"]).output

    assert "ui-design" not in default
    assert "ui-design" in everything
    assert "backend-only change" in everything


def test_all_does_not_change_the_json_payload(storyctl_dir: types.SimpleNamespace) -> None:
    """FR-020: the flag selects a console rendering and nothing else — the
    payload always carries the full tree."""
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "ui-design", "manual": True, "evidence": "x.md"}],
    })
    runner.invoke(app, ["step", "none", "brainstorm.ui-design", "--reason", "backend-only"])

    plain = json.loads(runner.invoke(app, ["status", "--json"]).output)
    with_all = json.loads(runner.invoke(app, ["status", "--all", "--json"]).output)
    assert plain == with_all
    brainstorm = next(s for s in plain["steps"] if s["name"] == "brainstorm")
    ui_design = next(s for s in brainstorm["sub_steps"] if s["name"] == "ui-design")
    assert ui_design == {
        "name": "ui-design", "state": "skipped", "annotation": None,
        "command": None, "manual": True, "claimed": "backend-only", "is_current": False,
    }


def test_check_config_reports_no_configuration(storyctl_dir: types.SimpleNamespace) -> None:
    result = runner.invoke(app, ["check", "config"])
    assert result.exit_code == 0
    assert "no configuration to check" in result.output


def test_check_config_reports_no_passes_declared(storyctl_dir: types.SimpleNamespace) -> None:
    (storyctl_dir.repo_root / "wfctl.json").write_text("{}")
    result = runner.invoke(app, ["check", "config"])
    assert result.exit_code == 0
    assert "no passes declared" in result.output


def test_check_config_counts_passes_under_steps(storyctl_dir: types.SimpleNamespace) -> None:
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "a", "manual": True, "evidence": "a.md"}],
        "specify": [{"name": "b", "manual": True, "evidence": "b.md"}],
    })
    result = runner.invoke(app, ["check", "config"])
    assert result.exit_code == 0
    assert "2 passes under 2 steps" in result.output


def test_check_config_exits_nonzero_on_a_finding(storyctl_dir: types.SimpleNamespace) -> None:
    _declare(storyctl_dir, {"brainstorm": [{"name": "a", "evidence": "a.md"}]})
    result = runner.invoke(app, ["check", "config"])
    assert result.exit_code == 1
    assert "declares no command and is not marked manual" in result.output


# --- T014: the console rendering is untouched by `attention` (FR-002, SC-003) ---

def test_console_rendering_never_mentions_attention_in_any_state(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`attention` is a JSON-only field, derived beside sentences the console
    already prints. Adding it must not add a word, a line or move a byte of
    what a person reading `wfctl status` sees — proven across all three
    conditions it answers for, plus the condition where none of them hold."""
    quiet = runner.invoke(app, ["status"]).output
    assert "attention" not in quiet.lower()

    storyctl_dir.stage_upstream_of("tasks")
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "issue-comment", "refused", "decompose",
    )
    blocked = runner.invoke(app, ["status"]).output
    assert "attention" not in blocked.lower()
    assert "blocked: host refused issue-comment" in blocked


def test_console_rendering_unchanged_for_manual_and_stalled(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    storyctl_dir.make_spec_artifact("brainstorm")
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "ui-design", "manual": True, "evidence": "ui-contract.md"}],
    })
    manual = runner.invoke(app, ["status"]).output
    assert "attention" not in manual.lower()

    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    _stall_on(storyctl_dir)
    stalled = runner.invoke(app, ["status"]).output
    assert "attention" not in stalled.lower()
    assert "was attempted 3 times and changed nothing" in stalled


# --- T025: the shape check is silent in front of a person (FR-015, SC-006) ---

def test_status_never_prints_anything_about_the_shape_check(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The comparison runs with the test suite and nowhere else — a mismatch
    between the shipped file and the live payload is the author's mistake, and
    it must surface where the author is, never on a person's screen. `version`
    itself is expected in the JSON payload (FR-011); what must never appear is
    a message *about* the check — a bump owed, a path named, a regeneration
    verb. Exercised across states, including one that is both blocked and
    stalled, since FR-015 is unconditional rather than a claim about the quiet
    case alone."""
    phrases = (
        "owes a major", "owes a minor", "unrecorded", "no longer emitted",
        "contract regenerate", "shape file", "status-payload",
    )

    storyctl_dir.stage_upstream_of("tasks", tasks="- [ ] T001 open\n")
    _stall_on(storyctl_dir)
    record_blocked(
        storyctl_dir.agent_dir, "418-storyctl", "push", "refused", "decompose",
    )

    console = runner.invoke(app, ["status"]).output
    payload = runner.invoke(app, ["status", "--json"]).output
    for phrase in phrases:
        assert phrase not in console.lower()
        assert phrase not in payload.lower()
