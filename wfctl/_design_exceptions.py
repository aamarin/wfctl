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

import textwrap
from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple

from wfctl import arch as _arch
from wfctl._io import write_atomic

# The name `arch none` writes under. It has no dot before `.md`, which is what
# keeps it out of `passes`: a pass is always `<step>.<pass>`.
BOUNDARY = "boundary"

# The name `spec none` writes under, with no dot for the same reason.
SPEC = "spec"

# The spec pipeline's own artifacts. Any one of them outranks a recorded "no
# spec", so a branch that switched to yes and forgot the file still runs the
# pipeline. Here rather than in `_evidence`, because `check-body` and the
# pipeline both decide whether the "no" is in effect, and two lists would let
# them disagree.
SPEC_ARTIFACTS = ("design.md", "spec.md", "plan.md", "tasks.md")

_FOLDER = "exceptions"


def folder(spec_dir: Path) -> Path:
    """The exceptions folder for `spec_dir`, whether or not it exists."""
    return spec_dir / _FOLDER


def _directory(spec_dir: Path, context: str | None) -> Path:
    """The folder one exception lives in: `exceptions/` for a branch-wide one,
    `exceptions/<context>/` for one answering a single context.

    A context is a folder name, so one that could leave `exceptions/` is refused
    here as well as where the CLI reads it. `wfctl.arch.names` only lists names
    of the right shape, but this module builds the path.
    """
    if context is None:
        return folder(spec_dir)
    if not context or context != Path(context).name or context.startswith("."):
        raise ValueError(f"not a context name: {context!r}")
    return folder(spec_dir) / context


def path(spec_dir: Path, name: str, *, context: str | None = None) -> Path:
    """The file one exception lives in, without touching the disk.

    Public because the worktree guard prints it in the command that removes a
    contradicted boundary exception, and would otherwise build the name itself.
    """
    return _directory(spec_dir, context) / f"{name}.md"


def _title(name: str, context: str | None) -> str:
    if name == BOUNDARY:
        return "No new boundary" if context is None else f"No new boundary for {context}"
    if context is None:
        return f"`{name}` does not apply"
    return f"{name} does not apply to {context}"


def write(spec_dir: Path, name: str, reason: str, *, context: str | None = None) -> Path:
    """Write one exception, replacing any earlier one under the same name.

    Creates the spec folder too: `arch none` is often the first thing a branch
    writes, before `design.md` exists (FR-003). The reason is not validated
    here, since each command prints its own refusal for an empty one or a
    placeholder.
    """
    target = path(spec_dir, name, context=context)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(target, f"# {_title(name, context)}\n\n{reason}\n")
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


def boundary(spec_dir: Path, *, context: str | None = None) -> str | None:
    """The boundary exception's reason, or None when there is none.

    A file with no reason is no exception. `arch none` refuses an empty reason,
    so only a hand-written file gets here, and read as an answer it cleared the
    design gate with nothing to show a reviewer.
    """
    file = path(spec_dir, BOUNDARY, context=context)
    if not file.is_file():
        return None
    return _reason(file) or None


def spec(spec_dir: Path) -> str | None:
    """The "no spec" answer's reason, or None when there is none, read the way
    `boundary` reads its file and for its reason about an empty one."""
    file = path(spec_dir, SPEC)
    if not file.is_file():
        return None
    return _reason(file) or None


def spec_artifact(spec_dir: Path) -> str | None:
    """The first of `SPEC_ARTIFACTS` in `spec_dir`, or None when there is none."""
    return next((name for name in SPEC_ARTIFACTS if (spec_dir / name).is_file()), None)


def spec_in_effect(spec_dir: Path) -> str | None:
    """The "no spec" reason when it decides the route, which is only while no
    spec artifact exists beside it.

    The one rule `check-body` and the pipeline share, so a PR with a spec is
    never asked for a no-spec reason the pipeline is ignoring.
    """
    reason = spec(spec_dir)
    if reason is None or spec_artifact(spec_dir) is not None:
        return None
    return reason


def passes(spec_dir: Path, *, context: str | None = None) -> dict[str, str]:
    """Every pass exception as `<step>.<pass>` -> reason.

    Without a context this reads one level and never a subfolder, so a "no"
    for one context is not a claim on the whole pass.

    Read from disk on every call, like every other fact the pipeline reads
    (`session-state-is-re-derived`). A missing folder is no exceptions, which is
    the state of every branch that has written none.
    """
    directory = _directory(spec_dir, context)
    if not directory.is_dir():
        return {}
    # A file with no reason is skipped, for `boundary`'s reason.
    found = {
        file.stem: _reason(file)
        for file in sorted(directory.glob("*.*.md"))
        if file.is_file()
    }
    return {name: reason for name, reason in found.items() if reason}


def reasons(spec_dir: Path) -> list[tuple[str, str]]:
    """Every exception's label and reason, branch-wide and per-context.

    One reader for `check-body`, which compares each reason against the PR body
    and must see a per-context "no" as well as a branch-wide one. A per-context
    label ends `for <context>`, so a finding says which answer is missing.
    """
    found: list[tuple[str, str]] = []
    spec_reason = spec_in_effect(spec_dir)
    if spec_reason is not None:
        found.append((SPEC, spec_reason))
    boundary_reason = boundary(spec_dir)
    if boundary_reason is not None:
        found.append((BOUNDARY, boundary_reason))
    found += list(passes(spec_dir).items())
    directory = folder(spec_dir)
    if not directory.is_dir():
        return found
    for sub in sorted(p for p in directory.iterdir() if p.is_dir()):
        sub_boundary = boundary(spec_dir, context=sub.name)
        if sub_boundary is not None:
            found.append((f"{BOUNDARY} for {sub.name}", sub_boundary))
        found += [
            (f"{name} for {sub.name}", reason)
            for name, reason in passes(spec_dir, context=sub.name).items()
        ]
    return found


def boundary_contexts(spec_dir: Path) -> list[str]:
    """The contexts this branch answered with a per-context boundary exception,
    sorted.

    Listed from the folder and not from the domain page's name list, so a reader
    still sees them after the list goes away (#653). A context with no reason in
    its file is no exception, as in `boundary`.
    """
    directory = folder(spec_dir)
    if not directory.is_dir():
        return []
    return sorted(
        sub.name
        for sub in directory.iterdir()
        if sub.is_dir() and boundary(spec_dir, context=sub.name) is not None
    )


# --- the brainstorm gate -------------------------------------------------------
#
# The gate pairs the branch's records, which architecture records owns, with the
# exceptions above, which are evidence's. It lives here and not beside the
# records because arch may not import evidence.


class Level(NamedTuple):
    """What differs between the two checks that match contexts: the noun the
    pause uses, the pass whose "no" answers a context, and the command that
    writes it. The architecture check's "no" is the boundary exception, which
    has no pass name."""

    noun: str
    pass_name: str | None
    command: str


ARCHITECTURE = Level("architecture record", None, "wfctl arch none")
SOFTWARE_DESIGN = Level(
    "software design record",
    "brainstorm.software-design",
    "wfctl step none brainstorm.software-design",
)


class Gap(NamedTuple):
    """Why brainstorm pauses and how to fix it. `unanswered` is True only when
    the cause is a listed context with no answer, the one case where git's
    silence about the branch's records can change the result."""

    reason: str
    remedy: str
    unanswered: bool


def _no(spec_dir: Path, context: str, level: Level) -> str | None:
    """The reason a branch gave for needing no record for `context`, if any."""
    if level.pass_name is None:
        return boundary(spec_dir, context=context)
    return passes(spec_dir, context=context).get(level.pass_name)


def _governed(context: str, records: Iterable[_arch.Record]) -> bool:
    return any(context in record.governs for record in records)


def unanswered(
    listed: Iterable[str], records: Iterable[_arch.Record], spec_dir: Path, level: Level
) -> str | None:
    """The first listed context that no record governs and that has no "no", or
    None when each one has an answer. A "no" for one context never answers
    another."""
    held = list(records)
    for context in listed:
        if not _governed(context, held) and _no(spec_dir, context, level) is None:
            return context
    return None


def pause(
    known: frozenset[str],
    spec_dir: Path,
    records: Iterable[_arch.Record],
    level: Level,
    *,
    location: str,
) -> Gap | None:
    """Why brainstorm pauses, or None when every listed context has an answer.

    A missing or empty `Contexts` line comes first, then a name that isn't on
    the domain page, then a context with no answer. The order matters because a
    misspelled name would otherwise read as a context nobody answered, and the
    remedy would ask for a record about a context that doesn't exist.

    `location` is where a record for this level goes. The caller knows the repo
    root and this module doesn't.
    """
    branch_lists = _arch.listed(spec_dir)
    if not branch_lists:
        return Gap(
            "design.md lists no contexts",
            "  Add a line under the title of design.md listing the contexts this branch changes:\n"
            "      Contexts: <names from the domain page>",
            False,
        )
    unknown = next((c for c in branch_lists if c not in known), None)
    if unknown is not None:
        wrapped = textwrap.fill(
            ", ".join(sorted(known)), width=84, initial_indent="      ",
            subsequent_indent="      ",
        )
        return Gap(
            f"{unknown} is not a context on the domain page",
            f"  The domain page lists:\n{wrapped}",
            False,
        )
    context = unanswered(branch_lists, records, spec_dir, level)
    if context is None:
        return None
    return Gap(
        f"no {level.noun} governs {context}",
        f"  Either add a record whose governs field names {context}, under:\n"
        f"      {location}/\n"
        "  or state that it needs none:\n"
        f'      {level.command} --context {context} --reason "<why>"',
        True,
    )


def answers(
    listed: Iterable[str], records: Iterable[_arch.Record], spec_dir: Path, level: Level
) -> list[str]:
    """One `<context>: no — <reason>` line for each listed context answered with
    a "no" and not by a record, for the done row in `wfctl status`."""
    held = list(records)
    lines = []
    for context in listed:
        reason = _no(spec_dir, context, level)
        if reason is not None and not _governed(context, held):
            lines.append(f"{context}: no — {reason}")
    return lines
