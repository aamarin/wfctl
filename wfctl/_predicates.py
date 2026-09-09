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

from wfctl import _tracker
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

# The design step's annotation when the boundary question went unanswered. Short
# because it sits inline in the step table; the two remedies are spelled out by
# `_pipeline.DESIGN_BLOCK_HELP`, which is formatted with a per-repo location.
# Here rather than there because it is what this module concludes; the help is
# how a view renders that conclusion.
DESIGN_BLOCK_REASON = "no architecture record for this change"


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
    tasks_text: str
    tasks_open: bool


def _file_exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def _has_open_checkboxes(text: str) -> bool:
    return bool(re.search(r"\[ \]", text))


def _tasks_open(tasks_text: str, spec_dir: Path) -> bool:
    """Whether the tasks are still open, by the two routes `implement` reads as
    finished: every box ticked, or the sentinel that says so over one left open.

    Only the tasks. A caller asking whether *implementation* is finished wants
    this and `verification_block` — a definition of done gets the last word over
    both routes here (#69), and a caller that negates this alone has skipped it.

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
    return _has_open_checkboxes(tasks_text) and not _file_exists(
        spec_dir / "checklists" / "implement-complete.md"
    )


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
    the issues are created, because creating them is notifying and waits for
    a human. An unkeyed row is therefore a legitimate mid-decompose state; what
    was wrong was reading it as a finished one (#8).

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
#   specify     1 + 3. `spec.md` is non-empty and carries no marker. Never 2: its
#               sections are not read.
#   clarify     2 + 3. A `## Clarifications` heading, and no marker left; nothing
#               under the heading is read. `skipped` where `plan.md` exists and the
#               heading does not.
#   plan        1. `plan.md` is non-empty.
#   tasks       1. `tasks.md` is non-empty — not that it holds a single task.
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
# `decompose` as `ambient`. The other five read a file that is there or is not.
# `decompose` was the exception until #314: it resolved two of its own readings —
# no tracker configured, and a plan carrying no map or no rows — without reaching
# the rule. Both still proceed; they now proceed because `blocks` says so.
#
# Where a rung sits below its flag, that is filed, not fixed. #308 is `tasks` and
# `implement` cleared by a file holding no task; #309 is `specify` and `plan`
# automatic on a file's mere existence; `decompose` is argued on #240, the issue that
# would spend it. `brainstorm` is automatic over a weak rung as well and is not
# filed: #283 settled that flag on reversibility, and a blocked step is never
# automatic whatever the table says (`next_step_content`). Nothing pins these lines
# to the predicates they describe — re-read the function before trusting one.


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
        # ```.*?``` is non-greedy under DOTALL so two separate fences don't merge
        # into one match spanning the prose between them; `[^`\n]+` excludes newline
        # so an unpaired backtick can't swallow the rest of the file.
        spec_text = re.sub(r"```.*?```|`[^`\n]+`", "", spec_md.read_text(), flags=re.DOTALL)

    return Evidence(
        spec_dir=spec_dir,
        repo_root=repo_root,
        spec_text=spec_text,
        # templates emit `[NEEDS CLARIFICATION: <question>]`, so the bracketed
        # literal `[NEEDS CLARIFICATION]` never matches a real marker — match the prefix
        has_markers="[NEEDS CLARIFICATION" in spec_text,
        tasks_text=tasks_text,
        tasks_open=_tasks_open(tasks_text, spec_dir),
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
    """A spec exists, and carries no unresolved marker."""
    if not _file_exists(ev.spec_dir / "spec.md"):
        return Reading("pending")
    return Reading("in_progress" if ev.has_markers else "done")


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
        return Reading("skipped")
    return Reading("in_progress")


def plan(ev: Evidence) -> Reading:
    """A plan exists."""
    return Reading("done" if _file_exists(ev.spec_dir / "plan.md") else "pending")


def tasks(ev: Evidence) -> Reading:
    """A task list exists — not that it holds a single task (#308)."""
    return Reading("done" if ev.tasks_text else "pending")


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

    # The tally, which is why this step's annotation is not its reason. Counted
    # from the same text the state is read from, so the two cannot disagree
    # about a file an implementing agent is rewriting.
    done = len(re.findall(r"\[x\]", ev.tasks_text, re.IGNORECASE))
    total = done + len(re.findall(r"\[ \]", ev.tasks_text))
    tally = f"{done}/{total} done"

    if ev.tasks_open:
        return Reading("in_progress", None, tally)
    # Tasks read complete. Before #69 that was the whole check, and both routes
    # to it are written by the agent doing the work. A configured definition of
    # done gets the last word.
    blocked = verification_block(ev.repo_root)
    if blocked:
        return Reading("in_progress", blocked, f"{tally}  {blocked}")
    return Reading("done", None, tally)
