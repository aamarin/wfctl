"""Tests for brainstorm's software design pass, and for both brainstorm checks
holding when git can't answer (#648).

On #635 an agent answered the level-3 question with a file layout, and the
pipeline moved on because nothing checked that the question was put. The pass
holds brainstorm until the branch writes a record under `<arch-root>/design/` or
claims the pass with `wfctl step none`. The same change made the architecture
check hold where it used to let a branch through silently, when git can't say
whether a record was written, with `design_record_checks` as the way a
repository whose arch root git can't see turns both checks off.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from wfctl import _paths


def _write_config(repo: Path, config: object) -> None:
    (repo / "wfctl.json").write_text(json.dumps(config))


# --- the `design_record_checks` setting ------------------------------------


def test_a_repo_with_no_wfctl_json_runs_both_checks(tmp_path: Path) -> None:
    """The default has to be on. A repository that never heard of the setting
    is the one the gate was written for, and off-by-default would ship it
    dead."""
    assert _paths.design_record_checks(tmp_path) == (True, [])


def test_a_wfctl_json_without_the_key_runs_both_checks(tmp_path: Path) -> None:
    _write_config(tmp_path, {"trunk": "main"})
    assert _paths.design_record_checks(tmp_path) == (True, [])


def test_on_and_off_are_the_two_values_the_setting_takes(tmp_path: Path) -> None:
    _write_config(tmp_path, {"design_record_checks": "on"})
    assert _paths.design_record_checks(tmp_path) == (True, [])
    _write_config(tmp_path, {"design_record_checks": "off"})
    assert _paths.design_record_checks(tmp_path) == (False, [])


def test_a_typo_leaves_the_checks_on_and_is_reported(tmp_path: Path) -> None:
    """A mistake must never turn a check off. Reading `"no"` or `false` as off
    would let a branch through on a value nobody meant, and the hold this
    feature adds would be gone with nothing saying so."""
    for value in ("yes", "no", False, None):
        _write_config(tmp_path, {"design_record_checks": value})
        on, problems = _paths.design_record_checks(tmp_path)
        assert on is True
        assert problems == [f"'design_record_checks' is {value!r}; use \"on\" or \"off\""]


def test_an_arch_root_outside_the_project_is_a_problem_while_the_checks_are_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every branch in that repo would be held at brainstorm, and `check config`
    is where the maintainer hears it before the first branch does."""
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(tmp_path / "outside"))

    problems = _paths.design_record_checks_problems(repo)
    assert len(problems) == 1
    assert "outside the project" in problems[0]
    assert '"design_record_checks": "off"' in problems[0]

    _write_config(repo, {"design_record_checks": "off"})
    assert _paths.design_record_checks_problems(repo) == []


def test_an_arch_root_inside_the_project_is_no_problem(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(tmp_path / "docs" / "architecture"))
    assert _paths.design_record_checks_problems(tmp_path) == []
