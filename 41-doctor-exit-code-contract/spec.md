# Feature Specification: doctor exit-code contract

**Feature Branch**: `41-doctor-exit-code-contract`
**Created**: 2026-08-17
**Status**: Draft
**Input**: Issue #41 — "doctor: one exit-code contract, and the checks that belong in it", with children #36, #31, #38

## Clarifications

### Session 2026-08-17

- Q: When a whole installed directory is abandoned, is that one finding or one per file inside it? → A: One finding, at the unit the install record stores — a directory is reported as a directory.
- Q: A check offers to fix the drift and the user accepts, so the repository is clean by the time the run ends. Exit zero or non-zero? → A: Zero. The exit code describes the repository's state when the run finishes, not what was observed along the way.
- Q: What should "the closest shipped name" mean when a table entry names no shipped command? → A: A nearest-match suggestion drawn from the shipped command names, using the standard library's existing close-match facility rather than hand-written matching.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A build can trust what doctor's exit code means (Priority: P1)

Someone adds `wfctl doctor` to a CI job. They need the job to fail when the
repository has genuinely drifted, and to pass otherwise — including when the
machine running it has no network.

Today the same command reports a problem and exits 0, so the job passes while
printing warnings nobody reads. Three different conventions coexist inside one
command: one check contributes a numeric code, four contribute nothing at all,
and a loop sets the code inline.

**Why this priority**: Every other story here either adds a check that must pick
a convention or removes one. Without a stated convention each new check invents
its own, which is how the current three arose.

**Independent Test**: Put `wfctl doctor` in a CI job against a repository with a
known single piece of drift; confirm the job fails. Remove the drift; confirm it
passes. Disconnect the network; confirm it still passes.

**Acceptance Scenarios**:

1. **Given** a repository whose teardown hook does not archive, **When** `doctor`
   runs, **Then** it reports the finding and exits non-zero.
2. **Given** a repository with no findings, **When** `doctor` runs, **Then** it
   exits zero.
3. **Given** no network access, **When** `doctor` runs and cannot determine
   whether a newer version exists, **Then** it says so and exits zero.
4. **Given** a layer installed before content hashing existed, **When** `doctor`
   runs, **Then** it reports that drift cannot be measured and exits zero.
5. **Given** a repository whose only problem is one a check can fix, **When**
   `doctor` runs interactively and the user accepts the offered fix, **Then** the
   repository is left clean and the run exits zero.
6. **Given** the same repository, **When** the user declines the fix, **Then** the
   run exits non-zero.

---

### User Story 2 - A newly set-up repository reports clean (Priority: P1)

Someone runs the command that seeds a repository's workmux configuration, then
runs `doctor`. Nothing they did was wrong, so `doctor` should find nothing.

Today it reports the seeded file as stale, and the remedy it prints is to re-run
the command that produced it — a loop with no exit. Under Story 1's contract
this would also fail their build on their first day.

**Why this priority**: Story 1 is unusable without this. A contract that fails
every freshly configured repository would be withdrawn the week it shipped.

**Independent Test**: Seed a fresh repository's configuration, run `doctor`, and
confirm it says nothing about the file just written.

**Acceptance Scenarios**:

1. **Given** an empty repository, **When** its configuration is seeded and
   `doctor` runs, **Then** no finding refers to the seeded file.
2. **Given** the shipped configuration template, **When** it is checked against
   the same rule `doctor` applies, **Then** it does not name a superseded command.
3. **Given** a repository whose configuration still names the superseded command
   because it was written long ago, **When** `doctor` runs, **Then** the teardown
   is still recognised as protected.

---

### User Story 3 - What the tool abandoned is surfaced (Priority: P2)

A skill or command file is renamed upstream. Installing again writes the new
name and leaves the old file behind, recorded nowhere. Uninstalling cannot reach
it either, because uninstall only removes what is currently recorded.

The leftover is not inert: it remains a valid, invocable command whose
instructions point at a handoff path nothing reads any more. Someone invokes it,
it appears to work, and the work goes to a location the rest of the pipeline
ignores.

**Why this priority**: Real and observed in a consuming repository, but it
misleads rather than breaks, and it needs Story 1's convention to decide whether
it fails a build.

**Independent Test**: Install, rename a source file, install again, then run
`doctor` and confirm the abandoned entry is named.

**Acceptance Scenarios**:

1. **Given** a file the tool installed and no longer records, **When** `doctor`
   runs, **Then** it names that file and exits non-zero.
2. **Given** a file the user wrote themselves in their own agent directory,
   **When** `doctor` runs, **Then** it is not reported.
3. **Given** a repository where every installed file is still recorded, **When**
   `doctor` runs, **Then** it reports no abandoned entries.
4. **Given** an installed directory that is no longer recorded, **When** `doctor`
   runs, **Then** it reports that directory once, not each file inside it.

---

### User Story 4 - The pipeline never names a command that does not exist (Priority: P3)

Starting a session prints the next command to run. That name comes from a table
that nothing verifies. The table can name a command that is not shipped, and the
first symptom is a session being told to run something that answers to nothing.

This has happened: the table said one name while the shipped command said
another, and it was caught by a person reading the output a week later.

**Why this priority**: Real, but the shipped commands and the table now live
together, so the check is cheap and catches the drift before release rather than
after.

**Independent Test**: Change a table entry to a name that is not shipped and
confirm the build fails.

**Acceptance Scenarios**:

1. **Given** every table entry names a shipped command, **When** the build runs,
   **Then** it passes.
2. **Given** a table entry naming a command that is not shipped, **When** the
   build runs, **Then** it fails, names the entry, and suggests the nearest
   shipped name.
3. **Given** a checkout where nothing has been installed, **When** the build
   runs, **Then** the check still works.

### Edge Cases

- **Nothing recorded as installed.** `doctor` stops early. Every file on disk is
  then unrecorded, so reporting abandoned entries would name all of them. The
  abandoned-entry report is skipped in this state.
- **Configuration file cannot be read.** Reported once, by the check that owns
  the file. A second check that reads the same file stays quiet rather than
  repeating it.
- **A finding is reported but the user declines the offered fix.** The decline is
  not recorded; the drift stands, so the run exits non-zero and re-reports on the
  next run.
- **A fix is offered where no person can answer.** Run without an interactive
  terminal, the offer is skipped and the drift stands, so the exit code is the
  same as declining. This is the only path a build ever takes.
- **No shipped command resembles a broken table entry.** The failure names the
  entry with no suggestion rather than offering an unrelated name.
- **The tool's own bundled content is missing or partial.** Reported as an error
  rather than treated as drift, because the remedy is reinstalling the tool, not
  reinstalling into the repository.
- **Multiple findings in one run.** All are reported; the exit code reflects that
  at least one was found, not how many.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Every health check MUST report one of three outcomes — drift found,
  no drift found, or could not determine.
- **FR-002**: `doctor` MUST exit non-zero when at least one check reports drift
  found, and zero otherwise. The code describes the repository's state when the
  run ends: drift a check resolved during the run — by applying a fix the user
  accepted — leaves nothing found.
- **FR-003**: A check reporting "could not determine" MUST NOT change the exit
  code, and MUST say so in its output rather than appearing to pass.
- **FR-004**: The convention MUST be recorded once, where the checks are defined,
  so a later check adopts it rather than inventing a third.
- **FR-005**: The shipped configuration template MUST NOT name a superseded
  command, and this MUST be verified automatically against the same rule `doctor`
  applies.
- **FR-006**: The check reporting a superseded command name in a repository's
  configuration MUST be removed, its stated removal condition now being met.
- **FR-007**: Configurations naming the superseded command MUST continue to be
  recognised as protected, so an older repository is never told its teardown is
  unwired.
- **FR-008**: `doctor` MUST report entries inside the tool's own installation
  trees that it installed but no longer records.
- **FR-008a**: Each abandoned entry MUST be reported at the granularity the
  install record uses. A directory installed and recorded as one path is one
  finding, not one per file within it.
- **FR-009**: The abandoned-entry report MUST NOT examine directories shared with
  the user's own agent configuration.
- **FR-010**: The abandoned-entry report MUST report only — never delete or move.
- **FR-011**: Every entry in the pipeline's step-to-command table MUST be verified
  against the shipped command set automatically, without a network connection and
  without anything being installed.
- **FR-012**: When a table entry names no shipped command, the failure MUST name
  the entry and the nearest shipped name, so a rename is distinguishable from a
  wrong table entry. The nearest-match suggestion MUST come from an existing
  standard-library facility rather than hand-written matching.
- **FR-013**: The version-freshness check MUST be left unmodified by this work,
  its rewrite belonging to separate, already-scoped work on the same function.

## Key Entities

- **Check**: One health question asked about a repository. Produces a human-
  readable report and exactly one of the three outcomes in FR-001.
- **Finding**: A single reported problem, with the observation and the action
  that resolves it. Multiple findings may come from one check.
- **Record of installed entries**: The list of paths the tool wrote into a
  repository. Some entries are single files, others whole directories installed
  as one unit. An entry present in an installation tree but absent from this
  record is what Story 3 reports, at the same granularity the record uses.
- **Step-to-command table**: The mapping from pipeline step to the command that
  advances it. Story 4 verifies its values against the shipped command set.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: For each check, a repository exhibiting exactly that one problem
  causes a non-zero exit, and the same repository with the problem removed causes
  a zero exit. Verified for 100% of checks.
- **SC-002**: With no network available, `doctor` completes and exits zero on a
  repository with no other findings.
- **SC-003**: A repository whose configuration was seeded moments earlier
  produces zero findings about that configuration.
- **SC-004**: A step-to-command mismatch is caught by an automated check before
  release. The prior detection path was a person noticing the printed output,
  roughly a week after the mismatch appeared.
- **SC-005**: Every finding produced against the two known repositories is
  confirmed genuine on inspection — zero false positives. One of the two carries
  real drift of a known kind and is expected to produce findings.
- **SC-006**: The whole feature is verifiable offline, with no test requiring
  network access.
- **SC-007**: An abandoned directory holding N files produces exactly one finding,
  for any N.

## Validation Strategy _(mandatory)_

- **Full suite**: `uv run --frozen pytest`. Baseline before this work is 395
  passing. Bare `python3 -m pytest` is not a valid run — it reports dozens of
  false failures because the package is not installed in that interpreter.
- **Type check**: the project's configured type checker over the changed modules.
- **Interactive fix path**: assert the exit code both when the offered fix is
  accepted (zero, repository left clean) and when it is declined (non-zero), plus
  the non-interactive path where the offer is skipped entirely.
- **Exit-code behaviour**: a test per check, asserting the exit code in both the
  drift and no-drift states, plus one asserting an undetermined outcome leaves the
  code at zero.
- **Regression coverage for the template**: assert the shipped configuration
  through the same rule `doctor` applies, rather than against a copied literal, so
  the two cannot disagree. Existing configuration tests seed a substitute bundle
  and therefore never read the shipped file.
- **End-to-end confirmation**: seed a fresh repository's configuration and run
  `doctor` against it, confirming a clean report — the loop described in Story 2
  is not observable from unit tests alone.
- **Prior-convention tests**: the existing test asserting that a drift warning
  leaves the exit code unchanged encodes the convention being replaced, and is
  expected to be rewritten rather than preserved.

## Assumptions

- Pre-specify design context loaded from
  `41-doctor-exit-code-contract/design.md` in the recorded spec root.
- The four checks flipped to affecting the exit code all key on positive evidence
  of drift and stay silent on a clean repository, so the flip introduces no new
  findings. Verified against this repository, which reports none of them.
- Nobody hand-authors files into the tool's own installation trees. If that
  assumption fails, the abandoned-entry report produces false findings, which under
  FR-002 become build failures.
- The superseded command name has no remaining consumer beyond the shipped
  template already corrected here. Checked against this repository and the one
  known consuming repository.
- Reporting abandoned entries, rather than removing them, is the right default:
  removal is correct for a genuine rename and destructive when the file was edited
  locally or its layer was intentionally deselected.
- Whether the stranded-spec-directory check is transitional or permanent does not
  affect this work. It changes a docstring, not behaviour, and is deferred.
- One pull request covers all four stories. Story 4 shares no code with the others
  and could be separated, but is kept together as a single reviewable decision.
