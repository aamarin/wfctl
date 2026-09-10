# Implementation Plan: promote a decision to accepted

**Branch**: `321-promote-a-decision` | **Date**: 2026-09-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/321-promote-a-decision/spec.md`

## Summary

Add `wfctl arch accept <slug> --agreed "<where>"`: the one transition that moves a
record from `proposed` to `accepted`, writing the citation into the record's own
`## Log`. `supersede()`'s body moves to a shared `_set_status`, and `accept()`
becomes its second caller with one guard `supersede` does not carry — only a
`proposed` record promotes.

The authority question is settled in `docs/architecture/a-human-accepts-a-decision.md`
and the structural one in `docs/architecture/design/321-one-status-mutation.md`.
This plan implements those; it does not re-decide them.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `typer`, `rich` — both already present. Nothing new.
**Storage**: markdown files under `wfctl arch-root`. No database, no state dir.
**Testing**: `uv run pytest -q`; new unit tests in `tests/test_arch_records.py`
for the module transition, and command-level tests beside the existing `arch`
command tests, with `NO_COLOR` pinned on anything asserting output.
**Target Platform**: local CLI, macOS and Linux, as CI runs it on 3.11 and 3.13.
**Project Type**: CLI (single package, `wfctl/`).
**Performance Goals**: none that differ from the surrounding commands. `accept`
reads every record once, which `arch context` already does on every session start.
**Constraints**: an accepted record's body is not editable (VR-005); the ruff set
stays `E4,E7,E9,F`; mypy runs with `disallow_untyped_defs`; minimal-complexity
bias.
**Scale/Scope**: 24 records in this repository; a repository with thousands is not
a case this feature is shaped for and none exists.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The project-specific
gates below are substituted from its own documented conventions in `AGENTS.md`
and from the accepted records `wfctl arch context` projects; the substitution is
recorded in Complexity Tracking, per the template's instruction.

- [x] **Validation plan exists**: `uv run pytest -q`, `uv run ruff check
      wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor` — the repository's
      definition of done — plus the unit and command tests named in
      Technical Context and the manual exercise in `quickstart.md`.
- [x] **Complexity is justified**: one new command, one new public function, one
      extracted private one. The extraction is argued in
      `design/321-one-status-mutation.md` against the direct baseline of a second
      independent function. No new module, no new dependency, no new state.
- [x] **Ownership is stated**: `docs/architecture/a-human-accepts-a-decision.md`
      — a human owns *"is this decision binding?"*; wfctl owns *"where was that
      said, and when?"*. wfctl cannot compute the first because every signal
      available to it is evidence the decision was implemented, not agreed.
- [x] **`a-rule-is-expressed-as-a-check`** (accepted): the rule ships as a
      command with refusals, not as prose. The one part that stays prose — that
      the citation is true — has no objective test, and NFR-001 says so rather
      than implying a check exists.
- [x] **`knowledge-placement`** (accepted): the `proposed`-only guard lives in
      `_arch` beside the mutation, not in `cli`, because it is a fact about the
      record. The slug-resolution and near-miss messages live in `cli`, because
      they are facts about an argument.
- [x] **`session-state-is-re-derived`** (accepted): nothing about acceptance is
      written to the state dir. The record file is the durable answer, and the
      Clarifications section records the decision not to duplicate it into
      `events.jsonl`.
- [x] **`pipeline-state-is-one-payload`** (accepted): untouched. This feature adds
      no step state and no view of one; `_arch` and `_pipeline` stay independent,
      which is one of the reasons the pipeline-gate candidate was rejected.
- [x] **`wfctl-runs-the-verification`** (accepted): the new command is not a
      verification and does not certify anything. It records a human's act, and
      NFR-001 names the same tamper-evident ceiling that record names for itself.

_Post-Phase-1 re-check_: unchanged. Phase 1 produced no new abstraction — the
contract is one command, the data model adds one transition to an existing
entity, and no boundary moved.

## Project Structure

### Documentation (this feature)

```text
specs/321-promote-a-decision/
├── plan.md              # This file
├── design.md            # Levels 1 and 3, from /speckit.brainstorm
├── spec.md              # Requirements and clarifications
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── arch-accept.md   # The command surface
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

Records are not in this tree. They are committed under `docs/architecture/`,
because `specs/` is gitignored and resolves outside the working tree.

### Source Code (repository root)

```text
wfctl/
├── _arch.py        # _set_status (extracted), supersede (caller), accept (new)
└── cli.py          # arch_app: the `accept` command beside `context`/`none`/`check`

tests/
├── test_arch_records.py    # module-level: the transition and its refusals
└── test_arch_commands.py   # command-level: argument handling and output
```

**Structure Decision**: the existing single-package layout. The feature adds no
directory and no module: the transition belongs in `_arch.py` with the other
record operations, and the command belongs in the `arch` typer group with the
three commands already there.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from `AGENTS.md` and the accepted records | The repository ships no `.specify/memory/constitution.md`, and the template requires that a substitution be recorded rather than left silent | Borrowing another project's constitution would state gates this project never adopted; leaving the section with only the two project-independent gates would drop the accepted records, which are the gates that actually bind here |
| `_set_status` extracted rather than `accept` written standalone | Four file-format hazards live in `supersede`'s body and a copy loses them silently; `_frontmatter_end` and `_key_value` both say in their docstrings that they exist so the parser and `supersede` cannot disagree | Argued in full against the direct baseline in `docs/architecture/design/321-one-status-mutation.md` |
