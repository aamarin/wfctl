"""`wfctl step none` — declaring one pipeline pass inapplicable.

Generalises `wfctl arch none`
(`an-absent-artifact-is-claimed-not-inferred`), and this file mirrors
`test_arch_records.py`'s own coverage of that command's refusals one level
down: every row of contracts/cli.md's `wfctl step none` table, named for the
failure it catches.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def _arch_root(storyctl_dir: types.SimpleNamespace, monkeypatch) -> Path:
    """`docs/architecture` inside the fixture's own repo, so a written claim
    lands in the working tree `touched_on_this_branch` inspects."""
    root = storyctl_dir.repo_root / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    return root


def _declare(storyctl_dir: types.SimpleNamespace, steps: dict) -> None:
    (storyctl_dir.repo_root / "wfctl.json").write_text(json.dumps({"steps": steps}))


def test_a_claimed_pass_is_recorded_and_the_file_lands_in_the_change(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    root = _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "ui-design", "manual": True, "evidence": "x.md"}],
    })

    result = runner.invoke(app, ["step", "none", "brainstorm.ui-design",
                                  "--reason", "backend-only change"])

    assert result.exit_code == 0
    assert "✓" in result.output
    claim = root / "step-claims" / "418-storyctl" / "brainstorm.ui-design.md"
    assert claim.exists()
    assert "backend-only change" in claim.read_text()
    assert "brainstorm.ui-design does not apply" in claim.read_text()


def test_an_empty_reason_writes_nothing(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """FR-013: refused, and nothing written — the same guard `arch none` uses."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "ui-design", "manual": True, "evidence": "x.md"}],
    })

    result = runner.invoke(app, ["step", "none", "brainstorm.ui-design", "--reason", "  "])

    assert result.exit_code == 1
    assert not (root / "step-claims").exists()


def test_a_placeholder_reason_writes_nothing(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    root = _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "ui-design", "manual": True, "evidence": "x.md"}],
    })

    result = runner.invoke(app, ["step", "none", "brainstorm.ui-design", "--reason", "<why>"])

    assert result.exit_code == 1
    assert "placeholder" in result.output
    assert not (root / "step-claims").exists()


def test_a_pass_that_is_not_declared_is_refused_and_names_what_is(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "ui-design", "manual": True, "evidence": "x.md"}],
    })

    result = runner.invoke(app, ["step", "none", "brainstorm.ghost", "--reason", "no"])

    assert result.exit_code == 1
    assert "brainstorm.ghost is not a declared pass" in result.output
    # Names what is, so the author does not have to go read wfctl.json.
    assert "ui-design" in result.output


def test_a_bare_name_with_one_match_resolves(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "ui-design", "manual": True, "evidence": "x.md"}],
    })

    result = runner.invoke(app, ["step", "none", "ui-design", "--reason", "backend-only"])

    assert result.exit_code == 0
    assert "brainstorm.ui-design does not apply" in result.output


def test_a_bare_name_declared_under_two_steps_is_refused_and_names_both(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "review", "manual": True, "evidence": "a.md"}],
        "plan": [{"name": "review", "manual": True, "evidence": "b.md"}],
    })

    result = runner.invoke(app, ["step", "none", "review", "--reason", "no"])

    assert result.exit_code == 1
    assert "declared under" in result.output
    assert "brainstorm" in result.output and "plan" in result.output
    assert "qualify it" in result.output


def test_a_bare_name_with_no_match_is_refused(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "ui-design", "manual": True, "evidence": "x.md"}],
    })

    result = runner.invoke(app, ["step", "none", "ghost", "--reason", "no"])

    assert result.exit_code == 1
    assert "'ghost' is not a declared pass" in result.output


def test_a_bare_name_never_resolves_against_the_current_step(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """FR-002c: a pass under the *current* step must still be qualified once a
    second pass elsewhere shares its name — resolution never special-cases
    whichever step `wfctl status` happens to report as current, because that
    changes as unrelated work lands and would make the same command resolve
    differently from one day to the next."""
    _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "review", "manual": True, "evidence": "a.md"}],
        "plan": [{"name": "review", "manual": True, "evidence": "b.md"}],
    })
    # brainstorm is current on a bare repo — nothing has run yet.
    assert json.loads(runner.invoke(app, ["status", "--json"]).output)["current"] == "brainstorm"

    result = runner.invoke(app, ["step", "none", "review", "--reason", "no"])

    assert result.exit_code == 1
    assert "qualify it" in result.output


def test_two_claims_on_one_branch_both_survive(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """FR-015, SC-005: `arch none`'s single-file overwrite would lose all but
    the last — one file per pass is what keeps both."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [
            {"name": "a", "manual": True, "evidence": "a.md"},
            {"name": "b", "manual": True, "evidence": "b.md"},
        ],
    })

    runner.invoke(app, ["step", "none", "brainstorm.a", "--reason", "first"])
    runner.invoke(app, ["step", "none", "brainstorm.b", "--reason", "second"])

    claims = root / "step-claims" / "418-storyctl"
    assert (claims / "brainstorm.a.md").read_text().strip().endswith("first")
    assert (claims / "brainstorm.b.md").read_text().strip().endswith("second")


def test_a_second_claim_on_the_same_pass_replaces_it(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    root = _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "a", "manual": True, "evidence": "a.md"}],
    })

    runner.invoke(app, ["step", "none", "brainstorm.a", "--reason", "first reason"])
    runner.invoke(app, ["step", "none", "brainstorm.a", "--reason", "second reason"])

    claim = root / "step-claims" / "418-storyctl" / "brainstorm.a.md"
    text = claim.read_text()
    assert "second reason" in text
    assert "first reason" not in text
