"""Four pipeline steps read the level-3 design records their feature lists.

`/speckit.brainstorm` writes the records and `idea-refine` lists their paths in
`design.md`, and until #326 the chain stopped there: `speckit-plan` loads
`FEATURE_SPEC` and the constitution, `speckit-tasks` loads `plan.md`,
`speckit-implement` loads `tasks.md`, and `speckit-analyze` ran six detection
passes over those three artifacts. Eight records sat in `docs/architecture/design/`
and no step in the pipeline read any of them.

The instruction that closes it is prose under `wfctl/agents/`, which is the one
thing the suite cannot otherwise see — `install-skills` copies it, no test reads
it, and a wrapper that lost a rule would ship green. So every assertion here is
about the shipped bundle rather than about `wfctl/`, which this feature does not
touch at all.

**The split under test is the point.** The shared rule lives once, in
`reading-design-records/SKILL.md`; each wrapper carries a pointer to it and only
the part the four steps do not share. It did not start that way — it started as
forty-odd lines pasted into four wrappers, which a review panel found had
*already* drifted on the commit that introduced them, one copy carrying three
sentences the others had lost. So the assertions are split the same way the
instruction is: the rule is asserted once against the skill, and four times only
that each wrapper still points at it. A test that asserted the rule four times
would pass on four copies again.
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

_SHARED = _AGENTS / "skills" / "reading-design-records" / "SKILL.md"
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
    return body.split("\n## ")[0]


# --- the shared rule, asserted once ------------------------------------------


def test_the_shared_record_skill_ships() -> None:
    """Four wrappers point at it, and a pointer to a missing skill fails silently.

    That is `test_skill_cross_references`' subject one directory over; this
    asserts the specific one the feature cannot work without.
    """
    assert _SHARED.exists()


def test_the_shared_rule_reads_the_list_from_design_md() -> None:
    """The whole feature in one assertion, and the ordering inside it matters.

    A rule that names `design.md` but resolves it as `specs/<branch>/` finds
    nothing in this repository, which records a spec root outside the working
    tree.
    """
    shared = _SHARED.read_text()

    assert "wfctl feature-paths" in shared
    assert "## Software design decisions" in shared


def test_the_shared_rule_takes_bullet_entries_only() -> None:
    """The rule with the most consequence and the smallest surface.

    `## Software design decisions` legitimately carries prose as well as entries:
    `/speckit.brainstorm` requires a level answered with no record to say so in
    one line rather than delete the heading. That prose may name a *level-2*
    record — this feature's own `design.md` does. A rule that says "the paths
    listed in the section" without saying "list items only" is read as *every
    path*, and a level-2 record then loads as level-3, binding nothing while
    looking like it does.

    Caught by `/speckit.clarify` on this feature rather than by a run: the defect
    was in the artifact the pipeline was about to consume.
    """
    shared = _SHARED.read_text()

    assert "**list item**" in shared
    assert "Prose in that section names no records." in shared


def test_the_shared_rule_says_what_a_relative_path_resolves_against() -> None:
    """Two reviewers found this independently, and it disabled the feature.

    The producer's template emits `<arch-root>/…`, which `wfctl arch-root` prints
    absolute; the one real entry ever written is repo-relative and backticked.
    With no stated base, the natural reading for an agent that just opened
    `<FEATURE_DIR>/design.md` is that directory — which is outside the working
    tree, so every record resolves to nothing and reports as `listed, not found`.
    The feature would have failed on its own single test case.
    """
    shared = _SHARED.read_text()

    assert "REPO_ROOT" in shared
    assert "never against the directory holding" in shared


def test_the_shared_rule_refuses_the_issue_prefixed_glob() -> None:
    """The mechanism this feature shipped with first, and it was silently wrong.

    A worktree is named for the issue that existed when it was created; a record
    is numbered for the issue being implemented, not its epic; and a child issue
    is filed *during* the brainstorm pass, after the worktree exists. On any
    branch cut from an epic those three compose into a glob that loads another
    feature's record and misses this one, with no error either way — observed on
    `121-level3-downstream`, where `design/121-*.md` matched #122's record.

    Stated as a refusal because the glob is the obvious implementation, and a
    rule that only says what to do leaves the obvious wrong thing available.
    """
    shared = _SHARED.read_text()

    assert "Do not glob" in shared
    assert "design-md-indexes-the-records" in shared


def test_the_shared_rule_names_four_states_not_three() -> None:
    """The fourth state is the majority one, and the first draft had no name for it.

    A `design.md` with no `## Software design decisions` heading is neither
    `listed` nor `none`. A reviewer counted the tree: 19 of 27 `design.md` files
    under this repo's spec root have no such heading, so reading it as `none`
    asserts "the design pass recorded no decision" about a pass that predates the
    section — for most features, on the first run.

    `/speckit.brainstorm` supplies the ruling: a missing section "reads as a level
    nobody ran", which is `unknown`.
    """
    shared = _SHARED.read_text()

    assert "no such section" in shared
    assert "a missing section reads as a level nobody" in shared.lower()
    for state in ("`listed`", "`none`", "`unknown`"):
        assert state in shared


def test_the_shared_rule_reports_every_state(  ) -> None:
    """A run that found nothing and a run that never looked must not read alike.

    #307's argument one directory over. A rule that describes only the populated
    case leaves the empty states to the model's judgement, and they collapse.
    """
    shared = _SHARED.read_text()

    assert "listed in design.md" in shared
    assert "none — design.md records no level-3 decision" in shared
    assert "unknown — no design.md at" in shared


def test_the_shared_rule_reports_a_listed_path_it_could_not_read() -> None:
    """A record that moved is a broken reference, not an absence.

    Silently skipping it produces the `N listed` line with fewer than N paths
    under it, which reads as a miscount rather than a missing file — so the one
    state needing a reader's attention looks like a bug in the step.
    """
    assert "listed, not found" in _SHARED.read_text()


def test_an_out_of_tree_record_is_not_reported_as_missing() -> None:
    """`arch_root` outside the working tree is supported, not broken.

    `wfctl arch-root` warns and exits 0 there, and the records read fine. An
    earlier draft folded that case into `listed, not found` — which applies to
    the records the very argument `design-md-indexes-the-records` rejects for
    `design.md`, in the change that record justifies.
    """
    shared = _SHARED.read_text()

    assert "does **not** cover a path outside the working" in shared


def test_the_shared_rule_says_why_it_is_not_in_the_speckit_skills() -> None:
    """The reason has to travel with the rule, or the rule gets moved.

    Someone will reasonably want it in the four skills the wrappers point at. The
    answer is that those are upstream-derived and the edit would be reverted by
    the next pull with no conflict to notice — invisible unless it is written
    down.
    """
    shared = _SHARED.read_text()

    assert "vendor-upstream-skills" in shared
    assert "reverted by the next upstream pull" in shared


# --- the four wrappers, asserted only as pointers ----------------------------


@pytest.mark.parametrize("step", _CONSUMERS)
def test_every_consumer_points_at_the_shared_record_skill(step: str) -> None:
    """Half the instruction lives in one file so it cannot drift between four.

    It had already drifted before the split existed: the same paste went into
    four wrappers and three of them lost sentences the fourth kept, on the
    commit that introduced them.
    """
    assert ".agents/skills/reading-design-records/SKILL.md" in _record_section(step)


@pytest.mark.parametrize("step", _CONSUMERS)
def test_every_consumer_says_when_it_reads_them(step: str) -> None:
    """The one thing the shared skill cannot say for any of the four.

    A step that reads the records after doing its work has read them for nothing
    — the plan is already written, the tasks already generated. The timing is the
    step's own and is why each wrapper still carries prose at all.
    """
    section = _record_section(step)

    assert "**Before" in section


@pytest.mark.parametrize("step", _CONSUMERS)
def test_every_consumer_may_run_feature_paths(step: str) -> None:
    """An instruction to run a command the frontmatter does not allow is inert.

    The wrapper would ship, every test above would pass, and the step would be
    unable to resolve `FEATURE_DIR` at runtime — a failure that appears only when
    someone runs it, and looks like a permissions problem rather than a missing
    line in this file.
    """
    assert "Bash(wfctl feature-paths*)" in _wrapper(step)


def test_no_speckit_skill_carries_the_instruction() -> None:
    """`vendor-upstream-skills` is the reason none of this is in the four skills.

    The pull toward moving it there is real and this is what resists it. A rule
    moved there survives until the next upstream pull, then vanishes in a diff
    that mentions neither the rule nor the feature.
    """
    for step in _CONSUMERS:
        skill = _AGENTS / "skills" / f"speckit-{step}" / "SKILL.md"

        assert "## Software design decisions" not in skill.read_text()


def test_the_producer_warns_that_only_bullets_are_read() -> None:
    """The producer and the consumers had no agreed format, and still emit two.

    `/speckit.brainstorm` requires a level answered with no record to say so in
    one line. Written as a bullet, that line is a record entry with no resolvable
    path — indistinguishable from a record that has gone missing. The rule holds
    on this repo's own `design.md` only because its author happened to write that
    note as prose.
    """
    brainstorm = _wrapper("brainstorm")

    assert "prose in this section is not" in brainstorm
    assert "REPO_ROOT" in brainstorm


# --- pass G, in analyze only -------------------------------------------------


def _analyze() -> str:
    return _wrapper("analyze")


def test_analyze_names_all_seven_detection_passes() -> None:
    """Six were listed by letter; a seventh added in prose alone is not run.

    The wrapper's coverage-row block is what the scan file is written from, so a
    pass described above it and missing from it produces a table silent about
    work the step did — the state #307's mechanism exists to replace.
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


def test_pass_g_uses_only_severities_the_step_already_has() -> None:
    """`warning` was a fifth severity in a scale of four, found by all three reviewers.

    `speckit-analyze` step 5 defines CRITICAL / HIGH / MEDIUM / LOW, and step 6's
    report table has a Severity column that takes one of them. `warning` had no
    cell to sit in — and since every record on disk is `proposed`, it was the only
    value pass G could emit.
    """
    analyze = _analyze()

    assert "| `approved` | CRITICAL |" in analyze
    assert "| `proposed` | HIGH |" in analyze
    assert "| `superseded` | no finding |" in analyze
    assert "| `rejected` | no finding |" in analyze
    assert "warning" not in analyze.split("**Severity comes from")[1][:1200]


def test_pass_g_rows_use_the_shared_status_vocabulary() -> None:
    """A coverage row is one of four words, and pass G had invented five more.

    `writing-a-scan-file` fixes the vocabulary at `Clear`, `Resolved`, `Deferred`,
    `Outstanding`, and this same wrapper says the coverage-percentage row "is the
    only row" carrying anything else. Rows reading `1 CRITICAL` or `No design.md`
    made both sentences false at once. The count belongs in a parenthetical on a
    real status.
    """
    rows = _analyze().split("**Coverage rows**")[1]

    for value in ("Clear (2 records read)", "Outstanding (1 CRITICAL)", "Deferred (no design.md)"):
        assert value in rows


def test_pass_g_handles_a_record_whose_status_is_unreadable() -> None:
    """A record nobody can classify is the one most likely to be hand-written.

    Left undefined, the four-row table says nothing about a record with no
    `status` or an unrecognised one, and the safe-looking reading — skip it — is
    the one that silently drops the record least likely to have followed the
    template.
    """
    assert "absent or unrecognised" in _analyze()


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
    assert 'Task: "<the task, quoted>"' in analyze


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
    and for a pass that never ran. So does a coverage row emitted only when
    something was found — the shape an implementer reaches for first, because
    writing a row about nothing feels like noise.
    """
    analyze = _analyze()

    assert "written on every run, including one that read no records" in analyze
    assert "Clear (design.md lists none)" in analyze
    assert "Deferred (no records section)" in analyze
