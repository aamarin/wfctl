# Feature Specification: is a session open now?

**Feature Branch**: `200-is-a-session-open-now`
**Created**: 2026-09-13
**Status**: Draft
**Input**: Issue #200 — "session_started cannot tell a running session from one that ran once — a gate on it covers only a branch's first session"

## Clarifications

### Session 2026-09-13

- Q: Does this feature include the caller-side wiring that presents the identity, or only wfctl's own surface? → A: Both — the surface and the session-opening workflow that presents to it, because wfctl ships that workflow.
- Q: Is a takeover visible, or does the branch quietly change hands? → A: Recorded on the branch's event record and reported by status.
- Q: What happens on a branch whose session was recorded before identities existed, when an identified session arrives? → A: Takeover — the identified session takes the branch.
- Q: Does the existing "has a session ever run here" answer change meaning, or does a second answer carry the new question? → A: It keeps its meaning; a second, distinct answer carries the new question.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A second conversation is told the truth (Priority: P1)

Someone opens a new conversation on a branch that has already had a development
session — a fresh chat, a resumed pane, an unattended agent picking the branch
up — and starts pipeline work without announcing itself. Today every gate that
asks "is a session open?" waves it through, because the only truth available is
"a session ran here once". The work proceeds, and its findings land in
scrollback that nobody reads.

After this feature, the gate recognises that the conversation in front of it is
not the one that opened the session, says so in its own words, and sends the
conversation to `/start-session`.

**Why this priority**: This is the defect. Every other story in this spec
protects something that already works; this one is the only story that changes
a wrong answer into a right one.

**Independent Test**: On a branch with a recorded session, present a session
identity that was never recorded and invoke a gated step. The gate must refuse
and name the remedy. Ship only this story and the defect in #200 is closed.

**Acceptance Scenarios**:

1. **Given** a branch whose session was opened by conversation A, **When**
   conversation B presents its own identity and invokes a gated step, **Then**
   the gate refuses and tells B to run `/start-session`.
2. **Given** that refusal, **When** the reader looks at its wording, **Then** it
   describes the conversation as unrecognised — not the branch as fresh, which
   is a different and already-correct message.
3. **Given** a branch whose session ended cleanly, **When** any conversation
   invokes a gated step without starting a session, **Then** it is refused the
   same way and by the same wording, because the remedy is the same.

---

### User Story 2 - A displaced conversation recovers with one command (Priority: P2)

The conversation refused in Story 1 has to be able to proceed. Without a way
back it is deadlocked: it cannot do pipeline work, it cannot wrap the session
up, and repeating the command that opens a session does nothing on a branch that
already has one.

Running `/start-session` takes the branch over. The conversation that held it
before recovers the same way, and neither needs a person to clear state by hand.

**Why this priority**: Without it Story 1 converts a silent wrong answer into a
loud dead end, which is not obviously an improvement. It is P2 rather than P1
only because it has no value on its own.

**Independent Test**: From the refused state, run the session-opening command
once and confirm the same gated step now passes. No file is deleted, no flag is
passed, nothing is edited by hand.

**Acceptance Scenarios**:

1. **Given** conversation B was refused, **When** B opens a session, **Then** the
   branch records B as its session and B's gated steps pass.
2. **Given** B now holds the branch, **When** A returns and invokes a gated step,
   **Then** A is refused with the Story 1 wording and recovers by the same route.
3. **Given** a conversation that already holds the branch, **When** it opens a
   session again, **Then** nothing about the branch's recorded state changes.
4. **Given** a conversation that does not hold the branch, **When** it tries to
   wrap the session up, **Then** it is refused — ending a session is not a way
   to take one over.

---

### User Story 3 - A repo nobody wired up is untouched (Priority: P3)

Most repositories that install wfctl will never tell it who is calling. Their
host exports no session identity, or exports one the project has not connected.
Those repositories must see exactly the behaviour they see today: the same gates,
the same passes, the same refusals, the same wording.

**Why this priority**: It constrains the feature rather than adding to it, and
it is the constraint most easily lost during implementation. Treating an absent
identity as grounds for refusal would regress every unwired repository — a
larger blast radius than the defect being fixed.

**Independent Test**: With no session identity presented at all, exercise every
gate this feature touches and diff the outcomes against the released behaviour.
They must be identical.

**Acceptance Scenarios**:

1. **Given** no session identity is available, **When** any gated step runs on a
   branch with a recorded session, **Then** it behaves exactly as the released
   version does.
2. **Given** no session identity is available, **When** a session is opened,
   **Then** the branch records a session and nothing about identity is invented.
3. **Given** a repository that starts presenting an identity partway through a
   branch's life, **When** the first identified session opens, **Then** it takes
   the branch over rather than being refused.

---

### Edge Cases

- **The host changes the identity more often than a conversation changes.** If
  what wfctl is handed rotates per command, every command reads as a takeover
  and the branch's record fills with sessions that never existed. wfctl cannot
  detect this; the project that wires the identity in is where it is caught.
- **A session dies without wrapping up.** Nothing clears the branch's record, and
  nothing needs to: the next conversation presents a different identity and takes
  over. There is no stale-state cleanup path to run, and no command that leaves a
  branch unusable after a crash.
- **A sub-agent or nested run inside an existing conversation.** If the inner run
  presents a different identity than its parent, it takes the branch over from
  the conversation that spawned it. Whether a host's nesting marker can be
  trusted to prevent this is unresolved (see Assumptions).
- **The same identity on two branches at once.** Each branch records its own
  session independently; holding one branch says nothing about another.
- **A command typed by hand rather than reached through the pipeline.** The
  re-inference command is reachable directly, so it carries its own check rather
  than relying on a caller to have run one.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The session-opening command MUST accept a session identity supplied
  by its caller and record it as given.
- **FR-002**: wfctl MUST NOT derive, parse, interpret, or infer a session
  identity from its own process, its environment, or any host-specific name.
- **FR-003**: Status MUST report whether a session is open **for the caller
  presenting an identity** as an answer distinct from whether the branch has ever
  had one. The existing "has a session ever run here" answer MUST keep its
  present meaning, so that the never-had-a-session case stays answerable.
- **FR-004**: Opening a session while presenting an identity that differs from
  the branch's recorded one MUST record the new identity as the branch's session.
- **FR-005**: Opening a session while presenting the branch's recorded identity
  MUST leave the branch's recorded state unchanged.
- **FR-006**: When no identity is presented, every gate MUST behave exactly as it
  does in the released version, with no new refusal and no changed wording.
- **FR-007**: The refusal in the unrecognised-conversation case MUST use wording
  distinct from the never-had-a-session case, describing the conversation rather
  than the branch.
- **FR-008**: Wrapping a session up MUST remain available only to the conversation
  that holds the branch.
- **FR-009**: The re-inference command MUST carry its own session check, because
  it is reachable without passing through any gate.
- **FR-010**: The identity MUST be carried on the branch's existing event record,
  not in a separate file that a crash could leave stale.
- **FR-011**: Skills and commands MUST obtain this answer from wfctl, never by
  reading the branch's event record themselves.
- **FR-012**: A branch whose recorded session was opened without an identity MUST
  accept the first identified session as a takeover rather than refusing it.
- **FR-013**: The session-opening workflow wfctl ships MUST present the host's
  session identity when the host exposes one, and MUST NOT name a host-specific
  variable in any committed hook.
- **FR-014**: A takeover MUST be recorded on the branch's event record and MUST be
  reported by status, so that neither the displaced conversation nor a later
  reader has to read that record directly to learn the branch changed hands.

## Key Entities

- **Session identity**: an opaque value supplied by whatever is calling wfctl,
  distinguishing one conversation from the next. wfctl stores it and compares it
  for equality; it has no other meaning to wfctl.
- **Branch session record**: the append-only history of what has happened on a
  branch, which already records that a session opened and now also records which
  identity opened it.
- **Gate**: any point in the pipeline that asks whether a session is open before
  allowing work to proceed.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: On a branch with a recorded session, a conversation that did not
  open it is refused on 100% of gated steps, where today it passes on 100%.
- **SC-002**: A repository presenting no session identity shows zero behavioural
  differences from the released version across every gate this feature touches.
- **SC-003**: A refused conversation reaches a working state in exactly one
  command, with no file edited, deleted, or inspected by hand.
- **SC-004**: No sequence of interrupted sessions leaves a branch in a state that
  requires manual cleanup before work can continue.
- **SC-005**: A reader shown the refusal can tell, without opening any file,
  whether the branch is fresh or already held by another conversation.
- **SC-006**: Every answer the released version gives to "has a session ever run
  on this branch" is unchanged, measured across the same branch states.
- **SC-007**: A conversation displaced by a takeover learns that the branch
  changed hands from what status prints, without reading any file itself.

## Assumptions

- Pre-specify design context loaded from
  `specs/200-is-a-session-open-now/design.md`. Its seven-row decisions ledger is
  the source for FR-001 through FR-010, and its four behaviour states are the
  source for the three user stories.
- The architectural boundary is settled and accepted: the caller supplies the
  identity and wfctl records it verbatim
  (`docs/architecture/session-identity-comes-from-the-caller.md`). The structural
  choice — the identity rides on the existing event record — is proposed
  (`docs/architecture/design/200-session-id-rides-on-the-start-event.md`).
- The host is assumed to change its session identity when and only when a
  conversation's context is lost. Measured across a context clear in this
  worktree and reproduced independently on 2026-09-13; **not** measured across a
  long session, which is the case that would falsify it.
- Whether a host's nesting marker can distinguish a sub-agent from a top-level
  conversation is unresolved. The measurement found the marker set in a
  conversation with no parent, so no requirement here depends on it.
- Which host variable a project presents is a wiring decision belonging to that
  project, not to wfctl. Because wfctl stores an opaque value, a wrong choice is
  a mapping to correct rather than a design to redo.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/` —
  the repository's definition of done, all three green.
- `uv run wfctl doctor` — no finding that still stands.
- Unit coverage for the identity comparison: same identity, different identity,
  absent identity, and a branch recorded before identities existed (FR-004,
  FR-005, FR-006, FR-012).
- Unit coverage asserting the two refusals are distinct strings (FR-007).
- A regression test pinning released behaviour when no identity is presented,
  asserted against the gate surface rather than a single call site (FR-006,
  SC-002).
- Manual two-conversation exercise on a scratch branch: open a session, present a
  second identity, confirm the refusal and its wording, take over, confirm the
  first conversation is now the one refused (SC-001, SC-003, SC-005).
- `uv run wfctl install-skills` and exercise any changed skill wording by hand —
  the suite checks that skills ship and cross-reference, not that they read well.
