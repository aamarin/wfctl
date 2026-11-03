# Feature Specification: Session report issue body

**Feature Branch**: `699-session-report-issue-body`  
**Created**: 2026-11-03  
**Status**: Draft  
**Input**: Issue #699 and `design.md` from brainstorm

## Clarifications

### Session 2026-11-03

- Q: Does the body hide whenever the report prints a handoff, or only after the branch's first session? → A: Whenever the report prints a handoff. This reverses #432's clarify answer, which printed the issue in full on every session.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A session with a handoff skips the issue body (Priority: P1)

An agent starts a session on a branch that already has a handoff. The session report prints the issue's header fields and a line naming the command that prints the full issue, but not the body. The handoff below it names the work, so the agent starts with what it needs and the body isn't loaded twice.

**Why this priority**: This is the saving the issue measured. In the #432 worktree the body was about 2.4k of the 9.4k tokens `/start-session` printed.

**Independent Test**: Build a session report with a handoff and an issue whose text has a header, a `--` line, and a body. The console output carries the header and the pointer line, and none of the body's lines.

**Acceptance Scenarios**:

1. **Given** a branch with a handoff and an issue whose tracker text has a `--` line, **When** the agent runs `wfctl status --session`, **Then** the `Issue (tracker text)` section prints the non-empty header fields, then the flush-left line ``Body left out, since the handoff below names the work. `wfctl issue view <id>` prints it.``, and no body line.
2. **Given** the same branch, **When** the agent runs `wfctl status --session --json`, **Then** the `issue_view` value still holds the whole tracker text, body included.

---

### User Story 2 - A session without a handoff still gets the body (Priority: P1)

An agent starts a session on a branch with no `session-summary.md`. Nothing else tells it what the work is, so the report prints the issue body as it does today.

**Why this priority**: Hiding the body here would leave the agent with no scope at all. It shares P1 with Story 1 because the change is only correct when both hold.

**Independent Test**: Build a session report with no handoff. The console output carries the body, unchanged from today.

**Acceptance Scenarios**:

1. **Given** a branch whose report prints `Handoff: none on this branch`, **When** the agent runs `wfctl status --session`, **Then** the `Issue (tracker text)` section prints the header and the body, and no pointer line.

---

### Edge Cases

- When the report prints a handoff but the tracker text has no `--` line, the report can't tell the header from the body, so it prints the whole text with no pointer line.
- When the issue read fails or times out, the section prints its reason code on one line, unchanged from today.
- When the handoff file exists but is empty, the report still prints the `Handoff (session-summary.md)` heading, so the body is hidden. The two sections use the same test, so they never disagree.
- When the issue's body is empty, the pointer line still prints. It stays true, since `wfctl issue view` prints the issue either way.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: When the report prints a handoff and the issue's tracker text has a `--` line, the console `Issue (tracker text)` section MUST print the header fields above the `--` line, with empty fields trimmed as today, and MUST NOT print the `--` line or anything below it.
- **FR-002**: In the case FR-001 covers, the section MUST end with one flush-left line naming the command that prints the full issue: ``Body left out, since the handoff below names the work. `wfctl issue view <id>` prints it.``, where `<id>` is the branch's issue key.
- **FR-003**: When the report prints `Handoff: none on this branch`, the section MUST print the issue text as it does today, header and body.
- **FR-004**: When the tracker text has no `--` line, the section MUST print the whole text as it does today, whether or not there is a handoff.
- **FR-005**: The JSON payload from `wfctl status --session --json` MUST keep the whole issue text in every case.
- **FR-006**: The body MUST be hidden under exactly the condition that makes the report print the `Handoff (session-summary.md)` heading, so the two sections can't disagree.
- **FR-007**: The `start-session` skill's row for an issue branch whose summary names no first action MUST tell the agent to read the issue with `wfctl issue view <id>` when the report left the body out. That row picks the next command from the issue, and asks the user when the issue body is empty, so it needs the body even when a handoff exists.

## Key Entities _(include if feature involves data)_

- **Issue text**: What the tracker's `view` verb returns. On GitHub that is a header of `field: value` lines, a `--` line, and the body.
- **Handoff**: The branch's `session-summary.md`, which the report already reads and prints last.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: On a branch with a handoff, the session report prints none of the issue body's lines.
- **SC-002**: On a branch with no handoff, the session report prints every line it prints today.
- **SC-003**: The JSON output is the same before and after the change, for both kinds of branch.

## Assumptions

- Pre-specify design context loaded from `design.md` in the branch's spec folder.
- GitHub is the only tracker wfctl ships, and its `view` verb prints a `--` line between the header and the body. Another backend's text with no `--` line prints whole, per FR-004.
- The report links the issue by command and not by URL, because `gh issue view` prints no URL and adding one means changing the tracker config every repo would have to reinstall.
- A worktree's first session often has a handoff already, because `worktree-handoff` copies the handoff that created the worktree into `session-summary.md`. That's why the condition is the handoff and not the session count (see Clarifications).

## Validation Strategy _(mandatory)_

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy
uv run wfctl doctor
```

- Unit tests on the session report's console rendering cover FR-001 to FR-006, and they assert on output with `NO_COLOR` pinned.
- `uv run wfctl status --session` in this worktree, which has a handoff, prints no issue body.
- The same command on a branch with no `session-summary.md` prints the body.
