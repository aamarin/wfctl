# Feature Specification: A sign-off opens a new window of review rounds

**Feature Branch**: `725-sign-off-round-window`  
**Created**: 2026-11-05  
**Status**: Draft  
**Input**: `design.md` in this folder, from the #725 brainstorm

## Clarifications

### Session 2026-11-05

- Q: After a sign-off, how do `review start`'s header and refusal describe the count? → A: They say the count is since the sign-off and name its commit, such as "round 1 of 3 since the sign-off at abc1234" and "security has run 3 of 3 rounds since the sign-off at abc1234". With no sign-off, the wording stays as it is today. Basis: the user asked for the run to go to completion without pauses, so this takes the recommended option; the count dropping from 3 to 0 needs a reason on screen, and the sign-off is that reason.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Fixes after a sign-off get reviewed (Priority: P1)

A branch has used every review round the cap allows. The agent adds a commit, and `wfctl review start` refuses it. The user signs off in their own terminal. The agent then runs the panel again, and each review group reviews the new commit. The next fixes each get a round too, up to the cap's number of rounds after the sign-off. After that, `review start` refuses again and asks for another sign-off.

**Why this priority**: Today every commit past the cap needs its own sign-off, and no reviewer sees it. This story is the whole point of #725.

**Independent Test**: With a cap of 3, start three runs for a group, sign off, then show `review start` writes three more runs and refuses the fourth.

**Acceptance Scenarios**:

1. **Given** a group has started 3 of 3 rounds and a new commit B is unreviewed, **When** the user signs off at B and the agent runs `review start` for the group, **Then** wfctl writes a run that reviews B, and the header reads round 1 of 3.
2. **Given** a sign-off when the group had started 3 rounds, **When** the agent starts rounds for commits C and D, **Then** both runs are written, and the header reads round 2 of 3 and round 3 of 3.
3. **Given** the group has started 3 rounds since the sign-off, **When** commit E is added and the agent runs `review start`, **Then** wfctl refuses and tells the agent to ask the user to sign off.
4. **Given** a group has never reached the cap and no one has signed off, **When** the agent runs `review start`, **Then** wfctl counts every round on the branch, as it does today.

---

### User Story 2 - A sign-off still lets the change merge (Priority: P1)

The user signs off to merge right away, such as on a release PR that gets no panel. The sign-off still covers every commit it lists, so the worktree guard and the CI `review` check pass without another round.

**Why this priority**: If the sign-off stopped covering its commits, the release flow would break.

**Independent Test**: Sign off at HEAD, then show the guard's unreviewed-commit check reports nothing pending.

**Acceptance Scenarios**:

1. **Given** unreviewed commits on a branch, **When** the user signs off at HEAD, **Then** no group has unreviewed commits at HEAD, and the guard allows `gh pr create`.

---

### User Story 3 - Status and the refusal agree (Priority: P2)

`wfctl status` already reports a group as capped when `review start` would refuse it. After a sign-off, status counts the window the same way `review start` does.

**Why this priority**: If the screen says a group can run and the refusal says it can't, the user loses trust in both. #665 builds a status row on this count.

**Independent Test**: After a sign-off, step a group from 0 to 3 rounds and show status reports capped only when `review start` would refuse.

**Acceptance Scenarios**:

1. **Given** a sign-off and 2 rounds started since, with a cap of 3, **When** status reads the branch, **Then** the group isn't capped.
2. **Given** a sign-off and 3 rounds started since, with a cap of 3, and an unreviewed commit, **When** status reads the branch, **Then** the group is capped.

### Edge Cases

- A sign-off file written by wfctl 0.26.0 or earlier has no round counts. wfctl treats it as recording no rounds, so the window covers the whole branch, and a branch already at the cap stays refused until the user signs off again.
- Two sign-offs with no rounds in between leave the same window. Windows don't stack.
- A branch renamed after a sign-off has no sign-off in its new state folder, while the round tally is kept by issue. Its window closes, and the user signs off again.
- A group that had never started a round at the sign-off counts its window from 0.
- A cap of 0 still means no group runs, with or without a sign-off.
- A trunk cap changed after the sign-off changes the window size. The window is the cap `review start` reads when it runs.
- `wfctl review sign-off` with nothing unreviewed still says no sign-off is needed and writes nothing, so a window can't be opened early.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: A sign-off MUST record, for each review group with runs or a round tally on disk, the number of rounds that group had started at the time of the sign-off. The count MUST be the one `review start` uses: the larger of the branch's run records and the issue's round tally.
- **FR-002**: `review start` MUST count a group's rounds as the rounds started since the latest sign-off: the current count minus the count the sign-off recorded for that group, or the current count when there's no sign-off or the sign-off recorded none for that group.
- **FR-003**: `review start` MUST refuse a run when that window count is at or above the cap, unless the sign-off covers every commit left, as today.
- **FR-004**: `wfctl status` MUST decide whether a group is capped with the same window count as `review start`, through one shared function.
- **FR-005**: The sign-off MUST still cover every commit it lists, for the guard, CI, and the review step.
- **FR-006**: The sign-off MUST NOT record the cap. The window size MUST be the cap `review start` reads when it runs.
- **FR-007**: A sign-off file without round counts MUST still be read, and it counts as recording no rounds.
- **FR-008**: `review start`'s header and refusal MUST report the count in the window. After a sign-off, both say the count is since the sign-off and name its short commit, such as "round 1 of 3 since the sign-off at abc1234". With no sign-off, or a sign-off file without round counts, the wording is unchanged, since that window covers the whole branch (FR-007).
- **FR-009**: `opening-a-change` MUST say that a sign-off gives each group the cap's number of rounds again.
- **FR-010**: The branch MUST commit a release note, `changes/725.change.md`.

## Key Entities _(include if feature involves data)_

- **Sign-off**: one per branch, in the branch's state folder. Holds the signed-off commit and the time, and now each group's round count when it was given.
- **Round tally**: one per issue, one empty folder per round started. Unchanged.
- **Run record**: one per run, in the branch's state folder. Unchanged.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: In the issue's example, four PR comments fixed after round 3, the user signs off 2 times instead of 4, and all 4 fixes get a review instead of none.
- **SC-002**: At every round count from 0 to the cap after a sign-off, status and `review start` agree on whether the group is capped.
- **SC-003**: A branch with a sign-off written by wfctl 0.26.0 behaves the same as it does today until the user signs off again.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, with new tests for each acceptance scenario and edge case above.
- `uv run ruff check wfctl/ tests/` and `uv run mypy`.
- `python3 .github/scripts/check_imports.py`.
- `uv run wfctl doctor`, after `uv run wfctl install-skills` for the `opening-a-change` edit.
- The issue's example, walked below the sign-off command: drive the sign-off and `start` functions on a scratch repository with a cap of 3, and confirm three rounds run after the sign-off and the fourth is refused.

## Assumptions

- Pre-specify design context loaded from `design.md` in this spec folder.
- Only `review start` and the status check decide whether a group is at the cap.
- #665's status row isn't part of this change. It reads the shared count once it lands.
- #723 isn't part of this change. The window follows whichever cap `review start` reads after #723.
