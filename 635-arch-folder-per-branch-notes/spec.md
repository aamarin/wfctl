# Feature Specification: Design exceptions move to the spec folder

**Feature Branch**: `635-arch-folder-per-branch-notes`
**Created**: 2026-10-25
**Status**: Draft
**Input**: Pre-specify design context loaded from `design.md` in this feature's spec folder. Issue #635.

A design exception is a branch's statement, with a reason, that a design step doesn't apply to it. There are two kinds today. A boundary exception says the branch drew no new boundary, and `wfctl arch none` records it. A pass exception says a pass the repo declared doesn't apply, and `wfctl step none` records it. Both are currently written into the architecture folder, which should describe the system and not individual branches. This feature moves them into the branch's spec folder for the pipeline, and into the PR body for the reviewer.

## Clarifications

### Session 2026-10-25

- Q: When a session ends, the summary's "Boundary" line only counts files under the architecture folder. Should it also count a boundary exception in the spec folder? → A: Yes. The summary counts the boundary question answered under the same rule as the brainstorm gate, so the two never disagree (FR-014).

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Record a boundary exception without touching the architecture folder (Priority: P1)

An agent on a branch that draws no new boundary runs `wfctl arch none --reason "…"`. The exception is saved in the branch's spec folder, and the brainstorm step counts the boundary question as answered. The architecture folder doesn't change.

**Why this priority**: This is the most common exception, with 15 of the 20 files in the architecture folder today. It's also the one the brainstorm gate waits on, so the pipeline can't move without it.

**Independent Test**: On a branch with `design.md` and no architecture record, run `arch none` with a reason. Check that `wfctl status` shows brainstorm's architecture sub-step done, that the exception file is in the spec folder, and that `git status` shows nothing new under the architecture folder.

**Acceptance Scenarios**:

1. **Given** a branch with `design.md` and no architecture record, **When** the agent runs `arch none` with a reason, **Then** the command prints the recorded reason and a line telling the user to put it in the PR body, and brainstorm's architecture sub-step reads done.
2. **Given** a branch with no spec folder yet, **When** the agent runs `arch none` with a reason, **Then** the spec folder is created, the exception is saved there, and brainstorm is still the current step.
3. **Given** a branch that already has a boundary exception, **When** the agent runs `arch none` again with a new reason, **Then** the new reason replaces the old one.
4. **Given** any branch, **When** the agent runs `arch none` with an empty reason or a `<why>` placeholder, **Then** the command refuses, as it does today.

---

### User Story 2 - Record pass exceptions beside the boundary exception (Priority: P2)

An agent runs `wfctl step none <step>.<pass> --reason "…"` for a pass the repo declared. The exception is saved in the same spec folder location as the boundary exception, one file per pass, and the pipeline reads that pass as skipped.

**Why this priority**: Pass exceptions are less common, with 5 files today, but they share the same problem and the same fix. Leaving them in the architecture folder would keep it growing.

**Independent Test**: Run `step none` on two different passes and `arch none` once. Check that the pipeline reports exactly those two passes as skipped, with their reasons, and doesn't report the boundary exception as a pass.

**Acceptance Scenarios**:

1. **Given** a repo that declares two passes, **When** the agent records an exception for each, **Then** both are saved and both read skipped, and neither replaces the other.
2. **Given** a branch with a boundary exception and one pass exception, **When** the pipeline lists skipped passes, **Then** it lists only the pass exception.
3. **Given** a pass name the repo doesn't declare, **When** the agent runs `step none` on it, **Then** the command refuses, as it does today.

---

### User Story 3 - The reviewer reads exceptions in the PR body (Priority: P3)

The user opening a PR answers a "Moves a boundary?" section, yes or no with a reason, and lists any pass exceptions under it. In a repo that lists the section under `change_sections`, `wfctl check-body` reports a PR body that leaves it missing or unanswered.

**Why this priority**: The spec folder isn't part of the PR, so without this section the reviewer never sees the exception. It ranks below stories 1 and 2 because those can ship and work on their own, while this one depends on the repo opting in.

**Independent Test**: In this repo, run `check-body` against a PR body with no "Moves a boundary?" section, then against one that answers it with a reason.

**Acceptance Scenarios**:

1. **Given** this repo's `wfctl.json` lists "Moves a boundary?", **When** `check-body` reads a body without that section, **Then** it reports the section missing.
2. **Given** the same repo, **When** `check-body` reads a body that answers "No. Copy fix in one help string; nothing moves.", **Then** it reports nothing for that section.
3. **Given** a repo that doesn't list the section, **When** `check-body` reads any body, **Then** it reports nothing about the section.
4. **Given** this repo, **When** `wfctl check config` runs, **Then** it finds the heading in `.github/pull_request_template.md`.

---

### User Story 4 - The architecture folder holds no exceptions (Priority: P4)

The 15 declarations in the architecture folder are deleted, and the 5 step claims move into their branches' spec folders. A declaration written by an older wfctl no longer satisfies the brainstorm gate, so the folder doesn't start filling up again.

**Why this priority**: The cleanup is the visible result of the feature, but it only makes sense once stories 1 and 2 stop new files from arriving.

**Independent Test**: List the architecture folder after the change. Then, on a scratch branch with `design.md`, add a file under `declarations/` and check that brainstorm's architecture sub-step still reads unanswered.

**Acceptance Scenarios**:

1. **Given** the change has merged, **When** a reader lists the architecture folder, **Then** there is no `declarations/` or `step-claims/` content.
2. **Given** a branch with `design.md` and only an old-style declaration file, **When** the pipeline reads brainstorm, **Then** the boundary question is unanswered.

---

### User Story 5 - A wrong boundary answer doesn't reach the reviewer (Priority: P2)

The boundary answer is written early, and the branch can change after that. When the PR body's copy of an exception doesn't match the spec folder's copy, `check-body` reports it. When a branch adds an architecture record after its own "no new boundary", or adds a record nobody has accepted, the worktree guard holds the PR. In an attended session, the agent stops when it writes a record on a branch that said "no new boundary", and the user accepts or rejects the record before the agent builds on it.

**Why this priority**: Moving the answer out of the diff splits it into two copies, and the gate reads only the early one. Without these checks, a PR can open with an answer the branch no longer matches, and an unattended run can merge a boundary nobody approved.

**Independent Test**: On a branch with a boundary exception, run `check-body` against a body without the reason. Then add a proposed level-2 record, commit it, and run `gh pr create` through the guard.

**Acceptance Scenarios**:

1. **Given** a branch with a boundary exception, **When** `check-body` reads a body that doesn't contain the exception's reason, **Then** it reports the missing reason, in any repo, whether or not it lists "Moves a boundary?".
2. **Given** a branch with a pass exception, **When** `check-body` reads a body that contains the reason rewrapped across two lines, **Then** it reports nothing for that exception.
3. **Given** a branch whose own spec folder holds a boundary exception and which touches a level-2 record, **When** the agent runs `gh pr create`, **Then** the guard refuses, names the record, and prints the command that deletes the exception.
4. **Given** a sub-issue that inherits the epic's boundary exception and touches a level-2 record, **When** the record is accepted and the agent runs `gh pr create`, **Then** the guard doesn't refuse for the exception.
5. **Given** a branch that touches a `proposed` level-2 record, **When** the agent runs `gh pr create` or `gh pr merge`, **Then** the guard refuses and names the record.
6. **Given** the same branch from the `main` checkout, **When** a person runs `gh pr merge` on it there, **Then** the guard reads the record's status at the PR's head commit, not from the `main` working tree.

---

### Edge Cases

- A branch name containing `/` resolves to the same spec folder for the writer and the readers, as the current code does with `Path(branch).name`.
- A pass named `boundary` can't be confused with the boundary exception, since a pass exception's file name always includes its step.
- Once `spec.md` exists, the brainstorm gate is done, whatever the exceptions say. That escape is unchanged.
- The spec folder is stored on `specs-trunk` with the rest of the branch's specs, so the exception outlives the worktree.
- An epic's sub-issues share the epic's spec folder, so they share its exceptions too. A sub-issue that adds an architecture record keeps sharing it, and the record answers the boundary question for that sub-issue. A sub-issue that needs different pass exceptions or a plan of its own gets its own spec folder, named after its branch. wfctl checks for that folder first, so the sub-issue stops sharing and starts with no exceptions. For example, #701 and #702 both use #700's boundary exception. #702 can add a record and still share the folder. It stops sharing only once it gets a `702-record-reader/` folder of its own.
- The test fixture in `_contract.py` that writes a step claim under the architecture folder writes it in the spec folder instead.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: `wfctl arch none` MUST save the boundary exception in the branch's spec folder, and MUST NOT write under the architecture folder.
- **FR-002**: `wfctl step none` MUST save each pass exception in the same spec folder location as the boundary exception, one file per pass.
- **FR-003**: Both commands MUST create the spec folder when it doesn't exist.
- **FR-004**: Both commands MUST keep their current refusals for an empty reason, a `<why>` placeholder, and, for `step none`, an undeclared pass.
- **FR-005**: Both commands MUST drop the refusal for a file that isn't part of the PR diff, and MUST end a successful run with a line telling the user to put the reason in the PR body.
- **FR-006**: The brainstorm gate MUST count the boundary question answered when the branch touches an architecture record or has a boundary exception in its spec folder.
- **FR-007**: The brainstorm gate MUST NOT count a file under the architecture folder's `declarations/` as an answer.
- **FR-008**: The pipeline MUST read each pass exception from the spec folder and report that pass as skipped, and MUST NOT report the boundary exception as a pass.
- **FR-009**: One module MUST own the location and file format of design exceptions. The commands and the readers MUST call it rather than building paths or parsing files themselves (`docs/architecture/design/design-exceptions-module.md`).
- **FR-010**: This repo's `wfctl.json` MUST list "Moves a boundary?" under `change_sections`, and `.github/pull_request_template.md` MUST carry that heading.
- **FR-011**: wfctl MUST NOT name the "Moves a boundary?" heading in its own code.
- **FR-012**: The 15 files under `declarations/` MUST be deleted. The 5 files under `step-claims/` MUST move to `exceptions/` in their branch's spec folder, rewritten in the new file format, so the record of each skipped walkthrough is kept. wfctl's code MUST NOT name `step-claims/` after the change.
- **FR-013**: Skill and command text that tells an agent where exceptions are written MUST name the spec folder. `opening-a-change` MUST tell the agent to copy the branch's design exceptions from the spec folder into the PR body, without naming a section, since that skill carries no section list of its own. The PR template's comment under "Moves a boundary?" says what goes there.
- **FR-014**: The "Boundary" line `wfctl end` writes into the session summary MUST read "answered" when the branch touches an architecture record or has a boundary exception in its spec folder, the same rule as FR-006. It reads "unknown" only when git can't tell whether a record was touched and the branch has no boundary exception.
- **FR-015**: `wfctl check-body` MUST report each design exception in the branch's spec folder whose reason doesn't appear in the PR body, ignoring differences in whitespace. It MUST NOT name a section to do so. A boundary exception inherited from an epic's folder MUST NOT be reported when the branch touches a level-2 record, since the record answers the boundary question for that sub-issue.
- **FR-016**: The worktree guard MUST refuse `gh pr create` and `gh pr merge` when the branch's own spec folder holds a boundary exception and the branch touches a level-2 architecture record. The refusal MUST name the record and print the command that deletes the exception. An exception inherited from an epic's folder MUST NOT trigger it.
- **FR-017**: The worktree guard MUST refuse `gh pr create` and `gh pr merge` while any level-2 record the branch touches is unaccepted, under the same rule as the "architecture accepted" fact.
- **FR-018**: The guard MUST read the records for FR-016 and FR-017 at the commit the command acts on, and MUST refuse when it can't read them.
- **FR-019**: `architecture-decisions` MUST tell the agent, on a branch with a boundary exception and with `auto_approve` false, to stop after writing a record as `proposed` and wait for the user to accept or reject it. With `auto_approve` true, it MUST tell the agent to complete the record's `Considered` section and continue.

## Key Entities _(include if feature involves data)_

- **Boundary exception**: One per spec folder, which is one per branch except for an epic's sub-issues that share the epic's folder. Holds the reason the branch drew no new boundary. A second one replaces the first.
- **Old step claim**: A file under `step-claims/<branch>/` written by wfctl 0.23.0 or earlier. After the release, nothing reads that folder. A step claim written by an older wfctl between merge and upgrade isn't read and could release the brainstorm gate. That's accepted while wfctl has one user, and the release note says to upgrade before writing an exception.
- **Pass exception**: One per spec folder and pass. Holds the reason a declared pass doesn't apply. Identified by its step and pass name.
- **"Moves a boundary?" PR section**: The reviewer's copy of both kinds, answered yes or no with a reason.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: After merge, the architecture folder holds 0 design exception files, down from 20.
- **SC-002**: A branch that records a boundary exception and any number of pass exceptions adds 0 files to the architecture folder.
- **SC-003**: Every scenario that releases or holds the brainstorm gate today gives the same result after the change, with one exception: the old-file case in story 4 now holds the gate. A branch with a boundary exception is released when git can't tell whether a record was touched, the same as today, since the gate already releases any branch when git can't answer. The difference is that the gate now reads the exception before it asks git.
- **SC-004**: In wfctl's code, changing where exceptions are stored, or their file format, is one edit in one module. The skill text and the PR template comment that name the folder are listed in the plan, since a move has to update them too.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`, all green.
- Tests for each acceptance scenario in stories 1, 2, and 4, run through the CLI.
- A `check-body` test for story 3's scenarios, and `uv run wfctl check config` green after editing `wfctl.json`.
- `uv run wfctl install-skills --agent claude`, then read the updated skill text in the installed tree.
- By hand: run `arch none` and `step none` on a scratch branch, and confirm `wfctl status` and the architecture folder match stories 1 and 2.

## Assumptions

- Pre-specify design context loaded from `design.md` in this feature's spec folder.
- `check-body` runs through the `opening-a-change` skill, not CI or the worktree guard, so the reviewer's copy depends on that skill running. `design-exceptions-live-with-specs.md` accepts that while wfctl has one user. The worktree guard enforces FR-016 and FR-017, since those decide whether a boundary nobody approved can merge.
- #382's short track reads the same boundary exception, and gets a comment saying so instead of being designed here.
- #648 adds a third exception kind to the same location later. It isn't part of this feature.
