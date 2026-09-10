# Feature Specification: promote a decision to accepted

**Feature Branch**: `321-promote-a-decision`
**Created**: 2026-09-09
**Status**: Draft
**Input**: Issue #321 — nothing promotes an architecture decision from `proposed` to `accepted`, so 14 of 24 records argue for nothing.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A maintainer makes a decision binding (Priority: P1)

A person has agreed to an architecture record — on the issue thread, in a review,
in a conversation that ended with a decision. They want the repository's contract
to say so, and they want a later reader to be able to ask where that agreement
happened.

**Why this priority**: This is the transition the feature exists for. Without it
nothing else in the feature has a subject.

**Independent Test**: Accept one record and confirm the architectural contract
now projects it, then open the file and confirm exactly two lines changed.

**Acceptance Scenarios**:

1. **Given** a record whose status is `proposed`, **When** the maintainer accepts
   it and says where the agreement happened, **Then** the record's status reads
   `accepted`, its history gains one dated line carrying that citation, and
   nothing else in the file differs.
2. **Given** that record is now accepted, **When** anyone reads the architectural
   contract, **Then** the record appears in it and the count of records withheld
   from the contract has dropped by one.
3. **Given** a record that has not been accepted, **When** anyone reads the
   architectural contract, **Then** it is still withheld — being on the trunk,
   having shipped, or having a passing pipeline does not put it in force.

---

### User Story 2 - A second acceptance is refused (Priority: P1)

Someone runs the acceptance a second time — a repeated command, a script, a
second person who did not know. The record's history must not gain a second line
claiming a second agreement.

**Why this priority**: The citation is the whole evidentiary value of the
transition. A history that records agreements which did not happen is worse than
one that records none, and it is silent.

**Independent Test**: Accept a record twice and confirm the second attempt
changes no bytes and reports why.

**Acceptance Scenarios**:

1. **Given** a record already accepted, **When** it is accepted again, **Then**
   the attempt is refused, the file is unchanged, and the message says the record
   is already accepted and when.
2. **Given** a record that is superseded, rejected or retired, **When** it is
   accepted, **Then** the attempt is refused and the message says a decision that
   is binding again is a new record rather than a reopened one.
3. **Given** a record whose status cannot be read, **When** it is accepted,
   **Then** the attempt is refused and the message says to fix the frontmatter,
   because accepting it would overwrite whatever it says.

---

### User Story 3 - The unaccepted set is nameable (Priority: P2)

Someone knows there are records not in force — the contract already tells them
how many — and wants to know which ones, at the moment they are trying to act on
one.

**Why this priority**: The count without the names is why the backlog reached
fourteen. It is P2 because the transition itself is usable without it, by anyone
who already knows a slug.

**Independent Test**: Ask to accept without naming a record, and confirm the
promotable slugs are listed and nothing was changed.

**Acceptance Scenarios**:

1. **Given** a repository with proposed records, **When** acceptance is requested
   with no record named, **Then** every promotable slug is listed, nothing is
   changed, and the request reports as unsuccessful.
2. **Given** a record name that is close to a real one but not exact, **When**
   acceptance is requested, **Then** the refusal names the near matches.
3. **Given** a repository whose records are all accepted, **When** acceptance is
   requested with no record named, **Then** the message says there is nothing to
   accept rather than printing an empty list.

---

### Edge Cases

- **A record with no history section.** The citation has nowhere to land, so the
  transition would change a status with no record of it having changed. Refused,
  and nothing is written — the same rule the existing supersede transition holds.
- **A record whose frontmatter declares the same key twice.** The status a reader
  sees is the last one; changing the first would log a transition the record does
  not carry. The line that is changed is the one a reader sees.
- **A record using Windows line endings.** Two lines change, not every line.
- **A record whose file does not end in a newline.** The new history line does not
  weld itself onto the previous entry.
- **A citation that is empty, or a placeholder copied from the help text.**
  Refused. A committed record whose evidence reads `<where>` is the un-auditable
  transition wearing the command that was supposed to prevent it.
- **A record outside the repository's own architecture root.** Out of scope: the
  root is resolved once and only records under it are addressable.
- **Interrupted mid-write.** The file is either its old contents or its new
  contents, never half of each.

## Clarifications

### Session 2026-09-09

Answered from the codebase and the tracker rather than asked, under
`auto_approve`. Each answer carries the basis it was decided on.

- **Non-Functional Quality Attributes — what date does the history line carry?**
  Q: The line is dated `YYYY-MM-DD` with no zone. Local or UTC?
  → A: **UTC.** Basis: every timestamp wfctl writes is UTC — `_session.py:38`,
  `_verify.py:174`, `_io.py:40`, `_archive.py:104` — and a column that is local
  for one contributor and UTC for another is not orderable. Decided against local
  date, which matches what the person running the command believes the date is:
  it is the friendlier answer for a single maintainer and it makes the field
  depend on where the maintainer was sitting. The cost is accepted and named — a
  maintainer west of UTC accepting late in the evening records tomorrow's date.

- **Non-Functional Quality Attributes — is the transition also written to the
  session event log?**
  Q: `events.jsonl` records `start`, `end`, `issue` and `notify-resolved`. Should
  acceptance join them?
  → A: **No.** Basis: the event log lives in the XDG state dir, is per-branch, and
  is not committed — it dies with the worktree, while the record it would describe
  outlives the branch (FR-010). Two durable answers to "when was this accepted"
  that can disagree is worse than one, and the record's own history is the answer
  a reader already opens the file for. Decided against logging it for
  observability: the observable artifact is the committed line.

- **Terminology & Consistency — accept or promote?**
  Q: The issue says "promote", the status is `accepted`, and the spec used both.
  → A: **`accept` is the verb; the status is `accepted`.** Basis: the status value
  is the fixed term (`_arch.STATUSES`), and a command whose name does not match
  the value it writes makes the reader hold two words for one transition.
  "Promotion" survives only in prose about the backlog of records awaiting one,
  where it names the class of pending work rather than the operation.

- **Edge Cases & Failure Handling — two acceptances at once.**
  Q: The refusal in FR-005 reads the status and then writes. What happens if two
  runs interleave between the read and the write?
  → A: **Accepted risk, stated rather than designed around.** Basis: the write is
  atomic (FR-011) so no file is ever half-written, but the read-then-write pair is
  not, so a genuine race appends two history lines. The actor is a person at a
  local CLI on a record they have just agreed to; a lock would add durable state
  to a repository whose records carry none. Recorded as NFR-002 so a later reader
  finds it decided rather than missed.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST provide a way for a person to move one architecture
  record from `proposed` to `accepted`, addressed by that record's slug.
- **FR-002**: The system MUST require a citation — where the agreement happened —
  and MUST refuse an empty one or a placeholder, changing nothing.
- **FR-003**: The system MUST write the citation into the record's own history as
  one dated line, so a later reader finds it in the file rather than in a commit
  message or a review thread.
- **FR-004**: The system MUST change nothing in the record except its status key
  and the one appended history line.
- **FR-005**: The system MUST refuse to accept a record whose current status is
  not `proposed`, and MUST distinguish already-accepted, ended (superseded,
  rejected or retired) and unreadable in what it reports, because the reader's
  next action differs for each.
- **FR-006**: The system MUST refuse, changing nothing, when the record has no
  history section to append to or no status to change.
- **FR-007**: The system MUST name the records that could be accepted when asked
  to accept without a record named, and MUST report that request as unsuccessful.
- **FR-008**: The system MUST NOT infer acceptance from any signal it can compute
  on its own — a merge, a passing pipeline step, shipped code, or an assessment
  of the decision's risk.
- **FR-009**: The architectural contract MUST project a record once it is
  accepted and MUST continue to withhold every record that is not.
- **FR-010**: A record's acceptance MUST survive the branch that wrote it — it is
  a fact about the record, not about a run.
- **FR-011**: The write MUST be all-or-nothing.

### Non-functional Requirements

- **NFR-002**: The status check and the write are not atomic as a pair. Two
  simultaneous acceptances of one record can append two history lines; the
  write itself is still all-or-nothing. Accepted rather than locked — see
  Clarifications.
- **NFR-001**: The check is tamper-evident, not unforgeable. Nothing prevents an
  invented citation; what the requirement buys is that a promotion with nothing
  behind it must state something false in the file a reviewer reads.

## Key Entities _(include if feature involves data)_

- **Record**: one architecture decision, identified by its slug, carrying a
  status and a history. Already exists; this feature adds a transition it can
  make and one line it can gain.
- **Citation**: where a person agreed to the record — an issue, a review, a
  conversation named well enough for a reader to find it. Free text; the system
  checks that it is present and not a placeholder, never that it is true.
- **Architectural contract**: the projection of accepted records that a session
  reads to learn what binds the repository. Already exists; this feature changes
  what reaches it.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A person who has agreed to a record can make it binding in one
  command, and the command's output names the history line it wrote.
- **SC-002**: For every record in force, a reader can find where it was agreed
  without leaving the record file — 100% of accepted records carry a citation
  from this feature onward.
- **SC-003**: Accepting one record moves it from the withheld count into the
  contract: the contract's list grows by one and its withheld count drops by one.
- **SC-004**: Every refusal path leaves the record byte-identical, verified for
  all six refusals.
- **SC-005**: A person who knows a record exists but not its exact name reaches
  the right slug without reading the directory.
- **SC-006**: The evidence class the pipeline already names for accepted records
  becomes producible, so the work blocked on this transition can start.

## Assumptions

- Pre-specify design context loaded from `specs/321-promote-a-decision/design.md`.
- Authority is one repository-wide rule, not per-project configuration. No second
  project has asked for a different one, and a configurable authority question
  means a reader of an unfamiliar repository cannot tell who accepted a record
  without reading its configuration. Reversible: a policy setting can be added
  over this rule later and cannot be removed from under one.
- The fourteen records currently withheld are not accepted by this feature.
  Stating the rule and applying it to the backlog are separate reviews.
- `rejected` and `retired` gain no way to be reached. They have no consumer.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, and
  `uv run wfctl doctor` — this repository's definition of done, all four green.
- The existing supersede tests pass unchanged. They are the regression suite for
  the shared mutation the new transition reuses, which is why that body moves
  rather than being rewritten.
- Unit tests over the record file itself for each edge case above: repeated
  frontmatter key, Windows line endings, missing final newline, missing history
  section, and each of the three not-proposed statuses — asserting in every
  refusal that the file is unchanged.
- An end-to-end check through the real command in a temporary repository:
  accept one record, confirm the contract projects it and the withheld count
  drops; confirm a record left alone is still withheld.
- Console assertions pin `NO_COLOR`, per this repository's testing conventions.
