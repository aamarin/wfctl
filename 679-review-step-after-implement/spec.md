# Feature Specification: Review step after implement

**Feature Branch**: `679-review-step-after-implement`  
**Created**: 2026-10-31  
**Status**: Draft  
**Input**: `design.md` in this folder, written by brainstorm. No description was typed.

## Clarifications

### Session 2026-10-31

- Q: Should `wfctl check-body` require the recorded "no spec" reason in the PR body? → A: Yes. It fails the PR when the "Needs a spec?" section doesn't carry the recorded reason, as it does for pass exceptions. Planning changed this to look for the reason anywhere in the body (research R5 and FR-017), since `check-body` names no section for any other exception.
- Q: How does `wfctl status` show a branch with a recorded "no"? → A: The terminal collapses the seven skipped steps into one line, "skipped: no spec", without the reason. The JSON marks each step skipped with "no spec" and carries the reason once, in a top-level `no_spec` field with the file's path.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Status keeps a branch open until it is reviewed (Priority: P1)

An agent finishes implementing a feature and asks `wfctl status` what to do
next. Today it hears "Story complete. Open PR or run /end-session", and the
review panel runs only if someone remembers it. After this change, status names
the review panel as the next command, and shows the branch complete only once
every review group has reviewed the newest commit.

**Why this priority**: This is the gap #679 was opened for. On pfms #919, every
step read done and the panel ran only because the user asked for it.

**Independent Test**: On a branch whose tasks are complete and whose
verification passed, run `wfctl status` before any review, after a complete
review, and after one more commit. The three outputs are the first three states
below.

**Acceptance Scenarios**:

1. **Given** a branch whose implement step is done and which no review group
   has reviewed, **When** the agent runs `wfctl status`, **Then** a `review` row
   follows `implement`, reads in progress, names every group with unreviewed
   commits, and gives `/fanning-out-code-review` as the next command.
2. **Given** every required group has reviewed the current HEAD, **When** the
   agent runs `wfctl status`, **Then** `review` reads done and the story reads
   complete.
3. **Given** a person signed off at the current HEAD and no group reviewed it,
   **When** the agent runs `wfctl status`, **Then** `review` reads done.
4. **Given** a reviewed branch gains one commit, **When** the agent runs
   `wfctl status`, **Then** `implement` reads stale and `wfctl verify` is the
   next command. Once verify passes, `review` reads in progress with
   "1 commit unreviewed" for each group.
5. **Given** any branch state, **When** the agent runs `wfctl status` and then
   `gh pr create`, **Then** the review step reads done exactly when the PR
   guard finds no unreviewed commits. The guard's other checks, such as a
   level-2 record still `proposed`, stay outside the review step, so the
   guard can still refuse a PR after review reads done.

---

### User Story 2 - A change that needs no spec goes straight to implement and review (Priority: P2)

An agent starts a bug fix. Before writing code, it asks the three spec
questions in `design-passes` step 1 and answers no to all three. It records
that with a reason. `wfctl status` then shows the spec steps as skipped and
points the branch at implement and then review. The reason travels to the
review panel through the status JSON and to the reviewer through the PR body.

**Why this priority**: Without it, a branch that needs no spec never reaches
the review step in `wfctl status`, since the pipeline points it at brainstorm
forever.

**Independent Test**: On a scratch issue branch, run `wfctl spec none --reason
"…"`, then `wfctl status`, then `wfctl verify`, then `wfctl status` again.

**Acceptance Scenarios**:

1. **Given** an issue branch with no spec folder, **When** the agent runs
   `wfctl spec none --reason "<a real reason>"`, **Then** wfctl writes the
   reason to the branch's spec folder and prints the path.
2. **Given** a recorded "no" and no spec artifacts, **When** the agent runs
   `wfctl status`, **Then** brainstorm through decompose read skipped, shown as one
   "skipped: no spec" line, `implement` is current, and `wfctl verify` is the next command.
3. **Given** that branch passed verification, **When** the agent runs
   `wfctl status`, **Then** `review` is current, as in User Story 1.
4. **Given** a branch that already has `design.md` or `spec.md`, **When** the
   agent runs `wfctl spec none`, **Then** wfctl refuses and writes nothing.
5. **Given** a placeholder reason such as `<why>` or an empty one, **When** the
   agent runs `wfctl spec none`, **Then** wfctl refuses and writes nothing.

---

### User Story 3 - A changed answer can't leave the branch on the wrong route (Priority: P3)

An agent records "no spec", then finds while coding that the change moves a
boundary, so it runs brainstorm. If it forgets to delete the recorded "no",
status must still run the full pipeline and say which file is stale.

**Why this priority**: The flip path is rarer than either answer, and the spec
artifacts already outrank the claim. The warning only saves a person time.

**Independent Test**: Record "no", then create `design.md`, then run
`wfctl status`.

**Acceptance Scenarios**:

1. **Given** a recorded "no" and a `design.md`, **When** the agent runs
   `wfctl status`, **Then** the pipeline reads as if no "no" were recorded, and
   a warning names the file to delete.

---

### User Story 4 - The agent asks the spec question at session start (Priority: P3)

A session starts on an issue branch that has no spec folder. `/start-session`
has the agent answer the spec question with the three spec questions before its first
action, and record a "no" or continue to brainstorm on a "yes".

**Why this priority**: The skill text for this is already committed on this
branch. What remains is exercising it once against a real `wfctl spec none`.

**Independent Test**: Start a session on a scratch issue branch with no spec
folder and read the step 7 report.

**Acceptance Scenarios**:

1. **Given** an issue branch with no spec folder, **When** `/start-session`
   runs, **Then** its report states the spec answer and which spec question decided it.
2. **Given** a trunk branch, **When** `/start-session` runs, **Then** it asks
   no spec question.

---

### Edge Cases

- The review config on the trunk can't be read. `review` reads in progress with
  the config error as its reason, never done, matching the guard's refusal.
- `review.rounds` is 0, or a group has used all its rounds. `review` reads in
  progress with a reason naming the group, and stops an unattended run with a
  remedy asking the user to sign off, since `review start` refuses the panel
  until they do.
- A group's review command isn't installed on this machine, so `review start`
  leaves that model's reviewers out. The step reads what the guard reads, so it
  follows whatever the completed run recorded.
- The branch has no `origin` remote or no trunk ref. The step reports the same
  error the guard would, as its reason.
- The agent runs `wfctl step complete implement` while `review` is current.
  wfctl accepts it, as it does while `implement` is current.
- A host refuses an outward action after the story is complete, and the agent
  runs `wfctl report-block`. The block holds `implement`, as it does today, not
  `review`.
- The branch is renamed. The review state follows the branch's state folder, as
  the guard's does today, so the step reads what the guard reads.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The pipeline MUST include a `review` step after `implement`, with
  `/fanning-out-code-review` as its command, run automatically in an unattended
  run.
- **FR-002**: `review` MUST read done only when every required review group
  has reviewed the current HEAD, or a person's sign-off covers HEAD.
- **FR-003**: `review` MUST read pending while `implement` is neither done nor
  skipped.
- **FR-004**: The review step and the PR guard MUST compute their answer with
  the same function, reading the same state files. Neither may read git notes
  for this.
- **FR-005**: While `review` is in progress with no blocking reason, its
  status line MUST name each group with unreviewed commits and how many it
  has. It carries no reason, so an unattended run starts the panel.
- **FR-006**: A review config that can't be read, or a missing trunk ref, MUST
  leave `review` in progress with the error as its reason.
- **FR-007**: No command MAY mark the review step done other than
  `wfctl review check` completing a run and `wfctl review sign-off`.
- **FR-008**: `wfctl spec none --reason "…"` MUST write the reason to the
  branch's spec folder, creating the folder when needed, and print the path.
- **FR-009**: `wfctl spec none` MUST refuse an empty or placeholder reason, and
  MUST refuse when `design.md`, `spec.md`, `plan.md` or `tasks.md` exists.
- **FR-010**: With a recorded "no" and none of those four artifacts, the seven
  steps from `brainstorm` to `decompose` MUST read skipped, each annotated "no
  spec". The status payload MUST carry the reason once, in a top-level
  `no_spec` field with the reason and the file's path, and `null` there when no
  "no" is in effect. The terminal view MUST show the seven steps as one line,
  `brainstorm … decompose  –  skipped: no spec`, without the reason.
- **FR-011**: With a recorded "no" and no `tasks.md`, `implement` MUST be
  judged by the verification record alone, and route to `wfctl verify` until it
  passes. Until the branch has a commit the trunk doesn't, `implement` MUST
  read in progress with the reason "no commits on this branch yet", since
  verify passes on a tree the trunk already holds. Review found this case: the
  story read complete the moment the "no" was recorded. A branch whose commits
  have all reached the trunk, such as one whose PR merged, reads that reason
  again, since nothing on disk separates it from a branch that never started.
- **FR-012**: With a recorded "no" and any of the four artifacts present, the
  pipeline MUST ignore the "no", and `wfctl status` MUST warn with the path of
  the file to delete.
- **FR-013**: `wfctl step complete implement` MUST accept `review` as the
  current step.
- **FR-014**: `wfctl report-block` MUST hold `implement` when the pipeline is
  complete, not the last step in the table.
- **FR-015**: The status payload version MUST change from 1.3 to 1.4, because a
  consumer that treated `implement` as the last step reads a different meaning
  under the same keys, and the payload gains the `no_spec` field.
- **FR-016**: README.md's description of the steps and `speckit-orchestrate`'s
  story-complete handling MUST name the review step.
- **FR-017**: When the branch has a recorded "no", `wfctl check-body` MUST fail
  a PR body that doesn't carry the recorded reason, the same way it fails a body
  missing a pass exception's reason. The PR template puts it under "Needs a
  spec?", and `change_sections` already fails that section when it's empty.

## Key Entities _(include if feature involves data)_

- **Review coverage**: For each required review group, the last commit a
  complete run covered, plus the commit a person signed off. Written only by
  `wfctl review check` and `wfctl review sign-off` in the branch's state
  folder. This change reads it and adds nothing to it.
- **No-spec answer**: The branch's statement, with a reason, that its change
  needs no spec. One file in the spec folder's `exceptions/`, written by
  `wfctl spec none`. A "yes" writes no file.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A branch can't read "Story complete" in `wfctl status` while the
  PR guard would refuse its PR for unreviewed commits. Checked on every
  combination in User Story 1.
- **SC-002**: One commit after a complete review, `wfctl status` names a next
  step again, in 100% of runs.
- **SC-003**: A no-spec branch reaches `review` without running brainstorm,
  specify, clarify, plan, tasks, analyze or decompose.
- **SC-004**: `wfctl status` on this branch, once implement is done, stays
  within half a second of its time without the review reading. The review
  reading runs only from that point, so an earlier branch measures nothing.
  The measurement records the branch's commit count, since the cost grows
  with the commits each group has left.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/` and `uv run mypy`.
- Tests that the guard and the review step agree on the same fixtures, with and
  without a sign-off, and one commit after a review.
- Tests for each `wfctl spec none` refusal, the skipped rows, the `implement`
  route on a no-spec branch, and the stale-claim warning.
- The status payload snapshot test, updated for the ninth row and version 1.4.
- `uv run wfctl install-skills`, then exercising `/start-session` on a branch
  with no spec folder.
- The real flow on this branch before the PR: finish implement, see `review`
  next, run the panel, see it done, make one commit, see it pending again.
- `uv run wfctl doctor` green, and `changes/679.addition.md` committed.

## Assumptions

- Pre-specify design context loaded from specs/679-review-step-after-implement/design.md.
- Keeping review reports after the worktree is removed needs no code. The
  reports stay in the state folder, which worktree removal doesn't delete.
- The refactor review group the issue raises stays out of scope. The refactor
  pass stays inside `/speckit.implement`.
- The change keeps wfctl's current flat module layout, since #671 reorganizes
  it later.
