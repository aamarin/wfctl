---
description: 'Task list for #626: wfctl stops a review group after three rounds'
---

# Tasks: wfctl stops a review group after three rounds

**Input**: Design documents from `626-review-round-cap/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Every task names its test file or command. Write each test first and
confirm it fails before writing the code it covers. Run everything through
`uv run`, and pin `NO_COLOR` in any test that asserts on output.

**Design records**: none. `design.md` records no level-3 decision. The accepted
level-2 records `review-round-count` and `review-round-cap` set the boundary.

**Two plan-review findings are settled here rather than in plan.md.** The third
plan review left two MINOR findings open. Any edit to plan.md makes its review
stale and costs another full review run, so these tasks carry both fixes:

1. PR-023 (T024, T025, T027). Today the guard's `_judge` refuses a branch whose
   `trunk` names the branch itself. With `origin/HEAD` set, the plan would have
   `review start` only warn in that case. As a result, an agent could spend
   rounds on a branch that can't open a PR. `review start` now refuses with
   today's same-name message, so it agrees with the guard. To do that,
   `review_trunk` takes a `branch` keyword, which the data model doesn't list.
   This is the one place these tasks go past the plan.
2. PR-024 (T035). Quickstart step 10 expects `review start` to list the
   branch's commits. At that point, the sign-off covers every commit, so the
   command prints outcome 3 and shows no range. Step 10 now adds a commit and
   checks the range with step 8's guard command.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 is the cap and the refusal, US2 is one run per group per
  round, and US3 is the cap and the trunk read from the default branch

---

## Phase 1: Setup

**Purpose**: Confirm the baseline before anything changes.

- [x] T001 Confirm the branch starts green: run `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` from the worktree root, and note any failure that predates this branch before going on

---

## Phase 2: Foundational

**Purpose**: The parser and the two helpers that every story reads through. No
behavior changes yet.

**⚠️ CRITICAL**: US1 and US3 both need T002 to T007.

- [x] T002 [P] Write failing tests in `tests/test_review_config.py` for `parse_rounds`: absent gives `(None, None)`; 0 and 3 are valid; -1, 1.5, `"3"`, and `true` each give `review.rounds must be a whole number of 0 or more`; `load` reports that problem for an invalid working-tree value; `load_rounds` returns a valid value, and None for an absent or invalid one
- [x] T003 Add `DEFAULT_ROUNDS = 3`, `rounds` in `_REVIEW_KEYS`, `parse_rounds`, the problem in `load`, and `load_rounds` to `wfctl/_review_config.py`, per plan.md `_review_config.py` items 1 to 4 and R1; verify with `uv run pytest -q tests/test_review_config.py`
- [x] T004 [P] Write failing tests in `tests/test_review.py` for `runs_started`: it counts the run folders that hold a `run.json`, including a run with no reports, which never completed; it skips a folder with no `run.json`; and it agrees with `latest_run` on which folders count
- [x] T005 Extract `_run_numbers(agent_dir, group)` from `latest_run` and add `runs_started` in `wfctl/_review.py` (R3); verify with `uv run pytest -q tests/test_review.py`, with the existing `latest_run` tests unchanged
- [x] T006 Extract `_covered_by_sign_off(repo_root, agent_dir, timeout)` from `unreviewed` in `wfctl/_review.py`. It returns the signed-off commit or None, and a function that says whether the sign-off covers a commit (R4). `unreviewed` behaves as before; verify with `uv run pytest -q tests/test_review.py tests/test_review_gate.py`, with every existing test passing unchanged
- [x] T007 Validate Phase 2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`, and confirm `uv run wfctl check config` accepts this repo's `wfctl.json` — merge gate

**Checkpoint**: `check config` accepts and reports `review.rounds`. The count and the sign-off check exist, and nothing calls them yet.

---

## Phase 3: User Story 1 - wfctl refuses a review run past the cap (Priority: P1) 🎯 MVP

**Goal**: `review start` counts a group's runs and refuses one past the cap,
unless the sign-off covers every commit left to review. It prints the four
outcomes in `contracts/cli.md`. The command passes `DEFAULT_ROUNDS` in this
phase, and US3 replaces it with the trunk's value.

**Independent Test**: With no `review.rounds` anywhere, take a group through
three runs with a commit between each. The fourth `review start` exits 1 with
outcome 4 and creates no `runs/004`. After a sign-off, the same command exits 0
with outcome 3.

**Verification**:

- Automated: `tests/test_review.py` and `tests/test_review_cli.py`, through `uv run pytest -q`
- Manual: quickstart.md steps 3 to 8, run in T037
- Evidence: outcome 4 leaves no new run folder, outcome 3 names the signed-off commit, and the header carries `round N of M`

### Tests for User Story 1 ⚠️

> Write these first, and confirm they fail.

- [x] T008 [P] [US1] Write failing tests in `tests/test_review.py` for `start(cap=...)`: the order in FR-002, so a group that is up to date at the cap returns outcome 1 and isn't refused; under the cap, it writes the run and `Started.rounds` is the prior count; at the cap with a sign-off covering the range, it sets `sign_off` and writes nothing; at the cap with an uncovered commit, it raises `RoundCapReached` and writes no folder; a sign-off on an older commit with one commit after it raises; a clean trunk merge after the sign-off still gives outcome 3; a count of 4 under a cap of 3 raises; and a cap of 0 raises on any range
- [x] T009 [P] [US1] Write failing tests in `tests/test_review.py` for the three `RoundCapReached` messages in R6: at the cap, past it, and a cap of 0
- [x] T010 [P] [US1] Write failing tests in `tests/test_review_cli.py` for every outcome line in `contracts/cli.md`, with its exit code: the header `security run 002 · round 2 of 3 · …`, the three outcome 3 lines, and the three outcome 4 lines with the sign-off line under them. Update `test_start_prints_the_run_the_reports_path_and_one_line_per_reviewer` for the round in the header

### Implementation for User Story 1

- [x] T011 [US1] Add `RoundCapReached(ReviewError)` with `group`, `rounds`, and `cap`, and the R6 messages, in `wfctl/_review.py`; verify with the T009 tests
- [x] T012 [US1] Add `rounds: int` and `sign_off: str | None` to `Started` in `wfctl/_review.py`, and pass both everywhere a `Started` is built; verify with `uv run mypy` and `uv run pytest -q tests/test_review.py`
- [x] T013 [US1] Give `start` a `cap: int` parameter and the order in plan.md `_review.py` item 8: the range first, then `runs_started` against the cap, then `_covered_by_sign_off` over every commit in the range, then `RoundCapReached`; verify with the T008 tests
- [x] T014 [US1] Update `review_start_cmd` in `wfctl/cli.py` per plan.md `cli.py` items 2 to 6. It passes `cap=_review_config.DEFAULT_ROUNDS`. It catches `RoundCapReached` before `ReviewError`, prints `✗ <message>` and the sign-off line, and exits 1. It checks `started.sign_off` before `started.run is None` and prints the outcome 3 line. It adds ` · round {started.rounds + 1} of {cap}` to the header, and its docstring says it refuses a run past `review.rounds`; verify with the T010 tests
- [x] T015 [US1] Validate US1 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: The cap holds at 3, and all four outcomes print. wfctl doesn't read the trunk's cap yet.

---

## Phase 4: User Story 2 - Each group runs once per round (Priority: P1)

**Goal**: The skills stop telling the security group to run again over its own
fixes, and they say wfctl enforces the cap. As a result, a group's run count is
the branch's round count.

**Independent Test**: After `uv run wfctl install-skills --agent claude`, the
installed `opening-a-change` Step 1 describes one run per group per round, says
wfctl enforces the cap, and has no #626 sentence. The installed
`fanning-out-code-review` header example shows the round.

**Verification**:

- Automated: `tests/test_opening_a_change_panel.py` and `tests/test_review_fanout_skill.py`
- Manual: read both skills as installed under `.claude/skills/` (T020)
- Evidence: the installed text matches plan.md "What the skill and doc rewrites say"

### Tests for User Story 2 ⚠️

- [x] T016 [P] [US2] Rewrite `test_the_panel_step_stops_after_three_rounds_to_ask_for_a_sign_off` in `tests/test_opening_a_change_panel.py` for FR-013. Step 1 names the round cap and runs each group once per round. It drops the extra security run and the #626 sentence, and the guard-refusal bullet matches. Confirm the test fails
- [x] T017 [P] [US2] Add failing tests in `tests/test_review_fanout_skill.py` for FR-014. The `review start` example header is `security run 003 · round 3 of 3 · 2 commits since a1b2c3d · head 9f8e7d6`, and the paragraph after it has the outcome 3 and outcome 4 sentences

### Implementation for User Story 2

- [x] T018 [P] [US2] Rewrite `opening-a-change` Step 1 (the round paragraph and **Stop after three complete rounds**, lines 73 to 89) and the guard-refusal bullet (line 375) in `wfctl/agents/skills/opening-a-change/SKILL.md`, per plan.md. Load `writing-style` first; verify with the T016 test
- [x] T019 [P] [US2] Update the header example at line 82, and add the two sentences after the up-to-date sentence, in `wfctl/agents/skills/fanning-out-code-review/SKILL.md`, per plan.md. Leave the `review check` example at line 259 as it is. Load `writing-style` first; verify with the T017 tests
- [x] T020 [US2] Run `uv run wfctl install-skills --agent claude`, read both skills as installed under `.claude/skills/`, and confirm they read as plan.md says. Then run `uv run wfctl doctor`
- [x] T021 [US2] Validate US2 with `uv run pytest -q tests/test_opening_a_change_panel.py tests/test_review_fanout_skill.py` and the full `uv run pytest -q` — merge gate

**Checkpoint**: The skills describe what US1 enforces.

---

## Phase 5: User Story 3 - A repository sets its own cap on the trunk (Priority: P2)

**Goal**: Reviews read the trunk from `wfctl.json` on the default branch, read
the cap from that trunk, and warn when the branch sets something else (FR-007
to FR-010, FR-017, R2, R5, and R11).

**Independent Test**: With `review.rounds` set to 5 only in the working tree,
`review start` prints the mismatch warning, and the header reads `of 3`. With
`trunk` set to another branch the clone has, it prints the trunk warning and
still measures against `main`. With `trunk` set to the branch itself, it
refuses with the same-name message, as the guard does.

**Verification**:

- Automated: `tests/test_review.py`, `tests/test_review_cli.py`, and `tests/test_review_gate.py`
- Manual: quickstart.md steps 9 and 10, run in T037
- Evidence: the cap and the range come from the default branch's trunk in every row of R11's case table

### Tests for User Story 3 ⚠️

- [x] T022 [P] [US3] Write failing tests in `tests/test_review.py` for `_read_config_at` and `trunk_rounds`: no file, no `review` key, a valid value, an invalid value, bad JSON, a top level or `review` value that isn't an object, and a stale `origin/main`, where the cap comes from the local ref
- [x] T023 [P] [US3] Write failing tests in `tests/test_review.py` for `review_trunk`, one per row of R11's case table: no `origin/HEAD`, where the branch's setting decides; a clone that doesn't fetch every branch; `origin/HEAD` naming a missing ref, refused with `git remote set-head origin --auto`; no file or no `trunk` key; `develop` declared on the default branch; a default-branch `trunk` the clone lacks, refused and naming `wfctl.json on origin/main`; a value that isn't a branch name, and `HEAD`; bad JSON; the working tree naming another trunk the clone has, which warns; `develop` declared only on the branch; a working-tree trunk the clone lacks, or that isn't a branch name, which raises `NoTrunk`; and `symbolic-ref` telling a missing `origin/HEAD` apart from a git failure. `test_range_with_no_trunk_branch_names_the_trunk_key` keeps passing unchanged
- [x] T024 [P] [US3] Write a failing test in `tests/test_review.py` for PR-023. With `origin/HEAD` set, a working tree whose `trunk` names the branch under review makes both `review_trunk(..., branch=<that branch>)` and `trunk_refs(..., branch=<that branch>)` raise today's same-name `ReviewError` (`the trunk branch is <x>, the branch under review; check trunk in wfctl.json`), with no mismatch warning
- [x] T025 [P] [US3] Write failing tests in `tests/test_review_cli.py` for every warning line in `contracts/cli.md`, the `origin/HEAD` refusal, the two default-branch refusal messages, and an invalid working-tree value. A branch that names another trunk prints the trunk warning and reviews against `main`, and `review sign-off` succeeds on that branch. With a trunk whose `wfctl.json` sets different groups, `review start` still prints the working tree's roster (FR-011). `test_start_with_no_trunk_branch_names_the_trunk_key` and `test_start_refuses_a_trunk_that_is_the_branch_under_review` keep passing unchanged. For PR-023, add a test that the same-name refusal also holds with `origin/HEAD` set
- [x] T026 [P] [US3] Write failing tests in `tests/test_review_gate.py`. An invalid branch `review.rounds` fails the guard the way any other invalid review setting does. A branch that names another trunk still has its own commits counted as unreviewed. The `main` checkout still merges a reviewed branch with `origin/HEAD` set. `test_no_trunk_branch_gives_the_error_refusal` and `test_a_trunk_that_is_the_judged_branch_is_refused` keep passing unchanged

### Implementation for User Story 3

- [x] T027 [US3] Add `_read_config_at` (R2), `ReviewTrunk`, and `review_trunk(repo_root, timeout, *, branch=None)` in `wfctl/_review.py`, following R11's five steps, with `symbolic-ref --quiet --short` and `answers=(0, 1)`. For PR-023, step 5 checks the working tree's declared trunk first. When it equals `branch`, `review_trunk` raises today's same-name `ReviewError` with the working-tree wording, before it resolves the name or builds a warning; verify with the T023 and T024 tests
- [x] T028 [US3] Make `trunk_refs` in `wfctl/_review.py` call `review_trunk(..., branch=branch)` in place of `_paths.trunk_branch`, per plan.md `_review.py` item 5. It keeps the same-name check and `NoTrunk`, in that order. On the default-branch path, both messages name `wfctl.json on origin/<default>`. `_refuse_a_single_branch_clone` runs only on the fallback path. `NoTrunk()` stays callable with no arguments, since `_judge` calls it that way. Rewrite the docstring; verify with `uv run pytest -q tests/test_review.py tests/test_review_gate.py`
- [x] T029 [US3] Add `TrunkRounds` and `trunk_rounds(repo_root, timeout, *, branch)` in `wfctl/_review.py`. It reads `trunk_refs(...)[0]` through `_read_config_at` and validates with `parse_rounds` (R2); verify with the T022 tests
- [x] T030 [US3] Update `review_start_cmd` in `wfctl/cli.py` per plan.md `cli.py` item 1 and R5. It calls `review_trunk(..., branch=<current branch>)` and prints its warning. It calls `trunk_rounds` and prints its warning, then compares the cap with `load_rounds` and prints the mismatch warning. A `ReviewError` from either call prints `✗` and exits 1. It passes the trunk's cap to `_review.start` in place of `DEFAULT_ROUNDS`, and both calls get `timeout=None`; verify with the T025 tests
- [x] T031 [US3] Confirm `wfctl/_review_gate.py` is unchanged (FR-012), so `git diff main -- wfctl/_review_gate.py` prints nothing, and that the guard path still imports neither `typer` nor `rich`; verify with `uv run pytest -q tests/test_review_gate.py tests/test_guard_entry.py`
- [x] T032 [US3] Add the `review.rounds` and `trunk` paragraphs to "Declaring reviewers" in `AGENTS.md`, per plan.md. Load `writing-style` first; verify by reading the section in place
- [x] T033 [US3] Validate US3 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `uv run wfctl check config` — merge gate

**Checkpoint**: Every story works. A branch can't raise its own cap or move its own trunk.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: The records, the release notes, the quickstart fix, and the
end-to-end check.

- [x] T034 [P] Add an `amended` Log line to `docs/architecture/design/642-commit-range-takes-judged-branch.md` and `docs/architecture/design/642-origin-head-trusted-on-full-fetch.md`. Each says that #626 moved trunk resolution for reviews into `review_trunk`, which reads `trunk` from the default branch and falls back to `_paths.trunk_branch`, so a declared trunk decides only on the fallback path. Load `writing-style` first; verify with `uv run wfctl arch check`
- [x] T035 [P] Rewrite quickstart step 10 in the spec dir's `quickstart.md` for PR-024, without touching plan.md. First add one commit to the branch, so the sign-off no longer covers it. Then push the branch's head to `origin` as `loose` with `"review": {"rounds": 9}`, and set `"trunk": "loose"` in this branch's working tree. `wf review start security` prints the trunk warning and outcome 4 reading `3 of 3`, which shows the cap came from `origin/main`. Step 8's guard command then refuses and lists the new commit under security, which shows the range is still measured from `main`. If wfctl used `loose` as the trunk, that commit would be on the trunk and the guard would allow the PR
- [x] T036 [P] Create `changes/626.addition.md` and `changes/626.change.md` with `uv run towncrier create`. The addition covers the `review.rounds` key, its default of 3, and the refusal. The change covers each group running once per round, and reviews reading `trunk` from the default branch, so a repository whose trunk isn't its default branch declares it there. Load `writing-style` first; verify with `uv run wfctl verify`
- [x] T037 Run quickstart.md steps 1 to 10 end to end against this worktree, with step 10 as T035 rewrote it, and record what each step printed in the session summary
- [x] T038 Validate the branch with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl check config`, `uv run wfctl verify`, and `uv run wfctl doctor` — merge gate
- [ ] T039 Store the spec dir with `uv run wfctl store specs` before the PR opens

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none.
- **Foundational (Phase 2)**: after Setup. It blocks US1 and US3.
- **US1 (Phase 3)**: after Phase 2.
- **US2 (Phase 4)**: after Phase 1, since it changes only skills and their
  tests. It should merge with US1 or after it, because the skills describe the
  cap US1 enforces.
- **US3 (Phase 5)**: after US1, because T030 replaces the cap that T014 passes
  and edits the same command.
- **Polish (Phase 6)**: after US1 to US3. T034 to T036 can start once the US3
  code is done.

### Within Each Story

- Tests come first and fail, then the code they cover.
- In `wfctl/_review.py`, T011 and T012 come before T013, and T027 comes before T028, which comes before T029.
- In `wfctl/cli.py`, T014 comes before T030.

### Parallel Opportunities

- T002 and T004, which use different test files.
- T008, T009, and T010, before any US1 code.
- All of US2, beside US1.
- T016 and T017, then T018 and T019.
- T022 to T026.
- T034, T035, and T036.

---

## Parallel Example: User Story 3

```bash
Task: "Write failing tests for trunk_rounds in tests/test_review.py"          # T022
Task: "Write failing CLI tests for every warning in tests/test_review_cli.py" # T025
Task: "Write failing guard tests in tests/test_review_gate.py"                # T026
```

T022, T023, and T024 share `tests/test_review.py`, so write them in one pass
when they run beside T025 and T026.

---

## Implementation Strategy

### MVP First

1. Phases 1 and 2.
2. US1, so the cap holds at the default of 3.
3. Stop and run the US1 Independent Test.

### Incremental Delivery

1. Phases 1 and 2, then US1: the cap of 3, the refusal, and the sign-off.
2. US2: the skills describe what US1 enforces. Ship them with US1 or right after.
3. US3: the cap and the trunk come from the default branch.
4. Polish: the records, the release notes, the quickstart, and the end-to-end check.

---

## Notes

- PR-023 adds a `branch` keyword to `review_trunk`, which data-model.md lists as
  `review_trunk(repo_root, timeout)`. It also changes two things plan.md and
  research.md R11 still say. First, plan.md's test list has
  `test_start_refuses_a_trunk_that_is_the_branch_under_review` drop
  `origin/HEAD`, and a new test pin a warning when `origin/HEAD` is set. T025
  keeps that test unchanged and adds a refusal test instead. Second, R11's
  "different trunk the clone has" row warns, and T027 refuses when that trunk
  is the branch itself. spec.md FR-017 states the exception. plan.md stays as
  it is, because any edit to it makes the plan review stale. Follow these tasks
  where the two disagree.
- Skill text is edited under `wfctl/agents/` only (`layer-model`), and checked
  after `uv run wfctl install-skills`.
- Commit after each task or group, with each message in its own scratchpad file
  for `git commit -F`.
