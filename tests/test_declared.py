"""`_declared.load` — parsing and validating `wfctl.json`'s `steps` key.

One test per finding class in contracts/cli.md's `wfctl check config` table,
named for the failure it catches, plus the ordering and defaulting rules
research.md settles. Nothing here drives the CLI — `test_declared` in
`tests/test_declared.py` (this file) is the parser's own test, and
`tests/test_cli_status.py` is where `check config`'s rendering is asserted.
"""
from __future__ import annotations

import types

from wfctl import _declared
from wfctl._pipeline import _STEPS


def test_a_repository_that_declares_nothing_still_carries_wfctls_own_passes(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """No `wfctl.json` at all is not an error — it is every repository's
    current state, and `brainstorm`'s two built-in passes are not conditional
    on a file existing."""
    passes, problems = _declared.load(declaring_repo.root)
    assert problems == []
    assert [s.name for s in passes["brainstorm"]] == ["architecture", "design-doc"]
    assert "specify" not in passes  # no passes at all, built-in or declared


def test_unknown_step_key_is_a_finding(declaring_repo: types.SimpleNamespace) -> None:
    """A typo'd step name — the eight are spelled out so the author does not
    have to open the source to find the right one."""
    declaring_repo.write_config({"brainstrom": [{"name": "x", "manual": True, "evidence": "x.md"}]})
    _, problems = _declared.load(declaring_repo.root)
    assert any("brainstrom" in p and "one of:" in p for p in problems)


def test_missing_name_is_a_finding(declaring_repo: types.SimpleNamespace) -> None:
    declaring_repo.write_config({"specify": [{"manual": True, "evidence": "x.md"}]})
    _, problems = _declared.load(declaring_repo.root)
    assert any("has no 'name'" in p for p in problems)


def test_duplicate_name_under_one_step_is_a_finding(declaring_repo: types.SimpleNamespace) -> None:
    declaring_repo.write_config({"specify": [
        {"name": "x", "manual": True, "evidence": "a.md"},
        {"name": "x", "manual": True, "evidence": "b.md"},
    ]})
    _, problems = _declared.load(declaring_repo.root)
    assert any("specify.x is declared twice" in p for p in problems)


def test_a_name_containing_a_slash_is_a_finding(declaring_repo: types.SimpleNamespace) -> None:
    """`step_none_cmd` builds a claim path from this name unvalidated — an
    unrejected `/` walks that write outside `step-claims/<branch>/` (and a
    name split across segments is never read back by `_step_claims`'s
    single-level glob either way), so `check config` must catch it before
    `step none` ever runs."""
    declaring_repo.write_config({"specify": [
        {"name": "../../../tmp/evil", "manual": True, "evidence": "a.md"},
    ]})
    _, problems = _declared.load(declaring_repo.root)
    assert any("is not a valid pass name" in p for p in problems)


def test_a_name_of_dot_dot_is_a_finding(declaring_repo: types.SimpleNamespace) -> None:
    """`Path('..').name == '..'`, so a slash check alone would let this one
    through — the lone segment that is still a traversal."""
    declaring_repo.write_config({"specify": [
        {"name": "..", "manual": True, "evidence": "a.md"},
    ]})
    _, problems = _declared.load(declaring_repo.root)
    assert any("is not a valid pass name" in p for p in problems)


def test_the_same_name_under_two_different_steps_is_accepted(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """FR-002a: uniqueness is per step. A repository adding a pass under one
    step is never refused on account of a pass under a step it did not name."""
    declaring_repo.write_config({
        "specify": [{"name": "x", "manual": True, "evidence": "a.md"}],
        "plan": [{"name": "x", "manual": True, "evidence": "b.md"}],
    })
    passes, problems = _declared.load(declaring_repo.root)
    assert problems == []
    assert [s.name for s in passes["specify"]] == ["x"]
    assert [s.name for s in passes["plan"]] == ["x"]


def test_a_pass_with_both_command_and_manual_is_a_finding(
    declaring_repo: types.SimpleNamespace,
) -> None:
    declaring_repo.write_config({"specify": [
        {"name": "x", "command": "/y", "manual": True, "evidence": "a.md"},
    ]})
    declaring_repo.install_command("y")
    _, problems = _declared.load(declaring_repo.root, is_installed=lambda c: True)
    assert any("declares a command and 'manual'" in p for p in problems)


def test_a_pass_with_neither_command_nor_manual_is_a_finding(
    declaring_repo: types.SimpleNamespace,
) -> None:
    declaring_repo.write_config({"specify": [{"name": "x", "evidence": "a.md"}]})
    _, problems = _declared.load(declaring_repo.root)
    assert any("declares no command and is not marked manual" in p for p in problems)


def test_a_manual_pass_is_never_checked_for_installation(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """FR-022a: nothing to install for a pass a person performs — `is_installed`
    must not even be asked, let alone answered no."""
    declaring_repo.write_config({"specify": [{"name": "x", "manual": True, "evidence": "a.md"}]})
    passes, problems = _declared.load(declaring_repo.root, is_installed=lambda c: False)
    assert problems == []
    assert passes["specify"][0].command is None


def test_an_uninstalled_command_is_a_finding(declaring_repo: types.SimpleNamespace) -> None:
    declaring_repo.write_config({"specify": [
        {"name": "x", "command": "/never-shipped", "evidence": "a.md"},
    ]})
    _, problems = _declared.load(declaring_repo.root, is_installed=lambda c: False)
    assert any("/never-shipped" in p and "not installed" in p for p in problems)


def test_a_non_string_command_is_a_finding(declaring_repo: types.SimpleNamespace) -> None:
    """A JSON number or array in `command` reached `is_installed`'s `lstrip`
    call unchecked and raised `TypeError` instead of landing as a finding —
    caught here, before it is ever asked whether it is installed."""
    declaring_repo.write_config({"specify": [
        {"name": "x", "command": 7, "evidence": "a.md"},
    ]})
    _, problems = _declared.load(declaring_repo.root, is_installed=lambda c: True)
    assert any("'command' that is not a string" in p for p in problems)


def test_no_is_installed_checker_skips_that_one_rule(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """`_pipeline` calls `load` with no checker at all — it does not care
    whether a command is installed, only `check config` does."""
    declaring_repo.write_config({"specify": [
        {"name": "x", "command": "/never-shipped", "evidence": "a.md"},
    ]})
    passes, problems = _declared.load(declaring_repo.root)
    assert problems == []
    assert passes["specify"][0].command == "/never-shipped"


def test_missing_evidence_is_a_finding(declaring_repo: types.SimpleNamespace) -> None:
    declaring_repo.write_config({"specify": [{"name": "x", "manual": True}]})
    _, problems = _declared.load(declaring_repo.root)
    assert any("has no 'evidence'" in p for p in problems)


def test_a_bad_on_finish_value_is_a_finding(declaring_repo: types.SimpleNamespace) -> None:
    declaring_repo.write_config({"specify": [
        {"name": "x", "manual": True, "evidence": "a.md", "on_finish": "immediately"},
    ]})
    _, problems = _declared.load(declaring_repo.root)
    assert any("on_finish 'immediately'" in p for p in problems)


def test_a_pass_declaring_passes_of_its_own_is_a_finding_and_is_not_loaded(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """FR-004: nesting is one level, and the outer pass is dropped rather than
    the whole step's declaration — its siblings still load."""
    declaring_repo.write_config({"specify": [
        {"name": "x", "manual": True, "evidence": "a.md", "steps": {}},
        {"name": "y", "manual": True, "evidence": "b.md"},
    ]})
    passes, problems = _declared.load(declaring_repo.root)
    assert any("passes nest one level below a step" in p for p in problems)
    assert [s.name for s in passes["specify"]] == ["y"]


def test_a_sibling_that_does_not_exist_is_a_finding(
    declaring_repo: types.SimpleNamespace,
) -> None:
    declaring_repo.write_config({"specify": [
        {"name": "x", "manual": True, "evidence": "a.md", "before": "ghost"},
    ]})
    _, problems = _declared.load(declaring_repo.root)
    assert any("names sibling 'ghost'" in p and "not declared" in p for p in problems)


def test_a_non_string_before_is_a_finding(declaring_repo: types.SimpleNamespace) -> None:
    """A JSON array or object in `before` reached `_known`'s `sibling in
    by_name` unchecked and raised `TypeError: unhashable type` instead of
    landing as a finding — caught here, before ordering ever runs."""
    declaring_repo.write_config({"specify": [
        {"name": "x", "manual": True, "evidence": "a.md", "before": ["ghost"]},
    ]})
    _, problems = _declared.load(declaring_repo.root)
    assert any("'before' that is not a string" in p for p in problems)


def test_a_non_string_after_is_a_finding(declaring_repo: types.SimpleNamespace) -> None:
    declaring_repo.write_config({"specify": [
        {"name": "x", "manual": True, "evidence": "a.md", "after": {"ghost": True}},
    ]})
    _, problems = _declared.load(declaring_repo.root)
    assert any("'after' that is not a string" in p for p in problems)


def test_a_pass_naming_itself_as_a_sibling_is_a_finding(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """A self-referencing `before`/`after` adds a self-loop edge that
    `_toposort` never violates (an item's own index never exceeds itself), so
    without this check it settles silently on the first pass instead of
    surfacing as the unsatisfiable order it actually is."""
    declaring_repo.write_config({"specify": [
        {"name": "x", "manual": True, "evidence": "a.md", "before": "x"},
    ]})
    passes, problems = _declared.load(declaring_repo.root)
    assert any("x names itself as a sibling" in p for p in problems)
    assert "specify" not in passes


def test_a_cycle_in_before_after_is_a_finding_not_an_order(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """FR-003a: a repository that wrote a cycle is refused rather than handed
    some order nobody can predict from the file they wrote."""
    declaring_repo.write_config({"specify": [
        {"name": "x", "manual": True, "evidence": "a.md", "before": "y"},
        {"name": "y", "manual": True, "evidence": "b.md", "before": "x"},
    ]})
    passes, problems = _declared.load(declaring_repo.root)
    assert any("the stated order cannot be satisfied" in p for p in problems)
    # wfctl's own passes are unaffected by a declared step's cycle — "specify"
    # has none of its own, so nothing loads for it at all.
    assert "specify" not in passes


def test_malformed_json_is_a_finding(declaring_repo: types.SimpleNamespace) -> None:
    (declaring_repo.root / "wfctl.json").write_text("{not json")
    passes, problems = _declared.load(declaring_repo.root)
    assert any("not valid JSON" in p for p in problems)
    assert passes == _declared._builtin_only()


def test_a_declared_pass_defaults_to_review_required(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """FR-021: wfctl cannot vouch for a command it does not ship."""
    declaring_repo.write_config({"specify": [{"name": "x", "manual": True, "evidence": "a.md"}]})
    passes, _ = _declared.load(declaring_repo.root)
    assert passes["specify"][0].on_finish == "review_required"


def test_an_overridden_automatic_pass_is_indistinguishable_from_a_tool_pass(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """FR-021a, FR-011: nothing on a `SubStep` records which list it came
    from, so a repository that opts a pass into `automatic` produces the
    exact shape a tool-shipped pass has."""
    declaring_repo.write_config({"specify": [
        {"name": "x", "manual": True, "evidence": "a.md", "on_finish": "automatic"},
    ]})
    passes, _ = _declared.load(declaring_repo.root)
    declared_pass = passes["specify"][0]
    builtin_pass = _STEPS["brainstorm"].sub_steps[0]
    assert type(declared_pass) is type(builtin_pass)
    assert declared_pass.on_finish == "automatic"


def test_a_declared_pass_runs_after_wfctls_own_and_before_moves_it_ahead(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """FR-003: written order is the default, and `before` can move a declared
    pass ahead of one of wfctl's own."""
    declaring_repo.write_config({"brainstorm": [
        {"name": "ui-design", "manual": True, "evidence": "a.md"},
    ]})
    passes, problems = _declared.load(declaring_repo.root)
    assert problems == []
    assert [s.name for s in passes["brainstorm"]] == ["architecture", "design-doc", "ui-design"]

    declaring_repo.write_config({"brainstorm": [
        {"name": "ui-design", "manual": True, "evidence": "a.md", "before": "architecture"},
    ]})
    passes, problems = _declared.load(declaring_repo.root)
    assert problems == []
    assert [s.name for s in passes["brainstorm"]] == ["ui-design", "architecture", "design-doc"]


def test_a_step_in_progress_for_its_own_reasons_leaves_its_passes_pending(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """R7 has no row for a parent whose own reading is `in_progress` — only
    `done`, `pending` and `skipped` are named, and the state a not-yet-`done`
    parent's passes report is `pending` in every one of them (data-model.md's
    own table has no "inherits in_progress" row).

    Mirroring the parent's own `in_progress` onto its passes instead — the
    first shape this function had — made a step whose own artifact was merely
    unfinished report every declared pass under it as outstanding at once,
    which is not one of the four states a pass can honestly hold, and is not
    what a repository declaring a pass under `specify` (or any step besides
    `brainstorm`) would see the moment that step's own spec was incomplete.
    """
    from wfctl._pipeline import _infer_steps

    declaring_repo.write_config({"specify": [
        {"name": "extra", "manual": True, "evidence": "x.md"},
    ]})
    spec_dir = declaring_repo.root / "specs" / "1-feature"
    spec_dir.mkdir(parents=True)
    # No required sections — `specify`'s own reading is `in_progress`, not
    # from any pass.
    (spec_dir / "spec.md").write_text("# Spec\n\nincomplete\n")

    steps = _infer_steps(spec_dir, declaring_repo.root)
    specify = next(s for s in steps if s.name == "specify")
    assert specify.state == "in_progress"
    assert [s.state for s in specify.sub_steps] == ["pending"]


def test_a_declared_passes_evidence_resolves_against_the_feature_directory(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """research.md R3: repo-root-relative would leave the pass reading `done`
    on every branch after the first that wrote it — resolved against the
    feature directory, the answer is per branch."""
    from wfctl._evidence import build_evidence

    declaring_repo.write_config({"specify": [
        {"name": "x", "manual": True, "evidence": "seen.md"},
    ]})
    passes, _ = _declared.load(declaring_repo.root)
    reader = passes["specify"][0].reads

    spec_dir = declaring_repo.root / "specs" / "1-feature"
    spec_dir.mkdir(parents=True)
    ev = build_evidence(spec_dir, declaring_repo.root)
    assert reader(ev).state == "in_progress"

    (spec_dir / "seen.md").write_text("x")
    assert reader(ev).state == "done"
    # The repo root itself never gets the file — proof the reader looked in
    # the feature directory and nowhere else.
    assert not (declaring_repo.root / "seen.md").exists()


def test_a_directory_named_as_evidence_is_never_done(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """A directory `.exists()` and generally reports a nonzero `st_size` too,
    so the old check would mark the pass `done` with no file ever written —
    the promised artifact missing and nothing saying so."""
    from wfctl._evidence import build_evidence

    declaring_repo.write_config({"specify": [
        {"name": "x", "manual": True, "evidence": "seen.md"},
    ]})
    passes, _ = _declared.load(declaring_repo.root)
    reader = passes["specify"][0].reads

    spec_dir = declaring_repo.root / "specs" / "1-feature"
    (spec_dir / "seen.md").mkdir(parents=True)
    ev = build_evidence(spec_dir, declaring_repo.root)
    assert reader(ev).state == "in_progress"


def test_a_declared_pass_is_listed_before_the_feature_directory_exists(
    declaring_repo: types.SimpleNamespace,
) -> None:
    """A `pending` step reports its passes, and *why* it is pending must not
    change that.

    `_infer_steps` returns early when no feature directory has been resolved,
    and that arm built bare steps carrying no `sub_steps` at all — so the same
    `pending` step rendered two ways depending on which arm produced it. The
    cascade arm calls `_pass_states` with exactly these arguments, which is the
    shape this one now matches. A consumer reading `status --json` on a branch
    before its spec directory exists could not see the pipeline the repository
    had declared.
    """
    from wfctl._pipeline import _infer_steps

    declaring_repo.write_config({"brainstorm": [
        {"name": "ui-design", "manual": True, "evidence": "x.md"},
    ]})

    steps = _infer_steps(None, declaring_repo.root)
    brainstorm = next(s for s in steps if s.name == "brainstorm")

    assert "ui-design" in [s.name for s in brainstorm.sub_steps]
    assert {s.state for s in brainstorm.sub_steps} == {"pending"}
