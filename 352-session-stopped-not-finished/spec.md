# Feature Specification: Session Stopped, Not Finished

**Feature Branch**: `352-session-stopped-not-finished`
**Created**: 2026-09-11
**Status**: Draft
**Input**: Issue #352 — "A session cut off mid-run cannot say so, so the next one stalls on a question nobody is there to answer", plus the branch handoff in the state dir.

## Clarifications

### Session 2026-09-11

- Q: What is the canonical name for a stop that did not finish — *continued*, *unfinished*, or *interrupted*? → A: **continued**. It names what happens next rather than passing judgment on the work. The tool can observe that a session stopped; it cannot observe that the work was incomplete, and it stopped claiming otherwise deliberately. This fixes the vocabulary the spec and the user-facing surface use — not the literal value stored on disk, which the architecture gate still owns.
- Q: Does this feature also surface the continued stop in the pipeline status view, or is the branch history the only place it is reported? → A: **Branch history only.** The status view is unchanged by this feature. A branch's history already reports every stop, which is all User Story 3 asks for; a status row would be a second reader of a record whose shape is not yet chosen.
- Q: When a stop is recorded as continued but the handoff beside it names no usable first action, is anything said at the moment of the stop? → A: **Yes — the stop reports it.** The operator is told the handoff names no first action and that the next session will therefore ask. The stop still happens.
- Q: Is the stop's kind the right thing for the next session to branch on, or is it the branch itself? → A: **The branch, with the stop's kind as the tie-break on trunk.** A branch that names a tracked issue has already answered "what are we working on today?" — the answer is the issue, the branch name carries it, and a session that wrapped up deliberately there left that same issue open. So an issue branch never asks. A trunk branch carries no such answer and accumulates a handoff from every session that ever ended on it, which is where the question belongs and where a continued stop is the one thing that can answer it with nobody present. This widens FR-004 and narrows FR-005; FR-016 carries the trunk case that was FR-004's.

## User Scenarios & Testing _(mandatory)_

A development session on a branch can stop for two unrelated reasons: a person
decided the work was at a good place to leave it, or the run was cut off while
it was still going. Today the branch's record says only *a session stopped
here*, and the routine that starts the next session reads that single mark as
the first reason. So a run that was cut off comes back, finds a handoff on disk
and work ready to do, and stops to ask a person which of the two it is — a
question that is only answerable by the person who is not there, which is
exactly why the run was cut off unattended in the first place.

The change is to let a stop say which of the two it was, and to let the next
session act on the difference — but only where the difference decides anything.
On a branch named for a tracked issue the question has one answer whatever the
stop said, because the branch is named for the work: a session that wrapped up
deliberately there left that same issue open. So the question survives on trunk
branches alone, and a continued stop is what answers it there with nobody
present.

### User Story 1 - A cut-off run comes back and carries on (Priority: P1)

A run is interrupted partway through its work. The interruption writes the
handoff and marks the stop continued. A new session starts on the same
branch, reads the handoff, and continues from the action the handoff names —
without asking anyone what to work on.

**Why this priority**: This is the stall. It is the only part of the change
that removes it; everything else here exists to make this safe or to make it
recordable. Shipped alone, on a branch whose log was marked by hand, it already
works.

**Independent Test**: On a branch naming a tracked issue, put a handoff naming a
first action beside any stop record at all. Start a session: it must begin that
action and must not ask. Then repeat on a branch naming no issue — a continued
mark must begin, a finished one must ask. The branch is the first column and the
stop's kind is the second.

**Acceptance Scenarios**:

1. **Given** a branch naming a tracked issue and a handoff naming a first action
   in a literal sentence, **When** a session starts, **Then** it quotes that
   sentence, states in one line what it is doing, and begins — with no question
   put to the human, whatever the last stop was and whether or not there was one.
2. **Given** a branch naming no tracked issue, whose most recent stop is marked
   continued, and whose handoff names a first action in a literal sentence,
   **When** a session starts, **Then** it begins the same way.
3. **Given** a branch naming no tracked issue, whose most recent stop is marked
   finished, **When** a session starts, **Then** it asks "What are we working on
   today?", offering the handoff's top next item as the default — unchanged from
   today.
4. **Given** any branch whose handoff names no first action, or names one still
   left as a placeholder, **When** a session starts, **Then** it asks, because
   there is no sentence to quote. Neither the branch nor the stop's kind reaches
   this: the quote is the gate and nothing relaxes it.

---

### User Story 2 - Stopping without finishing is something you can record (Priority: P2)

A person — or an automated resetter acting for one — wants to stop a run,
preserve the handoff for whoever comes next, and say plainly that the work was
not finished. They do it with the tool rather than by editing the branch's
record by hand.

**Why this priority**: Second because it produces input for a reader that must
already exist. Shipped before Story 1, it writes a mark nothing consults and
nothing changes. Shipped after, it is what makes Story 1 reachable without
hand-editing.

**Independent Test**: Stop a session declaring it continued. The handoff must
be written exactly as a finished stop writes it, and the branch's record must
carry a stop distinguishable from a finished one.

**Acceptance Scenarios**:

1. **Given** a started session, **When** the operator ends it declaring the
   work continues, **Then** the handoff artifact is produced by the same
   template, at the same location, under the same write-once rule as a finished
   end — and the branch's record shows the stop as continued.
2. **Given** a branch that already has a handoff on disk, **When** a session
   ends declaring that the work continues, **Then** the existing handoff is left
   untouched and the operator is told it was kept, exactly as a finished end
   reports it.
3. **Given** no session has been started on the branch, **When** a continued
   end is attempted, **Then** it is refused the same way a finished end is
   refused.
4. **Given** an operator ends a session without declaring anything, **When**
   the record is read, **Then** the stop is a finished one — the existing
   spelling and the existing meaning, unchanged.
5. **Given** a handoff that names no first action, or names one still left as
   a placeholder, **When** a session ends declaring that the work continues,
   **Then** the stop is still recorded and the operator is told the handoff
   names no first action, so the next session will ask anyway.

---

### User Story 3 - An interrupted run is visible afterwards (Priority: P3)

Someone looking at a branch later can see that a run was interrupted, and how
many times, rather than seeing a branch that looks as though nobody ever
worked on it.

**Why this priority**: It is the reason this change records the interruption
instead of erasing the stop. The alternative — removing the stop from the
record so the next session routes past it — produces the same routing today and
leaves a branch interrupted four times indistinguishable from an untouched one.

**Independent Test**: Interrupt a branch three times. Its history shows three
stops, each marked continued, in order, with nothing removed.

**Acceptance Scenarios**:

1. **Given** a branch interrupted several times, **When** its history is
   printed, **Then** every stop appears, each carrying which kind it was, in
   the order they happened.
2. **Given** a branch whose stops are a mix of both kinds, **When** its history
   is printed, **Then** the two kinds are told apart by what is recorded and
   not by their position or timing.

### Edge Cases

- A branch carries stops of both kinds. The most recent one governs; an older
  finished stop does not re-impose the question on a branch interrupted since,
  and an older continued stop does not suppress the question on a branch a
  person has since deliberately wrapped up.
- The handoff on disk was written *for* the branch before any session ran on it
  — a worktree handoff, not a session's own summary. Which of the two it is
  stays unrecoverable from the file, and nothing in this change tries to
  recover it. Only the stop record is consulted.
- A continued stop is recorded, and the handoff beside it is a scaffold whose
  next action is still a placeholder. The session asks. The requirement to
  quote a literal sentence is not relaxed by the stop's kind — but the stop
  itself says so at the time, while the operator is still there to fix it.
- A continued stop is recorded by an operator that then never restarts. The
  branch simply sits with a continued mark, which is a true statement about
  it.
- The branch record is unreadable or absent. The session falls back to the
  no-record behaviour and asks, rather than assuming either kind.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: A session MUST be able to record that it stopped *without
  finishing*, and that record MUST be distinguishable from a stop that
  finished.
- **FR-002**: Recording a continued stop MUST produce the handoff artifact
  under the same rules as a finished stop — same template, same location, same
  write-once behaviour, same report of a kept file.
- **FR-003**: The continued mark MUST survive a reset of the operator's
  working context, and MUST be readable by the next session from durable state
  alone, with nothing carried forward in memory.
- **FR-004**: A session starting on a branch that names a tracked issue, whose
  handoff names a first action as a literal sentence, MUST proceed with that
  action and MUST NOT ask the human what to work on — whatever kind the last
  stop was, and whether or not there was one.
- **FR-005**: A session starting on a branch that names no tracked issue, whose
  most recent stop is not continued, MUST ask what to work on, as it does today.
- **FR-016**: A session starting on a branch that names no tracked issue, whose
  most recent stop is continued and whose handoff names a first action as a
  literal sentence, MUST proceed with that action and MUST NOT ask.
- **FR-006**: A session MUST ask what to work on whenever it cannot quote a
  literal sentence naming a first action, whatever kind the last stop was.
- **FR-007**: When a branch's record carries more than one stop, the most
  recent one MUST determine the behaviour in FR-005 and FR-016. It determines
  nothing in FR-004, which does not consult the stop record at all.
- **FR-008**: Every stop MUST be retained. Nothing in this feature removes,
  rewrites or overwrites a stop already recorded.
- **FR-009**: A person stopping a run themselves MUST be able to mark it
  continued at the moment they stop, without editing stored state by hand.
- **FR-010**: Neither the mark nor the routing rule MAY name a particular agent
  or depend on a mechanism only one agent has.
- **FR-011**: Omitting the declaration MUST record a finished stop — existing
  callers keep their existing meaning with no change at the call site.
- **FR-012**: The routing rule MUST reach every repository the tool installs
  into, rather than depending on a hand edit in any one of them.
- **FR-013**: Recording a continued stop over a handoff **the tool itself
  wrote**, whose next-action section was never filled in, MUST still record the
  stop and MUST tell the operator so — the one person who could still supply the
  sentence hears about it before they leave. A handoff written by anyone else
  MUST NOT be judged: the tool has no shape to judge it against, and the
  document that carries a first action in its own form is the common case, not
  the exception.
- **FR-014**: *continued* is the canonical term for the mark wherever the
  feature is described or surfaced. No other word names the same thing.
- **FR-015**: The pipeline status view MUST be unchanged by this feature. The
  branch history is the only place a continued stop is reported.

## Key Entities

- **Stop record**: the fact that a session stopped on this branch, carrying
  which kind of stop it was (finished / continued), when it happened, and the
  pipeline step observed at the time. Appended, never amended.
- **Continued**: the canonical name for a stop that did not finish. It
  describes what happens next — someone continues — rather than judging the
  work, which is a thing the tool cannot observe and stopped claiming.
- **Handoff**: the prose a person or agent wrote for whoever comes next,
  including the first action to take. Independent of the stop record, and the
  only thing that can supply the quoted sentence.
- **Branch history**: the ordered sequence of stop records for one branch. Its
  last stop answers "why did the last session stop"; its whole length answers
  "how often was this run interrupted".

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A branch interrupted mid-run and restarted unattended reaches its
  first work action with zero inputs from a human.
- **SC-002**: A branch naming no tracked issue, whose last stop was a finished
  one, asks what to work on on 100% of restarts — no case where this change
  starts work against a trunk branch's accumulated handoff.
- **SC-003**: A session never begins work on an inferred first action: in 100%
  of cases where work begins without a question, a literal sentence from the
  handoff is quoted first.
- **SC-004**: Every interruption on a branch is recoverable from its history
  afterwards — a branch interrupted N times reports N, for every N.
- **SC-005**: A stop recorded without any declaration is read by every existing
  reader exactly as it is today — no reader changes its verdict on a branch
  whose behaviour did not change.

## Validation Strategy _(mandatory)_

The repository's definition of done, all four green:

```bash
uv run --frozen --extra dev pytest -q
uv run --frozen --extra dev ruff check wfctl/ tests/
uv run --frozen --extra dev mypy wfctl/
uv run wfctl doctor
```

Story-specific validation beyond that, because the test suite does not cover
the instruction text this change edits:

- **Unit** — the stop record's two kinds: written with and without the
  declaration, read back, and the most-recent-wins rule from FR-007 exercised
  against a record carrying both.
- **Unit** — the handoff write-once rule holds for a continued stop exactly
  as for a finished one, including the kept-file report.
- **Unit** — a continued stop over a handoff naming no first action still
  records the stop and reports that the handoff names none (FR-013).
- **Contract** — existing readers of a stop record are unchanged for a stop
  recorded without the declaration (SC-005), and the status view's output is
  byte-identical to today's on a branch carrying a continued stop (FR-015).
- **Manual, both halves** — install the skills from the working tree, then
  start a session on a branch whose record carries a continued stop (must
  begin work, quote the handoff, ask nothing) *and* on a branch whose record
  carries a finished one (must still ask). A run that exercised only the first
  half has not tested the protection FR-005 exists to provide.

## Assumptions

- No pre-specify design artifact exists for this branch — the upstream design
  document the pipeline looks for is absent. The description above is drawn
  from issue #352 and the branch handoff, both of which record decisions
  already taken.
- **How the record distinguishes the two kinds is deliberately not decided
  here.** A separate kind of stop and a field on the existing kind both satisfy
  every requirement above. The choice is expensive to reverse — it changes what
  existing readers must interpret — and is left to the architecture gate.
- The surface an operator uses to declare a continued stop (a flag on the
  existing command, or a command of its own) is likewise not decided here.
- The automated resetter that produced the observed failure lives outside every
  repository and is installed by a person. It is out of scope. The requirements
  above are written so that such a resetter *could* drive them, and so that a
  person stopping by hand gets the same thing.
- The neighbouring work on per-session identity asks a different question of
  the same record ("is a session open now" rather than "why did the last one
  stop"). Whichever lands first, the other rebases.
