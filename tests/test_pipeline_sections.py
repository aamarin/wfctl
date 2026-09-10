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
from wfctl._paths import spec_root
from wfctl._pipeline import (
    _STEPS,
    _current_step_name,
    _infer_steps,
    next_step_content,
    next_step_file,
)
from wfctl._predicates import (
    CLARIFY_UNSCANNED,
    TEMPLATE_PLACEHOLDER,
    _REQUIRED_PLAN_SECTIONS,
    _REQUIRED_SPEC_SECTIONS,
    _missing_sections,
    _quoted_out,
)

_TEMPLATES = Path(str(files("wfctl"))) / "specify" / "templates"

def _corpus() -> Path | None:
    """The durable spec root this repo records, or None if there is not one.

    Resolved rather than written down: `WFCTL_SPEC_DIR`, then this repo's
    manifest, then the main checkout's, then `<repo>/specs` (AGENTS.md, "ask
    `wfctl feature-paths` rather than assuming a path"). The literal
    `~/Development/wfctl-specs` this replaced was true on one machine, and the
    positive half of this file's own argument — that a check rejecting `x` and
    also rejecting real work has fixed nothing — was bound to it.
    """
    root = spec_root(Path(__file__).resolve().parent.parent)
    return root if root.is_dir() else None

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
        "missing: Summary, Technical Context, Constitution Check, Project Structure"
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

def test_the_skipped_clarify_annotation_is_the_constant_the_module_exports() -> None:
    """The literal, tied to the name, so a rename cannot leave a test agreeing.

    Every other assertion here re-types `scan never ran`. Renaming the constant
    and every rendering of it would leave those green while `CLARIFY_UNSCANNED`
    named something nothing checks — the string is the interface a reader sees.
    """
    assert CLARIFY_UNSCANNED == "scan never ran"


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


def test_the_matcher_finds_every_required_section_in_the_templates_themselves() -> None:
    """The strings agreeing is not the same as the matcher finding them.

    The list check above compares two sets of names, and a name can match itself
    while matching nothing in a document — that is exactly how `\b` failed for a
    name ending in `)`. So run the real matcher over the real templates: if a
    required section cannot be found in the file that declares it, the field is
    about to become unpassable and the string comparison would still be green.

    The gap this closes is narrow and silent, which is the pair that gets shipped.
    """
    for template, required in (
        ("spec-template.md", _REQUIRED_SPEC_SECTIONS),
        ("plan-template.md", _REQUIRED_PLAN_SECTIONS),
    ):
        missing = _missing_sections(_quoted_out((_TEMPLATES / template).read_text()), required)
        assert missing == (), f"{template}: the matcher cannot find {list(missing)}"


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
    assert {name: step.continuation for name, step in _STEPS.items()} == {
        "brainstorm": "automatic",
        "specify": "automatic",
        "clarify": "review_required",
        "plan": "automatic",
        "tasks": "automatic",
        "analyze": "review_required",
        "decompose": "automatic",
        "implement": "automatic",
    }


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
    corpus = _corpus()
    if corpus is None:
        pytest.skip("no durable spec root resolves from here")
    legacy = {
        "24-read-artifacts-from-specs",
        "configurable-issue-key",
        "install-config-workmux",
    }
    checked = 0
    for spec_dir in sorted(p for p in corpus.iterdir() if p.is_dir()):
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
        corpus = _corpus()
        assert corpus is not None and corpus.is_dir(), (
            "WFCTL_REQUIRE_CORPUS is set and no durable spec root resolves from here"
        )


# --------------------------------------------------------------------------
# Routing. The hole the panel's only blocker lived in.
# --------------------------------------------------------------------------

def test_a_shapeless_spec_routes_to_specify_and_not_to_clarify(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The flagship case, all the way to the file an agent acts on.

    `_current_step_name` skips `specify` when `clarify` is also `in_progress`,
    which was written when markers were specify's only cause. Missing sections
    are a second cause and clarify cannot clear it, so the thin spec routed to
    `/speckit.clarify` — the one command that cannot fix it, and one that would
    write its `## Clarifications` into a one-character file. `status` was right
    the whole time; only routing was wrong, and routing is what an unattended
    run acts on.

    Three reviewers found this independently and no test in the change caught
    it, because nothing in it called `_current_step_name`. That is what this
    section is for.
    """
    steps = _infer_steps(spec_tree(content={"spec.md": "x"}), tmp_path)
    assert _current_step_name(steps) == "specify"


def test_a_shapeless_spec_carries_its_reason_into_the_agents_file(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """`next-step.md` is where the annotation has to arrive, not just `status`.

    `cli` reads `blocked` off the *current* step, so routing to the wrong step
    dropped the `missing: …` line entirely — computed, stored, and delivered
    nowhere. SC-003 is about the reader of this file as much as the table.
    """
    steps = _infer_steps(spec_tree(content={"spec.md": "x"}), tmp_path)
    current = _current_step_name(steps)
    reason = next(s.reason for s in steps if s.name == current)
    command, _auto = next_step_content(current, reason)
    body = next_step_file(command, False, reason, None)
    assert "/speckit.specify" in body
    assert "why: missing: User Scenarios & Testing" in body


def test_a_marked_spec_still_routes_to_clarify(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The skip the fix had to preserve, not merely narrow.

    A spec with markers standing still belongs to clarify. Sending it back to
    `/speckit.specify` regenerates the file from the template and destroys the
    Clarifications section — the sequence this file names twice. The condition
    keys on `reason` because the marker branch sets none and the section branch
    sets the rendered string, so the skip asks whether specify is held for
    something clarify can clear rather than whether it is held at all.
    """
    marked = "# Spec\n\n[NEEDS CLARIFICATION: which?]\n"
    steps = _infer_steps(spec_tree(content={"spec.md": marked}), tmp_path)
    assert _current_step_name(steps) == "clarify"


def test_a_held_step_is_never_handed_out_as_automatic(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The change's other effect on orchestration, pinned rather than assumed.

    `specify` is `automatic` in the table, and a held step is never automatic
    whatever the table says (`next_step_content`). So tightening the predicate
    also stops an unattended run where it previously proceeded — which is the
    point, and was unobserved by any test until this one.
    """
    steps = _infer_steps(spec_tree(content={"spec.md": "x"}), tmp_path)
    current = _current_step_name(steps)
    reason = next(s.reason for s in steps if s.name == current)
    _command, auto = next_step_content(current, reason)
    assert auto is False


def test_a_spec_that_is_only_a_fenced_block_is_not_pending(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """Presence is a fact about the file, not about what survives blanking.

    A `spec.md` holding one fenced block blanks to whitespace. Testing presence
    on the blanked text read that as `pending`, cascading the whole pipeline and
    contradicting `brainstorm`, which calls the same directory `skipped` from
    `_file_exists` two arms up. Narrow input, and the two arms disagreeing about
    one directory is the part that would have been hard to diagnose.
    """
    only_a_fence = "```\n## Requirements\n```\n"
    states = {s.name: s.state for s in _infer_steps(
        spec_tree(content={"spec.md": only_a_fence}), tmp_path)}
    assert states["specify"] == "in_progress"
    assert states["brainstorm"] == "skipped"


def test_a_heading_only_illustrated_survives_every_fence_shape(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """Three fence shapes a private regex got wrong, now the shared walker's job.

    `~~~`, a ```-block nested inside a ````-fence, and an unclosed fence each let
    an *illustrated* heading read as a written one — the defect class this step
    exists to reject, arriving through the checker itself. `_md.walk` is the
    package's one fence walker and exists because three modules carrying their
    own answered differently; `_prose` had quietly become a fourth.
    """
    shapes = {
        "tilde": "~~~\n" + SPEC_SECTIONS + "~~~\n",
        "nested": "````\n```\n" + SPEC_SECTIONS + "```\n````\n",
        "unclosed": "```\n" + SPEC_SECTIONS,
    }
    for label, text in shapes.items():
        step = _step(spec_tree(content={"spec.md": text}), tmp_path, "specify")
        assert step.state == "in_progress", f"{label}: illustrated heading counted as written"


def test_the_required_plan_sections_do_not_contradict_the_template() -> None:
    """A required list may out-strict its template; it may not contradict it.

    `plan-template.md` says of `Complexity Tracking`: "Fill ONLY if Constitution
    Check has violations that must be justified". 23 of the 24 plans on disk
    carry it anyway, which is why requiring it would have passed the corpus — and
    it would still have left an author who followed the template's own
    instruction unable ever to clear the step.
    """
    template = (_TEMPLATES / "plan-template.md").read_text()
    for name in _REQUIRED_PLAN_SECTIONS:
        section = template.split(f"## {name}", 1)
        assert len(section) == 2, f"{name} is required of a plan and absent from the template"
        assert "Fill ONLY if" not in section[1].split("\n##", 1)[0], (
            f"{name} is required, but the template tells the author to delete it"
        )


# --------------------------------------------------------------------------
# The document that is still its own template
# --------------------------------------------------------------------------

def test_a_verbatim_plan_template_does_not_read_done(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The case structure alone cannot reject, on the path the tool always takes.

    `setup-plan.sh` runs `cp plan-template.md plan.md`, so the first act of
    `/speckit.plan` creates a file carrying every required heading and no
    content. A section check has nothing to say about it. Before this, the rung
    `plan` claimed was the one rung it did not reach in the one case that always
    happens.

    `spec.md` never had this hole — its template ships `[NEEDS CLARIFICATION`
    markers — which is why it went unnoticed on the side that did.
    """
    verbatim = (_TEMPLATES / "plan-template.md").read_text()
    spec = spec_tree(content={"spec.md": FULL_SPEC, "plan.md": verbatim})
    step = _step(spec, tmp_path, "plan")
    assert step.state == "in_progress"
    assert step.annotation == "still the template"


def test_a_verbatim_spec_template_routes_to_specify_not_clarify(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The routing blocker, one door along, and why the check runs before markers.

    The spec template carries its own markers, so an untouched copy was
    `in_progress` before this too — but as a *marked* spec, which routes to
    `/speckit.clarify`. Clarify cannot write a spec nobody has written. Reading
    the document as unwritten sends it to the command that can.
    """
    verbatim = (_TEMPLATES / "spec-template.md").read_text()
    steps = _infer_steps(spec_tree(content={"spec.md": verbatim}), tmp_path)
    assert _current_step_name(steps) == "specify"
    assert next(s.annotation for s in steps if s.name == "specify") == "still the template"


def test_a_written_spec_with_an_open_marker_still_belongs_to_clarify(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The ordering above narrows the marker branch; it must not swallow it.

    A spec someone has written carries no `ACTION REQUIRED` — the template tells
    the author to delete it — so a real open marker reaches the marker branch and
    routes to clarify exactly as before.
    """
    written = FULL_SPEC + "\n[NEEDS CLARIFICATION: which one?]\n"
    steps = _infer_steps(spec_tree(content={"spec.md": written}), tmp_path)
    assert _current_step_name(steps) == "clarify"


def test_no_artifact_the_pipeline_wrote_carries_the_placeholder() -> None:
    """The pair a placeholder marker needs: in both templates, in no real document.

    `NEEDS CLARIFICATION` would have been the symmetric choice and is not usable
    on the plan side — three plans on disk discuss markers in prose, so it
    rejects real work. This string appears in neither corpus and in both
    templates, which is what makes it evidence rather than a guess.
    """
    for template in ("spec-template.md", "plan-template.md"):
        assert TEMPLATE_PLACEHOLDER in (_TEMPLATES / template).read_text(), (
            f"{template} no longer carries the placeholder the check keys on"
        )
    corpus = _corpus()
    if corpus is None:
        pytest.skip("no durable spec root resolves from here")
    for artifact in sorted(corpus.glob("*/spec.md")) + sorted(corpus.glob("*/plan.md")):
        assert TEMPLATE_PLACEHOLDER not in artifact.read_text(), (
            f"{artifact.parent.name}/{artifact.name} carries the placeholder and would be held"
        )
