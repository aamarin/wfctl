"""What each pipeline step reads, and what it concludes from it.

Separate from `_pipeline` because the two change for different reasons. The walk
— which step comes next, what cascades, how the payload is shaped — moves when
the pipeline's structure changes, which is rarely. What a step accepts as
evidence moves whenever someone decides a rung was too weak, which is four open
issues at the time of writing (#308, #309, #240, #299). Held in one module those
were the same diff, and a reviewer could not tell which half a change came from.

Every predicate here has one signature — `(Evidence) -> Reading` — so `_STEPS`
can hold it and the walk never names a step. The signature was extracted rather
than designed: `_implement_verdict` already returned a state and a reason, and
the six values in `Evidence` are the reads the walk already performed before its
loop began. `Reading`'s third field arrived later, to carry the one annotation
that is not simply a reason.

`_pipeline` imports from here and never the reverse. The step table lives there
and holds these functions as values, so the arrow only points one way.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable
from typing import Literal, NamedTuple

from wfctl import _md, _tracker
from wfctl._paths import arch_root

# What reading one evidence source concluded. Three values rather than a bool
# because "the evidence says proceed" and "there was no evidence" are the two a
# bool collapses, and the rule below is the one place that distinction is spent.
Verdict = Literal["satisfied", "unsatisfied", "inconclusive"]

# Who owed the evidence. Closed rather than a bare `str`: the rule reads
# "promised or not", so an unrecognised source would take the ambient branch and
# proceed — a typo failing open on evidence somebody promised. mypy is not strict
# here, and a `str` parameter is the shape that hides it.
Source = Literal["repo-declared", "accepted-record", "human", "ambient"]

# Sources someone undertook to produce. The repo declares its commands, the
# process accepts its records, a person records an approval — so silence from
# one of these is a missing answer, not the absence of a question.
_PROMISED: frozenset[Source] = frozenset({"repo-declared", "accepted-record", "human"})


# The four names a step's position can take. A closed set rather than `str`
# because `pipeline-state-is-one-payload` writes these four out by hand and
# nothing checked them — a predicate returning "finished" type-checked fine and
# rendered as an unknown glyph. `done` and `skipped` both advance the pipeline;
# `in_progress` and `pending` both hold it, and differ in whether anything ran.
State = Literal["done", "in_progress", "pending", "skipped"]


class Reading(NamedTuple):
    """What one predicate concluded: the state, why, and what to render.

    `reason` rather than a bool because the caller renders the string, and a
    caller that only needs to know *whether* the step is blocked reads it as
    truthy.

    `annotation` defaults to `None`, which means "the reason is what renders" —
    true of seven steps. `implement` is the eighth: it prefixes a task tally, so
    its annotation carries something its reason cannot be recovered from, and the
    routing read wants the reason alone. Carried here rather than composed in the
    walk so the walk never has to know which step is the exception — that branch
    was the last `if name ==` left in it.
    """

    state: State
    reason: str | None = None
    annotation: str | None = None

    def renders(self) -> str | None:
        """What a view shows for this step."""
        return self.reason if self.annotation is None else self.annotation


# What every step's predicate is.
Predicate = Callable[["Evidence"], Reading]


# The three values one readiness fact takes. A closed set for `State`'s reason —
# mypy is not strict here, so a derivation returning "missing" would type-check
# and render as an unknown glyph.
#
# Three words that appear in neither neighbouring vocabulary, deliberately.
# `State` grades a step and `Verdict` grades whether evidence could be read at
# all; borrowing either set here would make one of those rules look applicable to
# a question it does not answer. `n/a` in particular is not `inconclusive`:
# `inconclusive` means the evidence was owed and could not be read, and `n/a`
# means nothing owed it because the question does not arise on this branch.
FactValue = Literal["met", "unmet", "n/a"]


class Fact(NamedTuple):
    """One of the four questions that decide whether a branch is ready.

    A fact is about the *branch*, not about a step —
    `readiness-is-not-a-step-state` is the record, and the whole point of it is
    that a step state answers one question and these answer four. Three of the
    four are answerable with no spec dir at all.

    `detail` is never None. Every value has something to say — `met` names what
    was read, `unmet` names what is missing, `n/a` names why the question does
    not arise — and a nullable field would let a derivation answer without one,
    which is the state the issue was filed against one level up.
    """

    name: str
    value: FactValue
    detail: str


# Statuses a person moved a record to. `proposed` is the one that means nobody
# has, and a status outside `_arch.STATUSES` parses to "" — so both fall outside
# this set without being named in it.
#
# Not "accepted" alone, which was the first shape and is wrong for a branch that
# supersedes a record: that leaves the old record at `superseded`, which a human
# did decide, and requiring `accepted` would hold such a branch forever.
_RULED_ON = frozenset({"accepted", "superseded", "rejected", "retired"})

# Sources whose answer could not be read, as opposed to answering no. Routed
# through `blocks` below rather than mapped straight to a value, so the rule that
# says what unavailable *promised* evidence means stays the one in
# `promised-evidence-blocks-on-silence` and is not restated here.
_UNREADABLE_GRANT = frozenset({"unreadable", "corrupt", "unknown-trunk"})

# The right-hand column of the fact block, keyed on which of the seven answers
# resolved the grant.
#
# Not `cli._NOTIFY_LINES`, which says the same things in longer words. That table
# renders one standalone line, so each entry has to be a complete sentence about
# what the run will do; these sit beside a name that has already asked the
# question, so the sentence would repeat it. Two renderings of one fact is what
# the payload is for — what would be wrong is two *derivations*, and there is one.
_GRANT_DETAIL = {
    "local": "you allowed it in this worktree",
    "label": "you allowed it on the issue",
    "unset": "nobody has allowed it for this work",
    "deny": "you turned it off here",
    "unreadable": "couldn't reach the issue tracker to check",
    "corrupt": "couldn't read the setting for this work",
    "unknown-trunk": "couldn't tell which branch is trunk",
}

# The design step's annotation when the boundary question went unanswered. Short
# because it sits inline in the step table; the two remedies are spelled out by
# `_pipeline.DESIGN_BLOCK_HELP`, which is formatted with a per-repo location.
# Here rather than there because it is what this module concludes; the help is
# how a view renders that conclusion.
DESIGN_BLOCK_REASON = "no architecture record for this change"

# The tasks step's annotation when its file holds no task (#308). Names the file
# rather than the step, because `status` prints it on the `tasks` row and "no
# tasks" there reads as a judgement about the work rather than about the artifact.
_TASKS_EMPTY_REASON = "tasks.md holds no task"


def blocks(verdict: Verdict, source: Source) -> bool:
    """Whether this verdict stops the step, given who owns the evidence.

    The gate does not decide this — see
    `docs/architecture/promised-evidence-blocks-on-silence.md`. A gate sees one
    transition and one source, which is how three gates here came to hold two
    policies without any of them being wrong. Whether anyone undertook to
    produce the evidence is a fact about its origin and reads the same at every
    gate, so it is answered once, here.

    Ambient evidence proceeds on silence because nothing promised it: a git fact
    that cannot be computed is not an answer the user can go and supply, and
    refusing on it stops a pipeline with no action that unblocks it.
    """
    if verdict == "inconclusive":
        return source in _PROMISED
    return verdict == "unsatisfied"


@dataclass(frozen=True)
class Evidence:
    """The reads the walk already performed before its loop, given a name.

    Not everything the predicates read, and deliberately not: `decompose` opens
    `delivery.md` and the tracker config inside itself, `implement` reaches a
    verification record and git through `verification_block`, and five predicates
    `stat` their own artifact. Those stay deferred because `cascade` means most
    runs never reach them — what is gathered here is what the walk paid for
    unconditionally before this change, and nothing more.

    Frozen because a predicate that mutated it would make the step order
    significant, and the order is the walk's business — a predicate decides its
    own step from evidence and nothing else.

    `spec_dir` is a `Path` and not `Path | None`: the walk returns eight pending
    steps before building this, so no predicate is ever reached without one and
    none carries a guard for it.
    """

    spec_dir: Path
    repo_root: Path
    # `spec.md` with fenced blocks and inline spans blanked, so a spec that
    # *documents* a marker or a heading does not read as having one. Empty when
    # the file is absent.
    spec_text: str
    has_markers: bool
    # `plan.md`, blanked the same way and for the same reason: since #309 the
    # plan predicate reads its sections, and `plan-template.md` carries `#` lines
    # inside fenced blocks — so an unblanked read would count a section the
    # document only illustrates. Empty when the file is absent.
    plan_text: str
    tasks_text: str
    tasks_open: bool
    # The tally, taken beside the one read of the file rather than recomputed by
    # each of the two predicates that need it (#308). `tasks_total` is zero for a
    # file that holds no task *and* for no file at all — `tasks_text` is what
    # tells those apart, and both predicates check it first.
    tasks_done: int
    tasks_total: int


def _file_exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


# The sections each artifact must carry for its step to pass. wfctl's own list,
# not one read from the template — `required-sections-are-wfctls`. Inference
# reads a spec directory and nothing else, and the template it would otherwise
# consult need not be installed in the repository under inspection: a repo that
# never ran `install-skills` has no `.specify/`, and neither answer to its
# absence is acceptable. `tests/test_pipeline_sections.py` holds these against
# the templates the same wheel ships, which is the condition the record accepted
# the coupling under — a rename fails the build here rather than changing a
# verdict in the field.
#
# Stems rather than whole lines. The template's own `_(mandatory)_` suffix
# reaches real specs verbatim, so a whole-line match would reject the corpus
# these were measured against. Template order, because the annotation lists what
# is missing and that is the order the reader will look for them in.
_REQUIRED_SPEC_SECTIONS: tuple[str, ...] = (
    "User Scenarios & Testing",
    "Requirements",
    "Success Criteria",
    "Validation Strategy",
)

# `plan-template.md` marks nothing `_(mandatory)_`, so this is wfctl's choice
# from the headings that template does carry — which is why the drift test
# asserts the two halves differently, and says so in its own docstring.
#
# `Complexity Tracking` is carried by 23 of the 24 plans on disk and is still not
# here. The template's own line above that section reads "Fill ONLY if
# Constitution Check has violations that must be justified", so a plan with no
# violations is *instructed* to delete it — and requiring it would leave that
# author unable to clear the step by following the template they were given. A
# required list may be stricter than what authors happen to do; it may not
# contradict the document it is derived from.
_REQUIRED_PLAN_SECTIONS: tuple[str, ...] = (
    "Summary",
    "Technical Context",
    "Constitution Check",
    "Project Structure",
)

# The templates' own instruction to the author, which they also tell the author to
# delete: "ACTION REQUIRED: Replace the content in this section", inside an HTML
# comment. Its presence means the document is still the template.
#
# This exists because structure alone could not tell the two apart, and on the
# path the tool itself takes they are the same document: `setup-plan.sh` runs
# `cp plan-template.md plan.md`, so the first act of `/speckit.plan` creates a
# file carrying every required heading and nothing else. `spec.md` was already
# covered — its template ships `[NEEDS CLARIFICATION` markers and the marker
# check catches them — and the plan template has no equivalent, so a rung this
# step claimed was not reached in the one case that always happens.
#
# The string rather than `NEEDS CLARIFICATION`, which would have been the
# symmetric choice: three plans on disk discuss clarification markers in prose,
# so it rejects real work. No spec or plan on disk carries this one, and both
# templates do — which is the pair a placeholder marker needs.
#
# Blanking leaves it alone: `_quoted_out` removes fences and inline spans, and
# this lives in an HTML comment. That is deliberate. A document quoting this
# constant inside a fence is discussing it, not carrying it.
TEMPLATE_PLACEHOLDER = "ACTION REQUIRED"

# Short, because they render inline in the step table beside the step's name.
UNWRITTEN_TEMPLATE = "still the template"

# clarify passed because a plan already exists, not because a scan ran.
CLARIFY_UNSCANNED = "scan never ran"


def _missing_sections(text: str, required: tuple[str, ...]) -> tuple[str, ...]:
    r"""Which of `required` the document does not carry, in the order given.

    `^##[ \t]+<name>(?!\w)` is `clarify`'s idiom for its own heading, reused
    rather than reinvented so the structural reads in this module cannot drift
    apart. MULTILINE anchors `^` to a line rather than the file. `[ \t]` rather
    than `\s` so a bare `##` line followed by the name on the next line is not a
    match. The lookahead rejects `## RequirementsTODO`, and also rejects
    `## Functional Requirements` — the second is the strictness the list was
    chosen for, and why three spec directories written before this pipeline
    existed do not satisfy it.

    `(?!\w)` and not `\b`, which is the same assertion only while every name
    ends in a word character. One ending in `)` or `_` — `Requirements (v2)`,
    say, after an upstream rename the constants were updated to follow — makes
    `\b` require a word character *next*, so the heading never matches, the
    drift test still passes because the strings agree, and `specify` becomes
    unpassable in the field. That is precisely the silent verdict change SC-004
    claims the build catches, arriving through the one door the build does not
    watch.
    """
    return tuple(
        name
        for name in required
        if not re.search(rf"^##[ \t]+{re.escape(name)}(?!\w)", text, re.MULTILINE)
    )


def _missing_reason(missing: tuple[str, ...]) -> str | None:
    """The held step's line, or None when nothing is missing.

    Names them rather than counting them: the reader fixes the artifact without
    opening it, which is what the annotation slot is for. Template order comes
    from the constant, so the list reads in the order the document declares.
    """
    return f"missing: {', '.join(missing)}" if missing else None


def _quoted_out(text: str) -> str:
    """Markdown with its fenced blocks and inline spans blanked out.

    An artifact that *documents* a syntax must not read as using it — a spec
    showing what a clarification marker looks like has no marker, and a
    `tasks.md` showing what a task line looks like holds no task. Every artifact
    read here quotes the rules it is checked against, so that is the common case
    rather than the exotic one.

    Fences come from `_md.walk` and not from a regex of our own. The regex this
    replaced was a fourth private implementation in a package whose one fence
    walker exists because three modules each carrying their own answered
    differently — and it failed open on the three shapes that matter: `~~~`
    fences, a ```-block nested inside a ````-fence, and an unclosed fence. Each
    let an *illustrated* heading or marker read as a written one, which since
    #309 decides whether a step passes rather than only how a marker is counted.

    Lines are blanked rather than dropped so line structure survives: `^##` under
    MULTILINE is what the callers match with, and deleting lines would join a
    fenced block's neighbours into one.

    Inline spans stay a local regex. `_md` answers a question about lines and
    this one is within a line; `[^`\n]+` excludes newline so an unpaired
    backtick cannot swallow the rest of the file.
    """
    return "\n".join(
        "" if line.inside or line.fence else re.sub(r"`[^`\n]+`", "", line.text)
        for line in _md.walk(text)
    )


def _task_tally(tasks_text: str) -> tuple[int, int]:
    """How many tasks are ticked, and how many there are.

    One spelling for the three readers that need it — `_tasks_open`, the `tasks`
    predicate, and the tally `implement` annotates with. The count is what they
    would each have written out, and #262 is what two hand-written copies of a
    tasks predicate cost.

    A total of zero is not the same fact as an empty string, and the difference
    is #308: no file means the step has not run, and a file with no box in it
    means the step ran and wrote down no task. Callers that need to tell those
    apart read `tasks_text` themselves.

    Counted over the text with code quoted out, because the total now gates an
    automatic step: an example box inside a fence would otherwise be a task, and
    a file whose only box is a worked example would clear the step it documents.
    Matched anywhere on the line rather than at a list bullet — real files write
    `**Checkpoint**: [X] T006 …`, and anchoring to `- [ ]` loses those.
    """
    text = _quoted_out(tasks_text)
    done = len(re.findall(r"\[x\]", text, re.IGNORECASE))
    return done, done + len(re.findall(r"\[ \]", text))


def _tasks_open(tasks_text: str, spec_dir: Path) -> bool:
    """Whether the tasks are still open, by the two routes `implement` reads as
    finished: every box ticked, or the sentinel that says so over one left open.

    Only the tasks. A caller asking whether *implementation* is finished wants
    this and `verification_block` — a definition of done gets the last word over
    both routes here (#69), and a caller that negates this alone has skipped it.

    A file holding no box at all takes neither route. It was read as the first
    one — nothing was left open, because nothing was written down — and that is
    what carried `implement` to its verification read at `0/0 done` having
    proved nothing (#308). Zero ticked out of zero is the absence of evidence,
    not evidence of completion.

    A function rather than a local, because a local answers the reads inside
    `_infer_steps` and cannot reach `next_step_content`, which spelled the
    predicate with the boxes alone and routed a story whose definition of done
    had not passed straight back to `/speckit.implement` with `auto: true`
    (#262). The sentinel exists precisely for the story whose boxes are not a
    reliable signal, so dropping it inverts the case it was written for.

    Takes the text rather than reading it, so a caller that already holds it
    decides from one read. The walk reads `tasks.md` for its own tally, and a
    second read inside here let the tally and this answer come from two versions
    of a file an implementing agent may be rewriting.
    """
    if _file_exists(spec_dir / "checklists" / "implement-complete.md"):
        return False
    done, total = _task_tally(tasks_text)
    if total:
        return done < total
    # No box anywhere. An absent file is not this function's question — the
    # predicates that care read `tasks_text` and report `pending` before asking —
    # so the remaining case is the file that exists and holds no task.
    return bool(tasks_text)


# The Issue Grouping Map, and the `|---|---|` line markdown puts under every
# table header. Rows are read by position — the lines after that separator, and
# the first cell of each — rather than by matching header labels. Both halves of
# that are the template's contract (`delivery-plan-template.md`): it fixes
# `Issue` as the leading column, and a label-driven scan would count the header
# row itself, whose `Issue` cell carries no key, as a row that failed.
_ISSUE_MAP_SECTION = re.compile(
    r"^#{1,6}[ \t]+Issue Grouping Map\b(?P<body>.*?)(?=^#{1,6}[ \t]|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)
_TABLE_SEPARATOR = re.compile(r"^\|[\s:|-]+\|$")


def _unkeyed_issues(text: str, key_pattern: str) -> int | None:
    """How many rows of a delivery plan promise an issue that does not exist yet.

    The Issue Grouping Map is authored with placeholder keys and filled in once
    the issues are created. Creating them tells people outside the repo, so what
    it waits on is the notify grant (#280) rather than this step, which since
    #240 runs unattended — ungranted, the run writes the plan and stops before
    the tracker. An unkeyed row is therefore a legitimate mid-decompose state;
    what was wrong was reading it as a finished one (#8).

    None means there is nothing here to judge — no map, or a map with no rows. A
    delivery plan predating the table is not evidence that issues are missing, so
    it goes on reading `done`.

    The key is looked for in the `Issue` cell alone, never across the whole row.
    `speckit-orchestrate` searches whole rows, but it is matching one key it
    already holds; here the `Closes With` cell carries `PR #4`, which would
    answer for the `_(TBD)_` beside it and hand back the state this exists to catch.
    """
    section = _ISSUE_MAP_SECTION.search(text)
    if section is None:
        return None

    rows: list[str] = []
    past_separator = False
    for line in (ln.strip() for ln in section.group("body").splitlines()):
        if _TABLE_SEPARATOR.match(line):
            past_separator = True
        elif not past_separator:
            continue
        elif line.startswith("|"):
            rows.append(line)
        else:
            break

    if not rows:
        return None

    # Anchored. Searching the cell, `_(TBD)_ (Issue 1)` satisfies the default
    # `\d+` on the `1` and the placeholder reads as a created issue; the template
    # mandates the key *lead* the cell, so matching from the front is reading the
    # contract rather than tightening it.
    #
    # Compiled exactly as configured, with the optional `#` taken off the cell
    # instead of wrapped around the pattern. `speckit-orchestrate` spells this
    # `#?{key_pattern}`, and building that here is what a repo cannot survive: a
    # pattern opening with an inline flag — `(?i)PROJ-\d+` — compiles alone, so
    # `load_key_pattern` hands it over, and then dies as `#?(?:…)` on "global
    # flags not at the start". Not a misread state; `wfctl status` exits on a
    # traceback for every feature that has a delivery plan.
    key = re.compile(key_pattern)

    def keyed(row: str) -> bool:
        # GitHub keys are written `#251` in prose; a `PROJ-123` never takes one.
        cell = row.split("|")[1].strip().removeprefix("#")
        return key.match(cell) is not None

    return sum(1 for row in rows if not keyed(row))


def verification_block(repo_root: Path) -> str | None:
    """Why `implement` cannot be complete, or None if nothing blocks it.

    Returns the *first* matching reason, in the order below. Where two hold at
    once the earlier one wins, and the order is chosen so the reason a user can
    act on is named ahead of the one they would only reach after fixing it: a
    failed run on a moved commit reports the failure, not the staleness.

    A repository with no definition of done is never blocked — that is the whole
    degrade path (FR-002), and it must cost nothing, so the config read happens
    before anything touches git.

    Public because the `implement` step is not the only place this answer is
    wanted. It is the only place that *has* one: a change `design-levels` sends
    around the pipeline reaches no `implement` step, so until #236 nothing asked
    this question about it. Takes `repo_root` alone and resolves the branch
    itself, which is what lets a caller with no spec dir call it at all.
    """
    from wfctl import _verify
    from wfctl._paths import resolve_agent_dir, resolve_branch

    commands, errs = _verify.load_config(repo_root)
    if errs:
        return "definition of done is malformed — run `wfctl verify`"
    if not commands:
        return None

    agent_dir = resolve_agent_dir(repo_root, resolve_branch(repo_root))
    record = _verify.load_record(agent_dir)
    if record is None:
        return "unverified — run `wfctl verify`"
    # The rule, not a second copy of it. A run whose tree moved underneath it
    # produced no verdict, and `wfctl.json` is the repo undertaking to produce
    # one — so this blocks by `promised-evidence-blocks-on-silence`, and it
    # blocks for the reason stated there rather than for a reason local to here.
    # Wired through `blocks` so the two gates cannot drift again: changing the
    # rule has to change both, because there is one rule.
    if blocks("inconclusive" if record["inconclusive"] else "satisfied", "repo-declared"):
        return "inconclusive — re-run `wfctl verify`"
    if record["exit"] != 0:
        failed = [" ".join(c) for c in record["failed"]]
        # Name the commands, not just the count: SC-006 requires a blocked user
        # to learn which one failed from `status` alone.
        return (
            f"failed — {len(failed)} of {len(record['command'])} "
            f"at {record['sha'][:7]}: {', '.join(failed)}"
        )
    if record["command"] != commands:
        return "stale — definition of done changed since it was verified"

    sha, dirty = _verify.code_identity(repo_root)
    if record["sha"] != sha:
        return f"stale — verified at {record['sha'][:7]}, HEAD is {sha[:7]}"
    if record["dirty"] or dirty:
        return f"stale — verified at {record['sha'][:7]}, tree has uncommitted changes"
    return None


def design_block(spec_dir: Path, repo_root: Path) -> str | None:
    """Why the design step cannot be complete, or None if nothing blocks it.

    Shaped like `verification_block` on purpose: both are a step's own evidence
    read, both report through inference, and the payload carries the reason.
    The previous shape returned `bool` to `cli`, which refused the transition
    beside the payload rather than in it — so `status` named a command `next`
    then refused, and `speckit-orchestrate` carried a prose workaround for the
    disagreement. `pipeline-state-is-one-payload` already forbids a fact
    computed inside a view; this is that fact moved back.

    Reported on the design step rather than at the transition out of it, but
    still scoped to that one transition: a step whose boundary question went
    unanswered has not finished, which is the same thing `verification_block`
    says about `implement` and needs no second mechanism to say it. Once
    `spec.md` exists the pipeline is past the boundary and the gate is done —
    see the guard below, which is the old `_AFTER_DESIGN` condition in the terms
    this arm already speaks.

    A record anywhere under the arch root answers, whatever its status: a
    `proposed` record still means the question was put. `design/` is excluded
    rather than counted — it holds level-3 records, which govern one feature and
    are barred from drawing a boundary, and #121 item 3 lands one in every such
    branch diff.

    What it does not check is whether the record is *about* this change, or
    whether a declaration is true. Neither has an objective test, and FR-010a
    settles the point: the purpose is to stop the question going unanswered, not
    to catch a wrong answer.
    """
    if not _file_exists(spec_dir / "design.md"):
        return None
    if _file_exists(spec_dir / "spec.md"):
        # Past the boundary. "Advance past the design step" is one transition,
        # and a gate that stayed up through plan, tasks and implement would
        # refuse work that already answered by moving on. `spec.md` is what
        # "a later step ran" looks like — the same stand-in the brainstorm arm
        # uses to tell `skipped` from `pending`.
        return None

    from wfctl._paths import touched_on_this_branch

    arch = arch_root(repo_root)
    # Three states in, three states out. `touched_on_this_branch` already returns
    # `None` for "git cannot answer" and says in its own docstring why — the old
    # call site spent that third state on `is False` one line after computing it.
    touched = touched_on_this_branch(repo_root, arch, exclude=arch / "design")
    verdict: Verdict = (
        "inconclusive" if touched is None else "satisfied" if touched else "unsatisfied"
    )
    return DESIGN_BLOCK_REASON if blocks(verdict, "ambient") else None


# What each predicate proves (#300, epic #100 scope 5). The rungs, weakest first:
# 1 an artifact was written; 2 the artifact has structure; 3 known questions were
# addressed, syntactically; 4 promised external objects exist; 5 executable
# completion criteria passed; 6 a decision has authority; 7 integration was approved.
#
# Rungs are not the four facts above, and the two vocabularies are kept apart on
# purpose (#299). A rung grades how strongly *one predicate* proves something
# about *its own step*; a fact is one of four questions about the branch. Only
# rungs 6 and 7 line up one-to-one, with `fact_architecture_accepted` and
# `fact_integration_authorized` — the two no predicate here reaches. Rungs 1
# through 5 are all evidence that a step's artifacts were written and how well,
# which is a single fact, so a stated mapping would be right about two rows and
# wrong about five.
#
# Beside the predicates by `knowledge-placement`: a fact about one file belongs to
# that file, and this is a fact about the functions below. It sat in `_pipeline.py`
# until #314, when the functions moved and it did not — which is exactly the drift
# its own closing line warns about.
#
# The two conditions that hold over all eight are facts about the *walk*, not about
# any predicate, and they are stated in `_pipeline.py` where the walk is.
#
#   brainstorm  1, and a gesture at 6 rather than 6 itself: a design doc exists and
#               git says some path under `<arch>/` outside `design/` changed on this
#               branch — an edit to a descriptive view, or a deletion, counts as
#               readily as a new record — or git could not say, which proceeds
#               (`ambient`). Never checked to be about this change, and not read at
#               all once `spec.md` exists.
#   specify     1 + 2 + 3. `spec.md` carries every section in
#               `_REQUIRED_SPEC_SECTIONS`, is not still its own template, and has
#               no marker left. Nothing under a heading is read, so 2 is the
#               heading and not its contents.
#   clarify     2 + 3. A `## Clarifications` heading, and no marker left; nothing
#               under the heading is read. `skipped` where `plan.md` exists and the
#               heading does not — annotated `scan never ran`, because that pass
#               is on the plan's existence and not on evidence a scan happened.
#   plan        1 + 2. `plan.md` carries every section in `_REQUIRED_PLAN_SECTIONS`
#               and is not still its own template — which structure alone cannot
#               tell, since `setup-plan.sh` makes the file by copying the
#               template. Never 3: a plan has no marker to carry.
#   tasks       2. `tasks.md` is non-empty and holds at least one checkbox (#308).
#               Never 3: what a task says is not read, and neither is whether it
#               is ticked — a file of open boxes finishes this step. `skipped`
#               where the implementation sentinel stands over a file with no box.
#   analyze     1. `checklists/analysis-report.md` is non-empty.
#   decompose   1, and a claim of 4 rather than 4 itself: `delivery.md` is non-empty,
#               and where a tracker is configured and it carries an Issue Grouping
#               Map, every row names a key — read from the delivery plan's own prose,
#               so the plan asserts its issues exist rather than the tracker
#               confirming it. Stops blocking once the tasks read closed, and
#               `skipped` where no plan exists and they already have. #100 scope 5
#               records this as rung 4 since #8; it does not reach one.
#   implement   5, or 1 + 3 where the repo declares no definition of done (FR-002):
#               the tasks read closed, and a repo-declared verification passed
#               against this tree.
#
# `blocks` is consulted three times, by the three predicates whose evidence has an
# inconclusive state to judge — `implement` as `repo-declared`, `brainstorm` and
# `decompose` as `ambient`. `tasks` reads inside its file and still reaches none:
# the file is read or it is absent, and one holding no task is `unsatisfied`, which
# stops the step whoever owed the evidence. The other four read a file that is
# there or is not.
# `decompose` was the exception until #314: it resolved two of its own readings —
# no tracker configured, and a plan carrying no map or no rows — without reaching
# the rule. Both still proceed; they now proceed because `blocks` says so.
#
# Two steps run automatic over a rung that sits below the flag, and neither is a
# gap left open. #283 settled `brainstorm` on reversibility. #240 settled
# `decompose` on a narrower claim: the part of that step which reaches people is
# creating the issues, and what stands in front of that is the notify grant
# `speckit-delivery-plan` reads before it creates any (#280) — never this flag.
# What the rung has to carry is therefore only the local half. A blocked step is
# never automatic whatever the table says (`next_step_content`), which is what an
# unkeyed map still stops.
#
# What it does not stop is either `ambient` reading above, and the second changed
# company when the flag moved: a `delivery.md` whose Issue Grouping Map is absent
# or misspelled reads `done`, and the run carries on to `implement`. The states
# either side of the flip are identical — a step reading `done` was never a pause
# — but the plan is now written with nobody there to see it come out malformed.
# Accepted on the ground the reading itself stands on: a plan predating the map
# and one written wrong are one file to this check, and refusing both strands
# every feature written before the map existed.
#
# Nothing pins these lines to the predicates they describe — re-read the function
# before trusting one.


def fact_artifacts_written(ev: Evidence | None) -> Fact:
    """Did this feature's steps write their artifacts? Owner: the spec dir.

    Reads `Evidence`'s three texts and no step's conclusion. That distinction is
    the feature: the predicates read these same three files, and reading their
    *verdicts* instead would be the collapse `readiness-is-not-a-step-state`
    undoes.

    Takes `Evidence | None` because `_infer_steps` builds none when no spec dir
    resolved. An empty `Evidence` would have served the type and not the answer —
    three empty strings cannot be told from a feature directory holding three
    empty files, and those are different states.

    Stops at the three `Evidence` gathers. Reaching further — `delivery.md`, the
    checklists — means re-implementing predicates that own those reads, and
    `Evidence` is this repo's own definition of what the walk already paid for.
    """
    name = "artifacts written"
    if ev is None:
        return Fact(name, "unmet", "no spec dir for this branch")
    written = {"spec.md": ev.spec_text, "plan.md": ev.plan_text, "tasks.md": ev.tasks_text}
    missing = [n for n, text in written.items() if not text]
    if missing:
        return Fact(name, "unmet", "missing " + ", ".join(missing))
    return Fact(name, "met", ", ".join(written))


def fact_definition_of_done(repo_root: Path) -> Fact:
    """Did the repo's own check pass on this tree? Owner: `wfctl.json` + the record.

    `verification_block` already holds every reason this can be unmet, in the
    order a user can act on. What it cannot say is the difference between "passed"
    and "there was nothing to run": both are `None`, because a repo with no
    definition of done is never blocked (FR-002) and that degrade path must cost
    nothing.

    So the config is asked first, for exactly that distinction, and the answer is
    not a second opinion — `load_config` returning no commands and no errors is
    the same first branch `verification_block` takes before it touches git.

    The record is read once more for the sha it verified against. That is a
    second read of one small file and not a second inference: the verdict is
    already decided above, and this only asks which tree it was decided about.
    """
    from wfctl import _verify
    from wfctl._paths import resolve_agent_dir, resolve_branch

    name = "definition of done"
    commands, errs = _verify.load_config(repo_root)
    if not commands and not errs:
        return Fact(name, "n/a", "no definition of done declared")

    blocked = verification_block(repo_root)
    if blocked:
        return Fact(name, "unmet", blocked)

    record = _verify.load_record(resolve_agent_dir(repo_root, resolve_branch(repo_root)))
    sha = record["sha"][:7] if record else ""
    return Fact(name, "met", f"passed at {sha}" if sha else "passed on this tree")


def fact_architecture_accepted(repo_root: Path) -> Fact:
    """Has a human ruled on what this branch decided? Owner: the record's `status`.

    Scoped to the branch and never to the projection. The repository-wide answer
    is a different question: a repo holding one un-accepted record would report
    every branch blocked forever, including branches that decided nothing, and a
    permanently false value is not a fact about the branch.

    `design/`, `scans/`, `views/` and `declarations/` drop out for free rather
    than by a second exclusion to maintain: `load_records` globs one level, which
    is already what keeps them out of `wfctl arch context`, so intersecting the
    touched slugs with the loaded ones excludes every subtree at once. Slugs
    cannot do that job alone — `records_on_this_branch` returns a bare stem, so a
    level-3 record and a top-level one of the same name look identical to it.

    Unmet is `proposed` or a status outside the closed set, not "anything but
    accepted". A branch that supersedes a record leaves it `superseded`, which a
    person decided; holding that branch would mean holding it forever.
    """
    from wfctl import _arch
    from wfctl._paths import records_on_this_branch

    name = "architecture accepted"
    arch = arch_root(repo_root)
    touched = set(records_on_this_branch(repo_root, arch))
    records = {r.slug: r for r in _arch.load_records(arch) if r.slug in touched}
    if not records:
        return Fact(name, "n/a", "no record on this branch")

    waiting = sorted(s for s, r in records.items() if r.status not in _RULED_ON)
    if waiting:
        # The status beside each slug, because "unmet" alone sends a reader to
        # accept a record that may instead be unreadable. `or "unreadable"` is
        # `parse_record`'s answer for a file it could not read, spelled out.
        named = ", ".join(f"{s} ({records[s].status or 'unreadable'})" for s in waiting)
        return Fact(name, "unmet", named)
    return Fact(name, "met", ", ".join(sorted(records)))


def fact_integration_authorized(granted: bool, source: str) -> Fact:
    """May this branch be integrated? Owner: a human's recorded grant.

    Reads the grant `build_report` resolved, already corrected for the trunk. The
    trunk is the one `n/a` here: there is no branch to integrate, so nothing was
    ever asked, and reporting it unmet would send a reader looking for a flag that
    the trunk refuses on purpose.

    Routed through `blocks` rather than mapping each source to a value directly.
    Three of the seven sources mean the answer could not be read, and what that
    means for a *promised* source is settled by
    `promised-evidence-blocks-on-silence`. Restating it here would be a fourth
    copy of a rule that exists because three copies had already drifted.
    """
    name = "integration authorized"
    if source == "trunk":
        return Fact(name, "n/a", "this is the trunk")

    verdict: Verdict = (
        "inconclusive" if source in _UNREADABLE_GRANT
        else "satisfied" if granted
        else "unsatisfied"
    )
    value: FactValue = "unmet" if blocks(verdict, "human") else "met"
    return Fact(name, value, _GRANT_DETAIL.get(source, _GRANT_DETAIL["unset"]))


def facts(
    ev: Evidence | None, repo_root: Path, granted: bool, source: str
) -> tuple[Fact, ...]:
    """The four, in the fixed order a consumer may index rather than search.

    The order runs from what the branch produced to who agreed it may land, which
    is the order #299 states them in. Fixed and never filtered: a consumer reading
    a short list learns nothing, where one reading no `facts` key at all learns
    that this wfctl predates the question — the distinction `notify` is
    present-and-false for.

    Four calls, four owners, and none of them is passed another's answer. That is
    the constraint `readiness-is-not-a-step-state` exists to hold, and this
    signature is where a future fifth fact would have to break it visibly.
    """
    return (
        fact_artifacts_written(ev),
        fact_definition_of_done(repo_root),
        fact_architecture_accepted(repo_root),
        fact_integration_authorized(granted, source),
    )


def build_evidence(spec_dir: Path, repo_root: Path) -> Evidence:
    """Read once, for all eight predicates.

    Public because the walk calls it, and because it is the only way to make an
    `Evidence` that reflects the disk — a caller assembling one by hand is
    writing a fixture, which is fine and is not this.

    Both file reads happen here rather than inside the predicates that want
    them. `tasks.md` is read by three steps and `spec.md` by two, and an
    implementing agent may be rewriting either while `status` runs — so two
    predicates reading the same file could disagree about it inside a single
    inference, and the payload would carry both answers.
    """
    tasks_md = spec_dir / "tasks.md"
    tasks_text = tasks_md.read_text() if _file_exists(tasks_md) else ""

    spec_md = spec_dir / "spec.md"
    spec_text = ""
    if _file_exists(spec_md):
        # Blank out fenced blocks and inline spans before matching, so a spec that
        # *documents* a marker or a heading doesn't read as having one. Both specify
        # and clarify match against the result.
        #
        # One helper for both artifacts (#308): a spec documenting a marker and a
        # tasks file documenting a task line are the same hazard.
        spec_text = _quoted_out(spec_md.read_text())

    plan_md = spec_dir / "plan.md"
    plan_text = _quoted_out(plan_md.read_text()) if _file_exists(plan_md) else ""

    done, total = _task_tally(tasks_text)
    return Evidence(
        spec_dir=spec_dir,
        repo_root=repo_root,
        spec_text=spec_text,
        plan_text=plan_text,
        # templates emit `[NEEDS CLARIFICATION: <question>]`, so the bracketed
        # literal `[NEEDS CLARIFICATION]` never matches a real marker — match the prefix
        has_markers="[NEEDS CLARIFICATION" in spec_text,
        tasks_text=tasks_text,
        tasks_open=_tasks_open(tasks_text, spec_dir),
        tasks_done=done,
        tasks_total=total,
    )


def brainstorm(ev: Evidence) -> Reading:
    """Whether the boundary question was put, and whether it was answered."""
    if _file_exists(ev.spec_dir / "design.md"):
        # A design document is the artifact; the boundary question is the step.
        # `design.md` on disk with no record for it means the step produced its
        # file and not its answer — the same shape `implement` reads when every
        # box is ticked and the definition of done has not passed.
        reason = design_block(ev.spec_dir, ev.repo_root)
        return Reading("in_progress" if reason else "done", reason)
    if _file_exists(ev.spec_dir / "spec.md"):
        # Passed by: the pipeline moved on without one, which `design-levels`
        # explicitly allows for a change that draws no new boundary.
        return Reading("skipped")
    # Nothing has happened here yet. Distinct from the branch above, and the two
    # need opposite advice — this is where the reader is sent, that is already
    # behind them. `spec.md` stands in for "a later step ran": every step after
    # this one cascades through specify, so nothing can be past brainstorm
    # without it.
    return Reading("pending")


def specify(ev: Evidence) -> Reading:
    """A spec exists, carries its mandatory sections, and has no marker left.

    Presence is asked of the file, not of `spec_text`: a spec that is one fenced
    block blanks to whitespace and is still a file someone wrote. Reading that as
    `pending` would cascade the whole pipeline and contradict `brainstorm`, which
    calls the same directory `skipped` from `_file_exists`.
    """
    if not _file_exists(ev.spec_dir / "spec.md"):
        return Reading("pending")
    if TEMPLATE_PLACEHOLDER in ev.spec_text:
        # Ahead of the marker check, and that ordering is the whole of what it
        # adds here. The spec template ships `[NEEDS CLARIFICATION` markers of
        # its own, so an untouched copy is `in_progress` either way — but as a
        # *marked* spec it routes to `/speckit.clarify`, which cannot write a
        # spec nobody has written. Reading it as unwritten routes it to the
        # command that can.
        #
        # A spec someone has actually written carries no `ACTION REQUIRED`, so a
        # real open marker still reaches the branch below.
        return Reading("in_progress", UNWRITTEN_TEMPLATE)
    if ev.has_markers:
        # Keeps priority over the section read: a marked spec is clarify's
        # business, and naming missing sections beside a marker would route the
        # reader to the wrong command. No reason, which is what
        # `_current_step_name` reads to know clarify can clear this one.
        return Reading("in_progress")
    reason = _missing_reason(_missing_sections(ev.spec_text, _REQUIRED_SPEC_SECTIONS))
    return Reading("in_progress" if reason else "done", reason)


def clarify(ev: Evidence) -> Reading:
    """The clarification scan ran, and left nothing standing.

    clarify has no file of its own — its artifact is the `## Clarifications`
    section /speckit.clarify writes into spec.md on every run, including a clean
    scan. Markers still standing mean the scan isn't finished, so both conditions
    must hold: without the marker check, a clarified-but-still-marked spec reads
    clarify ● and routes back to /speckit.specify, which rewrites spec.md from
    the template and destroys the section.

    ^##[ \\t]+Clarifications\\b — MULTILINE anchors ^ to any line, not the file.
    [ \\t] rather than \\s so a bare `##` line followed by a `Clarifications` line
    isn't a match. \\b rejects `## ClarificationsTODO` while allowing
    `## Clarifications (2026-08-04)`.
    """
    scanned = re.search(r"^##[ \t]+Clarifications\b", ev.spec_text, re.MULTILINE)
    if scanned and not ev.has_markers:
        return Reading("done")
    if ev.has_markers:
        # markers are clarify's actual job — no bypass, whatever else exists.
        # in_progress here also keeps _current_step_name's skip branch firing, so
        # a marked spec routes to clarify rather than back to specify.
        return Reading("in_progress")
    if _file_exists(ev.spec_dir / "plan.md"):
        # a spec that predates the gate — planning already passed through where
        # clarify now sits. skipped not done: the scan genuinely never ran, and
        # saying otherwise would hide that. Does not block, so an in-flight story
        # is not sent back to clarify a spec its implementation is already built on.
        #
        # The annotation is what stops it being silent (#309): `skipped` advances
        # the pipeline exactly as `done` does, and this branch passes the step on
        # the plan's existence rather than on any evidence a scan happened. In
        # `annotation` and not `reason` — a `skipped` step is never
        # `_current_step_name`, so a reason here would reach no consumer, and it
        # would widen what that field means in exchange for nothing observable.
        #
        # Existence, deliberately, and not the section read `plan` now performs.
        # The question is whether planning already passed through here, which a
        # thin plan still answers yes; tightening it would send an in-flight spec
        # back to re-clarify a document its plan is already built on.
        return Reading("skipped", annotation=CLARIFY_UNSCANNED)
    return Reading("in_progress")


def plan(ev: Evidence) -> Reading:
    """A plan exists and carries the sections a plan carries."""
    if not _file_exists(ev.spec_dir / "plan.md"):
        return Reading("pending")
    if TEMPLATE_PLACEHOLDER in ev.plan_text:
        # Ordered before the section read on purpose: `setup-plan.sh` runs
        # `cp plan-template.md plan.md`, so the document this step most often
        # meets carries every required heading and no content. Structure alone
        # has nothing to say about it and would report `done`.
        return Reading("in_progress", UNWRITTEN_TEMPLATE)
    reason = _missing_reason(_missing_sections(ev.plan_text, _REQUIRED_PLAN_SECTIONS))
    return Reading("in_progress" if reason else "done", reason)


def tasks(ev: Evidence) -> Reading:
    """A task list exists and holds at least one task (#308).

    Never reads what a task *says*, nor whether it is ticked — a file of open
    boxes finishes this step. What it stopped accepting is a file with no box at
    all, which cleared both this step and `implement` while proving nothing.
    """
    if not ev.tasks_text:
        return Reading("pending")
    if ev.tasks_total:
        return Reading("done")
    if _file_exists(ev.spec_dir / "checklists" / "implement-complete.md"):
        # A story declared implemented over a file with no task in it. `skipped`
        # rather than `done`, for clarify's reason: the step genuinely produced
        # nothing, and `done` would hide that. It stops blocking for decompose's
        # reason: `/speckit.tasks` rewrites this file from a template, so sending
        # a shipped story there is a pipeline with no route to `/end-session` (#8).
        #
        # Not a second escape from #308. The sentinel is written by hand at the
        # end of implementation, which is the declaration that was missing when a
        # bare file cleared both steps unattended.
        return Reading("skipped")
    # The step wrote its artifact and put no task in it, which is the same shape
    # `brainstorm` reads when `design.md` exists with no record behind it: a file
    # produced, an answer not.
    return Reading("in_progress", _TASKS_EMPTY_REASON)


def analyze(ev: Evidence) -> Reading:
    """An analysis report exists."""
    report = ev.spec_dir / "checklists" / "analysis-report.md"
    return Reading("done" if _file_exists(report) else "pending")


def decompose(ev: Evidence) -> Reading:
    """A delivery plan exists, and every issue row it groups names a key.

    Two questions, deliberately not one. `blocks` answers *is an unkeyed row a
    finding*; `tasks_open` answers *does the finding stand in the way*. Folding
    the second into the first would change behaviour: past the point where the
    work is closed the reader is being sent to `/speckit.decompose`, which does
    not backfill a table, for a story that has already shipped — and no route to
    `/end-session` exists while a step blocks. The annotation still says what is
    missing; it just stops standing in the way. Clarify's `skipped` arm declines
    the same trap in the same terms.

    `ambient` is the source because neither inconclusive reading has an owner. A
    repo that declared no tracker promised no keys and can never gain any, and a
    delivery plan written before the Issue Grouping Map existed never promised
    one — so reading either as a missing answer would strand the pipeline with no
    action that unblocks it.
    """
    delivery_md = ev.spec_dir / "delivery.md"
    if not _file_exists(delivery_md):
        if ev.tasks_text and not ev.tasks_open:
            return Reading("skipped")
        return Reading("pending")

    # Writing the plan is not the whole step — `speckit-delivery-plan`'s own
    # checklist requires the issues it groups to exist. Read from the file's text
    # rather than from the tracker: `status` runs on every session start, and a
    # pipeline read that costs a network round-trip is one nobody makes.
    #
    # No tracker means no key to wait for. That repo said so deliberately
    # (`"tracker": null`), nothing there creates an issue, and gating on a key it
    # can never gain would strand the pipeline at decompose for the life of the repo.
    pattern = _tracker.configured_key_pattern(ev.repo_root)
    unkeyed = _unkeyed_issues(delivery_md.read_text(), pattern) if pattern else None
    verdict: Verdict = (
        "inconclusive" if unkeyed is None else "unsatisfied" if unkeyed else "satisfied"
    )
    if not blocks(verdict, "ambient"):
        return Reading("done")

    # What was read, not what it implies. The rows are the whole evidence:
    # "issues not created" is a claim about the tracker, and it is the wrong one
    # for a plan whose issues exist and whose table was never filled back in.
    assert unkeyed is not None  # `unsatisfied` is the only arm that blocks here
    plural = "" if unkeyed == 1 else "s"
    reason = f"{unkeyed} issue row{plural} without a key"
    return Reading("in_progress" if ev.tasks_open else "done", reason)


def implement(ev: Evidence) -> Reading:
    """The tasks read closed, and a repo-declared verification passed on this tree.

    One owner for a verdict that was composed at two sites — this arm and the
    routing branch in `next_step_content` — and kept in agreement by convention
    alone (#265). A new blocking condition applied at one and not the other
    reproduces #262 one level up: the step table reports one thing and the
    routing path executes another, and `speckit-orchestrate` acts on the routing
    path.
    """
    if not ev.tasks_text:
        return Reading("pending")

    # No tally where there is nothing to tally. `0/0 done` is how #308 was
    # reported, and beside any state it reads as a count of work rather than as
    # the absence of anything to count.
    tally = f"{ev.tasks_done}/{ev.tasks_total} done" if ev.tasks_total else None

    if ev.tasks_open:
        return Reading("in_progress", None, tally)
    # Tasks read complete. Before #69 that was the whole check, and both routes
    # to it are written by the agent doing the work. A configured definition of
    # done gets the last word.
    blocked = verification_block(ev.repo_root)
    if blocked:
        annotation = f"{tally}  {blocked}" if tally else blocked
        return Reading("in_progress", blocked, annotation)
    return Reading("done", None, tally)
