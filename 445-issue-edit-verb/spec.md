# Feature Specification: issue edit verb

**Feature Branch**: `445-issue-edit-verb`  
**Created**: 2026-11-09  
**Status**: Draft  
**Input**: Pre-specify design context loaded from `design.md` in this spec folder. "`wfctl issue edit` changes an issue's title, its body, or both, through the tracker backend, and logs the write like every other `wfctl issue` write."

## Clarifications

### Session 2026-11-09

- Q: When the tracker doesn't support `edit`, or no tracker is set up, and both fields are given, how many notices print? → A: One. wfctl checks once before any write, prints the notice once, sends nothing, and exits 0.
- Q: When both fields are given and the title write fails, so the body is never sent, what prints after the backend's error? → A: `✗ title write failed, body was not sent`, with the backend's exit code. The plan walkthrough changed this from `✗ nothing changed, body was not sent`, since a write that times out can still land, and wfctl knows only that the call failed. The body-failure line changed the same way, to `✗ title changed, body write failed`.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Change an issue's body or title (Priority: P1)

An agent working on an issue finds that the issue covers more than its body
says, or that its title no longer describes it. The agent runs
`wfctl issue edit <id>` with `--body`, `--title`, or both. The issue changes in
the tracker, and wfctl records the write so a later session can see it
happened.

Currently, the agent has no way to do this through wfctl. It either calls the
tracker's own client, which leaves no record, or leaves a comment instead of
fixing the issue.

**Why this priority**: This is the whole feature. Without it, every title or
body change either goes around wfctl or doesn't happen.

**Independent Test**: Run `wfctl issue edit <id> --body "…"` against a real
issue, confirm the body changed in the tracker, and confirm the session's log
has one `issue-edit` entry.

**Acceptance Scenarios**:

1. **Given** a repository using the GitHub tracker, **When** the agent runs
   `wfctl issue edit 445 --title "New title"`, **Then** the issue's title
   changes, the body is left as it was, and one `issue-edit` write is recorded.
2. **Given** the same repository, **When** the agent runs
   `wfctl issue edit 445 --body "New body"`, **Then** the body changes, the
   title is left as it was, and one `issue-edit` write is recorded.
3. **Given** the same repository, **When** the agent passes both `--title` and
   `--body`, **Then** both fields change, the title first, and two
   `issue-edit` writes are recorded.

---

### User Story 2 - Know what happened when an edit goes wrong (Priority: P2)

An agent passes both fields and the second write fails, or passes no field, or
forgets the issue id. The output says what changed and what didn't, so the
agent doesn't retry a write that already landed or assume one that didn't.

**Why this priority**: A wrong report here leads the agent to redo or skip a
write on the issue. It matters only once story 1 works.

**Independent Test**: Use a backend whose body write fails, run an edit with
both fields, and check the output and the recorded writes.

**Acceptance Scenarios**:

1. **Given** a backend whose body write fails, **When** the agent passes both
   fields, **Then** the output shows the backend's error and the line
   `✗ title changed, body write failed`, the exit code is non-zero, and only the
   title write is recorded.
2. **Given** a backend whose title write fails, **When** the agent passes both
   fields, **Then** the output shows the backend's error and the line
   `✗ title write failed, body was not sent`, the exit code is non-zero, the body
   is never sent, and nothing is recorded.
3. **Given** any backend, **When** the agent runs `wfctl issue edit 445` with
   neither field, **Then** the output is `✗ 'edit' needs --title, --body, or
   both`, the exit code is 2, and nothing is sent to the tracker.
4. **Given** any backend, **When** the agent runs `wfctl issue edit --body "B"`
   with no issue id, **Then** the output is `✗ 'edit' requires an issue id`,
   the exit code is 2, and nothing is sent. The branch's issue is not used in
   place of a missing id.

---

### User Story 3 - Author a backend that supports edit (Priority: P3)

A user writing a tracker backend for a tracker other than GitHub, using the
`scaffold-tracker` skill, is asked whether the backend supports `edit` along
with every other verb. A backend that leaves `edit` out gets the same notice
every other missing verb gets.

**Why this priority**: Only users with a non-GitHub tracker need this, and the
GitHub backend ships with `edit` declared.

**Independent Test**: Run `wfctl tracker-check` on a config with an `edit`
entry and on one without it, and run `wfctl issue edit` against the second.

**Acceptance Scenarios**:

1. **Given** a tracker config declaring `edit` with `{id}`, `{field}`, and
   `{value}`, **When** `wfctl tracker-check` runs, **Then** the config is valid
   and `edit` is in the verb list.
2. **Given** a tracker config declaring `edit` with any other placeholder,
   **When** `wfctl tracker-check` runs, **Then** it reports the placeholder as
   not allowed.
3. **Given** a backend named `jira` with no `edit` verb, **When** the agent runs
   `wfctl issue edit 445 --body "B"`, **Then** the output is
   `ℹ Tracker 'jira' does not support 'edit' — skipped` and the exit code is 0.
4. **Given** the `scaffold-tracker` skill, **When** a user authors a backend,
   **Then** the verb table it asks about includes `edit`, and says that a
   tracker with differently named flags points the verb at a script.

---

### Edge Cases

- A body containing several lines, backticks, quotes, or `$(...)` reaches the
  tracker unchanged, since each value is passed as one argument and never
  through a shell.
- An empty string passed as `--title ""` or `--body ""` is sent as given. The
  tracker decides whether it accepts it, and GitHub refuses an empty title.
- No tracker configured: the edit prints the existing "No tracker configured"
  notice and exits 0, like every other verb.
- A tracker config that is missing or invalid: the edit prints the existing
  warning and exits 0, like every other verb.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: `wfctl issue edit <id>` MUST accept `--title`, `--body`, or both.
- **FR-002**: The tracker backend contract MUST allow an `edit` verb whose
  template takes `{id}`, `{field}`, and `{value}`, and no other placeholder
  except `{me}`. `tracker-check` MUST report an `edit` template that leaves out
  any of the three, since a template with no `{field}` writes every value to
  the same field.
- **FR-003**: wfctl MUST call the backend's `edit` once for each field given,
  title before body, with `field` set to `title` or `body` and `value` set to
  the text passed.
- **FR-004**: wfctl MUST stop at the first failed call and not send the
  remaining field.
- **FR-005**: When the title write succeeded and the body write failed, wfctl
  MUST print `✗ title changed, body write failed` after the backend's error and exit
  with the backend's exit code.
- **FR-005a**: When both fields were given and the title write failed, wfctl
  MUST print `✗ title write failed, body was not sent` after the backend's error
  and exit with the backend's exit code. When only one field was given and its
  write failed, wfctl prints the backend's error alone, since nothing else was
  requested.
- **FR-006**: wfctl MUST record each successful `edit` call as an `issue-edit`
  write, in the same log `comment`, `create`, `label`, and `close` writes go to.
- **FR-007**: With neither `--title` nor `--body`, wfctl MUST print
  `✗ 'edit' needs --title, --body, or both`, exit 2, and call nothing.
- **FR-008**: With no issue id, wfctl MUST print `✗ 'edit' requires an issue
  id`, exit 2, and call nothing. It MUST NOT use the branch's issue.
- **FR-009**: A backend without `edit` MUST get the existing unsupported-verb
  notice and exit 0. wfctl MUST check this once, before any write, so the
  notice prints once however many fields were given. The same holds for the
  "No tracker configured" notice and the invalid-config warning.
- **FR-010**: The shipped GitHub backend MUST declare
  `"edit": ["gh", "issue", "edit", "{id}", "--{field}", "{value}"]`.
- **FR-011**: The `scaffold-tracker` skill's verb table MUST list `edit` with
  its placeholders, and say that a tracker whose flags aren't named `--title`
  and `--body` points the verb at a script.
- **FR-012**: The `wfctl issue` help text MUST list `edit` and its options.

## Key Entities _(include if feature involves data)_

- **Recorded write**: one entry in the session's log of tracker writes, named
  `issue-edit` for this verb. A restarted session reads these to know that the
  previous one made an edit. The entry holds only the name, so it doesn't say
  which issue or which field changed. Recording those details for every verb is
  tracked in #746.
- **Field**: one of `title` or `body`. These two names are part of the backend
  contract, so a backend translates them to its own flag names if they differ.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: An agent can change an issue's title or body with one
  `wfctl issue edit` command, with no call to the tracker's own client.
- **SC-002**: Every successful edit leaves exactly one recorded write per field
  changed, and a failed write leaves none.
- **SC-003**: In each of the seven cases in User Stories 1 and 2, the output says
  correctly which fields changed.
- **SC-004**: A real body edit on a GitHub issue changes the body and is
  recorded as `issue-edit`.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, with new tests for the single-field, two-field,
  partial-failure, no-field, no-id, and unsupported-backend cases, and for
  the tracker config check accepting `edit` and refusing an unknown placeholder
  on it.
- `uv run ruff check wfctl/ tests/` and `uv run mypy`.
- `uv run wfctl install-skills --tracker github`, then `uv run wfctl
  tracker-check`, confirming `edit` is in the verb list.
- One real `wfctl issue edit` against a GitHub issue, changing its body with
  text containing several lines, backticks, and quotes. Then confirm the body
  in the tracker and the `issue-edit` entry in the session's log.
- `uv run wfctl doctor` and a release note at `changes/445.addition.md`.

## Assumptions

- Pre-specify design context loaded from `design.md` in this spec folder.
- Nothing depends on a title and body changing together, so two separate
  writes are acceptable. wfctl doesn't roll back the title when the body fails.
- A tracker with differently named flags, such as Jira's `--summary`, can ship
  a short script that translates `title` and `body`.
- `edit` for changes (PRs) is out of scope. The `changes` section has no write
  verbs yet, and that work is tracked in #126.
- `label` stays its own verb. Verb naming rules are tracked in #402.
