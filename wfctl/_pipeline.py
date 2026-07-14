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

    steps: list[_PipelineStep] = []
    cascade = False
    specify_symbol = "○"

    for name in _STEP_NAMES:
        if name == "clarify":
            steps.append(_PipelineStep(name, specify_symbol, None))
            continue

        if cascade:
            steps.append(_PipelineStep(name, "○", None))
            continue

        if name == "brainstorm":
            agent_spec = repo_root / ".agent" / "spec.md"
            symbol = "●" if _file_exists(agent_spec) else "–"

        elif name == "specify":
            spec_md = spec_dir / "spec.md"
            if _file_exists(spec_md):
                text = spec_md.read_text()
                text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
                text = re.sub(r"`[^`\n]+`", "", text)
                symbol = "▶" if "[NEEDS CLARIFICATION]" in text else "●"
            else:
                symbol = "○"
            specify_symbol = symbol

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
    """Return first ▶ or ○ step; skip specify when clarify inherits it; 'complete' if all done."""
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
