# Implementation Plan: Architecture Knowledge Lifecycle

**Branch**: `86-architecture-knowledge-lifecycle` | **Date**: 2026-08-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/86-architecture-knowledge-lifecycle/spec.md`

## Summary

Architectural decisions currently die with the conversation that produced them:
`design-levels` mandates a Boundaries and Ownership section and 0 of 11 designs
have one. This feature makes the level-2 design gate write a durable record
directly, rather than producing prose that must be copied into one.

Records are markdown files under a configurable architecture root (default
`docs/architecture/`, committed in-tree), in MADR-simple form with one added
field naming who owns a piece of truth and why the other side cannot compute it.
Status is read by a frontmatter line scan reusing the shape of
`_skill_deployment`, so no runtime dependency is added. Only `accepted` records
are projected to agents; the other four statuses stay on disk for people.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer`, `rich` — no additions. Status parsing is a
line scan, per `_workmux.py:12-15`.
**Storage**: Markdown files on disk; git supplies edit history
**Testing**: `uv run pytest -q`; unit tests for resolution and projection, plus a
manual `install-skills` pass for the skill changes the suite cannot verify
**Target Platform**: CLI, macOS and Linux
**Project Type**: CLI tool that also ships skills as package data
**Performance Goals**: N/A — tens of records per repository, read at session start
**Constraints**: No new runtime dependency; ruff rule set stays narrow (`E4`,
`E7`, `E9`, `F`); new functions annotated for `disallow_untyped_defs`; and
minimal-complexity bias
**Scale/Scope**: One repository, tens of records, two new commands and one skill

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md` — verified absent, and
`.specify/` is gitignored, so running `/speckit.constitution` would not produce
one a contributor receives. Gates below are substituted from `AGENTS.md`, the
repository's own documented conventions. The substitution is recorded in
Complexity Tracking.

**Project-independent gates**

- [x] Validation plan exists: the project's type or build check plus the
      specific automated tests and checks needed for the changed surface are
      named. — see Validation Strategy in `spec.md` and quickstart.md
- [x] Complexity is justified: any added abstraction, infrastructure, or
      dependency has a measured or explicit reason the simpler path is
      insufficient. — see Complexity Tracking
- [x] Ownership is stated: for every piece of state or derived value this
      feature introduces, the plan names which side computes it and why the
      other side cannot. — six ownership decisions in `design.md`, carried into
      `data-model.md`

**Substituted from `AGENTS.md`**

- [x] Definition of done is the documented three: `uv run pytest -q`,
      `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, then
      `wfctl doctor` exit 0.
- [x] Changes under `wfctl/agents/` are exercised, not just tested. The suite
      checks that skills ship and cross-reference; it does not check that they
      read well or work. The ADR skill and the `start-session` change require
      `wfctl install-skills` plus a live run.
- [x] Source is edited, never install output. `wfctl/agents/` is the source
      tree; `.agents/`, `.claude/`, `.specify/` are gitignored install artifacts.
- [x] No new runtime dependency. Status parsing is a line scan.
- [x] Ruff rule set is not widened as a drive-by; new functions are annotated.
- [x] `version` in `pyproject.toml` is not bumped as part of this work —
      bumping it on `main` ships a release.
- [x] One PR closes one issue. This epic decomposes into two child issues, each
      with its own PR.

## Project Structure

### Documentation (this feature)

```text
specs/86-architecture-knowledge-lifecycle/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── record-format.md
│   └── cli-commands.md
├── spec.md
├── design.md
└── tasks.md             # /speckit.tasks output — not created here
```

### Source Code (repository root)

```text
wfctl/
├── _paths.py                    # + arch_root(), arch_root_declaration()
├── _arch.py                     # NEW — record parsing, status filter, projection
├── _pipeline.py                 # + design-step advance check
├── cli.py                       # + arch-root, arch context; − promote
├── _session.py                  # − promote()
└── agents/skills/
    ├── architecture-decisions/  # NEW — the ADR skill
    │   ├── SKILL.md
    │   └── record-template.md
    ├── design-levels/SKILL.md   # level-2 gate writes the record
    └── start-session/SKILL.md   # + load the in-force set

tests/
├── test_arch_root.py            # NEW — resolution order, out-of-tree warning
├── test_arch_records.py         # NEW — status parsing, projection, supersession
├── test_agent_session.py        # − promote tests
└── test_pipeline.py             # + advance check

docs/architecture/               # NEW — the default root, committed
AGENTS.md                        # − relocated content (issue B, step 3)
```

**Structure Decision**: Single project, matching the existing flat `wfctl/`
module layout. Record handling goes in a new `_arch.py` rather than into
`cli.py`, following the precedent of `_workmux.py` — logic that can be tested by
a plain function call is concentrated in its own module rather than inlined in
`cli.py`, so tests need no fixture.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates substituted from `AGENTS.md`, not a constitution | `.specify/memory/constitution.md` does not exist and `.specify/` is gitignored, so a constitution would not reach contributors | Writing one now expands this epic's scope into governance it does not otherwise touch; `AGENTS.md` already carries the same conventions and is committed |
| `wfctl arch context` — a new kind of CLI output (project domain content, not pipeline state) | Filter logic placed in a seeded hook can never be fixed forward: `install-config` is seed-once, so a fix reaches only repos seeded afterwards | Hook shell (`grep -l "^status: accepted"`) is genuinely one line and was preferred until the seed-once constraint ruled it out. A falsification test is recorded: if this command is still equivalent to that grep in a year, it did not need to exist |
| New module `_arch.py` rather than functions in `cli.py` | Record parsing and the status filter must be testable without a repo fixture | Inlining in `cli.py` is what `_workmux.py`'s docstring identifies as the pattern to avoid — it forces tests to build git repos to assert on string handling |
