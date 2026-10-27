"""The exceptions folder inside a spec folder: where it is and what its files say.

A design exception is a branch's statement, with a reason, that a design step
doesn't apply to it. `wfctl arch none` writes the boundary exception and
`wfctl step none` writes one per pass; the brainstorm gate, the pipeline, the
session summary, `check-body` and the worktree guard read them.

One module for every writer and reader, because the format used to be written
in `cli.py` and parsed in `_pipeline.py`, and a move or a format change had to
find four places that each built their own path (`design-exceptions-module.md`).
Plain functions rather than a class: there is one place exceptions are stored
and no second backend planned.
"""
from __future__ import annotations

from pathlib import Path

from wfctl._io import write_atomic

# The name `arch none` writes under. It has no dot before `.md`, which is what
# keeps it out of `passes`: a pass is always `<step>.<pass>`.
BOUNDARY = "boundary"

_FOLDER = "exceptions"


def folder(spec_dir: Path) -> Path:
    """The exceptions folder for `spec_dir`, whether or not it exists."""
    return spec_dir / _FOLDER


def path(spec_dir: Path, name: str) -> Path:
    """The file one exception lives in, without touching the disk.

    Public because the worktree guard prints it in the command that removes a
    contradicted boundary exception, and would otherwise build the name itself.
    """
    return folder(spec_dir) / f"{name}.md"


def _title(name: str) -> str:
    if name == BOUNDARY:
        return "No new boundary"
    return f"`{name}` does not apply"


def write(spec_dir: Path, name: str, reason: str) -> Path:
    """Write one exception, replacing any earlier one under the same name.

    Creates the spec folder too: `arch none` is often the first thing a branch
    writes, before `design.md` exists (FR-003). The reason is not validated
    here, since each command prints its own refusal for an empty one or a
    placeholder.
    """
    target = path(spec_dir, name)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(target, f"# {_title(name)}\n\n{reason}\n")
    return target


def _reason(file: Path) -> str:
    # Everything after a leading `# ` header, so a reason with a blank line of
    # its own survives. Not a split on the header's blank line: a file written
    # by hand as one line, or with no blank line under its header, then read
    # back as an empty reason.
    lines = file.read_text().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def boundary(spec_dir: Path) -> str | None:
    """The boundary exception's reason, or None when there is none."""
    file = path(spec_dir, BOUNDARY)
    if not file.is_file():
        return None
    return _reason(file)


def passes(spec_dir: Path) -> dict[str, str]:
    """Every pass exception as `<step>.<pass>` -> reason.

    Read from disk on every call, like every other fact the pipeline reads
    (`session-state-is-re-derived`). A missing folder is no exceptions, which is
    the state of every branch that has written none.
    """
    directory = folder(spec_dir)
    if not directory.is_dir():
        return {}
    return {
        file.stem: _reason(file)
        for file in sorted(directory.glob("*.*.md"))
        if file.is_file()
    }
