# Implementation Plan: one predicate signature

**Branch**: `314-one-predicate-signature` | **Date**: 2026-09-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from this branch's spec directory (`wfctl feature-paths`)

## Summary

Give the eight pipeline step predicates one signature — `(Evidence) -> tuple[State, str | None]`
— hang each off its row in `_STEPS`, and reduce `_infer_steps` to a loop that
walks the table without branching on the step name. What each step proves does
not change. The structural choice is recorded at
`docs/architecture/design/314-the-step-table-holds-the-predicate.md`.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `typer>=0.12`, `rich>=13` — unchanged by this feature.
No dependency is added; pydantic was weighed and rejected (see the design record).
**Storage**: N/A. Inference reads files under the spec directory and the repo
root; it writes nothing.
**Testing**: `uv run pytest -q`; plus the eight-step render diff described in
`contracts/status-render.md`, which the suite cannot perform.
**Target Platform**: local developer machines and CI (3.11 and 3.13).
**Project Type**: single project — a CLI packaged as a wheel.
**Performance Goals**: no regression. `Evidence` is assembled from reads
`_infer_steps` already performs unconditionally, so per-invocation work is
unchanged (FR-009).
**Constraints**: `uv run` for every command — this repo has two wfctls on PATH
and only `uv run` compares the installed tree against the source being edited.
Ruff rule set stays `E4,E7,E9,F`; mypy stays non-strict with
`disallow_untyped_defs`.
**Scale/Scope**: one module today (`wfctl/_pipeline.py`, 892 lines), becoming
two. Eight predicates, three call sites that unpack `_STEPS`.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repo ships no `.specify/memory/constitution.md`. The gates below are
substituted from its own documented conventions — `AGENTS.md` and the accepted
records `wfctl arch context` projects — and the substitution is recorded in
Complexity Tracking, because a gate borrowed from another project is false.

- [x] **Validation plan exists.** `uv run pytest -q`, `uv run ruff check
      wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor` — the repo's
      stated definition of done — plus the eight-step render diff and a
      deliberately-incomplete-declaration check that must fail mypy.
- [x] **Complexity is justified.** One abstraction is added: `Evidence`. It
      names the prologue `_infer_steps` already computes rather than introducing
      a new concept, and the simpler path (per-step argument lists) is what makes
      the eight predicates undispatchable. No dependency is added.
- [x] **Ownership is stated.** This feature introduces no state and no derived
      value. Every value in `Evidence` is read today by the same code in the same
      order. The one ownership question it touches — whether an inconclusive
      reading stops a step — is already owned by `blocks(verdict, source)`, and
      `decompose` is being routed *to* that owner rather than away from it.
      Declared to the pipeline with `wfctl arch none`; the reason is committed at
      `docs/architecture/declarations/314-one-predicate-signature.md`.
- [x] **Re-checked after Phase 1.** `data-model.md` adds no entity that is not
      already a value in the loop, and `contracts/status-render.md` constrains
      output to be unchanged. No gate moved.

## Project Structure

### Documentation (this feature)

```text
<spec_root>/314-one-predicate-signature/
├── design.md            # brainstorm output
├── spec.md              # /speckit.specify output
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── status-render.md # Phase 1 — the eight renderings that must not change
└── checklists/
    └── requirements.md
```

`specs/` is gitignored and this repo records a `spec_root` outside the working
tree. These reach a reviewer via `specs-trunk`, not via the PR.

### Source Code (repository root)

```text
wfctl/
├── _pipeline.py     # keeps: _STEPS, _infer_steps, PipelineReport,
│                    #        build_report, next_step_content, the command
│                    #        inventory, arch_location
├── _predicates.py   # new: Evidence, State, the eight predicates,
│                    #      blocks, Verdict, Source, _file_exists,
│                    #      _tasks_open, _unkeyed_issues, verification_block,
│                    #      design_block
└── cli.py           # unchanged — imports build_report and verification_block

tests/
├── test_pipeline_state_names.py   # updated imports; assertions unchanged
├── test_pipeline_commands.py      # updated _STEPS unpack at :72
└── test_predicates.py             # new: the shared-signature properties
```

**Structure Decision**: two modules, not the three `_pipeline.py`'s docstring
names. Splitting *display* from *inference* is what
`pipeline-state-is-one-payload` forbids, so "step inference and display" stays
one module. `_predicates.py` takes the evidence readers and the rule they
consult; `_pipeline.py` keeps the table, the walk, the report and the command
inventory. `_STEPS` stays in `_pipeline.py` and imports the eight predicates —
the other direction would have `_predicates.py` import the table it is stored in,
which is circular.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from `AGENTS.md` and the accepted records, not from `.specify/memory/constitution.md` | The repo ships no constitution file; `wfctl arch context` is where its binding decisions actually live | Leaving the gates unfilled makes them decorative; copying another project's constitution would assert rules this repo never accepted |
| `Evidence` — one new type | Eight predicates cannot be dispatched from a table while each takes a different argument list | Per-step argument lists are the status quo and are the defect being fixed |
| `_predicates.py` — one new module | FR-010, and the design record's argument that the dispatcher and the evidence readers change for different reasons | Keeping one 892-line module is the alternative; it is why `#300`'s audit needed 54 lines of prose to describe what eight predicates do |
