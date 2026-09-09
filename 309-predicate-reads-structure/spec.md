# Feature Specification: predicate reads structure

**Feature Branch**: `309-predicate-reads-structure`
**Created**: 2026-09-09
**Status**: Draft
**Input**: Issue #309 — specify and plan carry automatic while proving only that a non-empty file exists

## User Scenarios & Testing _(mandatory)_

### User Story 1 - An unattended run stops on a spec that is not a spec (Priority: P1)

An orchestrated run reaches `specify`, and whatever wrote `spec.md` produced a
file with no sections in it — a truncated write, a failed generation, a bare
`touch`. Today the pipeline reports the step green and moves on to planning
against nothing. The person finds out at review, several steps later, with the
plan and tasks already built on top.

After this change the step reports itself unfinished and names why, and the run
routes back to the command that writes the file.

**Why this priority**: This is the defect. `automatic` means no human is in the
loop, so a wrong verdict here is not caught until the artifacts built on it are.

**Independent Test**: Point inference at a spec directory whose `spec.md` is the
single character `x` and read the `specify` state.

**Acceptance Scenarios**:

1. **Given** a spec directory whose `spec.md` is the single character `x`,
   **When** the pipeline state is read, **Then** `specify` is not `done`, and
   its annotation says the sections are missing.
2. **Given** a spec directory whose `spec.md` carries every mandatory section,
   **When** the pipeline state is read, **Then** `specify` is `done` exactly as
   it is today.
3. **Given** no `spec.md` at all, **When** the pipeline state is read, **Then**
   `specify` is `pending` — unchanged, and distinct from the shapeless case.

---

### User Story 2 - The same, for the plan (Priority: P1)

The identical failure one step later: `plan.md` exists, holds nothing that makes
it a plan, and `plan` reads green.

**Why this priority**: Same rung, same flag, same blast radius. #309 holds the
two together because they share one decision — whether a predicate may name
sections from a template this project vendors rather than owns — and answering
it twice invites two answers.

**Independent Test**: Point inference at a spec directory whose `plan.md` is the
single character `x` and read the `plan` state.

**Acceptance Scenarios**:

1. **Given** a spec directory whose `plan.md` is the single character `x`,
   **When** the pipeline state is read, **Then** `plan` is not `done`.
2. **Given** a `plan.md` carrying every required section, **When** the pipeline
   state is read, **Then** `plan` is `done`.

---

### User Story 3 - A reader can see that the clarification scan never ran (Priority: P2)

A spec that never ran `/speckit.clarify` and has a plan beside it passes the
`clarify` step silently. The step advances, prints one dim glyph, and nothing
says the scan was never performed.

After this change it still advances — the verdict is deliberate and is not being
relitigated here — but it says why in the annotation slot the pipeline already
uses for three other steps.

**Why this priority**: Nothing is unblocked by it and no verdict changes; it
removes a silence. Folded into this change on the maintainer's call, having been
raised as a candidate for its own issue first.

**Independent Test**: Point inference at a spec directory with a `plan.md`, a
`spec.md` carrying no `## Clarifications` heading and no markers, and read the
`clarify` annotation.

**Acceptance Scenarios**:

1. **Given** that directory, **When** the pipeline state is read, **Then**
   `clarify` is `skipped` — unchanged — and carries an annotation saying the
   scan never ran.
2. **Given** a `spec.md` that does carry `## Clarifications` and no markers,
   **When** the pipeline state is read, **Then** `clarify` is `done` with no
   such annotation.

---

### Edge Cases

- A `spec.md` that *documents* a required heading inside a fenced code block or
  an inline span does not thereby satisfy the check. Fenced and inline spans are
  blanked before matching, as they already are for the marker and the
  clarification scan.
- A heading carrying the template's own `_(mandatory)_` suffix satisfies the
  check. The suffix reaches real specs verbatim, so a whole-line match would
  reject the corpus.
- A heading that merely starts with a required name does not satisfy it:
  `## RequirementsTODO` is not `## Requirements`, and neither is
  `## Functional Requirements`.
- A spec directory written before this pipeline existed may carry none of the
  required headings. It reports unfinished. Three such directories exist, all
  closed work on closed branches, and they are left as they are.
- A repository that has never installed the templates still reports correctly:
  the check reads the spec directory and nothing else.

## Clarifications

### Session 2026-09-09

- Q: When a step is held back for missing sections, what should the annotation
  beside it say? → A: Name the missing sections — `missing: Requirements,
  Validation Strategy`. Chosen over a fixed "no sections yet" and over a `2/4`
  tally: the reader fixes the artifact without opening it, and the annotation
  slot already carries variable text (`implement` renders `12/12 done`).
- Q: Should the drift check fail when the template gains a mandatory section the
  constants do not require, as well as when it renames one? → A: Yes, both
  directions — the constant list and the template's mandatory set must be
  equal. Not asked: the rename direction is the dangerous one and equality
  catches it, while the addition direction costs only a build failure that
  forces a deliberate decision. Recorded here rather than put to the reader
  because the safer answer also subsumes the other.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The `specify` step MUST report `done` only when `spec.md` carries
  every section the specification template marks mandatory.
- **FR-002**: The `plan` step MUST report `done` only when `plan.md` carries
  every section this project requires of a plan.
- **FR-003**: A file that exists but carries none of its required sections MUST
  report `in_progress`, not `pending` — the artifact exists, and reporting
  otherwise would direct the writer to start over rather than continue.
- **FR-004**: A step held back by missing sections MUST name the sections it
  did not find, in the annotation a reader already sees beside the step.
- **FR-005**: The list of required sections MUST live in this project's own
  code, and a check MUST fail the build when that list and the shipped template
  disagree — whether the template renamed a section or gained one. The two
  artifacts are not symmetric and the check is not either: the specification
  template declares its mandatory sections, so the check compares against that
  declaration; the plan template declares none, so it compares against the
  headings the template actually carries.
- **FR-006**: Inference MUST read the spec directory and nothing else. It MUST
  NOT depend on the templates being installed in the repository under
  inspection.
- **FR-007**: Section matching MUST tolerate trailing text on the heading line
  and MUST NOT match a heading that merely begins with a required name.
- **FR-008**: The `clarify` step MUST carry an annotation naming why it passed
  when it passes on the grounds that a plan already exists.
- **FR-009**: No step's continuation flag changes, and no step's state changes
  for any artifact that satisfies its sections today.

## Key Entities _(include if feature involves data)_

- **Required section list**: the set of headings an artifact must carry for its
  step to pass. One list per artifact kind, owned by this project, checked
  against the shipped template.
- **Step annotation**: the short line rendered beside a step, already used by
  three steps to say why they hold or what they counted.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A spec directory whose `spec.md` and `plan.md` are each the single
  character `x` leaves both steps not `done`. This case reports both green
  today.
- **SC-002**: Every one of the 22 spec directories written by this pipeline
  reads exactly as it does today — no step changes state.
- **SC-003**: A reader seeing a held step learns which sections are missing
  from the step's own line, without opening the artifact.
- **SC-004**: A renamed heading in a future template pull fails this project's
  own build, rather than changing a verdict silently in a consuming repository.
- **SC-005**: A repository that has never installed the templates reports the
  same verdicts as one that has.

## Validation Strategy _(mandatory)_

- `uv run pytest -q` — the suite, including new cases for SC-001 and SC-002 and
  the drift check for SC-004.
- `uv run ruff check wfctl/ tests/`
- `uv run mypy wfctl/`
- `uv run wfctl doctor`
- The positive exercise, which a negative-only run does not cover: inference run
  against a real spec directory from the durable spec root, asserted still to
  read `done` at `specify` and `plan`.

## Assumptions

- Pre-specify design context loaded from `design.md` in this feature directory.
- The specification template's four `_(mandatory)_` headings are the right
  required set for `spec.md`. Verified against the corpus: 22 of 25 carry all
  four, and the three exceptions predate this pipeline.
- The plan template marks nothing mandatory, so its five headings are this
  project's own choice. Verified: 23 of 24 real plans carry all five.
