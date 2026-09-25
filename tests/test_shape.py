"""Tests for `wfctl._shape.body_findings` and `check-body`, the command that
runs it.

The detector judges a PR body's drawings, so what these assert is the
*boundary* it draws, not merely that it fires: a false positive on the drawing
form the form-selection table recommends most often is worse than a missed one.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl import _shape
from wfctl.cli import app

runner = CliRunner()

# The shipped template, read through the package rather than the repo root: what
# a consuming project installs is the copy under question, and the two are held
# byte-identical by `test_install_config`.
_TEMPLATE = (
    Path(__file__).resolve().parent.parent
    / "wfctl/agents/configs/github/.github/pull_request_template.md"
)


REJECTED = """```
  1. directory named 567-*  ------------------------------ none
  2. issue-key glob "567"   ------------------------------ none
  3. NEW  a delivery.md whose grouping map names 567
          555-taxonomy-redesign  claims 567 ------------- resolved
  4. ancestor branches, nearest first
          562-transaction-balance      -> specs/562-...
                                         BEFORE: returned it
                                         AFTER: its map claims 575
                                            and 576, not 567 - a decomposed
                                            feature that had its chance to
                                            name us and did not. Skipped.
```
"""

ACCEPTED = """```
BEFORE                                   AFTER
$ wfctl status                           $ wfctl status
brainstorm   *                           brainstorm   *
implement    *  46/46 done               implement    *  5/64 done
                 ^                                        ^
     feature 562's task list,                 feature 555's task list
```
"""


def test_the_drawing_the_reader_rejected_is_flagged() -> None:
    """PR #208's second drawing, verbatim. The reader called it "noisy and
    confusing"; opening-a-change/SKILL.md:234 names the fault exactly — tabular
    content aligned by hand, with a cell that outgrew its header."""
    found = _shape.body_findings(REJECTED)
    assert len(found) == 1
    assert "opening-a-change/SKILL.md:234" in found[0]
    assert "name us and did not. Skipped." in found[0]


def test_the_drawing_the_reader_accepted_is_not_flagged() -> None:
    """The same PR body's first drawing, which nobody objected to. It is hand
    aligned too — two columns is the form-selection table's most frequent row —
    so alignment alone would have flagged the fix along with the fault."""
    assert not _shape.body_findings(ACCEPTED)


def test_check_body_names_the_file_it_cannot_read() -> None:
    result = runner.invoke(app, ["check-body", "/nonexistent/body.md"])
    assert result.exit_code == 1
    assert "body.md" in result.output


def test_check_body_exits_one_on_a_finding_and_zero_without(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exit 1 so the finding is hard to walk past. It gates nothing — nothing
    runs this but the author.

    `WFCTL_REPO_ROOT` points at a directory with no `wfctl.json`, which silences
    the verification finding the command also reports (#236). Without it these
    two assertions read the repository they run in, and the drawing rules under
    test here would be decided by whether someone had run `wfctl verify` on the
    branch — the machine-dependence `NO_COLOR` is pinned against, arriving by a
    different door.
    """
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(tmp_path))
    bad = tmp_path / "bad.md"
    bad.write_text(REJECTED)
    good = tmp_path / "good.md"
    good.write_text(ACCEPTED)
    assert runner.invoke(app, ["check-body", str(bad)]).exit_code == 1
    assert runner.invoke(app, ["check-body", str(good)]).exit_code == 0


def test_the_template_wfctl_ships_passes_its_own_drawing_check() -> None:
    """The repository would otherwise be shipping a template its own command
    rejects, and nobody would find out from a green suite.

    Asserted since #347, which deleted the one test that ran `check-body` over
    this file — that one pinned the panel rule and asserted the template *failed*
    until it was filled in. The drawing rules read the fenced blocks the template
    still carries, so a later `_shape` change can start flagging an unfilled
    template with no other test in the way.
    """
    assert _shape.body_findings(_TEMPLATE.read_text(encoding="utf-8")) == []


def test_both_sources_report_in_one_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`check-body` is a sum of two finding sources, and nothing else asserts
    they compose — each of the other tests silences one to read the other.

    A `return` on the first non-empty source would pass every one of those and
    still hide a drawing fault behind an unverified branch, which is the half a
    reader is likeliest to act on.
    """
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / "wfctl.json").write_text(json.dumps({"verify": ["true"]}))
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))

    body = tmp_path / "body.md"
    body.write_text(REJECTED)
    result = runner.invoke(app, ["check-body", str(body)])

    assert result.exit_code == 1
    assert "line " in result.output, result.output
    assert "verification" in result.output, result.output


def test_an_unclosed_fence_is_a_block_even_though_it_never_closes() -> None:
    """A body cut off mid-block still reports a drawing finding, however badly
    its columns were aligned — `_blocks` treats an unclosed fence as a block
    rather than as a still-open, unscanned tail.
    """
    body = "intro\n```\nA   ok. Then more.\nB   also. Also more.\nC   yes. Yes more.\n"
    assert _shape.body_findings(body)
    assert "line 2" in _shape.body_findings(body)[0]
