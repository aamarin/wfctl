# Implementation Plan: record leads with drawing

**Branch**: `109-record-leads-with-drawing` | **Date**: 2026-09-16 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/109-record-leads-with-drawing/spec.md`

## Summary

A record that carries no drawing cannot be accepted. The author declares which of
three kinds the drawing is, in the frontmatter; wfctl checks that a drawing is
there and that the declared kind is one it knows, and never decides which kind
the decision needed.

Technically this is one field on `Record`, one generalised section scanner, and
one function — `accept_blockers` — that `acceptable` and `accept` both read, so
a listing never offers a record whose own suggested command then fails. The
label-agreement warning joins the record findings `doctor` already prints, at a
mechanism chosen by measurement over this repository's corpus rather than by
argument (research R-004).

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: none added. `typer` and `rich` at runtime, unchanged —
the label check is a line scan, and `109-traceability-is-label-agreement` rejects
a mermaid parser by name
**Storage**: markdown files under `wfctl arch-root` (default `docs/architecture/`).
No database, no cache, no index — every value is re-derived per read
**Testing**: `uv run pytest -q`, plus a template-drift test following
`tests/test_pipeline_sections.py`, plus the manual pass in `quickstart.md`
**Target Platform**: CLI, wherever wfctl is installed
**Project Type**: single project — a CLI plus a package-data skills tree
**Performance Goals**: none beyond the existing read. `Record.body` is already in
memory; both new checks are one pass over it
**Constraints**: ruff rule set stays `E4,E7,E9,F` (#14); mypy with
`disallow_untyped_defs`; no new runtime dependency; minimal-complexity bias
**Scale/Scope**: 40 records in this repository, 4 of them carrying a
`## Boundary`. Every repository that installs the skills, by the same rule
(FR-013)

## Design records this feature was written against

Resolved from `design.md`'s `## Software design decisions` section, per
`reading-design-records`.

```
Design records: 1 listed in design.md
  docs/architecture/design/109-traceability-is-label-agreement.md
```

Binding at level 2, named in that section's prose rather than listed as entries —
they are level-2 records and in force by their own tier:

- `docs/architecture/the-author-declares-the-diagram-kind.md`
- `docs/architecture/the-drawing-is-required-at-acceptance.md`

All three are `proposed`; under this feature's `auto_approve` the approval is the
PR review.

**One of them is falsified by Phase 0.** `109-traceability-is-label-agreement`
decides that "every label in the `## Boundary` block must appear somewhere in
`## Owns truth` or `## Decision`", and its own Verification names the test that
would sink it. Run over the corpus, that rule reports **43 findings across 4
records** — every label — because authors draw in phrases and prose does not
repeat a phrase. The record's `Assumed` section predicted this shape and the
measurement confirms it.

The decision is not reversed. Its *mechanism* is narrowed to the one that passes
its own gate: a label is reported when **no content word of it appears anywhere
else in the record**, which produces 1 finding over the same 4 records against
SC-004's ceiling of 2. Research R-004 carries the three mechanisms and their
counts. The record needs a Log line recording the narrowing; that is a task, not
a silent edit.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The gates below are
substituted from its own documented conventions — `AGENTS.md`'s definition of
done and the accepted records `wfctl arch context` projects — and the
substitution is recorded in Complexity Tracking, per the template's own rule that
a gate borrowed from another project is false.

- [x] **Validation plan exists.** `uv run pytest -q`, `uv run ruff check
      wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor` — AGENTS.md's
      whole bar. Plus a template-drift test (FR-010), a refusal test per
      acceptance scenario, a test that an accepted record with no drawing is
      never read, and the manual skills pass in `quickstart.md`.
- [x] **Complexity is justified.** No new dependency, no new module, no new
      command. One field, one constant, one generalised helper, two functions.
      The one thing that could have been a dependency — a mermaid parser — is
      rejected by the level-3 record and by measurement: the check reads node
      labels, and a grammar parser earns it no property.
- [x] **Ownership is stated.** The author owns "which kind does this decision
      need" (`the-author-declares-the-diagram-kind` — wfctl cannot compute it
      without classifying English). wfctl owns "may this record be accepted"
      (`the-drawing-is-required-at-acceptance` — it already answers it from two
      facts and this adds a third of the same kind). Nobody owns "is the drawing
      correct"; the feature says so rather than implying a check.

**In force and directly binding:**

| Record | How this plan satisfies it |
|---|---|
| `a-rule-is-expressed-as-a-check` | a missing drawing is visible in the record, so it ships as a refusal and not as a line in a skill |
| `required-sections-are-wfctls` | `DIAGRAM_KINDS` is wfctl's, beside the code that reads it, held against the shipped template by a test (FR-010) |
| `knowledge-placement` | the kind vocabulary is a constraint on the system → `docs/architecture/`; how to pick one is guidance for the author → the skill |
| `layer-model` | `wfctl/agents/skills/…` is the source; `.agents/` and `.claude/` are generated and never hand-edited |
| `vendor-upstream-skills` | `architecture-decisions` is wfctl's own skill, not derived, so an in-place edit is correct there |
| `pipeline-state-is-one-payload` | untouched. Nothing here reaches the pipeline payload |

**Post-Phase-1 re-check**: unchanged. Phase 1 added no abstraction the gate above
did not already cover, and the one place it could have — a type for blockers —
was resolved to a list of strings in R-002 for exactly that reason.

## Project Structure

### Documentation (this feature)

```text
specs/109-record-leads-with-drawing/
├── plan.md                      # This file
├── research.md                  # Phase 0 — R-001 … R-009
├── data-model.md                # Phase 1 — Record.diagram, Drawing, blockers, VR-006/007
├── quickstart.md                # Phase 1 — the end-to-end pass, including the manual half
├── contracts/
│   ├── record-format.md         # the frontmatter key and the required section
│   └── cli.md                   # what accept, the listing and doctor print
├── spec.md
├── design.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
wfctl/
├── _arch.py                     # DIAGRAM_KINDS; Record.diagram; _section_bounds;
│                                # _drawing; _labels; accept_blockers; acceptable;
│                                # accept; validate (VR-006, VR-007)
├── _md.py                       # unchanged — walk_lines already reports fence interiors
├── cli.py                       # arch accept: the refusal wording and the kind table
└── agents/skills/architecture-decisions/
    ├── SKILL.md                 # which kind suits which decision (FR-012)
    └── record-template.md       # diagram: in frontmatter; Boundary no longer optional

tests/
├── test_arch_diagram.py         # new — the declared kind, VR-006, FR-002/003
├── test_arch_accept_drawing.py  # new — the refusals, the listing, the frozen accepted
├── test_arch_labels.py          # new — VR-007, and the corpus run behind SC-004
└── test_arch_sections.py        # new — DIAGRAM_KINDS against the shipped template
```

**Structure Decision**: single project, existing layout, no new module.
`wfctl/_arch.py` already holds parse, validate, supersede and accept, and every
addition here is one of those four. A separate `_diagram.py` would split
`accept_blockers` from the `_set_status` guard it has to agree with, which is the
divergence `acceptable`'s docstring exists to prevent.

## Phase 2 — implementation order

Each story is independently shippable in the spec's own terms, and the order is
its priority order. Nothing below crosses a story boundary.

1. **US2 first, though it is P2.** `Record.diagram`, `DIAGRAM_KINDS`, VR-006, the
   template-drift test. The P1 refusal needs the kind to name it (FR-005), so
   shipping US1 first means writing its refusal twice.
2. **US1.** `_section_bounds`, `_drawing`, `accept_blockers`, `acceptable`,
   `accept`, the CLI wording. This is the feature.
3. **US2's author-facing half.** `record-template.md` and
   `architecture-decisions/SKILL.md` — the kind table (FR-012), and `## Boundary`
   promoted from optional to required (FR-009). Then `install-skills` and the
   manual pass, because a green suite is not evidence about a skills change.
4. **US3.** `_labels`, VR-007, and the corpus run. Its gate is SC-004 and Phase 0
   already measured it at 1 of an allowed 2 — but on 4 records, so the run is
   repeated at implementation against whatever the corpus holds then.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from AGENTS.md and the accepted records | No `.specify/memory/constitution.md` exists in this repository | Borrowing another project's constitution would state gates nothing here is built under; leaving the section empty would let the plan pass a check it never ran |
| `SC-004`'s corpus corrected from 22 records to 4 | Only 4 records carry a `## Boundary`; the 22 carry fenced blocks under `## Context` and `## Decision`, which are not drawings under this feature's own definition (research R-006) | Widening the check to any fence anywhere would make prose examples and code samples into drawings, which clarification Q2 settled against |
| `109-traceability-is-label-agreement`'s mechanism narrowed | The record's stated rule reports every label in the corpus — 43 findings over 4 records — and its own Verification says that means the baseline was right | Shipping the rule as written fails SC-004 by a factor of twenty; dropping the story loses the issue's traceability item when a mechanism that passes the gate exists |

## Open, and carried forward

- **`component` versus `data-flow` is unvalidated.** `design.md` proposed
  validating the three kinds against the 22 existing drawings; research R-006 is
  why that test cannot run. Four records is evidence of nothing. If the two
  collapse later it is a change to `DIAGRAM_KINDS` and to
  `the-author-declares-the-diagram-kind`, and to nothing else here.
- **The label check reads bracketed and quoted labels only.** An ASCII drawing
  yields none and passes with nothing compared. Stated in `contracts/cli.md` as a
  limit rather than left to be discovered.
- **Eleven — now twenty-four — proposed records carry no drawing.** They are held
  deliberately (`proposed-records-held-for-end-to-end-validation`) and gain
  drawings when someone accepts them. Not this feature's scope, and the count
  moved because the corpus grew, not because anything drifted.
