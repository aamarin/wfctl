"""Four pipeline steps read the level-3 design records their feature lists.

`/speckit.brainstorm` writes the records and `idea-refine` lists their paths in
`design.md`, and until #326 the chain stopped there: `speckit-plan` loads
`FEATURE_SPEC` and the constitution, `speckit-tasks` loads `plan.md`,
`speckit-implement` loads `tasks.md`, and `speckit-analyze` ran six detection
passes over those three artifacts. Seven records sat in `docs/architecture/design/`
and no step in the pipeline read any of them.

The instruction that closes it is prose under `wfctl/agents/commands/`, which is
the one thing the suite cannot otherwise see — `install-skills` copies it, no test
reads it, and a wrapper that lost a rule would ship green. So every assertion here
is about the shipped bundle rather than about `wfctl/`, which this feature does
not touch at all.

`wfctl/agents/commands/` and not the four `speckit-*` skills, deliberately: those
are `github/spec-kit`-derived, and `vendor-upstream-skills` prefers a layer to an
edit because an in-place change is reverted by the next upstream pull with no
conflict to notice. `test_no_speckit_skill_carries_the_instruction` is what keeps
that true after someone finds the wrapper indirection annoying.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import pytest

# Resolved through `files("wfctl")` for `test_skill_cross_references`' reason:
# conftest's autouse `bundle` fixture repoints `_bundle.BUNDLE_ROOT` at a fake
# tree, and reading the real shipped one is this file's whole purpose.
_AGENTS = Path(str(files("wfctl"))) / "agents"

# The four steps that consume records. `analyze` also carries pass G, which the
# other three do not, so it appears in both this tuple and its own tests.
_CONSUMERS = ("plan", "tasks", "implement", "analyze")

_SECTION = "## Read this feature's design records"


def _wrapper(step: str) -> str:
    return (_AGENTS / "commands" / f"speckit.{step}.md").read_text()


def _record_section(step: str) -> str:
    """The record-reading section, isolated from the rest of the wrapper.

    Isolated rather than searched whole, so an assertion cannot pass on a string
    that happens to appear somewhere else in a file that is mostly prose about
    other things.
    """
    body = _wrapper(step).split(_SECTION)[1]
    # `analyze` carries pass G and the scan-file instruction after this section;
    # the other three end the file with it.
    return body.split("\n## ")[0]


# --- the shared instruction, in all four -------------------------------------


@pytest.mark.parametrize("step", _CONSUMERS)
def test_every_consumer_reads_the_record_list_from_design_md(step: str) -> None:
    """Each of the four asks the feature's own document, not the filesystem.

    This is the whole feature in one assertion, and the ordering matters: a
    wrapper that names `design.md` but resolves it as `specs/<branch>/` finds
    nothing in this repository, which records a spec root outside the working
    tree.
    """
    section = _record_section(step)

    assert "wfctl feature-paths" in section
    assert "design.md" in section
    assert "## Software design decisions" in section


@pytest.mark.parametrize("step", _CONSUMERS)
def test_every_consumer_states_the_bullet_only_parse_rule(step: str) -> None:
    """The rule with the most consequence and the smallest surface.

    `## Software design decisions` legitimately carries prose as well as entries:
    `/speckit.brainstorm` requires a level answered with no record to say so in one
    line rather than delete the heading. That prose may name a *level-2* record —
    this feature's own `design.md` does. A wrapper that says "the paths listed in
    the section" without saying "list items only" is read as *every path*, and a
    level-2 record then loads as level-3, binding nothing while looking like it
    does.

    Caught by `/speckit.clarify` on this feature rather than by a run: the defect
    was in the artifact the pipeline was about to consume.
    """
    section = _record_section(step)

    assert "list item" in section
    assert "Prose in that section names no records." in section


@pytest.mark.parametrize("step", _CONSUMERS)
def test_every_consumer_refuses_the_issue_prefixed_glob(step: str) -> None:
    """The mechanism this feature shipped with first, and it was silently wrong.

    A worktree is named for the issue that existed when it was created; a record
    is numbered for the issue being implemented, not its epic; and a child issue
    is filed *during* the brainstorm pass, after the worktree exists. On any
    branch cut from an epic those three compose into a glob that loads another
    feature's record and misses this one, with no error either way — observed on
    `121-level3-downstream`, where `design/121-*.md` matched #122's record.

    Stated as a refusal in each wrapper because the glob is the obvious
    implementation, and an instruction that only says what to do leaves the
    obvious wrong thing available.
    """
    section = _record_section(step)

    assert "Do not glob" in section
    assert "design-md-indexes-the-records" in section


@pytest.mark.parametrize("step", _CONSUMERS)
def test_every_consumer_names_all_three_record_states(step: str) -> None:
    """A run that found nothing and a run that never looked must not read alike.

    #307's argument one directory over. `none` says a design pass ran and recorded
    no structural decision, which is a legitimate answer — the record threshold
    exists so that not every choice earns a file. `unknown` says no design pass
    ran. A wrapper that describes only the populated case leaves both empty states
    to the model's judgement, and they collapse into one.
    """
    section = _record_section(step)

    assert "listed in design.md" in section
    assert "none — design.md records no level-3 decision" in section
    assert "unknown — no design.md at" in section


@pytest.mark.parametrize("step", _CONSUMERS)
def test_every_consumer_reports_a_listed_path_it_could_not_read(step: str) -> None:
    """A record that moved is a broken reference, not an absence.

    Silently skipping it produces the `N listed` line with fewer than N paths
    under it, which reads as a miscount rather than as a missing file — so the one
    state that needs a reader's attention is the one that looks like a bug in the
    step.
    """
    section = _record_section(step)

    assert "listed, not found" in section


@pytest.mark.parametrize("step", _CONSUMERS)
def test_every_consumer_says_why_the_rule_is_in_the_wrapper(step: str) -> None:
    """The reason has to travel with the rule, or the rule gets moved.

    Someone reading four near-identical sections will reasonably want them in the
    skill they all point at. The answer is that the skill is upstream-derived and
    the edit would be reverted by the next pull with no conflict to notice — which
    is invisible from the wrapper unless the wrapper says it.
    """
    section = _record_section(step)

    assert "vendor-upstream-skills" in section
    assert "reverted by the next upstream pull" in section


@pytest.mark.parametrize("step", _CONSUMERS)
def test_every_consumer_may_run_feature_paths(step: str) -> None:
    """An instruction to run a command the frontmatter does not allow is inert.

    The wrapper would ship, the test above would pass, and the step would be
    unable to resolve `FEATURE_DIR` at runtime — a failure that appears only when
    someone runs it, and looks like a permissions problem rather than a missing
    line in this file.
    """
    assert "Bash(wfctl feature-paths*)" in _wrapper(step)


def test_no_speckit_skill_carries_the_instruction() -> None:
    """`vendor-upstream-skills` is the reason all four copies live in wrappers.

    The pull toward deduplicating them into the skills is real and this is what
    resists it. A rule moved there survives until the next upstream pull, then
    vanishes in a diff that mentions neither the rule nor the feature.
    """
    for step in _CONSUMERS:
        skill = _AGENTS / "skills" / f"speckit-{step}" / "SKILL.md"

        assert "## Software design decisions" not in skill.read_text()


# --- pass G, in analyze only -------------------------------------------------


def _analyze() -> str:
    return _wrapper("analyze")


def test_analyze_names_all_seven_detection_passes() -> None:
    """Six were listed by letter; a seventh added in prose alone is not run.

    The wrapper's coverage-row block is what the scan file is written from, so a
    pass described above it and missing from it produces a table that is silent
    about work the step did — which is the state #307's whole mechanism exists to
    replace.
    """
    analyze = _analyze()

    for pass_name in (
        "A · Duplication",
        "B · Ambiguity",
        "C · Underspecification",
        "D · Constitution alignment",
        "E · Coverage gaps",
        "F · Inconsistency",
        "G · Design-record contradiction",
    ):
        assert pass_name in analyze


def test_pass_g_sits_between_inconsistency_and_the_measurement() -> None:
    """The coverage table's last row is the only one carrying a percentage.

    Appending G after `Requirement-to-task coverage` would put a status row below
    a measurement, and the wrapper's own line about that row being the only one
    that differs would stop being true of the table it describes.

    Measured inside the coverage-rows section rather than across the file: pass G
    has a section of its own further up, so a whole-file `index()` finds that
    heading and reports an ordering the table does not have. The first version of
    this test did exactly that and failed on a correct wrapper.
    """
    rows = _analyze().split("**Coverage rows**")[1]

    inconsistency = rows.index("F · Inconsistency")
    pass_g = rows.index("G · Design-record contradiction")
    measurement = rows.index("Requirement-to-task coverage")

    assert inconsistency < pass_g < measurement


def test_pass_g_splits_severity_on_the_records_status() -> None:
    """Gating on `approved` alone is the literal reading of #121 item 6.

    It ships the pass dead: only a human moves a record past `proposed`, an
    unattended run moves none, and all seven records in this repository are
    `proposed`. The four-row table is what keeps the ratification distinction
    without making the check fire on nothing.
    """
    analyze = _analyze()

    assert "| `approved` | CRITICAL |" in analyze
    assert "| `proposed` | warning |" in analyze
    assert "| `superseded` | no finding |" in analyze
    assert "| `rejected` | no finding |" in analyze
    assert "Do not gate on `approved` alone." in analyze


def test_pass_g_compares_tasks_and_not_the_plan() -> None:
    """Left open, this doubles every finding it reports.

    Tasks are derived from the plan, so a plan element contradicting a record
    surfaces again as the tasks carrying it. Reporting both is not two findings
    about two problems — it is one problem reported twice, in a table a reader
    uses to judge how much was found.
    """
    assert "Tasks, and not `plan.md`" in _analyze()


def test_a_pass_g_finding_carries_the_record_and_the_task() -> None:
    """This pass is a model's judgement, so two runs can disagree.

    That is acceptable only because a finding is disputable, and it is disputable
    only with both halves in front of the reader. A finding naming the record
    alone asks them to take the contradiction on trust.
    """
    analyze = _analyze()

    assert "Record: `<arch-root>/design/<issue>-<decision>.md`" in analyze
    assert "Task: \"<the task, quoted>\"" in analyze


def test_pass_g_reports_and_never_gates() -> None:
    """A CRITICAL finding reads like a stop unless the wrapper says otherwise.

    Nothing in this feature refuses a transition, and `speckit-analyze`'s step 8
    remediation stays an offer. A reader who infers a gate either works around one
    that does not exist or reports the pipeline as broken.
    """
    assert "Pass G reports; it never gates." in _analyze()


def test_pass_g_writes_its_row_on_a_run_that_read_no_records() -> None:
    """The failure this row exists to prevent, met on its own empty path.

    A findings list renders identically for a thorough pass over clean artifacts
    and for a pass that never ran. So does a coverage row that is emitted only
    when something was found — which is the shape an implementer reaches for
    first, because writing a row about nothing feels like noise.
    """
    analyze = _analyze()

    assert "written on every run, including one that read no records" in analyze
    assert "| G · Design-record contradiction | None listed            |" in analyze
    assert "| G · Design-record contradiction | No design.md           |" in analyze
