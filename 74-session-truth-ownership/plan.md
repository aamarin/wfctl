# Implementation Plan: session truth ownership

**Branch**: `74-session-truth-ownership` | **Date**: 2026-08-30 | **Spec**: `spec.md`
**Input**: Feature specification from the branch's spec dir (outside the repo; ask `wfctl feature-paths`)

## Summary

Delete the two session files that are written once and go stale, and make every
value they carried derive from artifacts at read time. `wfctl end` stops
claiming a completion it cannot observe and reports what it can see. Pipeline
state stops being a glyph inside the inference and becomes a name, with symbols
applied when printing.

Three defects, one boundary: #42 (stale resume point), #70 (unobservable
completion claim), and the encoding that makes both hard to fix safely.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer`, `rich`. No new runtime dependency; this
feature adds none and the project's whole runtime surface is those two.
**Storage**: files. Spec artifacts under the resolved spec root, session state
under the XDG state dir (`wfctl state-dir`), both plain text.
**Testing**: `uv run --frozen pytest -q`, `uv run --frozen ruff check wfctl/
tests/`, `uv run --extra dev mypy wfctl/`. Console assertions pin `NO_COLOR`.
**Target Platform**: local developer machines, macOS and Linux.
**Project Type**: single project — a CLI plus the skills it installs.
**Performance Goals**: re-derivation happens on every read, so `status` and
`resume` must stay file reads. No subprocess beyond the git calls already made,
and none added to the inference path.
**Constraints**: the ruff rule set stays `E4,E7,E9,F` (#14); mypy stays
non-strict with `disallow_untyped_defs`; skills changes are not verified by the
suite alone and must be exercised with `wfctl install-skills`.
**Scale/Scope**: one developer, tens of worktrees per machine, eight pipeline
steps, four states.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repo has no `.specify/memory/constitution.md`. Gates are substituted from
its own documented conventions — `AGENTS.md` and the accepted records under
`wfctl arch-root` — and the substitution is recorded in Complexity Tracking.

- [x] Validation plan exists: the three definition-of-done commands are named
      above, plus one test per reachable pipeline state, a test that advances
      artifacts with no session command in between, and a test that no output
      path emits a completion claim.
- [x] Complexity is justified: this feature removes two files, one field and one
      encoding. It adds no abstraction, no dependency and no new output surface —
      the machine view was explicitly deferred to its own issue at
      `/speckit.clarify`.
- [x] Ownership is stated: `session-state-is-re-derived` (accepted) and
      `pipeline-state-is-one-payload` (proposed) name the owning side and why the
      other cannot compute it. This plan implements them; it does not re-decide
      them.
- [x] No new runtime dependency, and the linter and type-checker configuration
      are untouched (`AGENTS.md`: enabling a rule set is its own reviewable diff).
- [x] Skills that ship with wfctl are exercised, not just tested: `start-session`
      reads a file this feature deletes, so it changes with the code and is run
      after `wfctl install-skills`.

**Post-design re-check (after Phase 1)**: still passing, and the design moved
one gate rather than merely restating it — the payload in `data-model.md` carries
`session_started`, which is what let `current.json` go without any command losing
a fact. No new abstraction, dependency or output surface was introduced by the
contracts.

## Project Structure

### Documentation (this feature)

```text
<spec root>/74-session-truth-ownership/
├── plan.md              # this file
├── spec.md
├── design.md            # levels 1 and 3, written before speckit ran
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
wfctl/
├── _session.py      start/end/resume — loses current.md, current.json, status
├── _pipeline.py     _PipelineStep carries a state name; not-started vs skipped
├── cli.py           glyph map, the next: line, state-dir cleanup on touch
├── _io.py           load_agentconfig deleted (zero callers)
└── agents/skills/
    ├── start-session/SKILL.md   reads the pipeline report, not current.md
    └── end-session/SKILL.md     no completion claim to fill in

tests/
├── test_pipeline.py     one test per reachable state, NO_COLOR pinned
├── test_session.py      derivation, deletion, migration cleanup
└── test_cli_*.py        rendered output per state
```

**Structure Decision**: single project, existing layout. The feature touches
four modules and two shipped skills; no new module is created, and no directory
is added.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from `AGENTS.md` and the accepted records | The repo has no `constitution.md`; a gate with no source is decorative | Borrowing another project's constitution would assert constraints this repo never adopted |
| A state name replaces a symbol across ten inference branches | `–` and `●` both mean "does not block" and only one of them ran; the difference is unrecoverable from the drawing once the pipeline report is the agent's only read | Leaving the glyph and documenting a legend puts the mapping in prose, where the test suite does not cover it and each reader duplicates it |
