"""Pipeline step inference and display."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_STEP_NAMES = [
    "brainstorm", "specify", "clarify", "plan",
    "tasks", "analyze", "decompose", "implement",
]

_STEP_COMMAND: dict[str, str] = {
    "brainstorm": "/speckit.brainstorm",
    "specify":    "/speckit.specify",
    "clarify":    "/speckit.clarify",
    "plan":       "/speckit.plan",
    "tasks":      "/speckit.tasks",
    "analyze":    "/speckit.analyze",
    "decompose":  "/speckit.decompose",
    "implement":  "/speckit.implement",
}

# auto=True → speckit-orchestrate may proceed without pausing
_STEP_AUTO: dict[str, bool] = {
    "brainstorm": False,
    "specify":    True,
    "clarify":    False,
    "plan":       True,
    "tasks":      True,
    "analyze":    False,
    "decompose":  False,
    "implement":  False,
}


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
    """Internal: return steps with ●/▶/○/– symbols."""
    if spec_dir is None:
        return [_PipelineStep(name, "○", None) for name in _STEP_NAMES]

    tasks_md = spec_dir / "tasks.md"
    tasks_text = tasks_md.read_text() if _file_exists(tasks_md) else ""

    spec_md = spec_dir / "spec.md"
    spec_text = ""
    if _file_exists(spec_md):
        # Blank out code before matching, so a spec that *documents* a marker or a
        # heading doesn't read as one. Both specify and clarify match against this.
        #
        # ```.*?``` with DOTALL — a fenced block: ``` then the shortest run of any
        # character including newlines, up to the next ```. Non-greedy, so two
        # separate blocks don't merge into one match spanning the prose between them.
        spec_text = re.sub(r"```.*?```", "", spec_md.read_text(), flags=re.DOTALL)
        # `[^`\n]+` — an inline span: a backtick, one or more characters that are
        # neither a backtick nor a newline, then the closing backtick. Excluding
        # newline keeps an unpaired backtick from swallowing the rest of the file.
        spec_text = re.sub(r"`[^`\n]+`", "", spec_text)

    steps: list[_PipelineStep] = []
    cascade = False

    for name in _STEP_NAMES:
        if cascade:
            steps.append(_PipelineStep(name, "○", None))
            continue

        if name == "brainstorm":
            agent_spec = repo_root / ".agent" / "spec.md"
            symbol = "●" if _file_exists(agent_spec) else "–"

        elif name == "specify":
            if _file_exists(spec_md):
                # prefix match: templates emit `[NEEDS CLARIFICATION: <question>]`,
                # so the bracketed literal never matches a real marker
                symbol = "▶" if "[NEEDS CLARIFICATION" in spec_text else "●"
            else:
                symbol = "○"

        elif name == "clarify":
            # clarify has no file of its own — its artifact is the `## Clarifications`
            # section /speckit.clarify writes into spec.md on every run, including a
            # clean scan. Presence means the scan happened, not that the spec was vague.
            if not _file_exists(spec_md):
                symbol = "○"
            # ^##\s+Clarifications\b with MULTILINE — `##`, one or more spaces, then
            # the word. MULTILINE anchors ^ to the start of any line, not the file.
            # \b requires a word boundary after it, so `## ClarificationsTODO` is not
            # a match while `## Clarifications (2026-08-04)` is. `### Clarifications`
            # fails too: \s+ needs whitespace after `##` and finds a third `#`.
            elif re.search(r"^##\s+Clarifications\b", spec_text, re.MULTILINE):
                symbol = "●"
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
    """Return (slash_command, auto_flag) for the given pipeline step."""
    command = _STEP_COMMAND.get(step, "")
    auto = _STEP_AUTO.get(step, False)
    return command, auto


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
