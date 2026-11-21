# Feature Specification: Agent accepts with approval

**Feature Branch**: `833-agent-accept-with-approval`
**Created**: 2026-11-20
**Status**: Draft
**Input**: User description: "Implement the design in the branch's design.md for #833: the agent runs wfctl arch accept, wfctl review sign-off, and wfctl arch approve-imports after the user approves each at the agent host's permission prompt."

## Clarifications

### Session 2026-11-20

- Q: When the user runs review sign-off or approve-imports in their own terminal, does it still ask for the typed head sha or digest? → A: Yes, keep it at a terminal. Only a run with no terminal skips it.
- Q: When the user accepts a record in their own terminal with no `--agreed`, what does the `Log` line say? → A: Nothing, since `--agreed` stays required at a terminal. Only a run with no terminal can leave it out.
- Q: How does a command tell it's running inside Claude Code before it skips the terminal check? → A: It reads the variable Claude Code itself sets in its shell, not `WFCTL_AGENT`.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Accept a record from the agent's session (Priority: P1)

The user reads a proposed record the agent wrote and tells the agent to accept
it. The agent runs the accept command. The agent host shows the user the exact
command and waits. The user approves, and the record is accepted with a `Log`
line saying it was approved at the permission prompt. If the user declines,
nothing is written.

**Why this priority**: Accepting records is what #833 asked for, and every
level-2 record on every branch passes through it.

**Independent Test**: In a project with the Claude Code layer installed, have
the agent run the accept on a throwaway proposed record. The prompt appears,
the record stays proposed until the user approves, and its `Log` line names
the prompt.

**Acceptance Scenarios**:

1. **Given** a proposed record and the Claude Code rules installed, **When**
   the agent runs the accept in its plain spelling, **Then** the host asks the
   user before the command runs.
2. **Given** the user approves the prompt, **When** the command runs with no
   `--agreed` citation, **Then** the record becomes accepted and its `Log` line
   reads "accepted — approved at the permission prompt".
3. **Given** the user approves the prompt, **When** the command runs with an
   `--agreed` citation, **Then** the `Log` line carries that citation, as it
   does today.
4. **Given** the user declines the prompt, **Then** the record stays proposed
   and nothing is written.

---

### User Story 2 - Sign off a review from the agent's session (Priority: P1)

The user tells the agent to sign off a branch's unreviewed commits. The agent
runs the sign-off command, the host asks, and the user approves. wfctl lists
the commits it covers, records the sign-off, and sends the review note, with
no typed confirmation.

**Why this priority**: The user is blocked by sign-off more often than by
accept, which is why the scope grew to cover it.

**Independent Test**: On a branch with an unreviewed commit, have the agent run
the sign-off. The prompt appears, and once approved, the guard lets the PR
open.

**Acceptance Scenarios**:

1. **Given** unreviewed commits and the rules installed, **When** the agent
   runs the sign-off, **Then** the host asks the user first.
2. **Given** the user approves, **When** the command runs without a terminal,
   **Then** it lists the commits, records the sign-off through HEAD, and sends
   the note, without asking for the head commit's short sha.

---

### User Story 3 - Approve imports from the agent's session (Priority: P2)

The user tells the agent to approve what a branch adds to the import check.
The agent runs the installed `wfctl arch approve-imports`, the host asks, and
the user approves. The command lists the additions and writes the approval
with no typed digest.

**Why this priority**: Import approvals happen less often than accepts and
sign-offs, but they block the same way.

**Independent Test**: On a branch that adds a baseline line, have the agent
run the installed command. The prompt appears, and once approved, the
`review` job passes on a rerun.

**Acceptance Scenarios**:

1. **Given** a branch with an addition, **When** the agent runs the installed
   `wfctl arch approve-imports`, **Then** the host asks the user first.
2. **Given** the agent runs `uv run wfctl arch approve-imports` from a
   worktree, **Then** the guard refuses it, since that runs the branch's own
   code.

---

### User Story 4 - The guard keeps refusing what the prompt can't see (Priority: P1)

An agent wraps one of the three commands, such as in `bash -c`, behind a
runner the rule doesn't match, or chained with another command. The host's
rule doesn't match those forms, so no prompt would appear. The guard refuses
each one and tells the agent to run the plain command.

**Why this priority**: Without it, a wrapped form runs with no prompt and no
refusal, which leaves the action with nobody's agreement.

**Independent Test**: Run every form in the record's "Must keep catching" list
through the guard and confirm each is refused, and every form in "Must let
through" passes.

**Acceptance Scenarios**:

1. **Given** the rules installed, **When** the agent runs `bash -c "wfctl
   arch accept s"`, **Then** the guard refuses it and names the plain command.
2. **Given** wfctl's auto-approve is on, **When** the agent runs a plain
   spelling, **Then** the guard lets it through and Claude Code asks the user.
3. **Given** the guard runs from Bob Shell, **When** the agent runs a plain
   spelling, **Then** the guard refuses it.
4. **Given** `.claude/settings.json` has lost the rule, **When** the agent
   runs a plain spelling, **Then** the guard refuses it and names the install
   command that puts the rule back.

---

### User Story 5 - Doctor reports a missing rule (Priority: P2)

The user runs `wfctl doctor` in a project whose settings file no longer carries
one of the rules. Doctor names the rule and what losing it costs.

**Why this priority**: The guard refuses the plain spelling when the rule is
missing, so the user needs a way to see why.

**Independent Test**: Delete one rule from `.claude/settings.json` and run
`doctor`.

**Acceptance Scenarios**:

1. **Given** a missing rule, **When** the user runs `doctor`, **Then** it
   prints a `⚠` line naming the rule. It leaves the exit code alone, as for
   every managed rule, since the guard refuses the command while the rule is
   gone.

### Edge Cases

- A host wfctl doesn't support, such as Cursor, runs no guard and shows no
  prompt. Each command still needs a terminal there.
- Codex is supported only once a session in Codex shows the prompt appears.
  Until then, each command still needs a terminal in Codex.
- An agent sets the host's session variable by hand to skip the terminal
  check. The record accepts this, and the PR diff or the review note records
  the result.
- The dry run matches the accept's rule, so `wfctl arch accept --dry-run` asks each time. `wfctl arch check-accept` runs the same checks and never asks, so an unattended run uses it.
- A user's own `ask` rule for another command doesn't widen what the guard
  lets through.
- `guard-catches-literal-accept.md` is superseded with no record naming it in
  `supersedes`. Its own `superseded` Log line names the successor, and doctor
  reads that.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: wfctl MUST keep one list of the spellings the host asks for: `wfctl arch accept`, `wfctl review sign-off`, and `wfctl arch approve-imports`. None has a `uv run` spelling, since `uv run wfctl` runs the branch's own copy, which the agent may have edited.
- **FR-002**: `wfctl install-skills --agent claude` MUST write a Claude Code `ask` rule for every spelling in that list.
- **FR-003**: wfctl MUST ship a Codex rules file with a `prompt` rule for every spelling in that list, and a test MUST fail when the file and the list disagree.
- **FR-004**: `wfctl doctor` MUST report a missing rule with a `⚠` line naming what losing it costs, and leave the exit code alone, as for every managed rule.
- **FR-005**: The worktree guard MUST let a command through only when the command is exactly one listed spelling and its arguments, with no separator, substitution, redirect, or second command.
- **FR-006**: The guard MUST NOT refuse a listed spelling because wfctl's auto-approve is on, since the mode doesn't turn off Claude Code's prompt.
- **FR-007**: The guard MUST refuse a listed spelling when the hook runs from Bob Shell.
- **FR-008**: The guard MUST refuse a listed spelling when `.claude/settings.json` doesn't carry its rule, and name the command that restores it.
- **FR-009**: The guard MUST keep refusing every form in the "Must keep catching" list of `prompt-approves-person-commands.md`, and let through every form in its "Must let through" list.
- **FR-010**: A refusal of a wrapped form MUST tell the agent to run the plain command.
- **FR-011**: Each of the three commands MUST run without a terminal when the variable Claude Code sets in its shell is present, and MUST still need a terminal otherwise. `WFCTL_AGENT` MUST NOT count as that signal, since a user's profile can set it in any shell.
- **FR-012**: Without a terminal, `review sign-off` and `arch approve-imports` MUST skip their typed confirmation and still list what they cover before writing. At a terminal, both MUST keep asking for it.
- **FR-013**: Without a terminal, `wfctl arch accept` MUST accept a record with no `--agreed` citation, and write "accepted — approved at the permission prompt" as the `Log` line. At a terminal, `--agreed` MUST stay required.
- **FR-014**: `arch approve-imports` MUST keep refusing to run from a worktree's own copy of wfctl.
- **FR-016**: wfctl MUST offer `wfctl arch check-accept <slug>`, which runs exactly what `wfctl arch accept --dry-run` runs and matches no prompted spelling, and the design gate's fix line MUST name it.
- **FR-015**: `wfctl doctor` MUST NOT warn about a superseded record whose last `superseded` Log line names a record that exists, so one record can replace two without editing an accepted body.
- **FR-017**: If an accepted record's last `Log` line is `amended`, `wfctl arch accept` MUST write a new `accepted` line for the amendment and keep the record accepted. If the last `Log` line is anything else, it MUST still say the record is already accepted and write nothing (#838).

## Key Entities _(include if feature involves data)_

- **Prompted spelling**: one command the host asks for, as the words it starts with and the command it belongs to.
- **Managed rule**: a permission rule wfctl installs and records, so `doctor` can report it missing and `uninstall-skills` can remove it.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: The user accepts a record, signs off a branch, and approves imports without typing in a terminal, in 3 of 3 walks in Claude Code.
- **SC-002**: 100% of the forms in the record's "Must keep catching" list are refused, and 100% of the "Must let through" forms pass.
- **SC-003**: Removing any one installed rule makes `doctor` print a `⚠` line naming it and the guard refuse that spelling.
- **SC-004**: Every accepted record's `Log` line says either where the user agreed or that the user approved at the permission prompt.

## Validation Strategy _(mandatory)_

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy
uv run wfctl doctor
uv run wfctl check config
```

Then walk it: `uv run wfctl install-skills --agent claude`, confirm the rules
are in `.claude/settings.json`, have the agent accept a throwaway proposed
record, and confirm the prompt appears and the record changes only after
approval. Repeat for a sign-off. The suite can't show the prompt appears.

## Assumptions

- Pre-specify design context loaded from specs/833-agent-accept-with-approval/design.md.
- #407 merges before implementation, and this feature reuses its rule plumbing.
- Claude Code sets `CLAUDECODE` in the shell it runs commands in (research R-001).
- Bob Shell's hook payload names its tool in `tool_name`.
- Codex support waits on a session in Codex, so Codex keeps the terminal check in this feature.
