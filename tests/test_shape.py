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
# a consuming project installs is the copy under question. This repository's own
# copy differs from it by the "Type of Change" section, which `test_install_config`
# compares around.
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


_SKILL = (
    Path(__file__).resolve().parent.parent
    / "wfctl/agents/skills/opening-a-change/SKILL.md"
)


def test_the_cited_section_still_holds_the_rule_the_finding_names() -> None:
    """The finding and the template send the reader to "Choosing a drawing" by
    name. A line number went stale here once already while this file stayed
    green, since nothing read the line it pointed at; a heading is only safer if
    something checks that the heading is still there and still says the rule."""
    skill = _SKILL.read_text()
    assert "\n## Choosing a drawing\n" in skill
    section = skill.split("\n## Choosing a drawing\n")[1].split("\n## ")[0]
    assert "**Tabular content goes in a table.**" in section
    assert "flows, trees and timelines" in " ".join(section.split())
    assert "\"Choosing a drawing\"" in _TEMPLATE.read_text()


def test_the_drawing_the_reader_rejected_is_flagged() -> None:
    """PR #208's second drawing, verbatim. The reader called it "noisy and
    confusing"; `opening-a-change`'s "Choosing a drawing" names the fault exactly — tabular
    content aligned by hand, with a cell that outgrew its header."""
    found = _shape.body_findings(REJECTED)
    assert len(found) == 1
    assert 'opening-a-change, "Choosing a drawing"' in found[0]
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


# --- check-body and the sections a repository lists -------------------------

_SECTION = "Needs a spec?"
_SECTION_COMMENT = "<!--\nDid this change need a full spec? Answer yes or no, then give the reason.\n-->"
_CLEAN = "✓ {path}: the drawings look right"


def _sections_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, config: dict | None
) -> Path:
    """A repository root declaring no definition of done, so the verification
    finding stays silent and a run reports only what these tests are about.

    `config` is written verbatim, or no `wfctl.json` at all when None. The
    absent-key rows of `contracts/cli.md` need both.
    """
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    if config is not None:
        (repo / "wfctl.json").write_text(json.dumps(config))
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo))
    return repo


def _body_with(tmp_path: Path, section: str) -> Path:
    body = tmp_path / "body.md"
    body.write_text(f"# Pull Request\n\n## Summary\n\nsomething\n\n{section}\n")
    return body


def _check(path: Path) -> tuple[int, str]:
    result = runner.invoke(app, ["check-body", str(path)])
    return result.exit_code, result.output


def test_an_answered_section_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _sections_repo(tmp_path, monkeypatch, {"change_sections": [_SECTION]})
    body = _body_with(
        tmp_path, f"## {_SECTION}\n{_SECTION_COMMENT}\nNo. It moves no boundary.\n"
    )
    code, output = _check(body)
    assert code == 0
    assert _CLEAN.format(path=body) in output.replace("\n", "")


@pytest.mark.parametrize(
    ("section", "finding"),
    [
        (
            "",
            f'"{_SECTION}" is missing. This repository asks every pull request to answer it.',
        ),
        (
            f"## {_SECTION}\n{_SECTION_COMMENT}\n",
            f'"{_SECTION}" is empty. The template\'s comment under that heading says what to write.',
        ),
        (
            f"## {_SECTION}\n{_SECTION_COMMENT}\nN/A\n",
            f'"{_SECTION}" holds N/A. The template\'s comment under that heading says what to write.',
        ),
        (
            f"## {_SECTION}\n{_SECTION_COMMENT}\nNo.\n",
            f'"{_SECTION}" answers yes or no with no reason. '
            "The template's comment under that heading says what to write.",
        ),
    ],
    ids=["deleted", "comment-only", "n-a", "bare-no"],
)
def test_a_listed_section_with_no_answer_is_a_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, section: str, finding: str
) -> None:
    """One row per bad body in `contracts/cli.md`: each prints its own line and
    exits 1, so an agent told only the line knows which of the four it did."""
    _sections_repo(tmp_path, monkeypatch, {"change_sections": [_SECTION]})
    code, output = _check(_body_with(tmp_path, section))
    assert code == 1
    assert f"⚠ {finding}" in " ".join(output.split())


@pytest.mark.parametrize("config", [None, {}, {"change_sections": []}])
@pytest.mark.parametrize(
    "section",
    [
        "",
        f"## {_SECTION}\n{_SECTION_COMMENT}\n",
        f"## {_SECTION}\nN/A\n",
        f"## {_SECTION}\nNo.\n",
    ],
    ids=["deleted", "comment-only", "n-a", "bare-no"],
)
def test_a_repository_listing_no_sections_sees_what_it_saw_before(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    config: dict | None,
    section: str,
) -> None:
    """SC-003: opting in is the only way to get the new findings. With no key,
    an empty list, or no `wfctl.json` at all, the four bodies that fail above
    print today's clean line and exit 0."""
    _sections_repo(tmp_path, monkeypatch, config)
    body = _body_with(tmp_path, section)
    code, output = _check(body)
    assert code == 0
    assert _CLEAN.format(path=body) in output.replace("\n", "")


def test_a_malformed_key_is_reported_by_check_body_too(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A value that is not a list would otherwise turn the check off with no
    output, in the command the author is running at that moment."""
    _sections_repo(tmp_path, monkeypatch, {"change_sections": "x"})
    code, output = _check(_body_with(tmp_path, f"## {_SECTION}\nNo.\n"))
    assert code == 1
    assert "wfctl.json: 'change_sections' must be a list of section headings" in " ".join(
        output.split()
    )


def test_section_findings_sit_between_the_drawing_and_verification_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The order in `contracts/cli.md`, so a reader meets the drawing fault
    first and the verification line, which every unverified branch shows, last."""
    repo = _sections_repo(tmp_path, monkeypatch, {"change_sections": [_SECTION]})
    (repo / "wfctl.json").write_text(
        json.dumps({"change_sections": [_SECTION], "verify": ["true"]})
    )
    body = tmp_path / "body.md"
    body.write_text(REJECTED)
    code, output = _check(body)
    flat = " ".join(output.split())
    assert code == 1
    assert flat.index("line ") < flat.index(f'"{_SECTION}" is missing') < flat.index(
        "verification"
    )


def test_outside_a_repository_check_body_reads_no_sections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """There is no `wfctl.json` to read, the way `_verification_finding` already
    returns nothing there."""
    monkeypatch.delenv("WFCTL_REPO_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)
    body = _body_with(tmp_path, "")
    code, output = _check(body)
    assert code == 0
    assert _SECTION not in output
