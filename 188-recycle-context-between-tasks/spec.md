# Feature Specification: recycle context between tasks

**Feature Branch**: `188-recycle-context-between-tasks`
**Created**: 2026-09-11
**Status**: Draft
**Input**: Issue #188 — "Nothing recycles context between tasks, so a run finishes in a window that no longer holds its own beginning"

## Clarifications

### Session 2026-09-11

- Q: Does the cycle run `/end-session` before the reset, or only reset and
  resume? → A: It runs `/end-session` first. `session-state-is-re-derived` holds
  that the session file carries "the handoff prose a human or agent wrote
  deliberately" — the one thing re-derivation cannot reach — and nothing else
  writes it. Decisively, `start-session`'s step 9 routes on whether
  `session-summary.md` names a first action: with no summary the returning
  session lands in the table's last row and asks "what are we working on
  today?", which stalls exactly the unattended run this feature exists for.
- Q: What is the threshold measured against? → A: An absolute token count held
  in wfctl's source. The transcript's usage object carries input, cache-read,
  cache-creation and output counts and no context-window total, so a percentage
  cannot be computed from what wfctl is handed. #188 scopes tuning out: pick one
  number, learn from it.
- Q: How does the run know whether its pane can be sent to? → A: The
  orchestrating skill asks, not wfctl. `wfctl-names-the-reset-it-cannot-perform`
  holds that wfctl declines the multiplexer dependency by construction, and
  putting "is a pane registered" on the payload would place that query inside
  the one report every view builds.

## User Scenarios & Testing _(mandatory)_

A run driven by `speckit-orchestrate` executes one pipeline step after another in
a single conversation. Today nothing measures how full that conversation has
become, and nothing acts on it, so the run reaches its last step holding a window
the harness has already compacted at a moment nobody chose.

### User Story 1 - An unattended run recycles at a task boundary and continues (Priority: P1)

A run with nobody watching finishes `plan`, and its window has passed the
threshold. Instead of carrying a degrading context into `tasks`, the run writes
its handoff, discards the window, and comes back with the handoff, the
architecture contract, and a pipeline position re-derived from artifacts.

**Why this priority**: it is the only story that serves #147's acceptance test —
one unattended run ending in a PR. A run long enough to produce a real PR is long
enough to outgrow one window, so that test cannot pass without this.

**Independent Test**: drive a run to the threshold at a step boundary, let the
cycle fire, and confirm the session that comes back reports its position from
artifacts on disk with no reference to anything that survived.

**Acceptance Scenarios**:

1. **Given** a run whose window is past the threshold and whose current step has
   just completed, **When** `speckit-orchestrate` reads the payload, **Then** it
   performs the cycle rather than emitting `EXECUTE_COMMAND` for the next step.
2. **Given** a cycle has completed, **When** the returning session reads
   `wfctl status`, **Then** the pipeline position matches what the artifacts on
   disk imply, and no step's state was carried across the boundary.
3. **Given** a cycle has completed, **When** the returning session reads the
   window again, **Then** the verdict is absent and the run proceeds rather than
   recycling a second time.

### User Story 2 - An attended run is told exactly what to do (Priority: P2)

A run in a terminal nobody has registered with a multiplexer reaches the same
threshold. It cannot perform the cycle itself, so it says so, names the three
commands in order, and names the step the next session will resume at.

**Why this priority**: it is today's behaviour made explicit, and it is the floor
under Story 1 rather than a lesser version of it. A run with no pane has no
better answer, and a run that silently carried on would be indistinguishable from
one where the feature never fired.

**Independent Test**: unset or remove the pane registration, drive the same run to
the threshold, and read what is printed.

**Acceptance Scenarios**:

1. **Given** the threshold is passed and no pane is registered, **When**
   orchestrate reads the payload, **Then** it prints the handoff, clear and
   resume commands in that order and stops without emitting `EXECUTE_COMMAND`.
2. **Given** that stop, **When** the reader follows the printed commands, **Then**
   the returning session resumes at the step the message named.

### User Story 3 - A finished run can be told from a stopped one (Priority: P3)

Someone opens a branch the next morning. `wfctl status` tells them whether the
run recycled and carried on, or stopped for a person and never resumed.

**Why this priority**: it costs one event line and it is what makes the other two
stories auditable after the scrollback is gone. Without it a run that recycled
cleanly and one that died at the same boundary look identical.

**Independent Test**: recycle a run, then read `wfctl status` on that branch in a
fresh session.

**Acceptance Scenarios**:

1. **Given** a branch whose run recycled once, **When** `wfctl status` is read,
   **Then** it reports that a recycle happened, when, and at which step boundary.
2. **Given** a branch whose run has never recycled, **When** `wfctl status` is
   read, **Then** it reports nothing about recycling rather than reporting zero.

### Edge Cases

- **The transcript cannot be read.** A moved, truncated or unreadable transcript
  yields no verdict and the run proceeds. Same posture as the existing hooks: a
  run that is otherwise fine is not stopped by a file wfctl could not open.
- **The run has stalled and is also past the threshold.** The stall wins. A
  stalled run needs a person, and recycling it would discard the context that
  person is about to be asked to look at.
- **The story is complete and the window is full.** Story-complete wins; there is
  no next task for a recycle to precede.
- **The threshold is passed mid-step rather than at a boundary.** Nothing fires.
  The boundary is the whole claim of this feature, and a verdict acted on
  mid-step would be the token-threshold compaction it exists to replace.
- **A second branch shares the state dir.** The recycle event is scoped to the
  branch that wrote it, for the reason `notify-resolved` already carries a branch:
  one feature's record must not answer for another's.
- **The returning session asks instead of resuming.** The failure FR-005a
  names, and the one that makes an unattended cycle a no-op: everything works,
  the window is fresh, and the run stops on a question nobody is there to
  answer. Found by reading step 9's own table while preparing to drive the
  acceptance test, not by a test.
- **The pane is registered but busy.** The cycle waits for idle before delivering
  anything. A prompt delivered mid-turn is surfaced into the running turn rather
  than executed at a boundary, which was observed directly while specifying this.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: wfctl MUST compute, from the agent transcript it is already handed,
  whether the run's window has passed the threshold at which the next task should
  start fresh.
- **FR-002**: The verdict MUST be carried on the single pipeline payload every
  view renders, not returned by a separate command and not injected into the
  agent's context alone.
- **FR-003**: The verdict MUST name the step current at the moment it was reached,
  so a message can say which step the next session resumes at.
- **FR-004**: `speckit-orchestrate` MUST act on the verdict between its stall
  branch and its `auto` branch, and MUST NOT derive the verdict itself.
- **FR-005**: Where the run's pane is registered with the multiplexer, the cycle
  MUST be performed without a person: handoff, then reset, then session start.
- **FR-005a**: The handoff step MUST NOT record the run as *ended*. `wfctl end`
  writes `{"event": "end"}`, and `start-session` step 9 routes a branch carrying
  one into its second row — "a session has finished here before" — which asks a
  human what to work on. A recycle is the opposite claim: the run is continuing.
  The cycle therefore needs its own event, or step 9 needs a row that tells a
  recycled branch from an ended one.
- **FR-005b**: The agent MUST NOT be the performer. Beyond being refused
  `/clear` by name, an agent that scripts the cycle against its own pane is
  refused by the harness's permission classifier — reason `[Tmux Self Drive]`,
  observed while attempting the acceptance test. A single plain-text send is
  allowed; assembling wait-reset-restart is not. The performer is therefore a
  supervisor process outside the run, or a person.
- **FR-006**: Where it is not, the run MUST print those three commands in order,
  name the resuming step, and stop.
- **FR-007**: Each recycle MUST append one line to the branch's event log carrying
  the time and the step boundary it fired at.
- **FR-008**: `wfctl status` MUST report a recycle that has happened on this
  branch, and MUST report nothing where none has.
- **FR-009**: A verdict MUST NOT be produced where the transcript cannot be read;
  the run proceeds.
- **FR-010**: A stall or a complete story MUST take precedence over a verdict.
- **FR-011**: The cycle MUST NOT be delivered while the pane is busy; it waits for
  idle.
- **FR-012**: The threshold MUST be a single value in wfctl's source, not a
  configurable key.

### Key Entities

- **Recycle verdict** — whether this run should reset before its next task, the
  step it was reached at, and the occupancy that decided it. Absent in the common
  case.
- **Recycle event** — one line per firing in the branch's event log: when, and at
  which step boundary. History, not cached state; it cannot be re-derived because
  the window has moved since.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A run driven past the threshold at a step boundary recycles exactly
  once and continues; the returning session reaches the next step without a
  person touching the keyboard.
- **SC-002**: The returning session's reported pipeline position is identical to
  what the artifacts on disk imply, checked by comparing `wfctl status --json`
  before and after the cycle with no artifact changed between.
- **SC-003**: A run that recycled is distinguishable from one that stopped, by
  reading `wfctl status` alone, in a session that saw neither.
- **SC-004**: No run recycles more than once per step boundary, and no run
  recycles with a step incomplete.
- **SC-005**: A run whose transcript is unreadable completes its pipeline
  unchanged from today's behaviour.

## Validation Strategy _(mandatory)_

The project's own definition of done, all four green:

```bash
uv run --frozen --extra dev pytest -q
uv run --frozen --extra dev ruff check wfctl/ tests/
uv run --frozen --extra dev mypy wfctl/
uv run wfctl doctor
```

Unit coverage for the verdict's arithmetic, its absence on an unreadable
transcript, its precedence behind stall and story-complete, and its branch
scoping in the event log — the shape `tests/` already uses for `_stall`.

A change under `wfctl/agents/` is not covered by that suite. Editing
`speckit-orchestrate/SKILL.md` requires `uv run wfctl install-skills` and then
exercising the new arm.

**The acceptance test is not a unit test.** SC-001 requires a real run driven to
a real boundary with the cycle actually firing. A verdict asserted in `pytest` and
never fired has not tested the cycle, and the three assumptions this spec rests on
— that a sent reset executes as a command, that the wait fires at idle, and that
the reading is stable across adjacent boundaries — are falsifiable only by driving
one.

## Assumptions

Pre-specify design context loaded from
`specs/188-recycle-context-between-tasks/design.md`.

- The window's denominator is not in the transcript. Occupancy is, and the
  statusline renders a percentage, so something knows the total; which value the
  threshold is measured against is carried as an open question in `design.md`
  rather than guessed here.
- `/end-session` runs before the reset. The architecture records hold that only
  deliberate prose survives re-derivation, which argues for writing the handoff;
  whether it earns its cost at a mid-run boundary is untested and is the design's
  second open question.
- The run is a single conversation in a single pane. A run spread across panes is
  out of scope, and a run that has died is #101's.
