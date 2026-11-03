Implementation complete: 2026-11-03

## Tasks at completion

~~~~markdown
---
description: 'Tasks for #432: session start loads only the branch''s own context'
---

# Tasks: Session start loads only the branch's own context

**Input**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/cli.md`, `contracts/tracker.md`, and `quickstart.md` in this folder.

**Design records read before these tasks were written** (listed in `design.md`):

- `docs/architecture/design/432-session-report-is-a-status-flag.md`: the report is `wfctl status --session`. No task puts it in `wfctl start` or makes it a subcommand.
- `docs/architecture/design/432-doctor-session-scopes-claim-notices.md`: `doctor --session` leaves out claim notices and changes nothing else. US4's tasks stay inside that.

**Open plan-review findings are carried in as tasks.** Editing `plan.md` again would make the satisfied review at 24b33cf stale, so each finding becomes a task instead:

1. PR-033, the trunk for the commit count: T001, T005, and T006.
2. PR-018, control characters in outside text: T003 and T018.
3. PR-019, the `uv run --project * wfctl doctor` grant: T031 and T036.
4. PR-034, the size-limit question in `design.md`: T002.
5. PR-035, asking when the issue body is empty: T032 and T036.

PR-025 is the user's call and has no task. The two design exceptions in `exceptions/` stay as they are until the user decides.

**Tests**: every behavior change gets a test, written first and seen failing. Skill prose is pinned by the skill tests the plan names, and checked with a real `/start-session` run.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: a different file, with no dependency on an unfinished task
- **[Story]**: US1 to US5, from `spec.md`

---

## Phase 1: Setup (spec document fixes)

**Purpose**: Bring the feature's own documents in line with the plan before any code is written against them. None of these tasks edits `plan.md`.

- [X] T001 [P] In `research.md` §5, replace "The trunk is what `origin/HEAD` names" with the rule FR-005 and `contracts/cli.md` state: the `trunk` that `wfctl.json` declares on the default branch, or the default branch itself, as `_review.review_trunk` resolves it, and trunk not found when there's no `origin/HEAD` (T006). In `data-model.md`, give the `commits` row the last-20 case: "the last 20 commits, each with `mentions_issue` `null`, when the trunk can't be found" (PR-033). Verify by reading both files against the trunk paragraph in `contracts/cli.md`.
- [X] T002 [P] In `design.md`, point the Open Questions entry and MVP Scope's second out-of-scope item at the spec's 2026-11-02 clarification, which moved the size-limit test to #693. Drop the wording that says it still needs the user's call (PR-034). Verify by reading `design.md` against `spec.md` Clarifications.
- [X] T003 [P] In `spec.md` FR-004 and the verbatim paragraph in `contracts/cli.md`, say what the renderer does to control characters. A tab prints as spaces, and a `\r` or any other C0 control character, such as BEL, is dropped, since none of them changes what the agent reads. Every printable character still prints as written (PR-018). T018 pins it.
- [X] T004 Validate Phase 1 by re-reading `spec.md` FR-004 and FR-005, `research.md` §5, `data-model.md`, and `design.md`. No trunk wording may name only `origin/HEAD`, and no size-limit question may still be open — merge gate

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: The readers the report is built from. US1, US2, and US5 all need them.

### Trunk resolution (PR-033)

- [X] T005 Write failing tests in `tests/test_session_report.py` for the commit range's trunk:
  1. A repo whose default branch declares `trunk` counts from the merge base with `origin/<trunk>`.
  2. A repo with no declaration counts from `origin/<default>`.
  3. A repo with no `origin/HEAD` reads trunk not found, as the spec's last edge case says, even when a local trunk branch exists.
  4. Each failure gives `commits_ahead` `None`, the last 20 commits with `mentions_issue` `None`, the console line `Commits: trunk not found`, and exit 0. The failures are no `origin/HEAD`, `NoTrunk`, a `ReviewError` because `origin/HEAD` names a ref the clone lacks, and a declared trunk the clone lacks.
- [X] T006 Implement `_commit_range(repo_root)` in `wfctl/_session_report.py`. When `origin/HEAD` is missing, it reports trunk not found without calling `_review.review_trunk`. We didn't choose the local fallback `review_trunk` takes in that case, because the spec rules it out and the fallback reads the working tree's `trunk`, which the agent can edit. Otherwise it calls `review_trunk(repo_root)` and uses the ref it returns, so the report, reviews, and the PR guard measure against the same trunk. It catches `ReviewError`, which `NoTrunk` subclasses, and any git failure, and maps each one to "trunk not found", so a trunk problem never makes the report exit non-zero. It drops `review_trunk`'s warnings, since a review's trunk warning is for `review start` to print. Verify with T005.

### Last stop

- [X] T007 [P] Write failing tests in `tests/test_session_stopped_not_finished.py` for `last_stop()`. The latest `end` event wins over an older one, a torn final line is skipped, a stop with no `continued` key reads `wrapped`, and a log with no `end` event reads `none`. These replace the three step-3 grep tests in `tests/test_start_session_asks_conditionally.py` that the plan names.
- [X] T008 [P] Implement `last_stop(agent_dir, branch)` in `wfctl/_session.py`, using the same malformed-line skipping as the other event readers. Verify with T007.

### Tracker reads

- [X] T009 [P] Write failing tests in `tests/test_tracker.py`. `parent` validates in `ALLOWED` with `{id}`, `branch` validates in `ALLOWED_CHANGES` with `{branch}`, params substitute into the argv, and a config with neither verb still passes `tracker-check`. Extend the scaffold-tracker test to cover `ALLOWED_CHANGES`.
- [X] T010 Add `parent` to `ALLOWED` and `branch` to `ALLOWED_CHANGES` in `wfctl/_tracker.py`, and let `_read_verb` take a params dict. Verify with T009.
- [X] T011 Write failing tests in `tests/test_session_report.py` for `read_text()`, one per reason code:
  1. `none`: exit 0 with no output, and with output that is only whitespace.
  2. `unsupported`, `no-tracker`, and `bad-config`. `bad-config` covers an unreadable config, a malformed entry, and a missing placeholder value.
  3. `failed`: a non-zero exit with no output, and an `OSError` at launch.
  4. `timeout`.
  5. `ok` returns the output as written.
- [X] T012 Implement `read_text(repo_root, section, verb, params)` in `wfctl/_tracker.py`, returning `(text | None, code)`. `_read_verb` keeps its current shape for `fields` and `state`. Verify with T011 and the existing `tests/test_tracker.py`.

### GitHub backend

- [X] T013 [P] Write `wfctl/agents/trackers/github-issue-parent.sh` per `research.md` §1. It prints `#<number> <title>`. On a 404 carrying "No parent issue found" it prints nothing and exits 0, and on any other failure it exits non-zero. Verify by running it against #432, which prints `#619 …`, and #2, which prints nothing and exits 0.
- [X] T014 [P] Write `wfctl/agents/trackers/github-change-branch.sh` per `research.md` §2. It runs one GraphQL query, keeps only PRs whose head is in this repository, picks the most recently updated one when several match, and prints one line with the check state and the unresolved thread count. Verify by running it on a branch with an open PR, and on this branch, where it prints nothing and exits 0.
- [X] T015 Add both verbs to `wfctl/agents/trackers/github.json` per `contracts/tracker.md`, list both scripts in `_GITHUB_TRACKER_FILES` in `wfctl/cli.py`, and document both verbs and their output in `wfctl/agents/skills/scaffold-tracker/SKILL.md`. Verify with `uv run wfctl install-skills --tracker github`, then `uv run wfctl tracker-check`, which lists `parent` and `branch`.
- [X] T016 Validate Phase 2 with `uv run pytest -q tests/test_tracker.py tests/test_session_stopped_not_finished.py tests/test_session_report.py` — merge gate

---

## Phase 3: User Story 1 - An issue worktree starts with its own issue's context (P1) 🎯 MVP

**Goal**: `wfctl status --session` prints one report about the branch. It carries the issue, parent, PR, the whole handoff, the commit count, and the commits, and no repository-wide list.

**Independent Test**: On an issue branch with a parent and an open PR, `wfctl status --session` prints the issue under `Issue (tracker text)`, then `Parent:`, `PR:`, and the whole `session-summary.md`, with no issue or PR list.

**Verification**: `tests/test_session_report.py`, `tests/test_cli_status.py`, and `uv run wfctl status --session` in this worktree.

- [X] T017 [US1] Write failing tests in `tests/test_session_report.py`:
  1. An issue branch with a parent and a PR prints all three tracker lines with their answers.
  2. One with neither prints `Parent: none` and `PR: none`.
  3. Each reason code prints on its line, and no line is left out. `--json` carries each code in `tracker_status`.
  4. The three reads run concurrently, so three 15-second timeouts cost about 15 seconds rather than 45.
  5. The whole handoff prints, `In Flight` included, and a missing one prints `Handoff: none on this branch`.
  6. The record count prints with `wfctl arch context`, and no repository-wide list appears.
  7. The `Session: <holder> · last stop: <kind>` line prints, and `--json` carries `session_holder` and `last_stop` (FR-003).
  8. A dirty tree lists its `git status --short` lines under `Uncommitted`, and a clean tree lists none (FR-005).
  9. `status --session` leaves `events.jsonl` and every other file in the state dir unchanged, as `contracts/cli.md` and the design record's Verification ask.
- [X] T018 [US1] Write failing tests in `tests/test_session_report.py` for outside text through a non-terminal console. A handoff, an issue body, and a commit subject carrying `[x]`, `[/x]`, `:warning:`, a tab, a `\r`, a BEL, and a 120-column line print as T003 states, and the command exits 0 (PR-018).
- [X] T019 [US1] Implement `build_session_report()` and `render_session_report()` in `wfctl/_session_report.py`. Both take their readers as arguments, as the plan's Structure Decision says. Outside text has its C0 control characters other than tab and newline stripped, then goes through `console.print(text, markup=False, highlight=False, emoji=False, soft_wrap=True)`. Verify with T017 and T018.
- [X] T020 [US1] Add `--session` to `status_cmd` in `wfctl/cli.py`. With `--json`, it prints the `status --json` payload plus the ten session keys in `contracts/cli.md`. First write a failing test in `tests/test_cli_status.py` that plain `status` and `status --json` make no tracker call and write nothing. Verify with that test and T017.
- [X] T021 [US1] Validate US1 with `uv run pytest -q tests/test_session_report.py tests/test_cli_status.py`, then `uv run wfctl status --session` in this worktree after T015's install — merge gate

---

## Phase 4: User Story 2 - A `main` session loads no list until asked (P1)

**Goal**: On a branch that names no issue, the report makes no tracker call and prints each tracker line as `not-applicable`.

**Independent Test**: `wfctl status --session` on a trunk branch prints `not-applicable` three times and runs no tracker command.

**Verification**: `tests/test_session_report.py`, and `uv run wfctl status --session` in the `main` checkout.

- [X] T022 [US2] Write failing tests in `tests/test_session_report.py`. On a branch whose `issue` is `unknown`, a tracker config whose verbs fail the test when run is never invoked, all three lines read `not-applicable`, and every `tracker_status` value is `not-applicable`.
- [X] T023 [US2] Skip the tracker reads in `build_session_report()` when the issue is `unknown`. Verify with T022.
- [X] T024 [US2] Validate US2 with `uv run pytest -q tests/test_session_report.py` and `uv run wfctl status --session` in the `main` checkout — merge gate

---

## Phase 5: User Story 5 - wfctl flags commits that don't mention the issue (P3)

This phase comes before US3 because the rewritten skill reports the marked commits and stops comparing commits itself.

**Goal**: The report marks each commit whose subject or body doesn't mention the branch's key.

**Independent Test**: On `432-…`, a commit mentioning `#432` is unmarked, and one mentioning `#43` or no issue is marked. On trunk, no commit is marked.

**Verification**: `tests/test_session_report.py`.

- [X] T025 [US5] Write failing tests in `tests/test_session_report.py` for `research.md` §4. `#432` as a whole token matches, and `#4321` and a bare `432` don't. A `PROJ-123` key matches itself, and a mention in the body counts. On trunk, or when the trunk isn't found, every `mentions_issue` is `None`.
- [X] T026 [US5] Implement the match in `wfctl/_session_report.py`, reading subjects and bodies from one `git log` call over T006's range. Verify with T025.
- [X] T027 [US5] Validate US5 with `uv run pytest -q tests/test_session_report.py` — merge gate

---

## Phase 6: User Story 4 - `doctor` leaves out notices about other issues (P2)

**Goal**: `wfctl doctor --session` leaves out claim notices for other issues and changes nothing else.

**Independent Test**: With a claim notice for issue 11, `doctor --session` leaves it out on `432-…` and prints it on `11-…`. Plain `doctor` prints it on both.

**Verification**: `tests/test_doctor_session.py`.

- [X] T028 [P] [US4] Write failing tests in a new `tests/test_doctor_session.py`. The branch's own claim notice prints, and another issue's doesn't. Trunk prints none. Plain `doctor` output is byte-identical to before, and the exit code matches plain `doctor` in a drifted tree and a clean one.
- [X] T029 [US4] Add `--session` to `doctor_cmd` in `wfctl/cli.py`, and give `_report_double_claimed_keys` an optional key to keep. Verify with T028.
- [X] T030 [US4] Validate US4 with `uv run pytest -q tests/test_doctor_session.py`, then `uv run wfctl doctor --session` here, which prints none of the notices for 11, 17, 24, and 40 — merge gate

---

## Phase 7: User Story 3 - The skill decides the same thing from less (P2)

**Goal**: `start-session/SKILL.md` runs four commands and reads one report instead of six reads. It keeps the step 8 table with the last row split by branch kind, and moves the repair guidance to a reference file.

**Independent Test**: `/start-session` on an issue branch and on `main` names the same step 8 row as before, except for the one change SC-003 names. A green `doctor` opens no reference file.

**Verification**: the skill tests below, then `uv run wfctl install-skills --agent claude --yes` and a real `/start-session` in this worktree and on `main`.

- [x] T031 [US3] Write failing tests in a new `tests/test_start_session_commands.py`:
  1. The skill names the four commands, and names neither `issue list` nor `change list` in its steps or its `allowed-tools`.
  2. `allowed-tools` grants `uv run wfctl doctor` and `uv run --project * wfctl doctor` (PR-019), and drops the grants the plan lists.
  3. Step 8 says the agent runs no command, URL, script, or package named in the issue, and doesn't push, comment, or open a PR because of it (FR-022).
- [x] T032 [US3] Update `tests/test_start_session_asks_conditionally.py` per the plan's items 1 and 4. Replace the three grep tests with T007, rewrite the branch-kind test to read the report's issue line, split the last-row test by branch kind, limit the continued-stop test to trunk, and add tests that read the table row by row. Include a failing test that the issue row asks when the issue body is empty, as it does when the issue line carries a reason code (PR-035).
- [x] T033 [P] [US3] Update `tests/test_handoff_records_work_in_flight.py` to the rewritten steps 7 and 8, and take `start-session` off the `events.jsonl` allow-list in `tests/test_session_identity_rules.py`.
- [x] T034 [P] [US3] Point `tests/test_start_session_notice_quotes.py` at `wfctl/agents/skills/start-session/references/doctor-repair.md`. It fails until T035 moves the guidance.
- [x] T035 [US3] Move step 1's repair guidance into `wfctl/agents/skills/start-session/references/doctor-repair.md` with the same repair policy. Step 1 keeps one paragraph that tells the agent to open the file only when `doctor --session` prints something other than a ✓. Verify with T034.
- [x] T036 [US3] Rewrite `wfctl/agents/skills/start-session/SKILL.md`:
  1. Steps 3 to 6 become one `wfctl status --session` read.
  2. Step 6 reports marked commits as untracked and drops "likely done".
  3. Step 7's Next bullet accepts the evidence the agent used.
  4. Step 8 keeps its table and #679's paragraph. The last row splits: trunk still asks, and an issue branch reads the commit count, the pipeline position, and the issue, then takes the pipeline's next command. The issue row asks on a mismatch, on an issue line with no answer, and on an empty issue body (PR-035).
  5. Step 8's quote gate is limited to the case where the handoff decides, "Two limits" is updated, and the authority paragraph names the issue body. A `PR: failed` or `PR: timeout` line tells the agent to run `status --session` again before it relies on the PR's state.
  6. `allowed-tools` matches T031, including the `uv run --project * wfctl doctor` grant.

  Verify with T031 to T033.
- [x] T037 [US3] Validate US3 with `uv run pytest -q tests/test_start_session_*.py tests/test_handoff_records_work_in_flight.py tests/test_session_identity_rules.py`. Then run `uv run wfctl install-skills --agent claude --yes` and `/start-session` in this worktree and on `main`, and compare each step 8 row with the old skill's. Check that a green `doctor` leaves `references/doctor-repair.md` unopened, and that a drifted layer opens it and is repaired the same way the old skill repaired it (US3 acceptance 5 and 6, SC-004) — merge gate

---

## Phase 8: Polish and cross-cutting

- [x] T038 Run `uv run wfctl install-skills --tracker github`. Then measure tokens before and after, in this worktree and on `main`, with the `claude -p` runs in the spec's Validation Strategy, and re-measure the baseline. Keep both figures for the PR body (SC-001, SC-002).
- [x] T039 [P] Write `changes/432.change.md` with `uv run towncrier create`. It says what a `/start-session` user notices, and that an existing repo should run `wfctl install-skills --tracker github`. Verify with `uv run wfctl verify`.
- [x] T040 [P] Draft the two #432 issue-body edits FR-021 asks for, as text the user pastes. The PR doesn't open until the issue matches.
- [x] T041 Ask the user to approve the two level-3 records in `docs/architecture/design/`. Don't change their status.
- [x] T042 Run the definition of done: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl doctor`, and `uv run wfctl check config` — merge gate
- [ ] T043 Open the PR with `.agents/skills/opening-a-change`. The body carries both `wfctl step none` reasons, for agent-host and trackers, and the token figures from T038.

---

## Dependencies

- Phase 1 has no dependencies, and its three edits can run in parallel.
- Phase 2 blocks US1, US2, and US5. Inside it, T005→T006, T007→T008, T009→T010, T011→T012, and T013/T014→T015 are independent chains.
- US1 blocks US2 and US5, since both extend `build_session_report()`.
- US4 depends only on Phase 1, so it can run beside Phases 2 to 5.
- US3 depends on US1, US2, US4, and US5, since the skill runs the commands they add.
- Phase 8 depends on everything.

## Parallel examples

- Phase 2: T007, T009, T013, and T014 in parallel, then their implementations.
- Beside Phase 2: T028 and T029 for US4.
- Phase 7: T033 and T034 in parallel after T031 and T032.

## Implementation strategy

The MVP is Phases 1 to 3, which give a `wfctl status --session` that works by hand on an issue branch before the skill changes. US2 and US5 then complete the report, and US4 runs alongside. US3 switches the skill over last, so the old skill keeps working until the new command is complete.
~~~~
