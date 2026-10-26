"""The review-panel skill drives each group through wfctl, and its layering
stays intact.

The panel skill once checked its own roster with two bash fences, and this
file ran them under `sh` and zsh. wfctl now holds that check: `wfctl review
start` writes the reviewers it expects, and `wfctl review check` judges the
reports against them (`tests/test_review.py`, `tests/test_review_cli.py`). What
is left here is whether the skill sends a coordinator through those commands,
and the layering: the skill's value is that it orchestrates three skills it
does not own, and both halves of that, naming them and not restating their
contents, fail silently.
"""
import re
from importlib.resources import files
from pathlib import Path

import pytest

from tests import test_review

_AGENTS = Path(str(files("wfctl"))) / "agents"
_SKILL = _AGENTS / "skills" / "fanning-out-code-review" / "SKILL.md"

_FENCE = re.compile(r"```bash\n(.*?)```", re.DOTALL)
_REFERENCE = re.compile(r"\.agents/skills/([a-z0-9][a-z0-9-]*)")


def _prose() -> str:
    """The skill with whitespace collapsed, so a rewrap of the prose can't fail
    an unchanged sentence."""
    return " ".join(_SKILL.read_text().split())


def test_the_skill_names_the_test_that_holds_the_verdict_spellings_open() -> None:
    """The skill points at a test by name, which a rename leaves aimed at
    nothing, and the pointer is prose, so no check but this one can see it
    (#218). The spellings moved to `tests/test_review.py` when wfctl took over
    judging reports, and the pointer moved with them.

    The name is read off the function rather than written out again. Spelled as
    a literal, this test compares one dead string against another and agrees
    with itself after a rename of the `def` alone.
    """
    assert (
        test_review.test_report_counts_with_each_verdict_spelling_reviewers_use.__name__
        in _SKILL.read_text()
    )


def test_the_skill_starts_each_group_with_wfctl_in_the_order_it_lists() -> None:
    """FR-026. wfctl writes the run record the guard later reads, so a group
    the coordinator ran without `review start` leaves the branch unreviewed
    however good the reports were."""
    fences = _FENCE.findall(_SKILL.read_text())

    assert any(f.strip() == "wfctl review groups" for f in fences)
    assert any(f.strip().startswith("wfctl review start ") for f in fences)
    assert "Run this skill once per group, in that order." in _prose()


def test_the_skill_shows_the_round_in_the_start_header_and_the_cap_outcomes() -> None:
    """FR-014. `review start` prints `round N of M` in the header, and at the
    cap it either finds nothing left to review or refuses. The coordinator has
    to know which of the two to follow, since one goes on to the next group and
    the other stops."""
    prose = _prose()

    assert (
        "security run 003 · round 3 of 3 · 2 commits since a1b2c3d · head 9f8e7d6"
    ) in prose
    assert (
        "When a sign-off covers every commit left at the cap, `review start` says "
        "nothing is left to review and exits 0. Go on to the next group."
    ) in prose
    assert (
        "When it refuses at the cap, stop and follow `opening-a-change` Step 1, "
        "which asks the user for a sign-off."
    ) in prose


def test_the_skill_launches_one_reviewer_per_id_with_only_the_reports_folder() -> None:
    """`reviewing-security` reads the run's commits from `run.json` (#636). A
    range handed over beside it would be built with `git log`, which includes
    the merge commits wfctl leaves out, so a reviewer would report code the
    branch didn't write."""
    prose = _prose()

    assert "Launch one reviewer per id `review start` printed" in prose
    assert "give each one only two values: its id and the reports folder" in prose
    assert "Don't give a reviewer a commit range" in prose
    assert "Review the commits listed in `run.json` in the reports folder" in prose


def test_the_skill_tells_each_reviewer_to_name_the_head_and_end_on_a_verdict() -> None:
    """R2. wfctl counts a report only with both, so a reviewer never told
    either writes a report that never counts."""
    prose = _prose()

    assert "Write the report to `<reports folder>/<id>.md`." in prose
    assert "`Reviewed: <sha>` line naming the run's head" in prose
    assert "its last line is the verdict" in prose


def test_the_skill_relays_a_blocked_report_from_a_file_and_never_from_text() -> None:
    """R8. A security report quotes `gh pr create`, which the guard refuses in
    a command's text while the branch is unreviewed, so a report pasted into a
    heredoc never arrives."""
    relays = [f for f in _FENCE.findall(_SKILL.read_text()) if "wfctl relay" in f]

    assert relays, "no fence shows wfctl relay"
    assert all(re.search(r'wfctl relay \S+ --reason "[^"]+" --from \S+', f) for f in relays)
    assert "Never put a report in a command's text," in _prose()


def test_the_skill_checks_a_relay_reason_against_what_the_coordinator_saw() -> None:
    """`622-blocked-reviewer-relays-report.md`. A reviewer that could write and
    didn't is a gap the roster can't show, and only the coordinator saw it."""
    prose = _prose()

    assert "Check each relay reason against what you saw." in prose
    assert "If the reviewer wasn't really blocked" in prose


def test_the_skill_finishes_each_group_with_wfctl_review_check() -> None:
    """The coordinator would otherwise be grading its own panel
    (`review-covers-unreviewed-commits`)."""
    fences = _FENCE.findall(_SKILL.read_text())

    assert any(f.strip().startswith("wfctl review check ") for f in fences)
    assert "you don't count them yourself" in _prose()


def test_the_skill_no_longer_writes_reports_under_the_feature_dir() -> None:
    """Reports live in the branch's state directory now, and a reviewer told to
    write to `$FEATURE_DIR/reviews/` would write a report wfctl never reads."""
    text = _SKILL.read_text()

    assert "$FEATURE_DIR/reviews" not in text
    assert "wfctl feature-paths" not in text


def test_the_panel_skill_names_every_skill_it_layers_over() -> None:
    """The whole layering is carried by these three references and nothing else.

    Drop one and the panel quietly becomes a second account of what that skill
    owns — the reviewer hand-off, the rubric, or verify-before-implementing —
    which is the duplication `knowledge-placement` and #50 are about. Not
    `vendor-upstream-skills`: it lists two of the three as superpowers-derived
    and not the third, so it explains why two of them are layered over rather
    than edited — not why the panel defers to all three.
    """
    named = set(_REFERENCE.findall(_SKILL.read_text()))
    for skill in ("requesting-code-review", "code-review", "receiving-code-review"):
        assert skill in named, skill


def test_the_panel_skill_does_not_restate_the_rubric() -> None:
    """The reviewers run `code-review`; a copy of its passes here is a second
    home for a fact wfctl ships one copy of (#50), and it would contradict
    `code-review`'s own "one review instead of four overlapping ones" the moment
    either file moved. Derived from `code-review`'s pass headings rather than a
    hardcoded list, so a renamed pass keeps the check honest."""
    rubric = (_AGENTS / "skills" / "code-review" / "SKILL.md").read_text()
    passes = re.findall(r"^\*\*\d\. ([A-Za-z][A-Za-z &-]*)\*\*", rubric, re.MULTILINE)
    assert len(passes) == 6, passes

    skill = _SKILL.read_text()
    restated = sorted(p for p in passes if f"**{p}" in skill)

    assert restated == []


def test_the_panel_skill_is_model_invocable() -> None:
    """The trigger is a change about to be merged, which is a moment nobody
    types a command (#124). Membership in `_MIRRORED_SKILLS` is what puts the
    skill on Claude's native discovery path; without it the command wrapper is
    the only way in, which is the failure being designed out."""
    from wfctl import _arch
    from wfctl.cli import _MIRRORED_SKILLS

    assert "fanning-out-code-review" in _MIRRORED_SKILLS
    # Column-zero keys only, via the same parser the frontmatter test uses:
    # the prose explaining why the key is absent names it, and a substring
    # search would read that explanation as the key it forbids.
    assert "disable-model-invocation" not in _arch._frontmatter(_SKILL.read_text())


def test_the_dispatch_list_requires_the_coverage_the_clean_row_reproduces() -> None:
    """Step 5 gives a reviewer that found nothing a row whose Finding cell
    carries what its report covered, and `code-review` Step 5 ends a clean
    report at the over-engineering metric and a verdict. Codex caught the gap on
    #369: the coverage requirement was stated only where the coordinator reads
    it, and a dispatched reviewer never does, so every clean run asked the
    coordinator for evidence no reviewer was told to produce. The count is
    checked against the lead-in rather than hardcoded, because a bullet added
    later that leaves the number behind is the same defect one word smaller."""
    skill = _SKILL.read_text()

    words = {"three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}
    lead_in = re.search(
        r"Every dispatch instruction carries these ([a-z]+):\n\n(.*?)\n\n[^-]",
        skill,
        re.DOTALL,
    )
    assert lead_in is not None, "the dispatch list's lead-in moved or was reworded"

    bullets = re.findall(r"^- \*\*(.+?)\*\*", lead_in.group(2), re.MULTILINE)
    assert len(bullets) == words[lead_in.group(1)], (lead_in.group(1), bullets)

    covering = [b for b in bullets if "which passes ran" in b]
    assert covering, bullets


@pytest.mark.parametrize(
    "start, end",
    [
        ("## Step 2: Dispatch", "### A reviewer on another model"),
        ("**A finished reviewer with no counted report gets asked again.**",
         "Run `wfctl review check` again"),
    ],
    ids=["dispatch", "re-ask"],
)
def test_the_panel_sends_its_reviewers_to_the_rubric_by_path(start: str, end: str) -> None:
    """A reviewer told to follow the `code-review` skill by name reached Claude
    Code's built-in `/code-review` instead, on #464's panel and again on #500's.
    That command fans out helper agents that never receive the dispatch rules,
    and on both panels an agent running under it edited the shared tree (#468).

    The path alone does not stop a reviewer reaching for the Skill tool, so the
    prohibition is pinned beside it. The re-ask is pinned too, because a re-ask
    worded by name sends a reviewer back to the command that swallowed its first
    report.

    Both anchors are asserted because a reworded end anchor would otherwise run
    the dispatch section on into the re-ask, which carries the same wording and
    passes it for a dispatch bullet reverted to the bare name. Whitespace is
    collapsed so a rewrap of the prose cannot fail an unchanged sentence."""
    skill = _SKILL.read_text()
    assert start in skill and end in skill, (start, end)
    section = " ".join(skill.split(start)[1].split(end)[0].split())

    assert "code-review" in _REFERENCE.findall(section)
    assert "Skill named `code-review`" in section
