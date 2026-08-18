# Feature Specification: Sweep the one-time migration checks

**Feature Branch**: `36-sweep-migration-checks`
**Created**: 2026-08-17
**Status**: Draft
**Input**: Issue #36 — "Sweep the one-time migration checks once the transitions have landed"

## Clarifications

### Session 2026-08-17

- Q: Is the stranded-spec-directory report transitional, or does it still have
  live work? → A: Recurring drift — keep it. The setup prompt that creates the
  condition still ships, and a repository can adopt or switch an external spec
  root at any time, stranding whatever `specs/` had already accumulated. This
  supersedes the design document's count: the sweep removes two reports, not
  three.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Health output stops reporting finished transitions (Priority: P1)

A developer runs the health check on a repository that completed every past
artifact-layout migration. Today it still prints warnings about a superseded
artifact directory and a retired hook command name — neither of which describes
anything wrong with that repository. After this change, both reports are gone and
the output describes only live drift.

**Why this priority**: This is the payoff issue #36 asks for. Health output that
grows monotonically trains the reader to skim past it, which defeats the one
warning in that output whose job is to be noticed — the unarchived-teardown
warning.

**Independent Test**: Run the health check in a fully-migrated repository and
confirm neither retired report appears, while both surviving drift reports still
appear when their conditions hold.

**Acceptance Scenarios**:

1. **Given** a repository with no superseded artifact directory and a hook naming
   the current command, **When** the health check runs, **Then** no
   transition-related warning is printed.
2. **Given** a repository that still has a superseded artifact directory,
   **When** the health check runs, **Then** it is not mentioned — the health
   check no longer reports on it at all.
3. **Given** a repository whose teardown hook names the retired command, **When**
   the health check runs, **Then** it is not mentioned; teardown still archives,
   and the archive command itself reports the retired name (Story 2).
4. **Given** a repository whose teardown hook does not archive at all, **When**
   the health check runs, **Then** it still warns and still offers to wire the
   hook.
5. **Given** a repository with a recorded external spec root and in-repo spec
   directories that will not be found, **When** the health check runs, **Then**
   it still reports them — this condition is reachable by any repository that
   adopts or switches a spec root, not only by one predating a migration.

---

### User Story 2 - An unmigrated machine announces itself during teardown (Priority: P2)

Two compatibility paths survive this change because deleting them destroys data:
the read that rescues artifacts from the superseded directory, and the retired
command name still accepted by the archive command. A developer tearing down a
worktree on a machine that predates either move sees a line saying so, naming
what was rescued or which name was used and how to update it. On an already
migrated machine, neither line appears.

**Why this priority**: Issue #36's core complaint is that a comment naming its
own deletion trigger never fires because nothing observes the condition. These
two lines make the condition observable from ordinary use, so the follow-up
removal rests on evidence rather than on a comment nobody reads.

**Independent Test**: Tear down a worktree containing a superseded artifact
directory and confirm the rescue line names the file count; invoke the archive
command under its retired name and confirm the rename notice appears. Repeat
both on clean inputs and confirm silence.

**Acceptance Scenarios**:

1. **Given** a worktree holding a superseded artifact directory, **When** the
   archive command runs, **Then** one line reports how many files were rescued
   from it and states that the path is scheduled for removal.
2. **Given** a worktree with no superseded artifact directory, **When** the
   archive command runs, **Then** no rescue line is printed.
3. **Given** a teardown hook invoking the archive command by its retired name,
   **When** the command runs, **Then** it reports the current name and how to
   re-seed the hook, and still archives normally.
4. **Given** the archive command invoked by its current name, **When** it runs,
   **Then** no rename notice is printed.
5. **Given** a worktree that both holds a superseded directory and is invoked
   under the retired name, **When** the command runs, **Then** both lines appear
   and neither suppresses the other.

---

### User Story 3 - Newly seeded repositories get the current command name (Priority: P3)

A developer seeds configuration into a repository. The teardown hook it receives
names the archive command by its current name, not the retired one.

**Why this priority**: Smallest change of the three, but without it the retired
name is re-seeded into every new repository, so Story 2's rename notice would
fire forever and its condition could never reach zero. Story 2's alias half is
only closable once this ships.

**Independent Test**: Seed configuration into an empty repository and confirm the
resulting hook names the current command; confirm the retired name appears
nowhere in the seeded file.

**Acceptance Scenarios**:

1. **Given** an unseeded repository, **When** configuration is seeded, **Then**
   the teardown hook invokes the archive command by its current name.
2. **Given** a repository seeded before this change, **When** the health check
   runs, **Then** it is not reported (Story 1 removed that report) but teardown
   still archives correctly via the retained compatibility name.

---

### Edge Cases

- A teardown hook file that cannot be read: the surviving hook warning reports
  the read failure; no retired-name reporting is attempted.
- A repository with no teardown hook file at all: no warnings, since not every
  repository uses the worktree tool.
- A superseded artifact directory holding files other than the design document:
  every file is rescued, and the rescue line counts all of them.
- A superseded artifact directory that exists but is empty: nothing is rescued
  and no rescue line is printed.
- A worktree whose spec directory lives outside it: the durable-spec-dir notice
  and the rescue line are independent and may both appear.
- A machine already fully migrated: teardown prints neither new line, which is
  the signal the compatibility paths are removable.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The health check MUST NOT report the presence of a superseded
  per-branch artifact directory.
- **FR-002**: The health check MUST continue to report in-repo spec directories
  stranded by a recorded external spec root. This condition is reachable by any
  repository that adopts or switches a spec root, so the report is recurring
  drift rather than a transition.
- **FR-003**: The health check MUST NOT report a teardown hook that names the
  retired archive command.
- **FR-004**: The health check MUST continue to report, and offer to fix, a
  teardown hook that does not archive at all. This check is not transitional.
- **FR-005**: Supporting logic that exists solely to serve a removed report MUST
  be removed with it, leaving no unreferenced helpers.
- **FR-006**: The archive command MUST continue to rescue every file from a
  superseded per-branch artifact directory before the worktree is destroyed.
- **FR-007**: The archive command MUST report, in one line, how many files it
  rescued from the superseded directory, and MUST state that the path is
  scheduled for removal.
- **FR-008**: The archive command MUST print nothing about the superseded
  directory when it rescues no files from it.
- **FR-009**: The archive command MUST continue to accept its retired name so
  that existing teardown hooks keep archiving.
- **FR-010**: When invoked under its retired name, the archive command MUST
  report the current name and the action that updates the hook.
- **FR-011**: When invoked under its current name, the archive command MUST print
  no rename notice.
- **FR-012**: Neither new report may change the archive command's exit code, and
  neither may prevent archiving from completing.
- **FR-013**: The bundled teardown-hook template MUST name the archive command by
  its current name, in both the executable hook line and its explanatory comment.
- **FR-014**: Each retained compatibility path MUST carry, in the code beside it,
  a removal condition stated in terms of the output it emits.
- **FR-015**: Tests asserting the behavior of removed reports MUST be removed;
  tests MUST be added covering the two new reports in both their firing and
  silent states.

## Key Entities

- **Superseded artifact directory**: The per-branch location that previously held
  design artifacts, before they moved into the branch's spec directory. Read only
  to rescue its contents during teardown; nothing infers pipeline state from it.
- **Teardown hook**: The repository-local configuration entry invoked before a
  worktree is removed. May name the archive command by its current or retired
  name; may be absent.
- **Bundled hook template**: The teardown-hook configuration shipped inside the
  tool and copied into repositories on seeding. Its command name determines what
  newly seeded repositories inherit.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: On a fully migrated repository, the health check prints zero
  transition-related warnings, down from up to two today. Both surviving drift
  reports still fire when their conditions hold.
- **SC-002**: The retired archive command name appears zero times in a newly
  seeded repository's configuration.
- **SC-003**: Tearing down a worktree holding superseded artifacts prints exactly
  one rescue line, naming a file count that matches the number of files rescued.
- **SC-004**: Tearing down a fully migrated worktree prints neither of the two
  new lines, giving a single observable signal that the compatibility paths are
  removable.
- **SC-005**: A developer can decide whether the two retained paths are removable
  using only output observed during normal teardowns, without inspecting code or
  running a dedicated audit command.
- **SC-006**: No artifact is lost in any teardown scenario covered by the
  acceptance scenarios above.

## Assumptions

- Pre-specify design context loaded from
  `specs/36-sweep-migration-checks/design.md`.
- The install base is a single developer across several machines; the tool is not
  published to a package index (issue #2 open). The removal condition for the
  retained paths is therefore "every one of my machines", not a release count.
- The teardown-hook template now ships inside the tool package following the
  vendoring change (#43/#47), so correcting it is a change to this repository
  rather than a cross-repository dependency.
- Removing the two retained compatibility paths is out of scope here and lands in
  a follow-up change once the conditions in FR-014 are observed to hold.
- Exit-code behavior of the health check is out of scope; that is issue #41. This
  change removes reports that never affected the exit code.

## Validation Strategy _(mandatory)_

- `uv run pytest -q` — full suite, including the removed and added test cases
  required by FR-015.
- `uv run ruff check .` — catches helpers left unreferenced by FR-005.
- `uv run mypy` — type coverage over the changed command signature.
- `.github/scripts/check_wheel_contents.py` and
  `.github/scripts/check_installed_tree.py` — confirm the corrected hook template
  (FR-013) ships in the wheel and lands correctly on install.
- Manual: run the health check in this repository before and after, and confirm
  the transition-related warnings disappear while the teardown-hook warning
  survives.
