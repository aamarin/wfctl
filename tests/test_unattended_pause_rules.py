"""What `clarify` and `analyze` do at an interactive pause nobody answers (#331).

`speckit.brainstorm.md` has carried a table of its skill's pauses since #283.
Neither review wrapper had one, and #325 flipped both steps to automatic — so an
unattended run entered each command and decided for itself what a pause meant.
The #299 run got past `analyze`'s remediation offer that way: an agent judged
that acting was fine, and no rule said so.

Two of these tests are cross-file rather than textual, which is the distinction
this module is built on. A table that *names* an upstream pause is worth nothing
if the pause it names no longer reads that way after an upstream pull — the
wrapper would go on describing a question the skill stopped asking, and
`vendor-upstream-skills` guarantees that pull lands with no conflict to notice.
So the pause quotes are matched against the skill they claim to quote.

The rest assert prose, and are the weaker kind on purpose: what they hold is a
decision whose loss is silent. #335 is where these rules become observed rather
than stated — the counts and the recorded basis both land in the scan file, which
is the yes side of `a-rule-is-expressed-as-a-check`.
"""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

import pytest

# The real shipped tree, for `test_skill_cross_references`' reason: conftest's
# autouse `bundle` fixture repoints `_bundle.BUNDLE_ROOT` at a fake one.
#
# `test_scan_files` opens with the same three lines and the same reason. Not
# shared: a test module importing another couples two files whose only relation
# is that both read these two wrappers, and that module already rejects the trade
# in `_repo`'s docstring. This comment is the pointer it costs instead.
_AGENTS = Path(str(files("wfctl"))) / "agents"

_REVIEW_WRAPPERS = ("clarify", "analyze")

# The heading both wrappers put the rules under. One string because two files
# spelling it differently is how a reader stops finding the second one.
_HEADING = "## When nobody answers"


def _wrapper(step: str) -> str:
    return (_AGENTS / "commands" / f"speckit.{step}.md").read_text()


def _skill(step: str) -> str:
    return (_AGENTS / "skills" / f"speckit-{step}" / "SKILL.md").read_text()


def _section(step: str) -> str:
    """The rules section alone, cut at the next same-level heading.

    Cutting at `\\n## ` rather than taking the rest of the file matters: both
    wrappers carry a scan-file section afterwards that also talks about step 8
    and about `Accepted`, and a test reading to end-of-file would pass on
    sentences this section never carried.
    """
    return _wrapper(step).split(_HEADING)[1].split("\n## ")[0]


def _flowed(text: str) -> str:
    return " ".join(text.split())


def _section_shape(step: str) -> str:
    """The copyable block under `**Section shape**:` — what an agent writes from.

    Not reached through `_section`, and not by cutting at the next `## ` either:
    the block's own first line is `## Session YYYY-MM-DD`, so a same-level cut
    lands inside the thing being read. The three tests below are about that
    template rather than about prose, because a rule whose template cannot hold
    it is what an unattended run actually hit.
    """
    return _wrapper(step).split("**Section shape**")[1].split("```markdown")[1].split("```")[0]


def _pause_rows(step: str) -> list[str]:
    """The table's body rows — the header and the `|---|` separator dropped."""
    rows = [ln for ln in _section(step).splitlines() if ln.startswith("|")]
    return [ln for ln in rows[1:] if not ln.startswith("|---")]


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_each_review_wrapper_carries_a_table_of_its_skills_pauses(step: str) -> None:
    """The shape #331 asked for, and the one thing a reader looks for first.

    Asserted as a table rather than as prose because the two columns are the
    content: a pause with no stated resolution, and a resolution attached to no
    pause, are both things a paragraph can say and a row cannot.
    """
    assert _HEADING in _wrapper(step)
    assert len(_pause_rows(step)) >= 3, "a pause the table does not name is one nobody governs"


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_every_pause_the_table_quotes_is_one_the_skill_still_asks(step: str) -> None:
    """The check with teeth here, and the only one an upstream pull can fail.

    Both skills are `github/spec-kit`-derived and are replaced wholesale on the
    next pull (`vendor-upstream-skills`). A reworded step 8 leaves this wrapper
    governing a question nobody asks any more, and the wrapper reads exactly as
    correct as it did the day before — there is no conflict, because nothing
    edited the wrapper.

    Every quote is checked, not a sampled one: the row that goes stale is the row
    whose wording upstream found worth changing.
    """
    skill = _skill(step)
    quoted = [q for row in _pause_rows(step) for q in re.findall(r'\*"([^"]+)"\*', row)]

    assert quoted, "the table names no upstream pause by its own words"
    for quote in quoted:
        assert quote in skill, f"speckit-{step} no longer says {quote!r}"


def test_the_clarify_rule_takes_the_answer_step_4_already_computed() -> None:
    """#331 asked how the recommendation relates to the answer taken; this is it.

    The alternative shapes were deferring the question or deriving a fresh answer
    at the pause. Both lose to this one for the same reason: step 4 renders its
    recommendation *and the reasoning for it* before any answer arrives, so the
    basis exists in the transcript before the decision does. An answer derived
    afterwards is one the run can shape to fit what it already wanted.

    Both literals are matched in the skill as well as in the wrapper — a wrapper
    telling the agent to reuse a label upstream stopped rendering sends it looking
    for something that is not there.
    """
    section = _section("clarify")
    skill = _skill("clarify")

    for label in ("**Recommended:**", "**Suggested:**"):
        assert label in section, "the wrapper does not say which computed answer to take"
        assert label in skill, f"step 4 no longer renders {label}"


def test_the_clarify_rule_refuses_to_invent_an_answer_it_cannot_derive() -> None:
    """The other half of #331's open question, and the half that can go missing.

    A rule that says "answer your own questions" and stops there is read by the
    next agent as licence to answer all of them, including the one about what a
    person wants. That is the silent decision `speckit.brainstorm.md`'s step-3 row
    already names as the failure the step exists to prevent, reached by obeying
    the remedy instead of skipping it.

    `Outstanding` rather than `Deferred` is asserted because only `Outstanding`
    drives this step's verdict to `unsatisfied`, which is the true statement about
    a scan that met a question it could not settle.
    """
    flowed = _flowed(_section("clarify"))

    assert "Do not invent a recommendation in order to have one" in flowed
    assert "`Outstanding` rather than `Deferred`" in flowed


def test_the_analyze_policy_decides_the_case_that_splits_its_candidates() -> None:
    """#331 listed three definitions of "in scope" and named where they disagree.

    A requirement with no task is a `tasks.md` edit that adds a task: in scope
    under "names an artifact the branch modifies", out under "adds no task". The
    issue's own words are that a policy silent here "will be resolved by whichever
    agent hits it first, which is the failure this issue exists to close" — so the
    case being decided, out loud, is the deliverable rather than a detail of it.

    Prose, and knowingly weak: nothing in the suite can see an agent apply the
    rule. What it stops is the sentence being dropped by an edit that thought the
    surrounding paragraph said enough.
    """
    flowed = _flowed(_section("analyze"))

    assert "A coverage gap is in scope" in flowed
    assert "no third door" in flowed


def test_the_clarify_withdrawal_still_puts_the_question_to_a_person() -> None:
    """Step 4 exists to ask a person the questions only a person can answer.

    The first draft made the withdrawal unconditional, on the reasoning that an
    answer the repository cannot derive is one the spec should have carried. That
    reasoning holds and the conclusion did not: unattended it withdraws, attended
    it takes the question away from the only reader who could have closed it, and
    the stated trigger for this whole section — a pause reached with no answer —
    has not happened. Caught on review of the branch that wrote it.
    """
    flowed = _flowed(_section("clarify"))

    assert "withdrawn only when no answer arrives" in flowed
    assert "unconditional" not in flowed


def test_the_analyze_in_scope_test_counts_the_constitution_as_having_decided() -> None:
    """Left off the list, the one finding the skill refuses to let stand is filed.

    `speckit-analyze` makes a constitution conflict automatically CRITICAL and
    says in its own words that it requires adjusting the spec, plan or tasks. A
    fix that brings a drifted artifact back into line decides nothing — the
    constitution decided it — but condition 2 named only the three artifacts and
    the design records, so the fix read as out of scope and got filed.
    `_predicates.analyze` reads the report's existence, so `implement` would then
    run over a known CRITICAL.
    """
    flowed = _flowed(_section("analyze"))

    assert "the project constitution have not" in flowed
    assert "Constitution Authority" in _skill("analyze")


def test_the_analyze_policy_defers_to_the_notify_gate_rather_than_around_it() -> None:
    """Filing is the one outward-facing action in a policy nobody is watching run.

    `wfctl issue create` refuses by default and only a person lifts it
    (`a-human-grants-outward-facing-authority`), so "file it as an issue" is
    unreachable on most branches this policy runs on. Left unsaid, the refusal
    reads to an agent as a misconfigured tracker, and the repair it reaches for is
    the backend directly — which is the gate defeated by the run it exists to
    constrain.

    The scan file is what catches the finding instead, and the reason line is what
    keeps "filed" and "somebody still has to file this" from rendering alike.
    """
    flowed = _flowed(_section("analyze"))

    assert "refuses by default" in flowed
    assert "Not filed:" in flowed


@pytest.mark.parametrize(
    ("step", "grant"),
    [("analyze", "wfctl issue create"), ("clarify", "wfctl issue view")],
)
def test_each_wrapper_can_run_the_tracker_verb_its_rules_require(
    step: str, grant: str
) -> None:
    """`allowed-tools` is a ceiling on the whole turn, so a rule without its grant
    reads correctly and cannot run.

    Silent in the worst way, as `test_scan_files` already records for the same
    field: the agent reports a tool refusal, not a missing instruction, and an
    unattended run has nobody to tell the difference to. Both grants are new with
    these rules — neither wrapper reached a tracker before them, analyze to file
    an out-of-scope finding and clarify to widen what an answer may rest on.

    Parametrized rather than written twice because the first version of this test
    covered analyze alone, which left clarify's grant as the kind of unpinned
    dependency the docstring above is about.
    """
    front = _wrapper(step).split("---")[1]
    allowed = next(ln for ln in front.splitlines() if ln.startswith("allowed-tools:"))

    assert grant in allowed


@pytest.mark.parametrize("step", _REVIEW_WRAPPERS)
def test_no_review_skill_carries_the_pause_rules(step: str) -> None:
    """`vendor-upstream-skills`: prefer layering to editing.

    The rules are about what the skill's own pauses become, so the skill is where
    they read most naturally and is the one place they must not be. An in-place
    edit is reverted by the next upstream pull with no conflict to notice, which
    is the failure mode #307 and #325 both routed around by writing into the
    wrapper.
    """
    assert _HEADING not in _skill(step)


def test_the_clarify_template_has_a_field_for_the_basis() -> None:
    """The rule was stated as the whole point of the section and the file had
    nowhere to put it.

    Found by running the step rather than by reading it: the wrapper requires an
    answer be recorded "together with the reasoning it was rendered with", and
    its section shape offered `Q: → A:` and `Decided against`. The second is the
    reasoning for the options *not* taken, which is the opposite question — so a
    real unattended run carried the basis inside the prose field meant for what
    was ambiguous, and #335 would have had nothing to key on.

    On both finding shapes, because the short-answer branch is where a field
    added to one example quietly stops being required.
    """
    template = _section_shape("clarify")

    assert template.count("Basis:") == 2


def test_the_clarify_template_has_somewhere_to_put_an_outstanding_question() -> None:
    """`| Category | Status |` is two columns and one of them is one word.

    The rule says the `Outstanding` row carries the question and what made it
    underivable. The coverage table cannot take either, and the marker rule from
    #325 has wanted the same block since before this change — a run that followed
    both wrote a heading the section shape does not license.
    """
    template = _section_shape("clarify")

    assert "### Outstanding" in template


def test_the_analyze_template_keeps_a_refused_filing_whole() -> None:
    """A reason line says somebody still has to file this and drops what to file.

    The policy's out-of-scope half is only as good as what survives it. Without
    the command, the person who picks the finding up re-derives a title and a
    body from a report that by then holds several — which is the tracker debt the
    apply half of the policy exists opposite, arriving through the other door.
    """
    template = _section_shape("analyze")

    assert "Not filed:" in template
    assert "### Filing" in template
