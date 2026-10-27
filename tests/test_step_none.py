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

import pytest
from typer.testing import CliRunner

from tests.conftest import CLEAN_PLAN, CLEAN_SPEC
from wfctl.cli import app

runner = CliRunner()


def _arch_root(storyctl_dir: types.SimpleNamespace, monkeypatch) -> Path:
    """`docs/architecture` inside the fixture's own repo, so a test can show
    that nothing lands there."""
    root = storyctl_dir.repo_root / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    return root


def _exceptions(storyctl_dir: types.SimpleNamespace) -> Path:
    return storyctl_dir.spec_dir / "exceptions"


def _declare(storyctl_dir: types.SimpleNamespace, steps: dict) -> None:
    (storyctl_dir.repo_root / "wfctl.json").write_text(json.dumps({"steps": steps}))


def test_a_claimed_pass_is_recorded_in_the_spec_folder(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """The exception sits beside the boundary exception in the spec folder, and
    nothing lands under the architecture folder, which changes only when the
    architecture does (`design-exceptions-live-with-specs`)."""
    root = _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "ui-design", "manual": True, "evidence": "x.md"}],
    })

    result = runner.invoke(app, ["step", "none", "brainstorm.ui-design",
                                  "--reason", "backend-only change"])

    assert result.exit_code == 0
    assert result.output == (
        '✓ Recorded: brainstorm.ui-design does not apply — "backend-only change"\n'
        "  Put the reason in the PR body.\n"
    )
    claim = _exceptions(storyctl_dir) / "brainstorm.ui-design.md"
    assert claim.read_text() == (
        "# `brainstorm.ui-design` does not apply\n\nbackend-only change\n"
    )
    assert not root.exists()


def test_an_empty_reason_writes_nothing(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """FR-013: refused, and nothing written — the same guard `arch none` uses."""
    _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "ui-design", "manual": True, "evidence": "x.md"}],
    })

    result = runner.invoke(app, ["step", "none", "brainstorm.ui-design", "--reason", "  "])

    assert result.exit_code == 1
    assert not _exceptions(storyctl_dir).exists()


def test_a_placeholder_reason_writes_nothing(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "ui-design", "manual": True, "evidence": "x.md"}],
    })

    result = runner.invoke(app, ["step", "none", "brainstorm.ui-design", "--reason", "<why>"])

    assert result.exit_code == 1
    assert "placeholder" in result.output
    assert not _exceptions(storyctl_dir).exists()


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
    _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [
            {"name": "a", "manual": True, "evidence": "a.md"},
            {"name": "b", "manual": True, "evidence": "b.md"},
        ],
    })

    runner.invoke(app, ["step", "none", "brainstorm.a", "--reason", "first"])
    runner.invoke(app, ["step", "none", "brainstorm.b", "--reason", "second"])

    claims = _exceptions(storyctl_dir)
    assert (claims / "brainstorm.a.md").read_text().strip().endswith("first")
    assert (claims / "brainstorm.b.md").read_text().strip().endswith("second")
    # Scenario 2.1: both read skipped, so neither file shadows the other.
    payload = json.loads(runner.invoke(app, ["status", "--json"]).output)
    brainstorm = next(s for s in payload["steps"] if s["name"] == "brainstorm")
    states = {s["name"]: (s["state"], s["claimed"]) for s in brainstorm["sub_steps"]}
    assert states["a"] == ("skipped", "first")
    assert states["b"] == ("skipped", "second")


def test_a_second_claim_on_the_same_pass_replaces_it(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "a", "manual": True, "evidence": "a.md"}],
    })

    runner.invoke(app, ["step", "none", "brainstorm.a", "--reason", "first reason"])
    runner.invoke(app, ["step", "none", "brainstorm.a", "--reason", "second reason"])

    claim = _exceptions(storyctl_dir) / "brainstorm.a.md"
    text = claim.read_text()
    assert "second reason" in text
    assert "first reason" not in text


def test_an_out_of_tree_arch_root_does_not_stop_step_none(
    storyctl_dir: types.SimpleNamespace, monkeypatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """`step none` used to refuse, and remove what it wrote, when the arch root
    sat outside the working tree, since no reviewer would see the file. The
    exception now goes to the spec folder and the reviewer reads the PR body,
    so where the arch root lives no longer matters (FR-005)."""
    outside = tmp_path_factory.mktemp("records-kept-elsewhere")
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(outside))
    _declare(storyctl_dir, {
        "brainstorm": [{"name": "ui-design", "manual": True, "evidence": "x.md"}],
    })

    result = runner.invoke(app, ["step", "none", "brainstorm.ui-design",
                                  "--reason", "backend-only change"])

    assert result.exit_code == 0
    assert "Put the reason in the PR body." in result.output
    assert (_exceptions(storyctl_dir) / "brainstorm.ui-design.md").is_file()
    assert list(outside.iterdir()) == []


def test_pass_exceptions_never_include_the_boundary_exception(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """Scenario 2.2, and the verification `design-exceptions-module.md` names.
    The boundary exception shares the folder with the pass exceptions, so a
    reader that globbed every file would report a pass named `boundary` that
    nobody declared."""
    _arch_root(storyctl_dir, monkeypatch)
    _declare(storyctl_dir, {
        "brainstorm": [
            {"name": "a", "manual": True, "evidence": "a.md"},
            {"name": "b", "manual": True, "evidence": "b.md"},
        ],
    })
    runner.invoke(app, ["step", "none", "brainstorm.a", "--reason", "first"])
    runner.invoke(app, ["step", "none", "brainstorm.b", "--reason", "second"])
    runner.invoke(app, ["arch", "none", "--reason", "no boundary"])

    payload = json.loads(runner.invoke(app, ["status", "--json"]).output)
    claimed = {
        f"{step['name']}.{sub['name']}"
        for step in payload["steps"]
        for sub in step["sub_steps"]
        if sub["claimed"] is not None
    }
    assert claimed == {"brainstorm.a", "brainstorm.b"}


def test_the_built_in_plan_review_can_be_claimed_away_and_a_person_still_starts_tasks(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """FR-008: `plan-review` is wfctl's own pass, not a declaration, so the
    claim has to resolve with no `wfctl.json` at all. Every other test here
    declares its pass first, which would hide a resolver that only searched
    the repository's declarations.

    The payload after the claim is R4's point. A person made the claim, not a
    review, so nothing about it grants the mode: with auto-approve off, the
    next command is `/speckit.tasks` and `auto` stays false, the same stop a
    clean review leaves."""
    _arch_root(storyctl_dir, monkeypatch)
    storyctl_dir.make_spec_artifact("specify", content=CLEAN_SPEC)
    storyctl_dir.make_spec_artifact("plan", content=CLEAN_PLAN)
    assert not (storyctl_dir.repo_root / "wfctl.json").exists()

    result = runner.invoke(app, ["step", "none", "plan.plan-review",
                                  "--reason", "a one-line config change"])

    assert result.exit_code == 0, result.output
    claim = _exceptions(storyctl_dir) / "plan.plan-review.md"
    assert "a one-line config change" in claim.read_text()

    payload = json.loads(runner.invoke(app, ["status", "--json"]).output)
    plan = next(s for s in payload["steps"] if s["name"] == "plan")
    review = next(s for s in plan["sub_steps"] if s["name"] == "plan-review")
    assert review["state"] == "skipped"
    assert "a one-line config change" in review["claimed"]
    assert (payload["next_command"], payload["auto"]) == ("/speckit.tasks", False)


# --- #649: `step none --context` ----------------------------------------------


def _with_name_list(storyctl_dir: types.SimpleNamespace, monkeypatch) -> None:
    from tests.conftest import write_domain_page

    write_domain_page(_arch_root(storyctl_dir, monkeypatch), "session-continuity, attention")


def test_the_branch_wide_claim_on_the_architecture_pass_is_refused_with_a_name_list(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """The claim would skip the architecture pass, and with it every listed
    context's check (FR-011, SC-001)."""
    _with_name_list(storyctl_dir, monkeypatch)

    result = runner.invoke(app, ["step", "none", "brainstorm.architecture", "--reason", "Copy"])

    assert result.exit_code == 1
    assert "checks each context separately" in result.output
    assert not _exceptions(storyctl_dir).exists()


def test_the_branch_wide_claim_on_the_software_design_pass_is_refused_with_a_name_list(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    _with_name_list(storyctl_dir, monkeypatch)

    result = runner.invoke(app, ["step", "none", "brainstorm.software-design", "--reason", "Copy"])

    assert result.exit_code == 1
    assert (
        'wfctl step none brainstorm.software-design --context <name> --reason "<why>"'
        in result.output
    )
    assert not _exceptions(storyctl_dir).exists()


def test_context_applies_only_to_the_software_design_pass(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    """The architecture pass has `arch none --context`, and no other pass reads
    a context, so a file under `exceptions/<context>/` would answer nothing."""
    _with_name_list(storyctl_dir, monkeypatch)

    result = runner.invoke(
        app,
        ["step", "none", "brainstorm.architecture", "--context", "attention", "--reason", "Copy"],
    )

    assert result.exit_code == 1
    assert "--context applies only to brainstorm.software-design" in result.output
    assert not _exceptions(storyctl_dir).exists()


def test_a_software_design_claim_for_one_context_is_written_under_that_context(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    _with_name_list(storyctl_dir, monkeypatch)

    result = runner.invoke(
        app,
        ["step", "none", "brainstorm.software-design", "--context", "attention",
         "--reason", "No structural choice"],
    )

    assert result.exit_code == 0, result.output
    assert (
        '✓ Recorded: brainstorm.software-design does not apply to attention — '
        '"No structural choice"' in result.output
    )
    assert (_exceptions(storyctl_dir) / "attention" / "brainstorm.software-design.md").is_file()


def test_step_none_context_is_refused_without_a_name_list_or_for_an_unknown_name(
    storyctl_dir: types.SimpleNamespace, monkeypatch
) -> None:
    _arch_root(storyctl_dir, monkeypatch)
    command = ["step", "none", "brainstorm.software-design", "--context", "attention",
               "--reason", "No structural choice"]

    assert "needs a name list" in runner.invoke(app, command).output

    _with_name_list(storyctl_dir, monkeypatch)
    unknown = runner.invoke(app, [*command[:4], "atention", *command[5:]])
    assert unknown.exit_code == 1
    assert "atention is not on the domain page" in unknown.output
    assert not _exceptions(storyctl_dir).exists()
