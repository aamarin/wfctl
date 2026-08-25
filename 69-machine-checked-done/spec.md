# Feature Specification: Machine-checked done

**Feature Branch**: `69-machine-checked-done`
**Created**: 2026-08-23
**Status**: Draft
**Input**: No description typed. Specification derived from `design.md` in this
directory, which records an approved four-level design pass for issue #69.

## Clarifications

### Session 2026-08-24

- Q: When is code identity captured, given the tree can change while verification runs? → A: Before and after the run; a mismatch records the run as inconclusive.
- Q: What happens to an interrupted verification run? → A: Nothing is written; the previous record survives and the next run repeats every command. No resume.
- Q: What does `wfctl verify` do when no definition of done is configured? → A: Prints a notice and exits 0, matching how tracker dispatch degrades.
- Q: Does the implementation step run verification itself? → A: Yes, as its final action, and it still writes the completion artifact.
- Q: Are completed verification runs appended to the session event log? → A: Yes, one event per completed run, carrying verdict, commit, and the failing command.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Completion cannot be self-certified (Priority: P1)

A developer's agent finishes an implementation, ticks every task, and writes the
completion artifact — but a check the project defined has not passed. Today the
pipeline reports the work complete. It should report the work blocked, and say
why.

**Why this priority**: This is the defect. Every other story is either a
safeguard around it or a consequence of it. Shipped alone, it delivers the whole
value: a completion claim backed by something other than the claimant.

**Independent Test**: Configure a definition of done that fails. Complete every
task. Confirm the pipeline reports implementation incomplete and names the failing
command.

**Acceptance Scenarios**:

1. **Given** a project with a definition of done and every task
   complete, **When** verification has never run, **Then** the pipeline reports
   implementation in progress and directs the user to run verification.
2. **Given** the same project, **When** verification runs and a command exits
   non-zero, **Then** the pipeline reports implementation in progress and names
   the command that failed.
3. **Given** the same project, **When** every command exits zero and
   the code has not changed since, **Then** the pipeline reports implementation
   complete.
4. **Given** a completion artifact asserting the work is done, **When** no passing
   verification exists, **Then** the artifact does not make the pipeline report
   complete.

---

### User Story 2 - A stale pass is not a pass (Priority: P2)

A developer verifies, then keeps working. The recorded verdict describes code that
no longer exists. The pipeline should stop reporting it as current.

**Why this priority**: Without it, story 1 is satisfied once and then decays into
the same false green it replaced — a verdict with no expiry is a claim about
nothing in particular.

**Independent Test**: Verify successfully, change one line without committing,
and confirm the pipeline no longer reports complete.

**Acceptance Scenarios**:

1. **Given** a passing verification, **When** a new commit is made, **Then** the
   pipeline reports implementation in progress and states which commit was
   verified.
2. **Given** a passing verification on a clean tree, **When** any uncommitted
   change exists, **Then** the pipeline reports implementation in progress and
   states that the tree has uncommitted changes.
3. **Given** a passing verification, **When** the configured command list changes,
   **Then** the pipeline reports implementation in progress, because the recorded
   verdict was produced by a different definition of done.
4. **Given** a passing verification, **When** the project is cloned fresh
   elsewhere, **Then** the new checkout reports implementation in progress,
   because nothing has been verified there.

---

### User Story 3 - Projects without a definition of done are untouched (Priority: P3)

A project that has not declared a definition of done sees no change of any kind.

**Why this priority**: Adoption safety. The feature must be additive; a project
that ignores it must not experience a pipeline that suddenly refuses to complete.

**Independent Test**: Run the full pipeline on a project with no configuration
file and confirm every reported state is identical to the current release.

**Acceptance Scenarios**:

1. **Given** no configuration file, **When** the pipeline reports status, **Then**
   every step reports exactly as it does today.
2. **Given** a configuration file with no verification key, or an empty command
   list, **Then** behavior is identical to having no file.

---

### Edge Cases

- **Verification run on a dirty tree.** The run proceeds and the result is
  recorded, but the record can never report complete while uncommitted changes
  remain. The command warns at the point of running, rather than letting the user
  discover it from a status line later.
- **A command is not installed.** Treated as a failed verification, not
  as a missing configuration — reporting complete because the checker is absent is
  the defect being fixed.
- **Verification passes while tasks are incomplete.** Implementation remains in
  progress. Verification is an additional condition, never a replacement for the
  existing ones.
- **A recorded verdict exists but no tasks are defined.** The step reports not
  started; a verdict about nothing does not begin the step.
- **The tree changes while verification runs.** The verdict describes a mixture of
  two states and is recorded as inconclusive; the user is told to re-run rather
  than shown a pass or a failure that neither capture supports.
- **Verification is interrupted.** Nothing is recorded and the previous record is
  left intact, so status continues to report whatever was last actually proven.
  The next run repeats every command from the start.
- **The configuration file is malformed.** `wfctl verify` reports the
  problem and exits non-zero. It is never treated as "no verification configured",
  because silent degradation is indistinguishable from the defect.
- **The record is deleted or the state directory is cleared.** Reports as never
  verified, which is true.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST read an optional, version-controlled, repository-level
  definition of done consisting of an ordered list of commands.
- **FR-002**: System MUST treat an absent file, a missing key, or an empty list as
  "no verification configured" and preserve today's completion behavior exactly.
- **FR-003**: System MUST provide a command that runs every configured command and
  records the outcome.
- **FR-004**: The record MUST capture the commands that ran, the overall verdict,
  which commands failed if any, the commit identity, whether the working tree had
  uncommitted changes, and when it ran. Commit identity and working-tree state
  MUST be captured both immediately before and immediately after the run.
- **FR-005**: System MUST derive the verdict from running the commands. It MUST
  NOT accept a verdict asserted by the caller or read one from any artifact the
  implementing agent writes.
- **FR-006**: When verification is configured, System MUST report implementation
  complete only when **all** hold: every task is complete; a recorded verdict
  passed; the record's commit matches the current commit; the working tree has no
  uncommitted changes; and the recorded commands match the definition of done.
- **FR-007**: When implementation is blocked by verification, System MUST state
  which condition failed — never run, failed, commit moved, tree dirty, or
  definition changed.
- **FR-008**: When implementation is blocked by verification, the next action the
  system directs the user to MUST be verification, not the implementation step
  whose tasks are already complete.
- **FR-009**: The status check MUST NOT execute the definition of done. It may
  read only the record and inexpensive repository state.
- **FR-010**: Commands MUST be executed as argument vectors, never
  through a shell, so that command text cannot be interpreted as shell syntax.
- **FR-011**: The configuration file MUST remain tracked by version control.
  Installation MUST NOT add it to the project's ignore rules.
- **FR-012**: A malformed configuration MUST be reported as an error by
  `wfctl verify`, not silently treated as absent.
- **FR-013**: `wfctl verify` MUST run every command even
  after one fails, so a single run reports every problem, and MUST exit non-zero
  when any failed.
- **FR-014**: Project documentation asserting that pipeline phases cannot be faked
  MUST be corrected to describe what is actually enforced.

- **FR-016**: When code identity differs between the capture before the run and
  the capture after it, System MUST record the run as inconclusive and MUST NOT
  report implementation complete from it. A verdict produced against a tree that
  changed mid-run describes neither state.

- **FR-017**: System MUST write the record only after every configured command has
  finished. An interrupted run MUST leave any existing record unchanged, so that a
  record's existence is itself proof the run completed.
- **FR-018**: System MUST NOT reuse a previous command result to skip work on a
  later run. Every run executes every configured command.

- **FR-019**: When no definition of done is configured, `wfctl verify`
  MUST report that fact and exit zero. Nothing to run is not a failure, and an
  unconditional caller — a setup hook, a CI step — must not break on a project
  that has not adopted the feature.

- **FR-020**: The implementation step MUST run verification as its final action and
  report the verdict, so the agent holding the context is the one told the build is
  red. It MUST continue to write its completion artifact, which remains the
  completion signal for projects with no verification configured.
- **FR-021**: The implementation step MUST NOT report the work complete when the
  verification it just ran did not pass.

- **FR-022**: Every completed verification run MUST append one entry to the
  session event log, carrying the verdict, the commit identity, and which command
  failed if any — so the history distinguishes a verdict earned over several
  attempts from one that appeared at once.

- **FR-015**: The repository health check MUST report a malformed configuration
  file as a finding. Promoted out of Deferred at analysis: it is additive once
  FR-012's loader exists, and a silently ignored broken configuration is the exact
  failure mode this feature removes.
- **FR-023**: A configured command that cannot be executed — no such executable on
  PATH — MUST be recorded as a failed command and reported by name. It MUST NOT
  surface as an unhandled error, and MUST NOT be read as an absent configuration.

## Terminology

One name per concept, across every artifact for this feature.

| Canonical | Means | Not |
| --- | --- | --- |
| definition of done | the ordered command list a repository declares | verification command, configured commands, the check |
| command | one entry in the definition of done; "configured command" is fine where it aids precision | the check |
| verification run | one execution of the whole list | a verification, the check |
| `wfctl verify` | the CLI command that performs a run | the verification command |
| verification record | what a completed run leaves on disk | the result file, the verdict file |
| verdict | pass or fail, derived from exit codes | result, outcome |

"verification command" is banned because it named two different things — the CLI
verb and one entry in the list. Where the distinction matters, say `wfctl verify`
or say command.

## Key Entities

- **Definition of Done**: An ordered list of commands, owned by the project and
  committed to version control. Chosen by a human at configuration time; the
  system never infers or guesses it, because a wrong guess reports success for a
  check that never ran.
- **Verification Record**: The outcome of one verification run, scoped to one
  branch and one checkout, never committed. Holds the verdict, the commands that
  produced it, and the identity of the code it describes. Its claim expires when
  any of those three change.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A project with no verification configured produces byte-identical
  pipeline output before and after this change, in every reachable state.
- **SC-002**: Reporting status executes zero commands from the definition of done, and adds at most
  a constant number of repository queries — so its cost does not grow with the
  size of the definition of done.
- **SC-003**: With a failing definition of done, implementation never reports
  complete, regardless of task state or completion artifacts present.
- **SC-004**: After any code change, committed or not, a previously passing verdict
  stops reporting complete until verification is re-run — measured as zero states
  in which changed code reports a green verdict.
- **SC-005**: A fresh checkout of a verified branch reports implementation
  incomplete until verification runs there.
- **SC-006**: A user blocked by verification learns which condition failed, and
  which commands failed, from `wfctl status` alone — not only from the output of
  the verification run, and without opening a file.
- **SC-007**: Reaching a complete implementation report requires a clean working
  tree, so every completion claim corresponds to committed code.
- **SC-008**: For any branch, the number of verification attempts and their
  outcomes can be reconstructed from the session event log alone, without the
  record.

## Assumptions

- Pre-specify design context loaded from `design.md` in this directory.
- **Untracked files count as uncommitted changes.** A new source file is untracked
  until added, and excluding untracked files would let new code reach a complete
  report without ever being verified. The cost is that scratch files also block
  completion.
- **Completion requires a clean tree.** This follows from FR-006 rather than being
  chosen separately: a record taken on a dirty tree describes code that is already
  not what is on disk. Stated explicitly because it is a behavior change worth
  seeing before it is discovered.
- **The configuration file is visible, not hidden.** A project's definition of done
  is not incidental configuration.
- **One definition of done per repository**, not one per pipeline step. No evidence
  exists that per-step verification is wanted.
- `wfctl verify` is available to a developer and to automation alike; no
  network access or hosting provider is assumed.

## Validation Strategy _(mandatory)_

- The project's own definition of done must pass: its test suite, its linter, and
  its type checker, plus its repository health check.
- **Story 1**: automated coverage for each completion condition in FR-006, each
  asserted independently — a test per condition, so a single over-broad
  implementation cannot satisfy them all at once.
- **Story 2**: automated coverage for each staleness trigger — commit moved, tree
  dirty, definition changed — asserted to report incomplete.
- **Story 3**: a regression assertion that pipeline output for an unconfigured
  project is unchanged, exercised across every reachable step state.
- **FR-005 (non-forgeability)**: a negative test asserting that a completion
  artifact written by the implementing agent does not, by itself, produce a
  complete report when verification is configured.
- **FR-009 (cost)**: an assertion that reporting status does not execute the
  definition of done.
- **FR-010 (argument vectors)**: a test with a command containing shell
  metacharacters, asserting they are passed through as literal arguments.
- **FR-011 (stays tracked)**: a positive assertion that installation leaves the
  configuration file tracked, because the ignore list it must stay out of is easy
  to extend by accident.
- **FR-016 (moving tree)**: a test that changes the tree between the two identity
  captures and asserts the run records as inconclusive rather than pass or fail.
- **FR-017 (interruption)**: a test that interrupts a run mid-list and asserts no
  record was written and any prior record is byte-identical.
- **FR-019 (no config)**: an assertion that `wfctl verify` exits zero and
  reports the absence, so an unconditional caller does not break.
- **FR-020/FR-021 (skill integration)**: an assertion that the implementation step
  does not report complete when the verification it ran did not pass.
- **FR-022 (audit trail)**: an assertion that a failing run followed by a passing
  run leaves two distinguishable entries in the event log.
