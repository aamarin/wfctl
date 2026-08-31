# Feature Specification: session truth ownership

**Feature Branch**: `74-session-truth-ownership`
**Created**: 2026-08-30
**Status**: Draft
**Input**: Epic #74, covering #42 and #70. Design context loaded from `design.md`.

## Clarifications

### Session 2026-08-30

- Q: What happens to `current.json` when `current.md` is removed? → A: Delete it
  too. Session existence is derived from the `start` event already written to
  `events.jsonl`. Two conditions attached: the CLI must cover everything the
  file carried, and the session facts ride the same structure as the pipeline
  states rather than a second one. Coverage verified — issue, branch and repo
  are derived in `_resolve_context` (`cli.py:82-86`), step and next command on
  every read, `updated` from the last event's timestamp, and `status` has no
  reader.
- Q: A feature with no artifacts renders two ways today — which one is right? →
  A: Nothing at all means the first step has not started, so it reads as
  not-started and is where the reader is sent. The skipped rendering is reserved
  for a step genuinely passed by: its own artifact absent *and* a later
  artifact present. This matches the design gate, which fires only when the
  design artifact exists (`_pipeline.py:267-273`) — a change that drew no design
  has nothing to advance past.
- Q: What happens to the session files already on disk in every existing state
  dir? → A: Any command that touches the state dir removes them on sight. They
  are inert to the new code, but an older session skill elsewhere still reads
  them and would get exactly the stale answer this feature removes; deleting on
  first touch makes that window zero.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A session that starts cold is told the truth (Priority: P1)

An agent resumes work on a branch after its conversation was cleared. It has no
memory of the session that came before. It asks where the feature is and what to
do next, and every answer it gets is computed from what is on disk at that
moment — not from what some earlier session wrote down and did not update.

**Why this priority**: This is the failure #42 names. A stale answer is worse
than no answer, because nothing marks it as stale: the session acts on it
confidently and the work goes sideways in a way that looks like a decision.

**Independent Test**: Advance a branch's artifacts without running any session
command, then start a fresh session and ask where it is. The answer must reflect
the artifacts, not the last write.

**Acceptance Scenarios**:

1. **Given** a session started at `brainstorm` and a `design.md` written
   afterwards, **When** the next session asks where the feature is, **Then** it
   is told `specify`, not `brainstorm`.
2. **Given** a worktree pointed at a different branch than the one its session
   started on, **When** anything reports the branch, **Then** it reports the
   branch the worktree is on now.
3. **Given** a feature with no artifacts at all, **When** the pipeline is
   reported, **Then** the first step reads as not-yet-started, and identically
   whether or not an empty feature directory exists.
4. **Given** every step is done, **When** the pipeline is reported, **Then** it
   says so in words, rather than by the absence of a cursor.

---

### User Story 2 - Ending a session leaves an honest handoff (Priority: P2)

A developer ends a session. What the tool writes and prints describes what it
could observe at that moment — where the pipeline stands, whether the boundary
question was answered, whether the tree is dirty. It does not describe the
session as finished, because nothing it can read tells it that.

**Why this priority**: This is #70. The claim is not merely unverified, it is
unverifiable, and it is read by the next session as fact.

**Independent Test**: End a session mid-implementation with uncommitted work and
read what was written. Nothing in it should assert completion.

**Acceptance Scenarios**:

1. **Given** a session ending with three of eight tasks done, **When** it ends,
   **Then** the output names the pipeline position and the dirty tree, and
   claims no completion.
2. **Given** a handoff file with no prose filled in, **When** the next session
   reads it, **Then** what it reads is honest standing alone — an empty handoff
   reads as empty, not as a completed session.

---

### User Story 3 - A step's state has a name (Priority: P3)

The state of a pipeline step is a word — done, in progress, pending, skipped —
from the moment it is worked out to the moment it is shown. The symbols a
developer reads are applied when the line is printed and nowhere else.

**Why this priority**: P1 and P2 deliver without it. It is here because
removing the resume-point file makes the pipeline report the only answer a
session gets, and a drawing cannot carry the difference between a step that was
skipped and one that was completed — both mean "does not block", and only one of
them ran.

**Independent Test**: Inspect the inferred states for a feature whose clarify
step was skipped; the skipped step is named differently from the done ones,
with no symbol involved.

**Acceptance Scenarios**:

1. **Given** a step that was skipped rather than completed, **When** the states
   are inferred, **Then** it carries a name distinct from a completed step's.
2. **Given** the symbol used for a state is changed, **When** the states are
   inferred, **Then** nothing about the inferred states differs.

### Edge Cases

- A feature directory that exists but is empty — created before any artifact is
  written. Reads as not-started, identically to no directory at all.
- A spec written without a design artifact. The design step reads as skipped,
  because a later artifact exists and the gate does not apply to a change that
  drew no design.
- A branch name that encodes no issue key. Out of scope here; noted in
  `design.md`.
- A session file that exists from before this feature. Must not be treated as
  authoritative for anything re-derivable.
- Two worktrees on the same repository, one of which changed the artifacts while
  the other's session was open.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Every value describing where a feature stands MUST be computed
  when it is read, from artifacts on disk.
- **FR-002**: No session file may be the authority for a value that can be
  recomputed. Session files hold only what re-derivation cannot reach — the
  handoff prose a human or agent wrote deliberately.
- **FR-003**: The resume-point file that is written once and never updated MUST
  be removed rather than kept current. The session state file beside it MUST be
  removed with it: every field it holds is derived elsewhere, and the one fact
  that is not — that a session was started here — is already recorded in the
  session event log.
- **FR-004**: The pipeline report MUST name the next command to run, including
  when no step remains, so that removing the resume-point file loses nothing a
  reader had.
- **FR-005**: A feature with no artifacts MUST report identically whether or not
  an empty feature directory exists, and MUST report its first step as
  not-started rather than skipped.
- **FR-005a**: A step MUST report as skipped only when it was genuinely passed
  by — its own artifact absent while a later step's artifact exists. Absence
  alone is not-started.
- **FR-006**: Ending a session MUST report only what is observable at that
  moment: pipeline position, whether the design boundary was answered, and
  whether the tree is dirty.
- **FR-007**: The session `status` field MUST be removed. It has no reader, and
  work status is derivable from the pipeline.
- **FR-008**: A handoff artifact MUST be honest when read standing alone,
  including when its prose was never filled in.
- **FR-009**: Pipeline state MUST be carried as a named value from the point it
  is inferred to the point it is displayed, with symbols applied only when
  printing, and `status` MUST expose that payload to a calling agent under a
  `--json` flag. Both outputs render one inference — the flag selects a format,
  it does not select a second path. Deleting `current.json` without this flag
  would leave a calling agent with no source of per-step state but the console's
  glyphs, which is what `pipeline-state-is-one-payload` forbids.
- **FR-010**: The named pipeline states and the session facts a caller needs —
  which step is current, what command comes next, whether a session was started
  here — MUST be carried by one structure. A command that needs two of those
  facts reads them from one place, not two.
- **FR-011**: Every field the removed session files carried — issue, branch,
  repo, step, next command, last-updated — MUST still be answerable after their
  removal, each from a named source, and `status` MUST have no reader at all. A
  field that disappears without changing a rendered line is the failure this
  requirement exists to catch.
- **FR-012**: A command that touches a state directory MUST remove the session
  files this feature stops writing, if they are present. A leftover file is
  readable by an older session skill, which is the stale read this feature
  exists to eliminate.

## Key Entities

- **Pipeline position**: which step a feature is on and what state each step is
  in. Derived from spec artifacts and the verification record; owned by wfctl.
- **Handoff prose**: what the last session accomplished, decided, and left to
  do. Written deliberately by a human or agent; not derivable.
- **Session existence**: whether a session has been started for this branch at
  all. The one piece of session state that is not derivable from spec artifacts
  — read from the session event log, which records the start as it happens
  rather than caching a conclusion about it.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A session started after artifacts changed reports the correct
  pipeline position with no command run in between.
- **SC-002**: Zero values reported by any command originate from a file written
  by an earlier session, except handoff prose.
- **SC-003**: Every reachable pipeline state renders a statement that is true in
  that state — including the two that are false today, an empty feature
  directory and a finished pipeline.
- **SC-004**: Nothing written or printed when a session ends asserts a
  completion, and a reader can name what each line was derived from.
- **SC-005**: After one command runs in a state directory carrying files from a
  previous version, no file remains there that any reader could mistake for
  current truth.

## Assumptions

- Pre-specify design context loaded from
  `/Users/andremarin/Development/wfctl-specs/74-session-truth-ownership/design.md`.
- Level-2 ownership is settled in `session-state-is-re-derived` (accepted) and
  `pipeline-state-is-one-payload` (proposed). This spec does not re-decide them.
- This feature implements the internal half of the proposed record — state as a
  name, symbols at print time. The payload's external surface, and the schema
  that would go with it, belong to a separate issue written after acceptance.
- The verification record and the design gate are unchanged by this feature.
- `load_agentconfig` having no callers is noted but not in scope.

## Validation Strategy _(mandatory)_

- `uv run --frozen pytest -q`, `uv run --frozen ruff check wfctl/ tests/`,
  `uv run --extra dev mypy wfctl/` — the project's definition of done.
- One test per reachable pipeline state from `design.md`'s level-1 pass,
  asserting the rendered line in that state, with `NO_COLOR` pinned.
- A test that advances artifacts without running a session command and asserts
  the reported position changed.
- A test asserting no output path emits a completion claim when a session ends.
