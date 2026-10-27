# Feature Specification: A required CI check fails a PR while a review group has unreviewed commits

**Feature Branch**: `627-ci-review-check`
**Created**: 2026-10-24
**Status**: Draft
**Input**: User description: "From the brainstorm output at design.md (issue #627: a required CI check can't enforce the final review, because the review record stays on the local machine)"

## Clarifications

### Session 2026-10-24

- Q: A release PR's only commit is the version bump, and no review group runs on it. How does a release PR get past the review check? → A: The maintainer runs `wfctl review sign-off` on the release commit by hand, in their own terminal. `release.py` doesn't sign off itself, because an agent can run the script, and a scripted sign-off would let it cut and merge a release with nobody involved. The guard refuses the sign-off command from an agent, so a release still needs a person.
- Q: Pushing the notes ref doesn't start a CI run, so a `review` job that failed before the notes arrived stays red. How does it turn green? → A: After wfctl sends the notes, it reruns the failed `review` job on the branch's open PR. This applies to `review check`, `sign-off`, and `wfctl store reviews`. A rerun changes nothing else, since the check still decides from the notes.

### Session 2026-10-25 (plan)

- Q: The CI job as designed runs the PR's own wfctl and the PR's own copy of the workflow, so a PR that breaks the check code, even by accident, passes its own check. Which wfctl does the job run? → A: `main`'s. GitHub runs `main`'s copy of the job and `main`'s wfctl, and reads the PR's commits, notes, and `wfctl.json` only as data. This feature's own PR is the one exception, since `main` doesn't have the check until it merges, so that PR relies on the local guard alone.

### Session 2026-10-25 (plan walkthrough)

- Q: CI reads the review groups from the PR's own `wfctl.json`, so a PR that removes a group skips that group's check on the same PR. Which list should CI require? → A: The groups `main` lists, plus any group the PR adds. A group removed in the PR still runs until the removal reaches `main`, and adding a group means it should run, so the PR that adds it needs its review.
- Q: wfctl pushes the notes, but the rerun of the failed check fails, for example when `gh` times out. What gets the check green? → A: The user reruns the check by hand. wfctl doesn't try to make up for a GitHub error, and its warning says to rerun the check rather than pointing at `wfctl store reviews`, which has nothing left to send.

### Session 2026-10-25 (plan review)

- Q: The local commands read the groups from the working tree, so on a PR that removes a group, the guard lets the PR open and CI then fails, and `wfctl review start` refuses to run the removed group. Should the local check use the same group list as CI? → A: Yes. The guard, the sign-off, and `wfctl check reviews` all require `main`'s groups plus the groups the PR's committed `wfctl.json` adds. `wfctl review start` can also run a group that's only in the uncommitted `wfctl.json`, so a user can try a new group before it's required. The check requires that group once the edit is committed.
- Q: The trunk comes from the `trunk` key in the PR's own `wfctl.json` before `origin/HEAD`, so a PR that names its own branch as trunk gets an empty range and passes with no review. Which branch should CI measure against? → A: The branch the PR targets, as GitHub reports it. The PR's files can't change it, and it's right for a repository that merges into `develop` and for a PR stacked on another PR's branch. A PR that targets an unusual branch gets nothing past the check, since the `main` ruleset only gates PRs into `main`.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A PR with unreviewed commits can't merge (Priority: P1)

A review group is a panel of agent reviewers with its own review skill, such
as `security` or `code`. Before a PR opens or merges, every group has to have
reviewed every commit on it, unless a human reviewer signed off on those
commits.

Currently, only the worktree guard enforces this. If a review group has
unreviewed commits, the guard blocks `gh pr create` and `gh pr merge` only
when the command exactly matches its rules. #622 records 14 ways around it,
such as a git alias or a different argument format. An agent without hook
support skips the check entirely.

After this change, CI runs a `review` job on every PR. The job fails while any
group has a commit that no review and no sign-off covers. The `main` ruleset
lists `review` as a required check, so GitHub blocks the merge however the
merge was started and whichever agent started it.

The job prints one of two messages. When every commit is covered:

```
✓ Every commit on this PR has been reviewed.
```

When a group has an unreviewed commit:

```
✗ 1 commit hasn't been reviewed:
    9f8e7d6 test: cover an empty note   (security, code)
  Run the review panel. If you already did, run `wfctl store reviews`.
```

Each unreviewed commit is listed once, with its short hash, its subject, and
the groups that haven't reviewed it.

**Why this priority**: This is the feature. A required check is the only
enforcement that holds for every agent and every form of the merge command.

**Independent Test**: In a repository whose CI runs the `review` job, open a
PR with one commit and no review. The job fails and lists the commit under
both default groups. Run both review groups, let wfctl send the notes, and
rerun the job. It passes.

**Acceptance Scenarios**:

1. **Given** a PR whose commits every group has reviewed, **When** the
   `review` job runs, **Then** it prints the pass message and exits 0.
2. **Given** a PR with a commit added after the last code group review,
   **When** the `review` job runs, **Then** it lists that commit with `(code)`
   and exits 1.
3. **Given** a PR whose commits a human reviewer signed off on, **When** the
   `review` job runs, **Then** it passes even though no group reviewed them.
4. **Given** a push to `main` that isn't a PR, **When** CI runs, **Then** the
   `review` job doesn't run, the same as `release-note`.
5. **Given** the `main` ruleset applied from `.github/rulesets/main.json`,
   **When** the `review` job fails on a PR, **Then** GitHub refuses to merge
   it.

---

### User Story 2 - wfctl records each completed review on GitHub (Priority: P1)

CI only sees what was pushed, and today wfctl keeps the review record in the
state directory on the local machine. So the record has to reach GitHub.

A git note is text that Git attaches to a commit without changing the commit.
When a review run completes, `wfctl review check` adds a note to the run's
head commit, saying which group reviewed it. When a human reviewer signs off,
`wfctl review sign-off` adds a note to the signed-off commit the same way.
wfctl keeps the notes under `refs/notes/wfctl-review`, and after adding one it
pushes that ref to `origin`.

A note holds one plain line per event:

```
reviewed by security
reviewed by code
signed off by a person
```

The line carries no run number or time. As a result, two machines that record
the same event write the same line, and joining their notes never produces a
duplicate.

**Why this priority**: Story 1 can't pass without it. Every PR would fail the
check, since CI would have nothing to read.

**Independent Test**: On a branch with one commit, run the security group to
completion. `git notes --ref=wfctl-review show HEAD` prints `reviewed by
security`, and `git ls-remote origin refs/notes/wfctl-review` shows the ref on
`origin`.

**Acceptance Scenarios**:

1. **Given** a review run that `wfctl review check` reports complete, **When**
   it finishes, **Then** the run's head commit carries a `reviewed by <group>`
   line and the ref is pushed to `origin`.
2. **Given** a human reviewer runs `wfctl review sign-off` on a commit,
   **When** it finishes, **Then** that commit carries a `signed off by a
   person` line and the ref is pushed to `origin`.
3. **Given** a commit that already carries a note, **When** a second group
   completes a run on it, **Then** the note holds both lines.
4. **Given** the push to `origin` fails, **When** `review check` or
   `sign-off` finishes, **Then** it prints a warning naming `wfctl store
   reviews`, keeps the note locally, and still exits as it would without the
   push.
5. **Given** the branch has an open PR whose last `review` job failed,
   **When** `review check` or `sign-off` pushes the notes, **Then** wfctl
   reruns that job.

---

### User Story 3 - The local check and CI agree on which commits are unreviewed (Priority: P1)

The worktree guard reads the review record from the state directory, and CI
reads it from the notes. If the two counted unreviewed commits differently, a
PR could pass locally and fail in CI, or the reverse.

Both sides count with the same function. It takes each group's last reviewed
commit and the signed-off commits as arguments, and reads nothing itself. Two
readers build those arguments:

1. The state directory reader builds them for the guard and `wfctl review
   sign-off`, the same way the check works today.
2. The notes reader builds them for CI. For each group, the last reviewed
   commit is the nearest ancestor of the PR's head commit whose note carries
   that group's line. The signed-off commits are every commit whose note
   carries the sign-off line.

A review on a commit covers that commit and every commit before it back to
where the branch left `main`. A sign-off covers the signed-off commit and its
ancestors, so a commit added after the sign-off is unreviewed again.

**Why this priority**: Without it, a change to the counting rules in one
place leaves the other behind, and the two checks drift apart without any
error.

**Independent Test**: In a scratch repository, build one branch history and
record the same reviews and sign-offs in both the state directory and the
notes. Both readers produce the same arguments, and the function returns the
same unreviewed commits for each.

**Acceptance Scenarios**:

1. **Given** one history with identical review records in the state directory
   and the notes, **When** the guard and the CI check each run, **Then** they
   report the same unreviewed commits per group.
2. **Given** a note on commit C for `security` and a later commit D,
   **When** CI counts, **Then** D is unreviewed for `security` and C and
   everything before it isn't.

---

### User Story 4 - A user resends review notes that didn't reach GitHub (Priority: P2)

Sometimes the push after a review fails, for example when the network drops
or another machine pushed notes first. The CI check then fails on a PR the
groups did review.

`wfctl store reviews` pushes `refs/notes/wfctl-review` to `origin`. If
`origin` rejects the push because it holds notes this machine doesn't have,
the command fetches the remote ref, joins it with the local one, and pushes
again. Joining keeps every line from both sides and drops exact duplicates.
The command sits next to `wfctl store specs`.

**Why this priority**: wfctl already pushes after each review, so this is the
repair path, not the main one. The CI failure message points the user to it.

**Independent Test**: Write a note in two clones of one repository and push
from the first. Run `wfctl store reviews` in the second. Its first push is
rejected, it joins the notes, and its second push succeeds. `origin`'s note
holds the lines from both clones.

**Acceptance Scenarios**:

1. **Given** local notes that `origin` lacks, **When** the user runs `wfctl
   store reviews`, **Then** the ref on `origin` matches the local one.
2. **Given** `origin` holds notes from another machine, **When** the user
   runs `wfctl store reviews`, **Then** the pushed ref holds every line from
   both sides.
3. **Given** the local and remote notes already match, **When** the user runs
   `wfctl store reviews`, **Then** it reports that nothing needed sending and
   exits 0.

---

### User Story 5 - An agent can't write review notes by hand (Priority: P2)

The CI check trusts the notes. An agent that wrote `reviewed by security`
itself, or pushed a notes ref it edited, would pass a PR no reviewer read.

The worktree guard blocks an agent from running any `git notes` command that
writes: `add`, `append`, `edit`, `copy`, `merge`, `remove`, and `prune`. It
also blocks any `git push` that names `refs/notes/` or carries `--mirror`. The
rule covers every notes ref, not only `refs/notes/wfctl-review`, since a
command can pick its ref through `--ref`, `GIT_NOTES_REF`, or `-c
core.notesRef`, and matching only ours would mean chasing each of them.
wfctl's own commands write and push notes from inside their process, so the
guard doesn't see or block them.

**Why this priority**: The check works without this rule, and the rule
doesn't stop a determined agent (see Assumptions). It closes the plain route
of an agent writing the note itself.

**Independent Test**: In a worktree with the guard installed, ask the agent
to run `git notes --ref=wfctl-review add -m "reviewed by code" HEAD`. The
guard refuses it. `git notes --ref=wfctl-review show HEAD` still runs.

**Acceptance Scenarios**:

1. **Given** the guard is installed, **When** an agent runs any `git notes`
   write subcommand on any ref, **Then** the guard refuses it.
2. **Given** the guard is installed, **When** an agent runs `git push origin
   refs/notes/wfctl-review` or `git push --mirror`, **Then** the guard refuses
   it.
3. **Given** the guard is installed, **When** an agent runs `git notes show`
   or `git notes list`, **Then** the guard allows it.
4. **Given** the guard is installed, **When** `wfctl review check` completes a
   run, **Then** its note is written and pushed.

---

### Edge Cases

- **"Update branch" on GitHub.** GitHub's "Update branch" button merges `main`
  into the PR and changes its head without the local machine. If the merge is
  clean, the range rules drop it, and the job passes. This is the reason CI
  works out the result itself instead of trusting a pass the local machine
  posted, which would block until someone reran the review.
- **A rebase after review.** A rebased branch's commits are new commits with
  no notes. The job fails and lists every rebased commit.
- **The branch reaches GitHub before its notes.** This happens on every
  commit pushed after a PR opens. Pushing the notes ref doesn't start a PR
  run, so the job fails once. When wfctl sends the notes, it reruns the failed
  job, and the rerun passes.
- **No open PR, or no failed `review` job.** wfctl sends the notes and reruns
  nothing.
- **A shallow clone, no trunk ref, or an unreadable note.** The job fails with
  a line naming the cause. It doesn't guess at a range.
- **A group added in the PR's own `wfctl.json`.** CI requires it on the same
  PR, so a new group with no notes reports every commit as unreviewed for it.
- **A group removed in the PR's own `wfctl.json`.** CI and the guard still
  require it, since `main` still lists it, and `wfctl review start` runs it
  with the skill and reviewers from `main`'s `wfctl.json`. The removal takes
  effect on PRs opened after it reaches `main`.
- **A group added to `wfctl.json` but not committed.** `wfctl review start`
  runs it, so a user can try a new group before it's required. Neither the
  guard nor CI requires it until the edit is committed.
- **A PR whose `wfctl.json` sets `trunk` to its own branch.** CI ignores the
  key and measures against the PR's base branch, so the commits still need
  reviews.
- **A PR stacked on another PR's branch.** CI measures against the parent's
  branch, so only the child's own commits count. When the parent merges and
  GitHub retargets the child to `main`, the job runs again against `main`.
  This assumes GitHub sends the `edited` event for a retarget it makes itself,
  which is checked after merge.
- **A note line for a group neither `main` nor the PR lists.** CI ignores it.
- **A note line wfctl doesn't recognize.** CI ignores the line and reads the
  rest of the note.
- **Two machines review the same commit.** Both write the same line, and
  joining the notes keeps one copy.
- **A merge commit in the PR's range.** It follows the same range rules as the
  local check today.
- **A release PR.** `release.py` commits the version bump, and no review
  group runs on it. The job fails until the maintainer signs off on the
  release commit by hand. The check has no exception for release branches.

## Requirements _(mandatory)_

### Functional Requirements

**Recording reviews as notes**

- **FR-001**: When `wfctl review check` reports a run complete, wfctl MUST add
  the line `reviewed by <group>` to the note on the run's head commit under
  `refs/notes/wfctl-review`, creating the note if the commit has none.
- **FR-002**: When `wfctl review sign-off` records a sign-off, wfctl MUST add
  the line `signed off by a person` to the note on the signed-off commit.
- **FR-003**: A note MUST hold one line per event, with no run number, time,
  or machine name, and MUST NOT hold the same line twice.
- **FR-004**: After adding a note, `review check` and `sign-off` MUST push
  `refs/notes/wfctl-review` to `origin`. If the push fails, they MUST print a
  warning that names `wfctl store reviews`, keep the local note, and leave
  their exit code unchanged.
- **FR-005**: The state directory record MUST still be written as it is
  today. The note is added alongside it, not in its place.
- **FR-005a**: After any successful push of the notes ref, by `review check`,
  `sign-off`, or `wfctl store reviews`, wfctl MUST rerun the most recent
  `review` job on the branch's open PR if that job failed. When the branch has
  no open PR or the job didn't fail, wfctl MUST rerun nothing. When the rerun
  fails, wfctl MUST print a warning telling the user to rerun the check on the
  PR by hand, and leave the command's exit code unchanged. wfctl MUST NOT retry
  the rerun itself.

**Resending notes**

- **FR-006**: `wfctl store reviews` MUST push `refs/notes/wfctl-review` to
  `origin`.
- **FR-007**: When `origin` rejects the push because it holds notes the local
  ref lacks, `wfctl store reviews` MUST fetch the remote ref, join it with the
  local ref keeping every distinct line from both, and push again.
- **FR-008**: `wfctl store reviews` MUST exit non-zero, naming the cause, when
  the second push also fails or the repository has no `origin`.

**Counting unreviewed commits**

- **FR-009**: One function MUST compute each group's unreviewed commits from
  the head commit, each group's last reviewed commit, and the signed-off
  commits, all passed in as arguments. It MUST NOT read the state directory
  or the notes itself.
- **FR-010**: The guard and `wfctl review sign-off` MUST build those arguments
  from the state directory, and MUST take the group list from the same
  function as FR-015. Their results MUST match what they report today for the
  same state, except where the working tree's `wfctl.json` lists different
  groups from the FR-015 list. There are three such cases:
  1. The branch's committed `wfctl.json` drops a group the trunk lists. They
     now require that group, as CI does.
  2. The working tree lists a group that isn't committed. They no longer
     require it.
  3. The `review` key has a problem in the trunk's or the head's committed
     file. They report it from there, rather than from the working tree.
- **FR-010a**: `wfctl review start`, `wfctl review check`, `wfctl review
  groups`, and `wfctl relay` MUST accept any group in the FR-015 list, plus
  any group the working tree's `wfctl.json` lists. `review groups` lists all
  of them, so the review panel runs a group the branch removed. `relay` finds
  a reviewer's group by its first letter in that list, and exits 1 naming
  both groups when two of them share the letter. They take the group's skill and reviewers from the working tree's
  `wfctl.json` when it lists the group, and from the trunk's otherwise. A run
  of a group that's only in the working tree records its review like any
  other, but the guard and the CI check don't require that group until the
  `wfctl.json` edit is committed.
- **FR-011**: The CI check MUST build those arguments from the notes. A
  group's last reviewed commit is the nearest ancestor of the head, the head
  included, whose note carries `reviewed by <group>`. The signed-off commits
  are those whose note carries `signed off by a person`.
- **FR-012**: A sign-off MUST cover the signed-off commit and its ancestors,
  and no commit after it.

**The CI check**

- **FR-013**: wfctl MUST provide `wfctl check reviews`, a command that reads
  the notes, prints the pass or failure message from User Story 1, and exits
  1 when any group has an unreviewed commit.
- **FR-014**: The failure message MUST list each unreviewed commit once, with
  its short hash, its subject, and the groups that haven't reviewed it, and
  MUST end with "Run the review panel. If you already did, run `wfctl store
  reviews`."
- **FR-015**: The subcommand MUST require every review group that the
  `wfctl.json` at the trunk lists, plus every group that the `wfctl.json` at
  the PR's head commit lists and the trunk's doesn't. It reads both files from
  git as data. When the trunk has no `wfctl.json`, or one with no `review`
  key, the trunk's list is the default groups.
- **FR-015a**: `wfctl check reviews` MUST accept `--base <branch>`. With it,
  the trunk is `origin/<branch>`, for both the range and the trunk's
  `wfctl.json`, and the `trunk` key in the working tree's `wfctl.json` is
  ignored. When `origin/<branch>` doesn't exist, or is the branch under
  review, the subcommand exits 1 with a line naming the cause. Without
  `--base`, it finds the trunk the way the guard does.
- **FR-016**: The subcommand MUST exit 1 with a line naming the cause when the
  clone is shallow, the trunk can't be found, or a note can't be read.
- **FR-017**: CI MUST run a `review` job on pull requests only. The job MUST
  check out the PR's head commit with full history, fetch
  `refs/notes/wfctl-review` from `origin`, and run the subcommand with
  `--base` set to the PR's base branch from the event. The job MUST also run
  when the PR's base branch changes, since GitHub retargets a stacked PR to
  `main` when its parent merges.
- **FR-017a**: The job MUST run the workflow definition and the wfctl code
  from the base branch, never from the PR. It MUST NOT execute any file from
  the PR's checkout, and reads the PR's commits, notes, and `wfctl.json` only
  as data.
- **FR-018**: `.github/rulesets/main.json` MUST list `review` among its
  required checks. Applying the ruleset to GitHub stays a manual step, as
  `AGENTS.md` describes.

**The guard rule**

- **FR-019**: The worktree guard MUST refuse an agent's `git notes add`,
  `append`, `edit`, `copy`, `merge`, `remove`, and `prune`, on any notes ref.
- **FR-020**: The guard MUST refuse an agent's `git push` whose text names
  `refs/notes/` or carries `--mirror`.
- **FR-021**: The guard MUST allow `git notes` commands that only read, such
  as `show` and `list`.
- **FR-022**: The guard's quick text test that decides whether to load the
  review check MUST also match `notes` and `--mirror`, so the rule above runs
  on those commands.

**Release PRs**

- **FR-023**: The review check MUST NOT exempt release branches. A release PR
  passes only when the maintainer signs off on its release commit.
- **FR-024**: `release.py` MUST NOT sign off itself. After it opens the
  release PR, it MUST print the two commands the maintainer has to run: `git
  switch release/v<version>`, then the sign-off command. The script ends on
  `main`, and the sign-off refuses to run there.

**Documentation**

- **FR-025**: `AGENTS.md` MUST list `review` among the ruleset's required
  checks, name `wfctl store reviews`, say that the guard refuses hand-written
  notes, and add the sign-off to the release steps.

## Key Entities _(include if feature involves data)_

- **Review note**: Text Git attaches to one commit under
  `refs/notes/wfctl-review`. It holds one line per event: `reviewed by
  <group>` or `signed off by a person`.
- **Review group**: A panel of agent reviewers with a name, such as
  `security` or `code`, read from `wfctl.json`.
- **Coverage**: Each group's last reviewed commit and the set of signed-off
  commits. The counting function takes this as input. The state directory
  and the notes are two sources of it.
- **Unreviewed commit**: A commit in the PR's range that comes after a
  group's last reviewed commit and isn't a signed-off commit or an ancestor of
  one.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A PR with at least one commit that some group hasn't reviewed
  and nobody signed off on can't merge on GitHub, in 100% of cases,
  whichever merge command or agent started it.
- **SC-002**: A PR whose commits every group reviewed, with the notes pushed
  before the PR's CI run, passes the `review` job with no step beyond running
  the review groups.
- **SC-003**: After a clean "Update branch" merge of `main` into a reviewed
  PR, the `review` job passes with no new review.
- **SC-004**: For the same history and review record, the guard and the CI
  check report the same unreviewed commits per group, in every scenario of the
  shared test.
- **SC-005**: An agent's attempt to write or push a notes ref by hand is
  refused in each of the forms FR-019 and FR-020 name.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` all
  pass.
- Unit tests for the counting function with coverage passed in, covering a
  group review, a later commit, a sign-off, and a commit after the sign-off.
- Unit tests for the notes reader: nearest ancestor per group, an unknown
  line, a line for a group no longer listed, and an unreadable note.
- A scratch repository test that records the same events in the state
  directory and the notes and checks both readers produce identical results
  (User Story 3).
- A scratch repository test for `wfctl store reviews` with two clones and a
  rejected first push (User Story 4).
- Guard tests for each `git notes` write subcommand, `git push` with
  `refs/notes/` and with `--mirror`, the read-only subcommands, and the
  `-c core.notesRef` and `GIT_NOTES_REF` forms.
- Tests for the CI subcommand's pass message, failure message, and each
  cause-naming failure in FR-016, with `NO_COLOR` pinned.
- A scratch repository test where the head's `wfctl.json` sets `trunk` to the
  branch under review: `wfctl check reviews --base main` still reports the
  branch's unreviewed commits (FR-015a).
- Tests for the local group list (FR-010, FR-010a): the guard refuses a branch
  whose committed `wfctl.json` drops a group the trunk lists; `review start`
  runs that group with the trunk's skill and reviewers, and `review groups`
  lists it; a group only in the working tree runs but the guard doesn't
  require it. The test that checks both readers agree adds the removed-group
  history.
- A run of the `review` job on a throwaway PR after this feature merges: it
  fails before the notes are pushed and passes after the rerun. This
  feature's own PR gets no `review` job, since GitHub reads the job from
  `main` (Clarifications, 2026-10-25).
- `uv run wfctl verify` and `uv run wfctl doctor` are green.

## Assumptions

- Pre-specify design context loaded from specs/627-ci-review-check/design.md.
- GitHub accepts a pushed notes ref, and a `pull_request` job can fetch it
  with the default token. Checked on 2026-10-25 with a throwaway notes ref and
  draft PR #647: the push succeeded, and the job fetched the ref and printed
  the note on the PR's head commit.
- On a `pull_request` run, `actions/checkout` checks out a merge of the PR into
  its base, not the PR's head. With `fetch-depth: 0` it leaves `origin/main`
  and a full history, but no `origin/HEAD` and no local `main`. Checked in the
  same run: `HEAD` was GitHub's merge commit, whose second parent was the PR's
  head. FR-017 asks the job to check out the head commit for this reason.
- The job names the trunk with `--base` from the event's base branch rather
  than discovering it, so neither `origin/HEAD` nor a `trunk` key in the PR's
  `wfctl.json` decides it (research R14). This replaces the `git remote
  set-head origin --auto` step plan first chose (research R5).
- The default token in this repository grants `contents: write` on a PR run,
  so a PR's own job could push notes. The `review` job should declare
  `permissions: contents: read`, and plan decides where else that applies.
- The CI command is `wfctl check reviews`, beside `wfctl check specs`, as plan
  settled (research R2).
- A review run always starts where the last complete run ended, so a note on
  commit C covers every commit from where the branch left `main` up to C.
  Checked after #642 merged: `start` begins at the last reviewed commit, or the
  merge base after a rebase (research R1).
- #642 added a `branch` keyword to `commit_range`, `unreviewed`, and `start`,
  and this branch has merged `main` with it.
- CI can't catch a forged note. The agent pushes with the maintainer's own
  credentials and keys, so signing the notes wouldn't help. Only running the
  reviewers in CI, or a step only a person can take, closes that gap
  (`review-record-in-git-notes.md`). The guard rule in User Story 5 closes the
  plain route and no more.
- PRs come from branches in this repository, not forks, so the job can fetch
  the notes ref from `origin`.
- A job triggered so that GitHub runs the base branch's workflow reports its
  check on the PR's head commit, so the ruleset can require it. This can only
  be checked once the job is on `main`, since GitHub reads that workflow from
  the base branch. If it doesn't hold, the fallback keeps the PR trigger and
  runs `main`'s wfctl from a second checkout. That fallback runs the PR's own
  workflow file, which FR-017a forbids, so the maintainer decides whether to
  amend FR-017a before the fallback is used.

### Not in scope

- Signing notes, for the reason above.
- Running the reviewers in CI. It's the only full fix for a forged note, and
  it's a much larger change.
- Having the local guard read the notes. The accepted record keeps the guard
  on the state directory, and #642 is changing that code now.
- Starting a CI run from GitHub's side when the notes ref arrives. wfctl
  reruns the failed job itself after it sends the notes (FR-005a).
- Applying the ruleset to GitHub. That's the maintainer's manual step.
