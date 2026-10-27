# Feature Specification: wfctl stops a review group after three rounds

**Feature Branch**: `626-review-round-cap`
**Created**: 2026-10-25
**Status**: Draft
**Input**: User description: "From the brainstorm output at design.md (issue #626: stop the review panel after three rounds on one change)"

## Clarifications

### Session 2026-10-25

- Q: Should `wfctl review start` refuse when the branch's own `wfctl.json` carries an invalid `review.rounds`, even though the cap is read from the trunk? → A: Yes. It refuses like any other invalid `review` setting, and `check config` reports it too.
- Q: Should `review.rounds` accept 0? → A: Yes. With 0, no review run starts, and every change goes through the user's sign-off. The worktree guard doesn't change. A setting that turns the PR check off is out of scope.
- Q: When a branch has already run more rounds than a lowered cap on the trunk allows, what does `review start` do? → A: It refuses, and the refusal names the real count, such as "security has run 4 rounds on this branch, more than the 3 review.rounds allows".

## User Scenarios & Testing _(mandatory)_

### User Story 1 - wfctl refuses a review run past the cap (Priority: P1)

A review round is one run of every review group, in order: security, then
code, then any group the repository adds. Each fix a group commits is a new
commit, so it starts another round, and #294 shows that a second panel finds
new problems in the first panel's fixes. In an unattended run, nobody is there
to stop that loop, and each round launches every reviewer in every group.

Currently, the cap is only an instruction. Step 1 of `opening-a-change` tells
the agent to stop after three rounds and count them itself. wfctl numbers each
group's runs but doesn't count them, and nothing refuses a fourth. When the
conversation is cleared or restarted, the agent's count starts again at zero.

After this change, `wfctl review start <group>` counts the runs the group has
started on the branch. When the group has reached the cap and still has
commits to review that no sign-off covers, `review start` refuses, writes
nothing, and tells the agent to ask the user to run `wfctl review sign-off`.
The sign-off is still the only way past the cap on one branch.

`review start` has four outcomes. The cap is 3 in every example below.

1. Nothing to review. This is unchanged. The cap doesn't apply, since no run
   is written, and the command exits 0:

   ```
   security is up to date at 9f8e7d6
   ```

2. Under the cap. The run starts as before, and the header gains the round, so
   the agent and the user see how close the cap is:

   ```
   security run 002 · round 2 of 3 · 3 commits since a1b2c3d · head 9f8e7d6
   ```

3. At the cap, with a sign-off that covers every commit left to review. No run is needed, so the
   command exits 0 and the agent moves on to the next group and then to the PR:

   ```
   security has run 3 of 3 rounds; the sign-off at 9f8e7d6 covers every commit left to review
   ```

4. At or past the cap, with commits no sign-off covers. The command exits 1
   and writes nothing:

   ```
   ✗ security has run 3 of 3 rounds on this branch, the most review.rounds allows
     Ask the user to run `wfctl review sign-off` in their own terminal.
   ```

   The first line names the real count when the group has run more rounds
   than the cap, which happens after the trunk lowers the cap:

   ```
   ✗ security has run 4 rounds on this branch, more than the 3 review.rounds allows
   ```

   When the cap is 0, the repository has chosen that no review runs, so the
   first line says that instead:

   ```
   ✗ review.rounds is 0, so security doesn't run on this branch
   ```

   The second line is the same in all three cases.

**Why this priority**: This is the feature. Without the count and the refusal,
the cap stays an instruction the agent can lose on a restart.

**Independent Test**: On a test branch in a repository with no `review.rounds`
key, run each group through three rounds, adding a commit between rounds. The
fourth `review start` for the security group exits 1 with outcome 4 and
creates no run folder. After the user signs off in their own terminal, the same
command exits 0 with outcome 3, and the worktree guard allows `gh pr create`.

**Acceptance Scenarios**:

1. **Given** a group that has started 1 run and has new commits, **When** the
   agent runs `review start` for it, **Then** the command writes run 002 and
   its header reads `round 2 of 3`.
2. **Given** a group that has started 3 runs and has new commits that no
   sign-off covers, **When** the agent runs `review start`, **Then** it exits 1
   with outcome 4, and no new run folder exists.
3. **Given** a group that has started 3 runs and has no new commits, **When**
   the agent runs `review start`, **Then** it exits 0 with outcome 1.
4. **Given** a group that has started 3 runs and a sign-off that covers every
   commit in its range, **When** the agent runs `review start`, **Then** it exits 0 with
   outcome 3, and no run is written.
5. **Given** a group that has started 3 runs and a sign-off that covers an
   older commit, with one commit added after it, **When** the agent runs
   `review start`, **Then** it exits 1 with outcome 4.
6. **Given** a group that has started 4 runs, a cap of 3, and new commits,
   **When** the agent runs `review start`, **Then** it exits 1, and the first
   line names 4 rounds and the cap of 3.

---

### User Story 2 - Each group runs once per round (Priority: P1)

Currently, Step 1 of `opening-a-change` tells the security group to run again
over its own fixes before the code group starts. That makes security run more
often than code, so a round has no fixed number of runs, and wfctl can't count
rounds by counting runs.

After this change, each group runs once per round. Security no longer runs
again over its own fixes. The code group reviews those fixes in the same round,
and security reviews them in its next run, which covers every commit since its
last review as before. As a result, a group's run count on the branch is the
branch's round count.

For example, take five commits of implementation on one branch:

1. Round 1: security run 001 reviews the 5 commits, and the agent commits fix
   A. Code run 001 reviews all 6, and the agent commits fixes B and C.
2. Round 2: security run 002 reviews A, B, and C. Code run 002 reviews B and C.
   Both are clean, so the guard allows `gh pr create`.

Under the old instruction, the same change took five runs, since security ran
again over A before code started.

**Why this priority**: User Story 1 counts runs as rounds, and that count is
correct only when every group runs once per round.

**Independent Test**: Read `opening-a-change` Step 1 after `uv run wfctl
install-skills`. It describes one run per group per round, in order, with no
extra security run over the security group's fixes. It says wfctl enforces the
cap, and it no longer says wfctl doesn't count rounds yet.

**Acceptance Scenarios**:

1. **Given** the security group has committed fixes in a round, **When** the
   agent follows `opening-a-change` Step 1, **Then** the code group starts next,
   and security doesn't run again until the next round.
2. **Given** the security group's next run starts, **When** it computes its
   commits, **Then** they include the fixes from the previous round, both its
   own and the code group's.

---

### User Story 3 - A repository sets its own cap on the trunk (Priority: P2)

A repository sets the cap as `review.rounds` in `wfctl.json`, and the default
is 3. wfctl reads the value from the copy of `wfctl.json` on the trunk, not
from the branch under review. The agent writes the branch, and the cap exists
to stop the agent, so a cap read from the branch is one the agent could raise
without asking. Raising the cap is a change merged to the trunk.

The groups and reviewers are still read from the branch, since changing them
doesn't let the agent run more rounds.

Two warnings tell the user when the trunk's value isn't the one they expect:

```
⚠ this branch sets review.rounds to 5, but wfctl reads 3 from origin/main until the change merges
⚠ review.rounds on origin/main isn't a whole number of 0 or more; wfctl uses the default of 3
```

A cap of 0 is valid. It means no review run starts on any branch, so every
change goes through the user's sign-off. The worktree guard still refuses the
PR until then, so 0 doesn't turn off the PR check.

**Why this priority**: The default of 3 covers this repository. A different
number is a repository's choice, and it has to come from somewhere the agent
can't edit.

**Independent Test**: Set `review.rounds` to 5 in the working tree's
`wfctl.json` on a branch, without merging it. `review start` prints the first
warning, and its header reads `of 3`. `wfctl check config` accepts the value.
Set it to -1, and both `check config` and `review start` report it.

**Acceptance Scenarios**:

1. **Given** the trunk's `wfctl.json` has no `review.rounds`, **When** the
   agent runs `review start`, **Then** the cap is 3.
2. **Given** the trunk's `wfctl.json` sets `review.rounds` to 2, **When** a
   group has started 2 runs and has new commits, **Then** `review start`
   refuses with outcome 4, reading `2 of 2 rounds`.
3. **Given** the branch sets `review.rounds` to 5 and the trunk sets nothing,
   **When** the agent runs `review start`, **Then** it prints the first warning
   and uses 3.
4. **Given** the trunk sets `review.rounds` to `"three"` or -1, **When** the
   agent runs `review start`, **Then** it prints the second warning and uses 3,
   and it doesn't refuse.
5. **Given** the working tree sets `review.rounds` to a negative number or a
   value that isn't an integer, **When** the user runs `wfctl check config`,
   **Then** it reports a finding naming `review.rounds`. **When** the agent
   runs `review start`, **Then** it refuses with the same finding, as it does
   for any other invalid `review` setting.
6. **Given** the trunk sets `review.rounds` to 0 and a group has commits to
   review, **When** the agent runs `review start`, **Then** it exits 1 with the
   cap-0 line from User Story 1 and writes no run.

---

### Edge Cases

- A run folder with no `run.json` is left by a `review start` that was
  interrupted. It isn't a run and isn't counted, the same as `latest_run`
  already treats it.
- A run that started and never completed still counts as a round. The cost of
  a run is spent when the reviewers launch, so a loop that starts runs and
  never completes them would never reach the cap otherwise. Starting
  `review start` again at the same head also counts as a round. Reusing an
  incomplete run is out of scope.
- A sign-off doesn't reset the count. A commit added after the sign-off is
  unreviewed again, and once the cap is reached it needs another sign-off.
- Rounds count across the whole branch, before and after the PR opens. A fix
  for a review comment on an open PR uses a round like any other fix.
- The trunk has no `wfctl.json`, or the file has no `review` key. wfctl uses
  the default of 3 and prints no warning.
- The trunk's `wfctl.json` isn't valid JSON. wfctl uses the default with a
  `⚠` line saying it can't read the trunk's `wfctl.json`, for the same reason
  as an invalid value: a refusal would block every review on every branch
  until someone fixes the trunk.
- `origin/<trunk>` is behind the trunk on GitHub. wfctl reads whatever the
  local `origin/<trunk>` ref holds, the same ref the commit range is measured
  from. A cap raised on GitHub takes effect after the next fetch.
- No trunk can be found. `review start` already refuses in that case, since
  it can't compute the commit range, and the cap adds nothing to it.
- A custom group runs once per round like security and code, and the cap
  applies to each group separately with the same number.
- The trunk lowers the cap below the number of rounds a branch has already
  run. The next `review start` with commits to review refuses and names the
  real count. A branch doesn't keep the cap it started under.
- The cap is 0. Every `review start` with commits to review refuses, and a
  group with nothing to review still prints outcome 1.
- The branch's own `review.rounds` is invalid. `review start` refuses with the
  `check config` finding, even though the cap comes from the trunk. The agent
  gains nothing from an invalid value, and every other invalid `review`
  setting is refused the same way.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: `wfctl review start <group>` MUST count the run folders for the
  group on the branch that hold a `run.json`. The count MUST be derived on
  every call and MUST NOT be stored (`session-state-is-re-derived.md`).
- **FR-002**: `review start` MUST decide in this order. First the commit range:
  a group with no commits to review prints outcome 1, whatever its count. Then
  the count against the cap: under the cap, it starts the run. At the cap, it
  checks the sign-off: a sign-off that covers every commit in the range gives
  outcome 3, and otherwise outcome 4.
- **FR-003**: At outcome 4, `review start` MUST exit 1, MUST write no run
  folder and no `run.json`, and MUST print the lines in User Story 1 naming
  the group, the count, the cap, `review.rounds`, and `wfctl review sign-off`.
  The first line MUST name the real count when it is above the cap, and MUST
  use the cap-0 wording when the cap is 0.
- **FR-004**: At outcome 3, `review start` MUST exit 0 and write no run. The
  sign-off has to cover every commit in the group's range, the same check
  `unreviewed()` makes. A sign-off covers a commit when the commit is the
  signed-off commit or one of its ancestors. A clean merge of the trunk after
  the sign-off isn't in the range, so it doesn't undo outcome 3.
- **FR-005**: The header of a run that starts MUST include `round N of M`,
  where N is the new run's position in the count and M is the cap, between the
  run number and the commit count.
- **FR-006**: `wfctl.json` MUST accept `review.rounds`, an integer of 0 or
  more. `wfctl check config` MUST report a finding for any other value,
  including a negative number, a float, a string, and a boolean. `review
  start` MUST refuse on an invalid value in the working tree, the same way it
  refuses on any other invalid `review` setting.
- **FR-007**: `review start` MUST read `review.rounds` from `wfctl.json` on the
  first ref `trunk_refs` returns, which is `origin/<trunk>` when it exists. It
  MUST NOT read the cap from the working tree.
- **FR-008**: When the trunk has no `wfctl.json` or no `review.rounds`, the cap
  MUST be 3, with no warning.
- **FR-009**: When the trunk's `review.rounds` is invalid, `review start` MUST
  print the second warning in User Story 3 and use 3. When the trunk's
  `wfctl.json` can't be parsed, it MUST print a `⚠` line naming the trunk ref
  and use 3. In neither case may it refuse.
- **FR-010**: When the working tree's `review.rounds` is valid and differs from
  the cap read from the trunk, `review start` MUST print the first warning in
  User Story 3, naming both values and the trunk ref.
- **FR-011**: The groups and reviewers MUST still be read from the working
  tree's `wfctl.json`, as they are today.
- **FR-012**: The worktree guard's code MUST NOT change. It already refuses
  `gh pr create` and `gh pr merge` while a group has unreviewed commits that no
  sign-off covers, and it reads the trunk through `trunk_refs`, so FR-017
  reaches it without a change.
- **FR-013**: `opening-a-change` Step 1 MUST describe one run per group per
  round, in order, and MUST NOT tell the security group to run again over its
  own fixes. It MUST say that wfctl enforces the cap and that the agent stops
  and asks the user to sign off when `review start` refuses. The sentence
  saying wfctl doesn't count rounds yet (#626) MUST be removed, and the
  guard-refusal bullet that repeats the three-round instruction MUST match.
- **FR-014**: The example header in `fanning-out-code-review` MUST show the
  round, matching FR-005.
- **FR-015**: `AGENTS.md` "Declaring reviewers" MUST describe `review.rounds`:
  what it caps, its default, and that wfctl reads it from the trunk.
- **FR-016**: The branch MUST commit `changes/626.addition.md` for the new
  `review.rounds` key, and `changes/626.change.md` for the round order and
  the trunk read from the default branch, including the upgrade step for a
  repository whose trunk isn't its default branch.
- **FR-017**: The readers that decide which commits a review covers MUST take
  the trunk from the `trunk` key in `wfctl.json` on the repository's default
  branch, the one `origin/HEAD` names, and not from the working tree. With no
  key there, the default branch is the trunk. Those readers are `review
  start`'s commit range and cap, `review sign-off`, and the PR check's list of
  unreviewed commits. The guard's own checks on where a command may run keep
  reading the working tree, since they can't hide a commit. Without this, an agent could set
  `trunk` to a branch it pushed, either with a higher `review.rounds` or
  carrying its own unreviewed commits, which the PR check would then leave
  out. When the working tree names a different trunk that the clone has,
  `review start` MUST print a `⚠` warning and go on, and MUST NOT refuse. The
  one exception is a working-tree `trunk` that names the branch under review.
  The guard refuses that branch's PR, so `review start` MUST refuse it too,
  with today's same-name message. When
  it names a branch the clone doesn't have, `review start` MUST refuse with
  `NoTrunk`, as it does today, since the guard refuses the same branch. With no `origin/HEAD`, or
  a clone that doesn't fetch every branch, wfctl MUST fall back to today's
  resolution. `research.md` R11 gives every case.

## Key Entities _(include if feature involves data)_

- **Run record**: The `run.json` that `review start` writes in
  `reviews/<group>/runs/<NNN>/` under the branch's state directory. It already
  exists. This feature counts these records and adds no field to them.
- **Sign-off**: The `reviews/sign-off.json` file that `wfctl review sign-off`
  writes, naming the commit the user signed off through. It already exists, and
  this feature only reads it.
- **Round cap**: The `review.rounds` value in the trunk's `wfctl.json`, or 3.
  It is read on every call to `review start` and never stored.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: With the default cap, no group can start a fourth run on a branch
  unless the user has signed off. A test branch taken through three rounds
  gets exit 1 on the fourth `review start` for every group, and no fourth run
  folder exists.
- **SC-002**: A conversation that is cleared or restarted partway through
  review sees the same count as before the restart, since the count comes from
  run records on disk.
- **SC-003**: Editing `review.rounds` on the branch changes the cap for 0 runs
  until the change merges to the trunk.
- **SC-004**: In the worked example in User Story 2, the change takes 4 runs
  instead of 5.
- **SC-005**: An invalid `review.rounds` on the trunk blocks 0 reviews. Every
  branch keeps running with the default and sees a warning.

## Validation Strategy _(mandatory)_

1. `uv run pytest -q`, with new tests for:
   1. Each of the four outcomes in FR-002, including the order (an up-to-date
      group at the cap prints outcome 1, not outcome 4).
   2. A run folder with no `run.json` isn't counted.
   3. Outcome 4 writes no run folder.
   4. A sign-off covering an older commit doesn't satisfy outcome 3 once a
      commit is added after it.
   5. The cap read from the trunk ref, with the branch's value ignored, and
      both warnings.
   6. `check config` findings for each invalid `review.rounds` value in
      FR-006, 0 accepted, and `review start` refusing on an invalid value in
      the working tree.
   7. The refusal wording for a count above the cap and for a cap of 0.
   8. The header carries `round N of M`.
   9. FR-017: a branch that names another trunk still measures its range and
      reads its cap from the default branch's trunk, with the warning, and
      `review sign-off` works there. Each case in `research.md` R11 has a
      test.
2. `uv run ruff check wfctl/ tests/` and `uv run mypy`.
3. `uv run wfctl check config` on this repository.
4. `uv run wfctl install-skills`, then read `opening-a-change` Step 1 and the
   `fanning-out-code-review` header as installed.
5. End to end: take a test branch through three rounds, confirm the fourth
   `review start` refuses, then sign off in a terminal and confirm the guard
   allows `gh pr create`.
6. `uv run wfctl verify`, which also checks the release note.

## Assumptions

- Pre-specify design context loaded from `design.md` in this feature's spec
  directory.
- `git show <ref>:wfctl.json` works from every worktree, including one whose
  `origin/main` is stale. The end-to-end check in the Validation Strategy tests
  this.
- The panel skill reads the `review start` header as prose, so adding the round
  breaks no parser. The `_say` docstring in `wfctl/cli.py` says the panel skill
  parses these lines, so the plan checks what `fanning-out-code-review` reads
  from the header before changing it.
- No consumer repository relies on security running again over its own fixes.
  wfctl has one user while this holds.
- The decisions behind this spec are the records `review-round-count.md` and
  `review-round-cap.md`, which the user accepted on 2026-10-25, after clarify.

## Out of Scope

- A command that grants more rounds on one branch, such as `wfctl review
  extend`. Sign-off already lets a change through, and a repository that wants
  more rounds raises the cap.
- A per-group cap. Every group runs once per round, so one number covers them
  all.
- Making the 20-reviewer limit configurable.
- Reusing an incomplete run when `review start` runs again at the same head.
- Resetting the count after a sign-off.
- Showing the round count in `wfctl status`.
