# Feature Specification: flip clarify and analyze

**Feature Branch**: `325-flip-clarify-and-analyze`
**Created**: 2026-09-10
**Status**: Draft
**Input**: Issue #325 — flip `clarify` and `analyze` to automatic; the artifacts that earn it have shipped, and nothing flipped the flags.

## Clarifications

### Session 2026-09-10

- Q: After the flip, does anything bound an unattended run re-entering `/speckit.clarify` on a spec whose markers the previous pass failed to resolve? -> A: No guard here. Re-entry is the mechanism, and the unbounded case is `speckit-orchestrate`'s gap rather than this step's - filed separately.
- Q: SC-004 claims one production file and one test file, but the table assertion and the per-state assertions belong in different test modules. Which way? -> A: Two test files; SC-004 relaxed to name both.
- Q: How should the test that pins all eight continuation flags change? -> A: Edited in place with an extended docstring, and renamed shorter - `test_the_table_pins_every_steps_unattended_flag`.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - An unattended run reaches the end of the pipeline (Priority: P1)

An agent running `/speckit.orchestrate` with nobody watching advances through
every step. Today it stops twice — once when `clarify` becomes current, once when
`analyze` does — and prints a command for a human to run. After this change it
runs both itself.

**Why this priority**: This is the whole feature. It is also the last thing
standing between the repository and #147's acceptance test, which is an
unattended run from a clean start to an open pull request.

**Independent Test**: Set a feature's artifacts so `clarify` is the current step,
run `wfctl status --json`, and read `auto`. It reads `true`. Repeat with
`analyze`.

**Acceptance Scenarios**:

1. **Given** a feature whose `spec.md` exists with no `## Clarifications` section
   and no clarification markers, **When** the pipeline payload is built, **Then**
   `next_command` is `/speckit.clarify` and `auto` is `true`.
2. **Given** a feature whose `spec.md` still carries clarification markers,
   **When** the pipeline payload is built, **Then** `next_command` is
   `/speckit.clarify` and `auto` is `true` — the markers are what re-entering the
   step resolves, and no reason is attached that would override the table.
3. **Given** a feature whose `tasks.md` is complete and whose
   `checklists/analysis-report.md` does not exist, **When** the pipeline payload
   is built, **Then** `next_command` is `/speckit.analyze` and `auto` is `true`.
4. **Given** any of the above, **When** `speckit-orchestrate` reads the payload,
   **Then** it emits `EXECUTE_COMMAND` for the step rather than printing
   "Next: run … when ready."

---

### User Story 2 - A blocked step still holds the run (Priority: P1)

An unattended run must not walk past a gate whose question nobody answered. That
guard is above the table and is unchanged by this feature, but it has to keep
holding after the flip or the flip has weakened the design gate.

**Why this priority**: Same priority as story 1 because it is the property that
makes story 1 safe. A flip that also removed a gate would be a different and much
larger change.

**Independent Test**: Build a payload for a feature whose `brainstorm` step is
blocked on an unanswered boundary question. `auto` reads `false`, even though
`brainstorm` is `automatic` in the table.

**Acceptance Scenarios**:

1. **Given** a step that is current and carries a blocking reason, **When** the
   payload is built, **Then** `auto` is `false` regardless of the step's table
   value.
2. **Given** a blocked `implement`, **When** the payload is built, **Then**
   `next_command` is `wfctl verify` and `auto` is `false`.

---

### User Story 3 - A reviewer can see what each step covered (Priority: P2)

A reviewer opening a pull request produced by an unattended run can read what
`clarify` and `analyze` examined and found, because both steps commit a scan file
into the repository.

**Why this priority**: P2 because it is already true — #307/#320 shipped it. It
is stated here because it is the evidence this feature's central claim rests on,
and a spec that asserts sufficiency without naming what makes it sufficient is
asserting it from nowhere.

**Independent Test**: Open `docs/architecture/scans/` on `main` and read a
`<issue>-clarify.md`. It names the verdict, what was scanned, the coverage per
category, each finding, and for each question the options rejected and why each
lost.

**Acceptance Scenarios**:

1. **Given** a completed unattended `clarify` pass, **When** a reviewer opens the
   pull request, **Then** the diff contains a scan file distinguishing a pass
   that found nothing from a pass that never ran.

---

### Edge Cases

- **A step is `skipped` rather than `done`.** `clarify` reports `skipped` for a
  spec that predates the gate — one where `plan.md` already exists. A `skipped`
  step is never the current step, so the continuation value never reaches a
  reader, and the flip changes nothing about this case.
- **`analyze` when `tasks.md` is closed and no report exists.** `analyze`'s
  predicate has no `skipped` arm; it reads `pending`, becomes current, and after
  the flip the run executes `/speckit.analyze`. That is the intended behavior —
  the step has not run.
- **Both steps reached in one unattended pass.** Each is evaluated independently
  from the same table; there is no interaction between the two flags.
- **A re-entered `clarify` on a spec whose markers still stand.** Two steps read
  `in_progress` in that state, `specify` and `clarify`, and the pipeline picks
  `clarify` - deliberately, because routing back to `/speckit.specify` would
  rewrite `spec.md` from the template and destroy the Clarifications section.
  Re-entry rescans the current spec, so a surviving marker becomes a candidate
  question again. What re-entry does not do is guarantee resolution, and nothing
  in `speckit-orchestrate` bounds the repetition. Out of scope here; see the
  Clarifications section.
- **A wfctl too old to know the question.** Out of scope: the flag is read from
  the same build that defines the table, so a version skew cannot produce a
  disagreement between them.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The step table MUST record `clarify` as automatic.
- **FR-002**: The step table MUST record `analyze` as automatic.
- **FR-003**: The pipeline payload MUST report `auto` as `true` when `clarify` is
  the current step and carries no blocking reason.
- **FR-004**: The pipeline payload MUST report `auto` as `true` when `analyze` is
  the current step and carries no blocking reason.
- **FR-005**: The payload MUST continue to report `auto` as `false` for any
  current step that carries a blocking reason, regardless of that step's table
  value.
- **FR-006**: The `auto` value MUST continue to be computed at exactly one site.
  No per-step branch may be added for `clarify` or `analyze`.
- **FR-007**: The flip MUST NOT be conditional on branch state, on any of the four
  facts the payload carries, or on any runtime value. It is a property of the
  step, decided once.
- **FR-008**: The single test that pins every step's continuation value MUST be
  updated in place to the new table and MUST carry a docstring naming this
  change, so that a future flip is caught by the same tripwire. It remains one
  test over one dict - a reader must still be able to see all eight flags at
  once.
- **FR-009**: No step other than `clarify` and `analyze` may change its
  continuation value.

## Key Entities

- **Step table**: the record, one row per pipeline step, of the command that
  advances the step and whether an unattended run may proceed past it once
  finished. It is the sole authority for the second value.
- **Continuation value**: one of *automatic* or *review required*. Named rather
  than boolean so that a change to one is greppable and reviewable. It carries
  three names across three surfaces, and each is correct where it appears: the
  **continuation value** in the table and in this document, `auto` on the wire
  where a consumer reads the payload, and the **unattended flag** in prose and
  test names written for a reader rather than for the code. Documents in this
  feature use the first; a fourth name is drift.
- **Blocking reason**: text a step's predicate attaches when the step has not
  finished. Its presence overrides the table's continuation value to *review
  required*. Neither `clarify` nor `analyze` sets one in any reachable state.
- **Scan file**: the per-step, per-issue record committed into the repository
  saying what a review step covered and what it found. It is the evidence that
  makes automatic continuation defensible for these two steps.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: The number of pipeline steps that stop an unattended run on a
  finished step falls from two to zero.
- **SC-002**: An unattended pipeline run reaching `clarify` and `analyze`
  executes both without emitting a prompt for a human.
- **SC-003**: Every reachable state of both steps is exercised by a test that
  asserts the reported continuation value.
- **SC-004**: The change touches exactly one production file, `wfctl/_pipeline.py`,
  and no new test module.

  **This criterion was written predicting two test files and the answer was
  five.** Recorded here rather than corrected away, because the gap is the
  finding: the continuation value was pinned in six places across five modules,
  not in the one dict the design claimed, and only running the suite found the
  other five. The file *count* was never the property worth asserting — "no new
  module" is, because a new module is what would fragment the coverage. The count
  is kept as a statement of what was predicted and what was true, so a reader of
  this spec learns the thing the author did not know.
- **SC-005**: The stored payload snapshot requires no regeneration, because it
  pins step verdicts and this change moves no verdict.

## Validation Strategy _(mandatory)_

The repository's four commands, all four, all green:

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
uv run wfctl doctor
```

Story-specific checks beyond the suite:

- Assert the continuation value for `clarify` and `analyze` directly, at the
  table, so a future flip fails a test rather than passing silently (FR-001,
  FR-002, FR-008, FR-009).
- Assert the reported `auto` for each reachable current-state of both steps —
  `clarify` pending, `clarify` with markers standing, `analyze` pending —
  covering FR-003 and FR-004.
- Assert that a blocked step still reports `auto` false, which the existing
  `brainstorm` test already covers and which must remain green (FR-005).
- Confirm by inspection that no per-step branch was added, and that the payload
  snapshot is unchanged (FR-006, SC-005).

The check this suite cannot make is the one #325's own definition of done names:
an actual unattended `/speckit.orchestrate` run from a clean start on a real
issue, reaching a pull request with no human input. A run that stopped at a gate
has not tested this, and neither has a run where a human answered a prompt. That
run is blocked on #331 — `analyze` step 8 still asks whether to apply
remediation, and unattended no rule says what to apply and what to file.

## Assumptions

- Pre-specify design context loaded from `specs/325-flip-clarify-and-analyze/design.md`.
- The judgment that both steps' artifacts are sufficient evidence to pass without
  a human is made by a person, recorded in issue #325, and is not derivable from
  the code. It is the assumption this whole specification rests on.
