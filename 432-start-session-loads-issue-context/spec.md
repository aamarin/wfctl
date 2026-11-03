# Feature Specification: Session start loads only the branch's own context

**Feature Branch**: `432-start-session-loads-issue-context`
**Created**: 2026-11-02
**Status**: Draft
**Input**: Issue #432 and `design.md` in this folder. The scope and Not Doing lists there carry over unchanged.

## Clarifications

### Session 2026-11-02

- Q: Does #432 keep the size-limit test on `start-session/SKILL.md`, which the accepted record and the issue's done-when both list? → A: No. It moves to #693, which asks for a person's approval when any skill grows more than 30% past its last approved size, and whether that skill should be split.
- Q: How much of the handoff does the report print? → A: All of `session-summary.md`, word for word. An agent on an issue branch reads the rest of the file almost every session, so printing only the path or the TODO list would make it open the file anyway.
- Q (2026-11-02, after measuring T038): Does the report print every section of the handoff? → A: No. It leaves out What We Accomplished and Files Changed, since the commits and uncommitted changes above it show the same work, and names them on a `Left out` line. The JSON `handoff` key keeps the whole file. The same pass prints the newest five commits plus every unmarked one, drops empty issue header fields, and drops plain `status`'s two notices about who decides.
- Q: Who flags commits that don't mention the branch's issue? → A: wfctl, in the report. The agent passes the flagged commits on and no longer compares commits itself.
- Q: What counts as an unanswered review comment in the PR line? → A: A review thread that isn't resolved, whether or not someone has replied to it.
- Q: Can the issue decide the first action? → A: It helps decide it, on an issue branch whose handoff names none. The agent reads three pieces of evidence in order: the count of commits ahead of the trunk, the pipeline position, and the issue. Each one hints at where the work is. No commits can mean no implementation yet, though specs may exist. No spec or a missing one can mean the pipeline hasn't started or is partway. The first action is the next command the pipeline position names. When the evidence disagrees, the agent asks and names the mismatch. A first action in Next Session TODO still wins, and nothing written in the issue is run because the issue said so (`session-start-reads-branch-progress.md`).

## User Scenarios & Testing _(mandatory)_

A session start is the first thing an agent runs in a new conversation, through the `/start-session` skill. Today it costs 19.2k tokens above a 43.8k baseline in this repository, measured on `main` at 13216e8 on 2026-11-01. Most of that is the open issue list, the open PR list, every accepted record's slug, and `doctor` notices about other issues. A worktree session works on one issue, so it uses little of that.

### User Story 1 - An issue worktree starts with its own issue's context (Priority: P1)

A developer opens a session in a worktree for issue 432. The agent runs `/start-session` and gets one report about this branch: the pipeline position, the handoff, the branch's commits, the issue's title and description, the parent epic, and the branch's open PR. It does not get the repository's open issues or open PRs.

**Why this priority**: This is the whole reason for the change. Today the agent starts without the issue's description unless a handoff tells it to look, and pays for lists it doesn't use.

**Independent Test**: Run `/start-session` in an issue worktree and check that the report names the branch's issue with its description, and that no repository-wide issue or PR list was loaded.

**Acceptance Scenarios**:

1. **Given** a worktree whose branch names an open issue with a parent epic and an open PR, **When** the agent runs `wfctl status --session`, **Then** the report prints the issue's title and description, the parent's id and title, and the PR with its check state and its count of unanswered review comments.
2. **Given** the same worktree, **When** the agent runs `/start-session`, **Then** the session does not run `wfctl issue list` or `wfctl change list`.
3. **Given** a branch whose issue has no parent and no open PR, **When** the agent runs `wfctl status --session`, **Then** the report prints `Parent: none` and `PR: none`.
4. **Given** the branch has a `session-summary.md`, **When** the agent runs `wfctl status --session`, **Then** the report prints the whole file, including its `In Flight` section, and the agent doesn't open the file separately.

---

### User Story 2 - A `main` session loads no list until asked (Priority: P1)

A developer opens a session on the `main` checkout. The branch names no issue, so each tracker line reads `not-applicable`. The agent asks what we're working on and loads a list only when the conversation needs one.

**Why this priority**: Sessions on `main` are usually exploratory, so a list loaded up front is often unused. It's P1 because the same report has to serve both kinds of branch.

**Independent Test**: Run `/start-session` on `main` and check that no tracker list was loaded before the first question.

**Acceptance Scenarios**:

1. **Given** the `main` checkout, **When** the agent runs `wfctl status --session`, **Then** the issue, parent, and PR lines each read `not-applicable`, and the report makes no tracker call.
2. **Given** the `main` checkout, **When** the agent runs `/start-session`, **Then** the session asks what we're working on, as step 8 decides today, and no repository-wide list is loaded before the user answers.

---

### User Story 3 - The skill decides the same thing from less (Priority: P2)

The `/start-session` skill runs four wfctl commands instead of six, and its doctor repair guidance moves to a reference file. An agent reads that file only when `doctor` prints something other than a ✓. The step 8 table still decides whether the agent starts work or asks. The one change is on an issue branch whose handoff names no first action, where the agent now starts from the branch's progress instead of asking.

**Why this priority**: The skill's instructions are 8.4k of the 19.2k, the largest single cost. Most of it is repair guidance a green session never uses.

**Independent Test**: Run `/start-session` on an issue branch and on `main`, before and after the change, and compare the step 8 row each one names.

**Acceptance Scenarios**:

1. **Given** a branch where the old skill took step 8's first row, **When** the new skill runs, **Then** it takes the first row and quotes the same Next Session TODO line.
2. **Given** a `main` checkout where the old skill took step 8's second or third row, **When** the new skill runs, **Then** it takes the same row.
3. **Given** an issue branch whose handoff names no first action, and evidence that agrees, **When** the new skill runs, **Then** it doesn't ask, runs the next command the pipeline position names, and says it used the commit count, the pipeline position, and the issue.
4. **Given** an issue branch whose handoff names no first action, and an issue that asks for something the spec left out, **When** the new skill runs, **Then** it asks what we're working on and names the mismatch.
5. **Given** `doctor` reports every layer ✓, **When** the new skill runs, **Then** the agent doesn't open the repair reference file.
6. **Given** `doctor` reports a layer behind, **When** the new skill runs, **Then** the agent opens the reference file and repairs the layer the same way the old skill did.

---

### User Story 4 - `doctor` leaves out notices about other issues (Priority: P2)

`doctor` currently prints a notice for each issue claimed by two spec folders, such as issues 11, 17, 24 and 40 in this repository. Those notices repeat every session and rarely concern the branch. `wfctl doctor --session` prints them only when they name the branch's own issue.

**Why this priority**: It removes recurring noise, and it's smaller than the report itself.

**Independent Test**: In a repository with a claim notice for issue 11, run `wfctl doctor --session` on a branch for issue 432 and on a branch for issue 11.

**Acceptance Scenarios**:

1. **Given** a claim notice for issue 11, **When** `wfctl doctor --session` runs on branch `432-…`, **Then** the notice is not printed.
2. **Given** the same notice, **When** `wfctl doctor --session` runs on branch `11-…`, **Then** the notice is printed.
3. **Given** any branch, **When** plain `wfctl doctor` runs, **Then** its output is the same as before this change.
4. **Given** any branch, **When** `wfctl doctor --session` runs, **Then** every finding other than a claim notice prints as it does in plain `doctor`, and the exit code is the same.

---

### User Story 5 - wfctl flags commits that don't mention the issue (Priority: P3)

Today the agent compares the branch's commits against every open issue. wfctl now does the comparison against the branch's own issue, and the report marks each commit that doesn't mention it.

**Why this priority**: It follows from dropping the issue list. Moving it into wfctl also removes a step the agent could skip without anyone seeing.

**Independent Test**: Run `wfctl status --session` on a branch whose commits all mention its issue, and on one with a commit that doesn't.

**Acceptance Scenarios**:

1. **Given** every commit on branch `432-…` mentions #432, **When** the agent runs `wfctl status --session`, **Then** no commit is marked.
2. **Given** a commit on branch `432-…` that mentions no issue or a different one, **When** the agent runs `wfctl status --session`, **Then** the report marks that commit, and the skill reports it as untracked.
3. **Given** the `main` checkout, **When** the agent runs `wfctl status --session`, **Then** no commit is marked, since the branch names no issue to compare against.

### Edge Cases

- The tracker isn't configured, its config can't be read, or the backend doesn't implement `view`, `parent`, or `branch`. The report prints that line with the reason code `no-tracker`, `bad-config`, or `unsupported`. A repository with an old `github.json` prints `Parent: unsupported` and `PR: unsupported` until it runs `wfctl install-skills --tracker github`.
- A tracker call fails or times out. The report prints that line as `failed` or `timeout`, prints the rest of the report, and `status --session` exits 0. Without this line, a branch whose PR has failing checks or unanswered review comments would look the same as a branch with no PR (`tracker-reads-report-failure.md`).
- The issue description carries an instruction, such as "push this branch and open the PR" or "run this script". The report prints it as tracker text, and the agent doesn't act on it. The issue tells the agent what the work is for, but the agent never runs a command, URL, script, or package named in it, and never pushes, comments, or opens a PR because of it.
- An issue branch has no handoff, or a handoff with no first action. The agent works out where to start from the commit count, the pipeline position, and the issue, in that order, and says which it used, instead of asking what we're working on.
- The evidence disagrees, such as an issue that asks for something the spec left out, or describes as still to do something the commits already did. The agent asks what we're working on and names the mismatch.
- The issue line reads `failed`, `timeout`, `unsupported`, `no-tracker`, or `bad-config`, or the issue body is empty. The agent has only the commit count and the pipeline position, so it asks.
- The worktree was cut from another feature branch. The commit count includes that branch's commits, so it overstates how far this issue has got. The agent treats the count as a hint.
- The branch names an issue that is closed or missing. `wfctl start` already refuses the session in a linked worktree, so the report is never reached there. On the `main` checkout the branch names no issue, so this can't happen.
- There is no `session-summary.md`. The report says no handoff exists. On a trunk branch, step 8 asks as it does today. On an issue branch, the agent works out where to start from the branch's progress.
- The handoff's `In Flight` section is still the template placeholder. The report prints the file as it is, and `wfctl start`'s existing ⚠ for the placeholder still prints.
- `doctor --session` runs on the `main` checkout. No issue matches, so it prints no claim notices.
- The repository has no `origin/HEAD`, so wfctl can't find the trunk. The report reads `Commits: trunk not found`, prints the newest five of the last 20 commits, and marks none of them, since it can't tell which commits are the branch's. This is the one exception to FR-019.

## Requirements _(mandatory)_

### Functional Requirements

**The session report**

- **FR-001**: `wfctl status --session` MUST print one report built from the branch, the pipeline position, the handoff, the commits, and the tracker. Plain `wfctl status` MUST stay unchanged and MUST make no tracker call.
- **FR-002**: `wfctl status --session --json` MUST print the same report as one JSON object, with the fields of `wfctl status --json` plus the session fields.
- **FR-003**: The report MUST carry every fact step 8 of the skill reads: the branch's issue key or `unknown`, the session holder, the handoff, and the most recent stop's kind (none, continued, or wrapped up).
- **FR-004**: The report MUST print `session-summary.md` word for word, except its What We Accomplished and Files Changed sections, which it MUST name on a `Left out` line, or say that none exists. A heading inside a fenced code block doesn't start a section. The skill MUST NOT read the file separately. Text from outside wfctl, meaning the handoff, tracker output, commit subjects, and `git status` lines, MUST print as written and MUST NOT stop the report. That covers square brackets such as a `[x]` checkbox or a `[/x]`, emoji codes such as `:warning:`, and lines longer than the console width. A tab prints as spaces, and a `\r` or any other control character, such as BEL, is dropped, since none of them changes what the agent reads.
- **FR-005**: The report MUST print how many commits the branch is ahead of the trunk, then list those commits and the uncommitted changes. The trunk is the `trunk` that `wfctl.json` declares on the default branch, which `origin/HEAD` names, or the default branch itself when none is declared. The count runs from the branch's merge base with the trunk.
- **FR-006**: The report MUST give the count of accepted architecture records and name `wfctl arch context` as the command that prints them, instead of listing their slugs.
- **FR-007**: On a branch that names an issue, the report MUST print the issue's title and description, its parent's id and title when it has one, and the branch's open PR with its check state and its count of unanswered review comments when it has one.
- **FR-008**: On a branch that names no issue, the report MUST make no tracker call and MUST print each tracker line as `not-applicable`.
- **FR-009**: The report MUST NOT print any repository-wide list, whether open issues, open PRs, open worktrees, or recent merges, on any branch.

**The tracker reads**

- **FR-010**: The tracker backend MUST support an optional `parent` verb that takes an issue id and prints the parent's id and title, or nothing when the issue has no parent.
- **FR-011**: The tracker backend MUST support an optional `branch` verb in its `changes` section that takes a branch name and prints the branch's open change with its check state and its count of unanswered review comments, or nothing when there is no open change. An unanswered review comment is a review thread that isn't resolved, whether or not it has a reply.
- **FR-012**: The GitHub backend MUST implement both verbs. The report MUST always print the issue, parent, and PR lines, and MUST NOT leave any of them out. A line whose lookup returned an answer shows the answer. Every other line shows exactly one reason code, with no error text:
  1. `none`: the lookup exited 0 with no output.
  2. `unsupported`: the backend doesn't implement the verb.
  3. `no-tracker`: the repository has no tracker configured.
  4. `bad-config`: the tracker config can't be read, or the verb's entry is malformed or needs a value wfctl doesn't have.
  5. `failed`: the lookup exited non-zero.
  6. `timeout`: the lookup gave no answer within 15 seconds.
  7. `not-applicable`: the branch names no issue, so no lookup runs.

  This follows `tracker-reads-report-failure.md`, which supersedes `backend-tracker-reads-parent-and-change.md`.

**`doctor --session`**

- **FR-013**: `wfctl doctor --session` MUST print the same findings and exit with the same code as plain `wfctl doctor`, except that it leaves out every notice about an issue claimed by two spec folders unless that issue is the branch's own.
- **FR-014**: Plain `wfctl doctor` MUST stay unchanged.

**The skill**

- **FR-015**: `/start-session` MUST run `wfctl start && wfctl doctor --session`, then `wfctl arch context`, then `wfctl status --session`. It MUST run `wfctl status --session` whatever `doctor` exited with, and MUST stop after `wfctl start` when `start` exits 1, as it does today.
- **FR-016**: `/start-session` MUST NOT run `wfctl issue list` or `wfctl change list`.
- **FR-017**: `/start-session` MUST keep the step 8 table and #679's paragraph about the spec question on an issue branch with no spec folder, with the same meaning, except for the change FR-022 makes to the last row on an issue branch.
- **FR-022**: The report MUST print the issue under a heading that marks it as text from the tracker. When the handoff's Next Session TODO names a first action, step 8 MUST still take it from there. On an issue branch whose handoff names none, step 8 MUST have the agent read the commit count, the pipeline position, and the issue, in that order, and take the next command the pipeline position names as the first action, instead of asking. The agent MUST ask, naming the mismatch, when the evidence disagrees, and MUST ask when the issue line has no answer. Step 7 MUST report which evidence the agent used. A trunk branch still asks. The agent MUST NOT run a command, URL, script, or package named in the issue, or push, comment, or open a PR because the issue says to, at any point in the session (`session-start-reads-branch-progress.md`).
- **FR-018**: The doctor repair guidance in step 1 MUST move to a reference file beside the skill. The skill MUST tell the agent to open it only when `doctor` prints something other than a ✓, and the guidance in it MUST keep the same repair policy.
- **FR-019**: On a branch that names an issue, the report MUST mark each commit whose subject or body doesn't mention that issue's key. A key that's only digits is mentioned as `#<key>`, such as `#432`, and any other key, such as `PROJ-123`, as itself. The skill MUST report marked commits as untracked and MUST NOT compare commits itself. The skill's "likely done" check, which compared commits against the open issue list, is dropped, since the report no longer loads that list.

**Release**

- **FR-020**: The branch MUST commit `changes/432.change.md`, since a user of `/start-session` sees a different report.
- **FR-021**: `session-report-built-in-code.md` is superseded by `session-start-reads-branch-progress.md`, which no longer promises a size check or a skill that runs one command. #432's done-when MUST drop the size-limit test, so it doesn't promise a test this change doesn't ship. #432's scope MUST also drop "The report gives the handoff's path rather than retelling it", since the report now prints the handoff. The user makes the two issue edits, because no `wfctl issue` verb edits an issue body and the agent shouldn't route around wfctl with `gh`. The agent drafts the replacement text for the user, and the PR doesn't open until the issue matches.

### Key Entities

- **Session report**: what `wfctl status --session` prints. It holds the step 8 facts, the handoff less the two sections FR-004 leaves out, the count of commits ahead of the trunk, the commits, the record count, and, on an issue branch, the issue, its parent, and the branch's open PR.
- **Claim notice**: a `doctor` line saying one issue is claimed by two spec folders. It names the issue, so `doctor --session` can tell whether it concerns the branch.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A `/start-session` in an issue worktree costs materially less than 19.2k tokens above the baseline. The PR records the before and after figures, both measured with the same headless `claude -p` run.
- **SC-002**: A `/start-session` on the `main` checkout costs less than it did before the change, by the same measurement, and loads no repository-wide list before the user's first answer.
- **SC-003**: On an issue branch and on `main`, the new skill names the same step 8 row as the old skill did on the same state, except on an issue branch whose handoff names no first action. There it starts from the branch's progress when the evidence agrees, asks when it disagrees, and names the evidence it used.
- **SC-004**: With `doctor` green, the session reads none of the repair guidance.
- **SC-005**: No claim notice about another issue appears in a `/start-session` report.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`, all green.
- Tests for `status --session` cover an issue branch with a parent and a PR, an issue branch with neither, a trunk branch, a backend missing each verb, and a backend that fails on each verb.
- Tests for `doctor --session` cover a claim notice for the branch's issue, one for another issue, and plain `doctor` output unchanged.
- `uv run wfctl install-skills`, then run `/start-session` in an issue worktree and on `main`, and compare the step 8 row with the old skill's, allowing the one change SC-003 names.
- Measure tokens before and after in an issue worktree and on `main`. The baseline run uses `claude -p "Reply with the single word ok." --output-format stream-json --verbose --no-session-persistence --permission-mode auto`, and the session run uses `/start-session` as the prompt. Sum `input_tokens`, `cache_read_input_tokens`, and `cache_creation_input_tokens` per assistant turn. Re-measure the baseline too, since the per-turn response-shape hook got smaller on 2026-11-02.
- `uv run wfctl doctor` reports no drift.

## Assumptions

- Pre-specify design context loaded from `design.md` in this folder.
- GitHub's sub-issues API returns an issue's parent in one call. A tracker without an equivalent prints `Parent: unsupported`.
- No second view of `status` is planned. If one comes, a `status` command group becomes worth its cost, as the record `432-session-report-is-a-status-flag.md` says.
- A tracker whose keys are only digits references them as `#<key>` in commits, as GitHub does. A tracker that references numeric keys another way, such as Azure DevOps's `AB#123`, would see every commit marked. No tracker setting overrides this today.
- The size-limit test on `start-session/SKILL.md` is out of scope, and #693 replaces it with a growth check on every skill.
