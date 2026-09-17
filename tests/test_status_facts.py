"""The readiness facts, and the two situations they exist to tell apart (#299).

A step state answered several questions with several owners, and the payload
carried one value for all of them. There were four facts until #384 removed the
outward-action grant the fourth one read. The test that matters here is the first pair below:
before this feature, a branch whose architecture record was still `proposed` and
one whose record had been accepted produced byte-identical output, and a reader
could not see the difference the whole pipeline turns on.

`NO_COLOR` is pinned by `conftest.py`. Without it rich colorizes on the terminal
and every console assertion here becomes machine-dependent.
"""
from __future__ import annotations

import json
import subprocess
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl import _evidence
from wfctl._pipeline import build_report
from wfctl.cli import _FACT_GLYPH, _STATE_GLYPH, app

runner = CliRunner()

FACT_NAMES = (
    "artifacts written",
    "definition of done",
    "architecture accepted",
)

RECORD = """---
status: {status}
---

# A decision

## Log

- 2026-09-10  {status}
"""


def _record(repo_root: Path, slug: str, status: str) -> Path:
    """One record under this repo's arch root, at `status`.

    Left untracked. `records_on_this_branch` counts `git status --porcelain
    -uall`, so an uncommitted record is on the branch — which is the common case
    it was written for, a record produced moments ago by the session under test.
    """
    path = repo_root / "docs" / "architecture" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(RECORD.format(status=status))
    return path


def _payload() -> dict:
    return json.loads(runner.invoke(app, ["status", "--json"]).output)


def _facts() -> dict[str, dict]:
    return {f["name"]: f for f in _payload()["facts"]}


def _console() -> str:
    return runner.invoke(app, ["status"]).output


def test_a_proposed_record_and_an_accepted_one_do_not_read_the_same(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The defect #299 was filed over, as one assertion.

    Both branches below have every artifact written and identical step states.
    The only difference is one field in one file — the field a human sets by
    running `wfctl arch accept` — and before this feature it reached no view at
    all, because `design_block` counts a record whatever its status and nothing
    else in inference reads one.
    """
    storyctl_dir.stage_upstream_of("tasks")
    _record(storyctl_dir.repo_root, "a-decision", "proposed")
    proposed = _console()

    _record(storyctl_dir.repo_root, "a-decision", "accepted")
    accepted = _console()

    assert proposed != accepted
    assert "a-decision (proposed)" in proposed
    assert "a-decision (proposed)" not in accepted


def test_the_console_names_which_fact_is_missing_and_which_record_is_waiting(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Scope item 2: *which* one, not only that something is.

    A block saying "something is unresolved" would pass the payload requirement
    and leave the reader exactly where they started — running a second command to
    find out which of the questions it was.
    """
    storyctl_dir.stage_upstream_of("tasks")
    _record(storyctl_dir.repo_root, "a-decision", "proposed")

    out = _console()
    assert "architecture accepted" in out
    assert "a-decision (proposed)" in out


def test_a_branch_that_touched_no_record_is_not_reported_as_blocked(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-010. "No" would be the wrong answer, not a conservative one.

    A branch with no record has nothing for a human to accept, so unmet would
    send its reader to promote a decision that was never written. `n/a` is the
    third value's whole reason for existing.
    """
    storyctl_dir.stage_upstream_of("tasks")
    fact = _facts()["architecture accepted"]
    assert fact["value"] == "n/a"
    assert fact["detail"] == "no level-2 record on this branch"


def test_a_superseded_record_does_not_hold_the_branch_forever(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The bug in the first shape of this derivation, which asked for `accepted`.

    Superseding a record leaves it `superseded` — a status a person moved it to.
    Requiring `accepted` would mean a branch that retired a decision could never
    report that decision settled, and no command would ever change it.
    """
    storyctl_dir.stage_upstream_of("tasks")
    _record(storyctl_dir.repo_root, "a-decision", "superseded")
    assert _facts()["architecture accepted"]["value"] == "met"


def test_an_unreadable_record_says_so_rather_than_reading_as_proposed(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`parse_record` resolves an unrecognised status to "", and "" is not a word.

    Rendered as `(proposed)` a reader would go looking for the accept command;
    the file is the thing that needs fixing.
    """
    storyctl_dir.stage_upstream_of("tasks")
    path = _record(storyctl_dir.repo_root, "a-decision", "proposed")
    path.write_text("# no frontmatter at all\n")
    assert "a-decision (unreadable)" in _facts()["architecture accepted"]["detail"]


def test_a_level_three_record_does_not_answer_the_level_two_question(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-009. `design/` records are durable and never binding.

    They cannot be excluded by slug — `records_on_this_branch` returns a bare
    stem, so `design/299-x.md` and a top-level `299-x.md` look identical to it.
    What excludes them is `load_records` globbing one level, the same thing that
    already keeps them out of `wfctl arch context`.
    """
    storyctl_dir.stage_upstream_of("tasks")
    design = storyctl_dir.repo_root / "docs" / "architecture" / "design"
    design.mkdir(parents=True, exist_ok=True)
    (design / "299-a-shape.md").write_text(RECORD.format(status="proposed"))

    fact = _facts()["architecture accepted"]
    assert fact["value"] == "n/a"
    assert "299-a-shape" not in fact["detail"]


def test_a_repo_with_no_definition_of_done_is_not_reported_unverified(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-011, and the FR-002 degrade path seen from the fact side.

    `verification_block` returns None both for "passed" and for "there was
    nothing to run", which is correct for a gate and useless for a reader. The
    fact asks the config directly for exactly that distinction.
    """
    storyctl_dir.stage_upstream_of("tasks")
    fact = _facts()["definition of done"]
    assert fact["value"] == "n/a"
    assert fact["detail"] == "no definition of done declared"


def test_a_malformed_definition_of_done_is_unmet_and_not_absent(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The line between "no question" and "the answer is broken".

    Both leave the repo with no usable verdict. Only one of them is something the
    reader can fix, and reporting it `n/a` would hide the one that is.
    """
    storyctl_dir.stage_upstream_of("tasks")
    (storyctl_dir.repo_root / "wfctl.json").write_text('{"verify": "not a list"}\n')

    fact = _facts()["definition of done"]
    assert fact["value"] == "unmet"
    assert "malformed" in fact["detail"]


def test_every_branch_carries_all_three_facts_in_the_same_order(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-004 and FR-007, asserted on the input that has the least to say.

    Nothing staged: no artifacts, no record. A payload that filtered to
    what it could answer would be shortest here, and a consumer indexing the list
    would read one fact's value as another's.
    """
    payload = _payload()
    assert tuple(f["name"] for f in payload["facts"]) == FACT_NAMES
    assert all(f["detail"] for f in payload["facts"])


def test_a_feature_with_no_spec_dir_still_answers_the_other_two(
    tmp_path: Path,
) -> None:
    """The state today's payload cannot describe at all.

    A branch whose feature directory does not exist still has a definition of
    done and a record set. Only the first fact reads the spec dir, and the walk
    returns eight `pending` steps that say nothing about the other two.
    """
    report = build_report(None, tmp_path, tmp_path)
    facts = {f.name: f for f in report.facts}
    assert tuple(facts) == FACT_NAMES
    assert facts["artifacts written"].value == "unmet"
    assert facts["artifacts written"].detail == "no spec dir for this branch"


def test_the_artifacts_fact_names_which_files_are_missing(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """"Unmet" without the names is the collapse this feature undoes, one level down."""
    storyctl_dir.make_spec_artifact("brainstorm")
    fact = _facts()["artifacts written"]
    assert fact["value"] == "unmet"
    assert "spec.md" in fact["detail"] and "tasks.md" in fact["detail"]


def test_no_fact_is_derived_from_a_step(storyctl_dir: types.SimpleNamespace) -> None:
    """FR-003, structurally rather than by example.

    The rule is that a fact reads its own owner, and the way it would be broken
    is by someone reaching for the answer already computed two lines above. None
    of the derivations accepts a step, a state or a report — so the shortcut
    is not available to write, rather than merely discouraged.
    """
    import inspect

    for fn in (
        _evidence.fact_artifacts_written,
        _evidence.fact_definition_of_done,
        _evidence.fact_architecture_accepted,
    ):
        annotations = str(inspect.signature(fn))
        assert "Assessment" not in annotations
        assert "_PipelineStep" not in annotations
        assert "State" not in annotations


def test_the_pipeline_still_has_exactly_four_step_states(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-008. The prohibition that would be broken by making this feature easier.

    A fifth state meaning "some of the facts hold" is the collapse wearing a
    new spelling, and it is the shape a later reader will propose precisely
    because it is shorter.
    """
    assert set(_STATE_GLYPH) == {"done", "in_progress", "pending", "skipped"}
    assert set(_FACT_GLYPH) == {"met", "unmet", "n/a"}
    assert not set(_STATE_GLYPH) & set(_FACT_GLYPH)


def test_the_rule_for_unavailable_evidence_is_unchanged() -> None:
    """FR-014, pinned against every verdict/source pair the loops below build.

    Written without a count on purpose: #384 dropped the `human` source and the
    number in this line would have gone stale with nothing to catch it (#247 is
    that failure as its own issue).

    #299 answers *which question* the evidence was about; `blocks` answers what
    it means that the evidence was unavailable. They are one level apart and
    conflating them re-opens #287, so the second rule is pinned here by the
    change that had the most reason to reach for it.
    """
    promised = ("repo-declared", "accepted-record")
    for source in promised:
        assert _evidence.blocks("inconclusive", source) is True
    assert _evidence.blocks("inconclusive", "ambient") is False
    for source in (*promised, "ambient"):
        assert _evidence.blocks("satisfied", source) is False
        assert _evidence.blocks("unsatisfied", source) is True


def test_the_console_prints_the_payload_detail_and_composes_nothing(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-015. Two renderings of one inference, never two inferences.

    The design remedy was composed in the console until it was moved back into
    the payload, and this block's detail strings are the same invitation.
    What holds it is that every string a reader sees is also in `--json`.
    """
    storyctl_dir.stage_upstream_of("tasks")
    _record(storyctl_dir.repo_root, "a-decision", "proposed")

    out = _console()
    for fact in _payload()["facts"]:
        assert fact["detail"] in out


def test_the_block_prints_even_when_nothing_is_outstanding(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-006. Absence must not be the thing that carries the answer.

    A block that appeared only on trouble would leave "all met" and "this wfctl
    predates the question" as the same output.
    """
    storyctl_dir.stage_upstream_of("tasks")
    out = _console()
    for name in FACT_NAMES:
        assert name in out


def test_git_being_unable_to_answer_is_not_the_same_as_nothing_to_accept(
    storyctl_dir: types.SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-013, on the fact that read `[]` three ways and called all three `n/a`.

    `records_on_this_branch` returns an empty list for "nothing touched", for
    "git could not be asked", and for an arch root outside the tree. Reading the
    second as the first reports a branch with an un-ruled record as having
    nothing pending — the same collapse the feature exists to undo, one level
    down, and reachable in any repo whose trunk cannot be named.
    """
    storyctl_dir.stage_upstream_of("tasks")
    repo = storyctl_dir.repo_root
    _record(repo, "a-decision", "proposed")
    subprocess.run(["git", "-C", str(repo), "add", "docs"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "record"],
                   check=True, capture_output=True)
    # No `main`, `master`, `dev` or `origin/HEAD` left to find, which is what
    # `_trunk_branch` looks for and the only way it answers None.
    subprocess.run(["git", "-C", str(repo), "branch", "-M", "418-storyctl"],
                   check=True, capture_output=True)
    monkeypatch.setenv("WFCTL_BRANCH", "418-storyctl")

    fact = _facts()["architecture accepted"]
    assert fact["value"] == "unmet"
    assert "git cannot say" in fact["detail"]


def test_records_kept_outside_the_repo_are_not_reported_unmet_forever(
    storyctl_dir: types.SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The case that must not borrow the answer above, though git returns the same.

    `arch_root`'s own docstring says a repo may declare its records elsewhere.
    Nothing failed there — git is being asked about a path it does not track — and
    routing it to `unmet` would hold every branch in such a repo with no command
    that clears it.
    """
    storyctl_dir.stage_upstream_of("tasks")
    outside = tmp_path.parent / "records-elsewhere"
    outside.mkdir(exist_ok=True)
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(outside))

    fact = _facts()["architecture accepted"]
    assert fact["value"] == "n/a"
    assert "outside this repository" in fact["detail"]


def test_a_scan_file_is_not_a_record_even_when_it_shares_a_slug(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`scans/` is excluded by name, which `AGENTS.md` requires of every reader.

    The intersection with `load_records` looks like it covers this and does not:
    it matches bare stems, so a scan sharing a stem with a top-level record reads
    as that record being touched — blocking a branch on a decision it never made.
    """
    storyctl_dir.stage_upstream_of("tasks")
    arch = storyctl_dir.repo_root / "docs" / "architecture"
    (arch / "scans").mkdir(parents=True, exist_ok=True)
    (arch / "a-decision.md").write_text(RECORD.format(status="proposed"))
    subprocess.run(["git", "-C", str(storyctl_dir.repo_root), "add", "docs"],
                   check=True, capture_output=True)
    subprocess.run(["git", "-C", str(storyctl_dir.repo_root), "commit", "-m", "record"],
                   check=True, capture_output=True)
    # Only the scan is this branch's work. The record beside it is history.
    (arch / "scans" / "a-decision.md").write_text("# a scan, not a record\n")

    fact = _facts()["architecture accepted"]
    assert fact["value"] == "n/a"
    assert "a-decision" not in fact["detail"]


def test_a_rejected_record_does_not_render_as_an_accepted_one(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The met detail names every status, not only the ones that are waiting.

    Dropped, a `rejected` record printed the same line as an accepted one under a
    label reading "architecture accepted". Both are rulings, so neither holds the
    branch — and they are not the same thing to say about it.
    """
    storyctl_dir.stage_upstream_of("tasks")
    _record(storyctl_dir.repo_root, "a-decision", "rejected")
    fact = _facts()["architecture accepted"]
    assert fact["value"] == "met"
    assert "a-decision (rejected)" in fact["detail"]


def test_a_passing_definition_of_done_names_the_tree_it_passed_on(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The one branch of this fact that reads something the gate does not.

    `verification_block` returns None for a clean pass and says nothing about
    which commit it ran against, so the sha comes from the record itself — the
    diff's only index into another module's dict schema. Untested it rendered in
    real use and in no assertion, and a field rename would reach `wfctl status`
    as a `KeyError` over a green suite.
    """
    from wfctl import _verify

    storyctl_dir.stage_upstream_of("tasks")
    repo = storyctl_dir.repo_root
    (repo / "wfctl.json").write_text('{"verify": [["true"]]}\n')
    subprocess.run(["git", "-C", str(repo), "add", "wfctl.json"],
                   check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "declare a check"],
                   check=True, capture_output=True)
    assert _verify.perform(storyctl_dir.agent_dir, repo) == 0

    sha, _ = _verify.code_identity(repo)
    fact = _facts()["definition of done"]
    assert fact["value"] == "met"
    assert fact["detail"] == f"passed at {sha[:7]}"


def test_the_verification_answer_is_read_once_per_report(
    storyctl_dir: types.SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The seam `build_report`'s own comment says it exists to collapse.

    Adding the fact reintroduced the second call the seam had closed: the
    `implement` predicate and this fact both asked, so every report ran the git
    and record reads twice. Counted rather than measured — a timing assertion
    would be machine-dependent, and the count is the thing that regressed.
    """
    from wfctl import _evidence as pred

    calls = []
    real = pred.verification_block
    monkeypatch.setattr(
        pred, "verification_block", lambda root: (calls.append(root), real(root))[1]
    )
    storyctl_dir.stage_upstream_of("tasks")
    build_report(storyctl_dir.spec_dir, storyctl_dir.repo_root, storyctl_dir.agent_dir)
    assert len(calls) == 1


def test_no_fact_claims_authority_to_merge_or_to_act_outside_the_repo(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Two defects, one assertion.

    The first shape of the grant fact was called `integration authorized` and a
    granted branch reported it `met` — a claim of authority for an irreversible
    action no human gave. `may this branch be merged?` has no owner in wfctl and
    is meant not to.

    Its successor, `outward actions authorized`, went with the grant (#384):
    whether a command may run is the host's to answer, and a fact here would be
    a second answer wfctl cannot compute. Neither may come back under any
    spelling a consumer would key on.
    """
    storyctl_dir.stage_upstream_of("tasks")
    names = tuple(f["name"] for f in _payload()["facts"])
    assert not any(
        word in n for n in names for word in ("integration", "merge", "authorized")
    ), names
