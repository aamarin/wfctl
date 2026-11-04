# Feature Specification: Session start loads the records for the branch's contexts

**Feature Branch**: `700-session-start-relevant-records`  
**Created**: 2026-11-03  
**Status**: Draft  
**Input**: User description: "Implement #700 from design.md in the feature directory"

## User Scenarios & Testing _(mandatory)_

The user here is the agent that runs `/start-session`, and the person who reads
its report. Each session starts by printing the accepted architecture records,
which bind the work. Today every accepted record prints, whatever the branch
changes.

### User Story 1 - A branch that lists its contexts sees only its records (Priority: P1)

An agent on a branch whose `design.md` lists the contexts it changes starts a
session. It reads the accepted records that apply to those contexts, plus every
record that binds every change. It also reads how many records were left out and
the command that prints them.

**Why this priority**: This is the whole point of the issue. It removes records
the branch never touches from every session start.

**Independent Test**: Write a `design.md` whose `Contexts` line names one
context, run `wfctl arch context`, and check that the output holds every
accepted record that governs that context or has no `governs` field, and none of
the others, and that a line names the count left out and `wfctl arch context
--all`.

**Acceptance Scenarios**:

1. **Given** a `Contexts` line naming `install-and-drift`, and an accepted
   record that governs only `session-continuity`, **When** the agent runs
   `wfctl arch context`, **Then** that record isn't printed, and the output
   says 1 record was left out and that `wfctl arch context --all` prints it.
2. **Given** the same branch and an accepted record with no `governs` field,
   **When** the agent runs `wfctl arch context`, **Then** that record is
   printed.
3. **Given** the same branch and an accepted record that governs
   `install-and-drift` and `workmux`, **When** the agent runs `wfctl arch
   context`, **Then** that record is printed.
4. **Given** a branch whose contexts cover every governed record, **When** the
   agent runs `wfctl arch context`, **Then** the output is the same as it is
   today, with no line about records left out.

---

### User Story 2 - A branch that hasn't listed its contexts sees every record (Priority: P1)

An agent on a new branch, or on a branch that skips the spec pipeline, starts a
session. Nothing says which contexts the branch changes, so it reads every
accepted record, and a line says why nothing was left out.

**Why this priority**: The issue's Done when says a binding record is never
left out. When wfctl can't tell which records apply, printing all of them is
what keeps that promise.

**Independent Test**: Run `wfctl arch context` on a branch with no spec folder,
then with a `design.md` that has no `Contexts` line, and check that every
accepted record prints in both cases, with the reason line.

**Acceptance Scenarios**:

1. **Given** a branch with no spec folder, **When** the agent runs `wfctl arch
   context`, **Then** every accepted record prints, followed by a line saying
   `design.md` lists no contexts for this branch yet.
2. **Given** a `design.md` with no `Contexts` line, or an empty one, **When**
   the agent runs `wfctl arch context`, **Then** the result is the same as in
   scenario 1.
3. **Given** a `Contexts` line naming `sesion-continuity`, which isn't on the
   domain page, **When** the agent runs `wfctl arch context`, **Then** every
   accepted record prints, followed by a warning that names the unknown name.
4. **Given** a repository whose domain page has no name list, **When** the
   agent runs `wfctl arch context`, **Then** the output is the same as it is
   today.

---

### User Story 3 - The session report and `--all` agree with the narrowed set (Priority: P2)

The person reading the session report sees how many records apply to the branch
out of how many are accepted, and the command that prints all of them. An agent
that needs a record left out runs `wfctl arch context --all`.

**Why this priority**: An agent that doesn't know records were left out can't
go looking for them. The report is the first thing a restarted session reads.

**Independent Test**: With a `Contexts` line that leaves records out, run
`wfctl status --session` and check that the `Records` line's counts match what
`wfctl arch context` printed, then run `wfctl arch context --all` and check that
every accepted record prints.

**Acceptance Scenarios**:

1. **Given** a branch where 6 of 28 accepted records apply, **When** the agent
   runs `wfctl status --session`, **Then** the `Records` line reads `Records: 6
   of 28 accepted apply to this branch · `wfctl arch context` prints them,
   `--all` prints every one`.
2. **Given** a branch where the set isn't narrowed, **When** the agent runs
   `wfctl status --session`, **Then** the `Records` line reads as it does
   today.
3. **Given** any branch, **When** the agent runs `wfctl arch context --all`,
   **Then** every accepted record prints, with no line about the branch's
   contexts.
4. **Given** any branch, **When** a consumer reads `wfctl status --json
   --session`, **Then** `applying_records` holds the narrowed count, or `null`
   when the set isn't narrowed.

---

### Edge Cases

- A record whose `governs` field names only outside parties, such as
  `trackers`, prints when the branch's `Contexts` line names that party, and is
  left out otherwise.
- A record whose `governs` field names something not on the domain page is
  already a `wfctl doctor` error. For selection, it applies only when the
  branch lists the same name, which the unknown-name rule then catches.
- A branch shares its spec folder with an epic. The `Contexts` line in that
  folder's `design.md` is the one used, the same one the design checks read.
- The spec folder can't be read. The selection treats that as no `Contexts`
  line and prints every record.
- Proposed, superseded, rejected, and retired records are never printed by
  `arch context` and aren't counted as left out.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: When the repository has a name list and the branch's `Contexts`
  line names only names on that list, `wfctl arch context` MUST print exactly
  the accepted records whose `governs` field shares a name with the line, plus
  every accepted record with no `governs` field.
- **FR-002**: When FR-001 leaves out at least one accepted record, the output
  MUST say in the header how many records apply out of how many are accepted,
  print the branch's contexts, and end with a line giving the count left out
  and the command `wfctl arch context --all`.
- **FR-003**: When FR-001 leaves out no record, the output MUST be the same as
  it is today.
- **FR-004**: When the branch has no spec folder, no `design.md`, or a
  `design.md` with no `Contexts` line or an empty one, `wfctl arch context`
  MUST print every accepted record and a line saying the branch lists no
  contexts yet.
- **FR-005**: When the `Contexts` line names something not on the domain page,
  `wfctl arch context` MUST print every accepted record and a warning naming
  the first unknown name.
- **FR-006**: When the repository has no name list, `wfctl arch context` MUST
  print what it prints today.
- **FR-007**: `wfctl arch context --all` MUST print every accepted record and
  no line about the branch's contexts.
- **FR-008**: The session report's `Records` line MUST give the applying count
  and the total, and name `--all`, whenever `arch context` would leave records
  out, and MUST read as it does today otherwise.
- **FR-009**: `wfctl status --json --session` MUST carry `applying_records`,
  the count FR-001 selects when it leaves records out, and `null` otherwise.
- **FR-010**: `arch context` and the session report MUST get the selection from
  one function, so their counts can't disagree.
- **FR-011**: The `start-session` skill MUST tell the agent that step 2 may
  print a subset, and that `wfctl arch context --all` prints the rest.
- **FR-012**: The `architecture-decisions` skill MUST say that a record which
  binds every change leaves the `governs` field out.

## Key Entities _(include if feature involves data)_

- **Branch contexts**: The names on the `Contexts` line of the branch's
  `design.md`, written by the agent at brainstorm.
- **Record scope**: A record's `governs` field, or its absence, written by the
  record's author.
- **Selection**: The records that apply, the count left out, and the reason
  nothing was left out when the set wasn't narrowed.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: In this repository today, a branch whose `Contexts` line names
  only `install-and-drift` prints 24 of the 28 accepted records. Of the 5
  records with a `governs` field, only `contexts-are-packages` names that
  context.
- **SC-002**: In every scenario under User Story 2, the number of records
  printed equals the number of accepted records.
- **SC-003**: In every scenario, the records printed plus the count left out
  equals the number of accepted records.
- **SC-004**: The session report's counts match `arch context`'s output in every
  scenario under User Story 3.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, with tests for each acceptance scenario above against a
  temporary arch root, domain page, and spec folder.
- `uv run ruff check wfctl/ tests/` and `uv run mypy`.
- `uv run python .github/scripts/check_imports.py` passes with no new baseline
  line.
- `uv run wfctl doctor` is green after `uv run wfctl install-skills`.
- By hand: run `wfctl arch context` with `WFCTL_SPEC_DIR` pointed at a scratch
  spec folder whose `Contexts` line names one context, and confirm the printed
  records include every record for that context and every record with no
  `governs` field. Then run it on a branch with no spec folder and confirm it
  prints every record.

## Assumptions

- Pre-specify design context loaded from
  `/Users/andremarin/Development/wfctl-specs/700-session-start-relevant-records/design.md`.
- The 23 accepted records with no `governs` field stay that way, since an
  accepted record's body is never edited.
- The level-2 record `branch-contexts-select-records` is accepted before the PR
  opens.

## Clarifications

### Session 2026-11-03

- Q: Should the narrowed output list the slugs of the records it left out, or
  only count them? → A: Only count them, beside the `wfctl arch context --all`
  command (FR-002). Basis: the issue's Done when asks for the count and the
  command, and a slug without its decision text gives the agent a name to guess
  from rather than a rule to follow.
- Q: When the branch shares an epic's spec folder, whose `Contexts` line
  narrows the set? → A: The `design.md` in the spec folder the branch resolves
  to, the same file the design checks read. Basis:
  `domain-page-names-contexts.md` and `_contexts.listed`, which take the
  resolved spec folder.
- Q: Does `wfctl arch context` exit non-zero when it prints a warning or leaves
  records out? → A: No, it exits 0 in every case. Basis: the command's
  docstring says an empty or unreadable set is not an error, and the
  `start-session` skill runs it as a read with nothing to stop on.
