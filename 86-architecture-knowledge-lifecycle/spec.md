# Feature Specification: Architecture Knowledge Lifecycle

**Feature Branch**: `86-architecture-knowledge-lifecycle`
**Created**: 2026-08-26
**Status**: Draft
**Input**: Epic #86 — architecture as managed knowledge rather than a one-time artifact. Pre-specify design context loaded from `design.md` in this feature directory.

## Clarifications

### Session 2026-08-26

- Q: FR-010 — how does the advance check distinguish "no boundary changed" from "not recorded"? → A: An explicit declaration, recorded where it lands in the change under review. The check cannot verify a judgment; it exists to stop the question going unanswered, turning a silent omission into a claim a reviewer can disagree with.
- Q: What happens when the architecture root resolves outside the working tree? → A: Allowed, but warned. The configured location is honoured; the system names what an out-of-tree root costs — records no longer share a commit with the code implementing them, and no longer reach anyone who clones the repository.
- Q: How are records identified, given parallel worktrees? → A: By descriptive slug alone, with no sequence number. Monotonic numbering collides when two worktrees create a record in overlapping windows, which is this repository's normal case, and renumbering to resolve a collision breaks inbound supersession links. Ordering is carried by status and dates, which state it more precisely than sequence does.
- Q: The epic says "promoted", the ADR format says "accepted" — which is the status value? → A: `accepted`, matching the adopted format. The epic's promotion language remains as prose describing the transition. No command name depends on this: the retirement of the existing promotion command in FR-011 is driven by it being orphaned, not by terminology, and is not a rename into this feature.
- Q: How does the model express a decision that ended without a successor? → A: A fifth status, `retired`, reached from `accepted`. The reason is carried by the existing log line. `superseded` implies a successor record and `rejected` means never-adopted, so neither can express a decision that governed the work and then ended — `wfctl checkpoint`'s removal is the worked example.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - An architectural decision survives the session that made it (Priority: P1)

A developer works through a design conversation and reaches a decision about who
owns a piece of truth — which side computes a value, and why the other side
cannot. Today that answer is spoken, occasionally written into a design
document, and never seen again. In this story it becomes a durable record filed
under the project's architecture root, committed alongside the code that
implements it.

**Why this priority**: Nothing else in this feature has value without it. The
projection has nothing to project and the enforcement check has nothing to check
until decisions are actually being captured. It is also the story that tests the
epic's core bet — that capture wired into the design gate produces records where
an instruction to write them did not.

**Independent Test**: Run a design session that reaches an ownership decision.
Confirm a record exists under the architecture root, carrying the decision, the
rejected alternatives, and a statement of which side owns the truth and why the
other side cannot compute it. Delivers value alone: the reasoning is now
recoverable by anyone who opens the file.

**Acceptance Scenarios**:

1. **Given** a design conversation that reaches an ownership decision, **When**
   the design gate is answered, **Then** a record is created under the resolved
   architecture root containing the decision, its rejected alternatives, and the
   ownership statement.
2. **Given** a project that has not configured an architecture root, **When** a
   record is created, **Then** it is written to the default location inside the
   repository and is tracked by version control.
3. **Given** a project that has configured an architecture root, **When** the
   root is queried, **Then** the configured location is reported rather than the
   default.
4. **Given** an existing accepted record, **When** a later decision replaces it,
   **Then** a new record is written and the original's status changes to
   superseded, with the original's body left unmodified.

---

### User Story 2 - An agent sees only the decisions currently in force (Priority: P2)

An agent begins work in the repository. Alongside the guidance file it already
loads, it receives the set of architectural decisions that currently bind —
and only those. Superseded and rejected decisions remain on disk for people to
read, but never reach the agent as if they were live.

**Why this priority**: Records nobody loads are records nobody follows. This is
also what makes it safe to consolidate misplaced knowledge out of the guidance
file in Story 4 — without it, moving anything makes it unreachable.

**Independent Test**: With one record on disk in each status — accepted,
proposed, superseded, rejected, retired — confirm that the projection presents
exactly the accepted one, and that the other four remain readable directly.
Delivers value alone: an agent can state which decisions bind without opening the
directory.

**Acceptance Scenarios**:

1. **Given** an architecture root containing accepted and superseded records,
   **When** the in-force set is requested, **Then** only accepted records are
   presented.
2. **Given** the same root, **When** a superseded record is opened directly,
   **Then** its full content is readable and its status is visible as superseded.
3. **Given** an architecture root with no records, **When** the in-force set is
   requested, **Then** the result reports an empty set rather than failing.
4. **Given** a new session in a repository with accepted records, **When** the
   session starts, **Then** the in-force set is available to the agent without
   the agent being told to go looking for it.

---

### User Story 3 - A design step cannot be completed without recording its boundary (Priority: P3)

The pipeline refuses to advance past the design step when a change draws a new
boundary and no record exists for it. A change that draws no new boundary
answers that explicitly and advances.

**Why this priority**: This is enforcement, and it is deliberately last. Story 1
tests whether capture happens unaided; if it does, this story may not be needed.
If it does not, Story 1's failure is the evidence that justifies building it.

**Independent Test**: Attempt to advance past the design step with no record
present, and confirm the advance is refused with a message naming what is
missing. Then answer that no boundary changed, and confirm the advance proceeds.

**Acceptance Scenarios**:

1. **Given** a feature at the design step with no architecture record, **When**
   advancing is attempted, **Then** the advance is refused and the message names
   the record that is missing and how to create it.
2. **Given** a feature that draws no new boundary, **When** that is stated
   explicitly, **Then** the advance proceeds and the statement is retained.
3. **Given** a feature at the design step with a record present, **When**
   advancing is attempted, **Then** it proceeds without prompting.

---

### User Story 4 - Knowledge lives in exactly one place (Priority: P3)

Guidance that constrains the system moves out of the agent guidance file and
into records. Facts about a single file move into that file. What remains in the
guidance file is guidance for the worker: how to run the tests, what to name
things, what the conventions are.

**Why this priority**: It is the payoff of the model — no duplication to keep in
sync — but it is strictly dependent on Story 2. Moving knowledge before the
projection exists puts it somewhere nothing reads.

**Independent Test**: After the move, ask an agent in a fresh session to make a
change to a skill. Confirm it edits the source tree rather than the installed
output — the specific failure that the relocated knowledge exists to prevent.

**Acceptance Scenarios**:

1. **Given** guidance that constrains the system rather than the worker, **When**
   placement is applied, **Then** it exists as a record and not in the guidance
   file.
2. **Given** a fact describing one specific file, **When** placement is applied,
   **Then** it is expressed in that file and not in the guidance file.
3. **Given** knowledge relocated out of the guidance file, **When** a fresh
   session begins, **Then** that knowledge still reaches the agent through the
   in-force set.

---

### Edge Cases

- A record's status value is absent or unrecognized — it must not silently
  default to in-force, since presenting an unreviewed decision as binding is the
  failure the status field exists to prevent.
- The architecture root is configured to a location that does not yet exist —
  creating the first record must not fail on the missing directory.
- Two records claim to supersede the same predecessor.
- A record is superseded by one that is itself later superseded; the in-force set
  must present only the final one.
- The retired promotion command is invoked from a stale script or muscle memory
  after removal — the failure must name what replaced it rather than reporting an
  unknown command.
- A repository has an architecture root configured outside the working tree, as
  this repository already does for specs.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST resolve an architecture root from, in order: an
  environment override, this repository's recorded configuration, the main
  checkout's recorded configuration, then a default location inside the
  repository.
- **FR-002**: Users MUST be able to ask the system where the architecture root
  resolves to, without inferring it from a path convention.
- **FR-002a**: When the architecture root resolves outside the working tree, the
  system MUST honour it and MUST warn what that costs: records no longer share a
  commit with the code implementing them, and no longer reach anyone who clones
  the repository. The reasoning that puts specs outside the tree does not
  transfer — specs are per-feature and disposable, records are permanent and
  shared.
- **FR-003**: A record MUST capture the decision, the alternatives that were
  rejected, and a statement naming which side owns the truth in question and why
  the other side cannot compute it.
- **FR-004**: Every record MUST carry an explicit status drawn from a closed set:
  proposed, accepted, superseded, rejected, retired.
- **FR-004a**: `retired` MUST be reachable from `accepted` and MUST NOT require a
  successor record. It expresses a decision that governed the work and then
  ended, which neither `superseded` (implies a successor) nor `rejected` (means
  never adopted) can state. The reason is carried by the record's log line.
- **FR-005**: System MUST treat an accepted record's body as immutable —
  replacing a decision creates a new record and changes only the predecessor's
  status.
- **FR-006**: The design gate that asks who owns a piece of truth MUST produce
  the record directly, rather than producing prose that is later copied into one.
- **FR-007**: System MUST be able to present the set of records currently in
  force, containing accepted records only.
- **FR-008**: Records that are proposed, superseded, rejected or retired MUST
  remain readable on disk and MUST NOT appear in the in-force set. Only
  `accepted` places a record in force.
- **FR-009**: The in-force set MUST reach an agent at session start through the
  same path as existing session guidance, without requiring the agent to be
  instructed to search for it.
- **FR-010**: System MUST refuse to advance past the design step when a change
  draws a new boundary and no record exists, and MUST accept an explicit
  declaration that no boundary changed.
- **FR-010a**: A "no boundary changed" declaration MUST be persisted where it
  appears in the change under review, so that the claim is visible to a reviewer
  rather than made silently. The system does not attempt to verify the
  declaration: whether a change draws a boundary is a judgment with no objective
  test, unlike completion, which either exits zero or does not. The check's
  purpose is to prevent the question going unanswered, not to catch a wrong
  answer.
- **FR-011**: System MUST remove the existing promotion command and its candidate
  file, which today read input nothing produces and write output nothing consumes.
- **FR-012**: Placement of knowledge MUST follow a stated rule: a fact about one
  file belongs to that file, a constraint on the system belongs in a record, and
  guidance for the worker belongs in the agent guidance file.
- **FR-013**: System MUST state, in a durable and discoverable place, the
  condition under which the in-force projection would not have needed to be a
  command — so that a later reader can retire it rather than inherit it.

## Key Entities

- **Architecture Decision Record**: One decision, addressable by a stable
  identifier — a descriptive slug, carrying no sequence number, so that records
  created concurrently in separate worktrees never collide and never need
  renaming. Holds the decision, its rationale, the rejected alternatives, the
  ownership statement, a status, and a link to any record it supersedes.
- **Architecture Root**: The resolved location where a repository's records live.
  Configurable per repository, defaulting to a version-controlled location inside
  the repository.
- **In-Force Set**: The projection of records whose status is accepted. Derived,
  never authored; the records are the source of truth.
- **Agent Guidance File**: The existing hand-authored file describing how to work
  in the repository. After this feature it holds worker guidance only.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Of the next three features that reach the design step after Story 1
  ships, all three produce either an architecture record or an explicit statement
  that no boundary changed. The baseline this replaces is zero of eleven.
- **SC-002**: An agent beginning a fresh session can name the decisions currently
  in force without opening the architecture directory or being asked to look.
- **SC-003**: Across ten sessions, zero instances of a superseded decision being
  presented or acted on as if it were in force.
- **SC-004**: After knowledge is relocated out of the guidance file, an agent
  asked in a fresh session to change a skill edits the source tree rather than the
  installed output in three of three trials.
- **SC-005**: The reasoning behind any in-force decision is recoverable by opening
  a single file, with no need to consult version-control history to understand why
  the decision holds.

## Validation Strategy _(mandatory)_

- `uv run pytest -q` — the full suite, green.
- `uv run ruff check wfctl/ tests/` and `uv run mypy wfctl/` — both clean.
- `wfctl doctor` — exit 0, no finding that still stands.
- Path resolution: tests covering each leg of the resolution order in FR-001,
  including a root configured outside the working tree and a root that does not
  yet exist.
- Projection: tests asserting that each status value is included or excluded from
  the in-force set, including an absent or unrecognized status.
- Supersession: a test asserting the predecessor's body is unchanged and only its
  status differs.
- Removal: a test asserting the retired promotion command is gone and its failure
  names the replacement.
- Skills changed under the agent tree are not verified by the suite. Run
  `wfctl install-skills` and exercise the design gate end to end, confirming a
  record is produced.

## Assumptions

- Pre-specify design context loaded from `design.md` in this feature directory.
- The record format follows the MADR simple shape with one added field for
  ownership of truth. Full MADR — decision-makers, consulted, informed — is
  excluded as team ceremony a small repository leaves blank.
- The architecture root resolution mirrors the existing spec root resolution
  exactly, including the main-checkout fallback. That fallback may prove
  unnecessary, since a version-controlled in-tree default resolves identically in
  every worktree; it is included for consistency and flagged in `design.md` as
  reviewable.
- Existing decisions are not backfilled in bulk. Only the guidance-file content
  identified as misplaced is relocated, plus a small number of seed records for
  decisions currently contested.
- Version control supplies the edit history of each record. Records carry only
  what version control cannot answer: which decision replaced which, why, and the
  current status.
- The identifier scheme is a descriptive slug with no sequence number, departing
  from the numbering half of ADR convention. The convention's purpose — a clear
  log of which decisions governed and for how long — is served by explicit status
  values and supersession links, which state it more precisely than sequence.
  Nothing here consumes external ADR tooling that would expect numbering.
