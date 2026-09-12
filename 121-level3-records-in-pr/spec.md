# Feature Specification: level3 downstream

**Feature Branch**: `121-level3-downstream`
**Issue**: #326 (child of epic #121, scope item 6)
**Created**: 2026-09-10
**Status**: Draft
**Input**: Advance epic #121 scope item 6 — `speckit-plan`, `speckit-tasks` and
`speckit-implement` load the level-3 design records their work is written
against, and `speckit-analyze` reports a task that contradicts one.

## Clarifications

### Session 2026-09-10

- Q: How should a step decide which paths under `## Software design decisions`
  are its record list, given the section may also carry prose — including prose
  naming a level-2 record? → A: Bullet lines only. An entry counts when it is a
  list item of the form `- <path> — <text>`, which is the format the
  `/speckit.brainstorm` wrapper specifies. Prose in the section is commentary and
  contributes no paths, so the one-line "this level was answered with no record"
  statement the wrapper requires cannot be mistaken for an entry, and a level-2
  record mentioned in passing is not loaded as a level-3 one. Encoded as FR-002a.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A pipeline step builds against the decision that was recorded (Priority: P1)

An agent runs `/speckit.plan` on a feature whose brainstorm pass argued out a
structural choice, wrote it down, and committed it. The plan it produces reflects
that choice, because the step read the record before generating anything. The
same holds for `/speckit.tasks` and `/speckit.implement`.

**Why this priority**: This is the loop that is open today. Seven records exist in
this repository and no step in the pipeline reads any of them, so every plan is
written against decisions its author cannot see. Closing it delivers value with
nothing else in this spec built.

**Independent Test**: Run `/speckit.plan` on a feature whose `design.md` lists one
record path. Confirm the step reports that record by path, and that the resulting
`plan.md` reflects the decision the record carries rather than contradicting it.
A run against a feature listing no records has not tested this.

**Acceptance Scenarios**:

1. **Given** a feature whose `design.md` lists one record under `## Software
   design decisions`, **When** `/speckit.plan` runs, **Then** it reports
   `Design records: 1 listed in design.md` followed by that record's path, and
   the record's content is available to the planning workflow.
2. **Given** the same feature, **When** `/speckit.tasks` and
   `/speckit.implement` run, **Then** each reports the same record by the same
   path.
3. **Given** a `design.md` listing three records, **When** any of the three steps
   runs, **Then** all three paths are reported and none outside that list is
   read.

---

### User Story 2 - A reviewer learns that a task contradicts a decision (Priority: P2)

An agent runs `/speckit.analyze`. Beyond the six consistency passes it already
performs, it compares each task against the decisions recorded for this feature
and reports any task that reverses one. The severity depends on whether a human
ratified the decision.

**Why this priority**: This is the half of #121 that makes an autonomously
produced PR arguable rather than merely correct. It depends on nothing in User
Story 1 — analyze reads the records itself — but it is worth less while the plan
those tasks came from was written blind.

**Independent Test**: Add to a feature's `tasks.md` a task that reverses an
`approved` record's `Decision` section. Run `/speckit.analyze`. Confirm a
CRITICAL finding naming that record. Change the record's `status` to `proposed`
and confirm the same task now reports HIGH rather than CRITICAL.

**Acceptance Scenarios**:

1. **Given** a record with `status: approved` and a task that reverses its
   `Decision`, **When** `/speckit.analyze` runs, **Then** it reports a CRITICAL
   finding that names the record by path and quotes the contradicting task.
2. **Given** the same task and a record with `status: proposed`, **When**
   `/speckit.analyze` runs, **Then** it reports a HIGH finding rather than a
   CRITICAL one.
3. **Given** records that no task contradicts, **When** `/speckit.analyze` runs,
   **Then** the scan file's coverage table carries a pass G row reading `Clear`
   with the number of records read.

---

### User Story 3 - A run that recorded nothing is distinguishable from one that never looked (Priority: P3)

Someone reading a PR can tell four states apart: the feature's design pass
recorded a decision, it recorded none, its `design.md` predates the section, or
no design pass ran at all. None of the four is silence.

**Why this priority**: It is #307's property applied one directory over, and it
is independently testable and independently valuable — it holds even if only User
Story 1 ships. It is P3 because it protects against a failure that is invisible
rather than wrong.

**Independent Test**: Run each of the four steps against a feature whose
`design.md` lists no records, then against a feature with no `design.md` at all.
Confirm the two produce different output, and that neither produces none.

**Acceptance Scenarios**:

1. **Given** a `design.md` whose `## Software design decisions` section says a
   level was answered with no record, **When** any of the four steps runs,
   **Then** it reports `Design records: none — design.md records no level-3
   decision`.
2. **Given** a feature directory with no `design.md`, **When** any of the four
   steps runs, **Then** it reports `Design records: unknown — no design.md at
   <FEATURE_DIR>` and does not report the previous state.
3. **Given** either of those states, **When** `/speckit.analyze` runs, **Then**
   the scan file still carries a pass G row, distinguishing `None listed` from
   `No design.md`.

---

### Edge Cases

- **A `design.md` listing a record path that does not exist.** The step reports
  the path as listed and unreadable rather than silently skipping it. A record
  that moved is a broken reference, not an absence.
- **A record path listed outside the repository.** Reported as listed and out of
  tree. `wfctl arch check` is what prevents this at write time; a step that reads
  the list is not the place to re-litigate it, but it must not present the record
  as read.
- **A `## Software design decisions` section that is missing entirely from an
  otherwise present `design.md`.** Reported as `unknown`, not `none`, and not as
  an error. `/speckit.brainstorm` requires the section even when a level was
  answered with no record, because "a missing section reads as a level nobody
  ran" — so its absence says the pass predates the rule, not that it found
  nothing. It is also the majority case: 19 of 27 `design.md` files under this
  repo's spec root have no such heading.
- **A record whose `status` is `superseded` or `rejected`.** Read and reported
  like any other, and a task contradicting it is not a finding. A superseded
  decision is not one a task can violate.
- **A feature carrying enough records to crowd the step's context.** No feature
  in this repository carries more than one; the behavior at scale is an
  assumption, recorded as such rather than specified.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: `/speckit.plan`, `/speckit.tasks`, `/speckit.implement` and
  `/speckit.analyze` MUST resolve the feature directory through
  `wfctl feature-paths` rather than assuming `specs/<branch>/`.
- **FR-002**: Each of the four steps MUST take the applicable record list from the
  paths listed under `## Software design decisions` in that feature's
  `design.md`, and MUST NOT derive it from a filename convention or an issue
  number.
- **FR-002a**: A path counts as an entry only when it appears as a list item of
  the form `- <path> — <text>`. Prose within the section MUST contribute no
  paths, so that the one-line statement the `/speckit.brainstorm` wrapper
  requires when a level was answered with no record is not read as an entry, and
  a level-2 record named in passing is not loaded as a level-3 one.
- **FR-003**: Each of the four steps MUST report the record list it read, by path,
  and MUST NOT summarise or restate a record's content in that report.
- **FR-004**: Each of the four steps MUST distinguish four states in that
  report: records listed, none listed, a `design.md` carrying no such section,
  and no `design.md` present. The last two both report `unknown` and MUST say
  which of the two they found.
- **FR-005**: `/speckit.analyze` MUST perform a seventh detection pass,
  `G · Design-record contradiction`, over the same artifacts its existing six
  passes read, with the record list as an additional input.
- **FR-005b**: Pass G MUST compare a task against the record's `Decision` and
  `Consequences` sections, and MUST NOT compare it against `Direct baseline`,
  `Considered`, or the baseline half of `Diagram`. Those describe what was
  *rejected*, so a task implementing the shape that won reads as contradicting
  them — which would make every correctly implemented record a finding.
- **FR-005a**: Pass G MUST compare **tasks** against records. A `plan.md` element
  that contradicts a record is not a pass G finding — the plan is what the tasks
  were derived from, so a contradiction there surfaces as the tasks that carry
  it, and reporting both would double every finding.
- **FR-006**: Pass G MUST report a task contradicting a record whose frontmatter
  `status` is `approved` as a CRITICAL finding, and one contradicting a record
  whose `status` is `proposed` as HIGH. Both are values `speckit-analyze` step 5
  already defines; the pass MUST NOT introduce a severity outside that scale.
- **FR-007**: Pass G MUST NOT report a task contradicting a record whose `status`
  is `superseded` or `rejected`.
- **FR-008**: A pass G finding MUST name the record by path and quote the task
  that contradicts it.
- **FR-009**: The scan file at `<arch-root>/scans/<issue>-analyze.md` MUST carry
  a pass G row on every run, including runs that read no records, and that row
  MUST distinguish `None listed` from `No design.md`.
- **FR-010**: The pass G row MUST sit between `F · Inconsistency` and the
  `Requirement-to-task coverage` row, which remains the only row carrying a
  percentage.
- **FR-011**: The instructions for FR-001 through FR-010 MUST live in the command
  wrappers under `wfctl/agents/commands/`, and MUST NOT be added to the
  `speckit-plan`, `speckit-tasks`, `speckit-implement` or `speckit-analyze`
  skills, which are spec-kit-derived.
- **FR-012**: The change MUST NOT modify anything under `wfctl/` outside
  `wfctl/agents/commands/` — no predicate, no constant, no CLI verb, and no
  change to the record template or its format.
- **FR-013**: A step MUST report a listed path it could not read as listed and
  unreadable, naming the path, and MUST NOT present it as read or silently omit
  it. Two shapes reach this: a path that does not exist, and a path outside the
  repository. Neither stops the step — `wfctl arch check` is what prevents the
  second at write time, and a step reading the list does not re-litigate it.

## Key Entities

- **Design record**: one level-3 structural decision, a file under
  `<arch-root>/design/`, carrying frontmatter `status` and a `Decision` section.
  Durable, tracked, in the branch diff, and never binding on other features.
- **The record list**: the paths under `## Software design decisions` in a
  feature's `design.md`, written by `idea-refine` at the moment the records were
  written. The feature's own index into the record store.
- **Pass G**: one detection pass inside `/speckit.analyze`, alongside the six
  that exist. Its output is a coverage row and zero or more findings.
- **The scan file**: `<arch-root>/scans/<issue>-analyze.md`, which already
  records what an analyze run covered. Pass G adds one row to its coverage table.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: For a feature listing N records, each of the four steps reports
  exactly those N paths and no others. Counted from the step's own output against
  the `## Software design decisions` section it read.
- **SC-002**: A task deliberately reversing an `approved` record is reported as
  CRITICAL by `/speckit.analyze` on the first run, with no prompting and no
  second pass.
- **SC-003**: The same task against a `proposed` record is reported, at lower
  severity, on the first run. The pass fires on every record in this repository
  today, of which none is `approved`.
- **SC-004**: All four steps produce three distinguishable outputs across the
  three record states, and produce no silent output in any of them.
- **SC-005**: The branch diff touches no file under `wfctl/` outside
  `wfctl/agents/commands/`. Files under `docs/architecture/` and `tests/` are
  expected — the two design records and the scan files are part of this change by
  design. Measured with `git diff --name-only origin/main...HEAD`.
- **SC-006**: `wfctl doctor` reports every layer current after
  `wfctl install-skills`, confirming the four edited wrappers ship.

## Validation Strategy _(mandatory)_

The repository's definition of done, all four, all through `uv run`:

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
uv run wfctl doctor
```

A change under `wfctl/agents/` is not verified by the suite, which checks that
skills ship and cross-reference rather than that they read well. So additionally:

```bash
uv run wfctl install-skills          # then exercise each edited wrapper
```

The exercises are real runs, not readings:

- `/speckit.plan` on a feature whose `design.md` lists a level-3 record —
  confirm the plan loads *that* record, by path, and not a catalog. A run where
  no record was listed has not tested this (US1).
- `/speckit.analyze` against a task written to contradict an `approved` record —
  confirm it reports CRITICAL and names the record; then flip the record to
  `proposed` and confirm the same task reports HIGH (US2).
- Each of the four steps against a feature with an empty list, and against one
  with no `design.md` — confirm three distinguishable outputs (US3).
- Read the resulting `<arch-root>/scans/<issue>-analyze.md` and confirm the pass
  G row sits between `F · Inconsistency` and the coverage percentage.

Tests added to the suite follow the repository's conventions: names are
sentences, docstrings say why the test exists and name the failure it caught, and
anything asserting on console output pins `NO_COLOR`.

## Assumptions

Pre-specify design context loaded from `design.md` in the feature directory that
`wfctl feature-paths` reports — this repository records a `spec_root` outside the
working tree, so that is not `specs/<branch>/`.

- The record list in `design.md` is the applicable set. The alternative — an
  issue-prefixed glob over `<arch-root>/design/` — was specified first and
  falsified during this session on this branch: the worktree is named for epic
  #121 and the record for child #326, so the glob loaded a record belonging to
  #122 and missed the one written here. Recorded in
  `docs/architecture/design-md-indexes-the-records.md`.
- A model reliably detects a prose contradiction between a record's `Decision`
  section and a task description. This is the bet FR-005 through FR-008 rest on,
  and SC-002 is the test that settles it. A clean verdict against a deliberately
  contradicting task falsifies the approach rather than the implementation.
- Reading a feature's records does not exhaust the context available to
  `/speckit.implement`. Unmeasured — no feature in this repository carries more
  than one record.
- `superseded` and `rejected` records are read and reported but never produce a
  finding (FR-007). No record in this repository carries either status yet, so
  this requirement is written from the template's stated lifecycle rather than
  from an observed case.

## Out of Scope

- `wfctl design check` and `wfctl design context`. #121's out-of-scope section
  holds: a command written against a record schema that has survived no real use
  is a migration.
- A machine-readable `invariant:` field on the record format.
- Cross-feature record references — a task in one feature respecting a record
  written for another. No instance exists.
- Making level-3 records binding. `wfctl arch context` continues not to see them.
- The disagreement between `_observe`'s boundary check and `design_block` about
  whether a level-3 record answers the ownership question. Filed as #327; this
  change makes it heavier without resolving it.
- Per-task record citation. Epic item 6's wording implies tasks name the records
  they reference; the list here is feature-scoped. Deferred, not answered.
