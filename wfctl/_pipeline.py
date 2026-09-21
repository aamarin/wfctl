"""The step table, the walk over it, and the commands wfctl names.

Two jobs, not the three this said before #314. What each step *reads* is
`_evidence`; what remains here is the order the steps come in, the cascade,
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

import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NamedTuple

from wfctl import _evidence, _stall
from wfctl._paths import arch_root, is_in_tree
from wfctl._evidence import DESIGN_BLOCK_REASON, EvidenceReader, Fact, State, build_evidence

if TYPE_CHECKING:
    # Under the guard rather than at module scope, matching every other read
    # of `_session` below (`auto_approve`, `standing_blocks`): a function-scoped
    # import there, so a type-only one stays off the runtime import path too.
    from wfctl._session import StandingBlock

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


class SubStep(NamedTuple):
    """A pass, one level below a step (`a-step-carries-sub-steps-one-level-deep`).

    The same shape `Step` has, minus the field a pass cannot vary on its own:
    `command` is `str | None` rather than `str`, and `None` is the whole of
    what "a person performs this pass" means once a declaration's `manual: true`
    has already been resolved into this shape — the ambiguity `command: null`
    would carry in `wfctl.json` itself (research.md R10) does not survive
    parsing, because `_declared` requires the affirmative key before it ever
    builds one of these.

    `reads` is a callable for the reason `Step.reads` is one: a `gate: str`
    field needs a second table mapping names to functions, and this way `grep`
    finds a reader's definition beside the row that names it. `evidence` in
    `wfctl.json` is sugar built by `build_file_exists_reader` — strictly less
    than a built-in reader can express, and a stated limit rather than an
    oversight.
    """

    name: str
    command: str | None
    on_finish: Continuation
    reads: EvidenceReader


class Step(NamedTuple):
    """One row of the table: how to advance the step, and how to read it.

    A `NamedTuple` rather than a bare tuple so the three fields have names, and
    rather than a frozen dataclass because it needs no import and no `__init__`
    to write. Tuple compatibility came free and is now unused: this change swept
    all three positional unpacks, so a two-element unpack against a three-field
    row raises `ValueError` rather than quietly taking the first two.

    `reads` is a callable and not a name to look up. A `gate: str` field
    would need a second table mapping names to functions, which is the registry
    #100 ruled out, and it would cost `grep`: written this way, searching for a
    reader finds its definition and its row here.

    `sub_steps` defaults to empty so every existing row keeps parsing. Only
    `brainstorm` carries any today — the artifacts it already produces are what
    earn a pass its own row (`a-step-carries-sub-steps-one-level-deep`); the
    other seven steps have exactly one artifact each and nothing to split.
    """

    command: str
    on_finish: Continuation
    reads: EvidenceReader
    sub_steps: tuple[SubStep, ...] = ()


_STEPS: dict[str, Step] = {
    "brainstorm": Step(
        "/speckit.brainstorm", _AUTOMATIC, _evidence.brainstorm,
        sub_steps=(
            # Architecture before design-doc: the order `design-levels` and the
            # brainstorm skill actually write them in, and the reverse of the
            # order the step's own reader used to check them — see
            # `_evidence.brainstorm`'s docstring for why that read was backwards.
            SubStep("architecture", "/speckit.brainstorm", _AUTOMATIC, _evidence.brainstorm_architecture),
            SubStep("design-doc", "/speckit.brainstorm", _AUTOMATIC, _evidence.brainstorm_design_doc),
        ),
    ),
    "specify":    Step("/speckit.specify",    _AUTOMATIC,       _evidence.specify),
    "clarify":    Step("/speckit.clarify",    _AUTOMATIC,       _evidence.clarify),
    "plan":       Step("/speckit.plan",       _AUTOMATIC,       _evidence.plan),
    "tasks":      Step("/speckit.tasks",      _AUTOMATIC,       _evidence.tasks),
    "analyze":    Step("/speckit.analyze",    _AUTOMATIC,       _evidence.analyze),
    "decompose":  Step("/speckit.decompose",  _AUTOMATIC,       _evidence.decompose),
    "implement":  Step("/speckit.implement",  _AUTOMATIC,       _evidence.implement),
}

# Insertion order is pipeline order — derived, so it cannot disagree with the table.
_STEP_NAMES = list(_STEPS)

# Two conditions hold over every reader, and both are facts about this walk
# rather than about any one of them. `cascade` at the foot of the loop forces every
# step after the first `pending` one to `pending` without calling its reader — so
# a satisfied reader is necessary and never sufficient. And `skipped` advances the
# pipeline exactly as `done` does (`infer_pipeline`), so a reader reaching it
# passes its step on none of the evidence it reads.
#
# What each reader actually proves is documented beside the readers, in
# `_evidence.py`. It moved there with them for the reason it gave for being here:
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

# What `next` names for a manual pass, in the `why:` slot `next_step_file`
# already carries for a blocked step (contracts/cli.md § `wfctl next`). Public
# beside `DESIGN_BLOCK_HELP` because `cli` is the one writer of that file and
# needs the exact sentence, not a paraphrase of it composed at the call site.
MANUAL_PASS_WHY = "a person performs this pass"

# The shape `status --json` promises, as `major.minor` (FR-011, research.md §
# 2). Read here and emitted directly by `status_cmd` — never read from
# `wfctl/contracts/status-payload.json` at runtime, so a package built without
# that file, which `test_packaging.py` catches before release, cannot break a
# caller that only ever asked the running command. The shipped file records
# the same value; `test_status_contract.py` is what proves the two agree.
STATUS_PAYLOAD_VERSION = "1.0"

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
class _PipelineSubStep:
    """A pass, as inference holds it — `SubStep`'s declared shape plus what was
    read from it.

    `claimed` is not a fifth state. `state` is one of the same four names a
    step carries; `claimed` is the field that tells the two producers of
    `skipped` apart (`an-absent-artifact-is-claimed-not-inferred`) — a
    non-null reason a person wrote, or `None` when the state was inherited
    from a parent the pipeline walked past and no claim was ever owed.
    """

    name: str
    state: State
    annotation: str | None
    command: str | None
    on_finish: Continuation
    claimed: str | None = None
    is_current: bool = False


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
    # Always present, always complete — every pass this step has, including a
    # settled-away one (FR-020). Empty for the seven steps with nothing to
    # split, and for a report built with no spec dir at all.
    sub_steps: list[_PipelineSubStep] = field(default_factory=list)


def _infer_steps(
    spec_dir: Path | None, repo_root: Path, ev: _evidence.Evidence | None = None
) -> list[_PipelineStep]:
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
    # Lazy: `_declared` imports this module at its own top level to reach
    # `_STEPS`, so importing it back at *our* top level would cycle. A
    # function-scoped import is the same shape `_apply_block_hold` already uses
    # to reach `_session`.
    from wfctl import _declared
    from wfctl._paths import resolve_branch

    # Above the no-spec-dir arm, not below it. A pass is declared by the
    # repository and claimed away per branch; neither fact needs a feature
    # directory, and a step that is `pending` reports its passes whichever arm
    # produced it. Building bare steps here instead rendered the same `pending`
    # step two ways, and left a consumer unable to see the declared pipeline
    # until a spec directory happened to exist.
    passes_by_step, _ = _declared.load(repo_root)
    claims = _step_claims(repo_root, resolve_branch(repo_root))

    if spec_dir is None:
        return [
            _PipelineStep(
                name, "pending", None,
                sub_steps=_pass_states(name, passes_by_step.get(name, ()), None, "pending", claims),
            )
            for name in _STEP_NAMES
        ]

    # Accepted from the caller when it has one, because `build_report` needs the
    # same reads for the four facts. Built here otherwise, so `next` and the
    # tests that call this directly are unchanged. Optional rather than required
    # for that reason alone: one read either way, and no call site rewritten to
    # gain it.
    if ev is None:
        ev = build_evidence(spec_dir, repo_root)

    steps: list[_PipelineStep] = []
    cascade = False

    for name, step in _STEPS.items():
        if cascade:
            steps.append(_PipelineStep(
                name, "pending", None,
                sub_steps=_pass_states(name, passes_by_step.get(name, ()), None, "pending", claims),
            ))
            continue

        reading = step.reads(ev)
        step_state = _PipelineStep(
            name, reading.state, reading.renders(), reading.reason
        )
        step_state.sub_steps = _pass_states(
            name, passes_by_step.get(name, ()), ev, reading.state, claims
        )
        # The roll-up (research.md R7): a step whose own reading is `done` with
        # an outstanding pass has not finished. The parent's `annotation` and
        # `reason` take the outstanding pass's own — `brainstorm`'s architecture
        # pass carries `DESIGN_BLOCK_REASON` exactly where the old single-reader
        # arm did, so `_design_remedy` below keys on it exactly as before and
        # a consumer reading the *step's* fields (`speckit-orchestrate`, or
        # `_infer_steps`' own callers) sees no change for that case. A pass with
        # nothing to say (`design-doc`) leaves both `None`, which is new: the
        # old reader could not reach "record done, document missing" without
        # reading `design.md` first, the read order `design.md` itself flagged
        # as backwards.
        outstanding = next((s for s in step_state.sub_steps if s.state == "in_progress"), None)
        if outstanding is not None:
            step_state.state = "in_progress"
            step_state.annotation = outstanding.annotation
            step_state.reason = outstanding.annotation
        step_state.remedy = _design_remedy(step_state, repo_root)
        steps.append(step_state)

        # Cascade on the step's *own* reading, unchanged from before this
        # feature: a step whose own artifact is missing was already not
        # evaluating passes above (the `own_state != "done"` arm of
        # `_pass_states`), so the roll-up never changes what triggers this.
        if reading.state == "pending":
            cascade = True

    return steps


def _pass_states(
    step_name: str,
    subs: tuple[SubStep, ...] | list[SubStep],
    ev: _evidence.Evidence | None,
    own_state: State,
    claims: dict[str, str],
) -> list["_PipelineSubStep"]:
    """One reading per pass under `step_name` (research.md R7,
    `an-absent-artifact-is-claimed-not-inferred`).

    A claim wins first and unconditionally (spec edge case 7): a person's
    judgment that a pass does not apply is not overturned by an artifact that
    appears later, or by the step not having been reached yet.

    Otherwise the parent's own reading gates whether passes are evaluated at
    all. `done` runs them in written order with a per-pass cascade exactly like
    the step-level one below it: the first pass that is not `done` is
    `in_progress`, and everything after it is `pending` without its reader
    being called. `skipped` means none of them are, and neither is a pass —
    inherited `skipped` is what "passed by with the parent" means. Every other
    reading — `pending`, and `in_progress` for a reason that is the step's own
    and not a pass's — means the step has not finished *its own* half yet, so
    no pass under it has been reached either; both report `pending`, which is
    the only one of the four names data-model.md's table gives a not-yet-`done`
    parent's passes.

    The `in_progress` case is the one an earlier pass at this function got
    wrong: mirroring the parent's own `in_progress` onto every pass made a
    step whose own artifact was merely unfinished — `specify` with sections
    still missing, say — report every declared pass under it as outstanding
    at once, which is not one of the four states a pass can honestly hold.
    """
    result: list[_PipelineSubStep] = []
    cascade = False
    for sub in subs:
        reason = claims.get(f"{step_name}.{sub.name}")
        if reason is not None:
            result.append(_PipelineSubStep(sub.name, "skipped", None, sub.command, sub.on_finish, claimed=reason))
            continue
        if own_state == "skipped":
            result.append(_PipelineSubStep(sub.name, "skipped", None, sub.command, sub.on_finish))
            continue
        if own_state != "done":
            result.append(_PipelineSubStep(sub.name, "pending", None, sub.command, sub.on_finish))
            continue
        if cascade:
            result.append(_PipelineSubStep(sub.name, "pending", None, sub.command, sub.on_finish))
            continue
        assert ev is not None  # own_state == "done" is only reachable once Evidence exists
        reading = sub.reads(ev)
        if reading.state != "done":
            cascade = True
        result.append(
            _PipelineSubStep(sub.name, reading.state, reading.renders(), sub.command, sub.on_finish)
        )
    return result


def _step_claims(repo_root: Path, branch: str) -> dict[str, str]:
    """Every pass claimed away on `branch`: `<step>.<name>` -> reason.

    One file per pass under `<arch-root>/step-claims/<branch>/`, written by
    `wfctl step none` — read from disk on every inference, like every other
    fact this module reads (`session-state-is-re-derived`); nothing here is
    cached.

    `Path(branch).name`, matching `step_none_cmd`'s own write path: `branch`
    reaches both as a path segment, and a branch containing `/` (a common
    convention this repo's own worktree-handle rule doesn't require) would
    otherwise make the writer and this reader disagree about which directory
    the claim lives in — a claim recorded as successful and never seen again.
    """
    from wfctl._paths import STEP_CLAIMS_DIR

    directory = arch_root(repo_root) / STEP_CLAIMS_DIR / Path(branch).name
    if not directory.is_dir():
        return {}
    claims: dict[str, str] = {}
    for path in sorted(directory.glob("*.md")):
        # Body: "# <step>.<name> does not apply — <branch>\n\n<reason>\n" — the
        # header and the blank line beneath it are `wfctl step none`'s own
        # formatting, stripped here rather than duplicated as a second parser.
        _, _, rest = path.read_text().partition("\n\n")
        claims[path.stem] = rest.strip()
    return claims


def _outstanding_pass(step: _PipelineStep | None) -> _PipelineSubStep | None:
    """The one pass holding `step` up, or None — at most one is ever
    `in_progress`, because `_pass_states`' own cascade stops at the first.
    """
    if step is None:
        return None
    return next((s for s in step.sub_steps if s.state == "in_progress"), None)


def manual_pass_reason(
    blocked: str | None, outstanding: _PipelineSubStep | None
) -> str | None:
    """The reason a view shows for a step held by a manual pass.

    A manual pass carries none of its own, and neither does its step: by the
    time a pass is outstanding the step's own reading is `done`, so the slot is
    empty exactly where a view most needs it filled.

    **Applied after routing, never before.** `next_step_content` reads a
    non-None `blocked` as a held step and returns the step's own command
    without ever looking at the outstanding pass, so filling the reason first
    turns `brainstorm.ui-design` into `/speckit.brainstorm` — the sentence
    explaining the pass would bury the pass.

    One function rather than the substitution `next` used to make inline.
    `resume` composes the same `next-step.md` from the report's step reason,
    found it empty, and wrote "run this command to continue" over a pass
    nothing ships a command for. `pipeline-state-is-one-payload`: a view
    compensating locally for a field the payload left blank is the shape that
    record rules out, and the second view is where it always shows.
    """
    if outstanding is not None and outstanding.command is None:
        return MANUAL_PASS_WHY
    return blocked


def _derive_attention(
    name: str,
    block: "StandingBlock | None",
    outstanding: _PipelineSubStep | None,
    stall: "_stall.Stall | None",
) -> Attention | None:
    """The one condition meaning a person is wanted, ranked blocked → manual →
    stalled — cause before symptom (FR-005, FR-006, data-model.md § Rank).

    Every argument is material `build_report` has already read for its own
    reasons — `block` from `_apply_block_hold`'s `by_step`, `outstanding` from
    `_outstanding_pass`, `stall` from `_stall.find_stall` — so this adds no new
    read (FR-009). `outstanding.command is None` is the same test
    `manual_pass_reason` makes: an outstanding pass with a command is not one a
    person performs, so it is not this condition.

    `detail` never reads from a sentence composed for a person (FR-007, FR-008):
    a block's is the raw `action`, a manual pass's is its dotted name, a
    stall's is written here as an observation of what was seen.
    """
    if block is not None:
        return Attention("blocked", name, block.action)
    if outstanding is not None and outstanding.command is None:
        return Attention("manual", name, f"{name}.{outstanding.name}")
    if stall is not None:
        return Attention(
            "stalled", stall.step,
            f"{stall.step} repeated {stall.passes} times with evidence unchanged",
        )
    return None


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


def _block_remedy(step_name: str, action: str) -> str:
    """FR-015: the block came from the agent's host, not from wfctl; re-running
    will be refused again; a person takes the action and then records it.

    Named by `action`, not by `step_name` — the release matches the string the
    block was filed under, which need not read like the step it holds. The
    release is `report-action` rather than a clearing verb of its own because
    recording the action is what lifts the hold, whoever took it
    (`384-the-agent-reports-through-two-flat-verbs`). A retry that succeeds
    through `wfctl issue` records it without being told.

    `action` is quoted with `shlex.quote` before it goes into the printed
    command: it is free text (`wfctl report-block "issue comment" --reason ...`
    is a legal call), and an unquoted multi-word or shell-metacharacter value
    pasted verbatim either fails Typer's parsing or records something other than
    the release it was meant to.
    """
    # Broken after the em-dash rather than left for `rich` to reflow, the same
    # rule `_IRREVERSIBLE_NOTICE` follows: an automatic wrap breaks at whatever
    # word the terminal width lands on, and `step_name` here is agent-supplied
    # (well, inference-supplied, but still variable-length) rather than a fixed
    # string the author could size for.
    quoted_action = shlex.quote(action)
    return (
        "  Your host refused this, not wfctl —\n"
        f"  re-running {step_name} will be refused again.\n"
        f"  Take the action yourself, then: wfctl report-action {quoted_action}"
    )


def _apply_block_hold(
    steps: list[_PipelineStep], agent_dir: Path, branch: str
) -> tuple[list[_PipelineStep], dict[str, "StandingBlock"]]:
    """Override a step's own reading with a host block reported against it
    (FR-010, FR-011).

    Applied once here, after `_infer_steps` has already produced every step's
    own reading — never spliced into that loop, which sets `cascade = True` on
    the first `pending` step and forces every step after it `pending` too. A
    hold injected there would cascade the same way past a step that is
    legitimately `done`, which is not what a held step means: the pipeline
    stopped at exactly the one step the block named, not at every step after
    it (`test_holding_a_done_step_does_not_cascade_the_steps_after_it`).

    Reads `standing_blocks` once rather than re-deriving the same answer per
    step — the same one-read argument `build_report` already makes for
    `verification_block` two lines above this call: a second read of the same
    log while an agent is writing to it is a window this file was built to
    close, not to reopen for a second question.

    The dict comprehension below is last-write-wins on purpose: two different
    actions can hold the same step, and `standing_blocks` returns them oldest
    first, so the one that lands in `by_step` is the most recently filed —
    the answer a report should give when asked which block currently applies.

    Returns `by_step` beside the steps, for `build_report`'s `attention`
    derivation to read the current step's own `StandingBlock` — its `action`,
    not the composed `annotation` this loop writes onto the step (FR-007). A
    second call to `standing_blocks` there would reopen the same window this
    function was written to close.
    """
    from wfctl._session import standing_blocks

    by_step = {b.step: b for b in standing_blocks(agent_dir, branch) if b.step is not None}
    for step in steps:
        block = by_step.get(step.name)
        if block is None:
            continue
        step.state = "in_progress"
        step.reason = block.reason
        step.annotation = f"blocked: host refused {block.action}"
        step.remedy = _block_remedy(step.name, block.action)
    return steps, by_step


def _current_step_name(steps: list[_PipelineStep]) -> str:
    """Return the first step that still blocks; 'complete' if none does.

    `done` and `skipped` are the two states that do not block — one ran, the
    other was passed by, and neither is somewhere to send a reader back to.

    Markers in spec.md leave specify `in_progress`, but clarify is the step that
    resolves them — so skip specify when clarify is also unfinished.

    **Only for markers.** Since #309 specify has other ways to be `in_progress` —
    sections missing from `spec.md`, or a document still carrying its template's
    `ACTION REQUIRED` — and clarify resolves none of them. Routing a shapeless
    spec to `/speckit.clarify` sends it to the one command that cannot fix it,
    which then writes its `## Clarifications` into a one-character document;
    clarify goes `done`, specify becomes current, and `/speckit.specify`
    regenerates the file from the template and destroys the section just written.
    `_evidence.clarify` names that sequence as the thing its own marker branch
    exists to prevent.

    `reason` is what tells them apart, and it is not a proxy: the marker branch
    deliberately returns none, and every other held branch returns the string
    `status` renders. So the skip asks the question it means — *is specify held
    for something clarify can clear* — rather than asking whether it is held.
    """
    step_map = {s.name: s.state for s in steps}
    for s in steps:
        if s.state not in ("in_progress", "pending"):
            continue
        if (
            s.name == "specify"
            and s.state == "in_progress"
            and s.reason is None
            and step_map.get("clarify") == "in_progress"
        ):
            continue
        return s.name
    return "complete"


def infer_pipeline(spec_dir: Path | None, repo_root: Path) -> list[tuple[str, bool]]:
    """Return [(step_name, is_done)] ordered list."""
    steps = _infer_steps(spec_dir, repo_root)
    return [(s.name, s.state in ("done", "skipped")) for s in steps]


def next_step_content(
    step: str,
    blocked: str | None = None,
    *,
    tasks_open: bool = False,
    outstanding: _PipelineSubStep | None = None,
    auto_approve: bool = False,
) -> tuple[str, bool]:
    """Return (command, auto_flag) for the given pipeline step.

    `outstanding` is the pass holding `step` up, when one is (FR-007) —
    computed by the caller via `_outstanding_pass`, for the reason `blocked` is
    passed rather than recomputed: it is read off the same `_infer_steps` walk
    the caller already has, and asking again here would be a second inference.
    Checked after `blocked`: a host block on the *step* is filed against the
    step name (`_apply_block_hold`), never against one of its passes, and it
    means the same thing regardless of what a pass underneath happens to read.

    A manual pass (`command is None`) returns the qualified pass name and
    `auto=False` always — nothing here ships the command that would run it.
    Otherwise `auto_approve` can turn a `review_required` pass automatic, the
    same grant that already answers a design gate without a person
    (`_AUTO_APPROVE_NOTICE`): autonomy is one switch, not one per kind of gate
    (FR-021b).

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

    A blocked `implement` with no tasks left open routes to `wfctl verify` rather
    than `/speckit.implement`, because re-running implement there does nothing —
    every task is already ticked and the verdict is what is missing. `tasks_open`
    is what tells the two apart: a host block filed mid-implementation (#364)
    holds `implement` the same way a failed verification does, but re-running
    implement is exactly what a mid-task block needs, not `wfctl verify` against
    an unfinished tree. The caller passes it rather than this function reading
    `tasks.md` itself, for the same reason `blocked` is passed rather than
    recomputed — one read of the evidence, held by the caller already.
    """
    if blocked and step in _STEPS:
        # `implement` routes to what produces its evidence, unless tasks are
        # still open — then re-entering implement is where the work is. Every
        # other blocked step routes to itself, because re-entering it is where
        # its answers get given. The flag is what changes, not usually the
        # destination.
        if step == "implement" and not tasks_open:
            return "wfctl verify", False
        return _STEPS[step].command, False
    if outstanding is not None:
        if outstanding.command is None:
            return f"{step}.{outstanding.name}", False
        return outstanding.command, (outstanding.on_finish == _AUTOMATIC or auto_approve)
    row = _STEPS.get(step)
    return (row.command, row.on_finish == _AUTOMATIC) if row else ("", False)


class Attention(NamedTuple):
    """One condition meaning a person is wanted, at most one per report
    (`wfctl-owns-whether-a-worktree-wants-a-human`, data-model.md § Attention).

    `kind` is one of exactly three names — `blocked`, `manual`, `stalled` — and
    is not the raw material each is derived from: that stays on `steps` and
    `stall` unchanged, so a consumer can still read a condition this field did
    not pick. `detail` is captured at derivation time, from the fact itself
    (`StandingBlock.action`, the outstanding pass's dotted name, the stall's own
    count) and never from a sentence composed for a person to read, which stays
    free to be reworded (FR-007, FR-008).
    """

    kind: str
    step: str
    detail: str


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
    # The second session question, beside the first rather than replacing it.
    # `session_started` answers "has a session ever run here" and six skills read
    # it; this answers "is one open for the caller asking" (#200). They are
    # different questions of the same log — the first `start` line against the
    # last — and collapsing them is the defect, not the fix.
    #
    # `session_holder` is not decoration on the boolean: `False` covers a branch
    # that never had a session and one another conversation is holding, and those
    # need different refusals (FR-007). It never carries the identity itself —
    # only whether it is yours.
    #
    # Defaulted so every existing construction keeps compiling. `"unknown"` with
    # `session_open` mirroring `session_started` is the unwired answer, which is
    # what makes the default the released behaviour rather than a refusal.
    session_open: bool = False
    session_holder: str = "unknown"
    # The three questions that decide whether the branch is ready, each read from
    # its own owner (`readiness-is-not-a-step-state`). Beside `steps` and never
    # inside them: they are facts about the branch, so a field on a step would
    # repeat one value down eight rows and assert a per-step variation that does
    # not exist.
    #
    # Defaulted, like `auto_approve` and for its reason: a report built without
    # them is a report about a feature nobody granted anything to. Outside the
    # `current`/`next_command`/`auto` triple below, because a finished story's
    # facts are as true as a running one's — there is no step left to run and the
    # branch is still ready or not.
    facts: tuple[Fact, ...] = ()
    # Whether the loop has stopped making progress (#332). A field on the one
    # report rather than a second read by whoever runs the loop: every view of
    # pipeline state is a rendering of this object, and a verdict the agent
    # derived for itself would be a source of pipeline truth living outside it.
    # `None` is the common case — a run that is progressing has nothing to say.
    stall: "_stall.Stall | None" = None
    # Beside `stall`, never instead of it — the same pairing `session_open`
    # keeps beside `session_started` two fields up. Derived in `build_report`
    # from material that function has already read (`standing_blocks`,
    # `_outstanding_pass`, `_stall.find_stall`), ranked blocked → manual →
    # stalled, cause before symptom (FR-006, FR-009, data-model.md § Rank).
    # Defaulted like `stall` beside it: `None` is the common case, a run with
    # nothing to say.
    attention: "Attention | None" = None
    # This pass's own digest, for `resume` to record. On the report rather than
    # recomputed at the call site because the two reads could disagree while an
    # implementing agent is writing — the window `build_report`'s own seam
    # comment exists to close, met again by a second reader of the same files.
    # `None` where no feature directory resolved: there is no evidence to digest,
    # and a pass that recorded none is one `find_stall` will not compare.
    evidence_digest: str | None = None

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


def build_report(
    spec_dir: Path | None,
    repo_root: Path,
    agent_dir: Path,
    session_id: str | None = None,
) -> PipelineReport:
    """The one inference. Every view of pipeline state is a rendering of this.

    `session_id` defaults to None so every existing caller keeps compiling and
    keeps its answer. That default is not a placeholder for a value wfctl could
    work out: the caller owns the identity and wfctl cannot derive it
    (`session-identity-comes-from-the-caller`), so "nothing was presented" is the
    honest input and `"unknown"` is the honest output.
    """
    # Aliased: the report field and the reader are the same word, and
    # `auto_approve=auto_approve(agent_dir)` two lines down reads as a
    # self-reference rather than a call.
    from wfctl._session import auto_approve as read_auto_approve
    from wfctl._paths import resolve_branch
    from wfctl._session import session_open_for, session_started

    branch = resolve_branch(repo_root)

    # `session_open` mirrors `session_started` under `"unknown"` — the unwired
    # row of contracts/cli.md — which is what makes a caller that presents
    # nothing see the released answer rather than a refusal (FR-006).
    # `session_open_for` only ever returns `"unknown"` after confirming
    # `session_started(agent_dir, branch)` itself, so the mirror needs no second
    # read of it below.
    holder = session_open_for(agent_dir, session_id, branch)

    # One read, two consumers. The step readers and the artifacts fact ask the
    # same three files, and two reads of them can disagree while an implementing
    # agent is writing — the window `build_report` was made to close for the
    # blocked reason, met again by a field added beside it.
    ev = None if spec_dir is None else build_evidence(spec_dir, repo_root)
    raw = _infer_steps(spec_dir, repo_root, ev)
    # After `_infer_steps` returns, never inside its loop — see
    # `_apply_block_hold`'s own docstring for why splicing it into the loop
    # would cascade a hold past every step legitimately `done` after it.
    raw, by_step = _apply_block_hold(raw, agent_dir, branch)
    # One read, whether or not a feature directory resolved. `Evidence` carries
    # it when there is one; with none there is no evidence to carry it and the
    # fact's owner is asked directly. Either way it is asked once — two calls per
    # report was the cost the panel measured, and the seam below says why.
    verification = (
        _evidence.verification_block(repo_root) if ev is None else ev.verification
    )
    name = _current_step_name(raw)
    # `_infer_steps` has already asked; `verification_block` reads the config,
    # loads a record and shells out to git, and `status` runs on every session
    # start. Recomputing it here is the one call this seam was meant to collapse.
    blocked = next((s.reason for s in raw if s.name == name), None)
    granted = read_auto_approve(agent_dir)
    outstanding = _outstanding_pass(next((s for s in raw if s.name == name), None))
    if outstanding is not None:
        outstanding.is_current = True
    command, auto = next_step_content(
        name, blocked, tasks_open=bool(ev and ev.tasks_open),
        outstanding=outstanding, auto_approve=granted,
    )
    # After the routing call above, for the reason `manual_pass_reason` gives.
    # Written onto the step rather than kept beside the payload: `resume` and
    # every other reader take the reason off the step, and a second field
    # carrying the same answer is the two-vocabularies problem one level down.
    current = next((s for s in raw if s.name == name), None)
    if current is not None:
        current.reason = manual_pass_reason(current.reason, outstanding)
    digest_now = None if ev is None else _stall.digest(ev)
    # Computed once, here, rather than inline in both the `attention` and
    # `stall` keyword arguments below — the same one-read argument this
    # function already makes for `verification` and for `by_step`.
    stall = _stall.find_stall(
        agent_dir,
        branch=branch,
        current=digest_now,
        covered=tuple(n for n in _stall.COVERED if spec_dir and (spec_dir / n).exists()),
    )
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
                # Always present and always complete (FR-020) — every pass this
                # step has, settled-away ones included. `--all` is a console
                # filter applied at the moment of printing; nothing here is
                # ever dropped from the payload.
                "sub_steps": [
                    {
                        "name": sub.name,
                        "state": sub.state,
                        "annotation": sub.annotation,
                        "command": sub.command,
                        "manual": sub.command is None,
                        "claimed": sub.claimed,
                        "is_current": sub.is_current,
                    }
                    for sub in s.sub_steps
                ],
            }
            for s in raw
        ],
        current=name if command else None,
        next_command=command or None,
        auto=auto if command else None,
        session_started=session_started(agent_dir, branch),
        session_open=holder in ("self", "unknown"),
        session_holder=holder,
        auto_approve=granted,
        facts=_evidence.facts(ev, repo_root, verification),
        attention=_derive_attention(name, by_step.get(name), outstanding, stall),
        # Read from the event log, which `resume` has already written this pass
        # into. The count has to outlive the agent's memory of it, which is the
        # whole of `wfctl-counts-the-passes`.
        #
        # `branch` because one state dir can serve several branches; `current`
        # because a verdict that outlived the artifacts it describes is a false
        # claim on the screen a person reads right after acting on it; `covered`
        # so the report names the files that are there rather than three
        # constants, two of which `status` may be reporting as missing.
        stall=stall,
        evidence_digest=digest_now,
    )
