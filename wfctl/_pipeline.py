"""The step table, the walk over it, and the commands wfctl names.

Two jobs, not the three this said before #314. What each step *reads* is
`_predicates`; what remains here is the order the steps come in, the cascade,
and the one payload every view renders.

Inference and display stay together deliberately, and that is the half of the
old docstring's third job that did not move. `pipeline-state-is-one-payload`
forbids a view computing a fact of its own, so splitting the payload's shape
from the inference that fills it would put the boundary in the one place the
record rules out.

The command inventory lives here rather than at its call sites so one check can
reach all of it: a slash command that no longer ships is indistinguishable from
one that does until someone runs it.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NamedTuple

from wfctl import _predicates
from wfctl._paths import arch_root, is_in_tree
from wfctl._predicates import DESIGN_BLOCK_REASON, Predicate, State, build_evidence

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


class Step(NamedTuple):
    """One row of the table: how to advance the step, and how to read it.

    A `NamedTuple` rather than a bare tuple so the three fields have names, and
    rather than a frozen dataclass because it needs no import and no `__init__`
    to write. Tuple compatibility came free and is now unused: this change swept
    all three positional unpacks, so a two-element unpack against a three-field
    row raises `ValueError` rather than quietly taking the first two.

    `predicate` is a callable and not a name to look up. A `gate: str` field
    would need a second table mapping names to functions, which is the registry
    #100 ruled out, and it would cost `grep`: written this way, searching for a
    predicate finds its definition and its row here.
    """

    command: str
    continuation: Continuation
    predicate: Predicate


_STEPS: dict[str, Step] = {
    "brainstorm": Step("/speckit.brainstorm", _AUTOMATIC,       _predicates.brainstorm),
    "specify":    Step("/speckit.specify",    _AUTOMATIC,       _predicates.specify),
    "clarify":    Step("/speckit.clarify",    _REVIEW_REQUIRED, _predicates.clarify),
    "plan":       Step("/speckit.plan",       _AUTOMATIC,       _predicates.plan),
    "tasks":      Step("/speckit.tasks",      _AUTOMATIC,       _predicates.tasks),
    "analyze":    Step("/speckit.analyze",    _REVIEW_REQUIRED, _predicates.analyze),
    "decompose":  Step("/speckit.decompose",  _REVIEW_REQUIRED, _predicates.decompose),
    "implement":  Step("/speckit.implement",  _AUTOMATIC,       _predicates.implement),
}

# Insertion order is pipeline order — derived, so it cannot disagree with the table.
_STEP_NAMES = list(_STEPS)

# Two conditions hold over every predicate, and both are facts about this walk
# rather than about any one of them. `cascade` at the foot of the loop forces every
# step after the first `pending` one to `pending` without calling its predicate — so
# a satisfied predicate is necessary and never sufficient. And `skipped` advances the
# pipeline exactly as `done` does (`infer_pipeline`), so a predicate reaching it
# passes its step on none of the evidence it reads.
#
# What each predicate actually proves is documented beside the predicates, in
# `_predicates.py`. It moved there with them for the reason it gave for being here:
# `knowledge-placement` puts a fact about one file in that file, and it is a fact
# about the arms — which are no longer below this line.

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


def next_step_file(command: str, auto: bool, blocked: str | None, remedy: str | None) -> str:
    """What `next` and `resume` write to `next-step.md`.

    Here for the reason `STORY_COMPLETE_FILE` is: two commands write this file,
    and the format was composed at both. Every field added to it since has had
    to be added twice — `why:` once, `how:` again — and the second writer is
    where one of them will eventually be forgotten.

    `how:` is keyed rather than appended. Unlabelled, the remedy's last line
    sits directly above the closing imperative and becomes its nearest
    antecedent, so "run this command" reads as pointing at a remedy rather than
    at `Next step:` above it.
    """
    why = f"why: {blocked}\n" if blocked else ""
    how = f"how:\n{remedy}\n" if remedy else ""
    return (
        f"Next step: {command}\nauto: {'true' if auto else 'false'}\n"
        f"{why}{how}Run this command to continue.\n"
    )


# Both escapes, because both are legitimate answers: `design-levels` excludes
# changes that draw no new state, and a check with only one exit turns those into
# records that say nothing.
#
# Rendered under the step table rather than folded into the annotation. A path is
# the one part of this that cannot be a constant — it is resolved per repo — so
# the payload carries the formatted block and each view renders it, the console
# escaping on the way out because `[wip]` is a legal directory name.
#
# Neither branch names a string that can be pasted back to fake the answer. The
# record side describes a file rather than printing `<slug>.md`: the gate reads
# `git status`, which counts an *untracked* file, so a reader following that path
# literally cleared the gate with no command and no commit — the same defect the
# `<why>` guard on the other branch was added for, on the half that had no guard.
DESIGN_BLOCK_HELP = (
    "  Either record the boundary this change draws — one file under:\n"
    "      {location}/\n"
    "  or state that it draws none:\n"
    '      wfctl arch none --reason "<why>"'
)

# What `next` and `resume` name for a blocked design step: the step itself.
#
# Not a remedy command. The two answers are "write a record" and "declare there
# is no boundary", and only the second is a command — so any single string here
# names one of them and hides the other. Naming the declaration is the worse
# half of that: it is the cheaper answer, it would arrive with a `<why>`
# placeholder a reader can paste back, and `status --json` returns before the
# other remedy is rendered, so an agent would see one option and it would be the
# one that closes the question without answering it.
#
# The step command names neither and reaches both. `implement` differs because
# its evidence has exactly one producer — `wfctl verify` — so there is nothing
# for a second option to be.


@dataclass
class _PipelineStep:
    name: str
    state: State
    annotation: str | None
    # The unrendered half of `annotation`, for the routing read. `implement`'s
    # annotation prefixes a task tally, so the reason cannot be recovered from it.
    reason: str | None = None
    # How to clear the block, where the reason alone does not say. Part of
    # inference rather than of each view: the string names a per-repo path, and
    # resolving it in a view is what left `status --json` carrying the reason
    # without the fix.
    remedy: str | None = None


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

    ev = build_evidence(spec_dir, repo_root)
    steps: list[_PipelineStep] = []
    cascade = False

    for name, step in _STEPS.items():
        if cascade:
            steps.append(_PipelineStep(name, "pending", None))
            continue

        reading = step.predicate(ev)
        step_state = _PipelineStep(
            name, reading.state, reading.renders(), reading.reason
        )
        step_state.remedy = _design_remedy(step_state, repo_root)
        steps.append(step_state)

        if reading.state == "pending":
            cascade = True

    return steps


def arch_location(root: Path, repo_root: Path) -> str:
    """How a path under the arch root is named in output.

    Repo-relative in-tree, absolute outside, and never with a trailing
    separator — it renders files as well as directories, so a caller that means
    a directory writes the slash itself.

    A record set lives beside the code by default, and printing the absolute
    path for it is noise that differs per machine. Out-of-tree has no relative
    form worth showing, so it stays absolute.

    Unescaped, and here rather than in `cli`, because the remedy it names is
    payload now: `status --json` would otherwise carry rich's `\\[wip]` to a
    consumer that has no rich. Escaping is the console's, applied where the
    string is printed — `cli._arch_location` is that wrapper, and every console
    caller still reaches the escaped form through it.
    """
    if not is_in_tree(root, repo_root):
        return str(root)
    rel = root.resolve().relative_to(repo_root.resolve())
    # `Path(".")` when the root *is* the repo root: "./" reads as a stray typo
    # next to a slug, so the absolute path is the clearer name for that case.
    return str(root) if rel == Path(".") else str(rel)


def _design_remedy(step: _PipelineStep, repo_root: Path) -> str | None:
    """The two ways to clear the design block, with this repo's path resolved.

    In the payload rather than in the console branch that used to build it. The
    reason alone says a record is missing and not where to put one, so a JSON
    consumer — `speckit-orchestrate` is the one that acts — had to resolve the
    arch root itself to render what `status` renders, which is the second
    inference path `pipeline-state-is-one-payload` exists to forbid.

    Keyed on the reason rather than on the step name: this is a rendering of a
    fact inference already established, and the step that carries the design
    block is `_infer_steps`' business, not this function's.
    """
    if step.reason != DESIGN_BLOCK_REASON:
        return None
    return DESIGN_BLOCK_HELP.format(location=arch_location(arch_root(repo_root), repo_root))


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


def next_step_content(step: str, blocked: str | None = None) -> tuple[str, bool]:
    """Return (command, auto_flag) for the given pipeline step.

    An undefined step yields ("", False) rather than raising: `_current_step_name`
    returns "complete" for a story with nothing left, and the caller reads the
    empty command as the finished pipeline it is.

    `blocked` is the reason inference already reached, or None. Asked for rather
    than recomputed: `build_report` and `next` both hold it by the time they get
    here, and re-deriving it runs the gate's git and verify work a second time
    against artifacts an implementing agent may be rewriting — two reads of one
    question that can disagree.

    That is also why `repo_root` and `spec_dir` are gone. They were here to
    recompute the block, so a caller that passed them and omitted `blocked` got
    a gate re-read; a caller that passed them once the sentinel was deleted got
    them silently ignored, which reads as a routing decision made from artifacts
    and is not one. Nothing here reaches disk.

    **A blocked step is never automatic, whatever the table says.** The table
    answers "may the loop proceed past a step that finished"; a blocked step has
    not finished. `brainstorm` is where the two diverge since it was flipped
    (#283): automatic in the table, and blocked whenever its boundary question is
    unanswered.

    A blocked `implement` routes to `wfctl verify` rather than
    `/speckit.implement`, because re-running implement there does nothing — every
    task is already ticked and the verdict is what is missing. Tasks still open
    route to the step command as before: the work itself is what remains.
    """
    if blocked and step in _STEPS:
        # `implement` routes to what produces its evidence; every other blocked
        # step routes to itself, because re-entering it is where its answers get
        # given. The flag is what changes, not usually the destination.
        return ("wfctl verify" if step == "implement" else _STEPS[step].command), False
    row = _STEPS.get(step)
    return (row.command, row.continuation == _AUTOMATIC) if row else ("", False)


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
    # Whether this run may take an action that tells someone outside the repo,
    # and which of the seven answers said so. Both always present and both
    # defaulted, for the reason above: a report built without them is a report
    # about a feature nobody granted anything to.
    #
    # `notify_source` is not decoration on the boolean. Five of its values mean
    # refused and they are not one event — nobody granted it, someone turned it
    # off, the stored value is damaged, the tracker could not be reached, this is
    # the trunk — and a consumer that sees only `False` cannot tell a person's
    # decision from a failed read (FR-015).
    notify: bool = False
    notify_source: str = "unset"

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
    from wfctl._paths import resolve_branch
    from wfctl._session import resolved_notify, session_started

    # The branch decides which recorded resolution counts. A state dir shared
    # across worktrees holds every branch's, and reading the newest regardless of
    # whose it was is how one feature's grant answered for another.
    notify = resolved_notify(agent_dir, resolve_branch(repo_root))
    raw = _infer_steps(spec_dir, repo_root)
    name = _current_step_name(raw)
    # `_infer_steps` has already asked; `verification_block` reads the config,
    # loads a record and shells out to git, and `status` runs on every session
    # start. Recomputing it here is the one call this seam was meant to collapse.
    blocked = next((s.reason for s in raw if s.name == name), None)
    command, auto = next_step_content(name, blocked)
    return PipelineReport(
        steps=[
            {
                "name": s.name,
                "state": s.state,
                "annotation": s.annotation,
                # The unrendered reason, beside the rendering of it. A view that
                # needs the reason without the tally `annotation` prefixes had to
                # parse it back out otherwise, and `_PipelineStep.reason` would be
                # a fact living below the payload rather than in it.
                "reason": s.reason,
                # The reason says a record is missing; this says where to put
                # one, and that one of the two answers is a command rather than
                # a file. Resolved here because the path is per-repo, which is
                # exactly why it used to be computed in the console view.
                "remedy": s.remedy,
                "is_current": s.name == name,
            }
            for s in raw
        ],
        current=name if command else None,
        next_command=command or None,
        auto=auto if command else None,
        session_started=session_started(agent_dir),
        auto_approve=read_auto_approve(agent_dir),
        # Read back rather than resolved here. `start` asks the tracker once and
        # records the answer; doing it in this function would put a network
        # round-trip inside the one call every view of pipeline state makes.
        notify=notify.granted,
        notify_source=notify.source,
    )
