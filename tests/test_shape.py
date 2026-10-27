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
_CLEAN = "✓ {path}: the body looks right"


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


def _epic_sub_issue(storyctl_dir, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Branch `701-sub` with no spec folder of its own, claimed by epic 700's
    Issue Grouping Map, so the spec folder it reads is the epic's (research R11).
    """
    from tests.test_paths import _delivery_map

    epic = storyctl_dir.repo_root / "specs" / "700-epic"
    epic.mkdir(parents=True)
    (epic / "delivery.md").write_text(_delivery_map("#701"))
    monkeypatch.setenv("WFCTL_BRANCH", "701-sub")
    return epic


def test_a_body_missing_an_exceptions_reason_is_a_finding_in_any_repo(
    storyctl_dir, tmp_path: Path
) -> None:
    """Scenario 5.1. The gate reads the spec folder's copy of the answer and the
    reviewer reads the PR body's, and before this nothing compared them. The
    check looks for the reason anywhere in the body, so it names no heading and
    runs in a repo that lists no "Moves a boundary?" section (FR-011)."""
    from wfctl import _design_exceptions

    _design_exceptions.write(storyctl_dir.spec_dir, "boundary", "Copy fix in one help string")
    body = _body_with(tmp_path, "")

    code, output = _check(body)

    assert code == 1
    assert (
        '⚠ the boundary exception\'s reason isn\'t in the body: "Copy fix in one help string"'
        in " ".join(output.split())
    )


def test_a_reason_rewrapped_across_lines_still_matches(storyctl_dir, tmp_path: Path) -> None:
    """Scenario 5.2. An author pasting a reason into a body wraps it to fit,
    and a check that compared bytes would report every wrapped reason missing.
    Whitespace collapses in both texts first."""
    from wfctl import _design_exceptions

    _design_exceptions.write(
        storyctl_dir.spec_dir, "brainstorm.ui-design", "No screen changes in this branch"
    )
    body = _body_with(tmp_path, "## Moves a boundary?\nNo.\n\n- ui-design: No screen\n  changes in this branch\n")

    code, output = _check(body)

    assert "exception reason" not in output
    assert code == 0


def test_a_missing_pass_reason_names_the_pass(storyctl_dir, tmp_path: Path) -> None:
    """One line per missing reason, naming which exception it came from, so the
    author knows which line to add without opening the spec folder."""
    from wfctl import _design_exceptions

    _design_exceptions.write(storyctl_dir.spec_dir, "brainstorm.ui-design", "No screen changes")

    code, output = _check(_body_with(tmp_path, ""))

    assert code == 1
    assert (
        '⚠ brainstorm.ui-design\'s exception reason isn\'t in the body: "No screen changes"'
        in " ".join(output.split())
    )


@pytest.mark.parametrize("record", [True, False], ids=["record", "no-record"])
def test_a_sub_issue_with_a_record_skips_the_epics_boundary_reason(
    storyctl_dir, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, record: bool
) -> None:
    """FR-015. A sub-issue reads its epic's "no new boundary". When the
    sub-issue adds a level-2 record, that record answers the boundary question
    for it, and its PR body says yes and names the record. Without the skip, it
    would have to quote the epic's "no" to pass. Without a record, the epic's
    answer is the sub-issue's too, so the reason is still required."""
    from wfctl import _design_exceptions

    epic = _epic_sub_issue(storyctl_dir, monkeypatch)
    _design_exceptions.write(epic, "boundary", "The epic reuses the review store")
    arch = storyctl_dir.repo_root / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(arch))
    if record:
        arch.mkdir(parents=True)
        (arch / "sub-owns-a-thing.md").write_text("---\nstatus: proposed\n---\n\n# x\n")

    code, output = _check(_body_with(tmp_path, ""))

    assert ("boundary exception's reason" in output) is not record
    assert code == (0 if record else 1)


# --- #649: per-context exceptions in check-body ---------------------------------


def test_a_missing_per_context_reason_is_a_finding_that_names_the_context(
    storyctl_dir, tmp_path: Path
) -> None:
    """The body has to carry each per-context "no", or the reviewer can't check
    what the branch said needed nothing (FR-018)."""
    from wfctl import _design_exceptions

    _design_exceptions.write(
        storyctl_dir.spec_dir, "boundary", "Copy change in the handoff template",
        context="session-continuity",
    )

    code, output = _check(_body_with(tmp_path, ""))

    assert code == 1
    assert (
        "⚠ the boundary exception for session-continuity: its reason isn't in the body: "
        '"Copy change in the handoff template"' in " ".join(output.split())
    )


def test_a_per_context_reason_in_the_body_passes(storyctl_dir, tmp_path: Path) -> None:
    from wfctl import _design_exceptions

    _design_exceptions.write(
        storyctl_dir.spec_dir, "boundary", "Copy change", context="session-continuity"
    )

    code, output = _check(_body_with(tmp_path, "- session-continuity: Copy change\n"))

    assert code == 0, output


@pytest.mark.parametrize(
    "governs, skipped",
    [("session-continuity", True), ("install-and-drift", False)],
    ids=["same context", "other context"],
)
def test_an_inherited_per_context_no_is_skipped_only_for_a_record_about_that_context(
    storyctl_dir, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, governs: str, skipped: bool
) -> None:
    """#653. A sub-issue branch's record answers its own context. Every other
    inherited "no" stays true, so the body still quotes it and the reviewer can
    check the branch didn't break it. #635's rule skips on any record, which
    would let a record about `install-and-drift` hide the epic's "no" for
    `session-continuity`."""
    from wfctl import _design_exceptions

    epic = _epic_sub_issue(storyctl_dir, monkeypatch)
    _design_exceptions.write(epic, "boundary", "The epic changes no hooks", context="session-continuity")
    arch = storyctl_dir.repo_root / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(arch))
    arch.mkdir(parents=True)
    (arch / "sub-owns-a-thing.md").write_text(
        f"---\nstatus: proposed\ngoverns: {governs}\n---\n\n# x\n"
    )

    code, output = _check(_body_with(tmp_path, ""))

    assert ("session-continuity" in output) is not skipped
    assert code == (0 if skipped else 1)
