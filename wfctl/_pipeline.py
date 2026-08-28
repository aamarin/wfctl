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


@dataclass
class _PipelineStep:
    name: str
    symbol: str
    annotation: str | None


def _infer_steps(spec_dir: Path | None, repo_root: Path) -> list[_PipelineStep]:
    """Internal: return steps with ●/▶/○/– symbols.

    `repo_root` is unused since the design doc moved into the spec dir, but is
    kept so `infer_pipeline`/`steps_display` keep their signatures — the caller
    in cli.py already has it, and dropping it would churn ~30 test call sites
    for no behavioural gain.
    """
    if spec_dir is None:
        return [_PipelineStep(name, "○", None) for name in _STEP_NAMES]

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

    for name in _STEP_NAMES:
        if cascade:
            steps.append(_PipelineStep(name, "○", None))
            continue

        if name == "brainstorm":
            symbol = "●" if _file_exists(spec_dir / "design.md") else "–"

        elif name == "specify":
            if _file_exists(spec_md):
                symbol = "▶" if has_markers else "●"
            else:
                symbol = "○"

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
                symbol = "●"
            elif has_markers:
                # markers are clarify's actual job — no bypass, whatever else exists.
                # ▶ here also keeps _current_step_name's skip branch firing, so a
                # marked spec routes to clarify rather than back to specify.
                symbol = "▶"
            elif _file_exists(spec_dir / "plan.md"):
                # a spec that predates the gate — planning already passed through where
                # clarify now sits. – not ● : the scan genuinely never ran, and saying
                # otherwise would hide that. Counts as done, so an in-flight story is
                # not sent back to clarify a spec its implementation is already built on.
                symbol = "–"
            else:
                symbol = "▶"

        elif name == "plan":
            symbol = "●" if _file_exists(spec_dir / "plan.md") else "○"

        elif name == "tasks":
            symbol = "●" if tasks_text else "○"

        elif name == "analyze":
            symbol = "●" if _file_exists(spec_dir / "checklists" / "analysis-report.md") else "○"

        elif name == "decompose":
            if _file_exists(spec_dir / "delivery.md"):
                symbol = "●"
            elif tasks_text and not _has_open_checkboxes(tasks_text):
                symbol = "–"
            else:
                symbol = "○"

        elif name == "implement":
            if not tasks_text:
                symbol = "○"
            elif _file_exists(spec_dir / "checklists" / "implement-complete.md"):
                symbol = "●"
            elif _has_open_checkboxes(tasks_text):
                symbol = "▶"
            else:
                symbol = "●"

        else:
            symbol = "○"

        annotation: str | None = None
        if name == "implement" and tasks_text:
            done = len(re.findall(r"\[x\]", tasks_text, re.IGNORECASE))
            total = done + len(re.findall(r"\[ \]", tasks_text))
            annotation = f"{done}/{total} done"

        steps.append(_PipelineStep(name, symbol, annotation))

        if symbol == "○":
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
    """Return first ▶ or ○ step; 'complete' if all done.

    Markers in spec.md leave specify ▶, but clarify is the step that resolves
    them — so skip specify when clarify is also pending.
    """
    step_map = {s.name: s.symbol for s in steps}
    for s in steps:
        if s.symbol not in ("▶", "○"):
            continue
        if s.name == "specify" and s.symbol == "▶" and step_map.get("clarify") == "▶":
            continue
        return s.name
    return "complete"


def infer_pipeline(spec_dir: Path | None, repo_root: Path) -> list[tuple[str, bool]]:
    """Return [(step_name, is_done)] ordered list."""
    steps = _infer_steps(spec_dir, repo_root)
    return [(s.name, s.symbol in ("●", "–")) for s in steps]


def current_step(steps: list[tuple[str, bool]]) -> str:
    """Return name of first incomplete step, or 'complete'."""
    for name, done in steps:
        if not done:
            return name
    return "complete"


def next_step_content(step: str) -> tuple[str, bool]:
    """Return (slash_command, auto_flag) for the given pipeline step.

    An undefined step yields ("", False) rather than raising: `current_step`
    returns "complete" for a story with nothing left, and the caller reads the
    empty command as the finished pipeline it is.
    """
    return _STEPS.get(step, ("", False))


def steps_display(spec_dir: Path | None, repo_root: Path) -> list[dict]:
    """Return per-step display dicts with name, symbol, is_current, annotation."""
    raw = _infer_steps(spec_dir, repo_root)
    current = _current_step_name(raw)
    return [
        {
            "name": s.name,
            "symbol": s.symbol,
            "is_current": s.name == current,
            "annotation": s.annotation,
        }
        for s in raw
    ]
