"""`wfctl doctor --session` leaves out claim notices about other issues (#432).

`doctor` prints a notice for every issue two spec folders both claim. This
repository has four, and every session start printed all four, 17 lines that
concern none of the branches reading them. A skill instruction to ignore them
still spends the tokens, so wfctl filters them instead
(`432-doctor-session-scopes-claim-notices`).

`NO_COLOR` is set once in `conftest.py`, since these assert on console text.
"""
from __future__ import annotations

import types

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def _claim_twice(storyctl_dir: types.SimpleNamespace, *keys: str) -> None:
    specs = storyctl_dir.repo_root / "specs"
    for key in keys:
        for slug in ("a", "b"):
            (specs / f"{key}-{slug}").mkdir(parents=True)


def _doctor(*flags: str) -> tuple[int, str]:
    result = runner.invoke(app, ["doctor", *flags])
    return result.exit_code, result.output


def test_another_issues_notice_is_left_out_and_the_branchs_own_is_kept(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A notice for the branch's own issue still prints, since that conflict
    decides which spec folder the branch resolves to."""
    _claim_twice(storyctl_dir, "11", "418")
    code, out = _doctor("--session")
    assert "issue 11 is claimed" not in out
    assert "issue 418 is claimed" in out


def test_plain_doctor_still_prints_every_notice(storyctl_dir: types.SimpleNamespace) -> None:
    """The notices are useful when someone runs `doctor` to check the whole
    repository, so the flag is the only thing that filters them."""
    _claim_twice(storyctl_dir, "11", "418")
    _, out = _doctor()
    assert "issue 11 is claimed" in out
    assert "issue 418 is claimed" in out


def test_a_trunk_branch_prints_no_claim_notice(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    _claim_twice(storyctl_dir, "11")
    monkeypatch.setenv("WFCTL_BRANCH", "main")
    _, out = _doctor("--session")
    assert "is claimed" not in out
    assert "Settle one by renaming" not in out


def test_everything_else_and_the_exit_code_match_plain_doctor(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Removing the other issues' notices is the whole difference, in a clean
    tree and in one with a finding that sets the exit code."""
    _claim_twice(storyctl_dir, "11")

    def without_notices(out: str) -> list[str]:
        lines, skip = [], False
        for line in out.splitlines():
            if line.startswith("ℹ issue "):
                skip = True
                continue
            if skip and line.startswith(" "):
                continue
            skip = False
            lines.append(line)
        return lines

    for drifted in (False, True):
        if drifted:
            (storyctl_dir.repo_root / "wfctl.json").write_text("{not json")
        plain_code, plain = _doctor()
        session_code, session = _doctor("--session")
        assert session_code == plain_code
        assert without_notices(session) == without_notices(plain)
    assert plain_code == 1
