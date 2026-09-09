# Feature Specification: one predicate signature

**Feature Branch**: `314-one-predicate-signature`
**Created**: 2026-09-09
**Status**: Draft
**Input**: Issue #314 — the eight pipeline stage predicates share no signature; give them one, decide what holds them, and either split `_pipeline.py` along the three jobs its docstring names or record why they belong together.

## Clarifications

### Session 2026-09-09

- No critical ambiguities detected.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Change one step's evidence without touching the others (Priority: P1)

A maintainer picks up one of the four open issues that each change what a single
pipeline step proves. They open the file, find that step, change what it reads,
and stop. The diff names one step and the reviewer can see which.

Today the same work means editing a 201-line function whose other 190 lines
belong to the seven steps they did not touch, and a reviewer reading the diff
cannot tell the changed step from its neighbours without reading all of it.

**Why this priority**: This is the cost the issue was opened over, and four
queued issues (#308, #309, #240, #299) each pay it. Nothing else here delivers
value on its own — the invariants and the module split are consequences of this
story, not alternatives to it.

**Independent Test**: Change what one step proves on a scratch branch and read
the diff. The test passes if the changed hunk is confined to one function and
names one step.

**Acceptance Scenarios**:

1. **Given** the eight steps decide their state through one shared signature,
   **When** a maintainer changes what a single step accepts as evidence,
   **Then** the diff touches that step's function and no dispatching code.
2. **Given** a maintainer is looking for how one named step decides its state,
   **When** they search the codebase for that step's name,
   **Then** they find both the step's row in the table and its predicate.

---

### User Story 2 - Tell a restructure from a behaviour change (Priority: P2)

A reviewer reads a change to the pipeline and can answer, without running it,
whether any step now reaches a different verdict. What each step proves is
unchanged by this feature, and the reviewer must be able to confirm that rather
than take it on trust.

**Why this priority**: It is the reason #300 audited without fixing and the
reason this change is separable from the four that follow it. It rides along with
story 1 rather than needing its own work, but it is the property that makes the
change reviewable and it is checked separately.

**Independent Test**: Capture what `wfctl status` renders at each of the eight
steps before the change, and diff it against the same eight after. The test
passes on a byte-identical result.

**Acceptance Scenarios**:

1. **Given** a branch sitting at any one of the eight steps, **When** a user runs
   `wfctl status` before and after this change, **Then** the step's glyph,
   annotation and blocked-reason text are identical.
2. **Given** the one step that resolves an inconclusive reading itself today,
   **When** it is routed through the shared rule for inconclusive evidence,
   **Then** the verdict it reaches is unchanged in every case the existing tests
   cover.

---

### User Story 3 - A step cannot be half-declared (Priority: P3)

A maintainer adds a ninth step, or edits an existing row, and forgets to say how
that step decides its state. They learn about it before the commit, from the type
checker the project already runs, rather than from a user whose pipeline reached
that step.

**Why this priority**: It is the property that decides where the predicates are
held rather than a goal in itself, and it costs nothing extra once story 1 is
built. Listed separately because it is checked separately.

**Independent Test**: Add a step declaration missing its predicate and run the
project's type check. The test passes if the check fails and names the row.

**Acceptance Scenarios**:

1. **Given** a step declared without a way to decide its state, **When** the
   project's type check runs, **Then** it fails and names the incomplete
   declaration.
2. **Given** a step's decision returns a state name outside the four the pipeline
   recognises, **When** the project's type check runs, **Then** it fails.

---

### Edge Cases

- **A step needs evidence the shared bundle does not carry.** The bundle grows a
  field; the signature does not change per step. If the new evidence is expensive
  to gather — a network call, a large parse — the field is gathered on demand
  rather than for every step on every run, because the bundle is assembled before
  any step is reached.
- **Routing the one divergent step through the shared inconclusive-evidence rule
  changes what it concludes.** Then the routing stops and is reported as a
  finding. Changing that step's verdict belongs to a different issue, and a
  restructure that also moved it would be unreviewable.
- **A step's annotation is not the same string as its reason.** One step prefixes
  a task tally to its reason. The shared return carries the state and the reason;
  whatever composes the tally reads evidence the bundle already holds.
- **A branch with no spec directory at all.** Every step reads `pending` and no
  predicate runs, exactly as today.
- **Two steps disagree about the same evidence.** Not reachable — each step reads
  the shared bundle and decides only its own state; nothing lets one step's
  verdict change another's.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: All eight pipeline steps MUST decide their state through one
  signature, taking the same evidence bundle and returning the same pair of
  values.
- **FR-002**: The decision for each step MUST return both the state and the
  reason it is not complete, so that a caller rendering the reason and a caller
  testing whether the step is blocked read the same value.
- **FR-003**: A step's declaration MUST carry its decision procedure, and a
  declaration missing one MUST fail the project's type check rather than a run.
- **FR-004**: A step's state MUST be one of the four names the accepted record
  `pipeline-state-is-one-payload` lists, enforced by the type checker rather than
  by convention.
- **FR-005**: Every step that reaches an inconclusive reading MUST resolve it
  through the shared rule that owns whether inconclusive evidence blocks, rather
  than deciding for itself.
- **FR-006**: What each step accepts as evidence, and the verdict it reaches from
  it, MUST be unchanged by this feature.
- **FR-007**: No step's continuation flag — whether the pipeline may advance past
  it unattended — MUST change.
- **FR-008**: Searching the codebase for a step's name MUST continue to find how
  that step decides its state, without an intervening lookup table of strings.
- **FR-009**: The evidence bundle MUST be assembled from reads the pipeline
  already performs, adding no new read on a path that did not perform one.
- **FR-010**: The predicates MUST be separable from the code that walks the steps,
  either as their own module or with a recorded reason why they belong together.

## Key Entities

- **Step declaration**: what the pipeline knows about one step — the command that
  advances it, whether the pipeline may pass it unattended, and how it decides its
  own state. All three named rather than positional.
- **Evidence bundle**: everything the eight decisions read, gathered once per
  inference. Today: the spec directory, the repository root, the specification's
  text with code spans removed, whether clarification markers stand, the tasks
  list's text, and whether any task is still open.
- **State**: one of four names — complete, in progress, not started, passed by.
  A closed set, and the only values a decision may return.
- **Predicate**: the codebase's name for a step's decision procedure — the
  three terms are the same thing, and this entry exists so the spec and the
  plan can be read against each other.
- **Reason**: why a step is not complete, or nothing. Rendered by views; read as
  truthy by callers that only need to know whether the step is blocked.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: At every one of the eight steps, what a user sees when they ask for
  the pipeline's position is byte-identical before and after the change —
  including each blocked step's reason and each step's annotation.
- **SC-002**: Changing what one step proves touches exactly one decision
  procedure and no dispatching code, measured on the diff.
- **SC-003**: A step declared without a decision procedure is rejected before the
  change is committed, by a check the project already runs on every change.
- **SC-004**: Every step that can reach an inconclusive reading resolves it
  through the shared rule — eight of eight, where seven of eight do today.
- **SC-005**: The function that walks the steps contains no branch on a step's
  name. The one annotation that is not simply the step's reason — a task tally —
  is carried by the decision that computes it rather than composed in the walk.
- **SC-006**: A reader looking for one step's decision reaches it in one hop from
  the step's name, in either direction.

## Validation Strategy _(mandatory)_

- `uv run pytest -q` — the suite, which asserts on rendered output and on step
  states.
- `uv run ruff check wfctl/ tests/`
- `uv run mypy wfctl/` — the check that carries FR-003 and FR-004. It must fail
  on a deliberately incomplete step declaration, and that failure is exercised
  rather than assumed.
- `uv run wfctl doctor` — drift between the installed tree and the source.
- **The eight-step render diff, which the suite cannot do.** Capture what `wfctl
  status` renders at each of the eight steps before the first edit; diff after.
  The suite asserts on step states and on console output, so a change that broke
  the shape while preserving every assertion would pass it. This is the check
  that carries SC-001, and it is a saved artifact rather than a recollection.
- The existing tests over unkeyed delivery rows, which pin the divergent step's
  reason text and its open/closed split — the evidence for FR-006 at the one step
  whose routing changes.

## Assumptions

- Pre-specify design context loaded from `design.md` in this branch's spec
  directory. The formal requirements above reflect decisions already made there
  and in `docs/architecture/design/314-the-step-table-holds-the-predicate.md`.
- The evidence bundle's six values cover all eight decisions. If one needs a
  seventh, the bundle grows a field — the signature is unaffected. Recorded as an
  assumption rather than a requirement because it is a claim about today's eight
  arms, checked by extracting them.
- Where the task tally is composed — inside the one step's decision or in the
  loop that renders it — is left to implementation. Both satisfy FR-002; the
  choice is whichever leaves the walking function shorter, and it changes no
  observable behaviour.
- Which module holds the step declarations, once the decisions move out, is left
  to implementation and settled by whichever arrangement has no circular import.
  FR-010 requires the separation, not a particular side for the table.
- No boundary is drawn or moved by this feature. Declared to the pipeline with
  `wfctl arch none`; the reason is recorded on the branch.
