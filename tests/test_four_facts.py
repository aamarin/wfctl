"""The four readiness facts, and the two situations they exist to tell apart (#299).

A step state answered four questions with four owners, and the payload carried
one value for all of them. The test that matters here is the first pair below:
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

from wfctl import _predicates
from wfctl._pipeline import build_report
from wfctl._session import NotifyGrant, record_notify_resolved
from wfctl.cli import _FACT_GLYPH, _STATE_GLYPH, app

runner = CliRunner()

FACT_NAMES = (
    "artifacts written",
    "definition of done",
    "architecture accepted",
    "outward actions authorized",
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
    find out which of four questions it was.
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


def test_nobody_granting_authority_reads_differently_from_a_failed_read(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-013. Five of the grant's seven answers mean refused and are not one event.

    A consumer seeing only `unmet` cannot tell a person's decision from a tracker
    that could not be reached, which is the distinction #280 spent a whole field
    on. The detail is where it survives into this block.
    """
    storyctl_dir.stage_upstream_of("tasks")
    assert _facts()["outward actions authorized"]["detail"] == (
        "nobody has allowed it for this work"
    )

    record_notify_resolved(
        storyctl_dir.agent_dir, NotifyGrant(False, "unreadable"), "418-storyctl"
    )
    fact = _facts()["outward actions authorized"]
    assert fact["value"] == "unmet"
    assert "tracker" in fact["detail"]


def test_a_granted_branch_reports_integration_authorized_met(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The other half of the pair above, which a refusal-only test cannot show.

    Without it the fact could be hardwired to `unmet` and every assertion here
    would still pass.
    """
    storyctl_dir.stage_upstream_of("tasks")
    record_notify_resolved(
        storyctl_dir.agent_dir, NotifyGrant(True, "local"), "418-storyctl"
    )
    fact = _facts()["outward actions authorized"]
    assert fact["value"] == "met"
    assert fact["detail"] == "you allowed it in this worktree"


def test_the_trunk_has_no_integration_question_to_answer(
    storyctl_dir: types.SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-012. There is no branch to integrate, so nothing was ever asked.

    Reported unmet, the trunk would send its reader looking for the flag that
    grants it — and the trunk refuses that flag by design, so the search ends
    nowhere.
    """
    storyctl_dir.stage_upstream_of("tasks")
    repo = storyctl_dir.repo_root
    subprocess.run(["git", "-C", str(repo), "branch", "-M", "main"],
                   check=True, capture_output=True)
    monkeypatch.setenv("WFCTL_BRANCH", "main")

    fact = _facts()["outward actions authorized"]
    assert fact["value"] == "n/a"
    assert fact["detail"] == "this is the trunk"


def test_every_branch_carries_all_four_facts_in_the_same_order(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-004 and FR-007, asserted on the input that has the least to say.

    Nothing staged: no artifacts, no record, no grant. A payload that filtered to
    what it could answer would be shortest here, and a consumer indexing the list
    would read one fact's value as another's.
    """
    payload = _payload()
    assert tuple(f["name"] for f in payload["facts"]) == FACT_NAMES
    assert all(f["detail"] for f in payload["facts"])


def test_a_feature_with_no_spec_dir_still_answers_three_of_the_four(
    tmp_path: Path,
) -> None:
    """The state today's payload cannot describe at all.

    A branch whose feature directory does not exist still has a definition of
    done, a record set and a grant. Only the first fact reads the spec dir, and
    the walk returns eight `pending` steps that say nothing about the other
    three.
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
    of the four derivations accepts a step, a state or a report — so the shortcut
    is not available to write, rather than merely discouraged.
    """
    import inspect

    for fn in (
        _predicates.fact_artifacts_written,
        _predicates.fact_definition_of_done,
        _predicates.fact_architecture_accepted,
        _predicates.fact_outward_actions_authorized,
    ):
        annotations = str(inspect.signature(fn))
        assert "Reading" not in annotations
        assert "_PipelineStep" not in annotations
        assert "State" not in annotations


def test_the_pipeline_still_has_exactly_four_step_states(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-008. The prohibition that would be broken by making this feature easier.

    A fifth state meaning "some of the four facts hold" is the collapse wearing a
    new spelling, and it is the shape a later reader will propose precisely
    because it is shorter.
    """
    assert set(_STATE_GLYPH) == {"done", "in_progress", "pending", "skipped"}
    assert set(_FACT_GLYPH) == {"met", "unmet", "n/a"}
    assert not set(_STATE_GLYPH) & set(_FACT_GLYPH)


def test_the_rule_for_unavailable_evidence_is_unchanged() -> None:
    """FR-014, pinned against all eight verdict/source pairs.

    #299 answers *which question* the evidence was about; `blocks` answers what
    it means that the evidence was unavailable. They are one level apart and
    conflating them re-opens #287, so the second rule is pinned here by the
    change that had the most reason to reach for it.
    """
    promised = ("repo-declared", "accepted-record", "human")
    for source in promised:
        assert _predicates.blocks("inconclusive", source) is True
    assert _predicates.blocks("inconclusive", "ambient") is False
    for source in (*promised, "ambient"):
        assert _predicates.blocks("satisfied", source) is False
        assert _predicates.blocks("unsatisfied", source) is True


def test_the_console_prints_the_payload_detail_and_composes_nothing(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-015. Two renderings of one inference, never two inferences.

    The design remedy was composed in the console until it was moved back into
    the payload, and this block's four detail strings are the same invitation.
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

    A block that appeared only on trouble would leave "all four met" and "this
    wfctl predates the question" as the same output — which is the confusion
    `notify` is present-and-false to avoid, met on the console side.
    """
    storyctl_dir.stage_upstream_of("tasks")
    record_notify_resolved(
        storyctl_dir.agent_dir, NotifyGrant(True, "local"), "418-storyctl"
    )
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


def test_an_unrecognised_grant_source_never_claims_someone_allowed_it(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`NotifyGrant.source` is read off `events.jsonl` without validation.

    Answered with the `unset` wording, a source this wfctl has never heard of
    produced `met` beside "nobody has allowed it for this work" — a value and a
    detail contradicting each other, about a human.
    """
    storyctl_dir.stage_upstream_of("tasks")
    record_notify_resolved(
        storyctl_dir.agent_dir, NotifyGrant(True, "from-the-future"), "418-storyctl"
    )
    fact = _facts()["outward actions authorized"]
    assert fact["value"] == "unmet"
    assert "from-the-future" in fact["detail"]


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
    from wfctl import _predicates as pred

    calls = []
    real = pred.verification_block
    monkeypatch.setattr(
        pred, "verification_block", lambda root: (calls.append(root), real(root))[1]
    )
    storyctl_dir.stage_upstream_of("tasks")
    build_report(storyctl_dir.spec_dir, storyctl_dir.repo_root, storyctl_dir.agent_dir)
    assert len(calls) == 1


def test_the_grant_fact_never_claims_authority_to_merge(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The defect a reviewer caught after this PR was opened.

    The first shape called this fact `integration authorized` and read it off the
    notify grant, which `AGENTS.md` § Safety says covers pushing, commenting and
    labelling and never merging, closing or deleting. A granted branch therefore
    reported `integration authorized: met` — a claim of authority for an
    irreversible action no human gave, which is worse than the silence the
    feature replaces, because a consumer keys on the name.

    `may this branch be merged?` has no owner in wfctl and is meant not to: the
    payload must not answer it under any spelling.
    """
    storyctl_dir.stage_upstream_of("tasks")
    record_notify_resolved(
        storyctl_dir.agent_dir, NotifyGrant(True, "local"), "418-storyctl"
    )
    names = tuple(f["name"] for f in _payload()["facts"])
    assert not any("integration" in n or "merge" in n for n in names), names
    assert "outward actions authorized" in names
