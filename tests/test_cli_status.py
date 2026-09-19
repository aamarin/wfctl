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

from wfctl.cli import app

runner = CliRunner()


def _declare(storyctl_dir: types.SimpleNamespace, steps: dict) -> None:
    (storyctl_dir.repo_root / "wfctl.json").write_text(json.dumps({"steps": steps}))


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
