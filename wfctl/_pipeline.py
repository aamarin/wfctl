"""Pipeline step inference and display, and the commands wfctl names.

The command inventory lives here rather than at its call sites so one check can
reach all of it: a slash command that no longer ships is indistinguishable from
one that does until someone runs it.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


# step → (slash command that advances it, whether speckit-orchestrate may proceed
# without pausing). One table rather than three keyed by the same names: a step
# defined here carries both values or it does not parse. Split across separate
# tables, omitting the command was silent and severe — `next_step_content`
# returned "", which `next_cmd` treats as a finished pipeline, so a step with no
# command announced "story complete" with half the pipeline unrun.
_STEPS: dict[str, tuple[str, bool]] = {
    "brainstorm": ("/speckit.brainstorm", False),
    "specify":    ("/speckit.specify",    True),
    "clarify":    ("/speckit.clarify",    False),
    "plan":       ("/speckit.plan",       True),
    "tasks":      ("/speckit.tasks",      True),
    "analyze":    ("/speckit.analyze",    False),
    "decompose":  ("/speckit.decompose",  False),
    "implement":  ("/speckit.implement",  False),
}

# Insertion order is pipeline order — derived, so it cannot disagree with the table.
_STEP_NAMES = list(_STEPS)

# The step `design_gate` fires on: whatever follows the design step in the table,
# so inserting a step between the two moves the gate with it. Derived rather than
# spelled "specify", which would go on naming a step that is no longer the one
# after design — silently, since every step name is a valid string.
_AFTER_DESIGN = _STEP_NAMES[_STEP_NAMES.index("brainstorm") + 1]

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


# Printed when the design step advanced without answering the boundary question.
# Both branches are offered because both are legitimate answers: `design-levels`
# excludes changes that draw no new state, and a check with only one exit turns
# those into records that say nothing.
DESIGN_GATE_REFUSAL = """[red]✗[/red] design: no architecture record for this change.

  Either record the boundary this change draws:
      {location}/<slug>.md
  or state that it draws none:
      wfctl arch none --reason "<why>\""""


def _file_exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def _has_open_checkboxes(text: str) -> bool:
    return bool(re.search(r"\[ \]", text))


def _verification_block(repo_root: Path) -> str | None:
    """Why `implement` cannot be complete, or None if nothing blocks it.

    Returns the *first* matching reason, in the order below. Where two hold at
    once the earlier one wins, and the order is chosen so the reason a user can
    act on is named ahead of the one they would only reach after fixing it: a
    failed run on a moved commit reports the failure, not the staleness.

    A repository with no definition of done is never blocked — that is the whole
    degrade path (FR-002), and it must cost nothing, so the config read happens
    before anything touches git.
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


@dataclass
class _PipelineStep:
    name: str
    state: str
    annotation: str | None


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

    for name in _STEP_NAMES:
        if cascade:
            steps.append(_PipelineStep(name, "pending", None))
            continue

        if name == "brainstorm":
            if _file_exists(spec_dir / "design.md"):
                state = "done"
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
            if _file_exists(spec_dir / "delivery.md"):
                state = "done"
            elif tasks_text and not _has_open_checkboxes(tasks_text):
                state = "skipped"
            else:
                state = "pending"

        elif name == "implement":
            if not tasks_text:
                state = "pending"
            elif _has_open_checkboxes(tasks_text) and not _file_exists(
                spec_dir / "checklists" / "implement-complete.md"
            ):
                state = "in_progress"
            else:
                # Tasks read complete. Before #69 that was the whole check, and
                # both routes to it are written by the agent doing the work.
                # A configured definition of done gets the last word.
                blocked = _verification_block(repo_root)
                state = "in_progress" if blocked else "done"
                implement_reason = blocked

        else:
            state = "pending"

        annotation: str | None = None
        if name == "implement" and tasks_text:
            done = len(re.findall(r"\[x\]", tasks_text, re.IGNORECASE))
            total = done + len(re.findall(r"\[ \]", tasks_text))
            annotation = f"{done}/{total} done"
            if implement_reason:
                annotation = f"{annotation}  {implement_reason}"

        steps.append(_PipelineStep(name, state, annotation))

        if state == "pending":
            cascade = True

    return steps


def design_gate(
    spec_dir: Path | None, step: str, unanswered: Callable[[], bool]
) -> bool:
    """Whether advancing past design is being attempted with the question open.

    Decides; it does not render. `DESIGN_GATE_REFUSAL` is the message, and the
    caller formats it with a location only this module has no way to name — so
    the path is resolved on the refusal path alone rather than on every `next`.

    Fires on one transition: the step after design, with `design.md` present.
    Not for the rest of the pipeline — "advance past the design step" is a
    boundary, and a gate that stayed up through plan, tasks and implement would
    refuse work that already answered by moving on. Not before it either: a
    change that never drew a design has nothing to advance past, and gating it
    would demand a record for the bug fixes and copy edits `design-levels`
    explicitly excludes.

    `unanswered` is a git fact, computed by the caller and passed unevaluated:
    this module is pure functions over a tmp dir, and reaching for `subprocess`
    would make every test of this rule build a repository to assert on a string.
    A callable rather than a value because the guards above reject every step but
    one, and an eagerly-evaluated argument would spend up to six git invocations
    per `next` to reach a result thrown away — while a second copy of the guard
    at the call site would be a second place to change when the rule moves.

    A `False` from `unanswered` means proceed, and so does a git answer the
    caller could not get — the caller collapses "cannot tell" into "answered" for the
    same reason: a gate with no evidence against the work does not refuse it.
    Deliberately not the conservative default `_arch` applies to record status.
    There, guessing wrong presents an unreviewed decision as binding; here,
    guessing wrong blocks a pipeline with no way to unblock it.

    What it does not check is whether the record is *about* this change, or
    whether a declaration is true. Neither has an objective test, and FR-010a
    settles the point: the purpose is to stop the question going unanswered, not
    to catch a wrong answer.
    """
    if spec_dir is None or step != _AFTER_DESIGN:
        return False
    if not _file_exists(spec_dir / "design.md"):
        return False
    return unanswered()


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


def next_step_content(
    step: str, repo_root: Path | None = None, spec_dir: Path | None = None
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
        tasks_md = spec_dir / "tasks.md"
        tasks_text = tasks_md.read_text() if _file_exists(tasks_md) else ""
        if tasks_text and not _has_open_checkboxes(tasks_text):
            if _verification_block(repo_root):
                return "wfctl verify", False
    return _STEPS.get(step, ("", False))


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
    from wfctl._session import session_started

    raw = _infer_steps(spec_dir, repo_root)
    name = _current_step_name(raw)
    command, auto = next_step_content(name, repo_root, spec_dir)
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
    )
