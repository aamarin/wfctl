"""Pipeline step inference and display, and the commands wfctl names.

The command inventory lives here rather than at its call sites so one check can
reach all of it: a slash command that no longer ships is indistinguishable from
one that does until someone runs it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from wfctl import _tracker

# What reading one evidence source concluded. Three values rather than a bool
# because "the evidence says proceed" and "there was no evidence" are the two a
# bool collapses, and the rule below is the one place that distinction is spent.
Verdict = Literal["satisfied", "unsatisfied", "inconclusive"]

# Sources someone undertook to produce. The repo declares its commands, the
# process accepts its records, a person records an approval — so silence from
# one of these is a missing answer, not the absence of a question.
_PROMISED = frozenset({"repo-declared", "accepted-record", "human"})


def blocks(verdict: Verdict, source: str) -> bool:
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


# step → (slash command that advances it, whether speckit-orchestrate may proceed
# without pausing). The second value is a name rather than a Boolean because a
# flag flip is a reviewable change and `grep _AUTOMATIC` finds every step that
# takes one, while `grep True` finds nothing (#240, #283). It is the same two
# states — the wire format `next_step_content` returns is still a bool.
# One table rather than three keyed by the same names: a step
# defined here carries both values or it does not parse. Split across separate
# tables, omitting the command was silent and severe — `next_step_content`
# returned "", which `next_cmd` treats as a finished pipeline, so a step with no
# command announced "story complete" with half the pipeline unrun.
Continuation = Literal["automatic", "review_required"]
_AUTOMATIC: Continuation = "automatic"
_REVIEW_REQUIRED: Continuation = "review_required"

_STEPS: dict[str, tuple[str, Continuation]] = {
    "brainstorm": ("/speckit.brainstorm", _REVIEW_REQUIRED),
    "specify":    ("/speckit.specify",    _AUTOMATIC),
    "clarify":    ("/speckit.clarify",    _REVIEW_REQUIRED),
    "plan":       ("/speckit.plan",       _AUTOMATIC),
    "tasks":      ("/speckit.tasks",      _AUTOMATIC),
    "analyze":    ("/speckit.analyze",    _REVIEW_REQUIRED),
    "decompose":  ("/speckit.decompose",  _REVIEW_REQUIRED),
    "implement":  ("/speckit.implement",  _AUTOMATIC),
}

# Insertion order is pipeline order — derived, so it cannot disagree with the table.
_STEP_NAMES = list(_STEPS)

# Commands wfctl names that no step advances to. `/end-session` ships in
# `agents/commands/` like any step command and carries the same drift risk, but a
# check that walks `_STEPS` cannot see it — and it is the last instruction a
# session receives, at the moment the pipeline reports complete. #23's failure one
# step later in the flow. Kept here so the inventory of commands wfctl emits is in
# one place; `cli` builds its completion messages from it rather than inlining the
# name three times.
_END_SESSION = "/end-session"
_LOOSE_COMMANDS = (_END_SESSION,)

# What `cli` prints once no step remains. Two spellings of one sentence: the file
# form is read by an agent, the console form marks the command up for a human.
# Public because `cli` imports them — the data above stays private.
STORY_COMPLETE_FILE = f"Story complete. Open PR or run {_END_SESSION}.\n"
STORY_COMPLETE_CONSOLE = f"Story complete — open PR or run `{_END_SESSION}`."


# The design step's annotation when the boundary question went unanswered. Both
# escapes are named because both are legitimate: `design-levels` excludes changes
# that draw no new state, and a check with only one exit turns those into records
# that say nothing.
DESIGN_BLOCK_REASON = "no architecture record — write one, or run `wfctl arch none`"


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
    decides from one read. `_infer_steps` reads `tasks.md` for its own tally,
    and a second read inside here let the tally and this answer come from two
    versions of a file an implementing agent may be rewriting.
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
    the issues are created, because creating them is outward-facing and waits for
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
    if record["inconclusive"]:
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


def _implement_verdict(
    tasks_text: str, spec_dir: Path, repo_root: Path
) -> tuple[str, str | None]:
    """The implement step's state, and why it is not `done`.

    One owner for a verdict that was composed at two sites — the implement arm
    of `_infer_steps` and the routing branch in `next_step_content` — and kept
    in agreement by convention alone (#265). A new blocking condition applied at
    one and not the other reproduces #262 one level up: the step table reports
    one thing and the routing path executes another, and `speckit-orchestrate`
    acts on the routing path.

    Returns the reason rather than a bool for the same reason `verification_block`
    does: the caller renders it, and a caller that only needed to know *whether*
    it is blocked reads the reason as truthy.
    """
    if not tasks_text:
        return "pending", None
    if _tasks_open(tasks_text, spec_dir):
        return "in_progress", None
    # Tasks read complete. Before #69 that was the whole check, and both routes
    # to it are written by the agent doing the work. A configured definition of
    # done gets the last word.
    blocked = verification_block(repo_root)
    return ("in_progress", blocked) if blocked else ("done", None)


@dataclass
class _PipelineStep:
    name: str
    state: str
    annotation: str | None
    # The unrendered half of `annotation`, for the routing read. `implement`'s
    # annotation prefixes a task tally, so the reason cannot be recovered from it.
    reason: str | None = None


def _infer_steps(spec_dir: Path | None, repo_root: Path) -> list[_PipelineStep]:
    """Internal: return steps carrying `done` / `in_progress` / `pending` / `skipped`.

    A name rather than a glyph — not because the glyphs are unreadable. Agents
    decode `● ▶ ○ –` fine, and an experiment run against this docstring's earlier
    claim found three doing so with no legend and no errors. They decode it by
    convention they bring, though, not by a map this file publishes: a fourth
    reader handed one off-map character assigned a state anyway and called itself
    confident. A legible rendering nothing can verify is still a contract, and it
    is one whose terms live outside the repo.

    So the state name is what inference stores, and `cli` maps it to a symbol at
    the moment of printing. That keeps the glyphs restylable — changing them is a
    change to a drawing, not to what the next session believes.

    `repo_root` is what the implement arm reads the definition of done and the
    live git state from. It was carried unused for a while after the design doc
    moved into the spec dir; #69 gave it a job again.
    """
    if spec_dir is None:
        return [_PipelineStep(name, "pending", None) for name in _STEP_NAMES]

    tasks_md = spec_dir / "tasks.md"
    tasks_text = tasks_md.read_text() if _file_exists(tasks_md) else ""

    tasks_open = _tasks_open(tasks_text, spec_dir)

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

    # templates emit `[NEEDS CLARIFICATION: <question>]`, so the bracketed literal
    # `[NEEDS CLARIFICATION]` never matches a real marker — match the prefix
    has_markers = "[NEEDS CLARIFICATION" in spec_text

    steps: list[_PipelineStep] = []
    cascade = False
    implement_reason: str | None = None
    decompose_reason: str | None = None
    design_reason: str | None = None

    for name in _STEP_NAMES:
        if cascade:
            steps.append(_PipelineStep(name, "pending", None))
            continue

        if name == "brainstorm":
            if _file_exists(spec_dir / "design.md"):
                # A design document is the artifact; the boundary question is the
                # step. `design.md` on disk with no record for it means the step
                # produced its file and not its answer — the same shape
                # `implement` reads when every box is ticked and the definition
                # of done has not passed.
                design_reason = design_block(spec_dir, repo_root)
                state = "in_progress" if design_reason else "done"
            elif _file_exists(spec_md):
                # Passed by: the pipeline moved on without one, which
                # `design-levels` explicitly allows for a change that draws no
                # new boundary.
                state = "skipped"
            else:
                # Nothing has happened here yet. Distinct from the branch above,
                # and the two need opposite advice — this is where the reader is
                # sent, that is already behind them. `spec.md` stands in for
                # "a later step ran": every step after this one cascades through
                # specify, so nothing can be past brainstorm without it.
                state = "pending"

        elif name == "specify":
            if _file_exists(spec_md):
                state = "in_progress" if has_markers else "done"
            else:
                state = "pending"

        elif name == "clarify":
            # clarify has no file of its own — its artifact is the `## Clarifications`
            # section /speckit.clarify writes into spec.md on every run, including a
            # clean scan. Markers still standing mean the scan isn't finished, so both
            # conditions must hold: without the marker check, a clarified-but-still-
            # marked spec reads clarify ● and routes back to /speckit.specify, which
            # rewrites spec.md from the template and destroys the section.
            #
            # ^##[ \t]+Clarifications\b — MULTILINE anchors ^ to any line, not the
            # file. [ \t] rather than \s so a bare `##` line followed by a
            # `Clarifications` line isn't a match. \b rejects `## ClarificationsTODO`
            # while allowing `## Clarifications (2026-08-04)`.
            scanned = re.search(r"^##[ \t]+Clarifications\b", spec_text, re.MULTILINE)
            if scanned and not has_markers:
                state = "done"
            elif has_markers:
                # markers are clarify's actual job — no bypass, whatever else exists.
                # in_progress here also keeps _current_step_name's skip branch firing,
                # so a marked spec routes to clarify rather than back to specify.
                state = "in_progress"
            elif _file_exists(spec_dir / "plan.md"):
                # a spec that predates the gate — planning already passed through where
                # clarify now sits. skipped not done: the scan genuinely never ran, and
                # saying otherwise would hide that. Does not block, so an in-flight story
                # is not sent back to clarify a spec its implementation is already built on.
                state = "skipped"
            else:
                state = "in_progress"

        elif name == "plan":
            state = "done" if _file_exists(spec_dir / "plan.md") else "pending"

        elif name == "tasks":
            state = "done" if tasks_text else "pending"

        elif name == "analyze":
            state = (
                "done"
                if _file_exists(spec_dir / "checklists" / "analysis-report.md")
                else "pending"
            )

        elif name == "decompose":
            delivery_md = spec_dir / "delivery.md"
            if _file_exists(delivery_md):
                state = "done"
                # Writing the plan is not the whole step —
                # `speckit-delivery-plan`'s own checklist requires the issues it
                # groups to exist. Read from the file's text rather than from the
                # tracker: `status` runs on every session start, and a pipeline
                # read that costs a network round-trip is one nobody makes.
                #
                # No tracker means no key to wait for. That repo said so
                # deliberately (`"tracker": null`), nothing there creates an
                # issue, and gating on a key it can never gain would strand the
                # pipeline at decompose for the life of the repo.
                pattern = _tracker.configured_key_pattern(repo_root)
                unkeyed = (
                    _unkeyed_issues(delivery_md.read_text(), pattern) if pattern else None
                )
                if unkeyed:
                    # What was read, not what it implies. The rows are the whole
                    # evidence: "issues not created" is a claim about the tracker,
                    # and it is the wrong one for a plan whose issues exist and
                    # whose table was never filled back in.
                    plural = "" if unkeyed == 1 else "s"
                    decompose_reason = f"{unkeyed} issue row{plural} without a key"
                    # Blocking only while the work is still open. Past that the
                    # reader is being sent to `/speckit.decompose`, which does not
                    # backfill a table, for a story that has already shipped — and
                    # no route to `/end-session` exists while a step blocks. The
                    # annotation still says what is missing; it just stops
                    # standing in the way. Clarify's `skipped` arm above declines
                    # the same trap in the same terms.
                    if tasks_open:
                        state = "in_progress"
            elif tasks_text and not tasks_open:
                state = "skipped"
            else:
                state = "pending"

        elif name == "implement":
            state, implement_reason = _implement_verdict(tasks_text, spec_dir, repo_root)

        else:
            state = "pending"

        annotation: str | None = None
        if name == "brainstorm":
            annotation = design_reason
        elif name == "decompose":
            annotation = decompose_reason
        elif name == "implement" and tasks_text:
            done = len(re.findall(r"\[x\]", tasks_text, re.IGNORECASE))
            total = done + len(re.findall(r"\[ \]", tasks_text))
            annotation = f"{done}/{total} done"
            if implement_reason:
                annotation = f"{annotation}  {implement_reason}"

        reason = {"implement": implement_reason, "brainstorm": design_reason}.get(name)
        steps.append(_PipelineStep(name, state, annotation, reason))

        if state == "pending":
            cascade = True

    return steps


def design_block(spec_dir: Path | None, repo_root: Path) -> str | None:
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
    if spec_dir is None or not _file_exists(spec_dir / "design.md"):
        return None
    if _file_exists(spec_dir / "spec.md"):
        # Past the boundary. "Advance past the design step" is one transition,
        # and a gate that stayed up through plan, tasks and implement would
        # refuse work that already answered by moving on. `spec.md` is what
        # "a later step ran" looks like — the same stand-in the brainstorm arm
        # of `_infer_steps` uses to tell `skipped` from `pending`.
        return None

    from wfctl._paths import arch_root, touched_on_this_branch

    arch = arch_root(repo_root)
    # Three states in, three states out. `touched_on_this_branch` already returns
    # `None` for "git cannot answer" and says in its own docstring why — the old
    # call site spent that third state on `is False` one line after computing it.
    touched = touched_on_this_branch(repo_root, arch, exclude=arch / "design")
    verdict: Verdict = (
        "inconclusive" if touched is None else "satisfied" if touched else "unsatisfied"
    )
    return DESIGN_BLOCK_REASON if blocks(verdict, "ambient") else None


def _current_step_name(steps: list[_PipelineStep]) -> str:
    """Return the first step that still blocks; 'complete' if none does.

    `done` and `skipped` are the two states that do not block — one ran, the
    other was passed by, and neither is somewhere to send a reader back to.

    Markers in spec.md leave specify `in_progress`, but clarify is the step that
    resolves them — so skip specify when clarify is also unfinished.
    """
    step_map = {s.name: s.state for s in steps}
    for s in steps:
        if s.state not in ("in_progress", "pending"):
            continue
        if (
            s.name == "specify"
            and s.state == "in_progress"
            and step_map.get("clarify") == "in_progress"
        ):
            continue
        return s.name
    return "complete"


def infer_pipeline(spec_dir: Path | None, repo_root: Path) -> list[tuple[str, bool]]:
    """Return [(step_name, is_done)] ordered list."""
    steps = _infer_steps(spec_dir, repo_root)
    return [(s.name, s.state in ("done", "skipped")) for s in steps]


# Distinguishes "the caller already has the verdict" from "the verdict is None",
# which `None` alone cannot: a caller holding a passing verdict passes None.
_RECOMPUTE = object()


def next_step_content(
    step: str,
    repo_root: Path | None = None,
    spec_dir: Path | None = None,
    implement_blocked: object = _RECOMPUTE,
) -> tuple[str, bool]:
    """Return (command, auto_flag) for the given pipeline step.

    An undefined step yields ("", False) rather than raising: `_current_step_name`
    returns "complete" for a story with nothing left, and the caller reads the
    empty command as the finished pipeline it is.

    `repo_root` and `spec_dir` are optional so the ~30 existing call sites keep
    working. Given both, an `implement` step whose tasks are all ticked but whose
    definition of done has not passed routes to `wfctl verify` instead of
    `/speckit.implement` — re-running implement there does nothing, because there
    is no task left to do. Tasks still open route to the step command as before:
    the work itself is what remains.
    """
    if step == "implement" and repo_root is not None and spec_dir is not None:
        if implement_blocked is _RECOMPUTE:
            tasks_md = spec_dir / "tasks.md"
            tasks_text = tasks_md.read_text() if _file_exists(tasks_md) else ""
            _, implement_blocked = _implement_verdict(tasks_text, spec_dir, repo_root)
        if implement_blocked:
            return "wfctl verify", False
    command, continuation = _STEPS.get(step, ("", _REVIEW_REQUIRED))
    return command, continuation == _AUTOMATIC


@dataclass(frozen=True)
class PipelineReport:
    """Where a feature stands — everything a caller needs from one inference.

    Replaces the pair of reads a caller used to make: the step table from
    `steps_display`, and the next command from `next_step_content` at the call
    site. Two reads of the same artifacts can disagree if anything changes
    between them, and the console and the serialized view would then be two
    inference paths rather than two renderings.

    `steps` are plain dicts, not `_PipelineStep`: this object is serialized as
    it stands, and a dataclass reaching `json.dumps` would need a second shape
    defined beside it to say what a step looks like on the wire.
    """

    steps: list[dict]
    current: str | None
    next_command: str | None
    auto: bool | None
    session_started: bool
    # The one field here nothing infers — a human's answer to "may the design
    # gates be answered without me", read back rather than recomputed. Defaulted
    # because it is the only field whose absence has a correct value: a report
    # built without it is a report about a feature nobody granted anything to.
    #
    # Outside the pairing below on purpose. `auto` is None at story complete
    # because there is no step left to run; the mode is still true of a finished
    # story, which ran under one.
    auto_approve: bool = False

    def __post_init__(self) -> None:
        # The failure `_STEPS` was collapsed into one table to prevent: a step
        # that is current with no command to advance it announced "story
        # complete" with half the pipeline unrun. Unconstructible rather than
        # merely tested, so no future branch can produce one. `auto` joins the
        # pair because it is the same fact seen from one more angle: there is a
        # step to run, or there is not.
        paired = (self.current, self.next_command, self.auto)
        if any(v is None for v in paired) and not all(v is None for v in paired):
            raise ValueError(
                f"current={self.current!r}, next_command={self.next_command!r} and "
                f"auto={self.auto!r} must be None together"
            )


def build_report(spec_dir: Path | None, repo_root: Path, agent_dir: Path) -> PipelineReport:
    """The one inference. Every view of pipeline state is a rendering of this."""
    # Aliased: the report field and the reader are the same word, and
    # `auto_approve=auto_approve(agent_dir)` two lines down reads as a
    # self-reference rather than a call.
    from wfctl._session import auto_approve as read_auto_approve
    from wfctl._session import session_started

    raw = _infer_steps(spec_dir, repo_root)
    name = _current_step_name(raw)
    # `_infer_steps` has already asked; `verification_block` reads the config,
    # loads a record and shells out to git, and `status` runs on every session
    # start. Recomputing it here is the one call this seam was meant to collapse.
    blocked = next((s.reason for s in raw if s.name == "implement"), None)
    command, auto = next_step_content(name, repo_root, spec_dir, blocked)
    return PipelineReport(
        steps=[
            {
                "name": s.name,
                "state": s.state,
                "annotation": s.annotation,
                "is_current": s.name == name,
            }
            for s in raw
        ],
        current=name if command else None,
        next_command=command or None,
        auto=auto if command else None,
        session_started=session_started(agent_dir),
        auto_approve=read_auto_approve(agent_dir),
    )
