# Feature Specification: Strip allow-notify

**Feature Branch**: `384-strip-allow-notify`
**Created**: 2026-09-15
**Status**: Draft
**Input**: Issue #384, "Remove --allow-notify: the outward-action grant adds a stop nobody asked for", and the approved design in `design.md`.

## Clarifications

### Session 2026-09-15

- Q: How does a skill know it is running unattended, so it attempts the action instead of asking? → A: It doesn't detect anything. It asks as written, and a run where nobody answers attempts the action. `auto_approve` is not read for this.
- Q: When `report-action` runs, what does it say about holds? → A: It names the hold it lifted, if there was one, and otherwise says only that the action was recorded. It never refuses.
- Q: Does `report-block` keep all of `blocked`'s current behaviour apart from `--clear`? → A: Yes. `--reason` is required, the held step is inferred at call time, and with no spec dir it records the block and holds nothing.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A person says "file it" and the issue gets filed (Priority: P1)

A maintainer is working with an agent in an attended session. The agent
suggests opening an issue, and the maintainer agrees. Today wfctl refuses
unless someone ran `wfctl start --allow-notify` earlier or labelled the issue
`authority:notify`. The maintainer has already said yes, and there is nothing
more they can do from the conversation to get it filed. After this change,
wfctl just runs the command. The only thing that can still stop it is the
agent host's own permission check, and the person who is present can answer
that one.

**Why this priority**: This is the failure that prompted the issue. It happened
on #371, and again while filing #384 itself.

**Independent Test**: On a branch where no grant was ever made, run
`wfctl issue create`, `comment` and `label` against a stubbed tracker. Each one
reaches the tracker and exits with the tracker's own result.

**Acceptance Scenarios**:

1. **Given** a feature branch with no grant and no label, **When** the agent
   runs `wfctl issue create --title … --body …`, **Then** wfctl calls the
   tracker and does not print a refusal.
2. **Given** the same branch, **When** `wfctl issue comment` or
   `wfctl issue label` runs, **Then** each reaches the tracker the same way.
3. **Given** the trunk branch, **When** any of those verbs runs, **Then** it
   also reaches the tracker, because being on trunk no longer blocks tracker
   writes.

---

### User Story 2 - A restarted session can see what the last run did and what it was stopped from doing (Priority: P1)

An unattended run pushes a branch, then tries to close an issue, and the host
refuses the close. The context fills up and the session restarts. The next
session reads the summary and `wfctl status`. It should see that the push
happened and that the close is still waiting, and the pipeline step should stay
unfinished until the close happens.

**Why this priority**: Recording is the part of the old design worth keeping.
Since #371, it is the only trace of these actions that survives a restart.

**Independent Test**: Run `wfctl report-action push`, then
`wfctl report-block issue-close --reason "host refused"`. `status` shows the
current step held for `issue-close`, and the restart hook's summary lists the
push.

**Acceptance Scenarios**:

1. **Given** a session with no grant, **When** the agent runs
   `wfctl report-action push`, **Then** the push is recorded, and no refusal
   is printed.
2. **Given** a session, **When** the agent runs
   `wfctl report-block issue-close --reason "…"`, **Then** `status` shows the
   current step as held, naming `issue-close` and the reason.
3. **Given** that hold, **When** `wfctl issue close` later succeeds, **Then**
   the hold is lifted without anyone typing anything else.
4. **Given** a hold on an action that no wfctl verb performs (for example
   `push`), **When** the agent or a person runs `wfctl report-action push`,
   **Then** the hold is lifted.
5. **Given** an automatic restart after either verb ran, **When** the summary
   is written, **Then** it includes the recorded action.

---

### User Story 3 - The status output stops talking about a permission that no longer exists (Priority: P2)

A person reads `wfctl status`, or a skill reads `wfctl status --json`. Today
both show "will not notify anyone — nobody has allowed it for this work", a
fourth fact called "outward actions authorized", and the `notify` and
`notify_source` keys. After this change none of that appears. The line saying
merge, force-push, close and delete stay with the human is still there. The
line about the agent host's permission rules is reworded so it no longer
suggests wfctl has rules of its own.

**Why this priority**: Leaving these in place would describe a gate that is no
longer there. It isn't P1, because the behaviour in Stories 1 and 2 can be
tested without it.

**Independent Test**: Run `wfctl status` and `wfctl status --json` on a fresh
branch and compare the output with the acceptance scenarios below.

**Acceptance Scenarios**:

1. **Given** any branch, **When** `wfctl status` runs, **Then** it prints no
   notify line and no "outward actions authorized" fact.
2. **Given** any branch, **When** `wfctl status --json` runs, **Then** the
   payload has no `notify` or `notify_source` key, and `facts` has three
   entries.
3. **Given** any branch, **When** `wfctl status` runs, **Then** the
   irreversible-actions line is still printed.
4. **Given** any branch, **When** `wfctl status` runs, **Then** the host
   permission line does not suggest wfctl keeps permission rules too.

---

### User Story 4 - Skills and docs describe how things work now (Priority: P2)

An agent following `end-session`, `speckit-delivery-plan`, `speckit.analyze`,
`speckit.decompose` or `speckit.implement` never reads the grant, never
records a decline, and never calls a removed verb. In an attended session it
still asks before commenting, labelling, creating, closing or pushing. In an
unattended run it tries the action. If the host refuses, it runs
`wfctl report-block`. A person reading `README.md`, `docs/reference.md` or
`AGENTS.md` finds the two reporting verbs and no mention of a grant.

**Why this priority**: If a skill still calls `wfctl notify` or reads `notify`,
it fails or gives up on the action. That brings back the stop the code change
removed.

**Independent Test**: Run `uv run wfctl install-skills --agent claude`. Then
search the installed tree, `README.md`, `docs/` and `AGENTS.md` for the removed
names, and read each changed skill as it was installed.

**Acceptance Scenarios**:

1. **Given** the installed skills, **When** they are searched for
   `wfctl notify`, `wfctl blocked`, `--allow-notify`, `notify_source` or
   `authority:notify`, **Then** nothing is found.
2. **Given** `end-session` in an unattended run, **When** it reaches the
   tracker step, **Then** it tries the action and, if the host refuses, files
   `report-block` under the `issue-<verb>` name.
3. **Given** `speckit-delivery-plan` in an unattended run, **When** it reaches
   issue creation, **Then** it tries `wfctl issue create` instead of stopping
   with placeholder keys because nobody granted permission.
4. **Given** the Safety section of `AGENTS.md`, **When** it is read, **Then**
   it no longer says `comment`, `create` and `label` refuse by default.

---

### Edge Cases

- **An event log written before this change** contains a `blocked` event
  followed by a `block-cleared` event for the same action. The hold stays
  lifted, even though nothing writes `block-cleared` anymore.
- **An old log records a bare `create`** from an earlier `wfctl issue create`.
  Nothing treats it as a hold or as lifting one. `wfctl log` shows it
  unchanged.
- **A skill installed from an older wheel** calls `wfctl notify` or
  `wfctl blocked`. The command fails with "No such command" and has no other
  effect. `doctor` reports the installed skills as stale at the next
  `/start-session`.
- **A leftover local grant file** (written by an old `--allow-notify`) sits in
  the state dir. Nothing reads it, and its presence changes nothing.
- **Someone passes `--allow-notify` or `--deny-notify` to `wfctl start`** out
  of habit. It fails with the CLI's usual "no such option" error.
- **A hold's action name is misspelled** when the agent files it by hand
  (`report-block issue-crate`). The hold can't be lifted by a successful
  `issue create`. `status` shows the misspelled name, and
  `report-action issue-crate` lifts it.
- **The tracker verbs `start` and `stop`** (board moves run from worktree
  hooks) succeed. They record nothing.
- **`wfctl issue close` succeeds** with no hold standing. It is recorded as
  `issue-close`, and the restart summary lists it.

## Requirements _(mandatory)_

### Functional Requirements

**The gate is removed**

- **FR-001**: `wfctl issue comment`, `create` and `label` MUST NOT refuse for
  lack of permission, on any branch, trunk included.
- **FR-002**: `wfctl start` MUST NOT accept `--allow-notify` or
  `--deny-notify`, and MUST NOT read issue labels or contact the tracker to
  decide whether actions are allowed.
- **FR-003**: No wfctl command may read the `authority:notify` label, a local
  grant file, or a recorded grant in order to decide what it does.
- **FR-004**: The `wfctl notify` command (including `--declined`) and the
  `wfctl blocked` command (including `--clear`) MUST be removed, with no
  aliases.
- **FR-005**: Code that only the grant used MUST be deleted. That includes the
  trunk check for the grant (`_paths.on_trunk`) and the label read for the
  grant (`_tracker.read_issue_labels`). The tracker's `labels` verb MUST stay
  in the tracker contract.

**Recording stays**

- **FR-006**: `wfctl report-action <action>` MUST record that the run took
  `<action>`, storing it under the existing `notify-action` event name. When a
  standing hold on `<action>` is lifted by this, it MUST say which one.
  Otherwise it says only that the action was recorded. It MUST NOT refuse
  because no hold matches, since a push with nothing held is the normal case.
- **FR-007**: `wfctl report-block <action> --reason "<text>"` MUST record that
  the host refused `<action>`, under the existing `blocked` event name. The
  current pipeline step MUST then show as held. It keeps every behaviour
  `wfctl blocked` has today apart from `--clear`. `--reason` is required. The
  held step is inferred when the command runs, never supplied by the caller.
  If the pipeline is complete, the last step is held. With no spec dir, the
  block is recorded and no step is held.
- **FR-008**: For each action, the most recent of these events decides whether
  a hold stands: `notify-action`, `blocked`, or an old `block-cleared`. A later
  `notify-action` lifts the hold, and so does a `block-cleared` that is already
  in a log.
- **FR-009**: When `wfctl issue` runs a write verb successfully, it MUST record
  it as `issue-<verb>` for `comment`, `create`, `label` and `close`. It MUST NOT
  record `start` or `stop`.
- **FR-010**: The restart hook's summary MUST keep including recorded
  `notify-action` events and MUST stop looking for `notify-declined`.

**Status output**

- **FR-011**: The `wfctl status` payload MUST NOT include `notify` or
  `notify_source`. `facts` MUST have three entries, without "outward actions
  authorized". Every view of the payload changes together.
- **FR-012**: `wfctl status` MUST stop printing the notify line, and MUST keep
  printing the irreversible-actions line.
- **FR-013**: The host-permission line in `wfctl status` MUST be reworded so
  it no longer implies wfctl has permission rules. The exact wording is left to
  the plan.

**Skills and docs**

- **FR-014**: `end-session`, `speckit-delivery-plan`, `speckit.analyze`,
  `speckit.decompose`, `speckit.implement` and the `end-session` command
  wrapper MUST stop reading `notify` or `notify_source` and stop calling the
  removed verbs, including in their `allowed-tools` lines. They MUST use
  `report-action` and `report-block` with `issue-<verb>` names.
- **FR-015**: These skills MUST still ask before taking an outward action,
  exactly as they do now. No mode is detected. When nobody answers, the run
  MUST try the action, and MUST run `report-block` if the host refuses it.
  Neither `auto_approve` nor any other setting may be read to decide this.
- **FR-016**: `scaffold-tracker` MUST stop describing the `labels` verb as
  deciding whether a run may notify.
- **FR-017**: `README.md`, `docs/reference.md` and the Safety section of
  `AGENTS.md` MUST describe the two reporting verbs and MUST NOT mention a
  grant. `AGENTS.md` MUST still say that `close` is the human's to run.

**Records**

- **FR-018**: Architecture records that point to the grant MUST be checked.
  Each one either gets a log line pointing to
  `wfctl-records-outward-actions-and-never-gates-them`, or is left alone if it
  is only history. The records are
  `the-agent-reports-the-block-wfctl-never-saw`,
  `readiness-is-not-a-step-state`,
  `wfctl-classes-the-action-not-the-command`,
  `the-repo-names-the-fields-a-change-must-carry`,
  `design/299-facts-render-as-a-block` and
  `design/200-session-id-rides-on-the-start-event`. No record may be marked
  `accepted` by the agent.

## Key Entities

- **Recorded action**: a line in the branch's event log saying an action was
  taken. It holds the action name and a timestamp. Written by `report-action`,
  and by `wfctl issue` after a successful write.
- **Block**: a line in the event log saying the host refused an action. It
  holds the action name and a reason, and it holds the current step until a
  later recorded action with the same name appears.
- **Action name**: free text. Tracker writes use `issue-<verb>`. Anything else
  (today, only `push`) is named by whoever reports it.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: On a branch where nobody granted anything, all three tracker
  write verbs reach the tracker on the first try. Zero refusals come from
  wfctl.
- **SC-002**: A hold filed under `issue-create` or `issue-close` is lifted by
  the next successful matching `wfctl issue` call. Nothing else needs to be
  typed.
- **SC-003**: Searching `wfctl/`, `README.md`, `docs/` and `AGENTS.md` for
  `allow.notify|notify_source|outward actions authorized|authority:notify|wfctl notify|wfctl blocked`
  finds matches only in superseded records and history log lines.
- **SC-004**: `wfctl start` makes zero tracker calls.
- **SC-005**: The status payload has three facts, and neither `notify` key.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/` and
  `uv run mypy wfctl/` all pass.
- `uv run wfctl doctor` exits 0 after `uv run wfctl install-skills --agent claude`.
  Then read each changed skill as installed.
- Tests that checked the refusal (`test_notify_{dispatch,flag,declined,grant,status}.py`,
  and the grant parts of `test_tracker.py` and `test_four_facts.py`) are
  deleted rather than flipped. The behaviour they checked no longer exists.
- New tests cover:
  - `report-action` and `report-block` recording and holding
  - a successful `wfctl issue create` and `close` lifting a matching hold
  - `start` and `stop` recording nothing
  - an old `blocked` → `block-cleared` pair still reading as lifted
  - `wfctl --help` listing neither removed command
  - the status payload shape
- Run the SC-003 search.
- Manual check, with the maintainer's OK first because it writes to the
  tracker: `uv run wfctl issue label <n> --action add --label <x>` on a
  throwaway issue, with no grant. The host decides, and wfctl stays quiet.

## Assumptions

- Pre-specify design context loaded from `specs/384-strip-allow-notify/design.md`.
- The host's permission layer is gate enough, as it was before #280.
- A repo refreshes its installed skills (through `/start-session`) before an
  old skill calls a removed verb. If it doesn't, that call fails loudly and
  does no harm.
- No log in use holds a block that only a bare action name like `create` would
  lift. Every block filed so far used the `issue-…` names from skill text.
- `speckit.implement.md` also calls `wfctl blocked`. It wasn't in the issue's
  blast radius or the design's list, and it is in scope here.
