# Feature Specification: Install asks before changing a settings file

**Feature Branch**: `859-ask-rule-literal-star`
**Created**: 2026-11-23
**Status**: Draft
**Input**: User description: "Write spec.md from the branch's design.md (#859: install asks before changing an existing settings file). Records: settings-edit-asks-first (accepted), design/settings-changes-ask-once (proposed)."

## Clarifications

### Session 2026-11-23

- No critical ambiguities detected.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Approve settings changes at a terminal (Priority: P1)

The user runs `wfctl install-skills` in their own terminal after upgrading
wfctl. The project's settings file already exists, and the new wfctl ships a
hook and a rule it doesn't have yet, and has retired an old rule. Install lists
the three changes, each with one line saying what it's for, and asks once. The
user says yes, and the file is saved once with all three changes. If the user
says no, the file is left exactly as it was.

**Why this priority**: This is the only way a settings change reaches an
existing file once the change ships, so without it no upgrade can update a
hook or a rule.

**Independent Test**: In a project whose settings file is missing one shipped
rule, run install at a terminal and answer yes, then repeat with no. The yes
run adds the rule in one save, and the no run leaves the file byte-identical.

**Acceptance Scenarios**:

1. **Given** an existing settings file that needs two or more changes, **When**
   the user runs install at a terminal, **Then** install lists every change for
   that file and asks one question for it.
2. **Given** the list, **When** the user reads it, **Then** each added or
   updated entry carries the line `wfctl doctor` prints for it, and each removed
   entry says wfctl no longer ships it.
3. **Given** the user answers yes, **Then** the file is saved once, with every
   listed change.
4. **Given** the user answers no, **Then** the file is byte-identical to before
   the run, and install names the command to run later.
5. **Given** both `.claude/settings.json` and `.bob/settings.json` need changes,
   **When** install runs, **Then** it asks once for each file.

---

### User Story 2 - An unattended install leaves the file alone (Priority: P1)

The agent runs install, or the worktree creation hook does, or
`/start-session` runs its repair with `--yes`. Nobody is at a terminal. Install
still copies the skills, but it doesn't change an existing settings file. It
prints how many changes it skipped and the command for the user to run in
their own terminal.

**Why this priority**: These runs are most installs, and they're the ones that
changed the user's file with nobody watching. This is the security control the
accepted record asks for.

**Independent Test**: Run each "Must keep catching" command from
`settings-edit-asks-first.md` against an existing settings file that needs a
change, and check the file is byte-identical afterwards.

**Acceptance Scenarios**:

1. **Given** an existing settings file that needs a change, **When** install
   runs with no terminal, with or without `--yes`, `--prune`, or `--force`,
   **Then** the file is byte-identical after the run.
2. **Given** the same run, **Then** install prints one warning naming the file,
   the number of skipped changes, and the install command to run in a terminal.
3. **Given** the same run, **Then** every skill, template, and script is still
   copied, and install exits 0.
4. **Given** a removal of a rule wfctl no longer ships, **When** install runs
   with no terminal, **Then** the rule stays in the file.

---

### User Story 3 - A new worktree still gets its settings file (Priority: P1)

The user creates a worktree. `.claude/` is gitignored, so the worktree has no
settings file. The creation hook runs install, which creates the file with the
worktree guard's hook and the ask rules, without asking.

**Why this priority**: If install asked here, nobody would answer, and the new
worktree would come up without the guard or the ask rules, which are
protections in their own right.

**Independent Test**: Run install with no terminal in a directory with no
settings file, and check the file is created with every shipped hook and rule.

**Acceptance Scenarios**:

1. **Given** no settings file, **When** install runs with no terminal, **Then**
   it creates the file with every shipped hook and rule and asks nothing.
2. **Given** an install that changes no settings file, **When** it runs with
   `--yes` and no terminal, **Then** it copies the skills and prints no settings
   warning.

---

### User Story 4 - Doctor reminds the user of pending changes (Priority: P2)

After an unattended install skipped a settings change, the user runs `wfctl
doctor`, or `/start-session` does. Doctor lists each pending change with a
warning and the install command for the user's terminal. It doesn't fail the
run.

**Why this priority**: Without the reminder, a skipped change waits forever.
It's P2 because the file is still safe without it.

**Independent Test**: Skip a change with an unattended install, run doctor,
and check it warns about the change, prints the command, and exits 0 when
nothing else is wrong.

**Acceptance Scenarios**:

1. **Given** a shipped hook missing from or out of date in a settings file
   wfctl manages, **When** doctor runs, **Then** it warns and names the install
   command, and that finding alone doesn't make it exit 1.
2. **Given** a shipped rule that isn't in the file, whether it was removed or
   never added, **When** doctor runs, **Then** it warns with the rule's cost
   line and the install command.
3. **Given** a retired rule still in the file, **When** doctor runs, **Then** it
   warns and names the install command, and that finding alone doesn't make it
   exit 1.
4. **Given** nothing pending, **Then** doctor prints no settings line.

### Edge Cases

- The settings file can't be parsed. Install reports it once for that file,
  changes nothing in it, and keeps the manifest's receipts for it.
- Saving the file fails, for example because it's read-only. Install reports
  it, the file keeps its old content, and the receipts stay as they were.
- The user answers yes, and only some of the changes are for entries the user
  wrote themselves. Install changes only wfctl's own entries, as today.
- The settings file is a symlink. Install handles it as each pass does today:
  the hooks and ask rules passes save through the link, and the retire and Bob
  Shell passes leave a linked file alone.
- The user declines, and a later install runs at a terminal. Install lists the
  same changes again.
- The file exists and is empty. Install treats it as an existing file and asks.
- `uninstall-skills` removes wfctl's entries without asking, as today.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Install MUST NOT change an existing `.claude/settings.json` or
  `.bob/settings.json` unless the user answers yes at a terminal during that
  run.
- **FR-002**: Install MUST treat a run as having a terminal only when standard
  input is a terminal. `--yes` MUST NOT count as a yes to the settings
  question.
- **FR-003**: Install MUST ask at most once per settings file per run, and MUST
  save each file at most once per run.
- **FR-004**: The question MUST list every change for that file: each hook or
  rule added or updated, with its existing cost line, and each rule or tool
  approval removed, saying wfctl no longer ships it.
- **FR-005**: The question MUST default to no.
- **FR-006**: If the file doesn't exist, install MUST create it with every
  shipped entry without asking.
- **FR-007**: If the change isn't saved, install MUST leave the file
  byte-identical and keep the manifest's prior receipts for that file.
- **FR-008**: If the change isn't saved, install MUST print one warning per
  file with the number of skipped changes and the install command to run in a
  terminal, and MUST exit 0 if nothing else failed.
- **FR-009**: Install MUST still copy skills, templates, and scripts when it
  skips a settings change.
- **FR-010**: Doctor MUST report each pending settings change as a warning with
  the install command, including a shipped rule that was never added.
- **FR-011**: A pending settings change MUST NOT by itself make doctor exit 1.
  This includes the missing or stale managed hook and the retired rule
  findings, which exit 1 today.
- **FR-012**: `uninstall-skills` MUST keep removing wfctl's own entries without
  asking.
- **FR-013**: Every hook and rule wfctl ships MUST have a cost line, and a test
  MUST fail when one doesn't.
- **FR-014**: The release note MUST say that the next install asks before
  removing the old `--project` ask rule.
- **FR-015**: `auto-approve-grant-asks-first.md` and `install-modes.md` MUST
  NOT be edited, since they're accepted. `settings-edit-asks-first.md` already
  states how both change.

### Key Entities

- **Settings file**: `.claude/settings.json` or `.bob/settings.json` in the
  project. It belongs to the user and holds both the user's entries and wfctl's.
- **Pending change**: one hook or rule wfctl would add, update, or remove in a
  settings file, with a line saying what it's for.
- **Manifest receipt**: the manifest's record that wfctl added an entry to a
  settings file. Install and uninstall use it to tell wfctl's entries from the
  user's.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Each of the 6 "Must keep catching" commands in the threat model
  leaves an existing settings file byte-identical.
- **SC-002**: Each of the 4 "Must let through" cases in the threat model
  completes as described.
- **SC-003**: An upgrade that changes 11 entries in one settings file asks the
  user 1 question.
- **SC-004**: After an unattended install skips a change, the next doctor run
  names that change and the command to apply it, and exits 0 if nothing else is
  wrong.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`.
- One test per "Must keep catching" item, checking the file's bytes before and
  after, with stdin not a terminal.
- One test per "Must let through" item.
- Tests for a yes and a no at a terminal, using the `_interactive` seam, that
  count the questions and the saves.
- A doctor test for each pending-change finding, checking the warning, the
  command, and the exit code.
- `uv run wfctl install-skills --agent claude` in this worktree, run once by the
  user at a terminal, to see the question.

## Assumptions

- Pre-specify design context loaded from the branch's `design.md`.
- Standard input is not a terminal for the worktree creation hook, for
  `/start-session`'s repair, and for an agent's Bash call.
- Whether Claude Code's `!` prefix gives install a terminal on desktop isn't
  known yet. The design doesn't depend on it.
- The agent applying changes after the user approves at Claude Code's prompt
  is out of scope and tracked in #860.
