# Feature Specification: two permission systems

**Feature Branch**: `364-two-permission-systems`
**Created**: 2026-09-13
**Status**: Draft
**Input**: User description: "" (empty — the design document is the input; see Assumptions)

## Clarifications

### Session 2026-09-13

- Q: Which step does a standing block hold? → A: The step that was current when the report was made.
- Q: Does a later recorded success for the same action release the hold, or only an explicit clear? → A: Yes — the most recent event for an action stands, whether it is a block, a clearing, or a recorded success.
- Q: What is a block scoped to? → A: The branch's own session state, like every other event.
- Q: Is clearing enforced as a person's action rather than the agent's? → A: No — ungated, the row closing an issue already occupies; the asymmetry is carried by the report command's shape.

Basis, and the options each answer was decided against: `docs/architecture/scans/364-clarify.md`.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - The refusal leaves a trace, and the step stops (Priority: P1)

An agent running the pipeline unattended reaches a step whose last act is a write
to the issue tracker — commenting a link, creating the child issues, closing the
issue. The agent's own host refuses that command before it starts. The agent
records the refusal against the action it was attempting, and the pipeline stops
at that step instead of reading as finished.

**Why this priority**: This is the failure the feature exists for. Today the
refused run and the successful run leave byte-identical state on disk, so the
pipeline advances past a step that never finished, and the only record of the
refusal is a transcript that is cleared or compacted. Without this story nothing
else here changes what a run can be trusted to have done.

**Independent Test**: Record a block for an action belonging to a completed step,
then read the pipeline. The step reports held with the reason attached, and the
event survives a new session. Delivers the trace and the stop with nothing else
built.

**Acceptance Scenarios**:

1. **Given** a run whose tracker write was refused by the host, **When** the
   agent records the block against that action with a reason, **Then** the report
   is accepted and stored, and the step that owns the action reports as not
   advanced, carrying the reason.
2. **Given** a step whose own artifacts are all present and which would otherwise
   read as finished, **When** a block is recorded against one of its actions,
   **Then** the step reports held rather than finished, even though a later step
   reports finished.
3. **Given** an agent that holds no authority to notify anyone, **When** it
   records a block, **Then** the report is accepted — recording a refusal is not
   an outward action and requires no grant.
4. **Given** an agent recording a block without stating a reason, **When** the
   report is submitted, **Then** it is refused and nothing is stored.
5. **Given** a branch that carries no feature, **When** a block is recorded,
   **Then** the report is still stored and the response says plainly that no step
   is being held.

---

### User Story 2 - A person reads what the run did not do, and releases it (Priority: P2)

Someone returns to an unattended run that stopped. The pipeline names the action
that was refused and why, says that re-running the step will be refused the same
way, and names what a person — not the agent — does to take the action and
release the hold.

**Why this priority**: The trace from Story 1 is worth little if the reader
cannot act on it, and the release is the half addressed to a person: ungated, by
the same rule that leaves closing an issue ungated, because a gate there would
refuse the only actor who can honestly run it. It is second because Story 1
delivers the honest stop on its own; this makes the stop recoverable.

**Independent Test**: With a block standing, read the pipeline and follow only
what it printed. The reader can name the refused action, understands that
re-running the step will not help, and can release the hold once the action has
actually been taken.

**Acceptance Scenarios**:

1. **Given** a held step, **When** a person reads the pipeline, **Then** the
   remedy states that the step was blocked by the agent's host rather than by
   wfctl, and that re-running it will be refused again.
2. **Given** a held step, **When** a person reads the next action the pipeline
   offers, **Then** it is the step's own command — never the command that
   releases the hold.
3. **Given** a person who has taken the refused action themselves, **When** they
   clear the block for that action, **Then** the hold is released and the step
   resumes reporting from its own artifacts.
4. **Given** an action with no block recorded against it, **When** someone clears
   it, **Then** the response says there was nothing to clear and no state changes.

---

### User Story 3 - The authority report stops overstating what it knows (Priority: P3)

Every run's authority report says that a second permission layer exists, that it
belongs to the agent rather than to wfctl, and that wfctl neither sees it nor
speaks for it. The line about actions wfctl will never take names the whole class
it implements rather than half of it.

**Why this priority**: It ships value with nothing else built — it is what the
issue asked for in its own words — and it is what stops the rest of the authority
report from reading as an account of everything that could stop the run. It is
third because it can never say that a refusal actually happened.

**Independent Test**: Read the authority report in each grant state. The new line
is present and true in every one, and the irreversible line names every action in
its class.

**Acceptance Scenarios**:

1. **Given** any grant state, **When** the authority report is read, **Then** it
   carries a line saying the agent has its own rules, that wfctl cannot see them,
   and that it says nothing about them.
2. **Given** any grant state, **When** the authority report is read, **Then** the
   line naming actions wfctl will never take names merging, force-pushing,
   closing an issue, and deleting a branch or worktree.
3. **Given** a run where an outward action has been authorized, **When** the
   authority report is read, **Then** it still reports that authorization as
   granted — the new line, not a change to that fact, is what keeps the pair from
   reading as a claim about the agent's own layer.

---

### Edge Cases

- **Two blocks of the same action in one session.** The later report is the one
  that stands; the earlier is not separately recoverable from the held step's
  reason.
- **A held step whose later steps report finished.** The hold is honest and is
  rendered as-is: a run can write every artifact and still never reach the
  tracker.
- **The action is blocked, then later succeeds through wfctl.** The success is
  recorded against the same action name and supersedes the block, so the hold
  releases with nobody clearing it. This rests on the two spellings matching.
- **A block recorded, then the work abandoned.** The hold persists across
  sessions until someone clears it. Nothing observes whether the action was ever
  taken, so an unrecorded release leaves the step held.
- **An action spelling that nothing later matches.** The report is stored and
  holds the step that was current when it was made, whatever the action is
  called — the action names no step of its own. What an odd spelling costs is the
  release: a clearing or a recorded success under a different string does not
  lift it, and clearing under the block's own spelling is the escape.
- **A host that terminates the run rather than returning an error.** No report
  can be made, and the run reverts to today's behaviour — silent. This is a
  stated limit, not a case to handle.
- **An agent that is blocked and stays quiet.** The step stays exactly where it
  was. The report is tamper-evident, not unforgeable.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The authority report MUST carry a line, in every grant state,
  stating that the agent has permission rules of its own, that wfctl cannot see
  them, and that wfctl says nothing about them.
- **FR-002**: That line MUST be keyed on nothing — identical text in every grant
  state, because it is true in all of them.
- **FR-003**: That line MUST NOT name the command that reports a block. An agent
  needs that command mid-run, long after it last read the authority report.
- **FR-004**: The line naming actions wfctl will never take MUST name every
  action in its class: merging, force-pushing, closing an issue, and deleting a
  branch or worktree.
- **FR-005**: An agent MUST be able to report that an outward action was refused
  by its host, naming the action and a reason.
- **FR-006**: That report MUST NOT require any authority grant. A run blocked by
  its host is by construction a run that may hold no grant.
- **FR-007**: The report MUST be refused, storing nothing, when no reason is
  given.
- **FR-008**: The report MUST be stored even where there is no feature and no
  step to hold, and the response MUST say that no step is being held.
- **FR-009**: There MUST be no way to report a *success* through this command.
  The agent may report a failure it alone witnessed; it may never report a
  success.
- **FR-010**: A standing block MUST hold the step that was current when the
  report was made, reporting it as not advanced with the reason attached. The
  report names no step of its own.
- **FR-011**: The hold MUST override a step that would otherwise report as
  finished, and MUST be applied to the inferred pipeline rather than computed
  inside any one step's own rule.
- **FR-012**: Where an action carries more than one event, the most recent one
  MUST be the one that stands — whether it is a block, a clearing, or a
  recorded success.
- **FR-013**: A person MUST be able to clear a standing block for a named action,
  releasing the hold. Clearing MUST NOT be gated behind any authority grant: it
  is a person's command by the same rule that leaves closing an issue ungated —
  a gate there would refuse the only actor allowed to run it.
- **FR-014**: Clearing an action with no block standing MUST change nothing and
  MUST say that there was nothing to clear.
- **FR-015**: A held step MUST carry a remedy stating that the block came from
  the agent's host rather than from wfctl, that re-running the step will be
  refused again, and that a person takes the action and then records that it
  happened.
- **FR-016**: The next action offered for a held step MUST remain the step's own
  command, never the command that clears the block.
- **FR-017**: The skills that drive the pipeline MUST tell an agent to report a
  block when its host refuses an outward action.
- **FR-018**: No new step state, no new fact row in the authority report, and no
  new top-level key in the machine-readable pipeline payload.
- **FR-019**: The existing command for recording notifying actions, including its
  authority gate, MUST be unchanged.
- **FR-020**: A recorded success for a blocked action MUST release the hold, with
  no clearing step of its own. A block and the success that answers it are
  matched on the action's name.
- **FR-021**: A block MUST be scoped to the branch it was reported on, and stored
  with that branch's other session events. A block on one branch MUST NOT hold a
  step on another.

## Key Entities

- **Block report**: what one refusal is recorded as — the action's name, the
  reason the host gave, the step that was current, and when. Written by the
  agent, read back by the pipeline, and stored with the branch's other session
  events.
- **Action name**: free text identifying what was attempted (`issue-create`,
  `issue-comment`). It is what a block and its clearing are matched on, and what
  ties a block to the step that owns it.
- **Held step**: a step the pipeline reports as not advanced because a block
  stands against it, regardless of what its own artifacts say. It is held until
  the action's next event — a clearing, or a recorded success — supersedes the
  block.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: After an unattended run whose tracker write was refused, a person
  can name which action was refused and the reason given, reading only what the
  pipeline prints — with no access to the agent's transcript.
- **SC-002**: A step whose tracker write was refused and reported never reports
  as finished, in 100% of cases, including where every artifact that step
  produces is present.
- **SC-003**: The authority report is true in all eight grant-state renderings
  with respect to both permission layers — the seven keyed states plus the one
  built for a label — and the actions-never-taken line is true in all four of the
  cases it covers, up from two of four today.
- **SC-004**: An agent holding no authority grant can record a refusal in one
  command, with no preparatory step.
- **SC-005**: A person can release a hold in one command, and no spelling of the
  reporting command records a *success*. The asymmetry is on what may be
  reported, not on who may clear: clearing is ungated, by the same rule that
  leaves closing an issue ungated.
- **SC-006**: A run in which nothing was refused renders exactly as it does
  today, apart from the two authority lines — no new fact row, no new step state,
  no new payload key.

## Assumptions

- Pre-specify design context loaded from
  `specs/364-two-permission-systems/design.md`.
- **The agent survives the refusal.** The host returns an error and the run
  continues; observed three times on 2026-09-13, including on the attempt to test
  the claim. A host that kills the run instead leaves no witness and makes this
  whole feature unavailable. Listed in the design as an assumption to re-probe on
  a second host before the command is relied on unattended.
- **The action name stays free text.** No fixed set of action names is defined,
  on either this command or the existing notify command. Falsified the first time
  something wants to branch on the value rather than print it.
- **Matching a clearing to a block by action name is enough.** Two blocks of one
  action in a session collapse to the later one, which is accepted rather than
  worked around.
- **A person who takes the blocked action will record it.** Nothing observes the
  action itself, so an unrecorded release leaves the step held.
- Where a step's own evidence happens to sit downstream of the refused write —
  `decompose`, whose rows carry tracker keys a refused create cannot produce —
  the pipeline already fails safe by accident. That is not relied on: no test
  pins it and nobody chose it for that reason.

## Dependencies

- **#297** moves the issue-splitting decision to brainstorm, which removes the
  only outward action in an unattended run that genuinely cannot be survived. If
  it lands first, this feature's value is entirely the trace and none of it is
  the stop. It does not block this work.
- The level-2 ownership record `the-agent-reports-the-block-wfctl-never-saw` and
  the level-3 record `364-the-block-report-is-its-own-verb` are both `proposed`.
  They bind this work as designed and are expected to be accepted with it.

## Out of Scope

- **Preventing the block** by installing a rule into the agent's own permission
  config. The issue's Boundary puts writing into the host's layer outside scope,
  as a person's act, and the claim that such a rule would override the host's own
  classifier is unverified.
- **Asking the host in advance** whether an action would be permitted. Permission
  rules are matched against command strings at call time; there is nothing to
  ask.
- **A verdict channel** marking each outward action survivable or fatal.
  Designed in full and dropped — once #297 lands, the partition has one side
  empty.
- **Closing the reach problem.** wfctl's own gate catches a well-behaved agent
  and nothing else; a direct tracker command walks around it. The fix is a rule
  in the agent's layer, which is out of this issue's Boundary. Worth its own
  issue for the part wfctl could own: saying out loud that its gate is not a
  boundary.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/` —
  all three green is the repository's whole bar for a code change.
- `uv run wfctl doctor` — green, against the working tree's own wfctl.
- Unit coverage for the report's storage and its rejection without a reason,
  including the no-feature-branch case.
- Pipeline-level coverage that a standing block holds the step it names,
  overrides a finished step, and releases on clear — asserted on the
  machine-readable payload, so every view inherits it.
- Rendering coverage for the two authority lines in every grant state, and for
  the remedy and next-action of a held step. Output assertions pin colour off, as
  the suite's convention requires.
- A test that the existing notify command and its gate are unchanged.
- For the skill changes: `uv run wfctl install-skills` from the working tree,
  then read the instruction as an agent would. The suite checks that skills ship
  and cross-reference; it does not check that they read well.
