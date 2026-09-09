"""What `specify` and `plan` prove, now that they read structure (#309).

Both steps carry `automatic` — `speckit-orchestrate` may pass them without
pausing — while their predicates proved only that a file held more than zero
bytes. A `spec.md` whose entire content was the character `x` read
`specify: done` in green, and that is not an adversarial case: a truncated
write, a failed generation and a bare `touch` all produce it.

The suite passed against that defect, so a green run was never the check. These
are the cases that fail if the fix does not work — the shapeless artifact
rejected, and the real corpus still accepted. A run that exercised only the
first has tested half of it, and the half that cannot make the pipeline
unpassable for genuine work.

`test_pipeline_state_names.py` owns the four state names; this file owns what
earns them for two of the eight steps.
"""
from __future__ import annotations

import os
import re
from collections.abc import Callable
from importlib.resources import files
from pathlib import Path

import pytest

from tests.conftest import PLAN_SECTIONS, SPEC_SECTIONS
from wfctl._pipeline import (
    _REQUIRED_PLAN_SECTIONS,
    _REQUIRED_SPEC_SECTIONS,
    _STEPS,
    _infer_steps,
)

_TEMPLATES = Path(str(files("wfctl"))) / "specify" / "templates"

# The durable spec root this repo records, holding every spec the pipeline has
# written. Not in the repository and absent in CI, which is why the corpus test
# skips rather than fails on it — see its own docstring.
_CORPUS = Path.home() / "Development" / "wfctl-specs"

FULL_SPEC = "# Spec\n\nBody.\n\n" + SPEC_SECTIONS
FULL_PLAN = "# Plan\n\nBody.\n\n" + PLAN_SECTIONS


def _step(spec_dir: Path, repo_root: Path, name: str):
    return next(s for s in _infer_steps(spec_dir, repo_root) if s.name == name)


# --------------------------------------------------------------------------
# US1 — specify
# --------------------------------------------------------------------------

def test_a_spec_of_one_character_leaves_specify_in_progress(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The case #300 constructed, and the reason this file exists.

    `in_progress` exactly, never merely "not done": `pending` also satisfies
    "not done", and the difference between the two is the whole of FR-003 — the
    artifact is there, so the writer is told to continue rather than to start
    over.
    """
    spec = spec_tree(content={"spec.md": "x"})
    assert _step(spec, tmp_path, "specify").state == "in_progress"


def test_a_held_specify_names_every_section_it_did_not_find(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The reader fixes the artifact without opening it.

    Chosen over a fixed "no sections yet" and over a `2/4` tally: neither says
    which heading to write.
    """
    step = _step(spec_tree(content={"spec.md": "x"}), tmp_path, "specify")
    assert step.annotation == (
        "missing: User Scenarios & Testing, Requirements, "
        "Success Criteria, Validation Strategy"
    )


def test_a_held_specify_names_only_the_sections_it_did_not_find(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """A partial spec is the common case, and the one a blanket message fails.

    Two of four present used to be indistinguishable from none of four, which is
    the state a reader is most likely to be in when they read the line.
    """
    partial = (
        "# Spec\n\n## User Scenarios & Testing _(mandatory)_\n\nx\n\n"
        "## Requirements _(mandatory)_\n\nx\n"
    )
    step = _step(spec_tree(content={"spec.md": partial}), tmp_path, "specify")
    assert step.annotation == "missing: Success Criteria, Validation Strategy"


def test_a_spec_carrying_every_section_still_reads_done(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The half a negative-only run does not cover, at unit scale."""
    assert _step(spec_tree(content={"spec.md": FULL_SPEC}), tmp_path, "specify").state == "done"


def test_the_template_suffix_satisfies_the_check(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """`## Requirements _(mandatory)_` is what a real spec carries.

    The suffix survives the template verbatim into 23 of the 25 specs on disk,
    so a whole-line match would have rejected the corpus it was measured
    against. This is why the constants are stems.
    """
    suffixed = "".join(f"## {n} _(mandatory)_\n\nx\n\n" for n in _REQUIRED_SPEC_SECTIONS)
    assert _step(spec_tree(content={"spec.md": suffixed}), tmp_path, "specify").state == "done"


def test_a_heading_that_merely_starts_with_the_name_does_not_satisfy_it(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """`## Functional Requirements` is not `## Requirements`.

    This is the strictness the required list was chosen for, and it is what
    holds three pre-pipeline spec directories outside the check. Without the
    `\\b` the first would pass and the check would be measuring nothing in
    particular.
    """
    drifted = FULL_SPEC.replace("## Requirements", "## Functional Requirements")
    step = _step(spec_tree(content={"spec.md": drifted}), tmp_path, "specify")
    assert step.state == "in_progress"
    assert step.annotation == "missing: Requirements"


def test_a_heading_with_a_suffix_run_onto_the_name_does_not_satisfy_it(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """`## RequirementsTODO` is a different heading, and `\\b` is what says so."""
    run_on = FULL_SPEC.replace("## Requirements _", "## RequirementsTODO _")
    assert _step(spec_tree(content={"spec.md": run_on}), tmp_path, "specify").state == "in_progress"


def test_a_section_only_illustrated_in_a_fenced_block_does_not_count(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """A spec that documents a heading has not thereby written one.

    The same blanking `specify`'s marker check and `clarify`'s scan already run
    against, applied to the third structural read so the three cannot disagree.
    """
    illustrated = "# Spec\n\n```\n" + SPEC_SECTIONS + "```\n"
    assert _step(
        spec_tree(content={"spec.md": illustrated}), tmp_path, "specify"
    ).state == "in_progress"


def test_a_marked_spec_reports_the_marker_and_not_the_sections(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """Marker handling keeps priority, and it is not an accident.

    A spec carrying both an open marker and missing sections routes to
    `/speckit.clarify`, not to `/speckit.specify`. Naming the sections beside a
    standing marker would send the reader to the command that rewrites the file
    from the template and destroys the clarification section.
    """
    step = _step(
        spec_tree(content={"spec.md": "# Spec\n\n[NEEDS CLARIFICATION: which?]\n"}),
        tmp_path,
        "specify",
    )
    assert step.state == "in_progress"
    assert step.annotation is None


# --------------------------------------------------------------------------
# US2 — plan
# --------------------------------------------------------------------------

def test_a_plan_of_one_character_leaves_plan_in_progress(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The other half of #309. `in_progress` exactly, for FR-003's reason."""
    spec = spec_tree(content={"spec.md": FULL_SPEC, "plan.md": "x"})
    assert _step(spec, tmp_path, "plan").state == "in_progress"


def test_a_held_plan_names_the_sections_it_did_not_find(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """No `_(mandatory)_` suffix on this side: the plan template marks none."""
    spec = spec_tree(content={"spec.md": FULL_SPEC, "plan.md": "x"})
    assert _step(spec, tmp_path, "plan").annotation == (
        "missing: Summary, Technical Context, Constitution Check, "
        "Project Structure, Complexity Tracking"
    )


def test_a_plan_carrying_every_section_still_reads_done(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    spec = spec_tree(content={"spec.md": FULL_SPEC, "plan.md": FULL_PLAN})
    assert _step(spec, tmp_path, "plan").state == "done"


def test_a_thin_plan_still_skips_clarify(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The regression tightening `plan` was most likely to cause.

    `clarify`'s `skipped` branch reads `plan.md` by existence and deliberately
    still does. It asks whether planning already passed through where clarify
    now sits — which a thin plan answers yes — and tightening it would send an
    in-flight spec back to re-clarify a document its plan is already built on.
    Different question from #309's, so it keeps the weaker test.
    """
    spec = spec_tree(content={"spec.md": FULL_SPEC, "plan.md": "x"})
    assert _step(spec, tmp_path, "clarify").state == "skipped"


# --------------------------------------------------------------------------
# US3 — clarify says why it passed
# --------------------------------------------------------------------------

def test_a_skipped_clarify_says_the_scan_never_ran(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """`skipped` advances the pipeline exactly as `done` does, and said nothing.

    `/speckit.clarify` writes its section on every run including a clean scan,
    so a missing heading is unambiguous evidence the scan never happened. The
    verdict is a deliberate policy and is not relitigated here — it only stops
    being silent.
    """
    spec = spec_tree(content={"spec.md": FULL_SPEC, "plan.md": FULL_PLAN})
    step = _step(spec, tmp_path, "clarify")
    assert step.state == "skipped"
    assert step.annotation == "scan never ran"


def test_a_skipped_clarify_carries_no_reason(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """Annotation only — the field's contract is arms setting `in_progress`.

    A `skipped` step is never `_current_step_name`, so a reason set here would
    reach no consumer: `next-step.md`'s `why:` and the report both read the
    *current* step's reason. Putting it there would widen what `reason` means in
    exchange for nothing observable.
    """
    spec = spec_tree(content={"spec.md": FULL_SPEC, "plan.md": FULL_PLAN})
    assert _step(spec, tmp_path, "clarify").reason is None


def test_a_scanned_clarify_carries_no_annotation(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The annotation marks the pass that had no scan, not every pass."""
    scanned = FULL_SPEC + "\n## Clarifications\n\n- none\n"
    spec = spec_tree(content={"spec.md": scanned, "plan.md": FULL_PLAN})
    step = _step(spec, tmp_path, "clarify")
    assert step.state == "done"
    assert step.annotation is None


# --------------------------------------------------------------------------
# The pin against upstream, and the two properties nothing else observes
# --------------------------------------------------------------------------

def _mandatory_headings(template: Path) -> tuple[str, ...]:
    return tuple(
        m.group(1).strip()
        for m in re.finditer(r"^##[ \t]+(.+?)\s+_\(mandatory\)_\s*$", template.read_text(), re.M)
    )


def _all_headings(template: Path) -> tuple[str, ...]:
    return tuple(
        m.group(1).strip()
        for m in re.finditer(r"^##[ \t]+(.+)$", template.read_text(), re.M)
    )


def test_the_required_spec_sections_are_the_templates_mandatory_ones() -> None:
    """The condition `required-sections-are-wfctls` accepted the coupling under.

    The names belong to `github/spec-kit`; the requirement that a spec carry
    them is wfctl's. Inference never opens a template — it reads a spec
    directory and nothing else — so this is where the two are held together, and
    a rename upstream fails the build here rather than changing a verdict
    silently in a consuming repository.

    Equality in both directions, deliberately. A rename is the dangerous half; an
    addition costs only a build failure that forces someone to decide whether
    wfctl requires the new section too, which is the decision this test exists to
    surface rather than to skip.
    """
    assert _REQUIRED_SPEC_SECTIONS == _mandatory_headings(_TEMPLATES / "spec-template.md")


def test_the_required_plan_sections_are_headings_the_plan_template_carries() -> None:
    """The plan half asserts differently, because the templates differ.

    `plan-template.md` marks nothing `_(mandatory)_`, so there is no declaration
    to compare against and the list is wfctl's own choice from the headings the
    template does carry. Containment rather than equality: the template holds
    `Project Structure`'s subheadings and others wfctl does not require, and
    requiring every heading it carries would make the plan step unpassable.

    The asymmetry is the finding. It is asserted rather than hidden behind a
    helper that treats the two templates alike.
    """
    carried = _all_headings(_TEMPLATES / "plan-template.md")
    missing = [name for name in _REQUIRED_PLAN_SECTIONS if name not in carried]
    assert not missing, f"required of a plan but absent from the template: {missing}"


def test_inference_reads_the_spec_directory_and_nothing_else(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """FR-006 and SC-005, and the level-2 record's load-bearing claim.

    A repository that has never run `install-skills` has no `.specify/`, and a
    predicate that consulted the template would have to decide what its absence
    means — passing restores the defect, failing blocks a repo whose only fault
    is not having installed. The record's answer is that the question never
    arises. If this fails, the record is wrong, not the test.

    `tmp_path` is a bare directory with no `.specify/` anywhere beneath it, so
    the assertion is that the verdicts are the ones the templates would have
    produced, reached without them.
    """
    spec = spec_tree(content={"spec.md": FULL_SPEC, "plan.md": FULL_PLAN})
    assert not list(tmp_path.rglob(".specify")), "fixture must not carry a template tree"
    states = {s.name: s.state for s in _infer_steps(spec, tmp_path)}
    assert states["specify"] == "done"
    assert states["plan"] == "done"


def test_no_step_changed_the_flag_that_says_it_may_run_unattended() -> None:
    """FR-009, and the one property no run can observe.

    #309's out-of-scope section rules out flipping `specify` or `plan` to
    `review_required`: that trades an unchecked pass for a human pause on every
    run, and #100's direction is to strengthen evidence rather than add gates.
    The flags live in a table, not in a code path, so nothing else in this file
    could notice one had moved.
    """
    assert {name: flag for name, (_cmd, flag) in _STEPS.items()} == {
        "brainstorm": "automatic",
        "specify": "automatic",
        "clarify": "review_required",
        "plan": "automatic",
        "tasks": "automatic",
        "analyze": "review_required",
        "decompose": "review_required",
        "implement": "automatic",
    }


@pytest.mark.skipif(not _CORPUS.is_dir(), reason="the durable spec root is not on this machine")
def test_every_spec_this_pipeline_wrote_still_reads_done(tmp_path: Path) -> None:
    """The exercise a negative-only run does not cover, against the real corpus.

    A check that rejects `x` and also rejects real work has not fixed anything.
    So this runs inference over every spec directory on disk and asserts the
    ones the pipeline itself wrote are unaffected.

    Three directories are excluded by name and not by a rule. They are the
    oldest on disk, ported in by "specs: port the last in-repo spec dirs before
    declaring a spec root" from before this pipeline existed, and they use a
    different heading vocabulary — `## Functional Requirements`, `## Testing`.
    Excluding them by name is the honest form: a rule that happened to skip them
    would also silently skip a real regression that resembled them.

    Skipped rather than failed where the root is absent: `specs/` is gitignored
    and this repo records a root outside the working tree, so CI has no copy.
    A skip here is the corpus being unavailable, never the check passing.
    """
    legacy = {
        "24-read-artifacts-from-specs",
        "configurable-issue-key",
        "install-config-workmux",
    }
    checked = 0
    for spec_dir in sorted(p for p in _CORPUS.iterdir() if p.is_dir()):
        if spec_dir.name in legacy or not (spec_dir / "spec.md").is_file():
            continue
        states = {s.name: s.state for s in _infer_steps(spec_dir, tmp_path)}
        assert states["specify"] == "done", f"{spec_dir.name}: specify {states['specify']}"
        if (spec_dir / "plan.md").is_file():
            assert states["plan"] == "done", f"{spec_dir.name}: plan {states['plan']}"
        checked += 1
    assert checked >= 20, f"only {checked} spec dirs checked — the corpus looks truncated"


def test_the_corpus_test_is_not_silently_skipping(tmp_path: Path) -> None:
    """A skip is invisible in a `-q` run, and this one guards the positive half.

    So say out loud, once, whether the corpus was reachable. `WFCTL_REQUIRE_CORPUS`
    turns the skip into a failure for a run that means to depend on it — CI does
    not set it, and a maintainer checking the claim by hand can.
    """
    if os.environ.get("WFCTL_REQUIRE_CORPUS"):
        assert _CORPUS.is_dir(), f"WFCTL_REQUIRE_CORPUS is set and {_CORPUS} is absent"
