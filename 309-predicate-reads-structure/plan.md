# Implementation Plan: predicate reads structure

**Branch**: `309-predicate-reads-structure` | **Date**: 2026-09-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `spec.md` in this directory

## Summary

`specify` and `plan` gain a structural read: each requires its artifact to carry
the sections its template defines, matched stem-anchored over text with fenced
and inline spans blanked. The required names are constants in `_pipeline.py`,
and a test holds them equal to the shipped templates' mandatory sets. A file
that exists and carries none of them reports `in_progress` annotated with the
sections it lacks. `clarify`'s existing `skipped` verdict is unchanged and gains
an annotation saying the scan never ran.

Ownership is recorded at `docs/architecture/required-sections-are-wfctls.md`.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: none beyond `typer` + `rich`, already present; this
feature adds none
**Storage**: N/A — inference reads files under the spec directory
**Testing**: `uv run pytest -q`; new unit cases in `tests/` against
`_infer_steps`, plus a drift test reading `wfctl/specify/templates/`
**Target Platform**: CLI, wherever wfctl runs
**Project Type**: single project (CLI + library)
**Performance Goals**: no regression. The feature adds one file read
(`plan.md`, previously stat-only) and two regex passes per inference; inference
already reads `spec.md` and `tasks.md` in full
**Constraints**: inference reads the spec directory and nothing else
(FR-006); no continuation flag changes (FR-009); minimal-complexity bias
**Scale/Scope**: two predicates tightened, one annotation added, one drift test

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository ships no `.specify/memory/constitution.md`. The gates below are
substituted from its own documented conventions — `AGENTS.md` and the accepted
records under `docs/architecture/` — and the substitution is recorded in
Complexity Tracking, as the template requires.

- [x] **Validation plan exists.** `uv run pytest -q`, `uv run ruff check
      wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor`, plus the two
      named exercises: the `x` case asserted not-done, and a real spec dir
      asserted still done.
- [x] **Complexity is justified.** No abstraction, dependency or infrastructure
      is added. Two module-level tuples and one helper.
- [x] **Ownership is stated.** wfctl owns *"must a spec carry these sections for
      the step to pass?"*; upstream cannot answer it because a template states
      what a document should contain and has no claim on what a pipeline treats
      as sufficient evidence, and the installed tree cannot because it need not
      exist. Recorded at `docs/architecture/required-sections-are-wfctls.md`.
- [x] **A rule wfctl ships is expressed as a check** (`a-rule-is-expressed-as-a-check`).
      The rule "a spec carries its mandatory sections" is violated visibly in an
      artifact the work already produces, so it is shipped as a predicate rather
      than as prose. Its own test.
- [x] **Inference is re-derived, never carried forward**
      (`session-state-is-re-derived`). The check reads the artifact at read
      time. The event log was considered as a source for clarify's history and
      rejected on this record — see Complexity Tracking.
- [x] **One payload, every view a transformation of it**
      (`pipeline-state-is-one-payload`). The new annotation is a field on the
      step, rendered by each view; no view computes it.
- [x] **Derived files are layered, not edited** (`vendor-upstream-skills`). No
      template is touched. The constants are wfctl's, held against the templates
      by a test.

Re-checked after Phase 1: unchanged. Phase 1 moved clarify's note out of
`reason` and into `annotation` alone, which strengthens the payload gate rather
than straining it.

## Project Structure

### Documentation (this feature)

```text
specs/309-predicate-reads-structure/
├── design.md            # brainstorm output, levels 1 and 3
├── spec.md              # /speckit.specify output
├── plan.md              # this file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit.tasks output — not created here
```

No `contracts/` directory. The feature adds no interface between two processes;
its contract is `_PipelineStep`, which `data-model.md` covers.

### Source Code (repository root)

```text
wfctl/
├── _pipeline.py         # the constants, the helper, the specify/plan/clarify arms,
│                        #   and the rung comment at the head of the file
└── specify/templates/
    ├── spec-template.md     # read by the drift test only, never at inference time
    └── plan-template.md     # same

tests/
└── test_pipeline_sections.py   # new: the x case, the corpus case, the drift check
```

**Structure Decision**: single project, existing layout, no new modules. The
change is local to `_pipeline.py` and one new test file. A separate module for
section matching was rejected — it would be one helper and two tuples behind an
import, and `_pipeline.py` is where every other predicate already lives.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from `AGENTS.md` and `docs/architecture/` rather than read from `.specify/memory/constitution.md` | The repo ships no constitution file | Borrowing another project's gates would be false, and leaving the section empty would make it decorative. The template names this substitution and requires it be recorded here. |
| Inference names section headings owned by `github/spec-kit` | It is the only machine-checkable property of a prose artifact | Extending `wfctl.json`'s `verify`, a per-step sentinel, and reading the template at inference time were each weighed in the level-2 record and rejected there. |
| Clarify's history not read from `events.jsonl` | `session-state-is-re-derived` forbids treating a session file as authoritative for a value derivable from artifacts | The absence of a `## Clarifications` heading is already unambiguous evidence the scan never ran, so the event log would add a forbidden dependency for information the artifact already carries. |
