# Feature Specification: Auto-approve has its own command

**Feature Branch**: `407-auto-approve-mid-session`  
**Created**: 2026-11-19  
**Status**: Draft  
**Input**: User description: "Let a person, or the agent at their request, turn auto-approve on or off at any point in a session, and let a scripted run start in the mode when its worktree is created." Loaded from `design.md`.

## Clarifications

### Session 2026-11-19

- Q: Who sees the reminder that `.workmux.yaml` has no grant line? → A: Only
  someone who runs `wfctl auto-approve` with no argument, as an `ℹ` note under
  the mode. `wfctl doctor` doesn't report it, since the line is opt-in and a
  repository that never uses auto-approve shouldn't be warned on every run.
  Basis: the user chose this over the options offered.

## User Scenarios & Testing _(mandatory)_

Auto-approve is a per-feature mode. When it's on, the agent answers each design
gate into its record instead of stopping to ask, and the user approves at the
PR. Previously, `wfctl start --auto-approve` was the only way to turn it on, and
`/start-session` can't pass that flag. In the #799 unattended run, the agent ran
`wfctl start --auto-approve` a second time to get the grant, and `start` then
printed "Already initialized", which reads like a failure.

### User Story 1 - Turn the mode on or off mid-session (Priority: P1)

The user is partway through a feature and says "run the rest of this
unattended". The agent runs `wfctl auto-approve on`, and wfctl confirms the mode
is on with no "Already initialized" line. Later the user says "stop, I want to
review the plan", and the agent runs `wfctl auto-approve off`.

**Why this priority**: This is the gap #407 reports. Without it, a grant made
during a session happens outside the workflow.

**Independent Test**: In a worktree with an open issue and a session started,
run `wfctl auto-approve on`, then check that `wfctl status --json` reports
`auto_approve: true`. Run `wfctl auto-approve off` and check that it reports
`false`.

**Acceptance Scenarios**:

1. **Given** a session that holds the branch and an open issue, **When** the
   agent runs `wfctl auto-approve on`, **Then** the mode is on, a `mode` event
   naming this session is appended, and the output prints the auto-approve
   notice and no "Already initialized" line.
2. **Given** the mode is on, **When** anyone runs `wfctl auto-approve off`,
   **Then** the mode is off and a `mode` event is appended.
3. **Given** the mode is already on, **When** the agent runs `wfctl
   auto-approve on` again, **Then** the command succeeds and prints the mode
   again, and no `mode` event is appended.
4. **Given** another session holds the branch, **When** this session runs
   `wfctl auto-approve on`, **Then** the command is refused, the mode doesn't
   change, and the refusal points at `/start-session`.
5. **Given** the branch's issue is closed, or the branch names no issue,
   **When** the agent runs `wfctl auto-approve on`, **Then** the command is
   refused with the same message and fix line that `wfctl start` prints.
6. **Given** the caller has no session identity, **When** it runs `wfctl
   auto-approve on`, **Then** the grant is allowed, as other commands behave
   without an identity.

---

### User Story 2 - See who turned the mode on (Priority: P1)

The user opens a PR from an unattended run and wants to know how the mode got
turned on. They run `wfctl auto-approve` with no argument, and it prints the
mode and when and from which session it was granted:

```
auto-approve on — design gates answered into the record, review stops run through, approval moves to the PR
  turned on 2026-11-19 14:02 UTC by this session
```

**Why this priority**: The agent can grant the mode, and wfctl can't tell a
grant someone asked for from one nobody did. The session on the grant is what
lets the user check.

**Independent Test**: Grant the mode from one session, then run `wfctl
auto-approve` from that session and from a second one, and compare the two
outputs.

**Acceptance Scenarios**:

1. **Given** this session granted the mode, **When** it runs `wfctl
   auto-approve`, **Then** the output says "by this session".
2. **Given** another session granted the mode, **When** this session runs
   `wfctl auto-approve`, **Then** the output says "by another session".
3. **Given** the last grant was written before this change, or by a caller with
   no identity, **When** anyone runs `wfctl auto-approve`, **Then** the output
   says "by an unknown session".
4. **Given** the review cap turned the mode off, **When** anyone runs `wfctl
   auto-approve`, **Then** the output says the mode is off and prints the
   revocation reason.
5. **Given** the mode was never granted, **When** anyone runs `wfctl
   auto-approve`, **Then** the output says the mode is off and that no grant is
   on record.
6. **Given** any grant, **When** the output names the session, **Then** it
   never prints the session's ID.

---

### User Story 3 - Start a scripted run in the mode (Priority: P2)

The user wants a run to go unattended from the start. They create the worktree
with `WFCTL_AUTO_APPROVE=1 workmux add 812-foo`, and the worktree comes up with
the mode on. Creating a worktree without the variable leaves it attended.

**Why this priority**: It serves scripted runs. A person can still turn the mode
on mid-session with User Story 1, so this is a convenience, not the gap.

**Independent Test**: Create a worktree with the variable set to `1` and check
that `wfctl status --json` reports `auto_approve: true`. Create another with the
variable unset and check that it reports `false`.

**Acceptance Scenarios**:

1. **Given** `WFCTL_AUTO_APPROVE=1` on `workmux add` for an open issue, **When**
   the worktree is created, **Then** the mode is on.
2. **Given** `WFCTL_AUTO_APPROVE` is unset, `0`, `true`, or any value other than
   exactly `1`, **When** the worktree is created, **Then** the mode stays off.
3. **Given** `WFCTL_AUTO_APPROVE=1` and a closed issue, **When** the worktree is
   created, **Then** the grant is refused, the worktree still comes up, and the
   mode stays off.
4. **Given** the review cap turned the mode off and `WFCTL_AUTO_APPROVE=1` is
   still set in the shell, **When** the pane restarts and runs `wfctl start`,
   **Then** the mode stays off.

---

### User Story 4 - Find out an existing repo is missing the grant line (Priority: P3)

A repository seeded `.workmux.yaml` before this change, so its `post_create` has
no grant line. The user runs `wfctl auto-approve` to check the mode and sees a
note under it that prints the line to add:

```
auto-approve off — no grant on record
  ℹ .workmux.yaml has no auto-approve line, so `WFCTL_AUTO_APPROVE=1 workmux add` won't start a worktree unattended.
    Add this entry to post_create:
      - cd "$WM_WORKTREE_PATH" && [ "$WFCTL_AUTO_APPROVE" = 1 ] && wfctl auto-approve on || true
```

`wfctl doctor` says nothing about the line.

**Why this priority**: `install-config` writes the seed once and never updates
it, and running it with `--force` replaces the repository's edits. Without the
note, an existing repository never finds out the line exists. The line is
opt-in, so the note goes where someone interested in the mode looks, and a
repository that never uses auto-approve never sees it.

**Independent Test**: Run `wfctl auto-approve` in a repository whose
`.workmux.yaml` lacks the line, then add the line and run it again.

**Acceptance Scenarios**:

1. **Given** `post_create` has no live grant line, **When** the user runs `wfctl
   auto-approve` with no argument, **Then** it prints the `ℹ` note with the line
   to add, and its exit code is unchanged.
2. **Given** the grant line is present but commented out, **When** the user runs
   `wfctl auto-approve`, **Then** it prints the note.
3. **Given** the grant line appears elsewhere in the file but not under
   `post_create`, **When** the user runs `wfctl auto-approve`, **Then** it prints
   the note.
4. **Given** the repository has no `.workmux.yaml`, **When** the user runs
   `wfctl auto-approve`, **Then** it prints no note.
5. **Given** any repository, **When** the user runs `wfctl doctor`, **Then** it
   prints nothing about the grant line.
6. **Given** `wfctl auto-approve on` or `off`, **When** either runs, **Then** it
   prints no note.

---

### User Story 5 - The agent's skills name the new command (Priority: P3)

An agent reading `using-wfctl` or `plan-walkthrough` learns to turn the mode on
with `wfctl auto-approve on` and off with `wfctl auto-approve off`. `using-wfctl`
also explains that `install-config` writes a file once and never updates it, so
a template change doesn't reach a repository already seeded, and that `--force`
replaces the repository's edits.

**Why this priority**: The command works without it, but an agent following the
old skill text would keep running `wfctl start --auto-approve`.

**Independent Test**: After `uv run wfctl install-skills`, search the installed
skills for `start --auto-approve` and for the `install-config` explanation.

**Acceptance Scenarios**:

1. **Given** the installed skills, **When** an agent reads how to set the mode,
   **Then** it finds `wfctl auto-approve on` and no instruction to run `wfctl
   start --auto-approve`.
2. **Given** `plan-walkthrough` refuses to run while the mode is on, **When** it
   prints its refusal, **Then** the refusal names `wfctl auto-approve off`.
3. **Given** `using-wfctl`, **When** an agent reads about `install-config`,
   **Then** it learns that the command writes once, never updates, and that
   `--force` replaces the repository's edits.

---

### Edge Cases

- The state dir can't be written. `wfctl auto-approve on` or `off` prints the
  error and exits 1. wfctl appends the event before it writes the mode file,
  so a failed append leaves the mode as it was. If the event lands and the
  file write fails, the mode keeps its old value, and the next `on` or `off`
  repairs it. Until then, the bare command says "turned off outside wfctl"
  after a failed `on`, and "no grant on record" after a failed `off`.
- The event log has a grant with no `session` field. It reads as "an unknown
  session".
- `wfctl start --auto-approve` runs on a session already started. The grant is
  still made, as it is today, and the takeover rules of `start` still apply.
- A hand-written mode file leaves no `mode` event. `wfctl auto-approve` reports
  the mode and says no grant is on record, even when an older grant or a
  revocation is in the event log. A later `wfctl auto-approve on` writes the
  grant, and the review cap counts from it.
- This conversation ran `wfctl end` and then runs `wfctl auto-approve on`. The
  command is refused with the same message as for another session, since no
  session is open for this conversation, and `/start-session` reopens one.
- `post_create`'s grant runs before any session exists. The grant is allowed,
  since no other session holds the branch. The hook inherits the environment
  of whoever ran `workmux add`. If an agent ran it, the grant carries that
  agent's session, and the new worktree's session reads it as "another
  session", which is true. If a person ran it from a plain shell, the grant
  reads as "an unknown session". The hook line doesn't clear the identity
  variables, since that would name an agent's variable in committed config
  (`no-hardcoded-agent`).

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: wfctl MUST provide `wfctl auto-approve on`, which turns the mode on
  for the current branch's feature and appends a `mode` event. If the mode is
  already on because of an earlier grant, it MUST write nothing, so a repeated
  `on` doesn't restart the review count. If the mode file reads on with no
  grant on record, `on` MUST write the grant, so the review cap has a starting
  point.
- **FR-002**: wfctl MUST provide `wfctl auto-approve off`, which turns the mode
  off and appends a `mode` event. It MUST never be refused for which session
  holds the branch or for the issue's state.
- **FR-003**: `wfctl auto-approve` with no argument MUST print the mode and,
  when a grant is on record, its time in UTC and whether it came from this
  session, another session, or an unknown session. It MUST never print a session
  ID.
- **FR-004**: `wfctl auto-approve on` MUST be refused, leaving the mode
  unchanged, when another session holds the branch, or when this conversation
  ended its own session with `wfctl end`. The refusal MUST be true in both
  cases and MUST name `/start-session`.
- **FR-005**: `wfctl auto-approve on` MUST be refused, leaving the mode
  unchanged, whenever `wfctl start` would refuse a session on the branch. The
  refusal MUST be the message and fix line `start` prints.
- **FR-006**: `wfctl auto-approve on` MUST be allowed when the caller presents no
  session identity.
- **FR-007**: Every `mode` event a grant writes MUST carry the granting session's
  identity when the caller has one. A grant event without it MUST read as from
  an unknown session.
- **FR-008**: `wfctl start --auto-approve` and `--no-auto-approve` MUST keep
  working and MUST write the same mode file and `mode` event as `wfctl
  auto-approve on` and `off`, including the session field. `start` MUST NOT
  refuse its grant because another session holds the branch, since `start`
  takes the branch over.
- **FR-009**: wfctl commands MUST NOT read `WFCTL_AUTO_APPROVE`. Only the grant
  line in `.workmux.yaml` reads it.
- **FR-010**: The `.workmux.yaml` wfctl ships and this repository's own
  `.workmux.yaml` MUST each have a `post_create` entry that runs `wfctl
  auto-approve on` only when `WFCTL_AUTO_APPROVE` is exactly `1`, and that
  never fails the worktree's creation.
- **FR-011**: `wfctl auto-approve` with no argument MUST print an `ℹ` note that
  names the line to add when `.workmux.yaml` exists and its `post_create` has no
  live `auto-approve on` entry. The note MUST NOT change the exit code, and
  `wfctl doctor` MUST NOT report the missing line.
- **FR-012**: The `using-wfctl` and `plan-walkthrough` skills MUST name `wfctl
  auto-approve on` and `off` as the way to set the mode, and `plan-walkthrough`'s
  refusal MUST name `wfctl auto-approve off`. `using-wfctl` MUST tell the agent
  to run `wfctl auto-approve on` only when a person asked for an unattended run,
  and never on its own judgment.
- **FR-013**: `using-wfctl` MUST explain that `install-config` writes a file once
  and never updates it, and that `--force` replaces the repository's edits.
- **FR-014**: The review cap's revocation MUST keep working as before. Only a
  new grant from either command resets the review count.
- **FR-015**: `install-skills --agent claude` MUST add `Bash(wfctl auto-approve
  on:*)` and `Bash(uv run wfctl auto-approve on:*)` to `permissions.ask` in
  `.claude/settings.json`, so Claude Code asks the person before the agent
  turns the mode on. Uninstall and `doctor` MUST treat these rules the same way
  they treat wfctl's managed deny rule.

## Key Entities _(include if feature involves data)_

- **Mode file**: The stored value of the mode for one feature, in the branch's
  state dir. It holds whether the mode is on and, after a revocation, the
  reason.
- **`mode` event**: A line in the branch's event log, written on every grant or
  revocation. It gains a `session` field holding the granting session's
  identity.
- **Grant line**: The `post_create` entry in `.workmux.yaml` that runs `wfctl
  auto-approve on` when `WFCTL_AUTO_APPROVE` is exactly `1`.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: An agent turns the mode on mid-session with one command, and the
  output contains no "Already initialized" line.
- **SC-002**: Each of the five "Must keep catching" cases in the
  `approval-mode-is-stored-intent` threat model leaves the mode off, and each of
  the six "Must let through" cases succeeds.
- **SC-003**: `wfctl auto-approve` names the granting session's relation for
  100% of grants written after this change, and says "an unknown session" for
  grants written before it.
- **SC-004**: A repository seeded before this change sees the grant-line note
  the first time anyone runs `wfctl auto-approve` there, and a repository that
  never runs it sees no output about the line.
- **SC-005**: No installed skill tells the agent to run `wfctl start
  --auto-approve` to set the mode.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`.
- Unit tests for each acceptance scenario in User Stories 1, 2, and 4, including
  the refusal cases and the grant event's `session` field.
- Tests that `start` never reads `WFCTL_AUTO_APPROVE`, and that a pane restart
  with the variable set leaves a revoked mode off.
- A test that runs the shipped `post_create` grant line in a shell with the
  variable unset, `0`, `true`, and `1`, and checks that only `1` grants the
  mode.
- `uv run wfctl install-skills`, then read the installed `using-wfctl` and
  `plan-walkthrough` to check the new text.
- One manual run of `WFCTL_AUTO_APPROVE=1 workmux add` on a throwaway issue,
  checking that the worktree comes up with the mode on.
- `uv run wfctl auto-approve` in this repository after its `.workmux.yaml` gains
  the line, checking that no note prints.
- One manual check that Claude Code prompts the user. After `uv run wfctl
  install-skills --agent claude`, the agent runs `wfctl auto-approve on` and
  `uv run wfctl auto-approve on` in the default permission mode and in auto
  mode, and each of the four runs is recorded as prompting or not.

## Assumptions

- Pre-specify design context loaded from `design.md` in the feature's spec
  folder.
- The issue's proposal, giving `start`'s option an `envvar`, is rejected. A pane
  restart would re-grant after the review cap revoked, a `0` in a profile would
  turn off a mid-session grant, and it can't reach a running session. The full
  argument is in `docs/architecture/approval-mode-is-stored-intent.md`.
- workmux hooks inherit the environment of the shell that runs `workmux add`.
  The shipped hook already relies on this for `WFCTL_AGENT`.
- Reporting the mode in `/start-session`'s report is out of scope. The issue
  lists it as wanting its own issue.
