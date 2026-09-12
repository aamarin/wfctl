"""The review-panel skill's roster check runs, and its layering stays intact.

The roster check is the only thing standing between a reviewer that silently
returned nothing and a pass recorded as clean — the failure #133 was filed for.
It is a shell command inside a skill, so it ships whether or not it works;
`test_skill_commands` exists because that same shape was wrong twice in
`opening-a-change`. The rest of this file guards the layering: the skill's value
is that it orchestrates three skills it does not own, and both halves of that —
naming them, and not restating their contents — fail silently.
"""
import re
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path

_AGENTS = Path(str(files("wfctl"))) / "agents"
_SKILL = _AGENTS / "skills" / "fanning-out-code-review" / "SKILL.md"

_FENCE = re.compile(r"```bash\n(.*?)```", re.DOTALL)
_REFERENCE = re.compile(r"\.agents/skills/([a-z0-9][a-z0-9-]*)")


def _roster_command() -> str:
    """The one fenced block that checks the roster. Keyed on content rather than
    position: Step 1's `wfctl feature-paths` is also a bash fence, and reordering
    the steps must not silently retarget this test at it."""
    blocks = [b for b in _FENCE.findall(_SKILL.read_text()) if "MISSING" in b]
    assert len(blocks) == 1, f"expected one roster fence, found {len(blocks)}"
    return blocks[0]


def _run(shell: str, bin_dir: Path) -> list[str]:
    """Nothing is injected but a `PATH` carrying the `wfctl` stub.

    `FEATURE_DIR` has to arrive the way the skill says it does — the fence calls
    `wfctl feature-paths` and evals it. Handing the variable in directly would
    test the loop while assuming away the step that binds what the loop reads,
    which is the defect this command shipped with twice: once with the name
    never bound at all, once with it bound only in an earlier shell that no
    longer exists by the time the check runs.
    """
    # `zsh -f` skips the startup files; `sh` has none to skip and reads `-f` as
    # "no globbing", so the flag cannot simply be passed to both. Without it,
    # /etc/zprofile runs `path_helper`, which prepends the login PATH and puts
    # the real `wfctl` ahead of the stub — the fence then reports on whatever
    # repo the test happens to run in.
    argv = [shell, "-f", "-c"] if shell == "zsh" else [shell, "-c"]
    out = subprocess.run(
        [*argv, _roster_command()],
        env={"PATH": f"{bin_dir}:/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )
    return out.stdout.split()


def _fixture(feature_dir: Path) -> Path:
    """One reviewer that reported, one that came back having written an empty
    file, and one still running — plus a `wfctl` stub printing the assignment
    the real one prints. Returns the directory to put on `PATH`.

    The three reviewers are the three states the loop can print, so one fixture
    exercises all of them. `r3` is absent from the fence's `RETURNED` list and
    writes nothing, which is what makes it a running reviewer rather than a dead
    one — the distinction #173 is about. Both halves are load-bearing, and
    `test_a_report_on_disk_outranks_an_incomplete_returned_list` is what holds
    them apart.
    """
    reviews = feature_dir / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "r1.md").write_text("BLOCKER cli.py:L1 — …\n")
    (reviews / "r2.md").write_text("")

    bin_dir = feature_dir / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "wfctl"
    stub.write_text(f"#!/bin/sh\necho \"FEATURE_DIR='{feature_dir}'\"\n")
    stub.chmod(0o755)
    return bin_dir


def test_the_roster_check_tells_the_three_states_apart(tmp_path: Path) -> None:
    """One word per state, and the two that mean *nothing on disk* differ.

    A reviewer that returns nothing is indistinguishable from one that found
    nothing, and in the run this skill was written from, the agent asserted the
    second — so an empty report still has to read as MISSING. #173 is the other
    half: on that same first run three reports landed across three minutes with
    the largest last, a roster read in that window said two of three, and the
    session was told to re-dispatch a reviewer that was working. `r2` came back
    empty and `r3` has not come back, and the loop is only useful if it says so
    in different words — both are non-empty output, so a check counting lines
    would pass the bug this asserts against.
    """
    bin_dir = _fixture(tmp_path)

    assert _run("sh", bin_dir) == [
        "reported", "r1", "MISSING", "r2", "RUNNING", "r3",
    ]


def test_a_report_on_disk_outranks_an_incomplete_returned_list(
    tmp_path: Path,
) -> None:
    """`RETURNED` answers one question — has this reviewer stopped — and it is
    asked only about a reviewer that wrote nothing.

    A panel where every reviewer reported is the one an agent is likeliest to
    hand a half-updated `RETURNED`, and nesting the two tests the other way
    round reads that as a reviewer still running, so the panel waits on a
    reviewer already back and its findings sit unread on disk — the step
    contradicting its own "against the disk, not against what you remember
    receiving".
    """
    bin_dir = _fixture(tmp_path)
    (tmp_path / "reviews" / "r3.md").write_text("BLOCKER cli.py:L9 — …\n")

    assert _run("sh", bin_dir) == [
        "reported", "r1", "MISSING", "r2", "reported", "r3",
    ]


def test_the_roster_check_survives_zsh(tmp_path: Path) -> None:
    """Same reason as `test_skill_commands`: the shell an agent runs this in on
    macOS is zsh, CI's is not, and the first bug in the sibling command was zsh
    treating a construct differently. Skipped where zsh is absent."""
    if not shutil.which("zsh"):
        return
    bin_dir = _fixture(tmp_path)

    assert _run("zsh", bin_dir) == _run("sh", bin_dir)


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


def _undispatched_command() -> str:
    """The one fenced block that checks the other direction. Keyed on content
    for the same reason as `_roster_command`, and disjoint from it: that one
    matches on `MISSING`, a word this fence must not carry — `UNDISPATCHED` is
    not a fourth roster state and the skill says so."""
    blocks = [
        b for b in _FENCE.findall(_SKILL.read_text()) if "UNDISPATCHED" in b
    ]
    assert len(blocks) == 1, f"expected one undispatched fence, found {len(blocks)}"
    assert "MISSING" not in blocks[0]
    return blocks[0]


def _run_undispatched(shell: str, bin_dir: Path) -> list[str]:
    argv = [shell, "-f", "-c"] if shell == "zsh" else [shell, "-c"]
    out = subprocess.run(
        [*argv, _undispatched_command()],
        env={"PATH": f"{bin_dir}:/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )
    return out.stdout.split()


def test_a_report_from_outside_the_roster_is_named_and_not_counted(
    tmp_path: Path,
) -> None:
    """The panel is the ids you dispatched, and a report from anywhere else is
    not a member of it however good the finding is.

    This is the run in #205: two agents nobody dispatched reported on the same
    diff, split by axis — the shape this skill forbids — and one of their
    findings was a real defect the panel confirmed independently forty minutes
    later. A session that read the reports in hand rather than the roster folds
    that in and has no reason to notice, so the check has to name the source
    rather than judge the finding. The two names here are the two shapes that
    actually arrived, not invented ids: neither is `r`-prefixed, and an
    implementation testing for the prefix instead of for roster membership would
    pass this and miss a fork dispatched as `r4`.
    """
    bin_dir = _fixture(tmp_path)
    reviews = tmp_path / "reviews"
    (reviews / "correctness-angles.md").write_text("BLOCKER cli.py:L1 — …\n")
    (reviews / "r4.md").write_text("BLOCKER cli.py:L2 — …\n")

    assert _run_undispatched("sh", bin_dir) == [
        "UNDISPATCHED", "correctness-angles", "UNDISPATCHED", "r4",
    ]


def test_the_undispatched_check_is_silent_on_a_clean_panel(tmp_path: Path) -> None:
    """Every line it prints is a failure, so a panel with nothing wrong prints
    nothing — including the two states the roster loop is about. `r2` came back
    empty and `r3` never wrote at all, and neither is this check's business: an
    implementation that flagged a dispatched id for having written nothing would
    duplicate the roster loop and contradict it, since that loop's own answer for
    `r3` is `RUNNING`."""
    bin_dir = _fixture(tmp_path)

    assert _run_undispatched("sh", bin_dir) == []


def test_the_undispatched_check_survives_an_empty_reviews_directory(
    tmp_path: Path,
) -> None:
    """A reviews directory with nothing in it is the normal state between
    dispatch and the first report, and it is where a bare `"$REVIEWS"/*.md`
    fails: zsh aborts the whole script on a glob that matches nothing, so the
    check would not run at all on the shell most of these runs happen in — and
    `sh` leaves the pattern unexpanded and reports the literal `*` as a stranger.
    Both failures are in the fence, not in the panel."""
    _fixture(tmp_path)
    reviews = tmp_path / "reviews"
    for report in reviews.iterdir():
        report.unlink()
    bin_dir = tmp_path / "bin"

    assert _run_undispatched("sh", bin_dir) == []
    if shutil.which("zsh"):
        assert _run_undispatched("zsh", bin_dir) == []


def test_the_undispatched_check_survives_zsh(tmp_path: Path) -> None:
    """Same reason as the roster check: the shell these runs happen in on macOS
    is zsh and CI's is not."""
    if not shutil.which("zsh"):
        return
    bin_dir = _fixture(tmp_path)
    (tmp_path / "reviews" / "correctness-angles.md").write_text("BLOCKER — …\n")

    assert _run_undispatched("zsh", bin_dir) == _run_undispatched("sh", bin_dir)
