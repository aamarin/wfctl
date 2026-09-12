# Feature Specification: orchestrate loop bound

**Feature Branch**: `332-orchestrate-loop-bound`
**Created**: 2026-09-10
**Status**: Draft
**Input**: Issue #332 — speckit-orchestrate has no loop bound; a step that cannot make progress runs until something external stops it.

## Clarifications

### Session 2026-09-10

- Q: When the record of past passes holds a line that cannot be read, does the bound treat the run as still progressing or as stalled? → A: Still progressing — an unreadable line is skipped and counting continues around it.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - An unattended run that cannot progress stops and says so (Priority: P1)

A developer leaves a run working through the pipeline overnight. One step needs a
decision only a person can make, so every pass through it leaves the work exactly
where it found it. Instead of repeating that step until someone interrupts it, the
run stops after three such passes and reports which step repeated and what did not
change, then hands the work back.

**Why this priority**: This is the defect. Without it an unattended run has no
terminal state other than external interruption, and a run that cannot finish is
indistinguishable from one still working.

**Independent Test**: Drive a step into a state where re-entering it changes
nothing, let the run proceed unattended, and confirm it halts on the third pass
naming that step — rather than continuing.

### User Story 2 - A run doing real work is never stopped (Priority: P1)

A step legitimately takes several passes and advances a little each time —
resolving some of the open questions in a document, or completing some of the
listed tasks. The run continues through all of them without interference.

**Why this priority**: Equal to the first. A bound that halts working automation
is worse than no bound, because it fails at the hour nobody is watching and its
failure looks like the feature working.

**Independent Test**: Drive a step across three consecutive passes that each
advance the work partially, and confirm the run does not stop.

### User Story 3 - A stopped run is still legible the next day (Priority: P2)

Someone returns to a branch after the run's output has scrolled away, or opens it
in a new session, and asks where the work stands. They are told the run stopped,
on which step, and what did not change — not that the work is simply unfinished.

**Why this priority**: Below the first two because a run that stops correctly is
already better than one that does not. Above nothing, because a stop visible only
in lost output leaves the same ambiguity the feature exists to remove.

**Independent Test**: Trigger a stop, discard the run's output, ask for the
branch's status in a fresh session, and confirm the stop and its cause are
reported.

### Edge Cases

- A branch whose history was written by an older version of the tool, which
  recorded each pass differently. Counting must not be distorted by the older
  shape.
- A step that repeats but whose evidence is not among the artifacts the pipeline
  reads. Such a step is outside the bound; this is accepted and recorded, not
  silently assumed away.
- A run whose first pass is also its last because the work completes. The bound
  must never fire on a single pass.
- A branch resumed days later, where earlier passes are in the record but belong
  to a different sitting. Consecutive passes are what count, not passes in total.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST count consecutive passes through the same pipeline
  step within a run.
- **FR-002**: The system MUST treat a pass as having made progress when the
  artifacts the pipeline reads changed during it, and as having made none when
  they did not.
- **FR-003**: The system MUST stop the run after three consecutive passes through
  one step that made no progress.
- **FR-004**: The system MUST reset the count whenever a pass makes progress, so
  that only consecutive unproductive passes accumulate.
- **FR-005**: A run stopped by this bound MUST report which step repeated and what
  did not change.
- **FR-006**: A run stopped by this bound MUST hand the work to a person rather
  than continuing to the next step.
- **FR-007**: The verdict that a run has stopped MUST remain available after the
  run's output is gone, including to a later session on the same branch.
- **FR-008**: The count MUST survive the loss of the working agent's memory
  within a run, including a cleared or compacted conversation.
- **FR-009**: The system MUST NOT require any record written solely to remember
  that a step has already been attempted.
- **FR-010**: Counting MUST tolerate records of past passes written by earlier
  versions of the tool without over- or under-counting.
- **FR-011**: A record of a past pass that cannot be read MUST be skipped rather
  than counted as a stalled pass, so that a damaged record slows the bound rather
  than halting a run that is working.

### Key Entities

- **Pass**: One traversal of a single pipeline step by a run. Carries which step
  it was and a summary of what the pipeline's artifacts held at the time.
- **Progress**: The difference between two passes' artifact summaries. Equal
  summaries mean no progress.
- **Stall**: Three consecutive passes through one step with no progress between
  them. The run's terminal state, distinct from completion.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: An unattended run whose current step cannot progress stops within
  three passes of that step, rather than continuing indefinitely.
- **SC-002**: A run whose step advances the work on each pass completes without
  being stopped, across at least three consecutive partial advances.
- **SC-003**: Every run stopped by the bound names the repeated step and the
  evidence that did not change; none stops silently.
- **SC-004**: The reason a run stopped is retrievable on a branch after the
  original run's output is no longer available, in 100% of stopped runs.

## Validation Strategy _(mandatory)_

- The project's own definition of done: its test suite, linter and type checker,
  all green.
- A test driving one step across three consecutive passes that each advance the
  work, asserting the run is not stopped.
- A test driving one step across three consecutive passes that advance nothing,
  asserting the run stops and names that step.
- A test covering a pass history written in the older record shape, asserting the
  count is unaffected.
- An observed unattended run against a genuinely repeating step, watched to a
  stop. A test asserting the bound fires, with no run that watched it fire, does
  not validate this feature.

## Assumptions

- Pre-specify design context loaded from the branch's `design.md`.
- Three passes is the threshold, fixed rather than configurable. A configurable
  bound invites tuning the number instead of addressing the stall.
- A step that repeats while its artifacts change in ways that do not advance the
  work — a rewritten timestamp, a reflowed heading — will not be stopped. This
  fails toward running longer rather than stopping working automation, which is
  the direction chosen deliberately.
- A step whose evidence lives outside the pipeline's three readable artifacts
  advances without changing them, so it can read as stalled while it is working.
  Two steps are in that position. The exposure is a false stop rather than a
  missed one, and it is recorded in the design decision rather than assumed away.
