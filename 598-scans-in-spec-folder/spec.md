# Feature Specification: Scan files in the spec folder

**Feature Branch**: `598-scans-in-spec-folder`  
**Created**: 2026-11-11  
**Status**: Draft  
**Input**: Issue #598, and `design.md` in this folder.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A review step saves its scan beside the spec (Priority: P1)

A developer runs clarify, plan review, or analyze on a feature. The step saves
its scan file in the feature's spec folder, as `scans/clarify.md`,
`scans/plan-review.md`, or `scans/analyze.md`. The branch commits nothing for
the scan, so the PR carries only the code change.

**Why this priority**: This is the change the issue asks for. Without it, every
PR in a repository using wfctl carries up to three scan commits that describe
files the PR doesn't contain.

**Independent Test**: Run each step's instructions on a feature and check that
the scan file appears under `scans/` in the spec folder, and that `git status`
in the code repository shows nothing new under the arch root.

**Acceptance Scenarios**:

1. **Given** a feature with a written `spec.md`, **When** clarify finishes,
   **Then** `scans/clarify.md` exists in the spec folder, and the branch adds no
   file under `<arch-root>/scans/`.
2. **Given** a reviewed plan, **When** plan review finishes, **Then**
   `scans/plan-review.md` exists in the spec folder.
3. **Given** `tasks.md`, **When** analyze finishes, **Then** `scans/analyze.md`
   exists in the spec folder.
4. **Given** scan files in the spec folder, **When** the developer saves the
   specs with `wfctl store specs`, **Then** the scan files are saved with the
   rest of the folder.

---

### User Story 2 - A skipped scan stops the pipeline (Priority: P1)

An unattended agent runs clarify and writes `## Clarifications` into `spec.md`
but no scan file. `wfctl status` keeps clarify as the current step and says the
scan file is missing, so the agent is sent back to clarify before planning
starts.

**Why this priority**: The PR reviewer used to find a skipped scan by its
absence from the PR. Once scans leave the PR, this check is the only thing that
finds one.

**Independent Test**: Build a feature folder with `## Clarifications` in
`spec.md` and no scan file, and check that `wfctl status` shows clarify as
current with the missing-scan reason.

**Acceptance Scenarios**:

1. **Given** a spec with `## Clarifications` and no `scans/clarify.md`, **When**
   the user runs `wfctl status`, **Then** clarify is the current step and its
   line reads `no scan file`.
2. **Given** `scans/clarify.md` without a `Verdict` line, **When** the user runs
   `wfctl status`, **Then** clarify is current and reads `scan file has no
   verdict`.
3. **Given** `scans/clarify.md` with a verdict and no coverage row carrying a
   status, **When** the user runs `wfctl status`, **Then** clarify is current
   and reads `scan file has no coverage rows`.
4. **Given** an analysis report and no `scans/analyze.md`, **When** the user
   runs `wfctl status`, **Then** analyze is current with the missing-scan reason.
5. **Given** a plan review report with no open BLOCKER and no
   `scans/plan-review.md`, **When** the user runs `wfctl status`, **Then** the
   plan review pass holds `plan` with the missing-scan reason.

---

### User Story 3 - A feature already past a step isn't sent back (Priority: P2)

A feature planned before this change has its clarify scan committed under the
arch root and a written `plan.md`. After upgrading wfctl, `wfctl status` still
reads clarify as done, with a warning that names the missing scan file.

**Why this priority**: Without it, every in-flight feature in wfctl and pfms
would be sent back to steps it has already run.

**Independent Test**: Build a feature folder with `## Clarifications`,
`plan.md`, and no scan file, and check that clarify reads done with the warning.

**Acceptance Scenarios**:

1. **Given** `## Clarifications`, a written `plan.md`, and no scan file,
   **When** the user runs `wfctl status`, **Then** clarify reads done and prints
   `no scan file` as a warning.
2. **Given** an analysis report, `delivery.md`, and no scan file, **Then**
   analyze reads done with the warning.
3. **Given** a plan review report with no open BLOCKER, `tasks.md`, and no scan
   file, **Then** the plan review pass reads done with the warning.

---

### User Story 4 - Signing off a plan edit writes to the spec folder (Priority: P2)

A developer makes a small edit to `plan.md` after its review and signs it off
with `wfctl step sign-off plan.plan-review`. The sign-off section lands in
the spec folder's `scans/plan-review.md`. The command prints where it wrote the
section and no commit line, and it doesn't refuse because the branch has no
change to that file.

The sign-off used to reach a person through the scan section in the PR. Now its
reason has to appear in the PR body, the same way a design exception's reason
does, and `wfctl check-body` reports a sign-off reason the body leaves out.

**Why this priority**: The sign-off is the one place wfctl writes a scan file
itself. Left alone, it keeps writing into the code repository.

**Independent Test**: Run the sign-off on a feature with a review report and
check the scan file's location and the command's output.

**Acceptance Scenarios**:

1. **Given** a review report and an edited `plan.md`, **When** the user signs it
   off, **Then** `scans/plan-review.md` in the spec folder gains a
   `## Sign-off` section, and nothing is written under the arch root.
2. **Given** the same, **Then** the output has no `Commit it` line.
3. **Given** the same, and a review section already in the scan file, **Then**
   the plan review pass reads done.
4. **Given** a sign-off on this branch, **When** the user runs
   `wfctl check-body` on a PR body that doesn't carry the sign-off's reason,
   **Then** it reports the missing reason.
5. **Given** a branch with no issue key, **When** the user signs off, **Then**
   the sign-off is written, with a heading that names no issue, since the file
   name no longer needs the key.

---

### User Story 5 - An evaluation scan stays in the code repository (Priority: P3)

A spike or tool evaluation has no spec folder, and its result is the branch's
deliverable. Its scan file stays at `<arch-root>/scans/<issue>-evaluation.md`,
committed and checked with `wfctl arch check`, as before.

**Why this priority**: It is a non-change, but the skill has to say it, since
the rest of the skill now points somewhere else.

**Independent Test**: Read the `writing-a-scan-file` skill and check that its
evaluation instructions still name the arch root, the commit, and the check.

**Acceptance Scenarios**:

1. **Given** the installed `writing-a-scan-file` skill, **When** an agent reads
   its evaluation section, **Then** it names `<arch-root>/scans/<issue>-evaluation.md`,
   the commit, and `wfctl arch check`.

### Edge Cases

- A sign-off section has no `Verdict` line and no coverage table. A scan file
  holding only sign-off sections fails the check, because a sign-off needs a
  review report, and a review that ran had to write its own section first.
- A spec folder with no `scans/` directory reads the same as a missing scan
  file.
- Scan files already committed under `<arch-root>/scans/` are not read by the
  step readers and are not moved. `scans/` stays excluded from the records.
- An `inconclusive` verdict passes the shape check. The step's own artifact
  check is what holds a step that couldn't run.
- The analyze scan's measurement row has no status, and it passes because the
  check needs one row with a status, not every row.

## Clarifications

### Session 2026-11-11

- Q: Does the scan check read the whole file or only its last section? → A: The
  whole file. Basis: a plan review scan ends with a `## Sign-off` section after
  every sign-off, and that section has no `Verdict` line or coverage table, so a
  last-section check would hold every signed-off plan. Decided against the
  last-section check for that reason.
- Q: Does a scan file holding only sign-off sections pass? → A: No. Basis: the
  sign-off refuses without a review report, so a review ran first and its
  wrapper had to write a section. A file with only sign-offs means the review
  skipped its scan. Decided against letting the sign-off event skip the scan
  check, because it would hide that skipped scan.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The clarify, plan review, and analyze instructions MUST write the
  scan file to `scans/<step>.md` in the feature's spec folder, the folder
  `wfctl feature-paths` prints as `FEATURE_DIR`.
- **FR-002**: Those instructions MUST NOT commit the scan file or run
  `wfctl arch check` on it.
- **FR-003**: The evaluation instructions MUST keep
  `<arch-root>/scans/<issue>-evaluation.md`, the commit, and `wfctl arch check`.
- **FR-004**: The clarify, analyze, and plan review readers MUST hold their step
  when the step's own artifact is complete and the scan file is missing, has no
  `Verdict` line with `satisfied`, `unsatisfied`, or `inconclusive`, or has no
  coverage table row whose status starts with `Clear`, `Resolved`, `Deferred`,
  or `Outstanding`. The check reads the whole file, not only its last section.
- **FR-005**: Each held reading MUST display which of the three it is: `no scan
  file`, `scan file has no verdict`, or `scan file has no coverage rows`. A held
  reading MUST NOT carry a blocking reason, so the step stays automatic and an
  unattended run is routed back to the step's own command, the same way the
  plan review pass already holds.
- **FR-006**: When the next step's artifact exists (`plan.md` for clarify,
  `tasks.md` for plan review, `delivery.md` for analyze), or for analyze when
  every task is closed and decompose reads skipped, the reader MUST read
  the step done and carry the same text as a warning, with the fix line
  `run /speckit.clarify`, `run /plan-review`, or `run /speckit.analyze`.
- **FR-007**: `wfctl step sign-off plan.plan-review` MUST write its section to
  `scans/plan-review.md` in the spec folder, MUST NOT check whether the branch
  changes that file, and MUST NOT print a commit line. It no longer refuses a
  branch with no issue key.
- **FR-012**: `wfctl check-body` MUST report each plan sign-off reason recorded
  for this branch that the PR body doesn't carry, and `opening-a-change` MUST
  say to copy it there.
- **FR-013**: When the plan review pass holds only for a scan reason, the
  `/plan-review` wrapper MUST write the scan section from the existing report
  instead of running a new review.
- **FR-015**: When analyze holds only for a scan reason, the `/speckit.analyze`
  wrapper MUST write the scan section from the existing analysis report only if
  that report ends with a `Remediation: settled` line, and MUST run the full
  analysis otherwise. The wrapper rewrites the report on every run that reaches
  step 8 and ends it with that line once every finding is fixed, filed, or
  written down for filing. A report without it was written before remediation
  settled, so a scan from it would mark the step done with findings neither
  fixed nor filed. Each successful filing MUST be written into the report as a
  `Filed as #<n>` line right away, and the full rerun MUST cite an issue those
  lines already name instead of filing its cause again, since a run cut off
  partway through step 8 may have filed some. wfctl's readers don't parse the line,
  and a person who can edit the report can write the scan file directly, so the
  line guards against an interrupted run, not a hand edit.
- **FR-014**: `writing-a-scan-file` MUST state the `- Verdict: <value>` line form
  the reader matches.
- **FR-008**: The step readers MUST NOT read the verdict's value to decide the
  step's state.
- **FR-009**: `scans/` MUST stay on the list of arch-root folders that aren't
  records.
- **FR-010**: The replaced record MUST be marked superseded by the new one.
- **FR-011**: AGENTS.md MUST describe where scan files go, including the
  evaluation exception.

## Key Entities _(include if feature involves data)_

- **Scan file**: One markdown file per review step per feature, with one section
  per run. Each section has a `Verdict` line, a coverage table, and findings.
  Clarify, plan review, and analyze keep theirs in the spec folder. An
  evaluation keeps its file in the code repository.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A feature that runs clarify, plan review, and analyze adds 0 files
  under `<arch-root>/scans/` to its branch, down from 3.
- **SC-002**: A run that follows the pipeline order and writes a step's artifact
  but no scan file leaves that step current in 100% of cases for clarify, plan
  review, and analyze. A run that writes the next step's artifact out of order
  gets only the warning, which is the same trade the clarify reader already
  makes for a plan written before clarify.
- **SC-003**: A feature whose next step's artifact already exists is never sent
  back to an earlier review step because of a missing scan file.
- **SC-004**: `wfctl store specs` saves every scan file in the spec folder.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and
  `python3 .github/scripts/check_imports.py`.
- Unit tests for each reader state in User Stories 2 and 3, and for the sign-off
  in User Story 4.
- Skill tests that the three wrappers and `writing-a-scan-file` name the spec
  folder path and no longer name the commit or `wfctl arch check`, except for
  evaluation.
- `uv run wfctl install-skills`, then one scan walked through the new path: write
  it to the spec folder, check that nothing appears under
  `docs/architecture/scans/`, and run `wfctl status` on it.
- `uv run wfctl doctor` and `uv run wfctl check config`.

## Assumptions

- Pre-specify design context loaded from `design.md` in this folder.
- The spec folder may not be a Git repository, so no check asks git about it.
- wfctl has one user, so the warning-only path for older features is enough
  migration.
